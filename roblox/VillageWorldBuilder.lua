--[[
	VillageWorldBuilder  (ModuleScript)

	Assembles the village from imported meshes and the generated WorldLayout
	module.  Run it once in Studio (command bar or plugin) and save the place,
	or call it from a server Script at runtime.

		local Builder = require(game.ServerStorage.VillageWorld.VillageWorldBuilder)
		local report = Builder.build({
			templates = game.ServerStorage.VillageAssets,   -- everything you imported
			layout    = require(game.ServerStorage.VillageWorld.WorldLayout),
		})

	How templates are matched
		Every imported mesh keeps the name of its asset id (for example
		"house_01_timber_cottage").  The builder searches `templates` for an
		Instance with that name; it may be a MeshPart or a Model.

	Why import settings hardly matter
		The layout stores the designed bounding box of every asset.  The builder
		measures each imported template, derives the import scale from it and
		re-centres the template on its designed origin.  So it does not matter
		at which scale or position the importer dropped the meshes, as long as
		they are upright and unrotated (default importer behaviour for glTF/FBX
		files exported by this project).

	Coordinates
		The layout is already in Roblox space (studs, Y up):
		Blender (x, y, z) -> Roblox (x, z, -y), yaw around Blender Z = yaw around Roblox Y.

	The code deliberately uses only the Lua 5.1 subset of Luau so that the
	placement maths can be unit-tested outside Roblox (see tests/).
]]

local WorldBuilder = {}

WorldBuilder.DEFAULTS = {
	templates = nil,            -- Instance that contains the imported meshes (required)
	layout = nil,               -- require(WorldLayout) (required)
	parent = nil,               -- defaults to workspace
	name = "Village",           -- name of the folder that receives the world
	origin = nil,               -- CFrame: where the village centre goes (default identity)
	includeGroups = nil,        -- optional set, e.g. { buildings = true, terrain = true }
	excludeGroups = nil,        -- optional set, e.g. { nature = true }
	createColliders = true,     -- invisible collision proxies for "proxy" assets
	createLights = true,        -- PointLights at lantern / window anchors
	lightShadows = false,
	replaceExisting = true,     -- destroy an earlier folder with the same name first
	sizeTolerance = 0.04,       -- warn if a template deviates more than 4 % from its design
	yieldEvery = 150,           -- instances between task.wait() calls (0 = never yield)
	applyLighting = false,      -- copy the suggested Lighting settings
	createSpawn = false,        -- add a SpawnLocation on the village square
	roadLift = 0,               -- extra height for the "roads" group (useful with voxel terrain)
	verbose = true,
}

-- ---------------------------------------------------------------- helpers
local function isPart(inst)
	return inst:IsA("BasePart")
end

