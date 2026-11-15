#!/usr/bin/env bash
# Rebuilds everything from the Python sources.
#   ./build.sh            assets + world + validation
#   ./build.sh --render   additionally re-render all previews (several minutes, CPU)
set -euo pipefail
cd "$(dirname "$0")"
PY="${VILLAGE_PYTHON:-.venv/bin/python}"
"$PY" blender/build_assets.py
"$PY" blender/build_world.py
if [ "${1:-}" = "--render" ]; then
  "$PY" blender/render_previews.py assets
  "$PY" blender/render_previews.py hero
  "$PY" blender/render_previews.py world
fi
"$PY" blender/validate.py
