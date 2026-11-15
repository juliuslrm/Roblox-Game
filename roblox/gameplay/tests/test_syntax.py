"""Compiles every gameplay Lua file (syntax only) and checks the Lua 5.1 subset rules.

Roblox-only files (Bootstrap, WorkshopWorld, client) cannot be executed here; compiling them at
least catches syntax errors.  Their behaviour is UNVERIFIED_IN_STUDIO.
"""
import os
import re
import sys

from lupa import LuaRuntime

from harness import GAMEPLAY, ROOT

FORBIDDEN = [(r"\bcontinue\b", "continue"), (r"[+\-*/]=", "compound assignment"), (r":\s*(number|string|boolean)\s*[,)=]", "type annotation")]


def main():
    lua = LuaRuntime()
    check = lua.eval("function(src, name) local f, err = load(src, name) return f ~= nil, err end")
    files = []
    for base, _dirs, names in os.walk(GAMEPLAY):
        files += [os.path.join(base, n) for n in names if n.endswith(".lua")]
    files += [os.path.join(ROOT, "roblox", n) for n in ("VillageWorldBuilder.lua", "VillageTerrainBuilder.lua")]
    bad = 0
    for path in sorted(files):
        src = open(path, encoding="utf-8").read()
        ok, err = check(src, "=" + os.path.relpath(path, ROOT))
        if not ok:
            print("  FAIL", err)
            bad += 1
        code = re.sub(r"--\[\[.*?\]\]", "", src, flags=re.S)
        code = "\n".join(re.sub(r'"(\\.|[^"\\])*"', '""', line.split("--")[0]) for line in code.splitlines())
        for pattern, what in FORBIDDEN:
            if re.search(pattern, code):
                print(f"  FAIL {os.path.relpath(path, ROOT)}: uses {what}")
                bad += 1
    print(f"syntax: {len(files)} Lua files compiled, {bad} problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
