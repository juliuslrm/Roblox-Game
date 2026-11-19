"""Builds the five market traders as realistic skinned characters for Roblox.

    python blender/build_characters.py [--no-render] [--only ROLE] [--tex 1024]

Per trader: a MakeHuman-based body with clothes, hair, face and the props in its hands (see
village/characters.py), bound to one skeleton.  Every mesh gets its own baked texture (colour x
procedural cloth / leather / skin detail x ambient occlusion).

Outputs
    exports/library/trader_<role>.fbx        rig + skinned meshes + textures (Roblox upload, one asset each)
    exports/textures/traders/*.png           baked textures
    roblox/gameplay/server/TraderArt.lua      bones, sizes, reference poses for the server check
    roblox/gameplay/shared/MarketMotion.lua   idle loops: local bone rotations per sample
    previews/market/01-haendler.png, 02-bewegung.png, 03-haende.png
Checks: grips (every finger on its prop), triangles per mesh (Roblox: 20 000), bone influences (4),
loops closed without jumps, props never pass through the body during the loops, back faces.
"""
import argparse
import json
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
from mathutils.bvhtree import BVHTree  # noqa: E402

from village import characters as C  # noqa: E402
from village import export, luadata  # noqa: E402
from village import scene as sc  # noqa: E402
from village import wardrobe as Wd  # noqa: E402

MESH_TRIANGLES = 19500            # Roblox imports at most 20 000 triangles per mesh
FPS = 8
TEX_DIR = ROOT / "exports/textures/traders"
# Blender (x, y, z) -> Roblox template frame (x, z, -y), as left by the asset loader
TO_ROBLOX = np.array(((1.0, 0, 0), (0, 0, 1.0), (0, -1.0, 0)))
BONE_NAME = {"root": "hips"}       # the MakeHuman 'root' is the hip bone; "Root" is the unweighted top bone
GROUPS = (("head", ("skin", "eyes", "lashes", "brows")),
          ("hair", ("hair", "beard", "braids", "hair_tie")),
          ("prop_L", ("prop_L",)), ("prop_R", ("prop_R",)))


