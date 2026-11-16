#!/usr/bin/env python3
"""Runs a Luau script inside the published place through Roblox Open Cloud and prints result + logs.

    ROBLOX_API_KEY=... python3 scripts/roblox_exec.py <universeId> <placeId> script.lua

Needs an API key with `luau-execution-sessions: write` for the experience.  The script runs in a
headless copy of the place (game scripts do not start by themselves); `return` values and print
output come back.  Used to verify the Roblox adapters without Roblox Studio.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://apis.roblox.com/cloud/v2/"


def call(method, url, body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("x-api-key", os.environ.get("ROBLOX_API_KEY", "proxy-injected"))
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"HTTP {exc.code}: {exc.read().decode()[:2000]}")


def main():
    universe, place, path = sys.argv[1:4]
    timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    script = open(path, encoding="utf-8").read()
    task = call("POST", f"{BASE}universes/{universe}/places/{place}/luau-execution-session-tasks",
                {"script": script, "timeout": f"{timeout}s"})
    task_path = task["path"]
    deadline = time.time() + timeout + 60
    while task.get("state") in ("PROCESSING", "QUEUED", None) and time.time() < deadline:
        time.sleep(3)
        task = call("GET", BASE + task_path)
    logs = call("GET", BASE + task_path + "/logs?maxPageSize=10000")
    for entry in logs.get("luauExecutionSessionTaskLogs", []):
        for line in entry.get("messages", []):
            print(line)
    print("STATE", task.get("state"))
    if task.get("error"):
        print("ERROR", json.dumps(task["error"], ensure_ascii=False))
    if task.get("output"):
        for value in task["output"].get("results", []):
            print(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False))
    return 0 if task.get("state") == "COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
