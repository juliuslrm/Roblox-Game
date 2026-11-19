"""Clothing for the Reom-based characters, built around the morphed body (metres, faces -Y, Z up).

Fitted garments (shirt, trousers, boots) are cut from the body surface where a scalar field is > 0:
faces crossing the zero line are clipped exactly on it, so hems are smooth curves and do not follow
the body's quads.  The cut surface is pushed out along the body normals (ease) and given thickness.
Hanging pieces (apron) are built on a grid that falls from the most forward point above it.

Every garment is bound to the character's rig by copying the skin weights of the nearest body
surface (Data Transfer), so it deforms with the body.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


# ---------------------------------------------------------------------------------------------- body
class Body:
    """Facts about the morphed body used to cut garments: positions, faces, normals, weights, bones."""

    def __init__(self, obj, rig, groups):
        me = obj.data
        self.obj, self.rig = obj, rig
        self.V = np.array([v.co[:] for v in me.vertices])
        self.faces = [tuple(p.vertices) for p in me.polygons]
        self.N = np.array([v.normal[:] for v in me.vertices])
        self.n = len(self.V)
        self.groups = groups
        self.bvh = surface_bvh(self.V, self.faces)

    def w(self, *prefixes):
        """Summed skin weight of every group whose name starts with one of the prefixes."""
        out = np.zeros(self.n)
        for name, (idx, wt) in self.groups.items():
            if name.startswith(prefixes):
                out[idx] += wt
        return out

    def head(self, bone):
        return np.array(self.rig.data.bones[bone].head_local[:])

    def tail(self, bone):
        return np.array(self.rig.data.bones[bone].tail_local[:])

    def arm_w(self, side):
        return self.w(f"DEF-upper_arm.{side}", f"DEF-forearm.{side}", f"DEF-hand.{side}") + self._fingers(side)

    def _fingers(self, side):
        out = np.zeros(self.n)
        for name, (idx, wt) in self.groups.items():
            if name.endswith(f".{side}") and name.startswith(("DEF-f_", "DEF-thumb", "DEF-palm")):
                out[idx] += wt
        return out

    def leg_w(self, side):
        return self.w(f"DEF-thigh.{side}", f"DEF-shin.{side}", f"DEF-foot.{side}", f"DEF-toe.{side}")

    def arm_chain(self, side):
        return [self.head(f"DEF-upper_arm.{side}"), self.head(f"DEF-forearm.{side}"),
                self.head(f"DEF-hand.{side}"), self.tail(f"DEF-hand.{side}")]

    def leg_chain(self, side):
        return [self.head(f"DEF-thigh.{side}"), self.head(f"DEF-shin.{side}"), self.head(f"DEF-foot.{side}"),
                self.head(f"DEF-toe.{side}"), self.tail(f"DEF-toe.{side}")]


def chain_param(P, pts, stops=None):
    """Arc-length parameter of the projection of every point onto a polyline, as a distance in
    metres from the first point (stops: None) ."""
    pts = [np.asarray(p, float) for p in pts]
    best_d = np.full(len(P), np.inf)
    best_t = np.zeros(len(P))
    acc = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        ab = b - a
        L = np.linalg.norm(ab)
        s = np.clip(((P - a) @ ab) / (L * L), 0, 1)
        q = a + s[:, None] * ab
        d = np.linalg.norm(P - q, axis=1)
        better = d < best_d
        best_d[better] = d[better]
        best_t[better] = acc + s[better] * L
        acc += L
    return best_t


# ------------------------------------------------------------------------------------------ surfaces
def clip_surface(body, field, offset):
    """(verts, faces) of the body surface where field > 0, clipped exactly at field = 0 and moved out
    along the vertex normals by `offset` (per body vertex)."""
    f = np.asarray(field, float)
    off = np.broadcast_to(np.asarray(offset, float), (body.n,))
    inside = f > 0
    rows, src, faces = {}, [], []

    def vid(key, a, b, t):
        if key not in rows:
            rows[key] = len(src)
            src.append((a, b, t))
        return rows[key]
    for fc in body.faces:
        if not inside[list(fc)].any():
            continue
        poly, n = [], len(fc)
        for k in range(n):
            a, b = fc[k], fc[(k + 1) % n]
            if inside[a]:
                poly.append(vid(a, a, a, 0.0))
            if inside[a] != inside[b]:
                poly.append(vid((min(a, b), max(a, b)), a, b, f[a] / (f[a] - f[b])))
        if len(poly) >= 3:
            faces.append(poly)
    ia = np.array([s[0] for s in src])
    ib = np.array([s[1] for s in src])
    t = np.array([s[2] for s in src])[:, None]
    P = body.V[ia] + (body.V[ib] - body.V[ia]) * t
    Nn = body.N[ia] + (body.N[ib] - body.N[ia]) * t
    Nn /= np.linalg.norm(Nn, axis=1, keepdims=True)
    o = (off[ia] + (off[ib] - off[ia]) * t[:, 0])[:, None]
    return P + Nn * o, faces


def mesh_object(name, verts, faces, material=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate()
    if smooth:
        me.shade_smooth()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    if material:
        me.materials.append(material)
    return obj


def relax(obj, iterations=6, factor=0.5, keep_boundary=True):
    """Laplacian smoothing of a garment surface (irons out small dents of the body underneath)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    verts = [v for v in bm.verts if not (keep_boundary and v.is_boundary)]
    for _ in range(iterations):
        new = {}
        for v in verts:
            nb = [e.other_vert(v).co for e in v.link_edges]
            if nb:
                c = sum(nb, Vector()) / len(nb)
                new[v] = v.co.lerp(c, factor)
        for v, co in new.items():
            v.co = co
    bm.to_mesh(obj.data)
    bm.free()


