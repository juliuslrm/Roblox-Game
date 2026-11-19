"""Lio, the reference trader of the new character pipeline: Reom base (CC-BY) shaped into Lio.

    python blender/build_lio.py -- [--stage base|face|dressed|poses] [--samples 64]

Stage "base": the body in the neutral A-pose without clothes, rendered for review
(previews/lio/01-base.png: front, back, side, face front, three-quarter and back, both hands).
"""
import argparse
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE)]

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from village import garments as G  # noqa: E402
from village import hair, posing, reom, reom_rig  # noqa: E402

OUT = ROOT / "previews/lio"
# Lio Glasfunke, about 22: young Black man, lean craftsman's build, alert face
SHAPE = {
    "Race_Blackman": 0.9,
    "Body_ReomMuscle": 0.45, "Body_ReomFat": 0.12,
    "Shoulders_ShoulderWidth": 0.25, "Neck_Girth": 0.25, "Arms_ForearmGirth": 0.3,
    "Jaw_Mandible": 0.8, "Cheeks_Zygomatic_Bone": 0.6, "Mouth_Lips_Height": 0.25,
    "Face_FrontalBone_BrowRidge": 0.5, "Jaw_Mandible_GonialAngle": 0.4, "Chin_AnteriorMandibleWidth": 0.3,
}
SKIN = dict(melanin=1.0, tone=0.1, melanin_blend=1.0, melanin_fraction=0.42,
            hemoglobin=0.06, lip_strength=0.0, stubble=0.35, scalp_tan_lines=0.0)


def scene_setup(samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.view_settings.view_transform = "AgX"
    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.62, 0.64, 0.68, 1)
    bg.inputs["Strength"].default_value = 0.8
    sc.world = world
    key = bpy.data.objects.new("key", bpy.data.lights.new("key", "AREA"))
    key.data.energy, key.data.size = 900, 2.5
    key.location = (-1.8, -2.6, 2.6)
    key.rotation_euler = (math.radians(55), 0, math.radians(-35))
    rim = bpy.data.objects.new("rim", bpy.data.lights.new("rim", "AREA"))
    rim.data.energy, rim.data.size = 500, 2.0
    rim.location = (2.0, 2.2, 2.4)
    rim.rotation_euler = (math.radians(-55), 0, math.radians(140))
    for o in (key, rim):
        sc.collection.objects.link(o)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.clip_start = 0.01
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, cam


def shoot(sc, cam, path, target, direction, dist, lens=50, res=(640, 640)):
    cam.data.lens = lens
    target = Vector(target)
    eye = target + Vector(direction).normalized() * dist
    cam.location = eye
    cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return path


def group_centre(obj, groups, name):
    idx, w = groups[name]
    V = np.array([obj.data.vertices[i].co[:] for i in idx])
    return (V * w[:, None]).sum(axis=0) / w.sum()


