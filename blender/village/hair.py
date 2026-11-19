"""Strand hair for the Reom-based characters, as Blender hair curves (rendered by Cycles).

- eyebrows(): one of Reom's eyebrow hairstyles (hairstyles/EyebrowsNNN.npz, CC-BY with the character),
  moved along with the morphed skin.
- coily_scalp(): short, tightly coiled hair grown on the scalp region of the face texture
  (green channel of Head_ScalpBeardShadowMask.png).

For Roblox the strands are not exported; they are baked into textures or cards later.
"""
import math

import bpy
import numpy as np
from mathutils.kdtree import KDTree

from village import reom


def hair_material(name, melanin=0.95, redness=0.15, roughness=0.35, radial=0.6, random_color=0.15):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    bsdf.parametrization = "MELANIN"
    bsdf.inputs["Melanin"].default_value = melanin
    bsdf.inputs["Melanin Redness"].default_value = redness
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Radial Roughness"].default_value = radial
    bsdf.inputs["Random Color"].default_value = random_color
    bsdf.inputs["Random Roughness"].default_value = 0.2
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return mat


def _curves_object(name, strands, radius_root, radius_tip, material):
    """strands: list of (n, 3) arrays. Radius tapers linearly from root to tip."""
    cv = bpy.data.hair_curves.new(name)
    cv.add_curves([len(s) for s in strands])
    pts = np.concatenate(strands).astype(np.float32)
    cv.position_data.foreach_set("vector", pts.ravel())
    rad = np.concatenate([np.linspace(radius_root, radius_tip, len(s)) for s in strands]).astype(np.float32)
    attr = cv.attributes.get("radius") or cv.attributes.new("radius", "FLOAT", "POINT")
    attr.data.foreach_set("value", rad)
    cv.materials.append(material)
    obj = bpy.data.objects.new(name, cv)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _displacement_lookup(base, morphed):
    tree = KDTree(len(base))
    for i, co in enumerate(base):
        tree.insert(co, i)
    tree.balance()
    d = morphed - base

    def shift(points):
        out = points.copy()
        for k, p in enumerate(points):
            # inverse-distance blend of the 4 nearest skin vertices: smooth across the brow
            near = tree.find_n(p, 4)
            w = np.array([1.0 / max(dist, 1e-5) for _, _, dist in near])
            out[k] += (d[[i for _, i, _ in near]] * w[:, None]).sum(axis=0) / w.sum()
        return out
    return shift


def eyebrows(base, morphed, style="Eyebrows001", children=10, spread=0.002, melanin=0.97, seed=3):
    """base / morphed: (n, 3) vertex positions of the mesh before and after the morphs.  The style
    files hold guide strands only; like CharMorph's particle children, every guide gets `children`
    copies with roots scattered within `spread` metres along the brow surface."""
    z = np.load(reom.CHAR / "hairstyles" / f"{style}.npz", allow_pickle=False)
    cnt, data = z["cnt"].astype(int), z["data"].astype(np.float64)
    rng = np.random.default_rng(seed)
    guides = np.split(data, np.cumsum(cnt)[:-1])
    strands = []
    for g in guides:
        strands.append(g)
        for _ in range(children):
            off = np.array((rng.normal(0, spread), 0.0, rng.normal(0, spread * 0.45)))
            tip = rng.uniform(0.8, 1.15)
            strands.append(g[0] + off + (g - g[0]) * tip)
    shift = _displacement_lookup(base, morphed)
    roots = np.array([st[0] for st in strands])
    moved = shift(roots) - roots
    strands = [st + mv for st, mv in zip(strands, moved)]
    mat = hair_material("BrowHair", melanin=melanin, redness=0.1, roughness=0.4)
    return _curves_object("Eyebrows", strands, 0.00007, 0.00003, mat)


