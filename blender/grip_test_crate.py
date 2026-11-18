"""Test scene for a two-handed grip (no trader carries a crate in the game; this proves the grip
system for two hands).

    python blender/grip_test_crate.py

1. Aron's body without props.  The right hand is the primary hand: its arm is solved (village/armik)
   into a carry pose (forearm forwards, thumb up, crate centred in front of the belly) and the crate
   hangs on its right handle bar (prop space of the right hand).
2. The left hand follows the crate's left handle: its arm is solved for position and orientation of
   the hand (6 goals), so nothing depends on itself in a circle.
3. Both poses are baked, then the fingers of both hands wrap their bars (characters._search_finger)
   and the thumbs close.
Writes previews/grips/after/crate_two_hands.png (views like validate_grips) and the measurements to
previews/grips/after/crate_two_hands.json.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE)]

import bpy  # noqa: E402,F401
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

from village import armik as IK  # noqa: E402
from village import characters as C  # noqa: E402
from village import handheld as P  # noqa: E402
from village import human as H  # noqa: E402
from village.meshkit import MeshBuilder  # noqa: E402

ROLE = "crate_test"


class Rig:
    """What armik.Scene needs from a character: body, role, bone heads, held props."""

    def __init__(self, body):
        self.body = body
        self.role = ROLE
        self.bones = list(body.order)
        self.heads = {b: np.asarray(body.bones[b][0]) for b in body.order}
        self.held = {}


def hand_frame(mats, frame_rest, side):
    return mats["wrist." + side] @ frame_rest


def main():
    C.LOOPS[ROLE] = dict(duration=1.0, keys={})
    body = C.rest_pose(C.make_body("aron"))
    # geometry the validator measures (as prepared_body stores it)
    body.hand_geometry = {}
    for side, _sx in C.SIDES:
        wrist, elbow = C._head(body, "wrist." + side), C._head(body, "lowerarm01." + side)
        bases = [C._head(body, f"finger{i}-1.{side}") for i in range(2, 6)]
        body.hand_geometry[side] = dict(forearm=C._unit(wrist - elbow), hand=C._unit(np.mean(bases, axis=0) - wrist),
                                        palm=C.hand_axes(body, side)[4])
    mb = MeshBuilder(seed=5)
    P.crate(mb, -1)
    bar = MeshBuilder(seed=6)                       # the bar alone: placement in each hand
    P._along_y(bar, [(0.0, -0.22), (0.045, -0.22), (0.045, 0.22), (0.0, 0.22)], "iron", segs=14)
    # the grip on a bar is solved in each hand first (same search as the traders); the arms are then
    # posed so that these hand-held bars sit on the crate's bars
    frames, grip_report = {}, {}
    for s_ in ("L", "R"):
        frames[s_], finger_rots, grip_report[s_] = C.grip_prop(body, s_, bar, 0.0)
        body.apply_pose(finger_rots)
    rig = Rig(body)
    rig.held = {s: ("bar", bar, frames[s]) for s in ("L", "R")}
    sc = IK.Scene(rig, 0.0)
    z = rig.heads["spine03"][2] + 0.1
    front = float(sc.posed_body[np.abs(sc.posed_body[:, 2] - z) < 0.06][:, 1].min())
    T_R = np.array((-P.CRATE_SPAN / 2, front - 0.5, z))

    def g_right(m):
        F = hand_frame(m, frames["R"], "R")
        c = 100 * float(np.sum((F[:3, 3] - T_R) ** 2))
        c += 3 * (1 + F[2, 1]) ** 2                     # bar (prop +Y) pointing down: thumb up
        c += 3 * (F[0, 0] - 1) ** 2                     # palm side (+X of the right prop space) towards the middle
        return c
    upR, foR, haR, costR, infoR = IK.solve(sc, "R", g_right, [(-20, 10, 10, -90, 0), (-35, 15, 20, -80, 0),
                                                              (-10, 5, 0, -100, 10)], iters=900)
    fixed = {"upper_r": upR, "fore_r": foR, "hand_r": haR}
    mR = sc.mats({}, fixed)
    crate_world = hand_frame(mR, frames["R"], "R")
    target_L = crate_world @ H_translate(P.CRATE_SPAN)

    centre = crate_world[:3, 3] + crate_world[:3, 0] * P.CRATE_SPAN / 2

    def g_left(m):
        # a bar only fixes its axis and that the palm faces the crate (the roll of the hand around
        # the bar and the mirror image of the right hand are free)
        F = hand_frame(m, frames["L"], "L")
        c = 2000 * float(np.sum((F[:3, 3] - target_L[:3, 3]) ** 2))
        c += 4000 * (1 - float(np.dot(F[:3, 1], target_L[:3, 1]))) ** 2        # same bar axis (a tilt shifts the fingers)
        palm = -F[:3, 0]                                                       # left palm = -X of its prop space
        to_c = centre - F[:3, 3]
        c += 3 * (1 - float(np.dot(palm, to_c / np.linalg.norm(to_c)))) ** 2
        return c
    # the body is mirror-symmetric: the mirrored right arm is the natural first guess for the left
    mirror = (upR[0], -upR[1], -upR[2], foR[0], -foR[2], haR[0], -haR[2])
    upL, foL, haL, costL, infoL = IK.solve(sc, "L", g_left, [mirror, (-20, -10, -10, -90, 0), (-35, -15, -20, -80, 0)],
                                         fixed=fixed, iters=1500)
    rots = C.local_rotations(ROLE, 0.0, {**fixed, "upper_l": upL, "fore_l": foL, "hand_l": haL})
    mats = body.bone_matrices(rots)
    left_error = float(np.linalg.norm(hand_frame(mats, frames["L"], "L")[:3, 3] - target_L[:3, 3]))
    body.apply_pose(rots)                            # carry pose baked; the crate stays in the world
    bvh = C.prop_bvh(mb, crate_world)
    report = {}
    for side in ("L", "R"):                       # contact of every finger link with the crate, in the pose
        hand = C.Hand(body, side)
        pts = hand.rest
        res = {}
        for i in range(1, 6):
            gaps = [float(C.signed_distance(bvh, pts[hand.link(f"finger{i}-{j}.{side}")]).min()) for j in (1, 2, 3)]
            res[i] = dict(angles=grip_report[side][i]["angles"], touching=sum(g < C.TOUCH for g in gaps),
                          deepest=round(min(gaps), 4))
        report[side] = res
    out = {"right_arm": {**infoR, "cost": round(costR, 4)}, "left_arm": {**infoL, "cost": round(costL, 4)},
           "left_hand_to_handle": round(left_error, 4), "fingers": report}
    problems = []
    for side, res in report.items():
        for i, r in res.items():
            if i != 1 and r["touching"] < 2:
                problems.append(f"{side} finger {i}: {r['touching']} links on the bar")
            if r["deepest"] < -0.02:
                problems.append(f"{side} finger {i}: {r['deepest']} into the crate")
    if left_error > 0.03:
        problems.append(f"left hand {left_error:.3f} studs from its handle")
    out["problems"] = problems
    render(body, mb, crate_world, out)
    print(json.dumps(out, indent=1, default=float))


def H_translate(x):
    M = np.eye(4)
    M[0, 3] = x
    return M


def render(body, mb, crate_world, out):
    from mathutils import Matrix
    from village import export
    from village import scene as sc
    import validate_grips as VG
    scene = export.new_scene()
    sc.setup_render(scene, res=(VG.TILE, VG.TILE), samples=16)
    sc.setup_light(scene)
    cam = sc.add_camera(scene)
    mat = VG.material()
    fids = body.face_ids("body")
    used = sorted({v for i in fids for v in body.faces[i]})
    rm = {v: k for k, v in enumerate(used)}
    VG.add_mesh("body", body.verts[used], [[rm[v] for v in body.faces[i]] for i in fids],
                np.tile((0.82, 0.62, 0.52), (len(used), 1)), mat)
    o = mb.to_object("crate", sc.TEXTURE_PATH)
    o.matrix_world = Matrix(crate_world.tolist())
    lo, hi = body.verts[used].min(axis=0), body.verts[used].max(axis=0)
    tiles = []
    tmp = str(ROOT / "world/_crate_%d.png")
    for az in (-90, 0, -55, 180):
        sc.frame_bounds(cam, lo, hi, az=az, el=8, aspect=1.0, lens=50, margin=0.8)
        tiles.append(VG.render_tile(tmp % len(tiles)))
    for side, sx in (("R", -1), ("L", 1)):
        c = np.asarray(body.bones["wrist." + side][0]) + np.array((0, -0.1, -0.15))
        for az, el in ((-90 + sx * 60, 15), (-90 + sx * 120, -25)):
            sc.orbit(cam, tuple(c), az, el, 1.2)
            tiles.append(VG.render_tile(tmp % len(tiles)))
    path = ROOT / "previews/grips/after"
    path.mkdir(parents=True, exist_ok=True)
    VG.sheet(tiles, str(path / "crate_two_hands.png"))
    (path / "crate_two_hands.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
