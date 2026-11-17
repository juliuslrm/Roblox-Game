-- ROBLOX ADAPTER: builds the walkable workshops (open buildings on plots in the village) and the visible
-- representation of every placed entity.  All game rules live in the pure services; this module only
-- mirrors server state into Instances.
local D = require(script.Parent.Data)
local Config, Machines, Grid = D.Config, D.Machines, D.GridMath
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("ArcaneShared")
local Architecture = require(Shared.WorkshopArchitecture)
local Models = require(Shared.WorkshopModels)
local Ports = require(Shared.MachinePorts)
local GoodsMotion = require(Shared.GoodsMotion)
local WW = {}
WW.__index = WW

local CARRIER = { belt = true, splitter = true, merger = true, sorter = true, lift = true, gate = true }
local PERIOD = { belt = "beltSecondsPerItem", lift = "liftSecondsPerItem", gate = "gateSecondsPerItem" }

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
-- plots: optional list of world positions (Vector3, ground level) of the building plots in the
--   village.  With plots the workshops are open buildings that players simply walk into; without
--   them (no level plan) they are closed interiors far away, entered by teleport as before.
function WW.new(parent, templates, plots, plotHalf)
	local self = setmetatable({ rooms = {}, slots = {}, templates = templates, plots = plots, plotHalf = plotHalf or 42 }, WW)
	if plots and #plots == 0 then self.plots = nil end
	self.root = Instance.new("Folder")
	self.root.Name = "ArcaneWorkshops"
	self.root.Parent = parent
	return self
end

-- Interiors live far away from the village so they are never visible from it.
function WW:slotOrigin(slot)
	if self.plots then
		-- floor surface a little above the levelled ground (it varies by up to 0.7 studs)
		return self.plots[slot + 1] + Vector3.new(0, WW.FLOOR_LIFT, 0)
	end
	return Vector3.new(6000 + (slot % 4) * 600, 800, 6000 + math.floor(slot / 4) * 600)
end

function WW:cellCenter(room, floor, x, z)
	local half = room.cells * Config.cellSize / 2
	return room.origin + Vector3.new(x * Config.cellSize - half + 1, (floor - 1) * Config.floorHeight, z * Config.cellSize - half + 1)
end

WW.FLOOR_LIFT = 0.6

-- Is a world position on the plot of a room (inside the building or on its yard)?  Used by the
-- server to decide in whose workshop a character stands.
function WW:ownerAt(position)
	if not self.plots then return nil end
	for ownerId, room in pairs(self.rooms) do
		local half = room.cells * Config.cellSize / 2 + 1.5
		local d = position - room.origin
		if math.abs(d.X) <= half and math.abs(d.Z) <= half and d.Y > -4 and d.Y < room.floors * Config.floorHeight + 8 then
			return ownerId
		end
	end
	return nil
end

local ARCHITECTURE_COLORS = {
	wood_dark = "5B3A26", wood_mid = "86573A", wood_pale = "D2AE7C", wood_red = "7A3B2A",
	plaster_cream = "EBDDBE", plaster_sage = "B9C4A0", stone_dark = "6E6A66", stone_warm = "B4A58C", stone_light = "C9C2B2",
	iron = "3E4046", brass = "C99A3C", glass_lit = "FFD27A", glass_light = "7FB2C9",
	leaf_dark = "3F7D3A", leaf_teal = "3F8A6A", roof_purple = "6F4E7C",
}

