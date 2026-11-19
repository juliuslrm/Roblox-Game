"""Solves the arm poses of the idle loops from contact goals (see village/armik.py) and prints them
as loop keys; the numbers are copied into characters.LOOPS.

    python blender/solve_poses.py -- [role ...]
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE)]

import bpy  # noqa: E402,F401
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

from village import armik as IK  # noqa: E402
from village import characters as C  # noqa: E402
from village import gripcheck as GC  # noqa: E402


def chest_front(scene, z, x=0.0):
    """Front of the trunk at height z (the arms and hands are left out: they move with the pose)."""
    P = scene.posed_body[scene.trunk]
    band = P[(np.abs(P[:, 2] - z) < 0.06) & (np.abs(P[:, 0] - x) < 0.15)]
    return float(band[:, 1].min())


def shoulder_top(scene, side):
    """Top of the shoulder (acromion): highest skin point above the shoulder joint in the rest pose
    (arm hanging), carried along by the collar bone of the current torso pose.  Not measured in the
    solved pose itself: the raised arm would move its own target."""
    j = scene.ch.heads["upperarm01." + side]
    V = scene.ch.body.verts
    near = np.nonzero(np.hypot(V[:, 0] - j[0], V[:, 1] - j[1]) < 0.12)[0]
    near = near[V[near, 2] < j[2] + 0.4]
    top = V[near[np.argmax(V[near, 2])]]
    M = scene.mats({})["clavicle." + side]
    return (M @ np.r_[top, 1.0])[:3]


def turned(sc, side, pose, goal, degrees):
    """The same hand position, the forearm turned `degrees` further round its own axis (turning
    something in the hand).  A key on the forearm's z channel would swing the bent forearm sideways
    instead, so the turned pose is solved: same goal, forearm rotation target, close to `pose`."""
    t = "l" if side == "L" else "r"
    geo = sc.ch.body.hand_geometry[side]
    m0 = sc.mats({f"upper_{t}": pose[f"upper_{t}"], f"fore_{t}": pose[f"fore_{t}"], f"hand_{t}": pose[f"hand_{t}"]})
    target = GC.arm_twist(geo, m0, side)[1] + degrees
    x0 = (*pose[f"upper_{t}"], pose[f"fore_{t}"][0], pose[f"fore_{t}"][2], pose[f"hand_{t}"][0], pose[f"hand_{t}"][2])

    def g(m):
        return goal(m) + 0.02 * (GC.arm_twist(geo, m, side)[1] - target) ** 2
    up, fo, ha, cost, info = IK.solve(sc, side, g, [x0], iters=900, prior=(x0, 0.0005))
    return {f"upper_{t}": up, f"fore_{t}": fo, f"hand_{t}": ha, "cost": cost, **info}


def seg_dist(p, pts):
    return float(np.min(np.linalg.norm(pts - p, axis=1)))


def esme(ch):
    sc = IK.Scene(ch, 0.0)
    S = shoulder_top(sc, "R") + np.array((0, 0, 0.05))            # on the tunic and vest
    ys = np.linspace(-1.5, -0.15, 40)
    handle = np.stack((np.zeros_like(ys), ys, 0.06 * np.sin(math.pi * (0.46 - ys) / 2.4)), axis=1)
    head = np.array([(0, -1.82, 0), (0, -1.82, -0.4), (0, -1.95, 0.1)])

    def goal(m):
        H = sc.prop_points("R", handle, m)
        Hd = sc.prop_points("R", head, m)
        k = int(np.argmin(np.linalg.norm(H - S, axis=1)))
        c = 200 * (np.linalg.norm(H[k] - S) - 0.075) ** 2               # handle resting on the shoulder
        c += 50 * max(0.0, S[2] + 0.02 - H[k][2]) ** 2                   # ... from above
        c += 20 * max(0.0, S[1] + 0.2 - Hd[0][1]) ** 2                   # head behind the shoulder
        c += 20 * max(0.0, S[2] + 0.3 - Hd[0][2]) ** 2                   # ... and above it
        c += 30 * sc.inside(np.vstack((H[::3], Hd)), 0.04)
        w = sc.joint(m, "wrist.R")
        # the hand at chest height (higher, the handle passes in front of the mouth)
        c += 5 * max(0.0, w[2] - (S[2] - 0.45)) ** 2 + 5 * max(0.0, (S[2] - 1.0) - w[2]) ** 2
        # the hand in front of the same shoulder, the handle running front to back over it (not across
        # the throat)
        c += 30 * (w[0] - S[0]) ** 2
        d = (H[-1] - H[0]) / np.linalg.norm(H[-1] - H[0])
        c += 10 * float(d[0]) ** 2
        return c
    starts = [(-26, 20, 14, -134, 3, -19, -13), (-40, 20, 20, -100, 0), (-60, 10, 40, -120, -20), (-30, 30, 0, -130, 20),
              (-50, 5, 10, -90, -40), (-20, 30, 20, -125, 10, -25, -20)]
    up, fo, ha, cost, info = IK.solve(sc, "R", goal, warm("esme", None, "R") + starts)
    m = sc.mats({"upper_r": up, "fore_r": fo, "hand_r": ha})
    H = sc.prop_points("R", handle, m)
    return {"upper_r": up, "fore_r": fo, "hand_r": ha, "cost": cost, **info,
            "handle_to_shoulder": round(float(np.min(np.linalg.norm(H - S, axis=1))), 3)}


# tap costs of the candidates (last full run): (0.1, 0.42, 0.45) 0.054, (-0.05, 0.45, 0.35) 0.063,
# (-0.2, 0.5, 0.3) 0.074, (0.0, 0.55, 0.2) 0.060, (0.1, 0.5, 0.25) 0.043 - only the best is solved again
ORE_TARGETS = ((0.1, 0.5, 0.25),)


def aron(ch):
    """The ore's place in front of the body decides whether the hammer face can meet it with a
    natural forearm (no twist in the wrist): every candidate is tried with a short tap solve, the
    best one gets the full swing path."""
    sc = IK.Scene(ch, 0.0)
    best = None
    for dx, dy, dz in ORE_TARGETS:
        z = sc.ch.heads["spine03"][2] + dz
        T = np.array((dx, chest_front(sc, z) - dy, z))
        cost = aron_at(ch, sc, T, quick=True)
        print(f"[aron] ore at {(dx, dy, dz)}: tap cost {cost:.4f}", flush=True)
        if best is None or cost < best[0]:
            best = (cost, T)
    out = aron_at(ch, sc, best[1])
    out["ore_target"] = [round(float(v), 3) for v in best[1]]
    return out


def aron_at(ch, sc, T, quick=False):
    out = {}
    ore = next(p for p in ch.pieces if p.name == "prop_L")
    inv = np.linalg.inv(ch.held["L"][2])
    ore_local = (np.c_[ore.verts, np.ones(len(ore.verts))] @ inv.T)[:, :3]
    centre_local = ore_local.mean(axis=0, keepdims=True)

    def g_ore(m):
        c = sc.prop_points("L", centre_local, m)[0]
        return 100 * float(np.sum((c - T) ** 2)) + 30 * sc.inside(sc.prop_points("L", ore_local[::6], m), 0.03)
    up, fo, ha, cost, info = IK.solve(sc, "L", g_ore, warm("aron", "hold_l", "L") + [(-22, -3, -14, -73, 2, -5, -14),
                                                                                 (10, -8, 1, -109, -22, 1, -6),
                                                                                 (-30, -6, -16, -76, 0)])
    out["hold_l"] = {"upper_l": up, "fore_l": fo, "hand_l": ha, "cost": cost, **info}
    fixed = {"upper_l": up, "fore_l": fo, "hand_l": ha}
    m0 = sc.mats({}, fixed)
    # the real ore surface (bumps and veins included), fixed in the left hand
    ore_w = sc.prop_points("L", ore_local, m0)
    ore_c = ore_w.mean(axis=0)
    ore_bvh = BVHTree.FromPolygons([Vector(v) for v in ore_w], [list(f) for f in ore.faces], all_triangles=False)
    hammer = next(p for p in ch.pieces if p.name == "prop_R")
    inv_r = np.linalg.inv(ch.held["R"][2])
    h_local = (np.c_[hammer.verts, np.ones(len(hammer.verts))] @ inv_r.T)[:, :3]
    head_pts = h_local[h_local[:, 1] < -0.6]
    face_pts = h_local[(h_local[:, 1] < -0.6) & (h_local[:, 2] < -0.22)]

    normal = np.array([(0, -0.82, -0.27), (0, -0.82, -0.37)])          # face centre and a point in front of it
    head = np.array([(0, -0.82, z_) for z_ in (-0.25, 0.0, 0.3)]
                    + [(0, y_, 0) for y_ in (-0.6, -0.3, 0.1, 0.42)])     # head and handle stay out of the body

    def sd(pts):
        return C.signed_distance(ore_bvh, pts)
    # the swing is solved as a path: contact, then 4, 9, 15 and 25 cm off, each pose starting from and
    # staying close to its neighbour; the loop puts one pose on every sample (1/8 s), so the engine only
    # blends between close, checked poses
    tap_x = None
    line = None                                     # (face centre, face normal) of the tap: the swing's straight line
    path = (("tap_r", 0.004), ("gap04_r", 0.04), ("gap09_r", 0.09), ("gap15_r", 0.15), ("gap25_r", 0.25),
            ("gap35_r", 0.35), ("gap45_r", 0.45))
    for name, gap in path[:1] if quick else path:
        def g_tap(m, gap=gap):
            F = sc.prop_points("R", face_pts, m)
            Hd = sc.prop_points("R", head_pts, m)
            n = sc.prop_points("R", normal, m)
            nv = (n[1] - n[0]) / np.linalg.norm(n[1] - n[0])          # outward normal of the striking face
            to_c = ore_c - F.mean(axis=0)
            c = 300 * (float(sd(F).min()) - gap) ** 2
            c += 3000 * float(np.sum(np.maximum(0.0, 0.002 - sd(Hd)) ** 2))       # no part of the head inside
            c += 3.0 * (1 - float(np.dot(nv, to_c / np.linalg.norm(to_c)))) ** 2   # the face points at the ore
            c += 30 * sc.inside(sc.prop_points("R", head, m), 0.05)
            if line is not None:                  # back along the line of the blow, face turned the same way
                c += 400 * float(np.sum((F.mean(axis=0) - (line[0] - line[1] * (gap - 0.004))) ** 2))
                c += 20 * (1 - float(np.dot(nv, line[1]))) ** 2
            return c
        rng = np.random.default_rng(7)
        starts = [(9, 4, 13, -77, 14, 4, 0), (-8, 29, 9, -78, -6, 6, 47), (21, 23, 5, -98, 13, -12, 34)]
        starts += [tuple(rng.uniform((-40, -10, -20, -120, -30, -30, -40), (30, 40, 40, -50, 30, 30, 50))) for _ in range(6)]
        prior = None if tap_x is None else (tap_x, 0.003)
        up, fo, ha, cost, info = IK.solve(sc, "R", g_tap, ([tap_x] if prior else warm("aron", name, "R")) + starts,
                                          fixed=fixed, iters=1200, prior=prior)
        if quick:
            return cost
        tap_x = (*up, fo[0], fo[2], ha[0], ha[2])                     # the next pose starts from this one
        m = sc.mats({"upper_r": up, "fore_r": fo, "hand_r": ha}, fixed)
        if line is None:
            nn = sc.prop_points("R", normal, m)
            line = (sc.prop_points("R", face_pts, m).mean(axis=0), (nn[1] - nn[0]) / np.linalg.norm(nn[1] - nn[0]))
        out[name] = {"upper_r": up, "fore_r": fo, "hand_r": ha, "cost": cost, **info,
                     "face_to_ore": round(float(sd(sc.prop_points("R", face_pts, m)).min()), 4),
                     "head_deepest": round(float(sd(sc.prop_points("R", head_pts, m)).min()), 4)}
    return out


def nyra(ch):
    sc = IK.Scene(ch, 2.2)
    z = ch.heads["head"][2] - 0.8                                    # chest height, below the hair
    T = np.array((-0.25, chest_front(sc, z) - 0.7, z))
    centre = np.array([(0, -0.15, 0)])
    # the point up, forwards and a little outwards, so it stays clear of hair and hood
    tip_dir = np.array((-0.3, -0.6, 0.75)) / np.linalg.norm((-0.3, -0.6, 0.75))

    def goal(m):
        c = sc.prop_points("R", centre, m)[0]
        tip = sc.prop_points("R", np.array([(0, -0.56, 0)]), m)[0]
        d = (tip - c) / np.linalg.norm(tip - c)
        return 100 * float(np.sum((c - T) ** 2)) + 5 * (1 - float(np.dot(d, tip_dir))) ** 2 \
            + 30 * sc.inside(sc.prop_points("R", np.array([(0, y, 0) for y in (-0.5, -0.3, 0.0, 0.15)]), m), 0.05)
    up, fo, ha, cost, info = IK.solve(sc, "R", goal, warm("nyra", None, "R") + [(-52, 6, 18, -96, 0), (-40, 10, 30, -110, -20)])
    out = {"upper_r": up, "fore_r": fo, "hand_r": ha, "cost": cost, **info}
    # she turns the crystal in the light: the same place, the forearm turned each way
    out["turn_a"] = turned(sc, "R", out, goal, 18)
    out["turn_b"] = turned(sc, "R", out, goal, -18)
    return out


def lio(ch):
    out = {}
    sc = IK.Scene(ch, 0.0)
    z = ch.heads["spine03"][2] + 0.25                              # lower chest: the forearm about level
    T = np.array((-0.12, chest_front(sc, z) - 0.32, z))
    centre = np.array([(0.0, 0.0, 0.0)])
    axis = np.array([(0, -0.3, 0), (0, 0.2, 0)])

    def g_hold(m):
        c = sc.prop_points("R", centre, m)[0]
        a = sc.prop_points("R", axis, m)
        up_dir = (a[0] - a[1]) / np.linalg.norm(a[0] - a[1])       # cork direction
        return 100 * float(np.sum((c - T) ** 2)) + 3 * (1 - up_dir[2]) ** 2
    up, fo, ha, cost, info = IK.solve(sc, "R", g_hold, warm("lio", "hold_r", "R") + [(2, -4, 15, -88, -1, -6, -3),
                                                                                  (-30, 6, 10, -86, 0)])
    out["hold_r"] = {"upper_r": up, "fore_r": fo, "hand_r": ha, "cost": cost, **info}
    fixed = {"upper_r": up, "fore_r": fo, "hand_r": ha}
    m0 = sc.mats({}, fixed)
    bottle_c = sc.prop_points("R", centre, m0)[0]
    cloth_c = np.array([(0, 0, 0)])
    for name, dz in (("rub_up_l", 0.05), ("rub_down_l", -0.07)):
        target = bottle_c + np.array((0.115, -0.02, dz))

        def g_rub(m, target=target):
            c = sc.prop_points("L", cloth_c, m)[0]
            return 100 * float(np.sum((c - target) ** 2))
        upl, fol, hal, cost, info = IK.solve(sc, "L", g_rub, warm("lio", name, "L") + [(-2, 3, -10, -88, -11, -1, 6),
                                                                                    (-34, -6, -10, -92, 0)], fixed=fixed)
        out[name] = {"upper_l": upl, "fore_l": fol, "hand_l": hal, "cost": cost, **info}
    sc2 = IK.Scene(ch, 4.4)
    eye = ch.heads["head"][2] + 0.12
    # out in front of the right shoulder at nearly arm's length, at eye height: he looks at the glass
    # against the light, the face stays visible from the front and from the side (a target 0.7 studs
    # in front of the chest put the bottle so close to the face that it read as drinking)
    T2 = np.array((-0.82, chest_front(sc2, ch.heads["head"][2] - 0.6) - 1.0, eye - 0.08))
    chin = ch.heads["head"][2] - 0.15
    face_x = ch.heads["head"][0]

    def g_light(m):
        c = sc2.prop_points("R", centre, m)[0]
        a = sc2.prop_points("R", axis, m)
        up_dir = (a[0] - a[1]) / np.linalg.norm(a[0] - a[1])
        cost = 100 * float(np.sum((c - T2) ** 2)) + 3 * (1 - up_dir[2]) ** 2
        # neither the hand nor the bottle in front of the face (right side is -X)
        for p in (sc2.joint(m, "wrist.R"), c, a[0], a[1]):
            if p[2] > chin:
                cost += 200 * max(0.0, p[0] - (face_x - 0.42)) ** 2
        return cost
    up, fo, ha, cost, info = IK.solve(sc2, "R", g_light, warm("lio", "light_r", "R") + [(-62, 22, 6, -92, 0), (-70, 30, 10, -80, 20),
                                                                                    (-50, 40, 20, -100, 0, 20, -60)])
    out["light_r"] = {"upper_r": up, "fore_r": fo, "hand_r": ha, "cost": cost, **info}
    out["light_turn_r"] = turned(sc2, "R", out["light_r"], g_light, 20)
    return out


PREVIOUS = {}


def warm(role, name, side):
    """The pose found last time (world/solved_poses.json) as an extra start: the solver keeps the
    better of the old and the new solution instead of jumping between local minima."""
    old = PREVIOUS.get(role, {})
    old = old.get(name, old) if name else old
    t = "l" if side == "L" else "r"
    if not old or f"upper_{t}" not in old:
        return []
    u, f, h = old[f"upper_{t}"], old[f"fore_{t}"], old.get(f"hand_{t}", (0, 0, 0))
    return [(u[0], u[1], u[2], f[0], f[2], h[0], h[2])]


def main():
    path = ROOT / "world/solved_poses.json"
    PREVIOUS.update(json.loads(path.read_text()) if path.exists() else {})
    roles = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["esme", "aron", "nyra", "lio"]
    results = {}
    for role in roles:
        ch = C.build(role)
        results[role] = globals()[role](ch)
        print(role, json.dumps(results[role], default=lambda v: round(float(v), 2)), flush=True)
    old = json.loads(path.read_text()) if path.exists() else {}
    old.update(results)
    path.write_text(json.dumps(old, indent=1, default=lambda v: round(float(v), 2)))


if __name__ == "__main__":
    main()
