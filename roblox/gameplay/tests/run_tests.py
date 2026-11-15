"""Runs the Lua test suites of the gameplay core.  python run_tests.py [suite ...]"""
import sys

from harness import new_runtime, lua_list

SUITES = ["spec_core", "spec_progression", "spec_adapter"]


def run(name):
    lua = new_runtime()
    res = lua.eval(f'loadModule("tests/{name}")')
    failed = lua_list(res.failed)
    for line in lua_list(res.names):
        print("  ok  ", line)
    for line in failed:
        print("  FAIL", line)
    info = lua_list(res.info) if res.info else []
    for line in info:
        print("  info", line)
    print(f"{name}: {res.passed} passed, {len(failed)} failed")
    return len(failed)


if __name__ == "__main__":
    import os
    wanted = sys.argv[1:] or [s for s in SUITES if os.path.exists(os.path.join(os.path.dirname(__file__), s + ".lua"))]
    total = sum(run(s) for s in wanted)
    sys.exit(1 if total else 0)
