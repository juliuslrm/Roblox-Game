#!/usr/bin/env bash
# Runs every check that can be executed without Roblox Studio.
#   ./scripts/check_all.sh          gameplay tests + world validation (about 1 minute)
#   ./scripts/check_all.sh --full   additionally rebuilds the gameplay assets and re-runs the back-face audit
set -uo pipefail
cd "$(dirname "$0")/.."
PY="${VILLAGE_PYTHON:-.venv/bin/python}"
[ -x "$PY" ] || PY=python3
fail=0
run() { echo; echo "== $1"; shift; "$@" || fail=1; }
cd roblox/gameplay/tests
run "data integrity"            "$PY" test_data.py
run "lua syntax (all modules)"  "$PY" test_syntax.py
run "gameplay core / progression / adapters" "$PY" run_tests.py
cd ../../..
run "village builder (mock)"    "$PY" tests/test_roblox_builder.py
run "place file + auto build"   "$PY" tests/test_place_and_autobuild.py
if [ "${1:-}" = "--full" ]; then
  run "gameplay assets"         "$PY" blender/build_gameplay_assets.py
  run "resource assets"         "$PY" blender/build_resource_assets.py
  run "item assets"             "$PY" blender/build_item_assets.py --no-render
  run "back-face audit"         "$PY" blender/audit_backfaces.py
fi
run "world validation"          "$PY" blender/validate.py
echo
if [ "$fail" = 0 ]; then echo "ALL CHECKS PASSED (TESTED_LOCAL only - nothing here runs in Roblox Studio)"; else echo "SOME CHECKS FAILED"; fi
exit $fail
