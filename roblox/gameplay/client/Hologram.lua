-- ROBLOX CLIENT: the white holograms of the build mode and the grid on the workshop floor.
-- A hologram is the real model of the part (the same model the server builds), drawn in bright
-- white with a glowing outline, placed by the same rule as the built part (PlacementPose) - so it
-- shows exactly how the part will sit.  Red means: this place is taken.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("ArcaneShared")
local Config = require(Shared.Config)
local Machines = require(Shared.Machines)
local Grid = require(Shared.GridMath)
local Pose = require(Shared.PlacementPose)
local Models = require(Shared.WorkshopModels)
local BeltPath = require(Shared.BeltPath)

local H = {}
H.WHITE = Color3.fromRGB(242, 247, 255)
H.RED = Color3.fromRGB(255, 104, 92)
local templates                          -- ReplicatedStorage.ArcaneMachineModels (copied there by the server)

local function template(id)
	templates = templates or ReplicatedStorage:FindFirstChild("ArcaneMachineModels")
	local t = templates and templates:FindFirstChild(Machines[id].modelAssetId, true)
	return (t and t:IsA("BasePart")) and t or nil
end

local function quiet(part)
	part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch, part.CastShadow = true, false, false, false, false
end

-- A group of hologram parts that glow together: a Model with one Highlight.
function H.group(name, color)
	local model = Instance.new("Model")
	model.Name = name
	-- a light fill only: a strong fill would flatten the model into a white blob; the bright
	-- outline and the shaded white model keep its shape readable
	local glow = Instance.new("Highlight")
	glow.FillColor, glow.FillTransparency = color, 0.82
	glow.OutlineColor, glow.OutlineTransparency = color, 0
	glow.DepthMode = Enum.HighlightDepthMode.Occluded
	glow.Parent = model
	model.Parent = workspace
	return model
end

function H.tint(group, color)
	local glow = group:FindFirstChildOfClass("Highlight")
	if glow then glow.FillColor, glow.OutlineColor = color, color end
	for _, d in ipairs(group:GetDescendants()) do
		if d:IsA("BasePart") then d.Color = color end
	end
end

-- The hologram body of a part: the real model in white, or a box of its footprint without models.
-- Returns { part, template, id }.
function H.body(id, color)
	local t = template(id)
	local part
	if t then
		part = t:Clone()
		if part:IsA("MeshPart") then part.TextureID = "" end
		for _, d in ipairs(part:GetChildren()) do d:Destroy() end
	else
		local def = Machines[id]
		part = Instance.new("Part")
		part.Size = Vector3.new(def.w * Config.cellSize - 0.2, 2, def.d * Config.cellSize - 0.2)
	end
	quiet(part)
	part.Name = "Hologram"
	part.Material, part.Color, part.Transparency = Enum.Material.SmoothPlastic, color or H.WHITE, 0.15
	return { part = part, template = t, id = id }
end

-- room: { x, y, z } (origin, from the snapshot) and cells: side length of the workshop in cells
function H.cellCenter(room, cells)
	local cs, half = Config.cellSize, cells * Config.cellSize / 2
	return function(floor, x, z)
		return Vector3.new(room.x + x * cs - half + cs / 2, room.y + (floor - 1) * Config.floorHeight, room.z + z * cs - half + cs / 2)
	end
end

-- Puts a hologram body where entity e = { gx, gz, floor, rot } of its part would sit.
function H.place(body, e, cellCenter)
	local def = Machines[body.id]
	local base, height = Pose.base(def, e, cellCenter)
	if body.template then
		Pose.place(body.part, body.template, def, e, base, height, Models)
	else
		local w, d = Grid.size(def, e.rot)
		body.part.Size = Vector3.new(w * Config.cellSize - 0.2, math.min(height, 2), d * Config.cellSize - 0.2)
		body.part.CFrame = CFrame.new(base.X, base.Y - height / 2 + body.part.Size.Y / 2, base.Z)
	end
end

-- Flat plate on the cells a part will take.
function H.plate(color)
	local p = Instance.new("Part")
	p.Name = "Footprint"
	quiet(p)
	p.Material, p.Color, p.Transparency = Enum.Material.SmoothPlastic, color or H.WHITE, 0.55
	return p
end

function H.placePlate(plate, id, e, cellCenter)
	local def = Machines[id]
	local w, d = Grid.size(def, e.rot)
	local cs = Config.cellSize
	local c = cellCenter(e.floor, e.gx, e.gz)
	plate.Size = Vector3.new(w * cs - 0.1, 0.06, d * cs - 0.1)
	plate.CFrame = CFrame.new(c.X + (w - 1) * cs / 2, c.Y + 0.04, c.Z + (d - 1) * cs / 2)
end

-- Grid on one floor of the workshop: a line on every cell border, the reserved cells (entrance,
-- staircase) shaded red.
function H.grid(room, cells, floor)
	local folder = Instance.new("Folder")
	folder.Name = "ArcaneBuildGrid"
	local cs, half = Config.cellSize, cells * Config.cellSize / 2
	local y = room.y + (floor - 1) * Config.floorHeight + 0.03
	local function line(size, pos)
		local p = Instance.new("Part")
		quiet(p)
		p.Material, p.Color, p.Transparency = Enum.Material.SmoothPlastic, H.WHITE, 0.72
		p.Size, p.Position = size, pos
		p.Parent = folder
	end
	for i = 0, cells do
		local o = -half + i * cs
		line(Vector3.new(0.06, 0.02, cells * cs), Vector3.new(room.x + o, y, room.z))
		line(Vector3.new(cells * cs, 0.02, 0.06), Vector3.new(room.x, y, room.z + o))
	end
	for x = 0, cells - 1 do
		for z = 0, cells - 1 do
			if BeltPath.reserved(cells, Config.door.width, Config.door.depth, floor, x, z) then
				local p = Instance.new("Part")
				quiet(p)
				p.Material, p.Color, p.Transparency = Enum.Material.SmoothPlastic, H.RED, 0.8
				p.Size = Vector3.new(cs - 0.1, 0.02, cs - 0.1)
				p.Position = Vector3.new(room.x - half + (x + 0.5) * cs, y, room.z - half + (z + 0.5) * cs)
				p.Parent = folder
			end
		end
	end
	folder.Parent = workspace
	return folder
end

return H
