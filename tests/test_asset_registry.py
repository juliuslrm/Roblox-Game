"""The asset registry must still know every asset that the exported world uses.

Guards against a module of the village pipeline being replaced by accident (it happened once: the
trader props were written over blender/village/props.py, and nothing noticed because the world is
loaded from already exported files).
    VILLAGE_PYTHON=/opt/bpyenv/bin/python python tests/test_asset_registry.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))

import bpy  # noqa: E402,F401  (mathutils comes with bpy)
from village import registry  # noqa: E402


def main():
    manifest = json.loads((ROOT / "world/asset_manifest.json").read_text(encoding="utf-8"))["assets"]
    exported = {name: a["category"] for name, a in manifest.items() if "category" in a}
    missing = sorted(n for n in exported if n not in registry.ASSETS)
    wrong = sorted(n for n, c in exported.items() if n in registry.ASSETS and registry.ASSETS[n]["category"] != c)
    assert not missing, f"exported assets without a builder: {missing}"
    assert not wrong, f"assets in another category than exported: {wrong}"
    print(f"  ok  asset registry: all {len(exported)} exported assets have their builder")


if __name__ == "__main__":
    main()
