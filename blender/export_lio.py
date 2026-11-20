"""Lio for Roblox: rig, meshes, textures and animation keys from the reference build (build_lio.py).

    /opt/bpyenv/bin/python blender/export_lio.py -- [--motion-only] [--tex 1024] [--no-render]

Animation: key poses are solved in Blender (arm IK, finger grips with contact check), then turned into
keys per bone in the format MarketPose.lua evaluates (Euler degrees in figure axes, monotone cubic
between keys).  The export's rest pose is the polishing pose, so a figure whose animation is paused
(far from the camera) still stands naturally.  A Python evaluator of the same format checks that the
keys reproduce the solved poses (forward kinematics) and that the bottle never goes into the body.

Writes exports/library/trader_lio.json (motion + art entry, merged by build_characters.py into
MarketMotion.lua and TraderArt.lua) and, unless --motion-only, exports/library/trader_lio.fbx.
"""
import argparse
import copy
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE)]

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import bmesh  # noqa: E402

import build_lio as L  # noqa: E402
from build_characters import MESH_TRIANGLES, TEX_DIR, export_rig, final_material  # noqa: E402
from village import characters as C  # noqa: E402
from village import hair, posing, reom  # noqa: E402

OUT_JSON = ROOT / "exports/library/trader_lio.json"
OUT_FBX = ROOT / "exports/library/trader_lio.fbx"
PREVIEW = ROOT / "previews/lio"
CHECKPOINT = None                 # --checkpoint: the scene before baking is saved there (for debugging)
STUDS = 1 / 0.28                  # Roblox: 1 stud = 0.28 m (the old traders are about 6.5 studs tall)
TO_ROBLOX = np.array(((1.0, 0, 0), (0, 0, 1.0), (0, -1.0, 0)))
RIG = {"breath": "DEF-spine.002", "neck": "DEF-spine.005", "head": "DEF-spine.006",
       "eyes": ["DEF-eye.L", "DEF-eye.R"], "wrists": {"L": "DEF-hand.L", "R": "DEF-hand.R"}}

# key poses: (pose of build_lio.POSES, changes)
KEY_POSES = {
    "polish": ("polish", {}),
    "polish_rub": ("polish", {"second_up": 0.062}),
    "inspect": ("inspect", {}),
    "inspect_turn": ("inspect", {"axis": (0.42, 0.32, 1.0), "look": (-0.25, -0.29, 1.57)}),
    "offer": ("offer", {}),
    "offer_hold": ("offer", {"centre": (-0.05, -0.43, 1.32), "look": (0.25, -2.0, 1.6)}),
}
# clips: (time, key pose); loops start and end in the rest pose (polish)
CLIPS = {
    "idle": dict(duration=8.4, loop=True, additive=False,
                 keys=[(0.0, "polish"), (0.9, "polish_rub"), (1.8, "polish"), (2.7, "polish_rub"), (3.6, "polish"),
                       (5.0, "inspect"), (6.0, "inspect_turn"), (7.0, "inspect"), (8.4, "polish")],
                 face={}),
    "idle2": dict(duration=7.0, loop=True, additive=False,
                  keys=[(0.0, "polish"), (1.6, "offer"), (3.8, "offer_hold"), (5.4, "offer"), (7.0, "polish")],
                  face={"smile": [(0.0, 0.0), (1.4, 0.0), (2.0, 0.6), (5.2, 0.6), (6.0, 0.0), (7.0, 0.0)]}),
}
# additive greeting: a nod and a smile (degrees in figure axes; +X tips the head forward)
GREET = dict(duration=2.4, loop=False, additive=True,
             keys={"DEF-spine.006": [(0.0, (0, 0, 0)), (0.55, (10, 0, 0)), (1.2, (0, 0, 0)), (2.4, (0, 0, 0))],
                   "DEF-spine.003": [(0.0, (0, 0, 0)), (0.6, (3, 0, 0)), (1.3, (0, 0, 0)), (2.4, (0, 0, 0))]},
             face={"smile": [(0.0, 0.0), (0.5, 1.0), (1.9, 1.0), (2.4, 0.0)],
                   "brows_up": [(0.0, 0.0), (0.3, 0.6), (0.9, 0.0), (2.4, 0.0)]})


# ------------------------------------------------------------------------------------------ poses
def merged(name):
    base, change = KEY_POSES[name]
    P = copy.deepcopy(L.POSES[base])
    P.update(change)
    return base, P


def solve_key_poses(rig, obj, btl, cal):
    """Bone orientations (armature space, 3x3) per key pose, plus grip measurements and the bottle's
    place relative to the right hand (must be the same in every pose: the bottle is skinned to it)."""
    poses, report, in_hand = {}, {}, {}
    for name in KEY_POSES:
        base, P = merged(name)
        info = L.apply_pose(rig, obj, base, btl, cal, P=P, eyes=False, face=False)
        poses[name] = {b.name: b.matrix.to_3x3().copy() for b in rig.pose.bones}
        hand = rig.pose.bones["DEF-hand.R"].matrix
        in_hand[name] = hand.inverted() @ btl.matrix_world
        report[name] = {"deepest_mm": info["contact"]["deepest_mm"], "palm_turn": info["palm_turn"],
                        "touching": [f for f, x in info["fingers"].items() if x["touch"]],
                        "wrist_bend": round(info["wrist_bend"], 1)}
        if "second" in info:
            report[name]["second_touching"] = [f for f, x in info["second"]["fingers"].items() if x["touch"]]
    ref = in_hand["polish"]
    drift = max(max((m.translation - ref.translation).length for m in in_hand.values()) * 1000, 0)
    return poses, report, drift


def local_deltas(rig, poses, rest):
    """Per key pose and bone the rotation q (figure axes) the runtime applies on top of the parent:
    D = posed @ rest^-1 is a bone's accumulated rotation, q = D_parent^-1 @ D."""
    out = {}
    for name, M in poses.items():
        D = {b: M[b] @ rest[b].inverted() for b in M}
        q = {}
        for bone in rig.data.bones:
            parent = bone.parent.name if bone.parent else None
            Dp = D[parent] if parent else Matrix.Identity(3)
            q[bone.name] = Dp.inverted() @ D[bone.name]
        out[name] = q
    return out


