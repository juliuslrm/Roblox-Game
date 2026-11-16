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

local function hasParts(template)
	if not template or template.Archivable == false then return false end
	if template:IsA("BasePart") then return true end
	for _, child in ipairs(template:GetChildren()) do
		if hasParts(child) then return true end
	end
	return false
end

local function missingTerrainTemplates(layout, templates)
	local checked, missing = {}, {}
	for _, row in ipairs(layout.instances) do
		local group = layout.groupNames[row[7]]
		if group == "terrain" or group == "water" then
			local name = layout.assetNames[row[1]]
			if not checked[name] then
				checked[name] = true
				local template = templates.Name == name and templates or templates:FindFirstChild(name, true)
				if not hasParts(template) then missing[#missing + 1] = name end
			end
		end
	end
	table.sort(missing)
	return missing
end

--[[
	opts: layout, heightmap, builder (VillageWorldBuilder), terrainBuilder (VillageTerrainBuilder),
	      templates (Instance or nil), parent (default workspace), origin (CFrame, default identity)
	Returns mode, meshTerrain, placed, missing (instance count), terrainCells,
	        missingTerrain (template names), warnings and needsPreciseCollision.
]]
function Auto.run(opts)
	local parent = opts.parent or workspace
	local origin = opts.origin or CFrame.new(0, 0, 0)
	local report = { mode = "greybox", meshTerrain = false, placed = 0, missing = 0, terrainCells = 0,
		missingTerrain = {}, warnings = {}, needsPreciseCollision = {} }
	local old = parent:FindFirstChild("Village")
	if old then old:Destroy() end

	local templates = opts.templates
	if templates then
		report.mode = "meshes"
		report.missingTerrain = missingTerrainTemplates(opts.layout, templates)
		report.meshTerrain = #report.missingTerrain == 0
		local exclude = nil
		if not report.meshTerrain then exclude = { terrain = true, water = true } end
		local built = opts.builder.build({ templates = templates, layout = opts.layout, parent = parent, origin = origin,
			workshopFacade = opts.workshopFacade, excludeGroups = exclude, roadLift = report.meshTerrain and 0 or 0.6, verbose = false,
			createLights = opts.createLights ~= false })
		report.placed = built.placed
		for _, n in pairs(built.missing) do report.missing = report.missing + n end
		report.warnings = built.warnings
		report.needsPreciseCollision = built.needsPreciseCollision
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

--[[
	Gives the ground meshes (terrain, roads, water) exact collision and exact rendering.

	Imported MeshParts arrive with CollisionFidelity.Default and RenderFidelity.Automatic, and
	neither can be changed from a script.  Measured / seen in the place (2026-11-16):
	  * Default collision misses the real ground by more than 1.5 studs at about 5 % of the points
	  * Automatic rendering swaps the big terrain meshes for coarser versions at a distance, so the
	    ground changes shape while walking and roads float or sink
	AssetService:CreateMeshPartAsync creates the same mesh with precise settings, MeshPart:ApplyMesh
	swaps it in.  That takes about 0.6 s per part and does not get faster in parallel (33 s for all
	54), so it runs in the background, nearest parts to `focus` first.

	Precise collision has a flaw of its own: about 0.25 % of the terrain area gets no collision at
	all (measured: 90 of 36 481 sample points, also on the village square).  After each terrain
	part is converted its square is scanned with rays and every hole is closed with an invisible
	plate at the height of the height map.

	opts: village (Folder built by Auto.run), assetService, heightmap, decodeHeights (function),
	      origin (CFrame), focus (Vector3, world), step (studs between rays, default 2)
	-> { converted, failed, patches, lastError }
]]
function Auto.refineGround(opts)
	local village, origin = opts.village, opts.origin or CFrame.new(0, 0, 0)
	local step = opts.step or 2
	local hm = opts.heightmap
	local heights = hm and opts.decodeHeights and opts.decodeHeights(hm)
	local function heightAt(x, z) -- village-local, bilinear
		local n, cell = hm.verticesPerSide, hm.cell
		local fx = math.clamp((x - hm.originX) / cell, 0, n - 1.001)
		local fz = math.clamp((hm.originZ - z) / cell, 0, n - 1.001)
		local i, j = math.floor(fx), math.floor(fz)
		local u, v = fx - i, fz - j
		local a, b = heights[j * n + i + 1], heights[j * n + i + 2]
		local c, d = heights[(j + 1) * n + i + 1], heights[(j + 1) * n + i + 2]
		return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v
	end

	local parts = {}
	for _, groupName in ipairs({ "terrain", "roads", "water" }) do
		local group = village:FindFirstChild(groupName)
		if group then
			for _, part in ipairs(group:GetDescendants()) do
				if part:IsA("MeshPart") then parts[#parts + 1] = { part = part, terrain = groupName == "terrain" } end
			end
		end
	end
	local focus = opts.focus or origin.Position
	table.sort(parts, function(a, b) return (a.part.Position - focus).Magnitude < (b.part.Position - focus).Magnitude end)

	local report = { converted = 0, failed = 0, patches = 0, lastError = nil }
	local patchFolder
	for _, entry in ipairs(parts) do
		local part = entry.part
		local ok, err = pcall(function()
			local precise = opts.assetService:CreateMeshPartAsync(Content.fromUri(part.MeshId), {
				CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition,
				RenderFidelity = Enum.RenderFidelity.Precise,
			})
			local size, cframe = part.Size, part.CFrame
			part:ApplyMesh(precise)
			part.Size, part.CFrame = size, cframe
			precise:Destroy()
		end)
		if not ok then
			report.failed = report.failed + 1
			report.lastError = tostring(err)
		else
			report.converted = report.converted + 1
			if entry.terrain and heights and part.CanCollide then
				task.wait() -- let the new collision geometry take effect before it is scanned
				local params = RaycastParams.new()
				params.FilterType = Enum.RaycastFilterType.Include
				params.FilterDescendantsInstances = { part }
				local centre = origin:PointToObjectSpace(part.Position)
				local half = math.max(part.Size.X, part.Size.Z) / 2
				local up = origin.UpVector
				for x = centre.X - half + step / 2, centre.X + half, step do
					for z = centre.Z - half + step / 2, centre.Z + half, step do
						local y = heightAt(x, z)
						local from = origin * Vector3.new(x, y + 200, z)
						if not workspace:Raycast(from, -up * 400, params) then
							if not patchFolder then
								patchFolder = Instance.new("Folder")
								patchFolder.Name = "CollisionPatches"
								patchFolder.Parent = village
							end
							local plate = Instance.new("Part")
							plate.Name, plate.Anchored, plate.Transparency, plate.CastShadow = "Patch", true, 1, false
							plate.CanQuery = false
							plate.Size = Vector3.new(step, 1, step)
							plate.CFrame = origin * CFrame.new(x, y - 0.5, z)
							plate.Parent = patchFolder
							report.patches = report.patches + 1
						end
					end
				end
			end
		end
	end
	return report
end

return Auto
