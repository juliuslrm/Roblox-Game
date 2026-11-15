#!/usr/bin/env bash
# Creates .venv with Blender-as-a-module (bpy) and the helper libraries.
# bpy 5.3 wheels need Python 3.13 on Linux x86_64 / macOS / Windows.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
"$PY" -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/python -c "import bpy; print('Blender', bpy.app.version_string, 'ready')"