def angle_of(m):
    return math.degrees(m.to_quaternion().angle)


def build_keys(deltas):
    """Channels (one per moving bone) and Euler keys per clip; Euler angles are kept continuous from
    key to key."""
    moving = sorted(b for b in deltas["polish"]
                    if any(angle_of(deltas[k][b]) > 0.05 for k in deltas) and b not in RIG["eyes"])
    clips = {}
    for cname, cl in CLIPS.items():
        keys = {}
        for b in moving:
            prev, track = None, []
            for t, kp in cl["keys"]:
                e = deltas[kp][b].to_euler("XYZ", prev) if prev else deltas[kp][b].to_euler("XYZ")
                prev = e
                track.append((t, tuple(math.degrees(a) for a in e)))
            keys[b] = track
        clips[cname] = {"duration": cl["duration"], "loop": cl["loop"], "additive": False, "keys": keys,
                        "face": cl["face"]}
    clips["greet"] = {"duration": GREET["duration"], "loop": False, "additive": True, "keys": GREET["keys"],
                      "face": GREET["face"]}
    channels = {b: [[b, 1]] for b in sorted(set(moving) | set(GREET["keys"]) | rig_bones())}
    return channels, clips


def rig_bones():
    """Bones the runtime must register even without keys: breathing, and the look turn on neck and head
    (the client and the server check only touch bones that some channel names)."""
    return {RIG["breath"], RIG["neck"], RIG["head"]}


# ------------------------------------------------------------------------------- python evaluator
def evaluate(channels, clips, clip, t, greet=None, breath=True):
    """Same as MarketPose.evaluate: bone -> 3x3 rotation (figure axes) relative to the parent."""
    cl = clips[clip]
    if cl["loop"]:
        t = t % cl["duration"]
    out = {}
    for ch, bones in channels.items():
        a = C.clip_angles(cl, ch, t) if ch in cl["keys"] else (0.0, 0.0, 0.0)
        if greet is not None and ch in clips["greet"]["keys"]:
            g = C.clip_angles(clips["greet"], ch, greet)
            a = tuple(a[i] + g[i] for i in range(3))
        for bone, share in bones:
            out[bone] = C._euler(tuple(x * share for x in a))
    if breath:
        bb = RIG["breath"]
        out[bb] = out.get(bb, np.eye(3)) @ C.H.rot((1, 0, 0), -C.breath_angle(cl["duration"], t))
    return out


class Skeleton:
    """Forward kinematics of the rest (export) skeleton: head positions and accumulated rotations."""

    def __init__(self, rig):
        self.order = [b.name for b in rig.data.bones]       # parents come before children
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
        self.head = {b.name: np.array(rig.pose.bones[b.name].head) for b in rig.data.bones}

    def fk(self, q):
        D, P = {}, {}
        for b in self.order:
            p = self.parent[b]
            Dp = D[p] if p else np.eye(3)
            P[b] = (P[p] + Dp @ (self.head[b] - self.head[p])) if p else self.head[b]
            D[b] = Dp @ np.asarray(q.get(b, np.eye(3)))
        return D, P


def ground_point(V):
    """Figure origin: between the feet on the floor."""
    feet = V[V[:, 2] < 0.04]
    return np.array((feet[:, 0].mean(), feet[:, 1].mean(), V[:, 2].min()))


def check_keys(skel, channels, clips, poses_heads):
    """Largest distance (mm) between the evaluated skeleton at the key times and the solved poses."""
    worst = 0.0
    for cname, cl in CLIPS.items():
        for t, kp in cl["keys"]:
            _, P = skel.fk(evaluate(channels, clips, cname, t, breath=False))
            for b, h in poses_heads[kp].items():
                worst = max(worst, float(np.linalg.norm(P[b] - h)) * 1000)
    return worst


def lbs(weights, rest_V, D, P, skel):
    """Linear blend skinning in numpy: weights = [(bone, idx, w)]."""
    out = np.zeros_like(rest_V)
    for b, idx, w in weights:
        out[idx] += w[:, None] * (P[b] + (rest_V[idx] - skel.head[b]) @ D[b].T)
    return out


def bottle_clearance(skel, channels, clips, body_V, body_F, body_W, bottle_V):
    """Deepest point of the bottle inside the body over every clip (mm, 15 samples per second)."""
    worst, where = 0.0, None
    for cname in ("idle", "idle2"):
        d = clips[cname]["duration"]
        for i in range(int(d * 15) + 1):
            t = d * i / int(d * 15)
            D, P = skel.fk(evaluate(channels, clips, cname, t))
            V = lbs(body_W, body_V, D, P, skel)
            bvh = BVHTree.FromPolygons([tuple(v) for v in V], body_F)
            hb = "DEF-hand.R"
            B = P[hb] + (bottle_V - skel.head[hb]) @ D[hb].T
            for p in B[::7]:
                # within 4 cm of the skin only: the body mesh is open where the hands were taken out, and
                # far from it the nearest face can point away from a point that is outside
                loc, nrm, _, dist = bvh.find_nearest(Vector(p), 0.04)
                if loc is not None and (Vector(p) - loc).dot(nrm) < 0 and dist > worst:
                    worst, where = dist, (cname, round(t, 2))
    return worst * 1000, where


# ------------------------------------------------------------------------------------------ meshes
HEAD_MATERIALS = ("Face", "Mouth", "Tongue", "Gums", "Teeth", "Sclera_Cornea", "Iris", "Pupil")
WEAR_BUDGET = {"Shirt": 9000, "Trousers": 9000, "Apron": 6000, "Boot.L": 3500, "Boot.R": 3500}


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def frozen(o, dg, bone=None):
    """A new mesh object with the evaluated shape of o in world space (pose, solidify; no subdivision),
    keeping its vertex groups; rigid parts (bone) get all their vertices on that bone."""
    for m in getattr(o, "modifiers", []):
        if m.type in ("SUBSURF", "COLLISION"):
            m.show_viewport = False
    dg.update()
    e = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(e, preserve_all_data_layers=True, depsgraph=dg)
    me.transform(o.matrix_world)
    name, groups = o.name, [vg.name for vg in getattr(o, "vertex_groups", [])]
    o.name = name + ".src"
    new = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(new)
    for g in groups:
        new.vertex_groups.new(name=g)
    if bone:
        vg = new.vertex_groups.get(bone) or new.vertex_groups.new(name=bone)
        vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    return new


