-- ROBLOX ADAPTER (UNVERIFIED_IN_STUDIO): builds the walkable workshop interiors and the visible
-- representation of every placed entity.  All game rules live in the pure services; this module only
-- mirrors server state into Instances.
local D = require(script.Parent.Data)
local Config, Machines, Grid = D.Config, D.Machines, D.GridMath
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("ArcaneShared")
local Architecture = require(Shared.WorkshopArchitecture)
local Models = require(Shared.WorkshopModels)
local WW = {}
WW.__index = WW

local COLORS = {
	machine = Color3.fromRGB(134, 87, 58), storage = Color3.fromRGB(181, 133, 86), transport = Color3.fromRGB(110, 106, 102),
	pipe = Color3.fromRGB(95, 160, 138),
}
local STATE_TEXT = { Running = "läuft", WaitingForInputs = "wartet auf Zutaten", OutputBlocked = "Ausgang voll",
	NoFuel = "kein Brennstoff", Paused = "pausiert", InvalidRecipe = "kein Rezept" }

local function part(props, parent)
	local p = Instance.new("Part")
	p.Anchored = true
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	for k, v in pairs(props) do p[k] = v end
	p.Parent = parent
	return p
end

-- templates: optional Folder with imported machine meshes named after Machines[id].modelAssetId
function WW.new(parent, templates)
	local self = setmetatable({ rooms = {}, slots = {}, templates = templates }, WW)
	self.root = Instance.new("Folder")
	self.root.Name = "ArcaneWorkshops"
	self.root.Parent = parent
	return self
end

-- Interiors live far away from the village so they are never visible from it.
function WW:slotOrigin(slot)
	return Vector3.new(6000 + (slot % 4) * 600, 800, 6000 + math.floor(slot / 4) * 600)
end

function WW:cellCenter(room, floor, x, z)
	local half = room.cells * Config.cellSize / 2
	return room.origin + Vector3.new(x * Config.cellSize - half + 1, (floor - 1) * Config.floorHeight, z * Config.cellSize - half + 1)
end

local ARCHITECTURE_COLORS = {
	wood_dark = "5B3A26", wood_mid = "86573A", wood_pale = "D2AE7C", wood_red = "7A3B2A",
	plaster_cream = "EBDDBE", plaster_sage = "B9C4A0", stone_dark = "6E6A66", stone_warm = "B4A58C", stone_light = "C9C2B2",
	iron = "3E4046", brass = "C99A3C", glass_lit = "FFD27A", glass_light = "7FB2C9",
	leaf_dark = "3F7D3A", leaf_teal = "3F8A6A", roof_purple = "6F4E7C",
}

local function buildShell(room)
	if room.shell then room.shell:Destroy() end
	local shell = Instance.new("Folder")
	shell.Name = "Shell"
	local size = room.cells * Config.cellSize
	local boxes, lights = Architecture.build(size, room.floors, Config.floorHeight)
	for _, spec in ipairs(boxes) do
		local item = part({
			Name = spec.name, Size = Vector3.new(table.unpack(spec.size)),
			CFrame = CFrame.new(room.origin + Vector3.new(table.unpack(spec.position)))
				* CFrame.Angles(0, 0, math.rad(spec.roll or 0)),
			Color = Color3.fromHex(ARCHITECTURE_COLORS[spec.color]),
			Material = (spec.name == "Lamp") and Enum.Material.Neon or Enum.Material.SmoothPlastic,
			CanCollide = spec.collides, CanQuery = spec.collides,
		}, shell)
		if spec.floor then item:SetAttribute("ArcaneFloor", spec.floor) end
		if spec.name == "ExitDoor" then
			local prompt = Instance.new("ProximityPrompt")
			prompt.ActionText, prompt.ObjectText, prompt.HoldDuration, prompt.MaxActivationDistance = "Verlassen", "Werkstatt", 0.2, 12
			prompt.Parent = item
			room.exitPrompt = prompt
		end
	end
	for _, spec in ipairs(lights) do
		local anchor = part({
			Name = "LightAnchor", Size = Vector3.new(0.2, 0.2, 0.2),
			Position = room.origin + Vector3.new(table.unpack(spec.position)),
			Transparency = 1, CanCollide = false, CanQuery = false, CastShadow = false,
		}, shell)
		local light = Instance.new("PointLight")
		light.Range, light.Brightness, light.Color = spec.range, spec.strength, Color3.fromRGB(255, 218, 164)
		light.Parent = anchor
	end
	shell.Parent = room.folder
	room.shell = shell