def surface_bvh(verts, faces):
    return BVHTree.FromPolygons([tuple(v) for v in verts], [tuple(f) for f in faces])


def obj_bvh(obj):
    """BVH of a garment's own surface (base mesh, modifiers ignored)."""
    me = obj.data
    return surface_bvh([v.co[:] for v in me.vertices], [p.vertices[:] for p in me.polygons])


def keep_outside(obj, layers, reach=0.03):
    """Pushes every vertex out to at least `gap` in front of each layer below it.
    layers: [(bvh, gap)]; a vertex counts as behind a layer when it is closer than gap on the side the
    nearest surface normal points away from, or inside it.  Only layers within `reach` count (a
    trouser leg is not pushed onto the far-away hem of the shirt)."""
    me = obj.data
    moved = 0
    for v in me.vertices:
        co = v.co.copy()
        for bvh, gap in layers:
            loc, nrm, _, dist = bvh.find_nearest(co, reach)
            if loc is None:
                continue
            side = (co - loc).dot(nrm)
            if side < gap:
                co = loc + nrm * gap
                moved += 1
        v.co = co
    me.update()
    return moved


def finish(obj, thickness=0.003, subdivide=1, rim=True):
    """Cloth thickness (outward), rolled hem edges and smoothing."""
    sol = obj.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness, sol.offset = thickness, -1.0
    sol.use_rim, sol.use_even_offset = rim, False    # even offset explodes on thin slivers
    if subdivide:
        sub = obj.modifiers.new("Subdivision", "SUBSURF")
        sub.levels = sub.render_levels = subdivide
    return obj


def bind(obj, body):
    """Skin weights from the nearest body surface, then deform with the rig."""
    for name in body.obj.vertex_groups.keys():
        obj.vertex_groups.new(name=name)
    dt = obj.modifiers.new("Weights", "DATA_TRANSFER")
    dt.object = body.obj
    dt.use_vert_data = True
    dt.data_types_verts = {"VGROUP_WEIGHTS"}
    dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"
    dt.layers_vgroup_select_dst = "NAME"
    obj.modifiers.move(obj.modifiers.find(dt.name), 0)
    with bpy.context.temp_override(object=obj, active_object=obj):
        bpy.ops.object.modifier_apply(modifier=dt.name)
    arm = obj.modifiers.new("Armature", "ARMATURE")
    arm.object = body.rig
    obj.modifiers.move(obj.modifiers.find("Armature"), 0)
    obj.parent = body.rig


