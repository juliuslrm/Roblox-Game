"""Posing the Reom deform rig: analytic arm IK, finger grips on cylindrical props, look-at.

Conventions measured on the rig (calibrate()): every finger joint curls towards the palm by a positive
rotation about its local X axis; the palm faces the hand bone's local -X on the right and +X on the left
hand; the hand's local Z points from the little finger towards the thumb side.  All matrices are in armature space (the rig sits
at the origin unscaled, so this is also world space).
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

FINGERS = ("f_index", "f_middle", "f_ring", "f_pinky")
# largest curl per joint (degrees): knuckle, middle joint, end joint
CURL_LIMIT = (85.0, 100.0, 75.0)


def update():
    bpy.context.view_layer.update()


def pose_matrix(rig, name):
    return rig.pose.bones[name].matrix.copy()


def set_rotation(rig, name, rot3):
    """Gives a pose bone the armature-space orientation rot3 (its head stays where the parent puts it)."""
    pb = rig.pose.bones[name]
    m = rot3.to_4x4()
    m.translation = pb.matrix.translation
    pb.matrix = m
    update()


def frame(y, x_hint):
    """Rotation with the bone axis y and the x axis as close as possible to x_hint."""
    y = Vector(y).normalized()
    x = Vector(x_hint) - y * Vector(x_hint).dot(y)
    x.normalize()
    z = x.cross(y)
    return Matrix((x, y, z)).transposed()


def reset(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    update()


# --------------------------------------------------------------------------------------------- arms
def arm_ik(rig, side, wrist, hand_rot, hint):
    """Places the arm so the hand bone's head is at `wrist` with orientation `hand_rot` (3x3).
    hint: direction the elbow should point to.  Upper arm and forearm are split in two halves (as in
    Rigify); the halves stay in line, the forearm twist is shared between them."""
    up, up2 = f"DEF-upper_arm.{side}", f"DEF-upper_arm.{side}.001"
    fo, fo2 = f"DEF-forearm.{side}", f"DEF-forearm.{side}.001"
    b = rig.data.bones
    L1 = b[up].length + b[up2].length
    L2 = b[fo].length + b[fo2].length
    S = pose_matrix(rig, up).translation
    W = Vector(wrist)
    d = W - S
    D = min(d.length, (L1 + L2) * 0.999)
    u = d.normalized()
    W = S + u * D
    a = (L1 * L1 - L2 * L2 + D * D) / (2 * D)
    h = math.sqrt(max(0.0, L1 * L1 - a * a))
    v = Vector(hint) - u * Vector(hint).dot(u)
    v.normalize()
    E = S + u * a + v * h
    d1, d2 = (E - S).normalized(), (W - E).normalized()
    hinge = d1.cross(d2)
    if hinge.length < 1e-6:
        hinge = b[up].matrix_local.to_3x3().col[0]
    hinge.normalize()
    # the elbow bends about the bones' local X: keep the sign of the rest X axis
    rest_x = b[fo].matrix_local.to_3x3().col[0]
    if hinge.dot(rest_x) < 0:
        hinge = -hinge
    r_up = frame(d1, hinge)
    set_rotation(rig, up, r_up)
    set_rotation(rig, up2, r_up)
    r_fo = frame(d2, hinge)
    # twist towards the hand: half on each forearm half
    hx = Vector(hand_rot.col[0]) - d2 * Vector(hand_rot.col[0]).dot(d2)
    twist = Vector(hinge).angle(hx) if hx.length > 1e-6 else 0.0
    if hinge.cross(hx).dot(d2) < 0:
        twist = -twist
    set_rotation(rig, fo, Quaternion(d2, twist * 0.35).to_matrix() @ r_fo)
    set_rotation(rig, fo2, Quaternion(d2, twist * 0.85).to_matrix() @ r_fo)
    set_rotation(rig, f"DEF-hand.{side}", hand_rot)
    return dict(elbow=E, reach=d.length / (L1 + L2), wrist_bend=wrist_bend(rig, side))


def wrist_bend(rig, side):
    """Angle (degrees) between the forearm and the hand axis."""
    f = pose_matrix(rig, f"DEF-forearm.{side}.001").to_3x3().col[1]
    h = pose_matrix(rig, f"DEF-hand.{side}").to_3x3().col[1]
    return math.degrees(Vector(f).angle(Vector(h)))


# ------------------------------------------------------------------------------------------- grips
class Cylinder:
    """A prop's grip surface: axis point, unit axis, radius and half length (armature space)."""

    def __init__(self, centre, axis, radius, half):
        self.c, self.a, self.r, self.half = Vector(centre), Vector(axis).normalized(), radius, half

    def dist(self, p):
        """Signed distance of a point from the cylinder surface (negative inside)."""
        v = Vector(p) - self.c
        t = v.dot(self.a)
        radial = (v - self.a * t).length - self.r
        cap = abs(t) - self.half
        return radial if cap <= 0 else max(radial, cap)


