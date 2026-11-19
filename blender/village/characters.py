"""The five market traders as realistic, skinned characters.

A trader is a shaped MakeHuman body (village/human.py) with its own clothes, hair, eyes and the
things it holds, bound to one reduced skeleton.  The build order is:

    body = make_body(role)        shape (gender, age, muscle, weight, race mix) and height
    rest_pose(body)               arms hanging, elbows slightly bent, hands turned so that the
                                  knuckle line runs front to back (thumb in front)
    grip_prop(body, side, ...)    every finger wraps the handle of the held thing (joint angles
                                  searched for the best wrap); baked into the rest pose
    ...                           clothes, hair, face, props (later modules)

Figure space: Z up, the figure faces -Y, its left side is +X, ground at z = 0, 1 unit = 1 stud.
"""
import math

import numpy as np
from mathutils import Matrix, Quaternion, Vector

from . import human as H

ROLES = ("selma", "nyra", "lio", "aron", "esme")

# body shape per trader: MakeHuman macro parameters (see human.macro_targets) and height in studs
SHAPE = {
    "selma": dict(gender=0.0, age=0.62, muscle=0.5, weight=0.62, race={"caucasian": 1.0}, height=6.15),
    "nyra": dict(gender=0.0, age=0.8, muscle=0.35, weight=0.42, race={"caucasian": 0.7, "asian": 0.3}, height=6.3),
    "lio": dict(gender=1.0, age=0.52, muscle=0.52, weight=0.44, race={"african": 0.6, "caucasian": 0.4}, height=6.45),
    "aron": dict(gender=1.0, age=0.64, muscle=0.88, weight=0.68, race={"caucasian": 1.0}, height=6.7),
    "esme": dict(gender=0.0, age=0.56, muscle=0.68, weight=0.5, race={"caucasian": 0.6, "african": 0.1, "asian": 0.3},
                 height=6.3),
}

SIDES = (("L", 1.0), ("R", -1.0))       # bone suffix, sign of x


def make_body(role):
    p = dict(SHAPE[role])
    height = p.pop("height")
    return H.Body.build(p, height)


def _head(body, bone):
    return np.asarray(body.bones[bone][0], dtype=np.float64)


