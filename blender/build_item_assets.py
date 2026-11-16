"""Builds the item models (one per item) and the icon sheet rendered from them.

    python blender/build_item_assets.py [--no-render]

Outputs: assets/items/*.blend, exports/glb/items/*.glb, exports/library/arcane_items.{glb,fbx},
world/item_asset_manifest.json, roblox/gameplay/server/ItemArt.lua (bounds),
exports/textures/item_icons.png (all items on one sheet), previews/assets/items.png.
The icon sheet layout (cell size, column and row of every item) is written into
roblox/gameplay/shared/ItemIconSheet.lua; the image id is added after the upload.
Checks: one model per item of Items.lua and vice versa, size limits, triangle budget, back-face
audit, glTF structure.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import audit_backfaces  # noqa: E402
import validate  # noqa: E402
from village import export, palette, registry  # noqa: E402
from village import scene as sc  # noqa: E402
from village.items import ITEMS  # noqa: E402
from village.meshkit import MeshBuilder  # noqa: E402

TRI_BUDGET = 700
MAX_HALF = 0.8       # studs: an item stays inside a 1.6 stud square (a belt is 2 studs wide)
MAX_HEIGHT = 1.75
ICON = 128           # pixels per icon
COLUMNS = 8


def item_ids():
    from lupa import LuaRuntime
    lua = LuaRuntime()
    table = lua.execute(open(sc.path("roblox", "gameplay", "shared", "Items.lua"), encoding="utf-8").read())
    return sorted(table.keys())


def build(name):
    mb = MeshBuilder(seed=registry.stable_seed(name))
    ITEMS[name](mb)
    mb.collision = "none"
    return mb


def render_icon(name, out):
    """One item, three-quarter view, transparent background."""
    scene = export.new_scene()
    sc.setup_render(scene, res=(ICON, ICON), samples=24)
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = "RGBA"
    sc.setup_light(scene)
    mb = build(name)
    mb.to_object(name, sc.TEXTURE_PATH)
    lo, hi = mb.bounds()
    cam = sc.add_camera(scene)
    sc.frame_bounds(cam, list(lo), list(hi), az=-62, el=24, aspect=1.0, lens=85, margin=1.04)   # 1.0 = bounding sphere fills the frame
    sc.render(scene, out)


def read_png(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return px


def write_sheet(names, tmp_dir, out):
    rows = (len(names) + COLUMNS - 1) // COLUMNS
    sheet = np.zeros((rows * ICON, COLUMNS * ICON, 4), dtype=np.float32)
    for i, name in enumerate(names):
        px = read_png(os.path.join(tmp_dir, name + ".png"))
        col, row = i % COLUMNS, i // COLUMNS
        y0 = (rows - 1 - row) * ICON                        # Blender images start at the bottom
        sheet[y0:y0 + ICON, col * ICON:(col + 1) * ICON] = px
    img = bpy.data.images.new("item_icons", COLUMNS * ICON, rows * ICON, alpha=True)
    img.pixels = sheet.ravel().tolist()
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()
    palette.write_texture(sc.TEXTURE_PATH)
    problems = []
    ids = item_ids()
    wanted = {"item_" + i for i in ids}
    if wanted != set(ITEMS):
        problems.append(f"id mismatch: items without model {sorted(wanted - set(ITEMS))}, models without item {sorted(set(ITEMS) - wanted)}")
    names = ["item_" + i for i in ids if "item_" + i in ITEMS]
    manifest = {}
    for name in names:
        export.new_scene()
        mb = build(name)
        obj = mb.to_object(name, sc.TEXTURE_PATH)
        entry = export.describe(mb, "items", f"assets/items/{name}.blend", f"exports/glb/items/{name}.glb")
        bmin, bmax = mb.bounds()
        if max(-bmin[0], bmax[0], -bmin[1], bmax[1]) > MAX_HALF:
            problems.append(f"{name}: wider than {2 * MAX_HALF} studs ({bmin[0]:.2f}..{bmax[0]:.2f}, {bmin[1]:.2f}..{bmax[1]:.2f})")
        # rocks and lumps may dip a little below their origin; the game places items by their bounds
        if bmax[2] > MAX_HEIGHT or bmin[2] < -0.15:
            problems.append(f"{name}: height range {bmin[2]:.2f}..{bmax[2]:.2f} outside -0.15..{MAX_HEIGHT}")
        if entry["triangles"] > TRI_BUDGET:
            problems.append(f"{name}: {entry['triangles']} triangles > {TRI_BUDGET}")
        entry["item"] = name[5:]
        export.save_blend(sc.path(entry["blend"]))
        export.export_glb([obj], sc.path(entry["glb"]))
        manifest[name] = entry
    rep = validate.Report()
    validate.TRI_BUDGET["items"] = TRI_BUDGET
    for name, entry in manifest.items():
        validate.check_asset(rep, name, entry, len(palette.COLORS))
    problems += [f"{sec}: {msg}" for status, sec, msg in rep.rows if status == "FAIL"]
    # back faces
    scene, cam, mat = audit_backfaces.setup()
    tmp = os.path.join(sc.path("world"), "_audit_tmp.png")
    for name in names:
        mb = build(name)
        mesh = mb.to_mesh(name, sc.TEXTURE_PATH)
        mesh.materials.clear()
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(name, mesh)
        scene.collection.objects.link(obj)
        back, front, worst = audit_backfaces.count_backfaces(scene, cam, obj, *mb.bounds(), audit_backfaces.VIEWS_ASSET, tmp)
        bpy.data.objects.remove(obj)
        manifest[name]["backface_pixels"] = back
        if back > max(8, front * 3e-4):
            problems.append(f"{name}: {back} back-face pixels (worst view {worst[1]})")
    if os.path.exists(tmp):
        os.remove(tmp)
    # library
    export.new_scene()
    objs = []
    for i, name in enumerate(names):
        obj = build(name).to_object(name, sc.TEXTURE_PATH)
        obj.location = ((i % 9) * 3.0, (i // 9) * 3.0, 0)
        objs.append(obj)
    export.export_glb(objs, sc.path("exports", "library", "arcane_items.glb"))
    export.export_fbx(objs, sc.path("exports", "library", "arcane_items.fbx"))
    with open(sc.path("world", "item_asset_manifest.json"), "w") as fh:
        json.dump({"units": "studs", "assets": manifest}, fh, indent=1)
    lines = ["-- Generated by blender/build_item_assets.py. Do not edit.",
             "-- Bounds of the item models in Roblox axes, relative to the point they stand on.",
             "return {"]
    for name in names:
        b = manifest[name]["bounds_roblox"]
        lines.append(f"\t{name} = {{ center = {{{b['center'][0]:g}, {b['center'][1]:g}, {b['center'][2]:g}}}, "
                     f"size = {{{b['size'][0]:g}, {b['size'][1]:g}, {b['size'][2]:g}}} }},")
    lines += ["}", ""]
    with open(sc.path("roblox", "gameplay", "server", "ItemArt.lua"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    tris = [e["triangles"] for e in manifest.values()]
    print(f"item assets: {len(manifest)} meshes, {min(tris)}-{max(tris)} triangles, {sum(tris)} total")

    if not args.no_render:
        tmp_dir = sc.path("world", "_icons_tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        for name in names:
            render_icon(name, os.path.join(tmp_dir, name + ".png"))
        sheet_path = sc.path("exports", "textures", "item_icons.png")
        rows = write_sheet(names, tmp_dir, sheet_path)
        for name in names:
            os.remove(os.path.join(tmp_dir, name + ".png"))
        os.rmdir(tmp_dir)
        # layout for the UI; keep an image id that was filled in after an earlier upload
        lua_path = sc.path("roblox", "gameplay", "shared", "ItemIconSheet.lua")
        image = '""'
        if os.path.exists(lua_path):
            m = re.search(r'^\timage = ("[^"]*")', open(lua_path, encoding="utf-8").read(), re.M)
            if m:
                image = m.group(1)
        out = ["-- Generated by blender/build_item_assets.py. Do not edit (the image id is set by the upload step).",
               "-- All item icons on one sheet (exports/textures/item_icons.png): cell size and cell of every item.",
               "-- An empty image id means the sheet has not been uploaded; the UI then falls back to symbol tiles.",
               "return {", f"\timage = {image},", f"\tcell = {ICON},", f"\tcolumns = {COLUMNS},", f"\trows = {rows},", "\titems = {"]
        for i, name in enumerate(names):
            out.append(f"\t\t{name[5:]} = {{ {i % COLUMNS}, {i // COLUMNS} }},")
        out += ["\t},", "}", ""]
        with open(lua_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out))
        print(f"icon sheet: {COLUMNS} x {rows} cells of {ICON} px")
        import render_previews
        registry.ASSETS.update({n: {"category": "items", "fn": fn, "dir": "assets/items", "default_collision": "none"}
                                for n, fn in ITEMS.items()})
        render_previews.render_sheet(names, sc.path("previews", "assets", "items.png"), 9, 2.6, az=-70, el=28)
    for p in problems:
        print("  FAIL", p)
    print(f"item asset checks: {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
