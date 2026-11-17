"""Builds the five market traders (jointed figures with idle loops) and their stalls.

    python blender/build_merchants.py [--no-render]

Outputs
    exports/glb/market/*.glb                 one file per figure part and per stall
    exports/library/arcane_market.{glb,fbx}  everything in one file (for the Roblox upload)
    assets/market/arcane_market.blend        editable source of the library
    roblox/gameplay/server/MarketArt.lua     bounds of stalls and figure parts, joint positions
    roblox/gameplay/shared/MarketMotion.lua  the idle loops, sampled as joint frames
    world/market_asset_manifest.json
    previews/market/01-haendler.png, 02-bewegung.png
Checks: market catalogue against the game data, triangle budgets, back-face audit of every figure,
loops close without a jump, and the sampled Roblox frames reproduce the Blender poses.
"""
import argparse
import json
import math
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE), str(ROOT / "roblox/gameplay/tests")]

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import audit_backfaces  # noqa: E402
from harness import lua_list, new_runtime  # noqa: E402
from village import coords, export, luadata, market, palette, registry  # noqa: E402
from village import merchants as M  # noqa: E402
from village import scene as sc  # noqa: E402
from village.meshkit import MeshBuilder  # noqa: E402

FIGURE_TRIANGLES = 32000      # whole figure (seven parts)
PART_TRIANGLES = 9500         # one part = one MeshPart; Roblox imports at most 10 000 triangles per mesh
FPS = 8
# Blender (x, y, z) -> Roblox (x, z, -y)
TO_ROBLOX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))


def audit_catalog():
    """The market data must stay consistent with items, recipes and resource nodes."""
    lua = new_runtime()
    data = lua.globals().loadModule("server/Data")
    layout = lua.execute((ROOT / "roblox/WorldLayout.lua").read_text(encoding="utf-8"))
    ids = lua_list(data.Market.order)
    assert sorted(ids) == sorted(M.ROLES) == sorted(market.STYLES)
    anchors = data.Market.anchors(layout)
    assert set(anchors) == set(ids)
    assert len({anchors[key].index for key in ids}) == len(ids)
    nodes = {n.item for n in data.Locations.nodes.values()}
    inputs = {key for recipe in data.Recipes.values() for key in recipe.inputs}
    if any(r.fuelUnits for r in data.Recipes.values()):
        inputs.add("fuel_charcoal")
    base = {item.id for item in data.Items.values() if item.type in ("raw", "fuel")}
    intermediates = {item.id for item in data.Items.values() if item.type == "intermediate"}
    outputs = {key for recipe in data.Recipes.values() for key in recipe.outputs}
    assert base <= nodes and base <= inputs and intermediates <= outputs
    listed = set()
    for key in ids:
        a = anchors[key]
        assert math.hypot(a.approachX - a.x, a.approachZ - a.z) > 4.3
        assert math.hypot(a.approachX, a.approachZ) > 17
        for offer in data.Market.merchants[key].offers.values():
            item = data.Items[offer.item]
            assert item and offer.item not in listed and offer.coins > 0 and offer.amount > 0
            assert offer.amount <= item.stackLimit and item.sellBase == 0
            if offer.unlock:
                rule = offer.unlock
                assert rule.research is None or data.Research[rule.research]
                assert rule.quest is None or data.Quests.main[rule.quest]
            listed.add(offer.item)
    assert listed == (base - {"water"}) | {"vial"}
    print(f"[market] catalogue ok: {len(ids)} stalls, {len(listed)} offers")
    return ids


def part_builder(role, part):
    mb = MeshBuilder(seed=registry.stable_seed(f"merchant_{role}_{part}"))
    M.build_part(mb, role, part)
    mb.collision = "none"
    return mb


def figure_builder(role, t):
    mb = MeshBuilder(seed=registry.stable_seed(f"merchant_{role}"))
    M.build_figure(mb, role, t)
    return mb


def roblox_frame(matrix):
    """Blender 4x4 joint frame -> (x, y, z, qx, qy, qz, qw) in Roblox axes."""
    pos = TO_ROBLOX @ matrix.to_translation()
    rot = TO_ROBLOX @ matrix.to_3x3() @ TO_ROBLOX.transposed()
    q = rot.to_quaternion()
    return [round(pos.x, 4), round(pos.y, 4), round(pos.z, 4), round(q.x, 5), round(q.y, 5), round(q.z, 5), round(q.w, 5)]