# ----------------------------------------------------------------------------------------- materials
# Colours are given as sRGB (as picked on screen) and converted to Blender's linear values.
def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def _principled(name, color, rough, metal=0.0, sheen=0.0, coat=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    p = nt.nodes["Principled BSDF"]
    color = lin(color)
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Sheen Weight"].default_value = sheen
    p.inputs["Coat Weight"].default_value = coat
    return mat, nt, p


def _texcoord(nt, scale):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def fabric(name, color, weave_scale=900.0, rough=0.85, sheen=0.0, mottle=0.12, bump=0.25):
    """Woven cloth: colour mottling, fine crossing threads as bump."""
    mat, nt, p = _principled(name, color, rough, sheen=sheen)
    co = _texcoord(nt, 1.0)
    # mottling of the dye
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 18.0
    nz.inputs["Detail"].default_value = 6.0
    nt.links.new(co, nz.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs["Factor"].default_value = mottle
    mix.inputs["A"].default_value = (*lin(color), 1)
    nt.links.new(nz.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
    # threads: two wave textures at right angles
    waves = []
    for axis in ("X", "Z"):
        wv = nt.nodes.new("ShaderNodeTexWave")
        wv.wave_type, wv.bands_direction = "BANDS", axis
        wv.inputs["Scale"].default_value = weave_scale
        wv.inputs["Distortion"].default_value = 2.0
        wv.inputs["Detail"].default_value = 1.0
        nt.links.new(co, wv.inputs["Vector"])
        waves.append(wv)
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(waves[0].outputs["Fac"], add.inputs[0])
    nt.links.new(waves[1].outputs["Fac"], add.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.0004
    nt.links.new(add.outputs[0], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return mat


def leather(name, color, rough=0.5, grain=0.35, wear=0.25):
    """Leather: grain bump from Voronoi cells, darker creases, lighter worn spots."""
    mat, nt, p = _principled(name, color, rough)
    co = _texcoord(nt, 1.0)
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = 260.0
    nt.links.new(co, vo.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 28.0
    nz.inputs["Detail"].default_value = 10.0
    nz.inputs["Roughness"].default_value = 0.6
    nt.links.new(co, nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.3, 0.7
    ramp.color_ramp.elements[0].color = lin(tuple(c * 0.82 for c in color)) + (1,)
    ramp.color_ramp.elements[1].color = lin(tuple(min(1.0, c * (1 + wear * 0.5)) for c in color)) + (1,)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = grain
    bp.inputs["Distance"].default_value = 0.0006
    nt.links.new(vo.outputs["Distance"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return mat


def brass(name="Brass"):
    mat, nt, p = _principled(name, (0.90, 0.74, 0.45), 0.32, metal=1.0)
    co = _texcoord(nt, 1.0)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 40.0
    nt.links.new(co, nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.2, 0.5
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], p.inputs["Roughness"])
    return mat


def glass(name, color, rough=0.04):
    mat, nt, p = _principled(name, color, rough)
    p.inputs["Transmission Weight"].default_value = 1.0
    p.inputs["IOR"].default_value = 1.5
    return mat


# ------------------------------------------------------------------------------------------ garments
def edge_pin(obj, width=0.03):
    """1 at the open edges of a garment, falling to 0 at `width` metres from them."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    edge = [v.co.copy() for v in bm.verts if v.is_boundary]
    bm.free()
    tree = KDTree(len(edge))
    for i, co in enumerate(edge):
        tree.insert(co, i)
    tree.balance()
    return np.array([max(0.0, 1 - tree.find(v.co)[2] / width) for v in me.vertices])


def cinch(obj, pin, bvh, gap):
    """Pulls the held edges of a garment onto the surface below (a tucked hem, a cuff, a waistband):
    each vertex moves towards `gap` in front of the nearest surface by its pin weight.  The cloth in
    between keeps its length, so it bunches up in the simulation."""
    for v, w in zip(obj.data.vertices, pin):
        if w <= 0:
            continue
        loc, nrm, _, _ = bvh.find_nearest(v.co)
        if loc is not None:
            v.co = v.co.lerp(loc + nrm * gap, float(min(1.0, w)))
    obj.data.update()


def boundary_loops(obj):
    """Open edges of a mesh as ordered closed loops of positions."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    edges = [e for e in bm.edges if e.is_boundary]
    nb = {}
    for e in edges:
        a, b = e.verts
        nb.setdefault(a.index, []).append(b.index)
        nb.setdefault(b.index, []).append(a.index)
    co = {v.index: np.array(v.co[:]) for v in bm.verts}
    bm.free()
    loops, seen = [], set()
    for start in nb:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [n for n in nb[cur] if n != prev and n not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        if len(loop) > 8:
            loops.append(np.array([co[i] for i in loop]))
    return loops


def edge_band(name, loop, width, thickness, material, lift=0.0, centre=None):
    """A band along an open edge loop (collar, rolled cuff): width across the edge, outward from
    `centre` (a point or None = the loop's own centre)."""
    c = loop.mean(axis=0) if centre is None else np.asarray(centre, float)
    out = loop - c
    pts = loop + np.array((0, 0, lift))
    return flat_strap(name, pts, width, thickness, material, closed=True, normal_hint=out)


def shirt(body, material, sleeve_end=0.40, hem_drop=0.07, ease=0.007, sleeve_ease=0.012, drape=False,
          ease_on_top=0.004):
    """Linen shirt: tucked hem, open V collar, sleeves rolled to mid-forearm.  sleeve_end is the
    distance in metres from the shoulder joint along the arm."""
    z = body.V[:, 2]
    neck = body.head("DEF-spine.004")
    hip = body.head("DEF-thigh.L")[2]
    centre_y = body.head("DEF-spine.003")[1]
    f_hem = z - (hip - hem_drop)
    front = np.clip((centre_y - body.V[:, 1]) / 0.04, 0, 1)
    vee = 0.05 * np.clip(1 - np.abs(body.V[:, 0]) / 0.04, 0, 1) ** 1.3 * front
    f_neck = (neck[2] + 0.012 - vee) - z
    f = np.minimum(f_hem, f_neck)
    off = np.full(body.n, ease)
    for side in ("L", "R"):
        aw = body.arm_w(side)
        t = chain_param(body.V, body.arm_chain(side))
        f_arm = sleeve_end - t
        on = aw > 0.5
        f[on] = np.minimum(f[on], f_arm[on])
        off = np.maximum(off, ease + (sleeve_ease - ease) * np.clip(aw, 0, 1))
    # cloth rests on the shoulders and the top of the arms: little ease where the skin faces up
    up = np.clip(body.N[:, 2], 0, 1)
    off = off + (ease_on_top - off) * up ** 1.5
    leg = body.leg_w("L") + body.leg_w("R")
    f[leg > 0.6] = np.minimum(f[leg > 0.6], -0.01)
    verts, faces = clip_surface(body, f, off)
    obj = mesh_object("Shirt", verts, faces, material)
    relax(obj, 3, 0.4)
    keep_outside(obj, [(body.bvh, ease * 0.8)])
    if drape:
        pin = edge_pin(obj, 0.03)
        cinch(obj, pin ** 2, body.bvh, 0.003)
        simulate(obj, pin, frames=45, mass=0.15, tension=10, bending=0.05)
        keep_outside(obj, [(body.bvh, 0.003)])
    finish(obj, 0.0022)
    return obj


def trousers(body, material, under=(), waist_up=0.07, leg_end=0.80, ease=0.014, drape=False):
    """Wool trousers from above the hips into the boots (leg_end: metres from the hip joint)."""
    z = body.V[:, 2]
    top = body.head("DEF-thigh.L")[2] + waist_up
    f = top - z
    arms = body.arm_w("L") + body.arm_w("R")
    f[arms > 0.3] = -0.01
    for side in ("L", "R"):
        lw = body.leg_w(side)
        t = chain_param(body.V, body.leg_chain(side))
        on = lw > 0.5
        f[on] = np.minimum(f[on], leg_end - t[on])
    verts, faces = clip_surface(body, f, ease)
    obj = mesh_object("Trousers", verts, faces, material)
    relax(obj, 4, 0.5)
    keep_outside(obj, [(body.bvh, ease * 0.8)] + [(obj_bvh(u), 0.0045) for u in under])
    if drape:
        for u in under:
            collider(u, 0.003)
        pin = edge_pin(obj, 0.035)
        cinch(obj, pin ** 2, body.bvh, 0.009)
        simulate(obj, pin, frames=45, mass=0.25, tension=15, bending=0.15)
        keep_outside(obj, [(body.bvh, 0.005)] + [(obj_bvh(u), 0.008) for u in under])
    finish(obj, 0.003)
    return obj


def boots(body, material, under=(), shaft=0.60, ease=0.010, voxel=0.0055):
    """Leather boots to mid-calf.  The toes are merged into one toe box by a voxel remesh of the
    offset foot surface; the bottom is flattened into a sole."""
    out = []
    for side in ("L", "R"):
        lw = body.leg_w(side)
        t = chain_param(body.V, body.leg_chain(side))
        f = np.where(lw > 0.5, t - shaft, -0.01)
        verts, faces = clip_surface(body, f, ease + 0.006)
        obj = mesh_object(f"Boot.{side}", verts, faces, material)
        sol = obj.modifiers.new("Solid", "SOLIDIFY")
        sol.thickness, sol.offset = 0.008, -1
        rm = obj.modifiers.new("Remesh", "REMESH")
        rm.mode, rm.voxel_size = "VOXEL", voxel
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier="Solid")
            bpy.ops.object.modifier_apply(modifier="Remesh")
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        # cut the top open again at the shaft line (the remesh closed it)
        top = max(v.co.z for v in bm.verts)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, top - 0.006), plane_no=(0, 0, 1), clear_outer=True)
        # flat sole: everything below the sole height is pressed onto the floor plane
        floor = body.V[:, 2].min()
        for v in bm.verts:
            if v.co.z < floor + 0.012:
                v.co.z = floor + max(0.0, v.co.z - floor) * 0.25
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.shade_smooth()
        relax(obj, 24, 0.5, keep_boundary=False)
        keep_outside(obj, [(body.bvh, 0.008)] + [(obj_bvh(u), 0.006) for u in under])
        sm = obj.modifiers.new("Subdivision", "SUBSURF")
        sm.levels = sm.render_levels = 1
        out.append(obj)
    return out


def apron(body, material, top_below_neck=0.15, bottom=None, half_top=0.10, half_bottom=0.23,
          belt_z=None, gap=0.012, cols=36, rows=64, folds=4.5, fold_depth=0.007, drape=False):
    """Glassblower's leather apron from the chest to below the knees.  Every row hangs straight down
    from the most forward point of the body above it (it does not follow the belly or crotch), the
    width wraps round the body, and below the belt the leather falls in soft vertical folds."""
    neck = body.head("DEF-spine.004")
    z_top = neck[2] - top_below_neck
    z_bot = bottom if bottom is not None else body.head("DEF-shin.L")[2] - 0.02
    belt_z = belt_z if belt_z is not None else body.head("DEF-thigh.L")[2] + 0.045
    arms = body.arm_w("L") + body.arm_w("R")
    torso = body.V[arms < 0.2]
    zs = np.linspace(z_top, z_bot, rows)
    us = np.linspace(-1, 1, cols)

    def front(x, z, rx=0.02, rz=0.012):
        near = torso[(np.abs(torso[:, 0] - x) < rx) & (np.abs(torso[:, 2] - z) < rz)]
        return near[:, 1].min() if len(near) else np.nan
    centre = np.array([front(0.0, z, 0.10) for z in zs])
    ok = ~np.isnan(centre)
    centre = np.interp(np.arange(rows), np.flatnonzero(ok), centre[ok])
    hang = np.minimum.accumulate(centre)           # never further back than anything above it
    for _ in range(4):
        hang[1:-1] = np.minimum(hang[1:-1], (hang[:-2] + hang[1:-1] + hang[2:]) / 3)
    grid = np.zeros((rows, cols, 3))
    for r, z in enumerate(zs):
        k = (z - z_top) / (z_bot - z_top)
        # bib: narrow at the chest, an armhole curve out to the waist, then a slight flare
        s_arm = np.clip((z_top - 0.05 - z) / (z_top - 0.05 - belt_z), 0, 1)
        half = half_top + (half_bottom * 0.88 - half_top) * (1 - math.cos(s_arm * math.pi / 2)) ** 0.7
        half += half_bottom * 0.12 * np.clip((belt_z - z) / (belt_z - z_bot), 0, 1)
        below = np.clip((belt_z - z) / 0.12, 0, 1)    # 0 above the belt, 1 a hand below it
        wrap = 0.055 * (1 - below) + 0.03 * below
        for c, u in enumerate(us):
            x = u * half
            y = hang[r] + wrap * u * u - gap
            f = front(x, z)
            if not np.isnan(f):
                y = min(y, f - gap)
            y += fold_depth * below * math.sin((u + 1) * math.pi * folds) * (0.4 + 0.6 * k)
            grid[r, c] = (x, y, z)
    for _ in range(2):                              # soften kinks where the body pushed the leather
        y = grid[:, :, 1].copy()
        grid[1:-1, 1:-1, 1] = (y[1:-1, 1:-1] * 2 + y[:-2, 1:-1] + y[2:, 1:-1] + y[1:-1, :-2] + y[1:-1, 2:]) / 6
    # the hem swings a little: corners slightly higher
    grid[-1, :, 2] += 0.012 * us ** 2
    verts = grid.reshape(-1, 3)
    faces = [(r * cols + c, r * cols + c + 1, (r + 1) * cols + c + 1, (r + 1) * cols + c)
             for r in range(rows - 1) for c in range(cols - 1)]
    obj = mesh_object("Apron", verts, faces, material)
    keep_outside(obj, [(body.bvh, gap * 0.6)])
    if drape:
        z = np.array([v.co.z for v in obj.data.vertices])
        pin = np.clip(1 - (z_top - z) / 0.04, 0, 1) + np.clip(1 - np.abs(z - belt_z) / 0.03, 0, 1)
        simulate(obj, pin, frames=40, mass=0.6, tension=40, bending=4.0)   # the top edge stays put
    finish(obj, 0.004)
    return obj, grid


def tube(name, pts, radius, material, sides=10, closed=False):
    """A round strap / cord along a polyline."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = (*co, 1)
    sp.use_cyclic_u = closed
    cu.bevel_depth, cu.bevel_resolution = radius, max(1, sides // 4)
    obj = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(obj)
    cu.materials.append(material)
    return obj


def flat_strap(name, pts, width, thickness, material, closed=False, normal_hint=None):
    """A flat leather strap along a polyline: the strap's width lies along the surface (normal_hint
    gives the outward direction at each point)."""
    pts = np.asarray(pts, float)
    n = len(pts)
    verts, faces = [], []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        if closed:
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        tdir = (b - a) / np.linalg.norm(b - a)
        out = np.asarray(normal_hint[i], float)
        side = np.cross(tdir, out)
        side /= np.linalg.norm(side)
        out = np.cross(side, tdir)
        for s, o in ((-1, 0), (1, 0), (1, 1), (-1, 1)):
            verts.append(pts[i] + side * s * width / 2 + out * o * thickness)
    m = n if closed else n - 1
    for i in range(m):
        j = (i + 1) % n
        for k in range(4):
            faces.append((i * 4 + k, i * 4 + (k + 1) % 4, j * 4 + (k + 1) % 4, j * 4 + k))
    if not closed:
        faces.append((0, 1, 2, 3)[::-1])
        faces.append(tuple((n - 1) * 4 + k for k in range(4)))
    obj = mesh_object(name, verts, faces, material)
    return obj


def ring_outline(points, centre, z, segments=96, pad=0.0):
    """Outline of a point cloud around a vertical axis at height z: for every angle the farthest point
    within the slice, smoothed, plus pad."""
    rel = points - np.array((centre[0], centre[1], 0))
    ang = np.arctan2(rel[:, 1], rel[:, 0])
    rad = np.hypot(rel[:, 0], rel[:, 1])
    out = []
    for a in np.linspace(-math.pi, math.pi, segments, endpoint=False):
        d = np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi)
        sel = d < (2 * math.pi / segments) * 1.5
        out.append(rad[sel].max() if sel.any() else np.nan)
    out = np.array(out)
    ok = ~np.isnan(out)
    out = np.interp(np.arange(segments), np.flatnonzero(ok), out[ok], period=segments)
    for _ in range(3):
        out = np.maximum(out, (np.roll(out, 1) + out + np.roll(out, -1)) / 3)
    out += pad
    return np.array([(centre[0] + r * math.cos(a), centre[1] + r * math.sin(a), z)
                     for r, a in zip(out, np.linspace(-math.pi, math.pi, segments, endpoint=False))])


def box(name, centre, size, material, frame=None, bevel=0.004):
    """A bevelled box; frame: 3x3 rotation (columns = local x, y, z)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    me.materials.append(material)
    _place(obj, centre, frame)
    if bevel:
        bv = obj.modifiers.new("Bevel", "BEVEL")
        bv.width, bv.segments = bevel, 3
    me.shade_smooth()
    return obj


def lathe(name, profile, material, segments=48, centre=(0, 0, 0), frame=None):
    """Surface of revolution of a (radius, height) profile around the local z axis."""
    verts, faces = [], []
    n = len(profile)
    for k in range(segments):
        a = 2 * math.pi * k / segments
        for r, h in profile:
            verts.append((r * math.cos(a), r * math.sin(a), h))
    for k in range(segments):
        k2 = (k + 1) % segments
        for i in range(n - 1):
            faces.append((k * n + i, k2 * n + i, k2 * n + i + 1, k * n + i + 1))
    obj = mesh_object(name, verts, faces, material)
    _place(obj, centre, frame)
    return obj


def _place(obj, centre, frame):
    from mathutils import Matrix
    m = Matrix.Identity(4)
    if frame is not None:
        f = np.asarray(frame, float)
        for i in range(3):
            for j in range(3):
                m[i][j] = f[i, j]
    m.translation = Vector(centre)
    obj.matrix_world = m


def frame_from(z_axis, x_hint):
    z = np.asarray(z_axis, float)
    z /= np.linalg.norm(z)
    x = np.asarray(x_hint, float) - z * (np.asarray(x_hint, float) @ z)
    x /= np.linalg.norm(x)
    return np.column_stack((x, np.cross(z, x), z))


def bind_rigid(obj, body, bone):
    """Accessories that do not bend (buckle, vials, goggles) follow one bone.  The parent inverse is
    the bone's rest matrix, so the object keeps its place in the rest pose."""
    from mathutils import Matrix
    b = body.rig.data.bones[bone]
    rest = body.rig.matrix_world @ b.matrix_local @ Matrix.Translation((0, b.length, 0))
    basis = obj.matrix_world.copy()
    obj.parent = body.rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_parent_inverse = rest.inverted()
    obj.matrix_basis = basis


# ------------------------------------------------------------------------------------- cloth simulation
def collider(obj, thickness=0.004):
    mod = obj.modifiers.get("Collision") or obj.modifiers.new("Collision", "COLLISION")
    obj.collision.thickness_outer = thickness
    obj.collision.thickness_inner = 0.002
    obj.collision.cloth_friction = 8.0
    return mod


def simulate(obj, pin, frames=40, mass=0.3, tension=15.0, bending=0.5, shrink=0.0, quality=8,
             self_collision=False, pin_stiffness=1.0, subdivide_first=True):
    """Drapes a garment under gravity over the colliders in the scene and bakes the result into the
    mesh.  pin: weight per vertex (1 = held in place, e.g. waistband or collar)."""
    me = obj.data
    if subdivide_first:
        bm = bmesh.new()
        bm.from_mesh(me)
        layer = bm.verts.layers.float.new("pin")
        for v in bm.verts:
            v[layer] = float(pin[v.index])
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True, smooth=0.5)
        bmesh.ops.dissolve_degenerate(bm, dist=0.0005, edges=bm.edges[:])
        pin = [v[layer] for v in bm.verts]
        bm.to_mesh(me)
        bm.free()
        me.update()
    vg = obj.vertex_groups.new(name="pin")
    for i, w in enumerate(pin):
        if w > 0:
            vg.add([i], float(min(1.0, w)), "REPLACE")
    keep = [(m.name, m.show_viewport, m.show_render) for m in obj.modifiers]
    for m in obj.modifiers:
        m.show_viewport = m.show_render = False
    cl = obj.modifiers.new("Cloth", "CLOTH")
    obj.modifiers.move(obj.modifiers.find("Cloth"), 0)
    st = cl.settings
    st.quality = quality
    st.mass = mass
    st.tension_stiffness = st.compression_stiffness = tension
    st.shear_stiffness = tension * 0.5
    st.bending_stiffness = bending
    st.shrink_min = shrink
    st.vertex_group_mass = "pin"
    st.pin_stiffness = pin_stiffness
    cc = cl.collision_settings
    cc.distance_min = 0.003
    cc.use_self_collision = self_collision
    cc.self_distance_min = 0.002
    cl.point_cache.frame_start, cl.point_cache.frame_end = 1, frames
    sc = bpy.context.scene
    for f in range(1, frames + 1):
        sc.frame_set(f)
    with bpy.context.temp_override(object=obj, active_object=obj):
        bpy.ops.object.modifier_apply(modifier="Cloth")
    sc.frame_set(1)
    for name, vp, rd in keep:
        m = obj.modifiers.get(name)
        if m:
            m.show_viewport, m.show_render = vp, rd
    obj.vertex_groups.remove(obj.vertex_groups["pin"])
    return obj