def _unit(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def _twist_angle(R, axis):
    """Angle (degrees) of the twist part of rotation R about `axis` (swing-twist decomposition)."""
    q = Matrix(R.tolist()).to_quaternion()
    a = Vector(axis).normalized()
    p = Vector((q.x, q.y, q.z)).dot(a)
    return math.degrees(2 * math.atan2(p, q.w))


def _frame(d, k):
    """Orthonormal 3x3 frame with columns (d, k orthogonalised, d x k)."""
    d = _unit(d)
    k = _unit(k - np.dot(k, d) * d)
    return np.column_stack((d, k, np.cross(d, k)))


def hand_frame(body, side):
    """(finger direction, knuckle line index -> little finger) of a hand."""
    wrist = _head(body, "wrist." + side)
    index, little = _head(body, "finger2-1." + side), _head(body, "finger5-1." + side)
    return (index + little) / 2 - wrist, little - index


def rest_pose(body, upper_out=6.0, upper_fwd=4.0, elbow=10.0, shoulder_drop=4.0, stance=0.36, weight_leg=None,
              tilt=0.0):
    """Arms down along the body (A-pose of the base mesh -> village rest pose).  Each step rotates one
    bone and bakes the result, so every rotation is a plain world rotation about the bone head."""
    for side, sx in SIDES:
        up, low = "upperarm01." + side, "lowerarm01." + side
        d = _head(body, low) - _head(body, up)
        a, f = math.radians(upper_out), math.radians(upper_fwd)
        target = np.array((sx * math.sin(a), -math.sin(f), -math.cos(a) * math.cos(f)))
        body.apply_pose({up: H.rotation_between(d, target)})
        d = _head(body, "wrist." + side) - _head(body, low)
        e = math.radians(elbow)
        target = np.array((sx * math.sin(math.radians(2)), -math.sin(e), -math.cos(e)))
        body.apply_pose({low: H.rotation_between(d, target)})
        # turn the hand: fingers continue the forearm, knuckle line front -> back (index in front);
        # the twist is spread over the forearm like a real pronation
        axis = _unit(_head(body, "wrist." + side) - _head(body, low))
        fd, kn = hand_frame(body, side)
        R = _frame(axis, np.array((0.0, 1.0, 0.0))) @ _frame(fd, kn).T
        twist = _twist_angle(R, axis)
        body.apply_pose({low: H.rot(axis, twist * 0.3)})
        body.apply_pose({"lowerarm02." + side: H.rot(axis, twist * 0.45)})
        fd, kn = hand_frame(body, side)
        body.apply_pose({"wrist." + side: _frame(axis, np.array((0.0, 1.0, 0.0))) @ _frame(fd, kn).T})
        # shoulders relaxed: the clavicle drops a little
        body.apply_pose({"clavicle." + side: H.rot((0.0, 1.0, 0.0), sx * shoulder_drop)})
    for side, sx in SIDES:
        # legs closer together: the ankle comes in to `stance` from the middle, the foot stays flat
        hip, knee, ankle = (_head(body, b + side) for b in ("upperleg01.", "lowerleg01.", "foot."))
        target = np.array((sx * stance, ankle[1], ankle[2])) - hip
        turn = H.rotation_between(ankle - hip, target)
        body.apply_pose({"upperleg01." + side: turn})
        body.apply_pose({"foot." + side: turn.T})
    if weight_leg:
        contrapposto(body, weight_leg, tilt)
    # stand on the ground with the soles of the skin (the helper geometry of the base mesh reaches lower)
    skin = sorted({v for i in body.face_ids("body") for v in body.faces[i]})
    lift = body.verts[skin, 2].min()
    body.verts[:, 2] -= lift
    body.bones = {b: (h - (0, 0, lift), t - (0, 0, lift)) for b, (h, t) in body.bones.items()}
    return body


# weight on one leg (contrapposto) per trader: standing leg, pelvis tilt in degrees
STANCE = {"selma": ("R", 2.5), "nyra": ("L", 2.0), "lio": ("L", 3.0), "aron": ("R", 2.0), "esme": ("L", 3.0)}


def contrapposto(body, weight_leg, tilt):
    """Weight on one leg: the pelvis rises on the standing side, the spine leans back the other way so
    the shoulders stay nearly level, the free leg bends its knee just enough for both soles to stay on
    the ground; both feet keep their place and stay flat.  The upper body keeps its orientation within
    a fraction of a degree, so the solved arm poses and grips stay valid."""
    sx = 1.0 if weight_leg == "L" else -1.0
    ankles = {s: _head(body, "foot." + s) for s, _ in SIDES}
    foot_dir = {s: np.asarray(body.bones["foot." + s][1]) - ankles[s] for s, _ in SIDES}
    body.apply_pose({"root": H.rot((0.0, 1.0, 0.0), -sx * tilt)})
    body.apply_pose({"spine05": H.rot((0.0, 1.0, 0.0), sx * tilt * 1.15)})

    def aim(side):
        hip = _head(body, "upperleg01." + side)
        now = _head(body, "foot." + side)
        want = np.array((ankles[side][0], ankles[side][1], now[2]))
        turn = H.rotation_between(now - hip, want - hip)
        body.apply_pose({"upperleg01." + side: turn})
        body.apply_pose({"foot." + side: turn.T})
    for side, _ in SIDES:
        aim(side)
    stand = "L" if sx > 0 else "R"
    free = "R" if stand == "L" else "L"
    target_z = _head(body, "foot." + stand)[2]
    # bend the free knee (thigh forward, shin back) until its ankle is as high as the standing one
    lo, hi = 0.0, 30.0
    snapshot = (body.verts.copy(), dict(body.bones))
    for _ in range(18):
        mid = (lo + hi) / 2
        body.verts, body.bones = snapshot[0].copy(), dict(snapshot[1])
        knee = _head(body, "lowerleg01." + free)
        body.apply_pose({"upperleg01." + free: H.rot((1.0, 0.0, 0.0), -mid * 0.5)})
        body.apply_pose({"lowerleg01." + free: H.rot((1.0, 0.0, 0.0), mid)})
        if _head(body, "foot." + free)[2] < target_z:
            lo = mid
        else:
            hi = mid
    aim(free)
    # both feet keep the direction they had (flat on the ground)
    for side, _ in SIDES:
        foot = _head(body, "foot." + side)
        toe = np.asarray(body.bones["foot." + side][1])
        body.apply_pose({"foot." + side: H.rotation_between(toe - foot, foot_dir[side])})
    return body


# ---------------------------------------------------------------- holding things
FINGER_LIMIT = (95.0, 110.0, 85.0)      # degrees
THUMB_RATIO = (0.55, 1.0, 1.0)
THUMB_LIMIT = (50.0, 65.0, 75.0)
PENETRATION = 0.004                     # studs: skin may press this far into a handle
CREASE = 0.016                          # extra give of the flesh right at a finger joint
STEP = 1.5                              # degrees per closing step


def hand_axes(body, side):
    """Grip frame of a hand in the rest pose: origin = middle of the knuckle line, ey = knuckle line
    (index -> little finger), ez = towards the wrist, ex = ey x ez; pn = palm normal."""
    sx = dict(SIDES)[side]
    wrist = _head(body, "wrist." + side)
    bases = [_head(body, f"finger{i}-1.{side}") for i in range(2, 6)]
    origin = np.mean(bases, axis=0)
    ey = _unit(bases[3] - bases[0])
    ez = wrist - origin
    ez = _unit(ez - np.dot(ez, ey) * ey)
    ex = np.cross(ey, ez)
    pn = -sx * ex
    return origin, ex, ey, ez, pn


class Hand:
    """Vertices, weights and signed distance for closing one hand around a prop."""

    def __init__(self, body, side):
        self.body, self.side = body, side
        names, W = body.dense_weights()
        self.names = names
        bones = ["wrist." + side] + [f"finger{i}-{j}.{side}" for i in range(1, 6) for j in range(1, 4)]
        cols = [names.index(b) for b in bones]
        mask = W[:, cols].sum(axis=1) > 0.05
        self.idx = np.nonzero(mask)[0]
        self.W = W[self.idx]
        dom = np.argmax(self.W, axis=1)
        self.dominant = np.array([names[k] for k in dom])
        self.rest = body.verts[self.idx]

    def posed(self, rots):
        mats = self.body.bone_matrices(rots)
        vh = np.c_[self.rest, np.ones(len(self.rest))]
        out = np.zeros_like(self.rest)
        for j, b in enumerate(self.names):
            w = self.W[:, j]
            nz = w > 0
            if nz.any():
                out[nz] += w[nz, None] * (vh[nz] @ mats[b].T)[:, :3]
        return out

    def link(self, bone):
        return self.dominant == bone


_RAY = Vector((0.5773, 0.5774, 0.5774))


def _inside(bvh, co):
    """Ray parity test (robust in dents of noisy shapes, where the nearest face normal misleads)."""
    hits, origin = 0, co
    for _ in range(64):
        loc, _n, _i, _d = bvh.ray_cast(origin, _RAY)
        if loc is None:
            break
        hits += 1
        origin = loc + _RAY * 1e-5
    return hits % 2 == 1


def signed_distance(bvh, pts):
    """Distance of points to a closed mesh; negative inside."""
    out = np.empty(len(pts))
    for i, p in enumerate(pts):
        co = Vector(p)
        hit = bvh.find_nearest(co)
        if hit[0] is None:
            out[i] = 1e3
            continue
        d = (co - hit[0])
        inside = d.dot(hit[1]) < 0
        if inside or d.length < 0.02:
            inside = _inside(bvh, co)
        out[i] = -d.length if inside else d.length
    return out


def prop_bvh(mb, matrix):
    """BVH of a prop (MeshBuilder in prop space) placed with a 4x4 numpy matrix."""
    from mathutils.bvhtree import BVHTree
    M = Matrix(matrix.tolist())
    verts = [M @ v for v in mb.verts]
    return BVHTree.FromPolygons(verts, [list(f) for f in mb.faces], all_triangles=False)


def place_prop(body, side, mb, tilt, along=-0.015, gap=0.004):
    """Prop frame (4x4) in figure space: handle axis along the knuckle line, tilted by `tilt` degrees
    (the little finger end towards the wrist, as in a real power grip), pushed against the palm until
    the skin touches it."""
    origin, ex, ey, ez, pn = hand_axes(body, side)
    Rp = np.column_stack((ex, ey, ez)) @ H.rot((1.0, 0.0, 0.0), tilt)
    hand = Hand(body, side)
    contact = np.isin(hand.dominant, ["wrist." + side] + [f"finger{i}-1.{side}" for i in range(2, 6)])
    pts = hand.posed(open_hand(body, side))[contact]

    def frame(d):
        M = np.eye(4)
        M[:3, :3] = Rp
        M[:3, 3] = origin + ez * along + pn * d
        return M

    lo, hi = 0.0, 0.6
    for _ in range(26):                         # smallest distance from the palm without touching
        mid = (lo + hi) / 2
        if signed_distance(prop_bvh(mb, frame(mid)), pts).min() < gap:
            lo = mid
        else:
            hi = mid
    return frame(hi)


OPEN = (-12.0, -18.0, -10.0)            # degrees: the open hand before it closes around a prop
THUMB_OPEN = (-20.0, -10.0, -5.0)


def _finger_axes(body, side, i, pn, axis_point=None, axis_dir=None):
    axes = []
    for j in (1, 2, 3):
        h, t = (np.asarray(x) for x in body.bones[f"finger{i}-{j}.{side}"])
        seg = _unit(t - h)
        if i == 1 and axis_point is not None:           # thumb: turns towards the handle axis
            rel = h - axis_point
            toward = -(rel - np.dot(rel, axis_dir) * axis_dir)
            axes.append(_unit(np.cross(seg, _unit(toward))))
        elif i == 1:                                     # thumb, no prop yet: across the palm
            axes.append(_unit(np.cross(seg, pn)))
        else:
            axes.append(_unit(np.cross(seg, pn)))
    return axes


def open_hand(body, side):
    """Finger rotations of the opened hand (fingers stretched, thumb spread)."""
    pn = hand_axes(body, side)[4]
    rots = {}
    for i in range(1, 6):
        start = THUMB_OPEN if i == 1 else OPEN
        for j, ax in zip((1, 2, 3), _finger_axes(body, side, i, pn)):
            rots[f"finger{i}-{j}.{side}"] = H.rot(ax, start[j - 1])
    return rots


def _close(hand, rots, chain, axes, ratio, limit, bvh, start=(0.0, 0.0, 0.0)):
    """Closes one finger around the prop like a real power grip: the base joint folds the first link
    onto the handle, then the middle joint wraps the middle link over it, then the tip joint.  A joint
    stops when it would press any link from its own outwards deeper into the prop than allowed."""
    angles = list(start)
    links = [hand.link(b) for b in chain]
    # the flesh in the crease of a joint gives way: vertices close to the joint of their link may
    # press deeper into the handle than the pads
    tolerance = []
    for b, link in zip(chain, links):
        h, t = (np.asarray(x) for x in hand.body.bones[b])
        dist = np.linalg.norm(hand.rest[link] - h, axis=1) / max(1e-6, np.linalg.norm(t - h))
        tolerance.append(PENETRATION + CREASE * np.clip(1 - dist / 0.5, 0, 1))

    def depths(ang):
        local = dict(rots)
        for b, ax, a in zip(chain, axes, ang):
            local[b] = H.rot(ax, a)
        pts = hand.posed(local)
        return [float((signed_distance(bvh, pts[link]) + tol).min()) if link.any() else 1.0
                for link, tol in zip(links, tolerance)]
    base = depths(angles)               # a cloth corner may touch a finger from the start
    for j in range(3):
        while angles[j] < limit[j]:
            trial = list(angles)
            trial[j] = min(limit[j], angles[j] + STEP * ratio[j])
            d = depths(trial)
            if any(d[k] < min(0.0, base[k]) - 1e-4 for k in range(j, 3)):
                break
            angles = trial
    for b, ax, a in zip(chain, axes, angles):
        rots[b] = H.rot(ax, a)
    return angles


# ---------------------------------------------------------------- assembly
GRIP_LIMITS = dict(contact=0.025, depth=-0.02)      # studs: every finger near the prop, none deep inside


def prepared_body(role):
    """Shaped body in the rest pose with both hands closed around their props.  Returns the body
    (finger and twist bones merged away), the props (MeshBuilder, 4x4 frame) and the grip report."""
    from . import grips as G
    from . import handheld as P
    from .meshkit import MeshBuilder
    leg, tilt = STANCE.get(role, (None, 0.0))
    body = rest_pose(make_body(role), weight_leg=leg, tilt=tilt)
    held, report = {}, {}
    for side, sx in SIDES:
        prof = G.profile(role, side)
        fn = getattr(P, prof["builder"])
        mb = MeshBuilder(seed=len(role) * 7 + (1 if side == "L" else 2))
        fn(mb, sx)
        frame, rots, rep = grip_prop(body, side, mb, prof["tilt"], G.ALONG[prof["kind"]])
        body.apply_pose(rots)
        held[side] = (G.HELD[role][side], mb, frame)
        report[side] = rep
    # remember for the validator what the finger bones were before they are merged into the hand
    names, W = body.dense_weights()
    body.part = np.array([names[i] for i in np.argmax(W, axis=1)])
    body.hand_geometry = {}
    for side, _sx in SIDES:
        wrist, elbow = _head(body, "wrist." + side), _head(body, "lowerarm01." + side)
        bases = [_head(body, f"finger{i}-1.{side}") for i in range(2, 6)]
        chain3 = [body.bones[f"finger3-{j}.{side}"] for j in (1, 2, 3)]
        length = float(np.linalg.norm(bases[1] - wrist) + sum(np.linalg.norm(np.asarray(t) - np.asarray(h)) for h, t in chain3))
        links = [f"finger{i}-{j}.{side}" for i in range(2, 6) for j in (1, 2, 3)]
        radii = []
        for b in links:
            h, t = (np.asarray(x) for x in body.bones[b])
            P_ = body.verts[body.part == b]
            if len(P_):
                d = (t - h) / np.linalg.norm(t - h)
                q = P_ - h
                radii.append(np.median(np.linalg.norm(q - np.outer(q @ d, d), axis=1)))
        body.hand_geometry[side] = dict(forearm=_unit(wrist - elbow), hand=_unit(np.mean(bases, axis=0) - wrist),
                                        palm=hand_axes(body, side)[4],
                                        length=length,
                                        finger_thickness=float(2 * np.median(radii)))
    # the finger bones stay in the rig (the grip is their rest pose, so they can open, close and
    # adjust at run time); only the twist bones that spread the forearm turn while posing go
    merge = [f"{b}.{s}" for s, _ in SIDES for b in ("lowerarm02", "upperarm02")]
    body.merge_bones(merge)
    return body, held, report


def grip_problems(report):
    out = []
    for side, fingers in report.items():
        for i, r in fingers.items():
            if i == "fit":
                continue
            if i != 1 and r.get("touching", 3) < 2:        # wrapped: at least two links of a finger on the handle
                out.append(f"hand {side} finger {i}: only {r.get('touching')} of 3 links on the prop")
            if min(r["tip_gap"], r["deepest"]) > GRIP_LIMITS["contact"]:
                out.append(f"hand {side} finger {i}: {min(r['tip_gap'], r['deepest']):.3f} studs from the prop")
            if r["deepest"] < GRIP_LIMITS["depth"]:
                out.append(f"hand {side} finger {i}: {r['deepest']:.3f} studs inside the prop")
    return out


class Character:
    """A finished trader: pieces (meshes with weights over `bones`), the skeleton and grip report."""

    def __init__(self, role, body, pieces, report):
        self.role = role
        self.body = body
        self.bones = list(body.order)
        self.parents = dict(body.parents)
        self.heads = {b: np.asarray(body.bones[b][0]) for b in self.bones}
        self.tails = {b: np.asarray(body.bones[b][1]) for b in self.bones}
        self.pieces = pieces
        self.report = report
        self.held = {}                  # side -> (profile id, MeshBuilder in prop space, prop frame 4x4)


def _skin_colors(anat, head, role):
    from . import outfits as O
    from .wardrobe import rgb
    V = anat.V
    col = np.tile(rgb(O.COLORS[role]["skin"]), (len(V), 1))
    m = head.mouth

    def blend(mask_w, target):
        w = np.clip(mask_w, 0, 1)[:, None]
        return col * (1 - w) + target * w
    front = (V[:, 1] < head.centre[1] - 0.08).astype(float)
    lips = np.exp(-(((V[:, 0] - m[0]) / 0.055) ** 2 + ((V[:, 2] - m[2]) / 0.022) ** 2) * 1.6) * front
    col = blend(lips * 0.85, rgb(O.COLORS[role]["lips"]))
    for side, (c, r) in head.eyes.items():
        cheek = c + np.array((0.0, -0.02, -0.11))
        d = np.linalg.norm(V - cheek, axis=1)
        col = blend(np.exp(-(d / 0.07) ** 2) * 0.22 * front, np.array((0.85, 0.45, 0.42)))
        d = np.linalg.norm(V - c, axis=1)
        col = col * (1 - 0.05 * np.exp(-(d / (r * 1.7)) ** 2))[:, None]          # faint shadow in the eye socket
    ears = np.exp(-((np.abs(V[:, 0]) - head.half_w) / 0.05) ** 2) * np.exp(-((V[:, 2] - head.eye_z + 0.05) / 0.12) ** 2)
    col = blend(ears * 0.25 * (anat.weight(("head",)) > 0.5), np.array((0.85, 0.5, 0.45)))
    hands = anat.weight(("wrist",))
    col = col * (1 - 0.05 * hands)[:, None]
    return np.clip(col, 0, 1)


def _prop_piece(anat, side, name, mb, frame):
    from . import palette
    from . import wardrobe as Wd
    M = np.asarray(frame)
    V = np.array([tuple(v) for v in mb.verts])
    V = (np.c_[V, np.ones(len(V))] @ M.T)[:, :3]
    # one vertex per face corner so palette colours and tones stay crisp
    verts, faces, cols = [], [], []
    for f, cname, shades in zip(mb.faces, mb.colors, mb.shades):
        base = len(verts)
        for i, s in zip(f, shades):
            verts.append(V[i])
            cols.append(palette.tone(palette.RGB[cname], s))
        faces.append(tuple(range(base, base + len(f))))
    W = Wd.fixed_weights(anat, len(verts), "wrist." + side)
    kind = "prop_" + name
    return Wd.Piece(f"prop_{side}", np.array(verts), faces, W, np.array(cols), kind, smooth=False)


def build(role, seed=None):
    """The complete trader (see Character)."""
    import random
    from . import heads as Hd
    from . import looks as Lk
    from . import outfits as O
    from . import wardrobe as Wd
    rng = random.Random(seed if seed is not None else sum(map(ord, role)))
    body, held, report = prepared_body(role)
    anat = Wd.Anatomy(body)
    pieces, covered = O.OUTFITS[role](anat)
    head_pieces, scalp = Lk.LOOKS[role](anat, rng)
    pieces += head_pieces
    covered |= scalp
    head = Hd.Head(anat)
    skin_faces = [f for f in anat.faces if not covered[list(f)].all()]
    used = sorted({v for f in skin_faces for v in f})
    rm = {v: k for k, v in enumerate(used)}
    colors = _skin_colors(anat, head, role)
    skin = Wd.Piece("skin", anat.V[used], [tuple(rm[v] for v in f) for f in skin_faces], anat.W[used], colors[used], "skin")
    pieces.insert(0, skin)
    for side, (name, mb, frame) in held.items():
        pieces.append(_prop_piece(anat, side, name, mb, frame))
    ch = Character(role, body, pieces, report)
    ch.held = held
    return ch


# ---------------------------------------------------------------- idle loops
# Joint angles in degrees (figure axes, the figure faces -Y), relative to the rest pose:
#   torso / head: (rx = nod forwards +, ry = tilt to the figure's left -, rz = turn to the figure's left +)
#   upper arm:    (rx = swing forwards -, ry = lift sideways: left arm -, right arm +,
#                  rz = turn the raised forearm inwards: left arm -, right arm +)
#   forearm:      (rx = bend forwards -, ry, rz = twist)
#   hand:         (rx, ry, rz) turn of the wrist (figure axes); the solver keeps the bend against the
#                 forearm within 45 degrees and the sideways bend within 20 degrees
# Keys are (time in seconds, value); values between keys are eased; the last key equals the first.
# A basket or lantern hangs from its bail: those arms stay low (a raised fist could not carry it
# hanging straight).
LOOPS = {
    # Selma smells the herbs, nods, lays them towards the basket and looks up at the customers.
    "selma": dict(duration=8.0, keys={
        "upper_l": [(0, (-4, -13, 0)), (4, (-7, -14, 0)), (6, (-2, -12, 0)), (8, (-4, -13, 0))],
        "fore_l": [(0, (-4, 0, 0)), (4, (-8, 0, 0)), (6, (-2, 0, 0)), (8, (-4, 0, 0))],
        "upper_r": [(0, (-22, 6, 0)), (1.6, (-44, 2, 26)), (3.4, (-44, 2, 26)), (5.2, (-26, 0, 34)), (6.4, (-26, 0, 34)),
                    (8, (-22, 6, 0))],
        "fore_r": [(0, (-56, 0, 0)), (1.6, (-92, 0, 0)), (3.4, (-88, 0, 0)), (5.2, (-52, 0, 0)), (6.4, (-48, 0, 0)),
                   (8, (-56, 0, 0))],
        "head": [(0, (0, 0, 8)), (1.6, (9, 0, -6)), (3.4, (10, 2, -6)), (4.4, (-4, 0, -4)), (5.4, (12, -4, 16)),
                 (6.6, (-2, 0, 18)), (8, (0, 0, 8))],
        "torso": [(0, (0, 0, 2)), (2.4, (4, 0, -3)), (5.4, (2, 0, 6)), (8, (0, 0, 2))],
    }),
    # Nyra holds the crystal in front of her chest (solved: blender/solve_poses.py) and turns it in
    # her fingers; the lantern sways a little.
    "nyra": dict(duration=7.0, keys={
        "upper_l": [(0, (-3, -9, 0)), (2, (-8, -10, 0)), (5, (-6, -10, 0)), (7, (-3, -9, 0))],
        "fore_l": [(0, (-4, 0, 0)), (2, (-6, 0, 0)), (5, (-8, 0, 0)), (7, (-4, 0, 0))],
        "upper_r": [(0, (-4, 4, 4)), (2.25, (-1.8, -8.0, -1.1)), (3.25, (-3.4, -5.9, 16.9)),
                   (4.25, (-0.8, -9.1, -12.2)), (5.25, (-1.8, -8.0, -1.1)), (7, (-4, 4, 4))],
        "fore_r": [(0, (-70, 0, 0)), (2.25, (-117.4, 0.0, 8.9)), (3.25, (-116.0, 0.0, -9.4)),
                  (4.25, (-118.1, 0.0, 19.4)), (5.25, (-117.4, 0.0, 8.9)), (7, (-70, 0, 0))],
        "hand_r": [(0, (0, 0, 0)), (2.25, (20.2, 0.0, -19.1)), (3.25, (13.7, 0.0, -19.6)), (4.25, (19.4, 0.0, -7.7)),
                  (5.25, (20.2, 0.0, -19.1)), (7, (0, 0, 0))],
        "head": [(0, (4, 0, -6)), (2.25, (14, 0, 10)), (3.75, (16, 3, 8)), (5.25, (14, -2, 10)), (7, (4, 0, -6))],
        "torso": [(0, (0, 0, 0)), (3.5, (3, 0, 3)), (7, (0, 0, 0))],
    }),
    # Lio holds the bottle upright at his lower chest and rubs it with the cloth, then holds it up to
    # the light beside his face and turns it (poses solved: blender/solve_poses.py).
    "lio": dict(duration=6.5, keys={
        "upper_l": [(0, (22.4, -11.5, -22.8)), (0.5, (22.6, -11.5, -23.5)), (1.0, (22.4, -11.5, -22.8)),
                   (1.5, (22.6, -11.5, -23.5)), (2.0, (22.4, -11.5, -22.8)), (3.375, (-4, -8, -2)),
                   (5.375, (-4, -8, -2)), (6.5, (22.4, -11.5, -22.8))],
        "fore_l": [(0, (-112.2, 0.0, -14.5)), (0.5, (-107.6, 0.0, -14.1)), (1.0, (-112.2, 0.0, -14.5)),
                  (1.5, (-107.6, 0.0, -14.1)), (2.0, (-112.2, 0.0, -14.5)), (3.375, (-30, 0, 0)),
                  (5.375, (-30, 0, 0)), (6.5, (-112.2, 0.0, -14.5))],
        "hand_l": [(0, (-2.7, 0.0, -7.7)), (0.5, (-2.6, 0.0, -8.4)), (1.0, (-2.7, 0.0, -7.7)),
                  (1.5, (-2.6, 0.0, -8.4)), (2.0, (-2.7, 0.0, -7.7)), (3.375, (0, 0, 0)), (5.375, (0, 0, 0)),
                  (6.5, (-2.7, 0.0, -7.7))],
        "upper_r": [(0, (25.5, 19.2, 22.6)), (2.0, (25.5, 19.2, 22.6)), (3.625, (-57.0, 14.1, -10.1)),
                   (4.375, (-52.2, 24.4, 5.8)), (5.125, (-57.0, 14.1, -10.1)), (6.5, (25.5, 19.2, 22.6))],
        "fore_r": [(0, (-111.5, 0.0, 13.5)), (2.0, (-111.5, 0.0, 13.5)), (3.625, (-89.6, 0.0, -5.0)),
                  (4.375, (-89.8, 0.0, -26.6)), (5.125, (-89.6, 0.0, -5.0)), (6.5, (-111.5, 0.0, 13.5))],
        "hand_r": [(0, (-3.8, 0.0, -8.0)), (2.0, (-3.8, 0.0, -8.0)), (3.625, (20.2, 0.0, -19.1)),
                  (4.375, (20.2, 0.0, -19.1)), (5.125, (20.2, 0.0, -19.1)), (6.5, (-3.8, 0.0, -8.0))],
        "head": [(0, (18, 0, -4)), (2.0, (18, 0, -4)), (3.625, (-8, 4, -24)), (5.125, (-8, 4, -24)), (6.5, (18, 0, -4))],
        "torso": [(0, (4, 0, 0)), (3.6, (-2, 0, -6)), (5.2, (-2, 0, -6)), (6.5, (4, 0, 0))],
    }),
    # Aron holds the ore in front of his belly and taps it twice with the hammer: the hammer head meets
    # the ore's surface at the taps (1.75 s and 2.625 s); the swing is a solved path along the line of
    # the blow with one pose per sample (blender/solve_poses.py), so the head never passes through the ore.
    "aron": dict(duration=6.0, keys={
        "upper_l": [(0, (11.2, 0.7, -5.8)), (4.25, (11.2, 0.7, -5.8)), (5.0, (7.2, 0.7, -5.8)), (6, (11.2, 0.7, -5.8))],
        "fore_l": [(0, (-97.0, 0.0, -9.9)), (4.25, (-97.0, 0.0, -9.9)), (5.0, (-108.0, 0.0, -9.9)), (6, (-97.0, 0.0, -9.9))],
        "hand_l": [(0, (-1.8, 0.0, -2.5)), (6, (-1.8, 0.0, -2.5))],
        "upper_r": [(0, (-6, 10, 6)), (0.95, (66.2, 41.1, 45.8)), (1.125, (66.2, 41.1, 45.8)),
                   (1.25, (55.5, 37.4, 40.0)), (1.375, (46.8, 34.3, 35.4)), (1.5, (41.8, 32.2, 32.5)),
                   (1.625, (38.2, 30.6, 30.8)), (1.75, (36.3, 29.1, 30.7)), (1.875, (41.8, 32.2, 32.5)),
                   (2.0, (46.8, 34.3, 35.4)), (2.125, (55.5, 37.4, 40.0)), (2.25, (46.8, 34.3, 35.4)),
                   (2.375, (41.8, 32.2, 32.5)), (2.5, (38.2, 30.6, 30.8)), (2.625, (36.3, 29.1, 30.7)),
                   (2.75, (41.8, 32.2, 32.5)), (2.875, (46.8, 34.3, 35.4)), (3.0, (55.5, 37.4, 40.0)),
                   (3.125, (66.2, 41.1, 45.8)), (3.3, (66.2, 41.1, 45.8)), (4.25, (-6, 10, 6)), (6, (-6, 10, 6))],
        "fore_r": [(0, (-30, 0, 0)), (0.95, (-114.0, 0.0, 31.5)), (1.125, (-114.0, 0.0, 31.5)),
                  (1.25, (-107.6, 0.0, 26.8)), (1.375, (-100.9, 0.0, 20.5)), (1.5, (-97.2, 0.0, 16.2)),
                  (1.625, (-94.5, 0.0, 13.4)), (1.75, (-92.5, 0.0, 13.0)), (1.875, (-97.2, 0.0, 16.2)),
                  (2.0, (-100.9, 0.0, 20.5)), (2.125, (-107.6, 0.0, 26.8)), (2.25, (-100.9, 0.0, 20.5)),
                  (2.375, (-97.2, 0.0, 16.2)), (2.5, (-94.5, 0.0, 13.4)), (2.625, (-92.5, 0.0, 13.0)),
                  (2.75, (-97.2, 0.0, 16.2)), (2.875, (-100.9, 0.0, 20.5)), (3.0, (-107.6, 0.0, 26.8)),
                  (3.125, (-114.0, 0.0, 31.5)), (3.3, (-114.0, 0.0, 31.5)), (4.25, (-30, 0, 0)), (6, (-30, 0, 0))],
        "hand_r": [(0, (0, 0, 0)), (0.95, (-21.3, 0.0, -20.4)), (1.125, (-21.3, 0.0, -20.4)),
                  (1.25, (-20.8, 0.0, -17.5)), (1.375, (-20.9, 0.0, -11.1)), (1.5, (-21.0, 0.0, -5.2)),
                  (1.625, (-21.2, 0.0, -0.7)), (1.75, (-21.0, 0.0, -1.0)), (1.875, (-21.0, 0.0, -5.2)),
                  (2.0, (-20.9, 0.0, -11.1)), (2.125, (-20.8, 0.0, -17.5)), (2.25, (-20.9, 0.0, -11.1)),
                  (2.375, (-21.0, 0.0, -5.2)), (2.5, (-21.2, 0.0, -0.7)), (2.625, (-21.0, 0.0, -1.0)),
                  (2.75, (-21.0, 0.0, -5.2)), (2.875, (-20.9, 0.0, -11.1)), (3.0, (-20.8, 0.0, -17.5)),
                  (3.125, (-21.3, 0.0, -20.4)), (3.3, (-21.3, 0.0, -20.4)), (4.25, (0, 0, 0)), (6, (0, 0, 0))],
        "head": [(0, (14, 0, 4)), (1.2, (22, 0, 2)), (2.4, (22, 0, 2)), (3.4, (10, 0, 4)), (4.4, (16, -4, 8)),
                 (5.2, (10, 0, 6)), (6, (14, 0, 4))],
        "torso": [(0, (2, 0, 0)), (1.2, (6, 0, -2)), (2.4, (6, 0, -2)), (4.4, (2, 0, 4)), (6, (2, 0, 0))],
    }),
    # Esme rests the axe on her right shoulder (the handle lies on it; pose solved:
    # blender/solve_poses.py) and sights along the folding rule.
    "esme": dict(duration=8.0, keys={
        "upper_r": [(0, (-27.6, -10.2, 1.7)), (2, (-28.6, -10.2, 1.7)), (4, (-27.6, -10.2, 1.7)),
                   (6, (-28.6, -10.2, 1.7)), (8, (-27.6, -10.2, 1.7))],
        "fore_r": [(0, (-134.7, 0.0, 1.2)), (4, (-133.7, 0.0, 1.2)), (8, (-134.7, 0.0, 1.2))],
        "hand_r": [(0, (-21.8, 0.0, -1.5)), (8, (-21.8, 0.0, -1.5))],
        "upper_l": [(0, (-20, -8, 0)), (2.2, (-68, -20, 12)), (3.4, (-68, -30, 26)), (4.6, (-68, -20, 12)),
                    (5.6, (-68, -20, 12)), (8, (-20, -8, 0))],
        "fore_l": [(0, (-54, 0, 0)), (2.2, (-34, 0, 0)), (3.4, (-26, 0, 0)), (4.6, (-34, 0, 0)), (5.6, (-40, 0, 0)),
                   (8, (-54, 0, 0))],
        "head": [(0, (0, 0, -4)), (2.2, (4, 0, 14)), (3.4, (4, 0, 28)), (4.6, (4, 0, 14)), (5.6, (8, 4, 12)),
                 (6.8, (-2, 0, -2)), (8, (0, 0, -4))],
        "torso": [(0, (0, 0, -2)), (3.4, (2, 0, 6)), (5.6, (2, 0, 4)), (8, (0, 0, -2))],
    }),
}

# ---------------------------------------------------------------- face rig poses
# Expressions of the bone face rig (human.FACE).  Per bone: rotation (degrees, figure axes, about the
# bone head) and/or move (studs, figure axes: x = figure's left, y = back, z = up; 0.0037 studs = 1 mm).
# ".X" entries are mirrored to both sides (x of the move flips for the right side).  At run time the
# client blends them with weights 0..1 (MarketMotion.poses); the rest pose is the neutral face.
FACE_POSES = {
    "blink": {"orbicularis03.X": dict(rot=(30, 0, 0)), "orbicularis04.X": dict(rot=(-7, 0, 0))},
    "smile": {"oris03.X": dict(move=(0.021, 0.009, 0.022)), "oris07.X": dict(move=(0.014, 0.006, 0.015)),
              "risorius03.X": dict(move=(0.006, 0.003, 0.018)), "orbicularis04.X": dict(rot=(-8, 0, 0)),
              "oris05": dict(move=(0.0, 0.0, -0.008)), "oris01": dict(move=(0.0, 0.0, 0.008))},     # lips stay closed
    "brows_up": {"oculi01.X": dict(move=(0.0, 0.0, 0.016)), "orbicularis03.X": dict(rot=(-5, 0, 0))},
    "focus": {"oculi01.X": dict(move=(-0.003, 0.0, -0.006)), "orbicularis03.X": dict(rot=(9, 0, 0)),
              "orbicularis04.X": dict(rot=(-4, 0, 0))},
    "talk": {"jaw": dict(rot=(4, 0, 0)), "oris05": dict(move=(0.0, 0.0, 0.002))},
    "skeptic": {"oculi01.L": dict(move=(0.0, 0.0, 0.010)), "oculi01.R": dict(move=(0.002, 0.0, -0.005)),
                "oris03.L": dict(move=(0.004, 0.0, 0.004)), "orbicularis03.R": dict(rot=(7, 0, 0))},
}


def face_pose(name, weight=1.0):
    """-> (rotations, moves) of one expression at `weight`, ready for Body.bone_matrices."""
    rots, moves = {}, {}
    for key, spec in FACE_POSES[name].items():
        sides = (("L", 1.0), ("R", -1.0)) if key.endswith(".X") else ((None, 1.0),)
        for side, sx in sides:
            bone = key[:-2] + "." + side if side else key
            if "rot" in spec:
                rx, ry, rz = (weight * a for a in spec["rot"])
                rots[bone] = _euler((rx, sx * ry, sx * rz))
            if "move" in spec:
                x, y, z = spec["move"]
                moves[bone] = np.array((sx * x, y, z)) * weight
    return rots, moves


# loop channel -> bones that share its rotation (fraction of the angles each)
CHANNELS = {
    "torso": (("spine03", 0.5), ("spine01", 0.5)),
    "head": (("neck01", 0.4), ("head", 0.6)),
    "upper_l": (("upperarm01.L", 1.0),), "fore_l": (("lowerarm01.L", 1.0),),
    "upper_r": (("upperarm01.R", 1.0),), "fore_r": (("lowerarm01.R", 1.0),),
    "hand_l": (("wrist.L", 1.0),), "hand_r": (("wrist.R", 1.0),),
    "clav_l": (("clavicle.L", 1.0),), "clav_r": (("clavicle.R", 1.0),),
}
ANIMATED = ("spine03", "spine01", "neck01", "head", "upperarm01.L", "lowerarm01.L", "wrist.L", "upperarm01.R",
            "lowerarm01.R", "wrist.R", "clavicle.L", "clavicle.R")

# ---------------------------------------------------------------- clips
# Each trader has the idle loop (LOOPS), a second idle ("idle2") and a greeting.
#   idle2   a loop that starts and ends in the idle's first pose, so the client can switch between the
#           two at a loop boundary without a blend.  Given as offsets (degrees) added to the idle's
#           first pose; channels not listed hold that pose.  The arms only move within their solved
#           holding poses (small bends that keep the grips and the wrist limits).
#   greet   additive (offsets on top of whatever idle plays): a nod, a slight bow and a smile.
#   face    expression weights 0..1 over time (FACE_POSES).
IDLE2 = {
    "lio": dict(duration=9.0, offsets={
        "hand_r": [(0, (0, 0, 0)), (2.0, (-8, 0, 0)), (4.6, (-8, 0, 0)), (6.0, (0, 0, 0)), (9, (0, 0, 0))],
        "head": [(0, (0, 0, 0)), (1.6, (6, 0, -8)), (4.4, (6, 2, -8)), (6.0, (-14, 0, 12)), (7.6, (-14, -2, 10)),
                 (9, (0, 0, 0))],
        "torso": [(0, (0, 0, 0)), (2.0, (2, -1.5, 0)), (6.0, (-2, 1.5, 3)), (9, (0, 0, 0))],
        "clav_r": [(0, (0, 0, 0)), (6.2, (0, 0, 0)), (7.0, (0, 3, 0)), (8.0, (0, 0, 0)), (9, (0, 0, 0))],
    }, face={"focus": [(0, 0), (1.6, 0.8), (4.4, 0.8), (5.4, 0), (9, 0)],
             "smile": [(0, 0), (5.6, 0), (6.4, 0.35), (7.6, 0.35), (8.6, 0), (9, 0)]}),
    "esme": dict(duration=9.0, offsets={
        "head": [(0, (0, 0, 0)), (1.8, (2, 0, 20)), (3.4, (2, 0, 20)), (4.4, (0, 0, 0)), (5.4, (-3, 2, -16)),
                 (6.8, (-3, 2, -16)), (8.0, (0, 0, 0)), (9, (0, 0, 0))],
        "upper_l": [(0, (0, 0, 0)), (1.6, (12, 0, 0)), (6.8, (12, 0, 0)), (8.2, (0, 0, 0)), (9, (0, 0, 0))],
        "fore_l": [(0, (0, 0, 0)), (1.6, (8, 0, 0)), (6.8, (8, 0, 0)), (8.2, (0, 0, 0)), (9, (0, 0, 0))],
        "torso": [(0, (0, 0, 0)), (2.0, (0, 0, 4)), (5.6, (0, 1.5, -4)), (9, (0, 0, 0))],
    }, face={"skeptic": [(0, 0), (5.2, 0), (5.8, 0.5), (6.8, 0.5), (7.6, 0), (9, 0)]}),
    "selma": dict(duration=9.0, offsets={
        "head": [(0, (0, 0, 0)), (1.6, (16, 0, 14)), (3.8, (16, 2, 14)), (5.2, (0, 0, 0)), (6.2, (-6, 0, -6)),
                 (7.8, (-6, 0, -6)), (9, (0, 0, 0))],
        "upper_r": [(0, (0, 0, 0)), (2.8, (-8, 0, 0)), (4.6, (-8, 0, 0)), (6.0, (0, 0, 0)), (9, (0, 0, 0))],
        "torso": [(0, (0, 0, 0)), (2.0, (3, 0, 4)), (6.0, (0, 1, -2)), (9, (0, 0, 0))],
    }, face={"smile": [(0, 0), (5.8, 0), (6.6, 0.5), (7.8, 0.5), (8.8, 0), (9, 0)]}),
    "nyra": dict(duration=9.0, offsets={
        "fore_l": [(0, (0, 0, 0)), (1.6, (-10, 0, 0)), (4.4, (-10, 0, 0)), (5.8, (0, 0, 0)), (9, (0, 0, 0))],
        "head": [(0, (0, 0, 0)), (1.6, (10, 0, 18)), (4.4, (10, -3, 18)), (6.0, (-4, 0, -10)), (7.8, (-4, 0, -10)),
                 (9, (0, 0, 0))],
        "torso": [(0, (0, 0, 0)), (2.0, (0, 0, 3)), (6.4, (0, 0, -2)), (9, (0, 0, 0))],
    }, face={"focus": [(0, 0), (1.8, 0.5), (4.4, 0.5), (5.2, 0), (9, 0)],
             "smile": [(0, 0), (6.0, 0), (6.8, 0.25), (7.8, 0.25), (8.6, 0), (9, 0)]}),
    "aron": dict(duration=9.0, offsets={
        "clav_l": [(0, (0, 0, 0)), (1.0, (0, -6, 0)), (1.8, (0, 0, 0)), (9, (0, 0, 0))],
        "clav_r": [(0, (0, 0, 0)), (1.0, (0, 6, 0)), (1.8, (0, 0, 0)), (9, (0, 0, 0))],
        "fore_l": [(0, (0, 0, 0)), (2.6, (-8, 0, 0)), (4.8, (-8, 0, 0)), (6.0, (0, 0, 0)), (9, (0, 0, 0))],
        "head": [(0, (0, 0, 0)), (1.2, (-4, 0, 4)), (2.8, (6, 0, 0)), (4.8, (6, 0, 0)), (6.2, (-12, 0, -10)),
                 (7.6, (-12, 0, -10)), (9, (0, 0, 0))],
        "torso": [(0, (0, 0, 0)), (1.2, (-2, 0, 0)), (3.0, (2, 0, 2)), (9, (0, 0, 0))],
    }, face={"skeptic": [(0, 0), (2.6, 0), (3.2, 0.4), (4.8, 0.4), (5.4, 0), (9, 0)],
             "smile": [(0, 0), (6.2, 0), (6.8, 0.3), (7.8, 0.3), (8.6, 0), (9, 0)]}),
}
GREET_SMILE = {"selma": 1.0, "nyra": 0.55, "lio": 0.9, "aron": 0.45, "esme": 0.7}


def _greet(role):
    k = GREET_SMILE.get(role, 0.7)
    return dict(duration=2.4, loop=False, additive=True,
                keys={"head": [(0, (0, 0, 0)), (0.55, (10, 0, 0)), (1.2, (0, 0, 0)), (2.4, (0, 0, 0))],
                      "torso": [(0, (0, 0, 0)), (0.6, (3, 0, 0)), (1.3, (0, 0, 0)), (2.4, (0, 0, 0))]},
                face={"smile": [(0, 0), (0.5, k), (1.9, k), (2.4, 0)],
                      "brows_up": [(0, 0), (0.3, 0.6), (0.9, 0), (2.4, 0)]})


_CLIPS = {}


def clip(role, name="idle"):
    """dict(duration, loop, additive, keys = {channel: [(t, (rx, ry, rz))]}, face = {pose: [(t, w)]})."""
    if (role, name) in _CLIPS:
        return _CLIPS[(role, name)]
    if name == "idle":
        L = LOOPS[role]
        out = dict(duration=L["duration"], loop=True, additive=False, keys=L["keys"], face=L.get("face", {}))
    elif name == "idle2":
        L, d = LOOPS[role], IDLE2[role]
        keys = {ch: list(v) for ch, v in L["keys"].items()}
        for ch, offs in d["offsets"].items():
            base = L["keys"][ch][0][1] if ch in L["keys"] else (0.0, 0.0, 0.0)
            keys[ch] = [(t, tuple(base[i] + o[i] for i in range(3))) for t, o in offs]
        for ch in L["keys"]:
            if ch not in d["offsets"]:
                keys[ch] = [(0, L["keys"][ch][0][1]), (d["duration"], L["keys"][ch][0][1])]
        out = dict(duration=d["duration"], loop=True, additive=False, keys=keys, face=d.get("face", {}))
    elif name == "greet":
        out = _greet(role)
    else:
        raise KeyError(name)
    _CLIPS[(role, name)] = out
    return out


def _tangents(ts, ys, cyclic, duration):
    """Monotone cubic (Fritsch-Butland) slopes at the keys: no overshoot, flat at holds and at turning
    points, smooth through keys on a steady move.  Cyclic: the loop's seam is treated like any key."""
    n = len(ts)
    if cyclic and n > 2:
        ts = [ts[-2] - duration] + list(ts) + [ts[1] + duration]
        ys = [ys[-2]] + list(ys) + [ys[1]]
    h = [ts[k + 1] - ts[k] for k in range(len(ts) - 1)]
    d = [(ys[k + 1] - ys[k]) / h[k] if h[k] > 0 else 0.0 for k in range(len(ts) - 1)]
    m = [0.0] * len(ts)
    for k in range(1, len(ts) - 1):
        if d[k - 1] * d[k] > 0:
            m[k] = 3 * (h[k - 1] + h[k]) / ((2 * h[k] + h[k - 1]) / d[k - 1] + (h[k] + 2 * h[k - 1]) / d[k])
    return m[1:-1] if cyclic and n > 2 else m


def _cubic(keys, t, cyclic, duration):
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return keys[0][1]
    if t >= ts[-1]:
        return keys[-1][1]
    j = max(i for i in range(len(ts) - 1) if ts[i] <= t)
    t0, t1 = ts[j], ts[j + 1]
    h = t1 - t0
    if h <= 0:
        return keys[j + 1][1]
    u = (t - t0) / h
    h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
    out = []
    dim = len(keys[0][1]) if isinstance(keys[0][1], (tuple, list)) else 0
    for c in range(max(dim, 1)):
        ys = [(k[1][c] if dim else k[1]) for k in keys]
        m = _tangents(ts, ys, cyclic, duration)
        out.append(h00 * ys[j] + h10 * h * m[j] + h01 * ys[j + 1] + h11 * h * m[j + 1])
    return tuple(out) if dim else out[0]


def clip_angles(cl, channel, t):
    keys = cl["keys"].get(channel)
    if not keys:
        return (0.0, 0.0, 0.0)
    if cl["loop"]:
        t = t % cl["duration"]
    return _cubic(keys, t, cl["loop"], cl["duration"])


def loop_angles(role, channel, t):
    return clip_angles(clip(role, "idle"), channel, t)


def face_weights(role, name, t):
    cl = clip(role, name)
    if cl["loop"]:
        t = t % cl["duration"]
    return {p: max(0.0, min(1.0, _cubic(keys, t, cl["loop"], cl["duration"]))) for p, keys in cl["face"].items()}


def _euler(a):
    """Rz @ Ry @ Rx of angles (rx, ry, rz) in degrees."""
    return H.rot((0, 0, 1), a[2]) @ H.rot((0, 1, 0), a[1]) @ H.rot((1, 0, 0), a[0])


BREATH = 3.4          # seconds per breath, rounded so that a whole number of breaths fills each loop


def breath_angle(duration, t):
    period = duration / max(1, round(duration / BREATH))
    return 1.2 * math.sin(TAU_LOOP * t / period)


def local_rotations(role, t, override=None, name="idle", greet=None):
    """Bone -> 3x3 rotation (figure axes, about the bone head, relative to the parent) at clip time t.
    override = {channel: angles} replaces channels (used by the pose solver); greet = time in the
    additive greeting (None: not greeting)."""
    cl = clip(role, name)
    out = {}
    add = clip(role, "greet") if greet is not None else None
    for channel, bones in CHANNELS.items():
        a = (override or {}).get(channel) or clip_angles(cl, channel, t)
        if add is not None and channel in add["keys"]:
            g = clip_angles(add, channel, greet)
            a = tuple(a[i] + g[i] for i in range(3))
        for bone, share in bones:
            out[bone] = _euler(tuple(x * share for x in a))
    out["spine01"] = out.get("spine01", np.eye(3)) @ H.rot((1, 0, 0), -breath_angle(cl["duration"], t % cl["duration"]))
    return out


TAU_LOOP = 2 * math.pi


# ---------------------------------------------------------------- power grip by search
GRIP_ALONG = (-0.01, 0.025, 0.06, 0.095)   # handle positions tried: from the knuckle line towards the wrist
LINK_WEIGHT = (1.0, 1.5, 2.0)              # a wrapped middle and tip link count more than the base link
TOUCH = 0.012                              # studs: a link this close to the prop touches it


def _palm_bvh(hand):
    """Surface of the palm (vertices that follow the wrist only), for finger tips that must not
    sink into their own palm."""
    from mathutils.bvhtree import BVHTree
    body, side = hand.body, hand.side
    palm = set(hand.idx[hand.dominant == "wrist." + side].tolist())
    faces = [list(f) for i in body.face_ids("body") for f in [body.faces[i]] if all(v in palm for v in f)]
    return BVHTree.FromPolygons([Vector(v) for v in body.verts], faces, all_triangles=False)


def _finger_state(hand, rots, chain, axes, ang, bvh, palm, tolerance, links):
    local = dict(rots)
    for b, ax, a in zip(chain, axes, ang):
        local[b] = H.rot(ax, a)
    pts = hand.posed(local)
    gaps, ok = [], True
    for k, (link, tol) in enumerate(zip(links, tolerance)):
        if not link.any():
            gaps.append(1.0)
            continue
        d = signed_distance(bvh, pts[link])
        if (d < -tol).any():
            ok = False
        gaps.append(float(d.min()))
        if k > 0 and ok and (signed_distance(palm, pts[link][::3]) < -0.004).any():
            ok = False                                          # finger sinks into its own palm
    return ok, gaps


def _search_finger(hand, rots, chain, axes, limit, bvh, palm):
    links = [hand.link(b) for b in chain]
    tolerance = []
    for b, link in zip(chain, links):
        h, t = (np.asarray(x) for x in hand.body.bones[b])
        dist = np.linalg.norm(hand.rest[link] - h, axis=1) / max(1e-6, np.linalg.norm(t - h))
        tolerance.append(PENETRATION + CREASE * np.clip(1 - dist / 0.5, 0, 1))

    def score(ang):
        ok, gaps = _finger_state(hand, rots, chain, axes, ang, bvh, palm, tolerance, links)
        if not ok:
            return None, gaps
        s = sum(w for g, w in zip(gaps, LINK_WEIGHT) if g < TOUCH)
        s -= 2.0 * min(0.3, max(0.0, min(gaps) - TOUCH))           # pulls a loose finger towards the prop
        return s + 0.001 * sum(ang), gaps
    best = (None, None, None)
    grid = [np.arange(0.0, lim + 0.1, 15.0) for lim in limit]
    for a1 in grid[0]:
        for a2 in grid[1]:
            for a3 in grid[2]:
                sc_, gaps = score((a1, a2, a3))
                if sc_ is not None and (best[0] is None or sc_ > best[0]):
                    best = (sc_, (a1, a2, a3), gaps)
    if best[1] is None:
        return (0.0, 0.0, 0.0), [1.0, 1.0, 1.0], 0.0
    step = 5.0
    for _ in range(3):                                           # refine around the best cell
        cur = best[1]
        for d1 in (-step, 0, step):
            for d2 in (-step, 0, step):
                for d3 in (-step, 0, step):
                    ang = tuple(min(lim, max(0.0, c + d)) for c, d, lim in zip(cur, (d1, d2, d3), limit))
                    sc_, gaps = score(ang)
                    if sc_ is not None and sc_ > best[0]:
                        best = (sc_, ang, gaps)
        step /= 2
    return best[1], best[2], best[0]


def grip_prop(body, side, mb, tilt, along_tried=GRIP_ALONG):
    """Power grip: for a few positions of the handle in the palm, every finger searches the joint
    angles that wrap the most links around the handle without pressing into it or into the palm;
    the position with the best wrap wins, then the thumb closes over it.
    -> (prop frame 4x4, finger rotations, report)."""
    hand = Hand(body, side)
    palm = _palm_bvh(hand)
    pn = hand_axes(body, side)[4]
    best = None
    for along in along_tried:
        frame = place_prop(body, side, mb, tilt, along)
        bvh = prop_bvh(mb, frame)
        rots = open_hand(body, side)
        total, rep = 0.0, {}
        for i in (2, 3, 4, 5):
            chain = [f"finger{i}-{j}.{side}" for j in (1, 2, 3)]
            axes = _finger_axes(body, side, i, pn)
            ang, gaps, sc_ = _search_finger(hand, rots, chain, axes, FINGER_LIMIT, bvh, palm)
            for b, ax, a in zip(chain, axes, ang):
                rots[b] = H.rot(ax, a)
            total += sc_
            rep[i] = dict(angles=[round(float(a), 1) for a in ang], tip_gap=round(gaps[-1], 4), deepest=round(min(gaps), 4),
                          touching=sum(g < TOUCH for g in gaps))
        if best is None or total > best[0]:
            best = (total, along, frame, bvh, rots, rep)
    total, along, frame, bvh, rots, report = best
    # thumb: closes over the handle from the other side, base to tip
    chain = [f"finger1-{j}.{side}" for j in (1, 2, 3)]
    axes = _finger_axes(body, side, 1, pn, frame[:3, 3], frame[:3, 1])
    ang = _close(hand, rots, chain, axes, THUMB_RATIO, THUMB_LIMIT, bvh, THUMB_OPEN)
    pts = hand.posed(rots)
    gaps = [float(signed_distance(bvh, pts[hand.link(b)]).min()) for b in chain if hand.link(b).any()]
    report[1] = dict(angles=[round(a, 1) for a in ang], tip_gap=round(gaps[-1], 4), deepest=round(min(gaps), 4),
                     touching=sum(g < TOUCH for g in gaps))
    report["fit"] = dict(along=along, score=round(total, 2))
    return frame, rots, report
