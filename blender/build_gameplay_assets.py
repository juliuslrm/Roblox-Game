"""Builds the gameplay assets (workshop machines, storage, logistics) - and only those.

    python blender/build_gameplay_assets.py [--preview]

Outputs: assets/machines/*.blend, exports/glb/machines/*.glb,
exports/library/arcane_machines.{glb,fbx}, world/gameplay_asset_manifest.json,
optionally previews/assets/machines_*.png.  The 91 village assets are not touched.
Checks while building: ids match Machines.lua, mesh stays inside its grid footprint,
triangle budget, back-face audit, glTF structure (same checks as the village assets).
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import audit_backfaces  # noqa: E402
import validate  # noqa: E402
from village import export, palette, registry  # noqa: E402
from village import scene as sc  # noqa: E402
from village.machines import MACHINES  # noqa: E402
from village.meshkit import MeshBuilder  # noqa: E402

TRI_BUDGET = 4500
CELL = 2.0


def machine_defs():
    """Reads footprints from roblox/gameplay/shared/Machines.lua through a Lua runtime."""
    from lupa import LuaRuntime
    lua = LuaRuntime()
    table = lua.execute(open(sc.path("roblox", "gameplay", "shared", "Machines.lua"), encoding="utf-8").read())
    return {v.modelAssetId: (k, v.w, v.d) for k, v in table.items()}


def build(name):
    mb = MeshBuilder(seed=registry.stable_seed(name))
    MACHINES[name](mb)
    mb.collision = "proxy"
    return mb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    palette.write_texture(sc.TEXTURE_PATH)
    defs = machine_defs()
    problems = []
    if set(defs) != set(MACHINES):
        problems.append(f"id mismatch: only in Lua {sorted(set(defs) - set(MACHINES))}, only in Blender {sorted(set(MACHINES) - set(defs))}")
    manifest = {}
    for name in MACHINES:
        export.new_scene()
        mb = build(name)
        obj = mb.to_object(name, sc.TEXTURE_PATH)
        entry = export.describe(mb, "machines", f"assets/machines/{name}.blend", f"exports/glb/machines/{name}.glb")
        _id, w, d = defs.get(name, (None, 1, 1))
        bmin, bmax = mb.bounds()
        if max(-bmin[0], bmax[0]) > w * CELL / 2 + 0.05 or max(-bmin[1], bmax[1]) > d * CELL / 2 + 0.05:
            problems.append(f"{name}: mesh leaves its {w}x{d} cell footprint ({bmin[0]:.2f}..{bmax[0]:.2f}, {bmin[1]:.2f}..{bmax[1]:.2f})")
        if bmin[2] < -0.01:
            problems.append(f"{name}: reaches below the floor")
        if entry["triangles"] > TRI_BUDGET:
            problems.append(f"{name}: {entry['triangles']} triangles > {TRI_BUDGET}")
        entry["machine"] = _id
        entry["footprint_cells"] = [w, d]
        export.save_blend(sc.path(entry["blend"]))
        export.export_glb([obj], sc.path(entry["glb"]))
        manifest[name] = entry
    # glTF structure / UV / winding checks shared with the village assets
    rep = validate.Report()
    validate.TRI_BUDGET["machines"] = TRI_BUDGET
    for name, entry in manifest.items():
        validate.check_asset(rep, name, entry, len(palette.COLORS))
    problems += [f"{sec}: {msg}" for status, sec, msg in rep.rows if status == "FAIL"]
    # back faces
    scene, cam, mat = audit_backfaces.setup()
    tmp = os.path.join(sc.path("world"), "_audit_tmp.png")
    for name in MACHINES:
        mb = build(name)
        mesh = mb.to_mesh(name, sc.TEXTURE_PATH)
        mesh.materials.clear()
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(name, mesh)
        scene.collection.objects.link(obj)
        back, front, worst = audit_backfaces.count_backfaces(scene, cam, obj, *mb.bounds(), audit_backfaces.VIEWS_ASSET, tmp)
        bpy.data.objects.remove(obj)
        manifest[name]["backface_pixels"] = back
        if back > max(8, front * 1e-4):
            problems.append(f"{name}: {back} back-face pixels (worst view {worst[1]})")
    if os.path.exists(tmp):
        os.remove(tmp)
    # library
    export.new_scene()
    objs, x = [], 0.0
    for name in MACHINES:
        mb = build(name)
        obj = mb.to_object(name, sc.TEXTURE_PATH)
        bmin, bmax = mb.bounds()
        x -= bmin[0]
        obj.location = (x, 0, 0)
        x += bmax[0] + 3
        objs.append(obj)
    export.export_glb(objs, sc.path("exports", "library", "arcane_machines.glb"))
    export.export_fbx(objs, sc.path("exports", "library", "arcane_machines.fbx"))
    with open(sc.path("world", "gameplay_asset_manifest.json"), "w") as fh:
        json.dump({"units": "studs", "cell": CELL, "assets": manifest}, fh, indent=1)
    tris = [e["triangles"] for e in manifest.values()]
    print(f"gameplay assets: {len(manifest)} meshes, {min(tris)}-{max(tris)} triangles, {sum(tris)} total")
    for p in problems:
        print("  FAIL", p)
    print(f"gameplay asset checks: {len(problems)} problems")
    if args.preview:
        import render_previews
        registry.ASSETS.update({n: {"category": "machines", "fn": fn, "dir": "assets/machines", "default_collision": "proxy"}
                                for n, fn in MACHINES.items()})
        names = list(MACHINES)
        render_previews.render_sheet(names[:9], sc.path("previews", "assets", "machines_1.png"), 3, 11, az=-118, el=22)
        render_previews.render_sheet(names[9:18], sc.path("previews", "assets", "machines_2.png"), 3, 13, az=-118, el=22)
        render_previews.render_sheet(names[18:], sc.path("previews", "assets", "machines_3.png"), 5, 7, az=-118, el=22)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
