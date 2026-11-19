"""Grip profiles and trader loops stay consistent (fast part of the grip validation).

    VILLAGE_PYTHON=/opt/bpyenv/bin/python python tests/test_grip_profiles.py

- every held prop has a profile, a builder in handheld.py, and a grip region that does not overlap
  its forbidden parts and lies on the modelled prop;
- every loop channel is sorted, starts at 0 and ends at the loop's duration with the start pose
  (closed loop, no jump at the seam);
- over both idle clips and the greeting (8 samples per second) the hand is never twisted in the wrist by more than 45
  degrees, the forearm never turned by more than 95 degrees, the wrist never bent beyond 50 / 25
  degrees (the same limits as blender/village/gripcheck.py).  These need the rest skeleton only,
  not the solved grips, so this runs in about a minute; the full check with contacts and renders
  is blender/validate_grips.py.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import bpy  # noqa: E402,F401  (mathutils comes with bpy)
import numpy as np  # noqa: E402

from village import characters as C  # noqa: E402
from village import gripcheck as GC  # noqa: E402
from village import grips as G  # noqa: E402
from village import handheld as P  # noqa: E402
from village.meshkit import MeshBuilder  # noqa: E402


def check_profiles():
    for role, hands in G.HELD.items():
        for side, pid in hands.items():
            assert pid in G.PROFILES, f"{role} {side}: no profile for {pid}"
    for pid, prof in G.PROFILES.items():
        builder = getattr(P, prof["builder"], None)
        assert builder is not None, f"{pid}: no builder {prof['builder']} in handheld.py"
        y0, y1 = prof["region"]
        assert y0 < y1, f"{pid}: empty grip region"
        for name, f0, f1 in prof["forbidden"]:
            assert f1 <= y0 or f0 >= y1, f"{pid}: grip region {prof['region']} overlaps the forbidden {name}"
        mb = MeshBuilder(seed=1)
        builder(mb, -1)
        ys = np.array([v[1] for v in mb.verts])
        assert ys.min() < y1 and ys.max() > y0, \
            f"{pid}: grip region {prof['region']} is not on the prop (y {ys.min():.2f}..{ys.max():.2f})"
    print(f"  ok  grip profiles: {len(G.PROFILES)} profiles, {sum(len(h) for h in G.HELD.values())} held props")


def check_loop_keys():
    for role, loop in C.LOOPS.items():
        d = loop["duration"]
        for ch, keys in loop["keys"].items():
            times = [t for t, _ in keys]
            assert times == sorted(times), f"{role}.{ch}: keys not sorted"
            assert times[0] == 0 and abs(times[-1] - d) < 1e-6, f"{role}.{ch}: keys must span 0..{d}"
            assert tuple(keys[0][1]) == tuple(keys[-1][1]), f"{role}.{ch}: loop not closed"
    print(f"  ok  loop keys: {len(C.LOOPS)} loops closed and sorted")


def check_wrists():
    for role in C.ROLES:
        leg, tilt = C.STANCE.get(role, (None, 0.0))
        body = C.rest_pose(C.make_body(role), weight_leg=leg, tilt=tilt)
        for side, _sx in C.SIDES:
            wrist, elbow = C._head(body, "wrist." + side), C._head(body, "lowerarm01." + side)
            bases = [C._head(body, f"finger{i}-1.{side}") for i in range(2, 6)]
            geo = dict(forearm=C._unit(wrist - elbow), hand=C._unit(np.mean(bases, axis=0) - wrist),
                       palm=C.hand_axes(body, side)[4])
            worst = [0.0, 0.0, 0.0, 0.0]
            moments = []
            for name in ("idle", "idle2"):                  # both idle clips, and the greeting on top
                d = C.clip(role, name)["duration"]
                moments += [(name, k / GC.FPS, None) for k in range(int(round(d * GC.FPS)))]
            moments += [("idle", 0.0, g / 8) for g in range(20)]
            for name, t, g in moments:
                m = body.bone_matrices(C.local_rotations(role, t, name=name, greet=g))
                tw, fr = GC.arm_twist(geo, m, side)
                bend, sideways = GC.wrist_bend(geo, m, side)
                worst = [max(a, abs(b)) for a, b in zip(worst, (tw, fr, bend, sideways))]
            tw, fr, bend, sideways = worst
            assert tw <= 45 and fr <= 95, f"{role} {side}: hand twisted {tw:.0f} in the wrist / forearm {fr:.0f} degrees"
            assert bend <= 50 and sideways <= 25, f"{role} {side}: wrist bent {bend:.0f} / sideways {sideways:.0f} degrees"
            print(f"  ok  {role} {side}: wrist twist <= {tw:.0f}, forearm <= {fr:.0f}, bend <= {bend:.0f} / {sideways:.0f}")


def main():
    check_profiles()
    check_loop_keys()
    check_wrists()


if __name__ == "__main__":
    main()