def sample_loops():
    motion, worst_step = {}, 0.0
    for role in M.ROLES:
        duration = M.LOOPS[role]["duration"]
        count = int(round(duration * FPS))
        tracks = {part: [] for part in M.PARTS if part != "lower"}
        for i in range(count):
            frames = M.pose_frames(role, duration * i / count)
            for part in tracks:
                tracks[part].append(roblox_frame(frames[part]))
        for part, rows in tracks.items():                      # no jump anywhere, also not from last to first
            for a, b in zip(rows, rows[1:] + rows[:1]):
                worst_step = max(worst_step, math.dist(a[:3], b[:3]))
        joints = M.joints(role)
        motion[role] = {"duration": duration, "joints": {part: coords.to_roblox(joints[part]) for part in tracks},
                        "parts": tracks}
    # the fastest intended move (hammer blow) covers about 0.25 studs per sample; a broken loop seam
    # or a wrong key would show up as a much larger step
    assert worst_step < 0.6, f"a joint jumps {worst_step:.2f} studs between two samples"
    return motion, worst_step


def check_conversion(motion, art):
    """A point of a part must land at the same place through the Blender pose and through the
    exported Roblox frame:  roblox(frame(t) * rest^-1 * v)  ==  F(t) * (roblox(v) - joint)."""
    rng = random.Random(7)
    worst = 0.0
    for role in M.ROLES:
        rest = M.pose_frames(role)
        duration = M.LOOPS[role]["duration"]
        rows = motion[role]["parts"]
        for part, track in rows.items():
            joint = Vector(art["merchants"][role]["parts"][part]["joint"])
            for _ in range(6):
                i = rng.randrange(len(track))
                v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0, 6)))
                posed = M.pose_frames(role, duration * i / len(track))[part] @ rest[part].inverted() @ v
                expect = TO_ROBLOX @ posed
                x, y, z, qx, qy, qz, qw = track[i]
                from mathutils import Quaternion
                got = Vector((x, y, z)) + Quaternion((qw, qx, qy, qz)).to_matrix() @ (TO_ROBLOX @ v - joint)
                worst = max(worst, (got - expect).length)
    assert worst < 2e-3, f"Roblox frames deviate by {worst:.4f} studs"
    return worst


def render_lineup(out):
    scene = export.new_scene()
    sc.setup_render(scene, res=(1920, 1080), samples=40)
    sc.setup_light(scene)
    lo, hi = [1e9] * 3, [-1e9] * 3
    poses = {"selma": 2.4, "nyra": 3.0, "lio": 1.0, "aron": 1.2, "esme": 3.0}
    for i, role in enumerate(M.ROLES):
        mb = figure_builder(role, poses[role])
        obj = mb.to_object(f"lineup_{role}", sc.TEXTURE_PATH)
        obj.location = (i * 4.3, 0, 0)
        bmin, bmax = mb.bounds()
        for k, off in enumerate((i * 4.3, 0, 0)):
            lo[k] = min(lo[k], bmin[k] + off)
            hi[k] = max(hi[k], bmax[k] + off)
    sc.ground_plane(scene, 6000, color="cobble")
    cam = sc.add_camera(scene)
    sc.frame_bounds(cam, lo, hi, az=-90, el=5, aspect=1920 / 1080, lens=75, margin=0.6)
    sc.render(scene, out)


