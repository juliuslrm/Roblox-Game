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
local __w = os.clock()
while not workspace:GetAttribute("VillageGroundRefined") and os.clock() - __w < 120 do task.wait(1) end
local out = {}
local function p(...) out[#out + 1] = string.format(...) end
p("VillageReady=%s errors=%d", tostring(workspace:GetAttribute("VillageReady")), #__errors)
for _, e in ipairs(__errors) do p("ERROR %s", e) end
local names = {}
for _, c in ipairs(workspace:GetChildren()) do names[#names + 1] = c.ClassName .. ":" .. c.Name end
p("workspace: %s", table.concat(names, ", "))
local market = workspace:FindFirstChild("ArcaneMarket")
p("market folders: %d", market and #market:GetChildren() or 0)
do -- traders: seven textured parts each, standing on the ground behind their stall, loop data usable
	local Motion = require(game:GetService("ReplicatedStorage").ArcaneShared.MarketMotion)
	local lines = {}
	for _, shop in ipairs(market and market:GetChildren() or {}) do
		local figure = shop:FindFirstChild("Figure")
		if not figure then
			lines[#lines + 1] = shop.Name .. ": stand-in figure"
		else
			local pivot = figure:GetAttribute("MerchantPivot")
			local role = figure:GetAttribute("MerchantRole")
			local parts, textured, low, high = 0, 0, math.huge, -math.huge
			for _, d in ipairs(figure:GetChildren()) do
				parts = parts + 1
				if d.TextureID ~= "" then textured = textured + 1 end
				low = math.min(low, d.Position.Y - d.Size.Y / 2)
				high = math.max(high, d.Position.Y + d.Size.Y / 2)
			end
			-- play the loop once like the client does and watch how far the hand parts travel
			local data = Motion.roles[role]
			local travel = 0
			for part, rows in pairs(data.parts) do
				local joint = data.joints[part]
				local mesh = figure[part]
				local rest = pivot:ToObjectSpace(mesh.CFrame)
				local last
				for _, r in ipairs(rows) do
					local cf = pivot * CFrame.new(r[1], r[2], r[3], r[4], r[5], r[6], r[7]) * CFrame.new(-joint[1], -joint[2], -joint[3]) * rest
					if last and part == "fore_r" then travel = travel + (cf.Position - last).Magnitude end
					last = cf.Position
				end
			end
			local stall = shop:FindFirstChild("stall_" .. shop.Name)
			lines[#lines + 1] = string.format("%s: %d parts (%d textured), feet %.2f above pivot, top %.2f, right hand travels %.1f studs per loop, %.1f studs from stall centre",
				shop.Name, parts, textured, low - pivot.Position.Y, high - pivot.Position.Y, travel,
				stall and (Vector3.new(stall.Position.X, 0, stall.Position.Z) - Vector3.new(pivot.Position.X, 0, pivot.Position.Z)).Magnitude or -1)
		end
	end
	p("traders:\n  %s", table.concat(lines, "\n  "))
end
do -- resource nodes: the model of the item stands on the ground and carries the prompt
	local res = workspace:FindFirstChild("ArcaneResources")
	local nodes, meshes, prompts, worst, circles = 0, 0, 0, 0, 0
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Include
	rp.FilterDescendantsInstances = { workspace.Village.terrain, workspace.Village.roads }
	local odd = {}
	for _, f in ipairs(res and res:GetChildren() or {}) do
		nodes = nodes + 1
		local body = f:FindFirstChild("Resource")
		if body and body:IsA("MeshPart") and body.TextureID ~= "" then meshes = meshes + 1 end
		if body and body:FindFirstChildOfClass("ProximityPrompt") then prompts = prompts + 1 end
		if body then
			local hit = workspace:Raycast(body.Position + Vector3.new(0, 60, 0), Vector3.new(0, -200, 0), rp)
			local gap = hit and (body.Position.Y - body.Size.Y / 2 - hit.Position.Y) or 99
			worst = math.max(worst, math.abs(gap))
			if math.abs(gap) > 1.2 then odd[#odd + 1] = string.format("%s %.1f", f.Name, gap) end
		end
	end
	local places, discs = 0, 0
	for _, m in ipairs(workspace.ArcaneMarkers:GetChildren()) do
		if string.sub(m.Name, 1, 5) == "Node_" then circles = circles + 1 end
		local gem = m:FindFirstChild("Gem")
		if gem and gem:FindFirstChildOfClass("ProximityPrompt") and gem:FindFirstChild("Name") then places = places + 1 end
		for _, d in ipairs(m:IsA("BasePart") and { m } or m:GetDescendants()) do
			if d:IsA("BasePart") and d.Material == Enum.Material.Neon then discs = discs + 1 end
		end
	end
	p("place markers: %d posts with name plate and prompt, %d glowing parts left", places, discs)
	p("resource nodes: %d, textured meshes %d, prompts %d, largest gap between model base and ground %.2f studs, old node circles %d %s",
		nodes, meshes, prompts, worst, circles, table.concat(odd, "; "))
end
do
	local fid, total, untextured = {}, 0, 0
	for _, g in ipairs({ "terrain", "roads", "water" }) do
		for _, d in ipairs(workspace.Village[g]:GetDescendants()) do
			if d:IsA("MeshPart") then
				total = total + 1
				if d.TextureID == "" then untextured = untextured + 1 end
				local key = d.RenderFidelity.Name .. "/" .. d.CollisionFidelity.Name
				fid[key] = (fid[key] or 0) + 1
			end
		end
	end
	local s = {}
	for k, v in pairs(fid) do s[#s + 1] = k .. "=" .. v end
	p("ground mesh fidelity (render/collision) of %d parts: %s", total, table.concat(s, " "))
	p("ground parts without texture: %d of %d", untextured, total)
end

local ServerStorage = game:GetService("ServerStorage")
local layout = require(ServerStorage.VillageWorld.WorldLayout)
do -- ground check: rays down on a grid, compared with the height map
	local heightmap = require(ServerStorage.VillageWorld.WorldHeightmap)
	local heights = require(ServerStorage.VillageWorld.VillageTerrainBuilder).decodeHeights(heightmap)
	local n, cell = heightmap.verticesPerSide, heightmap.cell
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Include
	rp.FilterDescendantsInstances = { workspace.Village.terrain }
	local patches = workspace.Village:FindFirstChild("CollisionPatches")
	if patches then
		-- patches are excluded from ray queries in the game; make them count for this measurement
		for _, q in ipairs(patches:GetChildren()) do q.CanQuery = true end
		rp.FilterDescendantsInstances = { workspace.Village.terrain, patches }
	end
	p("collision patches: %d", patches and #patches:GetChildren() or 0)
	local misses, count, worst, sum, big = 0, 0, 0, 0, 0
	for j = 1, n - 2 do
		for i = 1, n - 2 do
			local hit = workspace:Raycast(Vector3.new(heightmap.originX + i * cell, 300, heightmap.originZ - j * cell), Vector3.new(0, -600, 0), rp)
			count = count + 1
			if not hit then misses = misses + 1 else
				local err = math.abs(hit.Position.Y - heights[j * n + i + 1])
				sum = sum + err
				if err > 1.5 then big = big + 1 end
				worst = math.max(worst, err)
			end
		end
	end
	p("ground rays: %d points, %d misses, mean error %.2f, %d over 1.5 studs, worst %.2f", count, misses, sum / math.max(1, count - misses), big, worst)
end

-- workshops: build one per plot through the real adapter and measure it
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
local ww = WorkshopWorld.new(holder, ServerStorage:FindFirstChild("ArcaneAssets"), plots, layout.workshopPlots.half,
	ServerStorage:FindFirstChild("ArcaneItemAssets"))
local sizes = { { 16, 1 }, { 24, 1 }, { 32, 2 }, { 40, 3 } }
for i, plot in ipairs(plots) do
	local cells, floors = sizes[i][1], sizes[i][2]
	local view = { owner = 100 + i, cells = cells, floors = floors, version = 1, entities = {
		{ uid = "k" .. i, machine = "kettle", gx = 2, gz = 2, floor = 1, rot = 0, inv = {}, fluids = {} },
		{ uid = "g" .. i, machine = "grinder", gx = 8, gz = 4, floor = 1, rot = 1, inSide = 2, outSide = 1, outAuto = false, inv = {}, fluids = {} },
		{ uid = "b" .. i, machine = "wooden_belt", gx = 12, gz = 4, floor = 1, rot = 1, inv = {}, fluids = {} },
		{ uid = "t" .. i, machine = "belt_turn", gx = 12, gz = 8, floor = 1, rot = 0, inv = {}, fluids = {} } } }
	local room = ww:sync(view, "Werkstatt von Test " .. i)
	if i == 1 then
		-- directions: a belt with rot 1 conveys towards +X; a curve with rot 0 hands over to its left (-X);
		-- the mill's outlet mark points away from the machine, its inlet mark into it; marks start hidden
		local function dirOf(body, name)
			local shaft = body:FindFirstChild(name)
			return shaft and shaft.CFrame.LookVector
		end
		local belt, turn, mill = room.entityFolder["b1"], room.entityFolder["t1"], room.entityFolder["g1"]
		local fb, ft = dirOf(belt, "Arrow"), dirOf(turn, "Arrow")
		local outMark, inMark = mill:FindFirstChild("PortOut"), mill:FindFirstChild("PortIn")
		local centre = Vector3.new(mill.Position.X, 0, mill.Position.Z)
		local function away(mark)
			local flat = Vector3.new(mark.Position.X, 0, mark.Position.Z) - centre
			return mark.CFrame.LookVector:Dot(flat.Unit)
		end
		local hidden, labels = 0, 0
		for _, d in ipairs(mill:GetDescendants()) do
			if d:IsA("BasePart") and d:GetAttribute("ArcanePortMark") and d.Transparency == 1 then hidden = hidden + 1 end
			if d:IsA("BillboardGui") and d.Name == "PortLabel" and not d.Enabled then labels = labels + 1 end
		end
		do -- goods: the server publishes them as attributes; clients draw them (GoodsAnimator)
			local now = workspace:GetServerTimeNow()
			ww:syncGoods(101, { b1 = { item = "herb_mint", age = 0.5, inDir = 1 } }, now)
			local surface = belt:GetAttribute("GoodsSurface")
			local top = belt.Position.Y + belt.Size.Y / 2
			local first = string.format("item=%s at=%.2f s ago in=%s out=%s period=%s cell=%s surface %.2f vs belt top %.2f",
				tostring(belt:GetAttribute("GoodsItem")), now - (belt:GetAttribute("GoodsAt") or 0), tostring(belt:GetAttribute("GoodsIn")),
				tostring(belt:GetAttribute("GoodsOut")), tostring(belt:GetAttribute("GoodsPeriod")), tostring(belt:GetAttribute("GoodsCell")),
				surface and surface.Y or -1, top)
			ww:syncGoods(101, {}, now + 1)
			local models = game:GetService("ReplicatedStorage"):FindFirstChild("ArcaneItemModels")
			local n = 0
			for _, d in ipairs(models and models:GetDescendants() or {}) do if d:IsA("MeshPart") then n = n + 1 end end
			p("goods attributes: %s; after leaving: item=%s; curve out=%s; mill has none=%s; item models for clients: %d, server-drawn goods: %s",
				first, tostring(belt:GetAttribute("GoodsItem")), tostring(turn:GetAttribute("GoodsOut")),
				tostring(mill:GetAttribute("GoodsOut") == nil), n, belt:FindFirstChild("Goods") and "yes" or "none")
		end
		p("directions: belt rot 1 arrow (%.1f, %.1f), curve rot 0 arrow (%.1f, %.1f), outlet mark away %.2f, inlet mark away %.2f, %d hidden mark parts, %d hidden labels, outlet label '%s'",
			fb.X, fb.Z, ft.X, ft.Z, away(outMark), away(inMark), hidden, labels, outMark.PortLabel:FindFirstChildOfClass("TextLabel").Text)
	end
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
