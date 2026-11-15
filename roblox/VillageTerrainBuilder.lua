--[[
	VillageTerrainBuilder  (ModuleScript, OPTIONAL)

	Alternative to the terrain meshes: writes the village ground into Roblox
	smooth Terrain from the generated WorldHeightmap module.  Use it when you
	prefer native terrain (grass decoration, cheap collision, real water).

		local TB = require(game.ServerStorage.VillageWorld.VillageTerrainBuilder)
		TB.build({ heightmap = require(game.ServerStorage.VillageWorld.WorldHeightmap) })

	and build the meshes without the mesh ground:

		Builder.build({ ..., excludeGroups = { terrain = true, water = true }, roadLift = 0.6 })

	Voxel terrain has a 4 stud resolution and is smoothed by the engine, so it
	follows the designed surface only approximately (roads may need roadLift).
	This module could not be executed outside Roblox Studio; treat it as a
	starting point and check the result in Studio.
]]

local TerrainBuilder = {}

TerrainBuilder.DEFAULTS = {
	heightmap = nil,          -- require(WorldHeightmap) (required)
	terrain = nil,            -- defaults to workspace.Terrain
	origin = nil,             -- CFrame of the village centre (same value as for VillageWorldBuilder)
	depth = 24,               -- how far the ground extends below the lowest point
	water = true,             -- fill the stream and the pond with Water
	waterDepth = 3.5,
	yieldEvery = 2000,
}

-- Decodes the two-character height samples. Returns a flat array (row major).
function TerrainBuilder.decodeHeights(heightmap)
	local index = {}
	local alphabet = heightmap.alphabet
	for i = 1, #alphabet do
		index[string.sub(alphabet, i, i)] = i - 1
	end
	local text = heightmap.heights
	local values = {}
	local count = 0
	for i = 1, #text, 2 do
		local hi = index[string.sub(text, i, i)]
		local lo = index[string.sub(text, i + 1, i + 1)]
		count = count + 1
		values[count] = (hi * 90 + lo) * heightmap.step - heightmap.offset
	end
	return values
end

function TerrainBuilder.build(options)
	local opts = {}
	for key, value in pairs(TerrainBuilder.DEFAULTS) do
		opts[key] = value
	end
	for key, value in pairs(options or {}) do
		opts[key] = value
	end
	local hm = opts.heightmap
	assert(hm, "VillageTerrainBuilder: options.heightmap is missing")
	local terrain = opts.terrain or workspace.Terrain
	local origin = opts.origin or CFrame.new(0, 0, 0)

	local n = hm.verticesPerSide
	local cell = hm.cell
	local heights = TerrainBuilder.decodeHeights(hm)
	local lowest = math.huge
	for i = 1, #heights do
		lowest = math.min(lowest, heights[i])
	end
	local bottom = lowest - opts.depth

	local materials = {
		Enum.Material.Grass,      -- grass
		Enum.Material.Rock,       -- rock
		Enum.Material.Sand,       -- shore
		Enum.Material.Ground,     -- stream bed
	}
	local cells = n - 1
	local done = 0
	for j = 0, cells - 1 do
		for i = 0, cells - 1 do
			local a = heights[j * n + i + 1]
			local b = heights[j * n + i + 2]
			local c = heights[(j + 1) * n + i + 1]
			local d = heights[(j + 1) * n + i + 2]
			local top = (a + b + c + d) * 0.25
			local x = hm.originX + (i + 0.5) * cell
			local z = hm.originZ - (j + 0.5) * cell
			local code = tonumber(string.sub(hm.materials, j * cells + i + 1, j * cells + i + 1)) or 0
			local height = top - bottom
			terrain:FillBlock(origin * CFrame.new(x, bottom + height * 0.5, z), Vector3.new(cell, height, cell),
				materials[code + 1] or Enum.Material.Grass)
			done = done + 1
			if opts.yieldEvery > 0 and done % opts.yieldEvery == 0 and task and task.wait then
				task.wait()
			end
		end
	end

	if opts.water and hm.water then
		local pts, widths = hm.water.points, hm.water.halfWidth
		for i = 1, #pts - 1 do
			local p0 = Vector3.new(pts[i][1], pts[i][2], pts[i][3])
			local p1 = Vector3.new(pts[i + 1][1], pts[i + 1][2], pts[i + 1][3])
			local mid = (p0 + p1) * 0.5
			local length = (p1 - p0).Magnitude
			local width = (widths[i] + widths[i + 1])
			local level = math.min(p0.Y, p1.Y)
			local centre = Vector3.new(mid.X, level - opts.waterDepth * 0.5, mid.Z)
			local look = Vector3.new(p1.X, centre.Y, p1.Z)
			terrain:FillBlock(origin * CFrame.new(centre, look), Vector3.new(width, opts.waterDepth, length + cell),
				Enum.Material.Water)
		end
	end
	return { cells = done, bottom = bottom }
end

return TerrainBuilder