def hide_covered_skin(body, cover, head_slots):
    """Deletes body faces that lie completely under clothing: a vertex is covered when a ray along its
    normal meets a garment within 8 cm; a face goes when all its vertices and their neighbours are
    covered (one ring of margin, so no gap opens at a hem)."""
    me = body.data
    covered = np.zeros(len(me.vertices), bool)
    for v in me.vertices:
        n = v.normal
        for bvh in cover:
            hit = bvh.ray_cast(v.co + n * 0.002, n, 0.08)
            if hit[0] is not None:
                covered[v.index] = True
                break
    nb = [[] for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices
        nb[a].append(b)
        nb[b].append(a)
    removable = covered & np.array([covered[n].all() if n else False for n in nb])
    bm = bmesh.new()
    bm.from_mesh(me)
    gone = [f for f in bm.faces if f.material_index not in head_slots and all(removable[v.index] for v in f.verts)]
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    bm.to_mesh(me)
    bm.free()
    return len(gone)


def cornea_faces(src):
    """Indices of the faces of the eyeball shell (sclera and cornea) in front of each iris, found on the
    undeformed mesh (eyes looking along -Y).  They are removed so the baked eye shows the iris (in the
    game the shell is opaque)."""
    me = src.data
    iris, sclera = reom.MATERIALS.index("Iris"), reom.MATERIALS.index("Sclera_Cornea")
    co = np.array([v.co[:] for v in me.vertices])
    out = []
    for sx in (1, -1):
        iv = co[sorted({v for p in me.polygons if p.material_index == iris for v in p.vertices if co[v][0] * sx > 0})]
        c = iv.mean(axis=0)
        r = np.hypot(iv[:, 0] - c[0], iv[:, 2] - c[2]).max()
        for p in me.polygons:
            if p.material_index != sclera:
                continue
            P = co[list(p.vertices)]
            if (P[:, 0] * sx > 0).all() and (np.hypot(P[:, 0] - c[0], P[:, 2] - c[2]) < r * 1.08).all() \
                    and (P[:, 1] < c[1] + 0.0005).all():
                out.append(p.index)
    return out


def delete_faces(o, idx):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in idx], context="FACES")
    bm.to_mesh(o.data)
    bm.free()


def split_faces(o, keep, name):
    """A copy of o with only the faces where keep(polygon) is true; those faces are removed from o."""
    c = o.copy()
    c.data = o.data.copy()
    c.name = name
    bpy.context.scene.collection.objects.link(c)
    for obj, want in ((c, True), (o, False)):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        idx = [p.index for p in obj.data.polygons if bool(keep(p)) != want]
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in idx], context="FACES")
        bm.to_mesh(obj.data)
        bm.free()
    return c