end

function WW:ensureRoom(ownerId, cells, floors)
	local room = self.rooms[ownerId]
	if not room then
		local slot = 0
		while self.slots[slot] do slot = slot + 1 end
		self.slots[slot] = ownerId
		room = { owner = ownerId, slot = slot, origin = self:slotOrigin(slot), entities = {}, cells = 0, floors = 0 }
		room.folder = Instance.new("Folder")
		room.folder.Name = "Workshop_" .. ownerId
		room.folder.Parent = self.root
		room.entityFolder = Instance.new("Folder")
		room.entityFolder.Name = "Entities"
		room.entityFolder.Parent = room.folder
		self.rooms[ownerId] = room
	end
	if room.cells ~= cells or room.floors ~= floors then
		room.cells, room.floors = cells, floors
		buildShell(room)
		room.version = nil
	end
	return room
end

function WW:spawnCFrame(room)
	local size = room.cells * Config.cellSize
	return CFrame.new(room.origin + Vector3.new(0, 4, -size / 2 + 5)) * CFrame.Angles(0, math.rad(180), 0)
end

local function entityModel(self, room, e)
	local def = Machines[e.machine]
	local w, d = Grid.size(def, e.rot)
	local cs = Config.cellSize
	local height = (def.category == "transport") and 0.8 or (def.kind == "shelf") and 6 or 4
	if def.layer == "pipe" then height = 0.5 end
	local base = WW.cellCenter(self, room, e.floor, e.gx, e.gz) + Vector3.new((w - 1) * cs / 2, height / 2 + (def.layer == "pipe" and 0.05 or 0), (d - 1) * cs / 2)
	local template = self.templates and self.templates:FindFirstChild(def.modelAssetId, true)
	local body
	if template and template:IsA("BasePart") then
		body = template:Clone()
		body.Anchored = true
		if template:GetAttribute("PublishedMachineLibrary") then
			-- undo whatever scale the importer applied: the mesh was designed to fill its footprint
			local k = math.max(body.Size.X, body.Size.Z) / (math.max(def.w, def.d) * cs)
			if k > 1.05 or k < 0.6 then body.Size = body.Size / k end
			-- keep the template's own rotation (the asset loader corrects the import orientation there)
			-- and stand the mesh on the floor: a MeshPart's CFrame is the centre of its bounding box
			local floorY = base.Y - height / 2
			body.CFrame = CFrame.new(base.X, floorY + body.Size.Y / 2, base.Z) * CFrame.Angles(0, math.rad(-90 * e.rot), 0)
				* (template.CFrame - template.CFrame.Position)
		else
			local pivot = CFrame.new(base - Vector3.new(0, height / 2, 0))
				* CFrame.Angles(0, math.rad(-90 * e.rot), 0)
			local mesh = Models[def.modelAssetId]
			if mesh then
				-- Imported MeshParts are centred on the geometry bounds. Recover the
				-- original grid-centred, ground-level pivot before applying rotation.
				local offset = Vector3.new(table.unpack(mesh.center))
				body.Size = Vector3.new(table.unpack(mesh.size))
				body.CFrame = pivot * CFrame.new(offset)
				for _, spec in ipairs(mesh.lights or {}) do
					local attachment = Instance.new("Attachment")
					attachment.Position = Vector3.new(table.unpack(spec.position)) - offset
					attachment.Parent = body
					local light = Instance.new("PointLight")
					light.Color = Color3.new(table.unpack(spec.color))
					light.Brightness, light.Range = spec.brightness, spec.range
					light.Parent = attachment
				end
			else
				body.CFrame = pivot
			end
		end
	else
		body = part({ Size = Vector3.new(w * cs - 0.2, height, d * cs - 0.2), Position = base,
			Color = (def.layer == "pipe") and COLORS.pipe or COLORS[def.category] or COLORS.machine,
			Material = (def.category == "transport") and Enum.Material.Metal or Enum.Material.Wood }, nil)
	end
	body.Name = e.uid
	body:SetAttribute("ArcaneUid", e.uid)
	body:SetAttribute("ArcaneMachine", e.machine)
	if def.category ~= "transport" then
		local gui = Instance.new("BillboardGui")
		gui.Name, gui.Size, gui.StudsOffset, gui.AlwaysOnTop, gui.MaxDistance = "Label", UDim2.new(0, 170, 0, 44), Vector3.new(0, height / 2 + 2.2, 0), false, 60
		local text = Instance.new("TextLabel")
		text.Name, text.Size, text.BackgroundTransparency, text.TextScaled = "Text", UDim2.new(1, 0, 1, 0), 0.25, true
		text.BackgroundColor3, text.TextColor3, text.Font = Color3.fromRGB(35, 32, 31), Color3.fromRGB(247, 244, 236), Enum.Font.GothamMedium
		text.Parent = gui
		gui.Parent = body
		local prompt = Instance.new("ProximityPrompt")
		prompt.ActionText, prompt.ObjectText, prompt.MaxActivationDistance, prompt.RequiresLineOfSight = "Öffnen", def.name, 9, false
		prompt.Parent = body
	else
		-- direction marker and item token for belts
		local arrow = part({ Name = "Arrow", Size = Vector3.new(0.5, 0.2, 1.2), Color = Color3.fromRGB(201, 154, 60), CanCollide = false,
			CFrame = CFrame.new(base + Vector3.new(0, height / 2 + 0.1, 0)) * CFrame.Angles(0, math.rad(-90 * e.rot), 0) }, body)
		arrow.Name = "Arrow"
		local token = part({ Name = "Token", Size = Vector3.new(0.9, 0.9, 0.9), Position = base + Vector3.new(0, height / 2 + 0.6, 0),
			Color = Color3.fromRGB(95, 163, 67), Transparency = 1, CanCollide = false, Shape = Enum.PartType.Ball }, body)
		token.Name = "Token"
	end
	body.Parent = room.entityFolder
	return body