def lin(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# ---------------------------------------------------------------- meshes
def split(piece, limit):
    """Pieces over the triangle limit are cut into consecutive face ranges."""
    if piece.triangles() <= limit:
        return [piece]
    out, faces, tris = [], [], 0
    for f in piece.faces:
        if tris + len(f) - 2 > limit:
            out.append(faces)
            faces, tris = [], 0
        faces.append(f)
        tris += len(f) - 2
    out.append(faces)
    parts = []
    for fs in out:
        used = sorted({v for f in fs for v in f})
        rm = {v: k for k, v in enumerate(used)}
        p = Wd.Piece(piece.name, piece.verts[used], [tuple(rm[v] for v in f) for f in fs], piece.weights[used],
                     piece.colors[used], piece.kind, piece.smooth)
        parts.append(p)
    return parts


def meshes_of(ch):
    """Groups the pieces of a character into meshes of at most MESH_TRIANGLES triangles:
    -> list of (mesh name, [pieces])."""
    taken, groups = set(), []
    for gname, names in GROUPS:
        members = [p for p in ch.pieces if p.name in names]
        taken |= {id(p) for p in members}
        groups.append((gname, members))
    groups.insert(2, ("wear", [p for p in ch.pieces if id(p) not in taken]))
    out = []
    for gname, members in groups:
        chunks, cur, tris = [], [], 0
        for p in members:
            for q in split(p, MESH_TRIANGLES):
                if tris + q.triangles() > MESH_TRIANGLES and cur:
                    chunks.append(cur)
                    cur, tris = [], 0
                cur.append(q)
                tris += q.triangles()
        if cur:
            chunks.append(cur)
        for k, c in enumerate(chunks):
            out.append((gname if len(chunks) == 1 else f"{gname}{k + 1}", c))
    return out


def top4(W, threshold=0.01):
    """Roblox skins with at most four bones per vertex."""
    W = W.copy()
    order = np.argsort(-W, axis=1)
    keep = np.zeros_like(W, dtype=bool)
    rows = np.arange(len(W))[:, None]
    keep[rows, order[:, :4]] = True
    W[~keep] = 0
    W[W < threshold] = 0
    s = W.sum(axis=1, keepdims=True)
    s[s == 0] = 1
    return W / s


# ---------------------------------------------------------------- materials
def detail_material(kind, image):
    """Bake source: vertex colour x procedural surface detail; `image` is the bake target."""
    mat = bpy.data.materials.new(f"src_{kind}")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    coord = nt.nodes.new("ShaderNodeTexCoord")

    def noise(scale, detail=4.0, distort=0.0):
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        if "Distortion" in n.inputs:
            n.inputs["Distortion"].default_value = distort
        nt.links.new(coord.outputs["Object"], n.inputs["Vector"])
        return n.outputs["Fac"]

    def wave(scale, axis):
        w = nt.nodes.new("ShaderNodeTexWave")
        w.wave_type = "BANDS"
        w.bands_direction = axis
        w.inputs["Scale"].default_value = scale
        w.inputs["Distortion"].default_value = 1.5
        nt.links.new(coord.outputs["Object"], w.inputs["Vector"])
        return w.outputs["Fac"]

    def span(src, lo, hi):
        m = nt.nodes.new("ShaderNodeMapRange")
        nt.links.new(src, m.inputs["Value"])
        m.inputs["To Min"].default_value = lo
        m.inputs["To Max"].default_value = hi
        return m.outputs["Result"]

    def multiply(a, b):
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1.0
        nt.links.new(a, mx.inputs[6])
        nt.links.new(b, mx.inputs[7])
        return mx.outputs[2]

    col = vc.outputs["Color"]
    if kind == "skin":
        col = multiply(col, span(noise(140.0, 6.0), 0.93, 1.05))
        col = multiply(col, span(noise(14.0, 2.0), 0.96, 1.03))
    elif kind == "cloth":
        col = multiply(col, span(wave(160.0, "X"), 0.9, 1.04))
        col = multiply(col, span(wave(160.0, "Z"), 0.92, 1.04))
        col = multiply(col, span(noise(9.0, 3.0), 0.9, 1.06))
    elif kind == "felt":
        col = multiply(col, span(noise(70.0, 6.0), 0.88, 1.06))
    elif kind == "leather":
        col = multiply(col, span(noise(55.0, 8.0, 0.4), 0.84, 1.08))
        col = multiply(col, span(noise(6.0, 2.0), 0.88, 1.06))
    elif kind == "hair":
        col = multiply(col, span(noise(260.0, 2.0), 0.82, 1.12))
    elif kind == "metal":
        col = multiply(col, span(noise(40.0, 6.0), 0.85, 1.1))
    elif kind.startswith("prop"):
        col = multiply(col, span(noise(36.0, 5.0), 0.9, 1.06))
    nt.links.new(col, bsdf.inputs["Base Color"])
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = image
    nt.nodes.active = img
    return mat


def final_material(name, image):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    return mat


def make_object(name, pieces, bones, scene):
    """Blender mesh object from pieces: vertex colours, one material slot per surface kind,
    vertex groups (top four weights)."""
    verts, faces, cols, W, kinds, smooth = [], [], [], [], [], []
    off = 0
    for p in pieces:
        verts.append(p.verts)
        cols.append(p.colors)
        W.append(p.weights)
        for f in p.faces:
            faces.append(tuple(i + off for i in f))
            kinds.append(p.kind)
            smooth.append(p.smooth)
        off += len(p.verts)
    V = np.vstack(verts)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], faces)
    me.polygons.foreach_set("use_smooth", smooth)
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    L = lin(np.vstack(cols))
    ca.data.foreach_set("color", np.c_[L, np.ones(len(L))].ravel())
    obj = bpy.data.objects.new(name, me)
    scene.collection.objects.link(obj)
    if not all(smooth):                                     # props: hard edges above 40 degrees
        me.set_sharp_from_angle(angle=math.radians(40))
    obj["kinds"] = json.dumps(kinds)
    Wt = top4(np.vstack(W))
    groups = {}
    for j, b in enumerate(bones):
        idx = np.nonzero(Wt[:, j])[0]
        if len(idx):
            g = groups.setdefault(b, obj.vertex_groups.new(name=BONE_NAME.get(b, b)))
            for i in idx:
                g.add([int(i)], float(Wt[i, j]), "REPLACE")
    return obj, Wt