def render_motion(out):
    """Six moments of every loop, one row per trader."""
    scene = export.new_scene()
    sc.setup_render(scene, res=(1920, 1500), samples=28)
    sc.setup_light(scene)
    lo, hi = [1e9] * 3, [-1e9] * 3
    for r, role in enumerate(M.ROLES):
        duration = M.LOOPS[role]["duration"]
        for i in range(6):
            mb = figure_builder(role, duration * i / 6)
            obj = mb.to_object(f"motion_{role}_{i}", sc.TEXTURE_PATH)
            off = (i * 4.4, r * 9.5, 0)
            obj.location = off
            bmin, bmax = mb.bounds()
            for k in range(3):
                lo[k] = min(lo[k], bmin[k] + off[k])
                hi[k] = max(hi[k], bmax[k] + off[k])
    sc.ground_plane(scene, 6000, color="cobble")
    cam = sc.add_camera(scene)
    sc.frame_bounds(cam, lo, hi, az=-90, el=30, aspect=1920 / 1500, lens=70, margin=0.56)
    sc.render(scene, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()
    palette.write_texture(sc.TEXTURE_PATH)
    ids = audit_catalog()
    problems = []
    art = {"merchants": {}}
    manifest = {}
    built = []                      # (name, builder, library offset)
    for index, role in enumerate(ids):
        joints = M.joints(role)
        parts, triangles = {}, 0
        for part in M.PARTS:
            name = f"merchant_{role}_{part}"
            mb = part_builder(role, part)
            bounds = coords.bounds_to_roblox(*mb.bounds())
            parts[part] = {"center": bounds["center"], "size": bounds["size"], "joint": coords.to_roblox(joints[part])}
            triangles += mb.tri_count()
            if mb.tri_count() > PART_TRIANGLES:
                problems.append(f"{name}: {mb.tri_count()} triangles > {PART_TRIANGLES}")
            manifest[name] = {"role": role, "part": part, "triangles": mb.tri_count(), "bounds_roblox": bounds,
                              "glb": f"exports/glb/market/{name}.glb"}
            built.append((name, mb, (index * 12.0, 0.0, 0.0)))
        whole = figure_builder(role, 0.0)
        lo, hi = whole.bounds()
        if triangles > FIGURE_TRIANGLES:
            problems.append(f"{role}: {triangles} triangles > {FIGURE_TRIANGLES}")
        if lo[2] < -0.02 or hi[2] > 8.0:
            problems.append(f"{role}: height range {lo[2]:.2f}..{hi[2]:.2f}")
        art["merchants"][role] = {"height": round(hi[2], 3), "parts": parts}
        print(f"[market] {role}: {triangles} triangles in {len(M.PARTS)} parts, {hi[2]:.2f} studs high")

        name = "stall_" + role
        mb = MeshBuilder(seed=registry.stable_seed(name))
        market.stall(mb, role)
        bounds = coords.bounds_to_roblox(*mb.bounds())
        art[name] = {"center": bounds["center"], "size": bounds["size"]}
        manifest[name] = {"role": role, "triangles": mb.tri_count(), "bounds_roblox": bounds, "glb": f"exports/glb/market/{name}.glb"}
        built.append((name, mb, (index * 12.0, 12.0, 0.0)))

    # single files
    for name, mb, _ in built:
        export.new_scene()
        obj = mb.to_object(name, sc.TEXTURE_PATH)
        export.export_glb([obj], str(ROOT / manifest[name]["glb"]))
    # library + editable source
    export.new_scene()
    objs = []
    for name, mb, offset in built:
        obj = mb.to_object(name, sc.TEXTURE_PATH)
        obj.location = offset
        objs.append(obj)
    export.export_glb(objs, str(ROOT / "exports/library/arcane_market.glb"))
    export.export_fbx(objs, str(ROOT / "exports/library/arcane_market.fbx"))
    export.save_blend(str(ROOT / "assets/market/arcane_market.blend"))

    # back faces: every figure in a pose of its loop
    scene, cam, mat = audit_backfaces.setup()
    tmp = str(ROOT / "world/_audit_tmp.png")
    for role in ids:
        mb = figure_builder(role, 1.5)
        mesh = mb.to_mesh("audit_" + role, sc.TEXTURE_PATH)
        mesh.materials.clear()
        mesh.materials.append(mat)
        obj = bpy.data.objects.new("audit_" + role, mesh)
        scene.collection.objects.link(obj)
        back, front, worst = audit_backfaces.count_backfaces(scene, cam, obj, *mb.bounds(), audit_backfaces.VIEWS_ASSET, tmp)
        bpy.data.objects.remove(obj)
        manifest["merchant_" + role + "_lower"]["figure_backface_pixels"] = back
        if back > max(8, front * 2e-4):
            problems.append(f"{role}: {back} back-face pixels (worst view {worst[1]})")
    if os.path.exists(tmp):
        os.remove(tmp)

    motion, step = sample_loops()
    deviation = check_conversion(motion, art)
    print(f"[market] loops: largest joint step {step:.3f} studs per sample, Roblox frames deviate {deviation:.5f} studs")

    (ROOT / "roblox/gameplay/server/MarketArt.lua").write_text(
        "-- Generated by blender/build_merchants.py. Do not edit.\n"
        "-- Bounds (Roblox axes, relative to the ground point) of the stalls and of every figure part;\n"
        "-- joint = the point a part turns around.\nreturn "
        + luadata.to_lua(art, inline_depth=4) + "\n", encoding="utf-8")
    (ROOT / "roblox/gameplay/shared/MarketMotion.lua").write_text(
        "-- Generated by blender/build_merchants.py. Do not edit.\n"
        "-- Idle loops of the traders: per part one joint frame per sample, { x, y, z, qx, qy, qz, qw }\n"
        "-- in Roblox axes relative to the figure's ground point; joints = rest position of each joint.\n"
        "-- A part moves with  frame(t) * CFrame.new(-joint).\nreturn "
        + luadata.to_lua({"fps": FPS, "roles": motion}, inline_depth=4) + "\n", encoding="utf-8")
    with open(ROOT / "world/market_asset_manifest.json", "w") as fh:
        json.dump({"units": "studs", "assets": manifest}, fh, indent=1)
    size = (ROOT / "roblox/gameplay/shared/MarketMotion.lua").stat().st_size
    if size > 190_000:
        problems.append(f"MarketMotion.lua has {size} bytes (Roblox script limit 200 000)")
    print(f"[market] MarketMotion.lua {size} bytes")

    if not args.no_render:
        render_lineup(str(ROOT / "previews/market/01-haendler.png"))
        render_motion(str(ROOT / "previews/market/02-bewegung.png"))
    for p in problems:
        print("  FAIL", p)
    print(f"market checks: {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
