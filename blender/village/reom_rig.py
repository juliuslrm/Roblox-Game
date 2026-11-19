"""Deform skeleton for a morphed Reom character, built from data only.

- Bones: the Rigify metarig of characters/reom/rigs.blend, one deform bone DEF-<name> per metarig bone
  that has a weight group; upper arm, forearm, thigh and shin are split into two halves (DEF-x and
  DEF-x.001) exactly as Rigify's generated rig does, because the weights are painted for that.
- Positions: joints/rigify.npz gives bone heads and tails as weighted averages of mesh vertices, so they
  follow every morph.  Ends without a joint entry move with the nearest skin.
- Eyes: Reom's eyeballs hang on the head bone; DEF-eye.L/R are added and the eyeball vertices
  (sclera, iris, pupil) bound to them, so the look direction can be animated.
- A "Root" bone at the floor is the parent of everything (as in the previous traders).
"""
import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

from village import reom

SPLIT = ("upper_arm", "forearm", "thigh", "shin")


def _joints(V):
    z = np.load(reom.CHAR / "joints/rigify.npz", allow_pickle=False)
    names = [n.decode() for n in bytes(z["names"]).split(b"\0")]
    out, i = {}, 0
    for name, cnt in zip(names, z["cnt"]):
        idx, w = z["idx"][i:i + int(cnt)], z["weights"][i:i + int(cnt)]
        out[name[len("joint_"):]] = (V[idx] * w[:, None]).sum(axis=0) / w.sum()
        i += int(cnt)
    return out


def _metarig():
    with bpy.data.libraries.load(str(reom.CHAR / "rigs.blend"), link=False) as (src, dst):
        dst.objects = ["metarig"]
    return dst.objects[0]


def build(obj, base, groups, name="LioRig"):
    """obj: the morphed mesh; base: its vertex positions before morphing; groups: reom.vertex_groups()."""
    V = np.array([v.co[:] for v in obj.data.vertices])
    J = _joints(V)
    tree = KDTree(len(base))
    for i, co in enumerate(base):
        tree.insert(co, i)
    tree.balance()

    def fitted(bone, end, metapos):
        key = f"{bone}_{end}"
        if key in J:
            return Vector(J[key])
        _, i, _ = tree.find(metapos)
        return Vector(metapos) + Vector(V[i] - base[i])

    meta = _metarig()
    mbones = meta.data.bones
    keep = [b for b in mbones if f"DEF-{b.name}" in groups]
    keepset = {b.name for b in keep}
    # metarig rest data before we leave object mode
    rest = {b.name: (b.head_local.copy(), b.tail_local.copy(), b.matrix_local.to_3x3().col[2].copy(),
                     b.parent.name if b.parent else None) for b in mbones}

    arm = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones
    root = eb.new("Root")
    root.head, root.tail = (0, 0, 0), (0, 0.15, 0)
    ends = {}  # metarig bone -> deform bone its children hang on

    for b in keep:
        h0, t0, z_axis, _ = rest[b.name]
        head, tail = fitted(b.name, "head", h0), fitted(b.name, "tail", t0)
        if b.name.split(".")[0] in SPLIT:
            mid = (head + tail) / 2
            e1, e2 = eb.new(f"DEF-{b.name}"), eb.new(f"DEF-{b.name}.001")
            e1.head, e1.tail, e2.head, e2.tail = head, mid, mid, tail
            e2.parent, e2.use_connect = e1, True
            for e in (e1, e2):
                e.align_roll(z_axis)
            ends[b.name] = (e1, e2)
        else:
            e = eb.new(f"DEF-{b.name}")
            e.head, e.tail = head, tail
            e.align_roll(z_axis)
            ends[b.name] = (e, e)

    def anchor(mname):
        p = rest[mname][3]
        while p is not None and p not in keepset:
            p = rest[p][3]
        return ends[p][1] if p else root

    for b in keep:
        first = ends[b.name][0]
        first.parent = anchor(b.name)
    for side in ("L", "R"):
        h0, t0, z_axis, _ = rest[f"eye.{side}"]
        e = eb.new(f"DEF-eye.{side}")
        e.head, e.tail = fitted(f"eye.{side}", "head", h0), fitted(f"eye.{side}", "tail", t0)
        e.align_roll(z_axis)
        e.parent = ends["spine.006"][1]
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.objects.remove(meta)

    _bind(obj, rig, groups)
    return rig


def _bind(obj, rig, groups):
    for vg in list(obj.vertex_groups):
        obj.vertex_groups.remove(vg)
    for gname, (idx, w) in groups.items():
        if gname not in rig.data.bones:
            continue
        vg = obj.vertex_groups.new(name=gname)
        for i, wi in zip(idx.tolist(), w.tolist()):
            vg.add([i], float(wi), "REPLACE")
    # eyeballs: whole eyeball to the eye bone of its side
    eye_slots = {reom.MATERIALS.index(m) for m in ("Sclera_Cornea", "Iris", "Pupil")}
    verts = {v for p in obj.data.polygons if p.material_index in eye_slots for v in p.vertices}
    head = obj.vertex_groups.get("DEF-spine.006")
    for side, sign in (("L", 1), ("R", -1)):
        vg = obj.vertex_groups.new(name=f"DEF-eye.{side}")
        mine = [i for i in verts if obj.data.vertices[i].co.x * sign > 0]
        vg.add(mine, 1.0, "REPLACE")
        if head:
            head.remove(mine)
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    obj.parent = rig
    # the armature must deform before the subdivision
    obj.modifiers.move(obj.modifiers.find("Armature"), 0)


def stats(obj, rig):
    """Bone count, vertices without weight, vertices with more than 4 influences."""
    unweighted = sum(1 for v in obj.data.vertices if not v.groups)
    over4 = sum(1 for v in obj.data.vertices if sum(1 for g in v.groups if g.weight > 1e-4) > 4)
    return dict(bones=len(rig.data.bones), unweighted=unweighted, over4=over4)
