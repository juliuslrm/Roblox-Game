"""Measurements that decide whether a trader holds a thing like a person would.

All limits scale with the trader's own hand: t = finger thickness, measured on the rig.  The checks:

  A contact      every finger of a wrapping grip touches the prop with its links (gap < 0.2 t),
                 the palm rests on it for power grips (< 0.6 t), the thumb touches it or the index
  B penetration  no hand vertex deeper than 0.3 t in the prop (skin gives a little at the joints);
                 the prop never enters the body (other than the holding hand) during the idle loop
  C grip region  the skin touches only the profile's region of the prop, never a forbidden part
  D joints       finger angles inside the anatomical limits; over the loop the wrist bent at most
                 50 degrees and 25 degrees sideways against the forearm (anatomically about 70 / 30),
                 elbow flexion 5 .. 145 degrees, upper arm < 110 degrees up
  E stability    the prop does not slide against the fingers during the loop (< 0.1 t)
  F motion       no jump between two samples or over the loop seam, no jitter
Mandatory (a grip with one of these fails whatever its score): B, C, wrist in D, no contact in A, E.

Scores (a development heuristic, not proof of realism): grip position 20, fingers and thumb 20,
wrist and arm 15, stability 15, motion 15, visual 15 (from the visual review only).
"""
import math

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from . import characters as C
from . import grips as G

FPS = 8


def _bvh(verts, faces):
    return BVHTree.FromPolygons([Vector(v) for v in verts], [list(f) for f in faces], all_triangles=False)


def _signed(bvh, pts):
    return C.signed_distance(bvh, pts)


def _angle(a, b):
    a = np.asarray(a) / np.linalg.norm(a)
    b = np.asarray(b) / np.linalg.norm(b)
    return math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(a, b))))))


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


def wrist_bend(geo, mats, side):
    """(bend, sideways bend) of the hand against the forearm in degrees (see armik.wrist_bend)."""
    fore = mats["lowerarm01." + side][:3, :3] @ geo["forearm"]
    hand = mats["wrist." + side][:3, :3] @ geo["hand"]
    palm = mats["wrist." + side][:3, :3] @ geo["palm"]
    palm = palm - np.dot(palm, hand) * hand
    palm /= np.linalg.norm(palm)
    side_axis = np.cross(hand, palm)
    bend = math.degrees(math.atan2(abs(float(np.dot(fore, palm))), float(np.dot(fore, hand))))
    sideways = math.degrees(math.atan2(abs(float(np.dot(fore, side_axis))), float(np.dot(fore, hand))))
    return bend, sideways


def _twist(D, axis):
    """Rotation angle (degrees, signed) of the 3x3 rotation D around `axis` (swing-twist split)."""
    from mathutils import Matrix
    q = Matrix(D.tolist()).to_quaternion()
    v = float(np.dot((q.x, q.y, q.z), axis))
    return math.degrees(2 * math.atan2(v, q.w)) if abs(q.w) > 1e-9 or abs(v) > 1e-9 else 0.0


def arm_twist(geo, mats, side):
    """(twist of the hand against the forearm, rotation of the forearm against the upper arm) in
    degrees, both around the forearm's axis.  The wrist itself hardly twists (the radius turns round
    the ulna, which is a forearm rotation); the forearm turns about 85 degrees each way from the
    neutral pose (thumb forwards)."""
    up, lo, wr = (mats[f"{b}.{side}"][:3, :3] for b in ("upperarm01", "lowerarm01", "wrist"))
    axis = geo["forearm"]
    wrist = _twist(np.linalg.inv(lo) @ wr, axis)
    fore = _twist(np.linalg.inv(up) @ wr, axis)
    return (wrist + 180) % 360 - 180, (fore + 180) % 360 - 180