-- Yard of an open workshop: marks the whole plot the building may grow into.
local function buildYard(room, shell, plotHalf, label)
	local stone, wood = Color3.fromHex(ARCHITECTURE_COLORS.stone_light), Color3.fromHex(ARCHITECTURE_COLORS.wood_dark)
	local ground = room.origin - Vector3.new(0, WW.FLOOR_LIFT, 0)
	local edge = plotHalf - 1
	for s = -1, 1, 2 do
		-- flat kerb stones along the plot boundary; low enough to walk over
		part({ Name = "PlotKerb", Size = Vector3.new(edge * 2 + 1, 0.5, 1), Position = ground + Vector3.new(0, 0.05, s * edge),
			Color = stone, Material = Enum.Material.Slate, CanCollide = false, CanQuery = false }, shell)
		part({ Name = "PlotKerb", Size = Vector3.new(1, 0.5, edge * 2 + 1), Position = ground + Vector3.new(s * edge, 0.05, 0),
			Color = stone, Material = Enum.Material.Slate, CanCollide = false, CanQuery = false }, shell)
		for t = -1, 1, 2 do
			part({ Name = "PlotPost", Size = Vector3.new(0.9, 4, 0.9), Position = ground + Vector3.new(s * edge, 2, t * edge),
				Color = wood, Material = Enum.Material.Wood, CanCollide = true }, shell)
		end
	end
	-- name board at every opening of the plot
	local half = room.cells * Config.cellSize / 2
	for _, dir in ipairs({ Vector3.new(1, 0, 0), Vector3.new(-1, 0, 0), Vector3.new(0, 0, 1), Vector3.new(0, 0, -1) }) do
		local side = Vector3.new(-dir.Z, 0, dir.X)
		local at = room.origin + dir * (half + 1.5) + side * (Architecture.OPENING / 2 + 1.6)
		part({ Name = "SignPost", Size = Vector3.new(0.5, 6, 0.5), Position = at + Vector3.new(0, 3 - WW.FLOOR_LIFT, 0),
			Color = wood, Material = Enum.Material.Wood, CanCollide = false, CanQuery = false }, shell)
		local board = part({ Name = "SignBoard", Size = Vector3.new(5, 2, 0.3),
			CFrame = CFrame.lookAt(at + Vector3.new(0, 6.2 - WW.FLOOR_LIFT, 0), at + Vector3.new(0, 6.2 - WW.FLOOR_LIFT, 0) + dir),
			Color = Color3.fromHex(ARCHITECTURE_COLORS.wood_pale), Material = Enum.Material.Wood, CanCollide = false, CanQuery = false }, shell)
		for _, face in ipairs({ Enum.NormalId.Front, Enum.NormalId.Back }) do
			local gui = Instance.new("SurfaceGui")
			gui.Face, gui.PixelsPerStud = face, 40
			local text = Instance.new("TextLabel")
			text.Size, text.BackgroundTransparency, text.TextScaled = UDim2.new(1, 0, 1, 0), 1, true
			text.Font, text.TextColor3, text.Text = Enum.Font.GothamBold, Color3.fromRGB(60, 40, 28), label
			text.Parent = gui
			gui.Parent = board
		end
	end
end

local function buildShell(self, room)
	if room.shell then room.shell:Destroy() end
	local shell = Instance.new("Folder")
	shell.Name = "Shell"
	local size = room.cells * Config.cellSize
	local boxes, lights = Architecture.build(size, room.floors, Config.floorHeight, self.plots ~= nil)
	if self.plots then buildYard(room, shell, self.plotHalf, room.label or "Werkstatt") end
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

function WW:ensureRoom(ownerId, cells, floors, label)
	local room = self.rooms[ownerId]
	if not room then
		local slot = 0
		while self.slots[slot] do slot = slot + 1 end
		if self.plots and slot >= #self.plots then return nil end -- every plot is taken
		self.slots[slot] = ownerId
		room = { owner = ownerId, slot = slot, origin = self:slotOrigin(slot), entities = {}, cells = 0, floors = 0, label = label }
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
		buildShell(self, room)
		room.version = nil
	end
	return room
end

function WW:spawnCFrame(room)
	local size = room.cells * Config.cellSize
	return CFrame.new(room.origin + Vector3.new(0, 4, -size / 2 + 5)) * CFrame.Angles(0, math.rad(180), 0)
end

-- Flat arrow lying on a surface, its tip at `tip`, pointing along the unit vector `dir`.
local function flatArrow(parent, name, tip, dir, color, length, hidden)
	local props = { Name = name, Color = color, Material = Enum.Material.SmoothPlastic, CanCollide = false, CanQuery = false,
		CanTouch = false, CastShadow = false, Transparency = hidden and 1 or 0 }
	local function piece(size, cframe)
		local q = part(props, parent)
		q.Size, q.CFrame = size, cframe
		if hidden then q:SetAttribute("ArcanePortMark", true) end
		return q
	end
	local look = CFrame.lookAt(tip, tip + dir)
	local shaft = piece(Vector3.new(0.28, 0.12, length - 0.25), look * CFrame.new(0, 0, (length - 0.25) / 2 + 0.2))
	for _, sign in ipairs({ -1, 1 }) do
		piece(Vector3.new(0.28, 0.12, 0.72), look * CFrame.Angles(0, sign * math.rad(140), 0) * CFrame.new(0, 0, -0.3))
	end
	return shaft