def hair_cap(body, mask, offset=0.007):
    """Short coily hair as a shell over the scalp (the strands are too many for the game): the scalp
    faces moved out along their normals, with the mask as vertex colour (soft hairline in the alpha)."""
    me = body.data
    face_slot = reom.MATERIALS.index("Face")
    faces = [p for p in me.polygons if p.material_index == face_slot and mask[list(p.vertices)].max() > 0.15]
    used = sorted({v for p in faces for v in p.vertices})
    remap = {v: k for k, v in enumerate(used)}
    V = np.array([(me.vertices[v].co + me.vertices[v].normal * offset * min(1.0, mask[v] * 2.5 + 0.2))[:]
                  for v in used])
    cap = bpy.data.meshes.new("hair")
    cap.from_pydata([tuple(v) for v in V], [], [tuple(remap[v] for v in p.vertices) for p in faces])
    cap.shade_smooth()
    obj = bpy.data.objects.new("hair", cap)
    bpy.context.scene.collection.objects.link(obj)
    col = cap.color_attributes.new("mask", "FLOAT_COLOR", "POINT")
    m = np.clip((mask[used] - 0.15) / 0.5, 0, 1)
    col.data.foreach_set("color", np.c_[m, m, m, np.ones(len(m))].ravel().astype(np.float32))
    for vg in body.vertex_groups:
        obj.vertex_groups.new(name=vg.name)
    for k, v in enumerate(used):
        for g in me.vertices[v].groups:
            obj.vertex_groups[g.group].add([k], g.weight, "REPLACE")
    mat = bpy.data.materials.new("HairCap")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 700.0
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 160.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.004, 0.003, 0.0027, 1)
    ramp.color_ramp.elements[1].color = (0.018, 0.013, 0.010, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.0015
    nt.links.new(vo.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.95          # coily hair is nearly matt
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "mask"
    nt.links.new(attr.outputs["Fac"], bsdf.inputs["Alpha"])
    cap.materials.append(mat)
    # the scalp faces are large: two smoothed subdivisions give the cap a round silhouette (weights and
    # the mask colour are interpolated)
    sub = obj.modifiers.new("Round", "SUBSURF")
    sub.levels = 2
    with bpy.context.temp_override(object=obj, active_object=obj):
        bpy.ops.object.modifier_apply(modifier=sub.name)
    return obj


def decimate(o, target):
    n = tris(o)
    if n <= target:
        return n
    mod = o.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = target / n
    mod.use_collapse_triangulate = True
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return tris(o)


def join(objs, name):
    target = objs[0]
    with bpy.context.temp_override(object=target, active_object=target, selected_objects=objs,
                                   selected_editable_objects=objs):
        bpy.ops.object.join()
    target.name = name
    target.data.name = name
    return target


def pack(objs, limit=MESH_TRIANGLES):
    """Objects into groups of at most `limit` triangles (largest first)."""
    bins = []
    for o in sorted(objs, key=tris, reverse=True):
        for b in bins:
            if sum(tris(x) for x in b) + tris(o) <= limit:
                b.append(o)
                break
        else:
            bins.append([o])
    return bins


def clean_weights(o, bones, limit=4, floor=0.001):
    """Roblox skins with at most four bones per vertex: groups of unknown bones are dropped, every
    vertex keeps its four strongest weights (normalised).  Returns (most bones on a vertex, vertices
    without weight)."""
    for vg in list(o.vertex_groups):
        if vg.name not in bones:
            o.vertex_groups.remove(vg)
    groups = o.vertex_groups
    drop = {}
    for v in o.data.vertices:
        ws = sorted(((g.weight, g.group) for g in v.groups if g.weight > floor), reverse=True)
        keep = ws[:limit]
        total = sum(w for w, _ in keep)
        for w, gi in keep:
            groups[gi].add([v.index], w / total, "REPLACE")
        for g in v.groups:
            if g.group not in {gi for _, gi in keep}:
                drop.setdefault(g.group, []).append(v.index)
    for gi, idx in drop.items():
        groups[gi].remove(idx)
    most = max((len(v.groups) for v in o.data.vertices), default=0)
    bare = sum(1 for v in o.data.vertices if not v.groups)
    return most, bare


# ------------------------------------------------------------------------------------------- bake
def _principled(mat):
    return [n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"] if mat and mat.node_tree else []


def _target(o, img):
    for m in o.data.materials:
        nt = m.node_tree
        node = nt.nodes.get("BakeTarget") or nt.nodes.new("ShaderNodeTexImage")
        node.name = "BakeTarget"
        node.image = img
        nt.nodes.active = node


def _bake(o, kind, img, samples, **kw):
    _target(o, img)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.context.scene.cycles.samples = samples
    bpy.ops.object.bake(type=kind, margin=8, use_clear=True, **kw)


def _emit_value(m, value_of):
    """Rewires a material to emit a grey value (for metalness and alpha bakes)."""
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output)
    em = nt.nodes.new("ShaderNodeEmission")
    v = value_of(m, nt)
    if isinstance(v, float):
        em.inputs["Color"].default_value = (v, v, v, 1)
    else:
        nt.links.new(v, em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])


def metal_of(m, nt):
    p = _principled(m)
    return float(p[0].inputs["Metallic"].default_value) if p and not p[0].inputs["Metallic"].is_linked else 0.0


def alpha_of(m, nt):
    p = _principled(m)
    if not p:
        return 1.0
    a = p[0].inputs["Alpha"]
    if a.is_linked:
        return a.links[0].from_socket
    if "lass" in m.name:                 # the glass materials (bottle, vials, goggle lenses)
        return 0.38
    return float(a.default_value)


def pin_uv(materials, uv_name):
    """Every image texture in the materials (and their node groups) reads the given UV map explicitly,
    so the bake UV can be the active and render UV without the textures moving."""
    seen = set()

    def walk(nt):
        if nt.name in seen:
            return
        seen.add(nt.name)
        for n in list(nt.nodes):
            if n.type == "GROUP" and n.node_tree:
                walk(n.node_tree)
            if n.type == "TEX_IMAGE" and not n.inputs["Vector"].is_linked:
                uv = nt.nodes.new("ShaderNodeUVMap")
                uv.uv_map = uv_name
                nt.links.new(uv.outputs["UV"], n.inputs["Vector"])
    for m in materials:
        if m and m.node_tree:
            walk(m.node_tree)


EYE_MATERIALS = ("Sclera_Cornea", "Iris", "Pupil")


def repair_uv(o, src_uv, eye_boost=2.5):
    """Faces the unwrap could not place (NaN coordinates) take the character's own UVs; on meshes with
    eyes every island then gets the same texel density, the eyes 2.5 times more (so the iris stays
    sharp), and the atlas is packed again."""
    me = o.data
    uv = me.uv_layers["bake"].data
    bad = [p for p in me.polygons
           if any(math.isnan(uv[li].uv.x) or math.isnan(uv[li].uv.y) for li in p.loop_indices)]
    eye = {i for i, m in enumerate(me.materials) if m and m.name.split(".")[0] in EYE_MATERIALS}
    if not bad and not any(p.material_index in eye for p in me.polygons):
        return 0
    src = me.uv_layers[src_uv].data if src_uv else None
    for p in bad:
        for li in p.loop_indices:
            uv[li].uv = src[li].uv if src else (0.0, 0.0)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode="OBJECT")
    uv = me.uv_layers["bake"].data            # the old reference is invalid after the mode switch
    for slot in eye:
        loops = [li for p in me.polygons if p.material_index == slot for li in p.loop_indices]
        if loops:
            c = sum((uv[li].uv for li in loops), Vector((0, 0))) / len(loops)
            for li in loops:
                uv[li].uv = c + (uv[li].uv - c) * eye_boost
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    uv = me.uv_layers["bake"].data
    left = sum(1 for d in uv if math.isnan(d.uv.x) or math.isnan(d.uv.y))
    assert left == 0, f"{o.name}: {left} UV corners still NaN"
    return len(bad)


