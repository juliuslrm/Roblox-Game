--[[
	VillageAutoBuild  (ModuleScript, UNVERIFIED_IN_STUDIO)

	Builds the village automatically when the place starts, so the place file works
	without any manual step:

	  * meshes imported (ServerStorage.VillageAssets exists)  -> VillageWorldBuilder places them
	  * no meshes yet                                         -> "greybox": voxel terrain from the
	    height map plus one coloured block per building, at the exact planned position and size

	Either way the gameplay (anchors, markers, workshop door) uses the same coordinates.
	Lua 5.1 subset, so the placement can be tested outside Roblox.
]]
local Auto = {}

local COLORS = {
	houses = { 221, 169, 143 }, landmarks = { 111, 78, 124 }, props = { 154, 150, 140 },
}
local EXTRA = { bridge_stone = true, fountain = true, well = true, gate_arch = true, dock = true }

-- One anchored block per building (and a few key props), sized like the designed bounding box.
function Auto.greybox(layout, parent, origin)
	local folder = Instance.new("Folder")
	folder.Name = "Village"
	local boxes = Instance.new("Folder")
	boxes.Name = "greybox"
	boxes.Parent = folder
	local count = 0
	for _, row in ipairs(layout.instances) do
		local name = layout.assetNames[row[1]]
		local def = layout.assets[name]
		if def.category == "houses" or def.category == "landmarks" or EXTRA[name] then
			local part = Instance.new("Part")
			part.Name = row[8] or name
			part.Anchored = true
			part.Size = Vector3.new(def.size[1], def.size[2], def.size[3])
			part.CFrame = origin * CFrame.new(row[2], row[3], row[4]) * CFrame.Angles(0, math.rad(row[5]), 0)
				* CFrame.new(def.center[1], def.center[2], def.center[3])
			local c = COLORS[def.category] or COLORS.props
			part.Color = Color3.fromRGB(c[1], c[2], c[3])
			pcall(function()
				part.Material = Enum.Material.SmoothPlastic
				part:SetAttribute("Greybox", true)
				part:SetAttribute("AssetId", name)
			end)
			-- the bridge and the gate must stay passable: no collision for the gate block
			if name == "gate_arch" then part.CanCollide = false part.Transparency = 0.6 end
			part.Parent = boxes
			count = count + 1
		end
	end
	folder.Parent = parent
	return folder, count
end

--[[
	opts: layout, heightmap, builder (VillageWorldBuilder), terrainBuilder (VillageTerrainBuilder),
	      templates (Instance or nil), parent (default workspace), origin (CFrame, default identity)
	Returns { mode = "meshes" | "greybox", meshTerrain = bool, placed = n, missing = n, terrainCells = n }
]]
function Auto.run(opts)
	local parent = opts.parent or workspace
	local origin = opts.origin or CFrame.new(0, 0, 0)
	local report = { mode = "greybox", meshTerrain = false, placed = 0, missing = 0, terrainCells = 0 }
	local old = parent:FindFirstChild("Village")
	if old then old:Destroy() end

	local templates = opts.templates
	if templates then
		report.mode = "meshes"
		report.meshTerrain = templates:FindFirstChild("terrain_r0_c0", true) ~= nil
		local exclude = nil
		if not report.meshTerrain then exclude = { terrain = true, water = true } end
		local built = opts.builder.build({ templates = templates, layout = opts.layout, parent = parent, origin = origin,
			excludeGroups = exclude, roadLift = report.meshTerrain and 0 or 0.6, verbose = false })
		report.placed = built.placed
		for _, n in pairs(built.missing) do report.missing = report.missing + n end
		report.warnings = built.warnings
	else
		local _folder, count = Auto.greybox(opts.layout, parent, origin)
		report.placed = count
	end
	if not report.meshTerrain and opts.terrainBuilder and opts.heightmap then
		local res = opts.terrainBuilder.build({ heightmap = opts.heightmap, origin = origin })
		report.terrainCells = res.cells
	end
	return report
end

return Auto