local function collectParts(root)
	local parts = {}
	if isPart(root) then
		parts[#parts + 1] = root
	end
	local descendants = root:GetDescendants()
	for i = 1, #descendants do
		if isPart(descendants[i]) then
			parts[#parts + 1] = descendants[i]
		end
	end
	return parts
end

-- Axis aligned bounding box (world space) of a list of parts.
local function worldBounds(parts)
	local minX, minY, minZ = math.huge, math.huge, math.huge
	local maxX, maxY, maxZ = -math.huge, -math.huge, -math.huge
	for i = 1, #parts do
		local part = parts[i]
		local cf, half = part.CFrame, part.Size * 0.5
		local rx = cf:VectorToWorldSpace(Vector3.new(half.X, 0, 0))
		local ry = cf:VectorToWorldSpace(Vector3.new(0, half.Y, 0))
		local rz = cf:VectorToWorldSpace(Vector3.new(0, 0, half.Z))
		local ex = math.abs(rx.X) + math.abs(ry.X) + math.abs(rz.X)
		local ey = math.abs(rx.Y) + math.abs(ry.Y) + math.abs(rz.Y)
		local ez = math.abs(rx.Z) + math.abs(ry.Z) + math.abs(rz.Z)
		local p = cf.Position
		minX, maxX = math.min(minX, p.X - ex), math.max(maxX, p.X + ex)
		minY, maxY = math.min(minY, p.Y - ey), math.max(maxY, p.Y + ey)
		minZ, maxZ = math.min(minZ, p.Z - ez), math.max(maxZ, p.Z + ez)
	end
	return Vector3.new(minX, minY, minZ), Vector3.new(maxX, maxY, maxZ)
end

local function v3(t)
	return Vector3.new(t[1], t[2], t[3])
end

local function yawCFrame(position, yawDegrees)
	return CFrame.new(position) * CFrame.Angles(0, math.rad(yawDegrees), 0)
end

-- Rotation part of a CFrame (translation removed).
local function rotationOf(cf)
	return cf - cf.Position
end

-- Rescale a part around the origin of its model space.
local function scalePart(part, factor)
	local cf = part.CFrame
	part.Size = part.Size * factor
	part.CFrame = CFrame.new(cf.Position * factor) * rotationOf(cf)
end

local function trySet(instance, property, value)
	return pcall(function()
		instance[property] = value
	end)
end

WorldBuilder._worldBounds = worldBounds
WorldBuilder._collectParts = collectParts

-- ---------------------------------------------------------------- prototypes
local function newHelperPart(name, size, cframe)
	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.Transparency = 1
	part.CastShadow = false
	part.Size = size
	part.CFrame = cframe
	trySet(part, "TopSurface", Enum.SurfaceType.Smooth)
	trySet(part, "BottomSurface", Enum.SurfaceType.Smooth)
	return part
end

--[[
	Turns an imported template into a normalised prototype Model:
	  * design scale (1 unit = 1 stud)
	  * designed origin at the world origin, unrotated
	  * physics flags, collision proxies and light anchors applied
	Returns the prototype Model or nil plus a reason.
]]
local function buildPrototype(assetName, def, template, options, report)
	local source = template:Clone()
	local model = Instance.new("Model")
	model.Name = assetName
	source.Parent = model      -- a MeshPart or a Model with its own hierarchy
	local parts = collectParts(model)
	if #parts == 0 then
		model:Destroy()
		return nil, "template contains no parts"
	end

	local bmin, bmax = worldBounds(parts)
	local size = bmax - bmin
	local centre = (bmin + bmax) * 0.5
	local design = v3(def.size)
	local designCentre = v3(def.center)

	-- import scale k: imported = k * designed.  Use the largest axis, it is the most reliable.
	local k
	if design.X >= design.Y and design.X >= design.Z then
		k = size.X / design.X
	elseif design.Y >= design.Z then
		k = size.Y / design.Y
	else
		k = size.Z / design.Z
	end
	if not (k > 0) then
		model:Destroy()
		return nil, "template has zero size"
	end
	local worst = 0
	local axes = { "X", "Y", "Z" }
	for i = 1, 3 do
		local a = axes[i]
		if design[a] > 1 then
			worst = math.max(worst, math.abs(size[a] / (design[a] * k) - 1))
		end
	end
	if worst > options.sizeTolerance then
		report.warnings[#report.warnings + 1] = string.format(
			"%s: proportions differ by %.1f %% from the design (imported size %.2f, %.2f, %.2f; expected ratio %.2f, %.2f, %.2f). "
				.. "The mesh is probably rotated or was imported with a different up axis.",
			assetName, worst * 100, size.X, size.Y, size.Z, design.X, design.Y, design.Z)
	end

	-- move the designed origin to the world origin and remove the import scale
	local originWorld = centre - designCentre * k
	local inv = 1 / k
	for i = 1, #parts do
		local part = parts[i]
		local cf = part.CFrame
		part.Anchored = true
		part.Size = part.Size * inv
		part.CFrame = CFrame.new((cf.Position - originWorld) * inv) * rotationOf(cf)
	end

	-- physics / rendering flags
	local collision = def.collision
	local meshCollides = (collision == "mesh" or collision == "mesh_precise")
	if collision == "proxy" and not options.createColliders then
		meshCollides = true
	end
	for i = 1, #parts do
		local part = parts[i]
		part.CanCollide = meshCollides
		trySet(part, "CastShadow", def.castShadow ~= false)
		if def.transparency then
			part.Transparency = def.transparency
		end
		if collision == "none" then
			trySet(part, "CanTouch", false)
			trySet(part, "CanQuery", false)
		elseif collision == "mesh_precise" then
			local ok = trySet(part, "CollisionFidelity", Enum.CollisionFidelity.PreciseConvexDecomposition)
			if not ok then
				report.needsPreciseCollision[assetName] = true
			end
		end
	end

	if collision == "proxy" and options.createColliders and def.colliders then
		for i = 1, #def.colliders do
			local c = def.colliders[i]
			local part
			if c.shape == "cylinder" then
				-- Roblox cylinders lie along their X axis: stand it upright
				part = newHelperPart("Collider", Vector3.new(c.height, c.radius * 2, c.radius * 2),
					CFrame.new(v3(c.center)) * CFrame.Angles(0, 0, math.rad(90)))
				part.Shape = Enum.PartType.Cylinder
			else
				part = newHelperPart("Collider", v3(c.size), yawCFrame(v3(c.center), c.yaw_deg or 0))
			end
			part.CanCollide = true
			part.Parent = model
		end
	end

	if options.createLights and def.lights then
		for i = 1, #def.lights do
			local l = def.lights[i]
			local anchor = newHelperPart("LightAnchor", Vector3.new(0.2, 0.2, 0.2), CFrame.new(v3(l.position)))
			anchor.CanCollide = false
			trySet(anchor, "CanTouch", false)
			trySet(anchor, "CanQuery", false)
			local light = Instance.new("PointLight")
			light.Color = Color3.new(l.color[1], l.color[2], l.color[3])
			light.Brightness = l.brightness
			light.Range = l.range
			light.Shadows = options.lightShadows
			light.Parent = anchor
			anchor.Parent = model
		end
	end

	trySet(model, "PrimaryPart", parts[1])
	return model
end

-- Places a clone of a prototype.  All prototype parts are expressed relative
-- to the designed origin, so the final CFrame is target * scaled(relative).
local function placeInstance(prototype, target, scale)
	local clone = prototype:Clone()
	local parts = collectParts(clone)
	for i = 1, #parts do
		local part = parts[i]
		local rel = part.CFrame
		if scale ~= 1 then
			part.Size = part.Size * scale
		end
		part.CFrame = target * (CFrame.new(rel.Position * scale) * rotationOf(rel))
	end
	if scale ~= 1 then
		local descendants = clone:GetDescendants()
		for i = 1, #descendants do
			if descendants[i]:IsA("PointLight") then
				descendants[i].Range = descendants[i].Range * scale
			end
		end
	end
	return clone
end

-- ---------------------------------------------------------------- public API
local function withDefaults(options)
	local merged = {}
	for key, value in pairs(WorldBuilder.DEFAULTS) do
		merged[key] = value
	end
	for key, value in pairs(options or {}) do
		merged[key] = value
	end
	return merged
end

local function findTemplate(templates, assetName)
	if templates.Name == assetName then
		return templates
	end
	return templates:FindFirstChild(assetName, true)
end

--[[
	Builds the world.  Returns a report table:
		folder                 the created Folder
		placed                 number of placed instances
		skipped                number of instances skipped by group filters
		missing                { [assetName] = number of instances that could not be placed }
		warnings               list of strings
		needsPreciseCollision  { [assetName] = true } - set CollisionFidelity by hand for these
]]
function WorldBuilder.build(options)
	options = withDefaults(options)
	local layout = options.layout
	assert(layout and layout.instances and layout.assets, "VillageWorldBuilder: options.layout is missing")
	assert(options.templates, "VillageWorldBuilder: options.templates is missing")
	local parent = options.parent or workspace
	local origin = options.origin or CFrame.new(0, 0, 0)

	local report = { placed = 0, skipped = 0, missing = {}, warnings = {}, needsPreciseCollision = {} }

	if options.replaceExisting then
		local old = parent:FindFirstChild(options.name)
		if old then
			old:Destroy()
		end
	end
	local root = Instance.new("Folder")
	root.Name = options.name
	local prototypeFolder = Instance.new("Folder")
	prototypeFolder.Name = "_Prototypes"

	local groupFolders = {}
	local function groupFolder(groupName)
		if not groupFolders[groupName] then
			local folder = Instance.new("Folder")
			folder.Name = groupName
			folder.Parent = root
			groupFolders[groupName] = folder
		end
		return groupFolders[groupName]
	end

	local prototypes = {}       -- assetName -> Model | false
	local function prototypeFor(assetName)
		local cached = prototypes[assetName]
		if cached ~= nil then
			return cached
		end
		local def = layout.assets[assetName]
		local template = findTemplate(options.templates, assetName)
		local proto = false
		if not def then
			report.warnings[#report.warnings + 1] = assetName .. ": no asset definition in the layout"
		elseif not template then
			report.warnings[#report.warnings + 1] = assetName .. ": template not found in " .. options.templates.Name
		else
			local built, reason = buildPrototype(assetName, def, template, options, report)
			if built then
				built.Parent = prototypeFolder
				proto = built
			else
				report.warnings[#report.warnings + 1] = assetName .. ": " .. tostring(reason)
			end
		end
		prototypes[assetName] = proto
		return proto
	end

	local instances = layout.instances
	for index = 1, #instances do
		local row = instances[index]
		local assetName = layout.assetNames[row[1]]
		local groupName = layout.groupNames[row[7]]
		local wanted = true
		if options.includeGroups and not options.includeGroups[groupName] then
			wanted = false
		end
		if options.excludeGroups and options.excludeGroups[groupName] then
			wanted = false
		end
		if not wanted then
			report.skipped = report.skipped + 1
		else
			local proto = prototypeFor(assetName)
			if proto then
				local y = row[3]
				if groupName == "roads" then
					y = y + options.roadLift
				end
				local target = origin * yawCFrame(Vector3.new(row[2], y, row[4]), row[5])
				local clone = placeInstance(proto, target, row[6])
				clone.Name = row[8] or assetName
				pcall(function()
					clone:SetAttribute("AssetId", assetName)
					clone:SetAttribute("LayoutIndex", index)
				end)
				clone.Parent = groupFolder(groupName)
				report.placed = report.placed + 1
			else
				report.missing[assetName] = (report.missing[assetName] or 0) + 1
			end
		end
		if options.yieldEvery > 0 and index % options.yieldEvery == 0 and task and task.wait then
			task.wait()
		end
	end

	prototypeFolder:Destroy()

	if options.createSpawn and layout.spawn then
		local spawn = Instance.new("SpawnLocation")
		spawn.Name = "VillageSpawn"
		spawn.Anchored = true
		spawn.Size = Vector3.new(8, 1, 8)
		spawn.Transparency = 1
		spawn.CanCollide = false
		spawn.CFrame = origin * CFrame.new(v3(layout.spawn))
		spawn.Parent = root
	end

	if options.applyLighting and layout.lighting then
		WorldBuilder.applyLighting(layout.lighting)
	end

	root.Parent = parent
	report.folder = root

	if options.verbose then
		local missingKinds, missingCount = 0, 0
		for _, n in pairs(report.missing) do
			missingKinds = missingKinds + 1
			missingCount = missingCount + n
		end
		print(string.format("[VillageWorldBuilder] placed %d instances, skipped %d, missing %d (%d asset types), %d warnings",
			report.placed, report.skipped, missingCount, missingKinds, #report.warnings))
		for i = 1, math.min(#report.warnings, 40) do
			warn("[VillageWorldBuilder] " .. report.warnings[i])
		end
		local precise = {}
		for name in pairs(report.needsPreciseCollision) do
			precise[#precise + 1] = name
		end
		if #precise > 0 then
			table.sort(precise)
			warn("[VillageWorldBuilder] Set CollisionFidelity = PreciseConvexDecomposition by hand for: "
				.. table.concat(precise, ", "))
		end
	end
	return report
end

-- Copies the suggested look into the Lighting service.
function WorldBuilder.applyLighting(settings)
	local lighting = game:GetService("Lighting")
	local function c3(t)
		return Color3.new(t[1], t[2], t[3])
	end
	trySet(lighting, "ClockTime", settings.clock_time)
	trySet(lighting, "GeographicLatitude", settings.geographic_latitude)
	trySet(lighting, "Brightness", settings.brightness)
	trySet(lighting, "Ambient", c3(settings.ambient))
	trySet(lighting, "OutdoorAmbient", c3(settings.outdoor_ambient))
	trySet(lighting, "ColorShift_Top", c3(settings.color_shift_top))
	trySet(lighting, "FogColor", c3(settings.fog_color))
	trySet(lighting, "FogStart", settings.fog_start)
	trySet(lighting, "FogEnd", settings.fog_end)
end

-- Lists which asset ids of the layout are (not) present in `templates`.
function WorldBuilder.checkTemplates(templates, layout)
	local found, missing = {}, {}
	for i = 1, #layout.assetNames do
		local name = layout.assetNames[i]
		if findTemplate(templates, name) then
			found[#found + 1] = name
		else
			missing[#missing + 1] = name
		end
	end
	return found, missing
end

return WorldBuilder
