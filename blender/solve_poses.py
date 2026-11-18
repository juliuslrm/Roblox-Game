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

from village import armik as IK  # noqa: E402
from village import characters as C  # noqa: E402


def chest_front(scene, z, x=0.0):
    P = scene.posed_body
    band = P[(np.abs(P[:, 2] - z) < 0.06) & (np.abs(P[:, 0] - x) < 0.15)]
    return float(band[:, 1].min())


def shoulder_top(scene, side):
    j = scene.ch.heads["upperarm01." + side]
    P = scene.posed_body
    near = P[(np.hypot(P[:, 0] - j[0], P[:, 1] - j[1]) < 0.16)]
    return near[np.argmax(near[:, 2])]


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
        c += 5 * max(0.0, w[2] - (S[2] - 0.25)) ** 2 + 5 * max(0.0, (S[2] - 1.0) - w[2]) ** 2
        return c
    starts = [(-40, 20, 20, -100, 0), (-60, 10, 40, -120, -20), (-30, 30, 0, -130, 20), (-50, 5, 10, -90, -40)]
    up, fo, ha, cost, info = IK.solve(sc, "R", goal, starts)
    m = sc.mats({"upper_r": up, "fore_r": fo, "hand_r": ha})
    H = sc.prop_points("R", handle, m)
    return {"upper_r": up, "fore_r": fo, "hand_r": ha, "cost": cost, **info,
            "handle_to_shoulder": round(float(np.min(np.linalg.norm(H - S, axis=1))), 3)}


def aron(ch):
    out = {}
    sc = IK.Scene(ch, 0.0)
    z = sc.ch.heads["spine03"][2] + 0.45
    T = np.array((0.1, chest_front(sc, z) - 0.42, z))
    ore = next(p for p in ch.pieces if p.name == "prop_L")
    inv = np.linalg.inv(ch.held["L"][2])
    ore_local = (np.c_[ore.verts, np.ones(len(ore.verts))] @ inv.T)[:, :3]
    centre_local = ore_local.mean(axis=0, keepdims=True)

    def g_ore(m):
        c = sc.prop_points("L", centre_local, m)[0]
        return 100 * float(np.sum((c - T) ** 2)) + 30 * sc.inside(sc.prop_points("L", ore_local[::6], m), 0.03)
    up, fo, ha, cost, info = IK.solve(sc, "L", g_ore, [(-30, -6, -16, -76, 0), (-45, -10, -25, -90, 10)])
    out["hold_l"] = {"upper_l": up, "fore_l": fo, "hand_l": ha, "cost": cost, **info}
    fixed = {"upper_l": up, "fore_l": fo, "hand_l": ha}
    m0 = sc.mats({}, fixed)
    ore_w = sc.prop_points("L", ore_local, m0)
    ore_c = ore_w.mean(axis=0)
    ore_r = float(np.median(np.linalg.norm(ore_w - ore_c, axis=1)))
    face = np.array([(0, -0.82, -0.27)])
    normal = np.array([(0, -0.82, -0.27), (0, -0.82, -0.37)])
    head = np.array([(0, -0.82, z_) for z_ in (-0.25, 0.0, 0.3)])
    for name, lift in (("tap_r", 0.006), ("lift_r", 0.35)):

        def g_tap(m, lift=lift):
            # the face meets the ore surface from outside, pointing at the ore's centre (tap), or
            # stands `lift` away from it along the same line (swing)
            F = sc.prop_points("R", face, m)[0]
            N = sc.prop_points("R", normal, m)
            n = (N[0] - N[1]) / np.linalg.norm(N[0] - N[1])          # outward normal of the face
            to_c = ore_c - F
            dist = np.linalg.norm(to_c)
            c = 300 * (dist - (ore_r + lift)) ** 2 + 3.0 * (1 - float(np.dot(n, to_c / dist))) ** 2
            c += 30 * sc.inside(sc.prop_points("R", head, m), 0.05)
            return c
        up, fo, ha, cost, info = IK.solve(sc, "R", g_tap, [(-30, 8, 26, -90, 0), (-40, 15, 35, -70, 10), (-25, 5, 20, -110, -10)],
                                      fixed=fixed)
        m = sc.mats({"upper_r": up, "fore_r": fo, "hand_r": ha}, fixed)
        F = sc.prop_points("R", face, m)[0]
        out[name] = {"upper_r": up, "fore_r": fo, "hand_r": ha, "cost": cost, **info,
                     "face_to_ore_surface": round(float(np.linalg.norm(ore_c - F) - ore_r - lift), 4)}
    return out


def nyra(ch):
    sc = IK.Scene(ch, 2.2)
    z = ch.heads["head"][2] - 0.55
    T = np.array((-0.16, chest_front(sc, z) - 0.38, z))
    centre = np.array([(0, -0.15, 0)])

    def goal(m):
        c = sc.prop_points("R", centre, m)[0]
        tip = sc.prop_points("R", np.array([(0, -0.56, 0)]), m)[0]
        return 100 * float(np.sum((c - T) ** 2)) + 5 * max(0.0, c[2] + 0.05 - tip[2]) ** 2 \
            + 30 * sc.inside(sc.prop_points("R", np.array([(0, y, 0) for y in (-0.5, -0.3, 0.0, 0.15)]), m), 0.05)
    up, fo, ha, cost, info = IK.solve(sc, "R", goal, [(-52, 6, 18, -96, 0), (-40, 10, 30, -110, -20)])
    return {"upper_r": up, "fore_r": fo, "hand_r": ha, "cost": cost, **info}


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
    up, fo, ha, cost, info = IK.solve(sc, "R", g_hold, [(-30, 6, 10, -86, 0), (-20, 10, 20, -100, 10)])
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
        upl, fol, hal, cost, info = IK.solve(sc, "L", g_rub, [(-34, -6, -10, -92, 0), (-40, -4, -20, -100, 10)], fixed=fixed)
        out[name] = {"upper_l": upl, "fore_l": fol, "hand_l": hal, "cost": cost, **info}
    sc2 = IK.Scene(ch, 4.4)
    eye = ch.heads["head"][2] + 0.12
    T2 = np.array((-0.32, chest_front(sc2, ch.heads["head"][2] - 0.6) - 0.5, eye))

    def g_light(m):
        c = sc2.prop_points("R", centre, m)[0]
        a = sc2.prop_points("R", axis, m)
        up_dir = (a[0] - a[1]) / np.linalg.norm(a[0] - a[1])
        return 100 * float(np.sum((c - T2) ** 2)) + 3 * (1 - up_dir[2]) ** 2
    up, fo, ha, cost, info = IK.solve(sc2, "R", g_light, [(-62, 22, 6, -92, 0), (-70, 30, 10, -80, 20)])
    out["light_r"] = {"upper_r": up, "fore_r": fo, "hand_r": ha, "cost": cost, **info}
    return out


def main():
    roles = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["esme", "aron", "nyra", "lio"]
    results = {}
    for role in roles:
        ch = C.build(role)
        results[role] = globals()[role](ch)
        print(role, json.dumps(results[role], default=lambda v: round(float(v), 2)), flush=True)
    path = ROOT / "world/solved_poses.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    old.update(results)
    path.write_text(json.dumps(old, indent=1, default=lambda v: round(float(v), 2)))


if __name__ == "__main__":
    main()