def check_grip(ch, side):
    """All measurements of one hand.  -> dict with the values, the problems and the automated scores."""
    body = ch.body
    pid, mb, frame = ch.held[side]
    prof = G.PROFILES[pid]
    geo = body.hand_geometry[side]
    t = geo["finger_thickness"]
    prop = next(p for p in ch.pieces if p.name == "prop_" + side)
    bvh = _bvh(prop.verts, prop.faces)
    inv = np.linalg.inv(frame)
    out = {"profile": pid, "kind": prop.kind, "finger_thickness": round(t, 4), "hand_length": round(geo["length"], 3)}
    problems, mandatory = [], []

    # ---- A contact and B penetration, per finger and link
    touch, depth_limit = 0.2 * t, 0.3 * t
    fingers = {}
    deepest = 1.0
    contact_pts = []
    for i in range(1, 6):
        links = []
        for j in (1, 2, 3):
            mask = body.part == f"finger{i}-{j}.{side}"
            if not mask.any():
                links.append(None)
                continue
            d = _signed(bvh, body.verts[mask])
            links.append(float(d.min()))
            deepest = min(deepest, float(d.min()))
            contact_pts.append(body.verts[mask][d < touch])
        fingers[i] = dict(gaps=[None if g is None else round(g, 4) for g in links],
                          touching=sum(1 for g in links if g is not None and g < touch))
    palm_mask = body.part == "wrist." + side
    dp = _signed(bvh, body.verts[palm_mask])
    deepest = min(deepest, float(dp.min()))
    contact_pts.append(body.verts[palm_mask][dp < touch])
    out["fingers"] = fingers
    out["palm_gap"] = round(float(dp.min()), 4)
    out["deepest"] = round(deepest, 4)
    wrapped = [fingers[i]["touching"] for i in range(2, 6)]
    if prof["kind"] in ("power", "bundle", "ball", "hook"):
        for i in range(2, 6):
            if fingers[i]["touching"] == 0:
                problems.append(f"finger {i} does not touch the {pid}")
    if prof["palm"] and dp.min() > 0.6 * t:
        problems.append(f"palm {dp.min():.3f} studs from the {pid} (power grip needs it on the handle)")
    thumb_gap = min(g for g in fingers[1]["gaps"] if g is not None)
    if thumb_gap > touch:
        # a thumb may also rest on the index finger that holds the handle
        idx = np.isin(body.part, [f"finger2-{j}.{side}" for j in (1, 2, 3)])
        th = body.verts[np.isin(body.part, [f"finger1-{j}.{side}" for j in (2, 3)])]
        dmin = min(float(np.min(np.linalg.norm(body.verts[idx] - p, axis=1))) for p in th[::3]) if len(th) else 1.0
        if dmin > 0.6 * t:
            problems.append(f"thumb touches neither the {pid} nor the index finger ({thumb_gap:.3f})")
    if sum(f["touching"] for f in fingers.values()) == 0 and dp.min() > touch:
        mandatory.append(f"the {pid} floats: no part of the hand touches it")
    if deepest < -depth_limit:
        mandatory.append(f"the hand cuts {-deepest:.3f} studs into the {pid} (limit {depth_limit:.3f})")

    # ---- C grip region: where on the prop the skin touches
    pts = np.vstack([p for p in contact_pts if len(p)]) if any(len(p) for p in contact_pts) else np.zeros((0, 3))
    ys = []
    for p in pts:
        hit = bvh.find_nearest(Vector(p))
        if hit[0] is not None:
            ys.append(float((inv @ np.r_[np.array(hit[0]), 1.0])[1]))
    ys = np.array(ys)
    y0, y1 = prof["region"]
    inside = float(((ys >= y0) & (ys <= y1)).mean()) if len(ys) else 0.0
    out["contact_points"] = int(len(ys))
    out["contact_y"] = [round(float(ys.min()), 3), round(float(ys.max()), 3)] if len(ys) else None
    out["region_share"] = round(inside, 3)
    for name, f0, f1 in prof["forbidden"]:
        n = int(((ys >= f0) & (ys <= f1)).sum()) if len(ys) else 0
        if n:
            mandatory.append(f"the hand holds the {name} ({n} contact points)")
    if len(ys) and inside < 0.9:
        mandatory.append(f"only {inside:.0%} of the contact lies on the grip region {prof['region']} (y {ys.min():.2f}..{ys.max():.2f})")

    # ---- D joints
    ang = {i: r["angles"] for i, r in ch.report[side].items() if isinstance(i, int)}
    lim = {i: (C.THUMB_LIMIT if i == 1 else C.FINGER_LIMIT) for i in ang}
    over = [(i, k) for i in ang for k in range(3) if ang[i][k] > lim[i][k] + 0.1 or ang[i][k] < -25]
    if over:
        problems.append(f"finger joints outside their limits: {over}")
    role = ch.role
    duration = C.LOOPS[role]["duration"]
    count = int(round(duration * FPS))
    up, lo, wr = (f"{b}.{side}" for b in ("upperarm01", "lowerarm01", "wrist"))
    elbow, lift, wrists, frames, bends, sides, twists, turns = [], [], [], [], [], [], [], []
    for k in range(count):
        mats = body.bone_matrices(C.local_rotations(role, duration * k / count))
        b_, s_ = wrist_bend(geo, mats, side)
        tw_, fr_ = arm_twist(geo, mats, side)
        twists.append(abs(tw_))
        turns.append(abs(fr_))
        bends.append(b_)
        sides.append(s_)
        p = {b: (mats[b] @ np.r_[ch.heads[b], 1])[:3] for b in (up, lo, wr)}
        elbow.append(180 - _angle(p[up] - p[lo], p[wr] - p[lo]))
        lift.append(_angle(p[lo] - p[up], (0, 0, -1)))
        wrists.append(p[wr])
        frames.append(mats[wr])
    wrist = max(bends)
    out["wrist_bend"] = round(wrist, 1)
    out["wrist_sideways"] = round(max(sides), 1)
    if wrist > 50 or max(sides) > 25:
        mandatory.append(f"wrist bent {wrist:.0f} / sideways {max(sides):.0f} degrees against the forearm (limits 50 / 25)")
    out["wrist_twist"] = round(max(twists), 1)
    out["forearm_rotation"] = round(max(turns), 1)
    if max(twists) > 45 or max(turns) > 95:
        mandatory.append(f"hand twisted {max(twists):.0f} degrees in the wrist / forearm turned {max(turns):.0f} degrees "
                         f"(limits 45 / 95)")
    elif max(twists) > 30:
        problems.append(f"hand twisted {max(twists):.0f} degrees in the wrist (the forearm should turn instead)")
    out["elbow_flexion"] = [round(min(elbow), 1), round(max(elbow), 1)]
    out["arm_lift_max"] = round(max(lift), 1)
    if min(elbow) < 5 or max(elbow) > 145:
        problems.append(f"elbow flexion {min(elbow):.0f}..{max(elbow):.0f} degrees outside 5..145")
    if max(lift) > 110:
        problems.append(f"upper arm lifted {max(lift):.0f} degrees")

    # ---- E stability: contact pairs between prop and fingers keep their distance during the loop
    names, Wb = body.dense_weights()
    hand_idx = np.nonzero(np.isin(body.part, [f"finger{i}-{j}.{side}" for i in range(1, 6) for j in (1, 2, 3)]
                                  + ["wrist." + side]))[0]
    Ph = body.verts[hand_idx]
    sel = np.argsort(_signed(bvh, Ph))[:40]
    pairs_h = hand_idx[sel]
    pv = []
    for i in pairs_h:
        hit = bvh.find_nearest(Vector(body.verts[i]))
        pv.append(int(np.argmin(np.linalg.norm(prop.verts - np.array(hit[0]), axis=1))))
    rest_d = np.linalg.norm(body.verts[pairs_h] - prop.verts[pv], axis=1)
    drift = 0.0
    for k in range(0, count, 2):
        rots = C.local_rotations(role, duration * k / count)
        A = _posed(ch, Wb[pairs_h], body.verts[pairs_h], rots)
        B = _posed(ch, prop.weights[pv], prop.verts[pv], rots)
        drift = max(drift, float(np.max(np.abs(np.linalg.norm(A - B, axis=1) - rest_d))))
    out["slide"] = round(drift, 5)
    if drift > 0.1 * t:
        mandatory.append(f"the {pid} slides {drift:.3f} studs against the fingers during the loop")

    # ---- F motion: steps, seam and jitter of the hand path
    W_ = np.array(wrists + wrists[:1])
    steps = np.linalg.norm(np.diff(W_, axis=0), axis=1)
    jerk = np.linalg.norm(W_[2:] - 2 * W_[1:-1] + W_[:-2], axis=1)
    rot_steps = [_angle((frames[(k + 1) % count][:3, :3] @ np.array((0, 1.0, 0))), (frames[k][:3, :3] @ np.array((0, 1.0, 0))))
                 for k in range(count)]
    out["hand_step_max"] = round(float(steps.max()), 3)
    out["hand_turn_max_deg"] = round(max(rot_steps), 1)
    out["seam_step"] = round(float(steps[-1]), 3)
    out["jerk_max"] = round(float(jerk.max()), 3)
    if steps.max() > 0.6 or max(rot_steps) > 40:
        problems.append(f"the hand jumps {steps.max():.2f} studs / {max(rot_steps):.0f} degrees between two samples")
    if steps[-1] > 2.5 * max(1e-3, float(steps[-2]), float(steps[0])) and steps[-1] > 0.05:
        problems.append(f"the loop seam jumps {steps[-1]:.2f} studs")

    # ---- automated scores
    s_pos = 20 * inside if not any("holds the" in m for m in mandatory) else 0
    s_fing = 14 * float(np.mean(wrapped)) / 3 + (6 if thumb_gap <= touch or "thumb" not in " ".join(problems) else 0)
    s_arm = 15 - (4 if wrist > 30 else 0) - (11 if wrist > 50 else 0) \
        - 5 * sum(("elbow" in p or "upper arm" in p or "twisted" in p) for p in problems + mandatory)
    s_stab = 15 if drift <= 0.05 * t else (8 if drift <= 0.1 * t else 0)
    s_mot = 15 - 7 * sum("jumps" in p for p in problems)
    out["scores"] = dict(position=round(s_pos, 1), fingers=round(s_fing, 1), wrist_arm=max(0, s_arm), stability=s_stab,
                         motion=max(0, s_mot))
    out["problems"] = problems
    out["mandatory"] = mandatory
    return out


def prop_body_clearance(ch, posed_vertices):
    """Smallest signed distance (studs) of each prop to the skin of the body without the arms during
    the loop -> {side: (distance, time)}."""
    body = ch.body
    names, W = body.dense_weights()
    arm = W[:, [names.index(b) for b in names if b.startswith(("wrist", "lowerarm", "upperarm"))]].sum(axis=1) > 0.3
    faces = [body.faces[i] for i in body.face_ids("body")]
    faces = [f for f in faces if not arm[list(f)].any()]
    worst = {}
    duration = C.LOOPS[ch.role]["duration"]
    for k in range(0, int(duration * FPS), 2):
        t = k / FPS
        rots = C.local_rotations(ch.role, t)
        P = posed_vertices(ch, W, body.verts, rots)
        bvh = _bvh(P, faces)
        for side in ("L", "R"):
            prop = next(p for p in ch.pieces if p.name == "prop_" + side)
            Q = posed_vertices(ch, prop.weights, prop.verts, rots)[::5]
            d = _signed(bvh, Q).min()
            if side not in worst or d < worst[side][0]:
                worst[side] = (float(d), t)
    return worst
