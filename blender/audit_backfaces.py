"""Back-face audit.

Roblox culls back faces, Cycles does not: a part that is wound inside-out looks
perfect in the previews and has holes in the game.  This script renders every
asset from all around with a diagnostic material (front faces white, back
faces magenta) and counts magenta pixels.  A clean asset shows none.

    python blender/audit_backfaces.py [--only id,id]

Writes world/backface_audit.json (read by validate.py).
"""
import argparse
import json
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

from village import export, palette, registry, worldmesh  # noqa: E402
from village import plan as pl  # noqa: E402
from village import scene as sc  # noqa: E402
from village.meshkit import MeshBuilder  # noqa: E402

RES = 256 if "--keep" not in " ".join(sys.argv) else 640
# (azimuth, elevation) in degrees; world meshes are only ever seen from above
VIEWS_ASSET = [(az, 18) for az in range(0, 360, 60)] + [(30, 55), (150, 55), (270, 55), (0, 89)]
VIEWS_GROUND = [(0, 89.5)]


def audit_material():
    mat = bpy.data.materials.new("BackfaceAudit")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mix = nt.nodes.new("ShaderNodeMixShader")
    front = nt.nodes.new("ShaderNodeEmission")
    back = nt.nodes.new("ShaderNodeEmission")
    front.inputs["Color"].default_value = (1, 1, 1, 1)
    back.inputs["Color"].default_value = (1, 0, 1, 1)
    nt.links.new(geo.outputs["Backfacing"], mix.inputs["Fac"])
    nt.links.new(front.outputs["Emission"], mix.inputs[1])
    nt.links.new(back.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def setup():
    scene = export.new_scene()
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 0
    scene.cycles.pixel_filter_type = "BOX"
    scene.render.resolution_x = scene.render.resolution_y = RES
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("Black")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scene.world = world
    cam = sc.add_camera(scene)
    cam.data.type = "ORTHO"
    return scene, cam, audit_material()


def count_backfaces(scene, cam, obj, bmin, bmax, views, tmp, keep=None):
    centre = [(a + b) / 2 for a, b in zip(bmin, bmax)]
    radius = math.dist(bmin, bmax) / 2
    cam.data.ortho_scale = radius * 2.1
    cam.data.clip_end = radius * 8 + 100
    total_back = total_front = 0
    worst = (0, None)
    for az, el in views:
        sc.orbit(cam, centre, az, el, radius * 3 + 10)
        scene.render.filepath = tmp if not keep else os.path.join(keep, f"{obj.name}_{az}_{int(el)}.png")
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(scene.render.filepath)
        px = np.array(img.pixels[:]).reshape(-1, 4)
        bpy.data.images.remove(img)
        back = int(((px[:, 0] > 0.6) & (px[:, 1] < 0.4) & (px[:, 2] > 0.6)).sum())
        front = int((px[:, 1] > 0.6).sum())
        total_back += back
        total_front += front
        if back > worst[0]:
            worst = (back, (az, el))
    return total_back, total_front, worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--keep", default="", help="directory that receives the diagnostic images")
    args = ap.parse_args()
    if args.keep:
        os.makedirs(args.keep, exist_ok=True)
    palette.write_texture(sc.TEXTURE_PATH)
    scene, cam, mat = setup()
    tmp = os.path.join(tempfile.mkdtemp(prefix="backface_"), "view.png")

    jobs = []
    for name in registry.ASSETS:
        jobs.append((name, lambda n=name: registry.build(n), VIEWS_ASSET))
    manifest = json.load(open(sc.path("world", "asset_manifest.json")))["assets"]
    plan = pl.build_plan(manifest)
    from build_world import build_world_meshes
    for name, mb, _origin, _col, _extra in build_world_meshes(plan):
        jobs.append((name, lambda m=mb: m, VIEWS_GROUND))
    only = [n for n in args.only.split(",") if n]
    if only:
        jobs = [j for j in jobs if j[0] in only]

    results = {}
    for name, make, views in jobs:
        mb = make()
        mesh = mb.to_mesh(name, sc.TEXTURE_PATH)
        mesh.materials.clear()
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(name, mesh)
        scene.collection.objects.link(obj)
        bmin, bmax = mb.bounds()
        back, front, worst = count_backfaces(scene, cam, obj, bmin, bmax, views, tmp, args.keep or None)
        bpy.data.objects.remove(obj)
        bpy.data.meshes.remove(mesh)
        results[name] = {"backface_pixels": back, "front_pixels": front, "views": len(views),
                         "worst_view": worst[1]}
        flag = "" if back == 0 else f"  <-- {back} back-face pixels, worst view az/el {worst[1]}"
        print(f"[audit] {name:32s} front {front:7d}{flag}")
    if not only:
        with open(sc.path("world", "backface_audit.json"), "w") as fh:
            json.dump({"resolution": RES, "results": results}, fh, indent=1)
    bad = {k: v for k, v in results.items() if v["backface_pixels"]}
    print(f"{len(results)} meshes audited, {len(bad)} with visible back faces")


if __name__ == "__main__":
    main()