end

-- Mirrors a workshop view (Game.workshopView) into Instances. Cheap when nothing changed.
function WW:sync(view, displayNames)
	local room = self:ensureRoom(view.owner, view.cells, view.floors)
	if room.version ~= view.version then
		local seen = {}
		for _, e in ipairs(view.entities) do
			seen[e.uid] = true
			local cur = room.entities[e.uid]
			local sig = e.machine .. ":" .. e.gx .. ":" .. e.gz .. ":" .. e.floor .. ":" .. e.rot
			if not cur or cur.sig ~= sig then
				if cur then cur.body:Destroy() end
				room.entities[e.uid] = { sig = sig, body = entityModel(self, room, e) }
			end
		end
		for uid, cur in pairs(room.entities) do
			if not seen[uid] then
				cur.body:Destroy()
				room.entities[uid] = nil
			end
		end
		room.version = view.version
	end
	for _, e in ipairs(view.entities) do
		local cur = room.entities[e.uid]
		if cur then
			local label = cur.body:FindFirstChild("Label")
			if label then
				local def = Machines[e.machine]
				local line = def.name
				if def.kind == "machine" or def.kind == "pump" then
					line = line .. "\n" .. (STATE_TEXT[e.state] or "bereit")
					if e.job then line = line .. string.format(" %d%%", math.floor((1 - e.job.remaining / e.job.total) * 100)) end
				else
					local n = 0
					for _, c in pairs(e.inv) do n = n + c end
					for _, c in pairs(e.fluids) do n = n + math.floor(c / 1000) end
					line = line .. "\n" .. n .. " Stück"
				end
				label.Text.Text = line
			end
			local token = cur.body:FindFirstChild("Token")
			if token then token.Transparency = e.item and 0 or 1 end
		end
	end
	return room
end

function WW:removeRoom(ownerId)
	local room = self.rooms[ownerId]
	if not room then return end
	self.slots[room.slot] = nil
	room.folder:Destroy()
	self.rooms[ownerId] = nil
end
return WW