def _scalp_samples(obj, density, rng, mask_threshold=0.08, min_below_eyes=0.075):
    """Random points on the scalp: (position, normal, mask value) by area-weighted sampling of the
    face-material triangles, weighted by the green channel of the scalp mask."""
    from PIL import Image
    mask = np.asarray(Image.open(reom.CHAR / "textures/Head_ScalpBeardShadowMask.png").convert("RGB"),
                      dtype=np.float32)[:, :, 1] / 255.0
    H, W = mask.shape
    me = obj.data
    me.calc_loop_triangles()
    face_slot = reom.MATERIALS.index("Face")
    uv = me.uv_layers.active.data
    co = np.array([v.co[:] for v in me.vertices])
    # mask value per vertex (largest over its UV corners), so strands do not thin out along UV seams
    vm = np.zeros(len(co))
    face_loops = [li for p in me.polygons if p.material_index == face_slot for li in p.loop_indices]
    for lp in (me.loops[i] for i in face_loops):
        u, v = uv[lp.index].uv
        vm[lp.vertex_index] = max(vm[lp.vertex_index], mask[min(H - 1, max(0, int((1 - v) * H))),
                                                            min(W - 1, max(0, int(u * W)))])
    tris = np.array([t.vertices[:] for t in me.loop_triangles if t.material_index == face_slot])
    # the mask's UV region also covers the sides and front of the neck: no hair below the ear lobes
    eyes_z = np.mean([co[v][2] for p in me.polygons if p.material_index == reom.MATERIALS.index("Iris")
                      for v in p.vertices])
    vm[co[:, 2] < eyes_z - min_below_eyes] = 0.0
    tris = tris[vm[tris].max(axis=1) > 0.02]
    a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    cross = np.cross(b - a, c - a)
    area = np.linalg.norm(cross, axis=1) / 2
    n = int(area.sum() * density)
    pick = rng.choice(len(area), size=n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n)
    s = np.sqrt(r1)
    w0, w1, w2 = 1 - s, s * (1 - r2), s * r2
    pos = a[pick] * w0[:, None] + b[pick] * w1[:, None] + c[pick] * w2[:, None]
    m = (vm[tris[pick, 0]] * w0 + vm[tris[pick, 1]] * w1 + vm[tris[pick, 2]] * w2)
    vn = np.array([v.normal[:] for v in me.vertices])
    nrm = (vn[tris[pick, 0]] * w0[:, None] + vn[tris[pick, 1]] * w1[:, None] + vn[tris[pick, 2]] * w2[:, None])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    # a soft hairline: the thinner the mask, the fewer strands survive
    alive = (m > mask_threshold) & (rng.random(n) < np.clip(m * 1.4, 0, 1))
    return pos[alive], nrm[alive], m[alive]


def coily_scalp(obj, density=900_000, length=0.012, coil_radius=0.0016, turns=2.6, points=12,
                melanin=0.98, seed=7):
    """Short type-4 coils: every strand is a helix around the skin normal, tilted backwards a little,
    with random length, radius, phase and handedness.  density is strands per square metre."""
    rng = np.random.default_rng(seed)
    pos, nrm, m = _scalp_samples(obj, density, rng)
    back = np.array((0.0, 1.0, -0.25))
    strands = []
    t = np.linspace(0, 1, points)
    for p, n, mv in zip(pos, nrm, m):
        axis = n + 0.25 * back
        axis /= np.linalg.norm(axis)
        u = np.cross(axis, (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0))
        u /= np.linalg.norm(u)
        v = np.cross(axis, u)
        L = length * (0.55 + 0.45 * min(1.0, mv * 1.3)) * rng.uniform(0.7, 1.25)
        R = coil_radius * rng.uniform(0.6, 1.3)
        ph = rng.uniform(0, 2 * math.pi)
        hand = rng.choice((-1.0, 1.0))
        ang = ph + hand * 2 * math.pi * turns * rng.uniform(0.8, 1.2) * t
        ramp = np.minimum(1.0, t * 4)[:, None]          # the coil opens up just above the skin
        s = (p - n * 0.0004 + axis * (L * t)[:, None]
             + ramp * R * (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v)
             - ramp * R * (math.cos(ph) * u + math.sin(ph) * v))
        strands.append(s)
    mat = hair_material("ScalpHair", melanin=melanin, redness=0.1, roughness=0.45, radial=0.75)
    return _curves_object("ScalpHair", strands, 0.00007, 0.00004, mat)
