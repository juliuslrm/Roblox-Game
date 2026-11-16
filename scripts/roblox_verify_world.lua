-- Rebuilds the village exactly like VillageAutoBuild.server.lua and measures the result.
local ServerStorage = game:GetService("ServerStorage")
local folder = ServerStorage.VillageWorld
local out = {}
local function p(...) out[#out + 1] = string.format(...) end
local ids = require(folder.VillageAssetIds)
local loaded = require(folder.VillageAssetLoader).load({ ids = ids, insertService = game:GetService("InsertService"), parent = ServerStorage })
p("loader: %d loaded, %d failed, %d mesh parts, %d retextured", loaded.loaded, #loaded.failed, loaded.meshParts, loaded.retextured)
local layout = require(folder.WorldLayout)
local heightmap = require(folder.WorldHeightmap)
local builder = require(folder.VillageWorldBuilder)
local terrainBuilder = require(folder.VillageTerrainBuilder)
local found, missing = builder.checkTemplates(ServerStorage.VillageAssets, layout)
p("templates: %d found, %d missing %s", #found, #missing, table.concat(missing, ","))
local t0 = os.clock()
local report = require(folder.VillageAutoBuild).run({ layout = layout, heightmap = heightmap, builder = builder,
	terrainBuilder = terrainBuilder, templates = ServerStorage.VillageAssets, createLights = false })
p("build: mode=%s meshTerrain=%s placed=%d missing=%d terrainCells=%d in %.1fs", report.mode, tostring(report.meshTerrain),
	report.placed, report.missing, report.terrainCells, os.clock() - t0)
for i = 1, math.min(8, #(report.warnings or {})) do p("warning: %s", report.warnings[i]) end
p("warnings total: %d", #(report.warnings or {}))
local village = workspace.Village
local names = {}
for _, c in ipairs(village:GetChildren()) do names[#names + 1] = c.Name .. "(" .. #c:GetChildren() .. ")" end
p("groups: %s", table.concat(names, " "))

local t1 = os.clock()
local conv, failed, lastError = require(folder.VillageAutoBuild).refineCollision(village, game:GetService("AssetService"))
p("refineCollision: %d converted, %d failed (%s) in %.1fs", conv, failed, tostring(lastError), os.clock() - t1)
task.wait(1)
-- ground check: ray down on a grid, compare with the height map
local heights = terrainBuilder.decodeHeights(heightmap)
local n, cell = heightmap.verticesPerSide, heightmap.cell
local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Include
local include = {}
for _, g in ipairs({ "terrain" }) do if village:FindFirstChild(g) then include[#include + 1] = village[g] end end
params.FilterDescendantsInstances = include
local misses, count, worst, sum, big = 0, 0, 0, 0, 0
local worstAt = ""
for j = 2, n - 3, 4 do
	for i = 2, n - 3, 4 do
		local x = heightmap.originX + i * cell
		local z = heightmap.originZ - j * cell
		local expected = heights[j * n + i + 1]
		local hit = workspace:Raycast(Vector3.new(x, 300, z), Vector3.new(0, -600, 0), params)
		count = count + 1
		if not hit then misses = misses + 1 else
			local err = math.abs(hit.Position.Y - expected)
			sum = sum + err
			if err > 1.5 then big = big + 1 end
			if err > worst then worst = err worstAt = string.format("(%d,%d) hit %.1f expected %.1f on %s", x, z, hit.Position.Y, expected, hit.Instance.Name) end
		end
	end
end
p("ground rays: %d points, %d misses, mean error %.2f, %d over 1.5 studs, worst %.2f %s", count, misses, sum / math.max(1, count - misses), big, worst, worstAt)
return table.concat(out, "\n")
