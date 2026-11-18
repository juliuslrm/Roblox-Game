"""Arm poses from contact goals (offline inverse kinematics for the idle loops).

The traders stand still and play baked loops, so the arm poses are solved once while building
(not with IKControl at run time): pose = upper arm (rx, ry, rz) and forearm (rx, rz) of one side in
the loop's angle convention (characters.LOOPS).  The cost combines the goals of a pose with
penalties that keep it human:
    joint limits   elbow flexion 10 .. 140 degrees, upper arm at most 100 degrees up, no arm
                   swung behind the body
    collisions     the held prop and the hand stay outside the body (arms excluded)
Solved with Nelder-Mead from several starts; the result is printed and copied into LOOPS, so the
loops stay readable data (blender/solve_poses.py).
"""
import math

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import characters as C
from . import gripcheck


COMFORT = 0.02
WRIST_BEND, WRIST_SIDE = 45.0, 20.0          # degrees: hand against forearm (anatomically about 70 / 30)


def nelder_mead(f, x0, step=8.0, iters=400, tol=1e-6):
    n = len(x0)
    pts = [np.array(x0, float)]
    for i in range(n):
        p = np.array(x0, float)
        p[i] += step
        pts.append(p)
    vals = [f(p) for p in pts]
    for _ in range(iters):
        order = np.argsort(vals)
        pts = [pts[i] for i in order]
        vals = [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) < tol:
            break
        c = np.mean(pts[:-1], axis=0)
        r = c + (c - pts[-1])
        fr = f(r)
        if fr < vals[0]:
            e = c + 2 * (c - pts[-1])
            fe = f(e)
            pts[-1], vals[-1] = (e, fe) if fe < fr else (r, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = r, fr
        else:
            k = c + 0.5 * (pts[-1] - c)
            fk = f(k)
            if fk < vals[-1]:
                pts[-1], vals[-1] = k, fk
            else:
                for i in range(1, len(pts)):
                    pts[i] = pts[0] + 0.5 * (pts[i] - pts[0])
                    vals[i] = f(pts[i])
    i = int(np.argmin(vals))
    return pts[i], vals[i]


class Scene:
    """A trader at one loop time: body collision without the arms, prop geometry, helpers."""

    def __init__(self, ch, t):
        self.ch, self.t = ch, t
        body = ch.body
        names, W = body.dense_weights()
        self.W = W
        arm = W[:, [names.index(b) for b in names if b.startswith(("wrist", "lowerarm", "upperarm"))]].sum(axis=1) > 0.3
        faces = [body.faces[i] for i in body.face_ids("body")]
        self.faces = [f for f in faces if not arm[list(f)].any()]
        self.trunk = ~arm                       # body vertices without the arms (targets are measured on it)
        rots = C.local_rotations(ch.role, t)
        P = _posed(ch, W, body.verts, rots)
        self.body_bvh = BVHTree.FromPolygons([Vector(v) for v in P], [list(f) for f in self.faces], all_triangles=False)
        self.posed_body = P

    def mats(self, override, fixed=None):
        return self.ch.body.bone_matrices(C.local_rotations(self.ch.role, self.t, {**(fixed or {}), **override}))

    def prop_points(self, side, local_pts, mats):
        """Prop-space points of the held prop -> world (figure) space."""
        frame = self.ch.held[side][2]
        P = (np.c_[local_pts, np.ones(len(local_pts))] @ frame.T)
        return (P @ mats["wrist." + side].T)[:, :3]

    def joint(self, mats, bone):
        return (mats[bone] @ np.r_[self.ch.heads[bone], 1])[:3]

    def inside(self, pts, margin=0.0):
        """Sum of depths by which points lie inside the body (or closer than margin)."""
        total = 0.0
        for p in pts:
            hit = self.body_bvh.find_nearest(Vector(p))
            if hit[0] is None:
                continue
            d = Vector(p) - hit[0]
            s = d.length if d.dot(hit[1]) >= 0 else -d.length
            if s < margin:
                total += margin - s
        return total


def _posed(ch, W, V, rots):
    mats = ch.body.bone_matrices(rots)
    out = np.zeros_like(V)
    vh = np.c_[V, np.ones(len(V))]
    for j, b in enumerate(ch.bones):
        w = W[:, j]
        nz = w > 0
        if nz.any():
            out[nz] += w[nz, None] * (vh[nz] @ mats[b].T)[:, :3]
    return out


def wrist_bend(scene, mats, side):
    """(bend, sideways bend) of the hand against the forearm in degrees (gripcheck.wrist_bend)."""
    return gripcheck.wrist_bend(scene.ch.body.hand_geometry[side], mats, side)


def arm_penalty(scene, mats, side):
    up, lo, wr = (scene.joint(mats, f"{b}.{side}") for b in ("upperarm01", "lowerarm01", "wrist"))
    a, b = up - lo, wr - lo
    flex = 180 - math.degrees(math.acos(np.clip(np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b), -1, 1)))
    bend, sideways = wrist_bend(scene, mats, side)
    lift = math.degrees(math.acos(np.clip(np.dot(lo - up, (0, 0, -1)) / np.linalg.norm(lo - up), -1, 1)))
    pen = max(0, 10 - flex) ** 2 + max(0, flex - 140) ** 2 + max(0, lift - 95) ** 2
    pen += 400 * max(0.0, (lo - up)[1] - 0.25) ** 2        # elbow far behind the shoulder
    pen += max(0.0, bend - WRIST_BEND) ** 2 + max(0.0, sideways - WRIST_SIDE) ** 2
    pen += 300 * scene.inside([lo, wr, (lo + wr) / 2], 0.06)
    return pen, flex, lift


