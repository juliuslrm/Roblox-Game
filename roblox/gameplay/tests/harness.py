"""Loads the gameplay Lua modules in a plain Lua runtime (via lupa).

The modules use Roblox-style `require(script.Parent.X)` and
`game:GetService("ReplicatedStorage"):WaitForChild("ArcaneShared")`.  The
harness provides minimal `script` / `game` stand-ins that map onto the files in
roblox/gameplay, so the very same source files run here and in Roblox.
"""
import os

from lupa import LuaRuntime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
GAMEPLAY = os.path.join(ROOT, "roblox", "gameplay")

LOADER = r"""
local readFile, exists = ...
local cache = {}
local nodeMeta = {}
local function node(path, name, parent)
    return setmetatable({ __path = path, Name = name, Parent = parent }, nodeMeta)
end
nodeMeta.__index = function(self, key)
    if key == "WaitForChild" or key == "FindFirstChild" then
        return function(s, childName) return s[childName] end
    end
    local p = rawget(self, "__path") .. "/" .. key
    if exists(p .. ".lua") then return node(p .. ".lua", key, self) end
    if exists(p .. ".server.lua") then return node(p .. ".server.lua", key, self) end
    if exists(p) then return node(p, key, self) end
    return nil
end
local services = {
    ReplicatedStorage = { ArcaneShared = "shared" },
    ServerScriptService = { ArcaneServer = "server" },
}
game = { GetService = function(_, name)
    local map = services[name] or {}
    local svc = { WaitForChild = function(s, child) return s[child] end, FindFirstChild = function(s, child) return s[child] end }
    return setmetatable(svc, { __index = function(_, child)
        if map[child] then return node(ROOT_PATH .. "/" .. map[child], child, nil) end
    end })
end }
function arcaneRequire(n)
    local path = rawget(n, "__path")
    if cache[path] ~= nil then return cache[path] end
    local env = setmetatable({ script = n, require = arcaneRequire }, { __index = _G })
    local dir = path:match("^(.*)/[^/]+$")
    rawset(n, "Parent", rawget(n, "Parent") or node(dir, dir:match("[^/]+$"), nil))
    local fn, err = load(readFile(path), "=" .. path:match("[^/]+$"), "t", env)
    if not fn then error(err) end
    local result = fn()
    cache[path] = result
    return result
end
function loadModule(rel)
    return arcaneRequire(node(ROOT_PATH .. "/" .. rel .. ".lua", rel:match("[^/]+$"), nil))
end
"""


def new_runtime():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().ROOT_PATH = GAMEPLAY

    def read_file(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    lua.execute("function __init(...) " + LOADER + " end")
    lua.globals().__init(read_file, os.path.exists)
    return lua


def lua_list(t):
    return [t[i] for i in range(1, len(t) + 1)]