end

-- Marks at the connections of a production machine: inlet, outlet and pipe connections.  They are
-- invisible on the server; the client shows them while building or while the machine window is
-- open (attribute ArcanePortMark).
local function portMarks(self, room, e, def, body)
	local cs = Config.cellSize
	local IN, OUT, FLUID = Color3.fromRGB(63, 138, 106), Color3.fromRGB(201, 154, 60), Color3.fromRGB(96, 150, 190)
	local function tag(anchor, text, color)
		local gui = Instance.new("BillboardGui")
		gui.Name, gui.Size, gui.StudsOffset, gui.MaxDistance, gui.Enabled = "PortLabel", UDim2.new(0, 110, 0, 24), Vector3.new(0, 1.3, 0), 60, false
		local label = Instance.new("TextLabel")
		label.Size, label.BackgroundColor3, label.BackgroundTransparency = UDim2.new(1, 0, 1, 0), color, 0.1
		label.TextColor3, label.Font, label.TextScaled, label.Text = Color3.fromRGB(247, 244, 236), Enum.Font.GothamBold, true, text
		local round = Instance.new("UICorner")
		round.CornerRadius = UDim.new(0, 6)
		round.Parent = label
		label.Parent = gui
		gui.Parent = anchor
	end
	local function edge(side)
		local x, z, dir = Ports.cell(def, e, side)
		local out = Vector3.new(Grid.DX[dir], 0, Grid.DZ[dir])
		-- middle of the neighbouring cell, just above the floor
		return WW.cellCenter(self, room, e.floor, x, z) + out * cs + Vector3.new(0, 0.12, 0), out
	end
	local inSide, outSide = Ports.sides(def, e)
	local at, out = edge(inSide)
	tag(flatArrow(body, "PortIn", at - out * 0.75, -out, IN, 1.5, true), "Einlauf", IN)
	at, out = edge(outSide)
	tag(flatArrow(body, "PortOut", at + out * 0.75, out, OUT, 1.5, true), Ports.isAuto(e) and "Auslauf · auto" or "Auslauf · fest", OUT)
	for _, p in ipairs(def.ports) do
		if p.type == "fluid" then
			local x, z, dir = Grid.port(def, p, e.gx, e.gz, e.rot)
			local o = Vector3.new(Grid.DX[dir], 0, Grid.DZ[dir])
			local drop = part({ Name = "PortFluid", Shape = Enum.PartType.Ball, Size = Vector3.new(0.8, 0.8, 0.8), Color = FLUID,
				Material = Enum.Material.Glass, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = false, Transparency = 1,
				Position = WW.cellCenter(self, room, e.floor, x, z) + o * cs + Vector3.new(0, 0.45, 0) }, body)
			drop:SetAttribute("ArcanePortMark", true)
			tag(drop, (p.mode == "in") and "Rohr · Zulauf" or "Rohr · Ablauf", FLUID)
		end
	end
end

