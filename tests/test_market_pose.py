"""MarketPose.lua (Roblox) evaluates the traders' clips exactly like blender/village/characters.py.

    VILLAGE_PYTHON=/opt/bpyenv/bin/python python tests/test_market_pose.py

For every trader, clip (idle, idle2) and 40 times per clip, with and without the additive greeting:
the local rotation of every animated bone from the Lua evaluator (quaternion, Roblox frame of the
figure) equals the Python rotation converted to the Roblox frame (angle between them < 0.01 degrees);
the expression weights agree to 1e-6.  Runs on the generated roblox/gameplay/shared/MarketMotion.lua,
so it also proves that the export carries the keys the Python side uses.
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import bpy  # noqa: E402,F401  (mathutils comes with bpy)
import numpy as np  # noqa: E402
from lupa import LuaRuntime  # noqa: E402

from village import characters as C  # noqa: E402

TO_ROBLOX = np.array(((1.0, 0, 0), (0, 0, 1.0), (0, -1.0, 0)))
NAME = {"root": "hips"}


def quat_matrix(q):
    x, y, z, w = q
    return np.array(((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
                     (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
                     (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y))))


def angle(A, B):
    c = (np.trace(A.T @ B) - 1) / 2
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def main():
    lua = LuaRuntime(unpack_returned_tuples=True)
    motion = lua.execute((ROOT / "roblox/gameplay/shared/MarketMotion.lua").read_text(encoding="utf-8"))
    pose = lua.execute((ROOT / "roblox/gameplay/shared/MarketPose.lua").read_text(encoding="utf-8"))
    pose.BREATH = motion.breath
    assert abs(motion.breath - C.BREATH) < 1e-9
    worst, worst_face, count = 0.0, 0.0, 0
    for role in C.ROLES:
        prep = pose.prepare(motion.roles[role])
        for name in ("idle", "idle2"):
            d = C.clip(role, name)["duration"]
            for k in range(40):
                t = d * k / 40 + 0.013
                for greet in (None, 0.37, 1.4):
                    q_lua = pose.evaluate(motion.channels, prep, name, t, greet)
                    rots = C.local_rotations(role, t, name=name, greet=greet)
                    for bone in C.ANIMATED:
                        q = q_lua[NAME.get(bone, bone)]
                        A = quat_matrix([q[1], q[2], q[3], q[4]])
                        B = TO_ROBLOX @ rots[bone] @ TO_ROBLOX.T
                        worst = max(worst, angle(A, B))
                        count += 1
                fw_lua = pose.faceWeights(prep, name, t)
                for pname, w in C.face_weights(role, name, t).items():
                    worst_face = max(worst_face, abs(fw_lua[pname] - w))
        for g in (0.1, 0.55, 1.5, 2.3):
            fw_lua = pose.faceWeights(prep, "greet", g)
            for pname, w in C.face_weights(role, "greet", g).items():
                worst_face = max(worst_face, abs(fw_lua[pname] - w))
    assert worst < 0.01, f"Lua and Python bone rotations differ by {worst:.4f} degrees"
    assert worst_face < 1e-6, f"face weights differ by {worst_face}"
    print(f"  ok  MarketPose.lua = characters.py: {count} bone rotations (worst {worst:.5f} deg), face weights "
          f"(worst {worst_face:.1e})")


if __name__ == "__main__":
    main()