def unwrap(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    uv = obj.data.uv_layers.new(name="UVMap")
    obj.data.uv_layers.active = uv
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_colour(obj, size):
    """Bakes vertex colour x surface detail into obj["albedo"]."""
    kinds = json.loads(obj["kinds"])
    names = sorted(set(kinds))
    albedo = bpy.data.images.new(obj.name + "_albedo", size, size)
    obj.data.materials.clear()
    mats = [detail_material(k, albedo) for k in names]
    for m in mats:
        obj.data.materials.append(m)
    obj.data.polygons.foreach_set("material_index", [names.index(k) for k in kinds])
    _select(obj)
    bpy.context.scene.cycles.samples = 8
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, margin=6, use_clear=True)
    return albedo, mats


def bake_ao(obj, size, mats):
    ao = bpy.data.images.new(obj.name + "_ao", size, size)
    for m in mats:
        m.node_tree.nodes.active.image = ao
    _select(obj)
    bpy.context.scene.cycles.samples = 24
    bpy.ops.object.bake(type="AO", margin=6, use_clear=True)
    return ao


def finish_texture(obj, albedo, ao, mats, ao_strength=0.62):
    size = albedo.size[0]
    a = np.array(albedo.pixels[:]).reshape(-1, 4)
    o = np.array(ao.pixels[:]).reshape(-1, 4)
    shade = 1 - ao_strength + ao_strength * np.clip(o[:, :1], 0, 1) ** 0.8
    out = bpy.data.images.new(obj.name, size, size)
    px = a.copy()
    px[:, :3] = a[:, :3] * shade
    px[:, 3] = 1
    out.pixels.foreach_set(px.astype(np.float32).ravel())
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    out.filepath_raw = str(TEX_DIR / f"{obj.name}.png")
    out.file_format = "PNG"
    out.save()
    obj.data.materials.clear()
    obj.data.materials.append(final_material(obj.name, out))
    obj.data.polygons.foreach_set("material_index", [0] * len(obj.data.polygons))
    for m in mats:
        bpy.data.materials.remove(m)
    bpy.data.images.remove(albedo)
    bpy.data.images.remove(ao)
    return out