-- byUid: all entities of the room (to find a gate's partner)
local function entityModel(self, room, e, byUid)
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
			body.CFrame = CFrame.new(base.X, floorY + body.Size.Y / 2, base.Z) * CFrame.Angles(0, math.rad(90 * e.rot), 0)
				* (template.CFrame - template.CFrame.Position)
		else
			local pivot = CFrame.new(base - Vector3.new(0, height / 2, 0))
				* CFrame.Angles(0, math.rad(90 * e.rot), 0)
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
		if Ports.isMachine(def) then portMarks(self, room, e, def, body) end
	else
		-- arrow in the real conveying direction (towards the first outlet of the part) and item token
		local outDir = e.rot % 4
		for _, p in ipairs(def.ports or {}) do
			if p.mode == "out" then outDir = (p.dir + e.rot) % 4 break end
		end
		local flow = Vector3.new(Grid.DX[outDir], 0, Grid.DZ[outDir])
		if def.kind == "belt" then
			-- belts show their direction by the moving cleats the client draws on the running surface
			body:SetAttribute("BeltIn", e.rot % 4)
		elseif def.layer ~= "pipe" then
			flatArrow(body, "Arrow", base + Vector3.new(0, height / 2 + 0.08, 0) + flow * 0.7, flow, Color3.fromRGB(201, 154, 60), 1.4, false)
		end
		if CARRIER[def.kind] then
			-- what every client needs to draw the goods gliding over this part (GoodsAnimator)
			local multi = 0
			for _, p in ipairs(def.ports or {}) do if p.mode == "out" then multi = multi + 1 end end
			body:SetAttribute("GoodsRoom", room.owner)
			body:SetAttribute("GoodsCell", Vector3.new(e.gx, e.floor, e.gz))
			-- top of the belt surface (the belt model sits a little below its nominal height)
			body:SetAttribute("GoodsSurface", base + Vector3.new(0, height / 2 - 0.11, 0))
			body:SetAttribute("GoodsOut", multi == 1 and outDir or -1)       -- splitters decide per item
			body:SetAttribute("GoodsPeriod", PERIOD[def.kind] and Config.sim[PERIOD[def.kind]] or 0.5)
			-- where the goods go next; lifts climb on the way, gates send them to their partner
			local partner = e.link and byUid and byUid[e.link]
			local links = GoodsMotion.links(def, e, partner)
			if links.next then body:SetAttribute("GoodsNext", Vector3.new(links.next.gx, links.next.floor, links.next.gz)) end
			if links.rise then body:SetAttribute("GoodsRise", links.rise * Config.floorHeight) end
			if links.warp then
				local w = links.warp
				body:SetAttribute("GoodsWarp", WW.cellCenter(self, room, w.floor, w.gx, w.gz) + Vector3.new(0, height - 0.11, 0))
				body:SetAttribute("GoodsWarpOut", w.out)
			end
		end
	end
	body.Parent = room.entityFolder
	return body
end

-- Publishes what lies on the conveyors of a room (Game.goodsView) as attributes of the conveyor
-- parts: GoodsItem, GoodsAt (server time the item arrived), GoodsIn (direction it came in).  Only
-- changes are written, so this can run several times a second.
function WW:syncGoods(ownerId, goods, now)
	local room = self.rooms[ownerId]
	if not room or not goods then return end
	for uid, cur in pairs(room.entities) do
		local body = cur.body
		if body and body.Parent and body:GetAttribute("GoodsOut") ~= nil then
			local g = goods[uid]
			local item = g and g.item or nil
			local at = g and (now - g.age) or nil
			if item ~= cur.goodsItem or (item and math.abs(at - cur.goodsAt) > 0.25) then
				cur.goodsItem, cur.goodsAt = item, at
				body:SetAttribute("GoodsItem", item)
				body:SetAttribute("GoodsAt", at)
				body:SetAttribute("GoodsIn", g and g.inDir or nil)
			end
		end
	end
end

-- Mirrors a workshop view (Game.workshopView) into Instances. Cheap when nothing changed.
function WW:sync(view, label)
	local room = self:ensureRoom(view.owner, view.cells, view.floors, label)
	if not room then return nil end
	if room.version ~= view.version then
		local seen, byUid = {}, {}
		for _, e in ipairs(view.entities) do byUid[e.uid] = e end
		for _, e in ipairs(view.entities) do
			seen[e.uid] = true
			local cur = room.entities[e.uid]
			local sig = e.machine .. ":" .. e.gx .. ":" .. e.gz .. ":" .. e.floor .. ":" .. e.rot
				.. ":" .. tostring(e.inSide) .. ":" .. tostring(e.outSide) .. ":" .. tostring(e.outAuto)
			local partner = e.link and byUid[e.link]
			if partner then                       -- a gate is redrawn when its partner moves
				sig = sig .. ":" .. partner.uid .. "@" .. partner.gx .. "," .. partner.gz .. "," .. partner.floor .. "," .. partner.rot
			end
			if not cur or cur.sig ~= sig then
				if cur then cur.body:Destroy() end
				room.entities[e.uid] = { sig = sig, body = entityModel(self, room, e, byUid) }
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
