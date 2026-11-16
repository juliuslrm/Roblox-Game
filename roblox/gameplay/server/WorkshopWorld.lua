-- ROBLOX ADAPTER (UNVERIFIED_IN_STUDIO): builds the walkable workshop interiors and the visible
-- representation of every placed entity.  All game rules live in the pure services; this module only
-- mirrors server state into Instances.
local D = require(script.Parent.Data)
local Config, Machines, Grid = D.Config, D.Machines, D.GridMath
local WW = {}
WW.__index = WW

local COLORS = {
	machine = Color3.fromRGB(134, 87, 58), storage = Color3.fromRGB(181, 133, 86), transport = Color3.fromRGB(110, 106, 102),
	floor = Color3.fromRGB(210, 174, 124), wall = Color3.fromRGB(235, 221, 190), beam = Color3.fromRGB(91, 58, 38),
	pipe = Color3.fromRGB(95, 160, 138), door = Color3.fromRGB(122, 59, 42),
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

local function buildShell(room)
	if room.shell then room.shell:Destroy() end
	local shell = Instance.new("Folder")
	shell.Name = "Shell"
	local size = room.cells * Config.cellSize
	local o, h = room.origin, Config.floorHeight
	for floor = 1, room.floors do
		local y = (floor - 1) * h
		local f = part({ Name = "Floor" .. floor, Size = Vector3.new(size, 1, size), Position = o + Vector3.new(0, y - 0.5, 0),
			Color = COLORS.floor, Material = Enum.Material.WoodPlanks }, shell)
		f:SetAttribute("ArcaneFloor", floor)
		for _, w in ipairs({ { 0, -size / 2, size, 1 }, { 0, size / 2, size, 1 }, { -size / 2, 0, 1, size }, { size / 2, 0, 1, size } }) do
			part({ Name = "Wall", Size = Vector3.new(w[3], h, w[4]), Position = o + Vector3.new(w[1], y + h / 2, w[2]),
				Color = COLORS.wall, Material = Enum.Material.Plaster }, shell)
		end
		for _, c in ipairs({ { -1, -1 }, { 1, -1 }, { 1, 1 }, { -1, 1 } }) do
			part({ Name = "Post", Size = Vector3.new(1.4, h, 1.4), Position = o + Vector3.new(c[1] * size / 2, y + h / 2, c[2] * size / 2),
				Color = COLORS.beam, Material = Enum.Material.Wood }, shell)
		end
		local lamp = part({ Name = "Lamp", Size = Vector3.new(1, 1, 1), Position = o + Vector3.new(0, y + h - 2, 0),
			Color = Color3.fromRGB(255, 210, 122), Material = Enum.Material.Neon, CanCollide = false }, shell)
		local light = Instance.new("PointLight")
		light.Range, light.Brightness, light.Color = 60, 1.4, Color3.fromRGB(255, 220, 170)
		light.Parent = lamp
	end
	-- staircase in the reserved back-left corner (rows z >= cells - 4, x < 3)
	if room.floors > 1 then
		for floor = 1, room.floors - 1 do
			local steps = 12
			for i = 1, steps do
				part({ Name = "Step", Size = Vector3.new(5, 1, 8 / steps + 0.2),
					Position = o + Vector3.new(-size / 2 + 3, (floor - 1) * h + i * (h / steps) - 0.5, size / 2 - 8 + i * (8 / steps) - 0.3),
					Color = COLORS.beam, Material = Enum.Material.Wood }, shell)
			end
		end
	end
	-- exit door at the middle of the front wall (z = -size/2 is the entrance side: cells z = 0)
	local door = part({ Name = "ExitDoor", Size = Vector3.new(6, 9, 0.6), Position = o + Vector3.new(0, 4.5, -size / 2 + 0.9),
		Color = COLORS.door, Material = Enum.Material.Wood }, shell)
	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText, prompt.ObjectText, prompt.HoldDuration, prompt.MaxActivationDistance = "Verlassen", "Werkstatt", 0.2, 12
	prompt.Parent = door
	room.exitPrompt = prompt
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
		-- undo whatever scale the importer applied: the mesh was designed to fill its footprint
		local k = math.max(body.Size.X, body.Size.Z) / (math.max(def.w, def.d) * cs)
		if k > 1.05 or k < 0.6 then body.Size = body.Size / k end
		-- keep the template's own rotation (the asset loader corrects the import orientation there)
		-- and stand the mesh on the floor: a MeshPart's CFrame is the centre of its bounding box
		local floorY = base.Y - height / 2
		body.CFrame = CFrame.new(base.X, floorY + body.Size.Y / 2, base.Z) * CFrame.Angles(0, math.rad(-90 * e.rot), 0)
			* (template.CFrame - template.CFrame.Position)
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