def bake_mesh(o, tex):
    """UV atlas and the maps of one mesh, then a single final material (colour x AO, alpha if any,
    normal, roughness, metalness)."""
    me = o.data
    # own copies: the metal and alpha bakes rewire the materials, and other meshes may share them
    for i, m in enumerate(me.materials):
        if m is not None:
            me.materials[i] = m.copy()
    src_uv = me.uv_layers[0].name if len(me.uv_layers) else None
    if src_uv:
        pin_uv(me.materials, src_uv)
    bake_uv = me.uv_layers.new(name="bake")
    me.uv_layers.active = bake_uv
    bake_uv.active_render = True
    # Reom's mesh comes with hidden faces (all of the head); the unwrap skips hidden faces, which then
    # keep the character's UVs and overlap the atlas
    for seq in (me.vertices, me.edges, me.polygons):
        seq.foreach_set("hide", [False] * len(seq))
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
    repair_uv(o, src_uv)

    def image(kind, size, data=False):
        img = bpy.data.images.new(f"{o.name}_{kind}", size, size, alpha=False)
        if data:
            img.colorspace_settings.name = "Non-Color"
        return img
    albedo, ao = image("albedo", tex), image("ao", tex)
    normal, rough = image("normal", tex, True), image("rough", tex // 2, True)
    # metal and glass have no diffuse part: for the colour bake they count as plain dielectrics
    saved = []
    for m in me.materials:
        for pr in _principled(m):
            for key in ("Metallic", "Transmission Weight"):
                inp = pr.inputs[key]
                if not inp.is_linked and inp.default_value > 0:
                    saved.append((inp, inp.default_value))
                    inp.default_value = 0.0
    _bake(o, "DIFFUSE", albedo, 6, pass_filter={"COLOR"})
    for inp, v in saved:
        inp.default_value = v
    _bake(o, "AO", ao, 16)
    _bake(o, "NORMAL", normal, 1, normal_space="TANGENT")
    _bake(o, "ROUGHNESS", rough, 1)
    has_metal = any(metal_of(m, m.node_tree) > 0.5 for m in me.materials)
    has_alpha = any(alpha_of(m, m.node_tree) != 1.0 for m in me.materials)
    metal = alpha = None
    if has_metal:
        metal = image("metal", tex // 4, True)
        for m in me.materials:
            _emit_value(m, metal_of)
        _bake(o, "EMIT", metal, 1)
    if has_alpha:
        alpha = image("alpha", tex, True)
        for m in me.materials:
            _emit_value(m, alpha_of)
        _bake(o, "EMIT", alpha, 4)
    return dict(albedo=albedo, ao=ao, normal=normal, rough=rough, metal=metal, alpha=alpha, src_uv=src_uv)


def finish_mesh(o, maps, ao_strength=0.55, paint=None):
    """Composes the final colour (AO, alpha, painted detail) and replaces the materials."""
    size = maps["albedo"].size[0]
    a = np.array(maps["albedo"].pixels[:], dtype=np.float32).reshape(-1, 4)
    ao = np.array(maps["ao"].pixels[:], dtype=np.float32).reshape(-1, 4)[:, 0]
    px = a.copy()
    px[:, :3] *= (1 - ao_strength + ao_strength * np.clip(ao, 0, 1) ** 0.8)[:, None]
    px[:, 3] = 1.0
    if maps["alpha"] is not None:
        px[:, 3] = np.array(maps["alpha"].pixels[:], dtype=np.float32).reshape(-1, 4)[:, 0]
    if paint:
        paint(px.reshape(size, size, 4))
    img = bpy.data.images.new(o.name, size, size, alpha=True)
    img.pixels.foreach_set(px.ravel())
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    img.filepath_raw = str(TEX_DIR / f"{o.name}.png")
    img.file_format = "PNG"
    img.save()
    for key in ("normal", "rough", "metal"):
        if maps[key] is not None:
            maps[key].filepath_raw = str(TEX_DIR / f"{o.name}_{key}.png")
            maps[key].file_format = "PNG"
            maps[key].save()
    me = o.data
    me.materials.clear()
    mat = final_material(o.name, img, maps["normal"], maps["rough"], maps["metal"])
    if maps["alpha"] is not None:
        nt = mat.node_tree
        tex = next(n for n in nt.nodes if n.type == "TEX_IMAGE" and n.image == img)
        nt.links.new(tex.outputs["Alpha"], nt.nodes["Principled BSDF"].inputs["Alpha"])
    me.materials.append(mat)
    me.polygons.foreach_set("material_index", [0] * len(me.polygons))
    if maps["src_uv"]:
        me.uv_layers.remove(me.uv_layers[maps["src_uv"]])
    me.uv_layers["bake"].active_render = True
    for key in ("albedo", "ao", "alpha"):
        if maps[key] is not None:
            bpy.data.images.remove(maps[key])


def brow_painter(head, strands, color=(0.012, 0.009, 0.008), strength=0.85):
    """Draws the eyebrow strands into the head's colour map: every strand point is found on the head
    surface (nearest point) and mapped to the atlas, then the strand is drawn as a 1-pixel line."""
    from mathutils.geometry import barycentric_transform
    me = head.data
    me.calc_loop_triangles()
    tris_ = list(me.loop_triangles)
    bvh = BVHTree.FromPolygons([v.co[:] for v in me.vertices], [t.vertices[:] for t in tris_])
    uv = me.uv_layers["bake"].data

    def to_uv(p):
        loc, _, i, _ = bvh.find_nearest(Vector(p))
        t = tris_[i]
        a, b, c = (me.vertices[k].co for k in t.vertices)
        ua, ub, uc = (Vector((*uv[li].uv, 0)) for li in t.loops)
        return barycentric_transform(loc, a, b, c, ua, ub, uc).xy

    lines = [[to_uv(p) for p in st] for st in strands]

    def paint(px):
        size = px.shape[0]
        for pts in lines:
            for p0, p1 in zip(pts[:-1], pts[1:]):
                n = max(2, int((p1 - p0).length * size * 2))
                for k in range(n + 1):
                    q = p0.lerp(p1, k / n)
                    x, y = int(q.x * size), int(q.y * size)
                    if 0 <= x < size and 0 <= y < size:
                        px[y, x, :3] = px[y, x, :3] * (1 - strength) + np.array(color) * strength
    return paint


# ----------------------------------------------------------------------------------------- face poses
def face_poses(rig, scale):
    """Blink, smile and raised brows as bone moves (figure axes, studs) for MarketMotion: the upper lid
    bones move onto the lower lid, the mouth corners up and out, the brows up."""
    head = {b.name: Vector(b.head_local) for b in rig.data.bones}
    poses = {"blink": {}, "smile": {}, "brows_up": {}}
    for s, sx in (("L", 1), ("R", -1)):
        tops = [f"DEF-lid.T.{s}", f"DEF-lid.T.{s}.001", f"DEF-lid.T.{s}.002", f"DEF-lid.T.{s}.003"]
        lows = [f"DEF-lid.B.{s}", f"DEF-lid.B.{s}.001", f"DEF-lid.B.{s}.002", f"DEF-lid.B.{s}.003"]
        for t in tops:
            low = min(lows, key=lambda b: (head[b] - head[t]).length)
            d = head[low] - head[t]
            poses["blink"][t] = Vector((0, d.y * 0.5, d.z * 0.92))
        for b in (f"DEF-lip.T.{s}.001", f"DEF-lip.B.{s}.001"):
            poses["smile"][b] = Vector((sx * 0.0035, 0.002, 0.0055)) / scale
        for b in (f"DEF-cheek.B.{s}.001", f"DEF-cheek.T.{s}.001"):
            poses["smile"][b] = Vector((sx * 0.001, -0.001, 0.003)) / scale
        for b in (f"DEF-brow.T.{s}", f"DEF-brow.T.{s}.001", f"DEF-brow.T.{s}.002", f"DEF-brow.T.{s}.003"):
            poses["brows_up"][b] = Vector((0, -0.0005, 0.005)) / scale
    return poses


def face_poses_lua(poses):
    return {name: {b: {"q": [0, 0, 0, 1], "p": [round(float(x), 5) for x in TO_ROBLOX @ np.array(m)]}
                   for b, m in sorted(bones.items())}
            for name, bones in poses.items()}


# ------------------------------------------------------------------------------------------- main
def motion(rig, obj, btl, cal):
    poses, grips, drift = solve_key_poses(rig, obj, btl, cal)
    print(f"[lio] key poses solved; bottle drift in the hand {drift:.2f} mm", flush=True)
    for k, v in grips.items():
        print(f"   {k}: {v}")
    # rest = polishing pose
    L.apply_pose(rig, obj, "polish", btl, cal, P=merged("polish")[1], eyes=False, face=False)
    rest = {b.name: b.matrix.to_3x3().copy() for b in rig.pose.bones}
    heads = {}
    for name in poses:
        L.apply_pose(rig, obj, merged(name)[0], btl, cal, P=merged(name)[1], eyes=False, face=False)
        heads[name] = {b.name: np.array(b.head) for b in rig.pose.bones}
    L.apply_pose(rig, obj, "polish", btl, cal, P=merged("polish")[1], eyes=False, face=False)
    deltas = local_deltas(rig, poses, rest)
    channels, clips = build_keys(deltas)
    skel = Skeleton(rig)
    err = check_keys(skel, channels, clips, heads)
    print(f"[lio] {len(channels)} channels; keys reproduce the solved poses within {err:.4f} mm", flush=True)
    # the body in the rest pose (armature only) and the bottle, for the clearance over the loops
    sub = [mm for mm in obj.modifiers if mm.type == "SUBSURF"]
    for mm in sub:
        mm.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    body_V = np.array([v.co[:] for v in me.vertices])
    body_F = [p.vertices[:] for p in me.polygons]
    ev.to_mesh_clear()
    for mm in sub:
        mm.show_viewport = True
    names = {vg.index: vg.name for vg in obj.vertex_groups}
    per = {}
    for v in obj.data.vertices:
        for gr in v.groups:
            per.setdefault(names[gr.group], ([], []))
            per[names[gr.group]][0].append(v.index)
            per[names[gr.group]][1].append(gr.weight)
    body_W = [(b, np.array(i), np.array(w) / 1.0) for b, (i, w) in per.items() if b in skel.head]
    tot = np.zeros(len(body_V))
    for _, i, w in body_W:
        np.add.at(tot, i, w)
    body_W = [(b, i, w / np.maximum(tot[i], 1e-9)) for b, i, w in body_W]
    # the gripping hands touch the bottle on purpose: only torso, arms and face count
    handw = np.zeros(len(body_V))
    for b, i, w in body_W:
        if b.startswith(("DEF-hand", "DEF-f_", "DEF-thumb", "DEF-palm")):
            np.add.at(handw, i, w)
    body_F = [f for f in body_F if handw[list(f)].max() < 0.3]
    bottle_V = []
    for o in [btl] + list(btl.children):
        e = o.evaluated_get(dg)
        mo = e.to_mesh()
        bottle_V += [tuple(o.matrix_world @ v.co) for v in mo.vertices]
        e.to_mesh_clear()
    depth, where = bottle_clearance(skel, channels, clips, body_V, body_F, body_W, np.array(bottle_V))
    print(f"[lio] bottle: deepest point inside the body over both loops {depth:.1f} mm ({where})", flush=True)
    return dict(channels=channels, clips=clips, skel=skel, grips=grips, drift=drift, key_error=err, rest=rest,
                bottle_depth_mm=depth, bottle_where=where)


def curve_points(o):
    """World positions of the strands of a hair curves object: [array (n, 3)]."""
    cv = o.data
    P = np.array([o.matrix_world @ Vector(p.position) for p in cv.points])
    out, i = [], 0
    for c in cv.curves:
        out.append(P[i:i + c.points_length])
        i += c.points_length
    return out


def meshes(rig, obj, tex):
    """Freezes the outfit in the rest (polishing) pose, makes the rest pose the armature's, builds the
    game meshes and bakes their maps.  Returns (mesh objects, ground point in metres)."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    brows = curve_points(bpy.data.objects["Eyebrows"])
    mask = hair.scalp_mask(obj)
    corneas = cornea_faces(obj)
    sources = [o for o in sc.objects if o.type in ("MESH", "CURVE") and o is not rig]
    frozen_objs = {}
    for o in sources:
        bone = o.parent_bone if (o.parent is rig and o.parent_type == "BONE") else None
        if o.name.startswith("Bottle"):
            bone = "DEF-hand.R"
        name = o.name                     # frozen() renames the source
        frozen_objs[name] = frozen(o, dg, bone)
    for o in sources:
        bpy.data.objects.remove(o)
    for o in [o for o in sc.objects if o.type == "CURVES"]:
        bpy.data.objects.remove(o)
    # the frozen shapes are the rest pose from now on
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    body = frozen_objs.pop("Lio")
    g = ground_point(np.array([v.co[:] for v in body.data.vertices]))      # before the feet go
    cap = hair_cap(body, mask)
    wear_names = ("Shirt", "Trousers", "Apron", "ApronStrap", "Belt", "Boot.L", "Boot.R", "Pouch", "PouchFlap",
                  "GoggleStrap") + tuple(n for n in frozen_objs if n.startswith(("Cuff.", "VialLoop.")))
    wear = [frozen_objs.pop(n) for n in wear_names if n in frozen_objs]
    glass = [frozen_objs.pop(n) for n in list(frozen_objs)
             if any("lass" in (m.name if m else "") for m in frozen_objs[n].data.materials)]
    gear = list(frozen_objs.values())
    cover = [BVHTree.FromPolygons([v.co[:] for v in w.data.vertices], [p.vertices[:] for p in w.data.polygons])
             for w in wear if w.name in ("Shirt", "Trousers", "Apron", "Boot.L", "Boot.R", "Belt")]
    head_slots = {reom.MATERIALS.index(m) for m in HEAD_MATERIALS}
    delete_faces(body, corneas)
    hidden = hide_covered_skin(body, cover, head_slots)
    head = split_faces(body, lambda p: p.material_index in head_slots, "head")
    print(f"[lio] skin under clothes removed: {hidden} faces; cornea caps opened: {len(corneas)} faces", flush=True)
    for w in wear:
        if w.name in WEAR_BUDGET:
            decimate(w, WEAR_BUDGET[w.name])
    # metres -> studs, ground point between the feet at the origin
    T = Matrix.Scale(STUDS, 4) @ Matrix.Translation(Vector(-g))
    everything = [head, body, cap] + wear + glass + gear
    for o in everything:
        o.data.transform(T)
    rig.data.transform(T)
    brows = [(np.asarray(st) - g) * STUDS for st in brows]
    groups = [("head", [head]), ("skin", [body]), ("hair", [cap])]
    for k, b in enumerate(pack(wear)):
        groups.append((f"wear{k + 1}", b))
    groups.append(("gear", gear))
    groups.append(("glass", glass))
    bones = {b.name for b in rig.data.bones}
    final = []
    for gname, objs in groups:
        if not objs:
            continue
        o = join(objs, f"trader_lio_{gname}") if len(objs) > 1 else objs[0]
        o.name = o.data.name = f"trader_lio_{gname}"
        most, bare = clean_weights(o, bones)
        n = tris(o)
        print(f"   {o.name}: {n} triangles, up to {most} bones per vertex, {bare} unweighted", flush=True)
        assert n <= MESH_TRIANGLES, f"{o.name} has {n} triangles"
        assert most <= 4 and bare == 0, f"{o.name}: weights"
        o.parent = rig
        mod = o.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        final.append(o)
    if CHECKPOINT:
        bpy.ops.wm.save_as_mainfile(filepath=str(CHECKPOINT), copy=True)
        np.save(str(CHECKPOINT) + ".brows.npy", np.array(brows, dtype=object), allow_pickle=True)
    bake_all(final, brows, tex)
    return final, g


def bake_all(final, brows, tex):
    for o in final:
        maps = bake_mesh(o, tex if o.name.endswith(("head", "skin", "wear1", "wear2")) else tex // 2)
        finish_mesh(o, maps, paint=brow_painter(o, brows) if o.name.endswith("_head") else None)
        print(f"   baked {o.name}", flush=True)


def lua_clips_of(clips):
    """Clips as written to MarketMotion.lua (keys rounded to 4 decimals)."""
    return {name: {"duration": cl["duration"], "loop": cl["loop"], "additive": cl["additive"],
                   "keys": {c: [[round(t, 4)] + [round(float(x), 4) for x in v] for t, v in k]
                            for c, k in cl["keys"].items()},
                   "face": {f: [[round(t, 4), round(w, 4)] for t, w in k] for f, k in cl["face"].items()}}
            for name, cl in clips.items()}


def py_clips_of(lua_clips):
    return {n: {"duration": c["duration"], "loop": c["loop"], "additive": c["additive"],
                "keys": {ch: [(k[0], tuple(k[1:])) for k in ks] for ch, ks in c["keys"].items()},
                "face": c["face"]} for n, c in lua_clips.items()}


def checks_and_reference(channels, lua_clips, skel, to_roblox):
    """Posed wrist positions for the server check and reference rotations for the Lua test, both from
    the keys exactly as exported (rounded)."""
    clips = py_clips_of(lua_clips)
    check = []
    for clip, t, greet in (("idle", 0.0, None), ("idle", 2.1, None), ("idle", 5.0, None), ("idle", 6.0, None),
                           ("idle2", 1.6, None), ("idle2", 3.8, None), ("idle", 1.1, 0.55)):
        _, P = skel.fk(evaluate(channels, clips, clip, t, greet))
        e = {"clip": clip, "t": t, "wristL": to_roblox(P["DEF-hand.L"]), "wristR": to_roblox(P["DEF-hand.R"])}
        if greet is not None:
            e["greet"] = greet
        check.append(e)
    reference = []
    for clip in ("idle", "idle2"):
        d = clips[clip]["duration"]
        for k in range(12):
            t = round(d * k / 12 + 0.013, 4)
            for greet in (None, 0.37):
                q = {}
                for b, R in evaluate(channels, clips, clip, t, greet).items():
                    qq = Matrix((TO_ROBLOX @ np.asarray(R) @ TO_ROBLOX.T).tolist()).to_quaternion()
                    q[b] = [round(qq.x, 6), round(qq.y, 6), round(qq.z, 6), round(qq.w, 6)]
                reference.append({"clip": clip, "t": t, "greet": greet, "q": q})
    return check, reference


def data_entry(m, final, g):
    """The trader's entries for MarketMotion.lua and TraderArt.lua, and reference samples for the test."""
    lua_clips = lua_clips_of(m["clips"])

    def roblox(p):
        return [round(float(x), 4) for x in TO_ROBLOX @ ((np.asarray(p) - g) * STUDS)]
    check, reference = checks_and_reference(m["channels"], lua_clips, m["skel"], roblox)
    height = max(max(v.co.z for v in o.data.vertices) for o in final)
    return {"motion": {"clips": lua_clips, "poses": face_poses_lua(m["faces"]), "channels": m["channels"], "rig": RIG},
            "art": {"height": round(height, 3), "meshes": [o.name for o in final], "check": check, "rig": "trader_lio"},
            "reference": reference, "grips": m["grips"], "key_error_mm": m["key_error"],
            "bottle_depth_mm": m["bottle_depth_mm"], "bottle_drift_mm": m["drift"]}


def set_clip_pose(rig, channels, clips, clip, t, greet=None):
    """Poses the (rest = polishing) rig like the game does at clip time t."""
    q = evaluate(channels, clips, clip, t, greet)
    D = {}
    for b in rig.data.bones:
        p = b.parent.name if b.parent else None
        D[b.name] = (D[p] if p else np.eye(3)) @ np.asarray(q.get(b.name, np.eye(3)))
    for b in rig.data.bones:
        posing.set_rotation(rig, b.name, Matrix(D[b.name].tolist()) @ b.matrix_local.to_3x3())


def set_face(rig, poses, weights):
    for b in rig.pose.bones:
        b.location = (0, 0, 0)
    for name, w in weights.items():
        for bone, move in poses[name].items():
            b = rig.data.bones[bone]
            rig.pose.bones[bone].location += b.matrix_local.to_3x3().inverted() @ (Vector(move) * w)
    posing.update()


def previews(rig, final, m, samples):
    """What the game gets: the baked meshes posed by the exported keys (08-roblox-motion.png) and the
    face poses (09-roblox-face.png)."""
    sc = bpy.context.scene
    sc.cycles.samples = samples
    for name in ("key", "rim"):
        o = bpy.data.objects[name]
        o.location = Vector(o.location) * STUDS
        o.data.size *= STUDS
        o.data.energy *= STUDS * STUDS
    cam = sc.camera
    tmp = PREVIEW / "_tiles"
    tmp.mkdir(parents=True, exist_ok=True)
    centre = np.array((0, 0, 3.6))
    tiles = []
    for k, (clip, t) in enumerate((("idle", 0.0), ("idle", 0.9), ("idle", 4.3), ("idle", 6.0), ("idle2", 0.8),
                                   ("idle2", 3.0), ("idle", 7.7), ("idle2", 6.2))):
        set_clip_pose(rig, m["channels"], m["clips"], clip, t)
        tiles.append(L.shoot(sc, cam, tmp / f"m{k}.png", centre, (-0.35, -1, 0.1), 15.0, res=(480, 640)))
    L.sheet(tiles, PREVIEW / "08-roblox-motion.png", cols=4)
    set_clip_pose(rig, m["channels"], m["clips"], "idle", 0.0)
    eyes = (Vector(rig.data.bones["DEF-eye.L"].head_local) + Vector(rig.data.bones["DEF-eye.R"].head_local)) / 2
    face = np.array(eyes) + np.array((0, 0, -0.1))
    tiles = []
    for k, w in enumerate(({}, {"blink": 1.0}, {"smile": 1.0}, {"brows_up": 1.0})):
        set_face(rig, m["faces"], w)
        tiles.append(L.shoot(sc, cam, tmp / f"f{k}.png", face, (0.25, -1, 0.05), 2.4, lens=70, res=(480, 480)))
    set_face(rig, m["faces"], {})
    L.sheet(tiles, PREVIEW / "09-roblox-face.png", cols=4)


def rebake(path, tex, samples, render):
    """Bakes again from a checkpoint (the motion data in OUT_JSON stays as it is)."""
    bpy.ops.wm.open_mainfile(filepath=str(path))
    brows = list(np.load(str(path) + ".brows.npy", allow_pickle=True))
    rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    for m in bpy.data.materials:                 # hair settings may have changed since the checkpoint
        if m.name.startswith("HairCap"):
            nt = m.node_tree
            nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
            for n in nt.nodes:
                if n.type == "BUMP":
                    n.inputs["Strength"].default_value, n.inputs["Distance"].default_value = 0.5, 0.0015
                if n.type == "VALTORGB":
                    n.color_ramp.elements[0].color = (0.004, 0.003, 0.0027, 1)
                    n.color_ramp.elements[1].color = (0.018, 0.013, 0.010, 1)
    final = sorted((o for o in bpy.data.objects if o.name.startswith("trader_lio_")), key=lambda o: o.name)
    entry = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    for b in sorted(rig_bones()):
        entry["motion"]["channels"].setdefault(b, [[b, 1]])
    skel = Skeleton(rig)                       # rest = polishing pose, already in studs
    entry["art"]["check"], entry["reference"] = checks_and_reference(
        entry["motion"]["channels"], entry["motion"]["clips"], skel,
        lambda p: [round(float(x), 4) for x in TO_ROBLOX @ np.asarray(p)])
    OUT_JSON.write_text(json.dumps(entry, indent=1), encoding="utf-8")
    if tex == 0:
        return
    bake_all(final, brows, tex)
    export_rig(rig, final, str(OUT_FBX))
    print(f"[lio] wrote {OUT_FBX}", flush=True)
    if render:
        entry = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        mo = entry["motion"]
        clips = {n: {"duration": c["duration"], "loop": c["loop"], "additive": c["additive"],
                     "keys": {ch: [(k[0], tuple(k[1:])) for k in ks] for ch, ks in c["keys"].items()},
                     "face": c["face"]} for n, c in mo["clips"].items()}
        previews(rig, final, {"channels": mo["channels"], "clips": clips, "faces": face_poses(rig, 0.28)}, samples)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--motion-only", action="store_true")
    ap.add_argument("--tex", type=int, default=1024)
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--checkpoint")
    ap.add_argument("--rebake", help="bake again from a checkpoint written by --checkpoint")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if args.rebake:
        rebake(Path(args.rebake), args.tex, args.samples, not args.no_render)
        return
    global CHECKPOINT
    CHECKPOINT = Path(args.checkpoint) if args.checkpoint else None
    L.scene_setup(16)
    obj, V = L.build_body()
    rig, body, pieces = L.dress(obj)
    cal = {s: posing.calibrate(rig, s) for s in ("L", "R")}
    btl = L.bottle()
    m = motion(rig, obj, btl, cal)
    final, g = meshes(rig, obj, args.tex)
    m["faces"] = face_poses(rig, 0.28)
    entry = data_entry(m, final, g)
    OUT_JSON.write_text(json.dumps(entry, indent=1), encoding="utf-8")
    print(f"[lio] wrote {OUT_JSON}", flush=True)
    if not args.motion_only:
        export_rig(rig, final, str(OUT_FBX))
        print(f"[lio] wrote {OUT_FBX}", flush=True)
    if not args.no_render:
        previews(rig, final, m, args.samples)


if __name__ == "__main__":
    main()