def _select(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


# Ambient occlusion is baked with the arms held away from the body: in the rest pose the hands and
# props hang at the thighs and their shadows would stay on the skirts while the arms move.
BAKE_POSE = {"upperarm01.L": (0, -42, 0), "upperarm01.R": (0, 42, 0)}


_REST = {}


def set_pose(ch, objs, Ws, rots):
    """Moves the meshes into a pose (None = back to the rest pose)."""
    for obj, W in zip(objs, Ws):
        n = len(obj.data.vertices)
        if obj.name not in _REST:
            V = np.zeros(n * 3)
            obj.data.vertices.foreach_get("co", V)
            _REST[obj.name] = V.reshape(-1, 3)
        V = _REST[obj.name]
        P = posed_vertices(ch, W, V, rots) if rots else V
        obj.data.vertices.foreach_set("co", P.ravel())
        obj.data.update()


def make_armature(ch, scene):
    arm = bpy.data.armatures.new(f"trader_{ch.role}")
    obj = bpy.data.objects.new(f"trader_{ch.role}", arm)
    scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    root = arm.edit_bones.new("Root")
    root.head, root.tail = (0, 0, 0), (0, 0.0, 0.4)
    eb = {}
    for b in ch.bones:
        e = arm.edit_bones.new(BONE_NAME.get(b, b))
        e.head = tuple(ch.heads[b])
        tail = ch.tails[b]
        if np.linalg.norm(tail - ch.heads[b]) < 1e-3:
            tail = ch.heads[b] + np.array((0, 0, 0.05))
        e.tail = tuple(tail)
        eb[b] = e
    for b in ch.bones:
        p = ch.parents[b]
        eb[b].parent = eb[p] if p else root
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


# ---------------------------------------------------------------- motion
def _q(R):
    q = Matrix((TO_ROBLOX @ R @ TO_ROBLOX.T).tolist()).to_quaternion()
    return [round(q.x, 6), round(q.y, 6), round(q.z, 6), round(q.w, 6)]


def _keys(keys, dim=3):
    if dim == 3:
        return [[round(float(t), 4)] + [round(float(x), 4) for x in v] for t, v in keys]
    return [[round(float(t), 4), round(float(v), 4)] for t, v in keys]


CHECK_TIMES = {"idle": (0.0, 0.31, 0.5, 0.77), "idle2": (0.25, 0.5, 0.8)}      # fractions of the clip


def motion_data(ch):
    """Animation data of a trader for MarketMotion.lua: the clips as keys (MarketPose.lua evaluates them
    exactly like characters.py), the face poses (quaternion + move in the Roblox frame per face bone),
    and posed wrist positions at some clip times for the server check.  Also measures the largest hand
    step at 30 samples per second over every clip."""
    role = ch.role
    clips = {}
    for name in ("idle", "idle2", "greet"):
        cl = C.clip(role, name)
        clips[name] = {"duration": cl["duration"], "loop": cl["loop"], "additive": cl["additive"],
                       "keys": {c: _keys(k) for c, k in cl["keys"].items()},
                       "face": {f: _keys(k, 1) for f, k in cl["face"].items()}}
    poses = {}
    for name in C.FACE_POSES:
        rots, moves = C.face_pose(name)
        entry = {}
        for b in sorted(set(rots) | set(moves)):
            e = {"q": _q(rots.get(b, np.eye(3)))}
            if b in moves:
                e["p"] = [round(float(x), 5) for x in TO_ROBLOX @ moves[b]]
            entry[b] = e
        poses[name] = entry
    check, worst = [], 0.0

    def wrists(rots):
        mats = ch.body.bone_matrices(rots)
        return {s: (mats["wrist." + s] @ np.r_[ch.heads["wrist." + s], 1])[:3] for s in ("L", "R")}
    for name in ("idle", "idle2"):
        d = C.clip(role, name)["duration"]
        prev = None
        for i in range(int(d * 30) + 1):
            w = wrists(C.local_rotations(role, d * i / int(d * 30), name=name))
            if prev is not None:
                worst = max(worst, max(np.linalg.norm(w[s] - prev[s]) for s in w))
            prev = w
        for f in CHECK_TIMES[name]:
            t = round(d * f, 4)
            w = wrists(C.local_rotations(role, t, name=name))
            check.append({"clip": name, "t": t, "wristL": [round(float(x), 4) for x in TO_ROBLOX @ w["L"]],
                          "wristR": [round(float(x), 4) for x in TO_ROBLOX @ w["R"]]})
    t, g = 1.1, 0.55
    w = wrists(C.local_rotations(role, t, greet=g))
    check.append({"clip": "idle", "t": t, "greet": g, "wristL": [round(float(x), 4) for x in TO_ROBLOX @ w["L"]],
                  "wristR": [round(float(x), 4) for x in TO_ROBLOX @ w["R"]]})
    # the fastest intended move (the hammer tap) covers about 0.1 studs per 1/30 s
    assert worst < 0.25, f"{role}: a hand jumps {worst:.2f} studs between two samples (1/30 s)"
    return {"clips": clips, "poses": poses}, check, worst


def posed_vertices(ch, pieces_W, verts, rots):
    mats = ch.body.bone_matrices(rots)
    out = np.zeros_like(verts)
    vh = np.c_[verts, np.ones(len(verts))]
    for j, b in enumerate(ch.bones):
        w = pieces_W[:, j]
        nz = w > 0
        if nz.any():
            out[nz] += w[nz, None] * (vh[nz] @ mats[b].T)[:, :3]
    return out


def prop_clearance(ch):
    """Smallest signed distance of the props to the skin of the (nearly closed) body without clothes,
    over the whole loop; the arms that hold the props are left out.  Negative = inside the body."""
    body = ch.body
    names, W = body.dense_weights()
    assert names == ch.bones
    arm = W[:, [names.index(b) for b in names if b.startswith(("wrist", "lowerarm", "upperarm", "finger"))]].sum(axis=1) > 0.3
    faces = [body.faces[i] for i in body.face_ids("body")]
    faces = [f for f in faces if not arm[list(f)].any()]
    worst = (1e9, None)
    moments = []
    for name in ("idle", "idle2"):
        d = C.clip(ch.role, name)["duration"]
        moments += [(name, i / FPS, None) for i in range(0, int(d * FPS), 2)]
    moments += [("idle", 0.0, g) for g in (0.3, 0.55, 0.9)]          # greeting on top of the idle
    for name, t, g in moments:
        rots = C.local_rotations(ch.role, t, name=name, greet=g)
        P = posed_vertices(ch, W, body.verts, rots)
        bvh = BVHTree.FromPolygons([Vector(v) for v in P], [list(f) for f in faces], all_triangles=False)
        for prop in (p for p in ch.pieces if p.name.startswith("prop")):
            Q = posed_vertices(ch, prop.weights, prop.verts, rots)[::5]
            for q in Q:
                hit = bvh.find_nearest(Vector(q))
                if hit[0] is None:
                    continue
                d = Vector(q) - hit[0]
                s = d.length if d.dot(hit[1]) >= 0 else -d.length
                if s < worst[0]:
                    worst = (s, (prop.name, f"{name} {round(t, 2)}" + (f" greet {g}" if g else "")))
    return worst


# ---------------------------------------------------------------- main
def motion_only(role, problems, art, motion):
    """Animation data and reference poses without meshes, bake or export (fast check of the motion)."""
    ch = C.build(role)
    for p in C.grip_problems(ch.report):
        problems.append(f"{role}: {p}")
    mo, check, step = motion_data(ch)
    motion[role] = mo
    V = np.vstack([p.verts for p in ch.pieces])
    art[role] = {"height": round(float(V[:, 2].max()), 3), "meshes": [f"trader_{role}_{m}" for m, _ in meshes_of(ch)],
                 "check": check, "rig": f"trader_{role}"}
    print(f"[traders] {role}: motion only, largest hand step {step:.3f}", flush=True)


def build_role(role, tex, problems, art, motion):
    scene = bpy.context.scene
    ch = C.build(role)
    for p in C.grip_problems(ch.report):
        problems.append(f"{role}: {p}")
    arm = make_armature(ch, scene)
    objs, all_W = [], []
    tris = 0
    for mname, pieces in meshes_of(ch):
        obj, Wt = make_object(f"trader_{role}_{mname}", pieces, ch.bones, scene)
        n = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        tris += n
        if n > MESH_TRIANGLES:
            problems.append(f"{obj.name}: {n} triangles > {MESH_TRIANGLES}")
        if (Wt > 0).sum(axis=1).max() > 4:
            problems.append(f"{obj.name}: more than four bones on a vertex")
        objs.append(obj)
        all_W.append(Wt)
    for obj in objs:
        unwrap(obj)
    baked = [bake_colour(obj, tex if "prop" not in obj.name else tex // 2) for obj in objs]
    set_pose(ch, objs, all_W, {b: C._euler(a) for b, a in BAKE_POSE.items()})
    aos = [bake_ao(obj, img.size[0], mats) for obj, (img, mats) in zip(objs, baked)]
    set_pose(ch, objs, all_W, None)
    for obj, (img, mats), ao in zip(objs, baked, aos):
        finish_texture(obj, img, ao, mats)
    for obj in objs:
        obj.parent = arm
        mod = obj.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
    V = np.vstack([p.verts for p in ch.pieces])
    height = float(V[:, 2].max())
    clearance = prop_clearance(ch)
    if clearance[0] < -0.03:                    # 3 cm into the skin: a prop passes through the body
        problems.append(f"{role}: {clearance[1][0]} goes {-clearance[0]:.2f} studs into the body at t={clearance[1][1]} s")
    mo, check, step = motion_data(ch)
    motion[role] = mo
    art[role] = {"height": round(height, 3), "meshes": [o.name for o in objs], "check": check,
                 "rig": f"trader_{role}"}
    print(f"[traders] {role}: {len(objs)} meshes, {tris} triangles, {height:.2f} studs high, "
          f"prop clearance {clearance[0]:.3f} ({clearance[1]}), largest hand step {step:.3f}", flush=True)
    return arm, objs, ch


def export_rig(arm, objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for o in objs:
        o.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"}, global_scale=0.01,
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
        bake_space_transform=False, mesh_smooth_type="FACE", use_mesh_modifiers=False, add_leaf_bones=False,
        primary_bone_axis="Y", secondary_bone_axis="X", armature_nodetype="NULL", bake_anim=False,
        path_mode="COPY", embed_textures=True)


def render_lineup(rigs, out):
    scene = bpy.context.scene
    sc.setup_render(scene, res=(1920, 1080), samples=48)
    sc.setup_light(scene)
    poses = {"selma": 2.4, "nyra": 3.0, "lio": 4.0, "aron": 1.2, "esme": 3.4}
    shown = []
    for i, (role, (arm, objs, ch)) in enumerate(rigs.items()):
        shown += pose_copy(ch, objs, poses[role], (i * 3.4, 0, 0))
    sc.ground_plane(scene, 6000, color="cobble")
    cam = sc.add_camera(scene)
    lo, hi = np.min([o[1] for o in shown], axis=0), np.max([o[2] for o in shown], axis=0)
    sc.frame_bounds(cam, lo, hi, az=-90, el=6, aspect=1920 / 1080, lens=70, margin=0.62)
    sc.render(scene, out)
    for o, _, _ in shown:
        bpy.data.objects.remove(o)


def pose_copy(ch, objs, t, offset):
    """Copies of the meshes posed at loop time t (linear blend skinning), moved by offset."""
    rots = C.local_rotations(ch.role, t)
    out = []
    for obj in objs:
        me = obj.data.copy()
        n = len(me.vertices)
        V = np.zeros(n * 3)
        me.vertices.foreach_get("co", V)
        V = V.reshape(-1, 3)
        W = np.zeros((n, len(ch.bones)))
        names = {BONE_NAME.get(b, b): j for j, b in enumerate(ch.bones)}
        for v in me.vertices:
            for g in v.groups:
                W[v.index, names[obj.vertex_groups[g.group].name]] = g.weight
        P = posed_vertices(ch, W, V, rots) + np.asarray(offset)
        me.vertices.foreach_set("co", P.ravel())
        me.update()
        o = bpy.data.objects.new(obj.name + "_posed", me)
        bpy.context.scene.collection.objects.link(o)
        out.append((o, P.min(axis=0), P.max(axis=0)))
    return out


def render_motion(rigs, out):
    scene = bpy.context.scene
    sc.setup_render(scene, res=(1920, 1500), samples=32)
    shown = []
    for r, (role, (arm, objs, ch)) in enumerate(rigs.items()):
        duration = C.LOOPS[role]["duration"]
        for i in range(6):
            shown += pose_copy(ch, objs, duration * i / 6, (i * 3.2, r * 7.0, 0))
    cam = scene.camera
    lo, hi = np.min([o[1] for o in shown], axis=0), np.max([o[2] for o in shown], axis=0)
    sc.frame_bounds(cam, lo, hi, az=-90, el=30, aspect=1920 / 1500, lens=70, margin=0.56)
    sc.render(scene, out)
    for o, _, _ in shown:
        bpy.data.objects.remove(o)


def render_hands(rigs, out):
    """Close-ups of every held prop in the lineup pose, seen from the front and outside."""
    scene = bpy.context.scene
    cam = scene.camera
    poses = {"selma": 2.4, "nyra": 3.0, "lio": 4.0, "aron": 1.2, "esme": 3.4}
    tiles = []
    for role, (arm, objs, ch) in rigs.items():
        shown = pose_copy(ch, objs, poses[role], (0, 0, 0))
        rots = C.local_rotations(role, poses[role])
        mats = ch.body.bone_matrices(rots)
        for side, sx in (("L", 1.0), ("R", -1.0)):
            wrist = (mats["wrist." + side] @ np.r_[ch.heads["wrist." + side], 1])[:3]
            hand = (mats["wrist." + side] @ np.r_[ch.heads["wrist." + side] + np.array((0, 0, -0.3)), 1])[:3]
            target = (wrist + hand) / 2
            sc.aim(cam, tuple(target + np.array((sx * 1.1, -1.5, 0.45))), tuple(target))
            cam.data.lens = 85
            path = str(ROOT / f"world/_hand_{role}_{side}.png")
            scene.render.resolution_x, scene.render.resolution_y = 400, 400
            sc.render(scene, path)
            tiles.append(path)
        for o, _, _ in shown:
            bpy.data.objects.remove(o)
    # contact sheet with Blender's image API (no PIL in the Blender environment)
    W, Ht = 400 * 5, 400 * 2
    sheet = np.zeros((Ht, W, 4), dtype=np.float32)
    for k, path in enumerate(tiles):
        img = bpy.data.images.load(path)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(400, 400, 4)
        col, row = k // 2, k % 2
        sheet[Ht - (row + 1) * 400:Ht - row * 400, col * 400:(col + 1) * 400] = px
        bpy.data.images.remove(img)
        os.remove(path)
    img = bpy.data.images.new("hands", W, Ht)
    img.pixels.foreach_set(sheet.ravel())
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--tex", type=int, default=1024)
    ap.add_argument("--motion-only", action="store_true",
                    help="only MarketMotion.lua and TraderArt.lua (no meshes, bake, FBX or renders)")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    scene = export.new_scene()
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.bake.margin = 6
    problems, art, motion, rigs = [], {}, {}, {}
    roles = [args.only] if args.only else list(C.ROLES)
    for role in roles:
        if args.motion_only:
            motion_only(role, problems, art, motion)
            continue
        arm, objs, ch = build_role(role, args.tex, problems, art, motion)
        rigs[role] = (arm, objs, ch)
        export_rig(arm, objs, str(ROOT / f"exports/library/trader_{role}.fbx"))
        for o in objs:                       # the next trader is baked alone (ambient occlusion)
            o.hide_render = True
    if not args.only:
        bones = sorted(BONE_NAME.get(b, b) for b in C.ANIMATED)
        (ROOT / "roblox/gameplay/server/TraderArt.lua").write_text(
            "-- Generated by blender/build_characters.py. Do not edit.\n"
            "-- Skinned traders: rig model name, meshes, height; check = posed wrist positions (Roblox template\n"
            "-- frame, relative to the figure's ground point) at some times of the clips (greet = time in the\n"
            "-- additive greeting).\nreturn "
            + luadata.to_lua({"traders": art, "animated": bones}, inline_depth=4) + "\n", encoding="utf-8")
        channels = {c: [[BONE_NAME.get(b, b), share] for b, share in bones_] for c, bones_ in C.CHANNELS.items()}
        text = ("-- Generated by blender/build_characters.py. Do not edit.\n"
                "-- Animation of the traders, evaluated by MarketPose.lua exactly like blender/village/characters.py:\n"
                "-- clips (idle, idle2: loops that start in the same pose; greet: additive) with keys per channel\n"
                "-- {t, rx, ry, rz} (degrees, figure axes), face weights per expression {t, w}; channels -> bones;\n"
                "-- poses: per expression and face bone a local rotation q {x, y, z, w} and a move p (Roblox frame).\n"
                "-- A bone's Transform is  restRot^-1 * (figureRot * CFrame(p) * q * figureRot^-1) * restRot.\nreturn "
                + luadata.to_lua({"version": 2, "breath": C.BREATH, "channels": channels, "roles": motion},
                                 inline_depth=5) + "\n")
        (ROOT / "roblox/gameplay/shared/MarketMotion.lua").write_text(text, encoding="utf-8")
        size = len(text.encode())
        print(f"[traders] MarketMotion.lua {size} bytes")
        if size > 190_000:
            problems.append(f"MarketMotion.lua has {size} bytes (Roblox script limit 200 000)")
    if not args.no_render and not args.motion_only:
        render_lineup(rigs, str(ROOT / "previews/market/01-haendler.png"))
        render_motion(rigs, str(ROOT / "previews/market/02-bewegung.png"))
        render_hands(rigs, str(ROOT / "previews/market/03-haende.png"))
    for p in problems:
        print("  FAIL", p)
    print(f"trader checks: {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