_PALM_SIGN = {}


def hand_frame(rig, side):
    """(knuckle centre, along the fingers, palm normal, across towards the thumb) of the posed hand.
    The palm faces the hand's local -X on the right hand and +X on the left one (measured by
    calibrate(); the rig's left-side rolls are not mirrored)."""
    m = pose_matrix(rig, f"DEF-hand.{side}").to_3x3()
    knuckles = sum((pose_matrix(rig, f"DEF-palm.0{i}.{side}") @ Vector((0, rig.data.bones[f"DEF-palm.0{i}.{side}"].length, 0))
                    for i in range(1, 5)), Vector()) / 4
    return knuckles, Vector(m.col[1]), -Vector(m.col[0]) * _PALM_SIGN.get(side, 1.0), Vector(m.col[2])


def grip_hand_rotation(axis, normal, cal):
    """Hand orientation whose palm faces `normal` and whose across-the-palm direction runs along the
    prop axis, thumb side towards +axis (cal: calibrate() of that hand)."""
    z = Vector(axis).normalized() * cal["zsign"]
    x = -Vector(normal).normalized() * cal["palm"]
    x = (x - z * x.dot(z)).normalized()
    y = z.cross(x)
    return Matrix((x, y, z)).transposed()


def _bone_points(rig, name, n=4):
    m = pose_matrix(rig, name)
    L = rig.data.bones[name].length
    return [m @ Vector((0, L * k / (n - 1), 0)) for k in range(n)]


def _tip(rig, name):
    return pose_matrix(rig, name) @ Vector((0, rig.data.bones[name].length, 0))


def calibrate(rig, side):
    """Signs measured on the rig: the palm side of the hand (where a positive X rotation curls the
    fingers to), the
    thumb-base axis (+Z or -Z) that swings the thumb tip towards the middle of the palm.  Also the sign
    of the hand's local Z relative to the thumb side."""
    _, _, normal, across = hand_frame(rig, side)
    pb = rig.pose.bones[f"DEF-f_middle.01.{side}"]
    a = _tip(rig, f"DEF-f_middle.03.{side}")
    pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(10))
    update()
    b = _tip(rig, f"DEF-f_middle.03.{side}")
    pb.rotation_quaternion = (1, 0, 0, 0)
    update()
    # Rigify fingers curl with a positive X rotation on both sides; the palm is the side the tip moves
    # to (the hand's local -X on the right hand, +X on the left one of this rig)
    toward = 1.0 if (b - a).dot(normal) > 0 else -1.0
    _PALM_SIGN[side] = _PALM_SIGN.get(side, 1.0) * toward
    curl = 1.0
    knuckles, along, normal, across = hand_frame(rig, side)
    goal = knuckles + normal * 0.04
    pb = rig.pose.bones[f"DEF-thumb.01.{side}"]
    best = None
    for sgn in (1.0, -1.0):
        pb.rotation_quaternion = Quaternion((0, 0, sgn), math.radians(25))
        update()
        d = (_tip(rig, f"DEF-thumb.03.{side}") - goal).length
        if best is None or d < best[0]:
            best = (d, sgn)
    pb.rotation_quaternion = (1, 0, 0, 0)
    update()
    thumb_dir = (_tip(rig, f"DEF-thumb.01.{side}") - pose_matrix(rig, f"DEF-hand.{side}").translation)
    zsign = 1.0 if thumb_dir.dot(across) > 0 else -1.0
    return dict(curl=curl, oppose=best[1], zsign=zsign, palm=_PALM_SIGN[side])


def curl_grip(rig, side, cyl, finger_radius=0.0085, step=2.0, thumb=True, cal=None):
    """Closes each finger joint by joint (knuckle first) until a bone of the finger touches the prop
    surface (bone line within finger_radius of it) or the joint reaches its limit.  Returns the
    angles and which fingers touch."""
    cal = cal or calibrate(rig, side)
    cx = (cal["curl"], 0, 0)
    out = {}
    chains = [(f, [f"DEF-{f}.0{j}.{side}" for j in (1, 2, 3)]) for f in FINGERS]
    for fname, chain in chains:
        angles, touch = [], False
        for j, bone in enumerate(chain):
            pb = rig.pose.bones[bone]
            base = pb.rotation_quaternion.copy()
            ang = 0.0
            while ang < CURL_LIMIT[j]:
                trial = ang + step
                pb.rotation_quaternion = base @ Quaternion(cx, math.radians(trial))
                update()
                pts = [p for b in chain[j:] for p in _bone_points(rig, b)][1:]   # the joint itself does not move
                if min(cyl.dist(p) for p in pts) < finger_radius:
                    pb.rotation_quaternion = base @ Quaternion(cx, math.radians(ang))
                    update()
                    touch = True
                    break
                ang = trial
            angles.append(round(ang, 1))
        out[fname] = dict(angles=angles, touch=touch)
    if thumb:
        chain = [f"DEF-thumb.0{j}.{side}" for j in (1, 2, 3)]
        angles, touch = [], False
        # opposition: thumb base swings across the palm (-Z), then the two outer joints curl (+X)
        axes = ((0, 0, cal["oppose"]), cx, cx)
        for j, (bone, axis, limit) in enumerate(zip(chain, axes, (40, 55, 65))):
            pb = rig.pose.bones[bone]
            base = pb.rotation_quaternion.copy()
            ang = 0.0
            while ang < limit:
                trial = ang + step
                pb.rotation_quaternion = base @ Quaternion(axis, math.radians(trial))
                update()
                pts = [p for b in chain[j:] for p in _bone_points(rig, b)][1:]   # the joint itself does not move
                if min(cyl.dist(p) for p in pts) < finger_radius * 1.1:
                    pb.rotation_quaternion = base @ Quaternion(axis, math.radians(ang))
                    update()
                    touch = True
                    break
                ang = trial
            angles.append(round(ang, 1))
        out["thumb"] = dict(angles=angles, touch=touch)
    return out


