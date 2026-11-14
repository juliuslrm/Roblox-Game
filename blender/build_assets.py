"""Build every reusable asset: .blend source, .glb export, combined library
(.glb + .fbx) and the asset manifest.

    python blender/build_assets.py [--only id,id] [--no-library]
"""
import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from village import coords, export, palette, registry  # noqa: E402
from village import scene as sc  # noqa: E402

MANIFEST = sc.path("world", "asset_manifest.json")


def collider_to_roblox(c):
    out = {"shape": c["shape"], "center": coords.to_roblox(c["center"])}
    if c["shape"] == "box":
        out["size"] = coords.size_to_roblox(c["size"])
        out["yaw_deg"] = round(c["rot_z"], 3)
    else:
        out["radius"] = round(c["radius"], 3)
        out["height"] = round(c["height"], 3)
    return out


def describe(name, mb):
    info = registry.ASSETS[name]
    bmin, bmax = mb.bounds()
    return {
        "category": info["category"],
        "blend": f"{info['dir']}/{name}.blend",
        "glb": f"exports/glb/{info['category']}/{name}.glb",
        "triangles": mb.tri_count(),
        "vertices": len(mb.verts),
        "collision": mb.collision,
        "bounds_blender": {"min": [round(v, 4) for v in bmin], "max": [round(v, 4) for v in bmax]},
        "bounds_roblox": coords.bounds_to_roblox(bmin, bmax),
        "colliders": [collider_to_roblox(c) for c in mb.colliders],
        "lights": [{"position": coords.to_roblox(lt["position"]),
                    "color": [round(v, 3) for v in lt["color"]],
                    "brightness": lt["brightness"], "range": lt["range"]} for lt in mb.lights],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--no-library", action="store_true")
    args = ap.parse_args()
    names = [n for n in args.only.split(",") if n] or list(registry.ASSETS)
    palette.write_texture(sc.TEXTURE_PATH)

    manifest = {}
    if args.only and os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST))["assets"]
    t0 = time.time()
    for name in names:
        export.new_scene()
        mb = registry.build(name)
        obj = mb.to_object(name, sc.TEXTURE_PATH)
        entry = describe(name, mb)
        export.save_blend(sc.path(entry["blend"]))
        export.export_glb([obj], sc.path(entry["glb"]))
        manifest[name] = entry
        print(f"[asset] {name:32s} {entry['triangles']:6d} tris  {entry['collision']}")
    manifest = {k: manifest[k] for k in registry.ASSETS if k in manifest}

    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w") as fh:
        json.dump({"units": "studs", "texture": "exports/textures/" + palette.TEXTURE_NAME,
                   "assets": manifest}, fh, indent=1)

    if not args.no_library:
        # one file with every asset as a separately named object, laid out on a grid
        export.new_scene()
        objs = []
        cursor = {}
        for name in registry.ASSETS:
            mb = registry.build(name)
            obj = mb.to_object(name, sc.TEXTURE_PATH)
            cat = registry.ASSETS[name]["category"]
            row = list(registry.CATEGORIES).index(cat)
            bmin, bmax = mb.bounds()
            x = cursor.get(cat, 0.0) - bmin[0]
            obj.location = (x, row * 90.0, 0.0)
            cursor[cat] = x + bmax[0] + 6.0
            objs.append(obj)
        export.save_blend(sc.path("assets", "village_asset_library.blend"))
        export.export_glb(objs, sc.path("exports", "library", "village_assets.glb"))
        export.export_fbx(objs, sc.path("exports", "library", "village_assets.fbx"))
    print(f"built {len(names)} assets in {time.time() - t0:.1f}s, total "
          f"{sum(e['triangles'] for e in manifest.values())} tris")


if __name__ == "__main__":
    main()