def pose_vector(x):
    """7 solver values -> loop angles (upper (rx, ry, rz), fore (rx, 0, rz), hand (rx, 0, rz))."""
    return ((float(x[0]), float(x[1]), float(x[2])), (float(x[3]), 0.0, float(x[4])),
            (float(x[5]), 0.0, float(x[6])))


def solve(scene, side, goal, starts, iters=500, fixed=None, prior=None):
    """Minimises goal(mats, scene) + human penalties over the arm of `side` (other channels as in the
    loop or as given in `fixed`).  prior = (angles, weight) keeps the solution close to a given pose
    (an approach right before a contact pose, so the last stretch of the motion is short)."""
    tag = "l" if side == "L" else "r"

    def f(x):
        up, fo, ha = pose_vector(x)
        mats = scene.mats({"upper_" + tag: up, "fore_" + tag: fo, "hand_" + tag: ha}, fixed)
        pen, flex, lift = arm_penalty(scene, mats, side)
        bend, sideways = wrist_bend(scene, mats, side)
        # comfort: a relaxed arm (elbow near 90 degrees, upper arm low, little turn, wrist near straight)
        comfort = ((flex - 90) / 60) ** 2 + (lift / 70) ** 2 + (x[2] / 50) ** 2 + (x[4] / 50) ** 2 + (x[1] / 45) ** 2 \
            + (bend / 40) ** 2 + (sideways / 25) ** 2
        wrist_twist, fore_turn = gripcheck.arm_twist(scene.ch.body.hand_geometry[side], mats, side)
        twist = max(0.0, abs(x[2]) - 60) ** 2 + 4 * max(0.0, abs(wrist_twist) - 20) ** 2 \
            + 4 * max(0.0, abs(fore_turn) - 80) ** 2
        near = 0.0 if prior is None else prior[1] * float(np.sum((np.asarray(x) - np.asarray(prior[0])) ** 2))
        return goal(mats) + 0.05 * pen + 0.05 * twist + COMFORT * comfort + near
    best = None
    for x0 in starts:
        x0 = tuple(x0) + (0.0, 0.0) * (len(x0) == 5)
        x, v = nelder_mead(f, x0, iters=iters)
        if best is None or v < best[1]:
            best = (x, v)
    up, fo, ha = pose_vector(best[0])
    mats = scene.mats({"upper_" + tag: up, "fore_" + tag: fo, "hand_" + tag: ha}, fixed)
    _, flex, lift = arm_penalty(scene, mats, side)
    bend, sideways = wrist_bend(scene, mats, side)
    wrist_twist, fore_turn = gripcheck.arm_twist(scene.ch.body.hand_geometry[side], mats, side)
    return up, fo, ha, best[1], dict(elbow_flexion=round(flex, 1), arm_lift=round(lift, 1), wrist_bend=round(bend, 1),
                                    wrist_sideways=round(sideways, 1), wrist_twist=round(wrist_twist, 1),
                                    forearm_rotation=round(fore_turn, 1))
