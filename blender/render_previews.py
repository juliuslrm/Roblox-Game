"""Render preview images.

    python blender/render_previews.py world [--views a,b] [--scale 0.5] [--samples 48]
    python blender/render_previews.py assets            # contact sheets of the asset library
    python blender/render_previews.py hero              # reference house close-ups
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

from village import export, palette, registry  # noqa: E402
from village import scene as sc  # noqa: E402

# name: (eye x, eye y, eye height above the ground, target, lens)  -- Blender coordinates
WORLD_VIEWS = {
    "01_overview_southwest": ((-430, -520, 310), (10, 20, 0), 32),
    "02_overview_northeast": ((470, 430, 280), (-10, -20, 5), 32),
    "03_market_square": ((38, -118, 46), (-4, 6, 8), 30),
    "04_south_street": ((-22, -262, 9), (22, -150, 12), 28),
    "05_mill_hill": ((-168, 78, 22), (-262, 180, 50), 35),
    "06_pond_and_bridge": ((238, -150, 30), (150, -40, 0), 32),
    "07_chapel_hill": ((-30, 120, 24), (88, 250, 44), 35),
    "08_east_gate": ((381, -56, 11), (300, -34, 12), 28),
    "09_farm": ((-120, -150, 26), (-215, -235, 10), 30),
    "10_square_at_street_level": ((8, -36, 7), (-30, 55, 18), 24),
}


def ground_height(x, y):
    """Terrain height from world/heightmap.json (clamped to the world edge)."""
    global _GRID
    if "_GRID" not in globals():
        import json
        import numpy as np
        from village import terrain as tr
        hm = json.load(open(sc.path("world", "heightmap.json")))
        _GRID = tr.HeightGrid(np.array(hm["heights"]))
    return _GRID.at(x, y)


def render_world(args):
    bpy.ops.wm.open_mainfile(filepath=sc.path("world", "village_world.blend"))
    scene = bpy.context.scene
    res = (int(1920 * args.scale), int(1080 * args.scale))
    sc.setup_render(scene, res=res, samples=args.samples)
    sc.setup_light(scene, sun_az=228.0, sun_el=40.0)
    cam = sc.add_camera(scene)
    views = [v for v in args.views.split(",") if v] or list(WORLD_VIEWS) + ["00_top_down"]
    for name in views:
        if name == "00_top_down":
            cam.data.type = "ORTHO"
            cam.data.ortho_scale = 800
            scene.render.resolution_x = scene.render.resolution_y = int(1600 * args.scale)
            sc.aim(cam, (0, 0, 900), (0, 0.001, 0))
            cam.rotation_euler = (0, 0, 0)
        else:
            (ex, ey, agl), target, lens = WORLD_VIEWS[name]
            eye = (ex, ey, ground_height(ex, ey) + agl)
            cam.data.type = "PERSP"
            cam.data.lens = lens
            scene.render.resolution_x, scene.render.resolution_y = res
            sc.aim(cam, eye, target)
        sc.render(scene, sc.path("previews", "world", f"{name}.png"))
        print("[render]", name)


def render_sheet(names, out, cols, cell, az=-70.0, el=22.0, res=(1920, 1200), samples=40, lens=70):
    scene = export.new_scene()
    sc.setup_render(scene, res=res, samples=samples)
    sc.setup_light(scene)
    lo, hi = [1e9] * 3, [-1e9] * 3
    for i, name in enumerate(names):
        mb = registry.build(name)
        obj = mb.to_object(name, sc.TEXTURE_PATH)
        cx, cy = (i % cols) * cell, -(i // cols) * cell
        obj.location = (cx, cy, 0)
        bmin, bmax = mb.bounds()
        for k, off in enumerate((cx, cy, 0)):
            lo[k] = min(lo[k], bmin[k] + off)
            hi[k] = max(hi[k], bmax[k] + off)
    lo[2] = 0
    sc.ground_plane(scene, 6000, color="grass_dark")
    cam = sc.add_camera(scene)
    sc.frame_bounds(cam, lo, hi, az=az, el=el, aspect=res[0] / res[1], lens=lens, margin=0.62)
    sc.render(scene, out)
    print("[render]", os.path.basename(out))


def render_assets(args):
    palette.write_texture(sc.TEXTURE_PATH)
    houses = list(registry.CATEGORIES["houses"][0])
    for k in range(0, len(houses), 6):
        render_sheet(houses[k:k + 6], sc.path("previews", "assets", f"houses_{k // 6 + 1}.png"), 3, 46, az=-105, el=20)
    lms = list(registry.CATEGORIES["landmarks"][0])
    render_sheet(lms[:4], sc.path("previews", "assets", "landmarks_1.png"), 2, 62, az=-110, el=16)
    render_sheet(lms[4:], sc.path("previews", "assets", "landmarks_2.png"), 3, 50, az=-60, el=16)
    nat = list(registry.CATEGORIES["nature"][0])
    render_sheet(nat[:17], sc.path("previews", "assets", "nature_1.png"), 6, 20, el=18)
    render_sheet(nat[17:], sc.path("previews", "assets", "nature_2.png"), 6, 16, el=24)
    props = list(registry.CATEGORIES["props"][0])
    render_sheet(props[:16], sc.path("previews", "assets", "props_1.png"), 4, 26)
    render_sheet(props[16:], sc.path("previews", "assets", "props_2.png"), 5, 24)


def render_hero(args):
    palette.write_texture(sc.TEXTURE_PATH)
    for tag, az, el in (("front", -112, 7), ("side", -62, 16), ("back", 60, 30)):
        render_sheet(["house_01_timber_cottage"], sc.path("previews", "assets", f"reference_house_{tag}.png"), 1, 40,
                     az=az, el=el, res=(1600, 1000), samples=64, lens=50)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["world", "assets", "hero"])
    ap.add_argument("--views", default="")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--samples", type=int, default=48)
    a = ap.parse_args()
    {"world": render_world, "assets": render_assets, "hero": render_hero}[a.what](a)
