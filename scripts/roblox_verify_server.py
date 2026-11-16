#!/usr/bin/env python3
"""Runs both server start scripts inside the published place and measures the result.

    python3 scripts/roblox_verify_server.py <universeId> <placeId>

Embeds the current roblox/VillageAutoBuild.server.lua and roblox/gameplay/server/Bootstrap.server.lua
(scripts do not start by themselves in a Luau execution session), then builds a workshop on every
plot and checks ground, floor and the walk-in detection.  The place must be published first.
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def read(*parts):
    return open(os.path.join(ROOT, *parts), encoding="utf-8").read()


CHECKS = r'''
task.wait(12)
local out = {}
local function p(...) out[#out + 1] = string.format(...) end
p("VillageReady=%s errors=%d", tostring(workspace:GetAttribute("VillageReady")), #__errors)
for _, e in ipairs(__errors) do p("ERROR %s", e) end
local names = {}
for _, c in ipairs(workspace:GetChildren()) do names[#names + 1] = c.ClassName .. ":" .. c.Name end
p("workspace: %s", table.concat(names, ", "))
local market = workspace:FindFirstChild("ArcaneMarket")
p("market folders: %d", market and #market:GetChildren() or 0)

-- workshops: build one per plot through the real adapter and measure it
local ServerStorage = game:GetService("ServerStorage")
local layout = require(ServerStorage.VillageWorld.WorldLayout)
local WorkshopWorld = require(game:GetService("ServerScriptService").ArcaneServer.WorkshopWorld)
local village = workspace:FindFirstChild("Village")
local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Include
params.FilterDescendantsInstances = { village.terrain, village.roads }
local function ground(x, z)
	local hit = workspace:Raycast(Vector3.new(x, 300, z), Vector3.new(0, -600, 0), params)
	return hit and hit.Position.Y
end
local plots = {}
for _, q in ipairs(layout.workshopPlots.plots) do plots[#plots + 1] = Vector3.new(q[1], q[2], q[3]) end
local holder = Instance.new("Folder")
holder.Name = "VerifyWorkshops"
holder.Parent = workspace
local ww = WorkshopWorld.new(holder, ServerStorage:FindFirstChild("ArcaneAssets"), plots, layout.workshopPlots.half)
local sizes = { { 16, 1 }, { 24, 1 }, { 32, 2 }, { 40, 3 } }
for i, plot in ipairs(plots) do
	local cells, floors = sizes[i][1], sizes[i][2]
	local view = { owner = 100 + i, cells = cells, floors = floors, version = 1, entities = {
		{ uid = "k" .. i, machine = "kettle", gx = 2, gz = 2, floor = 1, rot = 0, inv = {}, fluids = {} } } }
	local room = ww:sync(view, "Werkstatt von Test " .. i)
	local lo, hi, misses = math.huge, -math.huge, 0
	for dx = -40, 40, 8 do
		for dz = -40, 40, 8 do
			local y = ground(plot.X + dx, plot.Z + dz)
			if y then lo, hi = math.min(lo, y), math.max(hi, y) else misses = misses + 1 end
		end
	end
	local half = cells
	local inside = ww:ownerAt(room.origin + Vector3.new(half - 1, 3, 0))
	local opening = ww:ownerAt(room.origin + Vector3.new(0, 3, -half - 1))
	local outside = ww:ownerAt(room.origin + Vector3.new(half + 6, 3, 0))
	local kettle = room.entityFolder:FindFirstChild("k" .. i)
	local parts = #room.shell:GetChildren()
	-- walk-in check: a ray at chest height through the middle of every side must not hit a wall
	local shellParams = RaycastParams.new()
	shellParams.FilterType = Enum.RaycastFilterType.Include
	shellParams.FilterDescendantsInstances = { room.shell }
	local blocked = 0
	for _, dir in ipairs({ Vector3.new(1, 0, 0), Vector3.new(-1, 0, 0), Vector3.new(0, 0, 1), Vector3.new(0, 0, -1) }) do
		local from = room.origin + dir * (half + 8) + Vector3.new(0, 3, 0)
		if workspace:Raycast(from, -dir * 12, shellParams) then blocked = blocked + 1 end
	end
	local sideHit = workspace:Raycast(room.origin + Vector3.new(half + 8, 1.5, half - 3), Vector3.new(-12, 0, 0), shellParams)
	p("plot %d at (%.0f, %.1f, %.0f): ground %.2f..%.2f (plan %.2f, %d misses), floor top %.2f, %d shell parts, %dx%d studs %d floors, "
		.. "owner inside=%s opening=%s outside=%s, openings blocked=%d of 4, wall beside opening=%s, kettle=%s y=%.2f",
		i, plot.X, plot.Y, plot.Z, lo, hi, plot.Y, misses, room.origin.Y, parts, cells * 2, cells * 2, floors,
		tostring(inside), tostring(opening), tostring(outside), blocked, sideHit and sideHit.Instance.Name or "none",
		kettle and kettle.ClassName or "missing", kettle and (kettle.Position.Y - kettle.Size.Y / 2) or 0)
end
holder:Destroy()
return table.concat(out, "\n")
'''


def main():
    universe, place = sys.argv[1:3]
    script = '''local __errors = {}
local function __run(name, fn)
	task.spawn(function()
		local ok, err = xpcall(fn, function(e) return tostring(e) .. "\\n" .. debug.traceback() end)
		if not ok then __errors[#__errors + 1] = name .. ": " .. tostring(err) end
	end)
end
__run("VillageAutoBuild", function()
	local script = game:GetService("ServerScriptService").VillageAutoBuild
''' + read("roblox", "VillageAutoBuild.server.lua") + '''
end)
local __t = os.clock()
while not workspace:GetAttribute("VillageReady") and os.clock() - __t < 60 do task.wait(0.5) end
__run("Bootstrap", function()
	local script = game:GetService("ServerScriptService").ArcaneServer.Bootstrap
''' + read("roblox", "gameplay", "server", "Bootstrap.server.lua") + '''
end)
''' + CHECKS
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
        fh.write(script)
    try:
        return subprocess.call([sys.executable, os.path.join(ROOT, "scripts", "roblox_exec.py"), universe, place, fh.name])
    finally:
        os.unlink(fh.name)


if __name__ == "__main__":
    sys.exit(main())