def relaxed_hand(rig, side, curl=(14, 18, 10), thumb=(8, 10, 8), cal=None):
    """A resting hand: fingers slightly curled, more towards the little finger."""
    cal = cal or calibrate(rig, side)
    cx = (cal["curl"], 0, 0)
    for k, f in enumerate(FINGERS):
        for j in range(3):
            pb = rig.pose.bones[f"DEF-{f}.0{j + 1}.{side}"]
            pb.rotation_quaternion = Quaternion(cx, math.radians(curl[j] * (1 + 0.25 * k)))
    for j, (ax, a) in enumerate(zip(((0, 0, cal["oppose"]), cx, cx), thumb)):
        rig.pose.bones[f"DEF-thumb.0{j + 1}.{side}"].rotation_quaternion = Quaternion(ax, math.radians(a))
    update()


def skin_contact(obj, groups, side, cyl):
    """Measured on the deformed mesh (armature only): deepest skin penetration into the prop (m, >0 =
    inside) and the share of each finger's skin within 3 mm of the prop surface."""
    sub = [m for m in obj.modifiers if m.type == "SUBSURF"]
    for m in sub:
        m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    co = [ev.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    for m in sub:
        m.show_viewport = True
    res, deepest = {}, 0.0
    names = [f"DEF-{f}.0{j}.{side}" for f in FINGERS for j in (1, 2, 3)] + \
            [f"DEF-thumb.0{j}.{side}" for j in (1, 2, 3)] + [f"DEF-palm.0{i}.{side}" for i in range(1, 5)] + \
            [f"DEF-hand.{side}"]
    for name in names:
        idx, w = groups[name]
        d = np.array([cyl.dist(co[i]) for i, wi in zip(idx, w) if wi > 0.5])
        if len(d) == 0:
            continue
        deepest = max(deepest, float(-d.min()))
        res[name] = round(float(d.min()) * 1000, 1)     # mm from the surface, negative = inside
    return dict(deepest_mm=round(deepest * 1000, 1), nearest_mm=res)


# -------------------------------------------------------------------------------------------- body
def rotate(rig, name, axis_world, degrees):
    """Adds a rotation about a world axis to a pose bone."""
    pb = rig.pose.bones[name]
    m = pb.matrix.copy()
    r = Quaternion(Vector(axis_world).normalized(), math.radians(degrees)).to_matrix().to_4x4()
    t = m.translation.copy()
    m = r @ m
    m.translation = t
    pb.matrix = m
    update()


def look_at(rig, target, neck_share=0.4, head_share=0.6, eyes=True):
    """Turns neck and head towards a point, the eyes all the way."""
    for name, share in (("DEF-spine.005", neck_share), ("DEF-spine.006", head_share)):
        m = pose_matrix(rig, "DEF-spine.006")
        eye_mid = (pose_matrix(rig, "DEF-eye.L").translation + pose_matrix(rig, "DEF-eye.R").translation) / 2
        fwd = Vector(m.to_3x3().col[2])         # the head bone's +Z points out of the face
        want = (Vector(target) - eye_mid).normalized()
        q = fwd.rotation_difference(want)
        axis, ang = q.to_axis_angle()
        rotate(rig, name, axis, math.degrees(ang) * share)
    if eyes:
        for side in ("L", "R"):
            pb = rig.pose.bones[f"DEF-eye.{side}"]
            m = pb.matrix
            d = Vector(m.to_3x3().col[1])
            want = (Vector(target) - m.translation).normalized()
            q = d.rotation_difference(want)
            axis, ang = q.to_axis_angle()
            rotate(rig, f"DEF-eye.{side}", axis, min(25.0, math.degrees(ang)))