def sheet(paths, out, cols):
    from PIL import Image
    ims = [Image.open(p) for p in paths]
    w, h = ims[0].size
    rows = math.ceil(len(ims) / cols)
    o = Image.new("RGB", (w * cols, h * rows), (30, 30, 34))
    for k, im in enumerate(ims):
        o.paste(im, ((k % cols) * w, (k // cols) * h))
    o.save(out)
    for p in paths:
        os.remove(p)


def material_centre(obj, name):
    slot = reom.MATERIALS.index(name)
    vs = {v for p in obj.data.polygons if p.material_index == slot for v in p.vertices}
    return np.array([obj.data.vertices[i].co[:] for i in vs]).mean(axis=0)


def hand_box(obj, groups, side):
    """Bounding box of every vertex weighted > 0.3 to the hand or a finger of one side."""
    idx = set()
    for name, (gi, gw) in groups.items():
        if name.endswith(f".{side}") and (name.startswith("DEF-hand") or name.startswith("DEF-f_")
                                          or name.startswith("DEF-thumb") or name.startswith("DEF-palm")):
            idx.update(int(i) for i in gi[gw > 0.3])
    V = np.array([obj.data.vertices[i].co[:] for i in idx])
    return V.min(axis=0), V.max(axis=0)


def build_body():
    obj = reom.load("Lio")
    base = np.array([v.co[:] for v in obj.data.vertices])
    reom.apply_morphs(obj, SHAPE)
    reom.set_skin(obj, **SKIN)
    reom.tint_lips()
    morphed = np.array([v.co[:] for v in obj.data.vertices])
    hair.eyebrows(base, morphed)
    hair.coily_scalp(obj)
    reom.refresh_normals(obj)
    obj["base_co"] = base.ravel().tolist()
    return obj, morphed


def stage_base(samples):
    sc, cam = scene_setup(samples)
    obj, V = build_body()
    groups = reom.vertex_groups()
    lo, hi = V.min(axis=0), V.max(axis=0)
    centre = (lo + hi) / 2
    h = hi[2] - lo[2]
    eyes = material_centre(obj, "Iris")
    face = eyes + np.array((0.0, 0.0, -0.025))
    tmp = OUT / "_tiles"
    tmp.mkdir(parents=True, exist_ok=True)
    tiles = [
        shoot(sc, cam, tmp / "0.png", centre, (0, -1, 0.04), h * 1.75),
        shoot(sc, cam, tmp / "1.png", centre, (0, 1, 0.04), h * 1.75),
        shoot(sc, cam, tmp / "2.png", centre, (1, 0, 0.04), h * 1.75),
        shoot(sc, cam, tmp / "3.png", face, (0, -1, 0.02), 0.62, lens=70),
        shoot(sc, cam, tmp / "4.png", face, (0.75, -1, 0.05), 0.65, lens=70),
        shoot(sc, cam, tmp / "5.png", face + np.array((0, 0.03, 0.04)), (-0.7, 1, 0.45), 0.7, lens=70),
    ]
    for k, side in enumerate(("L", "R")):
        blo, bhi = hand_box(obj, groups, side)
        c = (blo + bhi) / 2
        size = float(np.linalg.norm(bhi - blo))
        sx = 1 if side == "L" else -1
        tiles.append(shoot(sc, cam, tmp / f"{6 + k}.png", c, (sx * 0.5, -1, 0.1), size * 2.6, lens=70))
    sheet(tiles, OUT / "01-base.png", cols=4)
    print(f"[lio] base: {len(obj.data.vertices)} vertices, {h:.3f} m tall -> {OUT / '01-base.png'}")


# ------------------------------------------------------------------------------------------- outfit
def dress(obj):
    """Rig plus Lio's outfit: linen shirt with rolled sleeves, wool trousers, mid-calf boots, the
    glassblower's leather apron, belt with brass buckle, pouch and three potion vials, brass goggles
    pushed up on the forehead."""
    base = np.array(obj["base_co"]).reshape(-1, 3)
    groups = reom.vertex_groups()
    rig = reom_rig.build(obj, base, groups)
    body = G.Body(obj, rig, groups)
    linen = G.fabric("Linen", (0.76, 0.68, 0.53), weave_scale=1100)
    wool = G.fabric("Wool", (0.25, 0.19, 0.15), weave_scale=700, rough=0.95, bump=0.35)
    apron_leather = G.leather("ApronLeather", (0.42, 0.25, 0.13))
    boot_leather = G.leather("BootLeather", (0.21, 0.13, 0.08), rough=0.62, wear=0.35)
    strap_leather = G.leather("StrapLeather", (0.30, 0.17, 0.09), rough=0.45)
    metal = G.brass()
    G.collider(obj)
    sh = G.shirt(body, linen, ease=0.016, sleeve_ease=0.026, drape=True)
    tr = G.trousers(body, wool, under=[sh], ease=0.022, drape=True)
    pieces = [sh, tr] + G.boots(body, boot_leather, under=[tr])
    G.collider(tr, 0.003)
    ap, grid = G.apron(body, apron_leather)
    pieces.append(ap)
    pieces += shirt_trim(body, sh, linen)
    for p in pieces:
        G.bind(p, body)
    pieces += belt(body, strap_leather, metal)
    pieces += apron_straps(body, grid, strap_leather)
    pieces += goggles(body, strap_leather, metal)
    for name in ("Eyebrows", "ScalpHair"):
        G.bind_rigid(bpy.data.objects[name], body, "DEF-spine.006")
    return rig, body, pieces


def shirt_trim(body, sh, linen):
    """Rolled cuffs at the sleeve ends."""
    loops = G.boundary_loops(sh)
    out = []
    for k, lp in enumerate(sorted(loops, key=lambda lp: abs(lp[:, 0].mean()))[-2:]):
        out.append(G.edge_band(f"Cuff.{k}", lp, 0.04, 0.0065, linen))
    return out


def belt(body, leather, metal):
    torso = body.V[(body.arm_w("L") + body.arm_w("R")) < 0.2]
    z = body.head("DEF-thigh.L")[2] + 0.045
    sl = torso[np.abs(torso[:, 2] - z) < 0.012]
    c = body.head("DEF-spine")
    ring = G.ring_outline(sl, c, z, segments=72, pad=0.024)
    out = (ring - np.array((c[0], c[1], z)))
    out /= np.linalg.norm(out, axis=1, keepdims=True)
    belt = G.flat_strap("Belt", ring, 0.045, 0.005, leather, closed=True, normal_hint=out)
    G.bind(belt, body)
    parts = [belt]
    front = ring[np.argmin(ring[:, 1])]
    for k, (dx, dz, sx, sz) in enumerate(((-0.028, 0, 0.007, 0.056), (0.028, 0, 0.007, 0.056),
                                         (0, 0.0245, 0.063, 0.007), (0, -0.0245, 0.063, 0.007))):
        parts.append(G.box(f"Buckle.{k}", front + np.array((dx, -0.007, dz)), (sx, 0.006, sz), metal, None, 0.0015))
    parts.append(G.box("BuckleTongue", front + np.array((0.008, -0.009, 0)), (0.04, 0.004, 0.005), metal, None,
                       0.001))

    def at(direction):
        d = np.array(direction, float)
        d /= np.linalg.norm(d)
        k = np.argmax(out[:, :2] @ d[:2])
        return ring[k], out[k]
    # pouch on the right hip
    p, n = at((-0.85, -0.45))
    fr = np.column_stack((np.cross((0, 0, 1), n) / np.linalg.norm(np.cross((0, 0, 1), n)), (0, 0, 1), n))
    centre = p + n * 0.028 + np.array((0, 0, -0.045))
    parts.append(G.box("Pouch", centre, (0.10, 0.12, 0.042), leather, fr, 0.012))
    parts.append(G.box("PouchFlap", centre + n * 0.022 + np.array((0, 0, 0.035)), (0.104, 0.055, 0.006),
                       leather, fr, 0.003))
    parts.append(G.box("PouchStud", centre + n * 0.027 + np.array((0, 0, 0.012)), (0.012, 0.012, 0.004),
                       metal, fr, 0.002))
    # three potion vials in leather loops on the left front, standing above the belt
    liquids = [(0.10, 0.65, 0.62), (0.85, 0.48, 0.10), (0.48, 0.20, 0.75)]
    for k, ang in enumerate((-0.35, -0.6, -0.85)):
        p, n = at((math.cos(ang), math.sin(ang)))
        c0 = p + n * 0.016 + np.array((0, 0, -0.035))
        parts += vial(f"Vial.{k}", c0, liquids[k], metal)
        loop = [c0 + np.array((0.0165 * math.cos(a), 0.0165 * math.sin(a), 0.035))
                for a in np.linspace(0, 2 * math.pi, 20, endpoint=False)]
        parts.append(G.flat_strap(f"VialLoop.{k}", loop, 0.03, 0.003, leather, closed=True,
                                  normal_hint=[q - np.array((c0[0], c0[1], q[2])) for q in loop]))
    for o in parts[1:]:
        G.bind_rigid(o, body, "DEF-spine")
    return parts


def vial(name, base, liquid_color, metal, h=0.088, r=0.0135):
    glass = G.glass(f"{name}.glass", (0.85, 0.93, 0.9), rough=0.12)
    liq_mat, nt, p = G._principled(f"{name}.liquid", liquid_color, 0.1)
    p.inputs["Transmission Weight"].default_value = 0.8
    p.inputs["Emission Color"].default_value = (*liquid_color, 1)
    p.inputs["Emission Strength"].default_value = 0.08
    prof = [(0.0, 0.0), (r * 0.9, 0.0), (r, 0.004), (r, h * 0.62), (r * 0.45, h * 0.78), (r * 0.42, h * 0.95),
            (r * 0.5, h)]
    body = G.lathe(name, prof, glass, 32, base)
    liq = G.lathe(f"{name}.liquid", [(0, 0.002), (r * 0.85, 0.003), (r * 0.88, h * 0.55), (0, h * 0.55)],
                  liq_mat, 24, base)
    cork_m = bpy.data.materials.get("Cork") or G._principled("Cork", (0.55, 0.40, 0.25), 0.9)[0]
    cork = G.lathe(f"{name}.cork", [(0, h * 0.9), (r * 0.42, h * 0.9), (r * 0.5, h + 0.012), (0, h + 0.013)],
                   cork_m, 16, base)
    return [body, liq, cork]


def apron_straps(body, grid, leather):
    """Neck strap: from each top corner of the bib up to the side of the neck, round the back of the
    neck (an ellipse; angle 90 degrees = straight behind), down to the other corner."""
    neck = body.head("DEF-spine.004")
    right, left = grid[0, 1], grid[0, -2]          # u = -1 is the character's right (x < 0)
    ny, nz, rx, ry = neck[1] + 0.008, neck[2] + 0.01, 0.068, 0.064
    angles = np.radians(np.linspace(215, -35, 26))
    arc = np.column_stack((rx * np.cos(angles), ny + ry * np.sin(angles),
                           nz + 0.015 * np.clip(np.sin(angles), 0, 1)))
    down_r = [right + (arc[0] - right) * t for t in np.linspace(0, 1, 8)[:-1]]
    down_l = [arc[-1] + (left - arc[-1]) * t for t in np.linspace(0, 1, 8)[1:]]
    pts = np.vstack([down_r, arc, down_l])
    out = pts - np.array((neck[0], ny, 0))
    out[:, 2] = 0.15
    strap = G.flat_strap("ApronStrap", pts, 0.026, 0.004, leather, normal_hint=out)
    G.bind(strap, body)
    return [strap]


def goggles(body, leather, metal):
    """Brass goggles pushed up on the forehead; the strap runs round the head over the hair."""
    eyes_z = material_centre(body.obj, "Iris")[2]
    zf = eyes_z + 0.072
    sl = body.V[np.abs(body.V[:, 2] - zf) < 0.012]       # only the head reaches this high
    c = (sl.min(axis=0) + sl.max(axis=0)) / 2
    ring = G.ring_outline(sl, c, zf, segments=64, pad=0.013)
    ymin, ymax = ring[:, 1].min(), ring[:, 1].max()
    ring[:, 2] -= 0.025 * (ring[:, 1] - ymin) / (ymax - ymin)
    out = ring - np.array((c[0], c[1], 0))
    out[:, 2] = 0
    out /= np.linalg.norm(out, axis=1, keepdims=True)
    parts = [G.flat_strap("GoggleStrap", ring, 0.022, 0.003, leather, closed=True, normal_hint=out)]
    lens_glass = G.glass("GoggleGlass", (0.75, 0.55, 0.25), 0.02)
    for sx in (1, -1):
        k = np.argmin(np.abs(ring[:, 0] - sx * 0.036) + (ring[:, 1] > c[1]) * 1.0)
        n = out[k] + np.array((0, 0, 0.8))
        n /= np.linalg.norm(n)
        centre = ring[k] + out[k] * 0.006
        fr = G.frame_from(n, (1, 0, 0))
        parts.append(G.lathe(f"GoggleRim.{sx}", [(0.017, 0), (0.024, 0.0), (0.025, 0.006), (0.023, 0.017),
                                                 (0.019, 0.019), (0.0175, 0.016)], metal, 40, centre, fr))
        parts.append(G.lathe(f"GoggleLens.{sx}", [(0, 0.014), (0.018, 0.014), (0.018, 0.015), (0, 0.016)],
                             lens_glass, 32, centre, fr))
    left, right = [p for p in parts if p.name.startswith("GoggleRim")]
    bridge = G.tube("GoggleBridge", [left.matrix_world.translation + Vector((-0.02, 0, 0.012)),
                                     (left.matrix_world.translation + right.matrix_world.translation) / 2
                                     + Vector((0, -0.008, 0.016)),
                                     right.matrix_world.translation + Vector((0.02, 0, 0.012))], 0.003, metal)
    parts.append(bridge)
    for o in parts:
        G.bind_rigid(o, body, "DEF-spine.006")
    return parts


def stage_dressed(samples):
    """The dressed figure in the A-pose: front, back, side, three-quarter, face (02-dressed.png)."""
    sc, cam = scene_setup(samples)
    obj, V = build_body()
    dress(obj)
    lo, hi = V.min(axis=0), V.max(axis=0)
    centre = (lo + hi) / 2
    h = hi[2] - lo[2]
    face = material_centre(obj, "Iris") + np.array((0.0, 0.0, -0.01))
    tmp = OUT / "_tiles"
    tmp.mkdir(parents=True, exist_ok=True)
    tiles = [
        shoot(sc, cam, tmp / "0.png", centre, (0, -1, 0.04), h * 1.75),
        shoot(sc, cam, tmp / "1.png", centre, (0, 1, 0.04), h * 1.75),
        shoot(sc, cam, tmp / "2.png", centre, (1, 0, 0.04), h * 1.75),
        shoot(sc, cam, tmp / "3.png", centre + np.array((0, 0, 0.25)), (-0.8, -1, 0.15), h * 1.2),
        shoot(sc, cam, tmp / "4.png", face, (0.4, -1, 0.1), 0.85, lens=70),
        shoot(sc, cam, tmp / "5.png", centre + np.array((0, 0, -0.05)), (0.3, -1, 0.1), 1.1, lens=50),
    ]
    sheet(tiles, OUT / "02-dressed.png", cols=3)


# ------------------------------------------------------------------------------------- bottle, poses
BOTTLE_R = 0.031          # radius of the bottle body where it is held
BOTTLE_HALF = 0.045       # half height of the cylindrical grip zone


def bottle():
    """Lio's sample bottle: a round-shouldered glass bottle with teal tincture and a cork.  Origin at
    the middle of the grip zone, axis = local Z."""
    import village.garments as G
    glass = G.glass("BottleGlass", (0.86, 0.95, 0.92), rough=0.03)
    liq, nt, p = G._principled("Tincture", (0.12, 0.62, 0.58), 0.05)
    p.inputs["Transmission Weight"].default_value = 0.9
    p.inputs["Emission Color"].default_value = (0.05, 0.5, 0.45, 1)
    p.inputs["Emission Strength"].default_value = 0.15
    r, b = BOTTLE_R, -0.06
    prof = [(0.0, b), (r * 0.85, b), (r, b + 0.008), (r, 0.035), (r * 0.82, 0.055), (0.012, 0.072),
            (0.011, 0.105), (0.0135, 0.108), (0.0135, 0.114), (0.0105, 0.115)]
    objs = [G.lathe("Bottle", prof, glass, 48)]
    objs.append(G.lathe("Bottle.liquid", [(0, b + 0.004), (r * 0.82, b + 0.005), (r * 0.9, b + 0.012),
                                          (r * 0.92, 0.03), (0, 0.03)], liq, 40))
    cork = bpy.data.materials.get("Cork") or G._principled("Cork", (0.55, 0.40, 0.25), 0.9)[0]
    objs.append(G.lathe("Bottle.cork", [(0, 0.098), (0.0098, 0.098), (0.0108, 0.122), (0, 0.123)], cork, 20))
    root = objs[0]
    for o in objs[1:]:
        o.parent = root
    for o in objs:
        o.data.shade_smooth()
        o.modifiers.new("Subdivision", "SUBSURF").levels = 1
    return root


def place(obj, centre, axis):
    z = Vector(axis).normalized()
    x = Vector((1, 0, 0)) if abs(z.x) < 0.9 else Vector((0, 1, 0))
    x = (x - z * x.dot(z)).normalized()
    m = Matrix((x, z.cross(x), z)).transposed().to_4x4()
    m.translation = Vector(centre)
    obj.matrix_world = m


def hold(rig, side, centre, axis, palm_normal, hint, cal, along_offset=0.022):
    """Arm IK and finger grip so the hand holds a bottle at `centre` (grip zone), axis `axis`, with the
    palm facing `palm_normal`.  Returns the measurements."""
    n = Vector(palm_normal).normalized()
    a = Vector(axis).normalized()
    n = (n - a * n.dot(a)).normalized()
    R = posing.grip_hand_rotation(a, n, cal)
    # knuckles relative to the wrist, from the rest pose of the hand
    hb = rig.data.bones[f"DEF-hand.{side}"]
    rest_inv = hb.matrix_local.to_3x3().inverted()
    kn = sum((rig.data.bones[f"DEF-palm.0{i}.{side}"].tail_local for i in range(1, 5)), Vector()) / 4
    k_local = rest_inv @ (kn - hb.head_local)
    along = Vector(R.col[1])
    K = Vector(centre) - n * (BOTTLE_R + 0.015) - along * along_offset
    wrist = K - R @ k_local
    info = posing.arm_ik(rig, side, wrist, R, hint)
    cyl = posing.Cylinder(centre, a, BOTTLE_R, BOTTLE_HALF)
    info["fingers"] = posing.curl_grip(rig, side, cyl, cal=cal)
    return info, cyl


POSES = {
    # holds the bottle up beside his face and looks through it
    "inspect": dict(side="R", centre=(-0.24, -0.32, 1.60), axis=(0.15, 0.0, 1.0), palm=(1.0, 0.1, 0.0),
                    hint=(-0.35, 0.25, -0.9), look=(-0.24, -0.32, 1.63), smile=0.0, other="relaxed"),
    # offers it to the customer at chest height
    "offer": dict(side="R", centre=(-0.07, -0.42, 1.30), axis=(0.0, 0.0, 1.0), palm=(1.0, 0.25, 0.0),
                  hint=(-0.6, 0.4, -0.7), look=(0.0, -2.0, 1.62), smile=0.75, other="relaxed"),
    # polishes it in both hands in front of the chest
    "polish": dict(side="L", centre=(0.03, -0.27, 1.22), axis=(-0.05, 0.1, 1.0), palm=(-1.0, -0.2, 0.0),
                   hint=(0.6, 0.4, -0.7), look=(0.03, -0.27, 1.22), smile=0.15, other="second"),
}


def set_expression(obj, weights):
    """ARKit face shapes of Reom as shape keys (created once)."""
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)
    for name, w in weights.items():
        kb = obj.data.shape_keys.key_blocks.get(name)
        if kb is None:
            kb = obj.shape_key_add(name=name, from_mix=False)
            idx, d = reom.expression(name)
            co = np.array([v.co[:] for v in obj.data.vertices])
            co[idx] += d
            kb.data.foreach_set("co", co.ravel())
        kb.value = w


def apply_pose(rig, obj, name, bottle_obj, cal):
    P = POSES[name]
    posing.reset(rig)
    # weight on the right leg, slight counter-turn of the chest
    posing.rotate(rig, "DEF-spine.003", (0, 0, 1), 4 if name != "polish" else 0)
    posing.rotate(rig, "DEF-spine.004", (1, 0, 0), -6 if name == "polish" else 0)
    side = P["side"]
    info, cyl = hold(rig, side, P["centre"], P["axis"], P["palm"], P["hint"], cal[side])
    place(bottle_obj, P["centre"], P["axis"])
    other = "L" if side == "R" else "R"
    if P["other"] == "second":
        # the free hand holds the upper part of the bottle from the other side
        c2 = Vector(P["centre"]) + Vector(P["axis"]).normalized() * 0.035
        info2, _ = hold(rig, other, c2, P["axis"], (-P["palm"][0], P["palm"][1], 0.0),
                        (-P["hint"][0], P["hint"][1], P["hint"][2]), cal[other], along_offset=0.03)
        info["second"] = info2
    else:
        sx = 1 if other == "L" else -1
        posing.rotate(rig, f"DEF-upper_arm.{other}", (0, 1, 0), sx * 12)
        posing.rotate(rig, f"DEF-forearm.{other}", (1, 0, 0), -14)
        posing.relaxed_hand(rig, other, cal=cal[other])
    posing.look_at(rig, P["look"])
    set_expression(obj, {"mouthSmileLeft": P["smile"], "mouthSmileRight": P["smile"],
                         "eyeSquintLeft": P["smile"] * 0.4, "eyeSquintRight": P["smile"] * 0.4})
    info["contact"] = posing.skin_contact(obj, reom.vertex_groups(), side, cyl)
    return info


def stage_poses(samples):
    """A-pose reference views plus the three market poses with the bottle (03-reference.png)."""
    import json
    sc, cam = scene_setup(samples)
    obj, V = build_body()
    rig, body, pieces = dress(obj)
    cal = {s: posing.calibrate(rig, s) for s in ("L", "R")}
    btl = bottle()
    lo, hi = V.min(axis=0), V.max(axis=0)
    centre = (lo + hi) / 2
    h = hi[2] - lo[2]
    face = material_centre(obj, "Iris") + np.array((0.0, 0.0, -0.015))
    tmp = OUT / "_tiles"
    tmp.mkdir(parents=True, exist_ok=True)
    tiles, report = [], {}
    # neutral A-pose: relaxed hands, bottle out of the way
    posing.reset(rig)
    for s in ("L", "R"):
        posing.relaxed_hand(rig, s, cal=cal[s])
    btl.location = (0, 0, -5)
    tiles.append(shoot(sc, cam, tmp / "a0.png", centre, (0, -1, 0.04), h * 1.75))
    tiles.append(shoot(sc, cam, tmp / "a1.png", centre, (0, 1, 0.04), h * 1.75))
    tiles.append(shoot(sc, cam, tmp / "a2.png", centre, (1, 0, 0.04), h * 1.75))
    tiles.append(shoot(sc, cam, tmp / "a3.png", face, (0.35, -1, 0.06), 0.6, lens=70))
    groups = reom.vertex_groups()
    for k, s in enumerate(("L", "R")):
        blo, bhi = hand_box(obj, groups, s)
        sx = 1 if s == "L" else -1
        tiles.append(shoot(sc, cam, tmp / f"a{4 + k}.png", (blo + bhi) / 2, (sx * 0.35, -1, 0.1),
                           float(np.linalg.norm(bhi - blo)) * 2.4, lens=70))
    for k, name in enumerate(POSES):
        report[name] = apply_pose(rig, obj, name, btl, cal)
        P = POSES[name]
        if name == "inspect":
            # hand with bottle, close
            tiles.append(shoot(sc, cam, tmp / "h.png", np.array(P["centre"]), (-0.9, -0.6, 0.1), 0.42, lens=70))
        side_view = 0.45 if name == "inspect" else -0.45     # never look through the bottle at the face
        tiles.append(shoot(sc, cam, tmp / f"p{k}.png", centre + np.array((0, 0, 0.25)), (side_view, -1, 0.12),
                           h * 1.15))
        if name == "polish":
            tiles.append(shoot(sc, cam, tmp / "h2.png", np.array(P["centre"]), (-0.3, -1, 0.35), 0.45, lens=70))
        if name == "offer":
            tiles.append(shoot(sc, cam, tmp / "f2.png", face, (-0.25, -1, 0.05), 0.6, lens=70))
    sheet(tiles, OUT / "03-reference.png", cols=4)
    (OUT / "03-reference.json").write_text(json.dumps(report, indent=1, default=lambda v: [round(x, 4) for x in v]))
    print(json.dumps(report, indent=1, default=lambda v: [round(x, 4) for x in v]))


def stage_face(samples):
    """Quick look at the head only: front, three-quarter, back (previews/lio/00-face.png)."""
    sc, cam = scene_setup(samples)
    obj, V = build_body()
    face = material_centre(obj, "Iris") + np.array((0.0, 0.0, -0.025))
    tmp = OUT / "_tiles"
    tmp.mkdir(parents=True, exist_ok=True)
    tiles = [
        shoot(sc, cam, tmp / "0.png", face, (0, -1, 0.02), 0.62, lens=70),
        shoot(sc, cam, tmp / "1.png", face, (0.75, -1, 0.05), 0.65, lens=70),
        shoot(sc, cam, tmp / "2.png", face + np.array((0, 0.03, 0.04)), (-0.7, 1, 0.45), 0.7, lens=70),
    ]
    sheet(tiles, OUT / "00-face.png", cols=3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="base")
    ap.add_argument("--samples", type=int, default=64)
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    OUT.mkdir(parents=True, exist_ok=True)
    {"base": stage_base, "face": stage_face, "dressed": stage_dressed, "poses": stage_poses}[args.stage](args.samples)


if __name__ == "__main__":
    main()
