-- ROBLOX CLIENT (UNVERIFIED_IN_STUDIO): HUD, panels and build mode of Arcane Village.
-- Mobile first: large touch targets, one panel at a time, everything reachable without a keyboard.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local ProximityPromptService = game:GetService("ProximityPromptService")
local Shared = ReplicatedStorage:WaitForChild("ArcaneShared")
local Items = require(Shared.Items)
local Recipes = require(Shared.Recipes)
local Machines = require(Shared.Machines)
local Research = require(Shared.Research)
local Quests = require(Shared.Quests)
local Locations = require(Shared.Locations)
local Market = require(Shared.MarketCatalog)
local Config = require(Shared.Config)
local Grid = require(Shared.GridMath)
local Net = require(script.Parent:WaitForChild("NetworkClient"))
local player = Players.LocalPlayer

local C = { cream = Color3.fromRGB(241, 235, 221), ink = Color3.fromRGB(35, 32, 31), brass = Color3.fromRGB(201, 154, 60),
	wood = Color3.fromRGB(91, 58, 38), ok = Color3.fromRGB(79, 138, 85), warn = Color3.fromRGB(206, 122, 59),
	bad = Color3.fromRGB(193, 67, 59), dim = Color3.fromRGB(138, 127, 115) }

-- ---------------------------------------------------------------- widgets
local gui = Instance.new("ScreenGui")
gui.Name, gui.ResetOnSpawn, gui.IgnoreGuiInset = "ArcaneUI", false, false
gui.Parent = player:WaitForChild("PlayerGui")
local scale = Instance.new("UIScale")
scale.Parent = gui
local function rescale()
	local cam = workspace.CurrentCamera
	if cam then scale.Scale = math.clamp(math.min(cam.ViewportSize.X / 1280, cam.ViewportSize.Y / 720), 0.7, 1.4) end
end
rescale()
RunService.Heartbeat:Connect(rescale)

local function make(class, props, parent)
	local o = Instance.new(class)
	for k, v in pairs(props) do o[k] = v end
	o.Parent = parent
	return o
end
local function corner(o, r) make("UICorner", { CornerRadius = UDim.new(0, r or 8) }, o) end
local function label(text, parent, size, color, bold)
	return make("TextLabel", { Text = text, Size = size or UDim2.new(1, 0, 0, 24), BackgroundTransparency = 1, TextColor3 = color or C.ink,
		Font = bold and Enum.Font.GothamBold or Enum.Font.Gotham, TextSize = 16, TextXAlignment = Enum.TextXAlignment.Left,
		TextWrapped = true, AutomaticSize = Enum.AutomaticSize.Y }, parent)
end
local function button(text, parent, onClick, color)
	local b = make("TextButton", { Text = text, Size = UDim2.new(0, 132, 0, 44), BackgroundColor3 = color or C.brass, TextColor3 = C.ink,
		Font = Enum.Font.GothamBold, TextSize = 15, AutoButtonColor = true, TextWrapped = true }, parent)
	corner(b)
	local busy = false
	b.Activated:Connect(function()
		if busy then return end           -- no double submits while the server answers
		busy = true
		local ok, err = pcall(onClick)
		if not ok then warn(err) end
		busy = false
	end)
	return b
end
local function amount(id, n)
	local it = Items[id]
	if it and it.unit == "ml" then return n .. " ml " .. it.name end
	return n .. " × " .. (it and it.name or id)
end
local function itemList(map)
	local parts = {}
	for id, n in pairs(map or {}) do parts[#parts + 1] = amount(id, n) end
	table.sort(parts)
	return (#parts > 0) and table.concat(parts, ", ") or "–"
end

-- toasts
local toastFrame = make("Frame", { Size = UDim2.new(0, 420, 0, 200), Position = UDim2.new(0.5, -210, 0, 70), BackgroundTransparency = 1 }, gui)
make("UIListLayout", { Padding = UDim.new(0, 6), HorizontalAlignment = Enum.HorizontalAlignment.Center }, toastFrame)
local function toast(text, color)
	local t = make("TextLabel", { Text = text, Size = UDim2.new(1, 0, 0, 36), BackgroundColor3 = color or C.ink, TextColor3 = C.cream,
		Font = Enum.Font.GothamMedium, TextSize = 16, TextWrapped = true }, toastFrame)
	corner(t)
	task.delay(3.5, function() t:Destroy() end)
end
local function send(action, payload)
	local result = Net.send(action, payload)
	local msg = Net.message(result)
	if msg then toast(msg, C.bad) end
	return result
end

-- HUD
local hud = make("Frame", { Size = UDim2.new(0, 300, 0, 132), Position = UDim2.new(0, 12, 0, 12), BackgroundColor3 = C.cream }, gui)
corner(hud, 10)
make("UIPadding", { PaddingLeft = UDim.new(0, 10), PaddingTop = UDim.new(0, 6), PaddingRight = UDim.new(0, 10) }, hud)
make("UIListLayout", { Padding = UDim.new(0, 2) }, hud)
local hudMoney = label("", hud, nil, C.ink, true)
local hudQuest = label("", hud, nil, C.wood, true)
local hudHint = label("", hud, nil, C.ink)
local hudSave = label("", hud, nil, C.dim)

-- panel host
local panel = make("Frame", { Size = UDim2.new(0, 430, 1, -170), Position = UDim2.new(1, -442, 0, 12), BackgroundColor3 = C.cream, Visible = false }, gui)
corner(panel, 10)
local panelTitle = make("TextLabel", { Size = UDim2.new(1, -60, 0, 40), Position = UDim2.new(0, 12, 0, 4), BackgroundTransparency = 1, Text = "",
	Font = Enum.Font.GothamBold, TextSize = 20, TextColor3 = C.wood, TextXAlignment = Enum.TextXAlignment.Left }, panel)
local scroll = make("ScrollingFrame", { Size = UDim2.new(1, -16, 1, -56), Position = UDim2.new(0, 8, 0, 48), BackgroundTransparency = 1,
	CanvasSize = UDim2.new(0, 0, 0, 0), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 8 }, panel)
make("UIListLayout", { Padding = UDim.new(0, 6) }, scroll)
local current = nil            -- { name, render }
local function closePanel() current = nil panel.Visible = false end
button("X", panel, closePanel, C.bad).Size = UDim2.new(0, 44, 0, 40)
panel:FindFirstChildOfClass("TextButton").Position = UDim2.new(1, -50, 0, 4)

local function clear()
	for _, child in ipairs(scroll:GetChildren()) do
		if not child:IsA("UIListLayout") then child:Destroy() end
	end
end
-- a row: text on the left, optional action button on the right
local function row(text, actionText, onClick, color)
	local f = make("Frame", { Size = UDim2.new(1, -8, 0, 48), BackgroundColor3 = Color3.fromRGB(233, 224, 204), AutomaticSize = Enum.AutomaticSize.Y }, scroll)
	corner(f, 6)
	local l = label(text, f, UDim2.new(1, actionText and -150 or -12, 0, 44), color)
	l.Position = UDim2.new(0, 8, 0, 2)
	if actionText then
		local b = button(actionText, f, onClick)
		b.Position = UDim2.new(1, -138, 0, 2)
	end
	return f
end
local function heading(text) label(text, scroll, UDim2.new(1, -8, 0, 26), C.wood, true) end
-- Short fingerprint of everything the panels show that changes through actions.
local function signature(s)
	local parts = { s.wallet, s.knowledge, s.repPoints, s.questIndex, s.version, tostring(s.inWorkshop),
		s.quest and s.quest.progress or 0, s.project and s.project.progress or 0, s.workshop and s.workshop.version or 0 }
	local ids = {}
	for id in pairs(s.items) do ids[#ids + 1] = id end
	table.sort(ids)
	for _, id in ipairs(ids) do parts[#parts + 1] = id .. "=" .. s.items[id] end
	local n = 0
	for _ in pairs(s.research) do n = n + 1 end
	parts[#parts + 1] = n
	for _, o in ipairs(s.orders or {}) do parts[#parts + 1] = tostring(o.id) end
	for id, c in pairs(s.chains or {}) do parts[#parts + 1] = id .. (c.done or 0) end
	for i = 1, #parts do parts[i] = tostring(parts[i]) end
	return table.concat(parts, "|")
end
local function open(name, title, render)
	current = { name = name, title = title, render = render, version = Net.snapshot and signature(Net.snapshot), at = os.clock() }
	panelTitle.Text = title
	panel.Visible = true
	clear()
	scroll.CanvasPosition = Vector2.new(0, 0)
	if Net.snapshot then render(Net.snapshot) end
end
-- Panels with running timers; everything else only changes when the game state changes.
local LIVE = { machine = 2, workshop = 2 }
-- The server sends a snapshot every second.  Rebuilding the open panel each time made lists jump
-- back to the top and swallowed taps on buttons that were just being replaced.  Rebuild only when
-- the state changed (or at a slow pace for panels that show timers) and keep the scroll position.
local function refresh(force)
	local s = Net.snapshot
	if not (current and s) then return end
	local age = os.clock() - current.at
	local sig = signature(s)
	if not force and sig == current.version and age < (LIVE[current.name] or 8) then return end
	current.version, current.at = sig, os.clock()
	local keep = scroll.CanvasPosition
	clear()
	current.render(s)
	task.defer(function() scroll.CanvasPosition = keep end)
end

-- ---------------------------------------------------------------- panels
local function renderInventory(s)
	heading("Rohstoffe und Zwischenprodukte")
	local ids = {}
	for id in pairs(s.items) do ids[#ids + 1] = id end
	table.sort(ids)
	for _, id in ipairs(ids) do
		if Items[id].type ~= "product" then row(amount(id, s.items[id])) end
	end
	heading("Produkte")
	for _, id in ipairs(ids) do
		if Items[id].type == "product" then row(amount(id, s.items[id]) .. "   (Wert " .. Items[id].sellBase .. ")") end
	end
	if #ids == 0 then row("Dein Beutel ist leer. Sammle Kräuter am Marktplatz.") end
end

local STATE = { Running = { "läuft", C.ok }, WaitingForInputs = { "wartet auf", C.warn }, OutputBlocked = { "Ausgang voll – bitte leeren", C.bad },
	NoFuel = { "braucht Holzkohle", C.bad }, Paused = { "pausiert", C.dim }, InvalidRecipe = { "kein Rezept gewählt", C.warn } }
local selectedUid = nil
local function renderMachine(s)
	local e
	for _, x in ipairs(s.workshop and s.workshop.entities or {}) do if x.uid == selectedUid then e = x end end
	if not e then row("Diese Maschine gibt es nicht mehr.") return end
	local def = Machines[e.machine]
	if def.kind == "machine" then
		local st = STATE[e.state] or { "bereit", C.ok }
		local text = "Status: " .. st[1]
		if e.state == "WaitingForInputs" and e.waiting then text = text .. " " .. Items[e.waiting].name end
		if e.job then text = text .. string.format("  (%d s übrig)", math.ceil(e.job.remaining)) end
		row(text, e.paused and "Fortsetzen" or "Pause", function() send("ToggleMachine", { uid = e.uid }) end, st[2])
		heading("Rezepte")
		for id, r in pairs(Recipes) do
			if r.machineId == e.machine then
				local known = s.research[r.requiredResearch]
				local line = itemList(r.inputs) .. "  →  " .. itemList(r.outputs) .. "  (" .. r.durationSec .. " s)"
				if not known then
					row("🔒 " .. line .. "\nForschung: " .. Research[r.requiredResearch].name, nil, nil, C.dim)
				else
					row(((e.recipe == id) and "● " or "") .. line, "Herstellen", function() send("StartManualCraft", { uid = e.uid, recipe = id }) end)
				end
			end
		end
		if def.usesFuel then
			row("Brennstoff: " .. e.fuel .. " Holzkohle", "Nachlegen", function()
				send("TransferStack", { from = "inv", to = e.uid, item = "fuel_charcoal", amount = 4 })
			end)
		end
	end
	heading("Inhalt")
	local function contents(store, slot, title)
		for id, n in pairs(store or {}) do
			row(title .. ": " .. amount(id, n), "Entnehmen", function()
				send("TransferStack", { from = e.uid, to = "inv", item = id, amount = n, slot = slot })
			end)
		end
	end
	contents(e.out, "out", "Fertig") contents(e.outFluid, "out", "Fertig")
	contents(e.inv, "in", (def.kind == "machine") and "Zutat" or "Lager") contents(e.fluids, "in", "Flüssigkeit")
	if e.item then contents({ [e.item] = 1 }, nil, "Auf dem Band") end
	if def.kind == "crate" or def.kind == "shelf" or def.kind == "tank" or (def.kind == "machine" and e.recipe) then
		heading("Aus dem Beutel einfüllen")
		for id, n in pairs(s.items) do
			local fits = def.kind == "crate" and Items[id].unit ~= "ml"
				or (def.kind == "shelf" and Items[id].type == "product")
				or (def.kind == "tank" and Items[id].unit == "ml")
				or (def.kind == "machine" and Recipes[e.recipe].inputs[id] ~= nil)
			if fits then
				row(amount(id, n), "Einfüllen", function()
					local action = (def.kind == "shelf") and "StockShelf" or "TransferStack"
					local payload = (def.kind == "shelf") and { uid = e.uid, item = id, amount = n }
						or { from = "inv", to = e.uid, item = id, amount = n }
					send(action, payload)
				end)
			end
		end
	end
	heading("Bauteil")
	row("Drehen (90°)", "Drehen", function() send("RotateMachine", { uid = e.uid }) end)
	row("Abbauen – Inhalt kommt in den Beutel, 60 % der Kosten zurück", "Abbauen", function()
		if send("RemoveMachine", { uid = e.uid }).ok then closePanel() end
	end, C.bad)
	if e.machine == "kettle" then
		row("Experiment: 1 Kraut + 1000 ml Wasser → +3 Wissen (max. 5 pro Tag)", "Forschen", function() send("Experiment", { uid = e.uid }) end)
	end
end

local Build = { machine = nil, rot = 0, ghost = nil, cell = nil }
local function renderBuild(s)
	if not s.workshop then row("Bauen kannst du nur in deiner Werkstatt. Folge dem Wegweiser „Deine Werkstatt“ und geh hinein.") return end
	for _, cat in ipairs({ { "machine", "Maschinen" }, { "transport", "Transport" }, { "storage", "Lager" } }) do
		heading(cat[2])
		local ids = {}
		for id, def in pairs(Machines) do if def.category == cat[1] then ids[#ids + 1] = id end end
		table.sort(ids, function(a, b) return Machines[a].cost < Machines[b].cost end)
		for _, id in ipairs(ids) do
			local def = Machines[id]
			if s.research[def.research] then
				row(def.name .. "  –  " .. def.cost .. " Münzen  (" .. def.w * 2 .. "×" .. def.d * 2 .. " Studs)", "Platzieren", function()
					Build.machine, Build.rot, Build.pointer, Build.cell = id, 0, nil, nil
					closePanel()
					toast("Tippe auf den Werkstattboden, um den Platz zu wählen. ⟳ dreht, ✓ baut, X bricht ab.", C.wood)
				end)
			else
				row("🔒 " .. def.name .. "\nForschung: " .. Research[def.research].name, nil, nil, C.dim)
			end
		end
	end
end

local function renderResearch(s)
	label("Wissen: " .. s.knowledge .. "   (erforschen in der Markthalle oder in deiner Werkstatt)", scroll, nil, C.wood, true)
	for tier = 1, 5 do
		heading("Stufe " .. tier)
		for id, node in pairs(Research) do
			if node.tier == tier then
				local ready = true
				local needs = {}
				for _, p in ipairs(node.prereqs) do
					if not s.research[p] then ready = false needs[#needs + 1] = Research[p].name end
				end
				local unlocks = {}
				for _, u in ipairs(node.unlocks) do
					unlocks[#unlocks + 1] = (Machines[u] and Machines[u].name) or (Recipes[u] and itemList(Recipes[u].outputs)) or u
				end
				local text = node.name .. "  (" .. node.cost .. " Wissen)\n→ " .. table.concat(unlocks, ", ")
				if s.research[id] then row("✓ " .. text, nil, nil, C.ok)
				elseif not ready then row("🔒 " .. text .. "\nBenötigt: " .. table.concat(needs, ", "), nil, nil, C.dim)
				else row(text, "Erforschen", function() send("UnlockResearch", { research = id }) end) end
			end
		end
	end
end

local function renderOrders(s)
	if s.quest then
		heading("Hauptauftrag")
		local o = s.quest.objective
		if o.type == "deliver" then
			row(s.quest.title .. "\n" .. s.quest.hint, "Abgeben", function() send("ClaimOrder", { kind = "main", id = s.quest.id }) end)
		else
			row(s.quest.title .. "\n" .. s.quest.hint)
		end
	end
	heading("Auftragstafel der Markthalle")
	for _, o in ipairs(s.orders) do
		row(o.title .. "\n" .. itemList(o.items) .. "  →  " .. o.coins .. " Münzen, " .. o.rep .. " Ruf", "Abgeben", function()
			send("ClaimOrder", { kind = "order", id = o.id })
		end)
	end
	heading("Dorfbewohner")
	for id, c in pairs(s.chains) do
		if c.step then
			local where = Locations.locations[c.at].name
			if c.unlocked then
				row(c.name .. " (" .. c.done .. "/" .. c.total .. ") – " .. where .. "\n" .. c.step.title .. ": " .. itemList(c.step.items), "Abgeben", function()
					send("ClaimOrder", { kind = "chain", id = id })
				end)
			else
				row("🔒 " .. c.name .. " – " .. where, nil, nil, C.dim)
			end
		else
			row("✓ " .. c.name, nil, nil, C.ok)
		end
	end
	if s.project then
		heading("Dorfprojekt (diese Server-Sitzung)")
		local p = s.project
		row(p.title .. "\n" .. p.progress .. " / " .. p.count .. " " .. Items[p.item].name .. (p.done and "  – fertig!" or ""),
			(not p.done) and "Spenden" or nil, function() send("DonateProject", { amount = 1 }) end)
	end
end

local function renderWorkshop(s)
	local w = s.workshop
	if not w then row("Du bist nicht in einer Werkstatt. Folge dem Wegweiser „Deine Werkstatt“ und geh hinein.") return end
	heading("Betrieb")
	row(string.format("Durchsatz: %.1f Teile pro Minute (letzte Minute)", w.ratePerMin))
	row("Im Regal: " .. itemList(w.stock) .. string.format("\nNächster Kunde in etwa %d s", math.max(0, math.ceil(w.nextCustomerIn))))
	heading("Ausbau")
	local nextPlot = Config.plotTiers[w.sizeTier + 1]
	if nextPlot then
		row("Grundfläche " .. nextPlot.cells * 2 .. "×" .. nextPlot.cells * 2 .. " Studs – " .. nextPlot.cost .. " Münzen", "Kaufen", function() send("BuyUpgrade", { kind = "plot" }) end)
	end
	local nextFloor = Config.floors[w.floors + 1]
	if nextFloor then
		row("Etage " .. (w.floors + 1) .. " – " .. nextFloor.cost .. " Münzen", "Kaufen", function() send("BuyUpgrade", { kind = "floor" }) end)
	end
end

-- ---------------------------------------------------------------- action bar
local bar = make("Frame", { Size = UDim2.new(0, 700, 0, 52), Position = UDim2.new(0.5, -350, 1, -64), BackgroundTransparency = 1 }, gui)
make("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), HorizontalAlignment = Enum.HorizontalAlignment.Center }, bar)
button("Beutel", bar, function() open("inv", "Beutel", renderInventory) end)
button("Bauen", bar, function() open("build", "Baukatalog", renderBuild) end)
button("Forschung", bar, function() open("research", "Forschung", renderResearch) end)
button("Aufträge", bar, function() open("orders", "Aufträge", renderOrders) end)
button("Werkstatt", bar, function() open("workshop", "Werkstatt", renderWorkshop) end)

-- ---------------------------------------------------------------- build mode (ghost on the grid)
local confirm = make("Frame", { Size = UDim2.new(0, 220, 0, 56), Position = UDim2.new(0.5, -110, 1, -130), BackgroundTransparency = 1, Visible = false }, gui)
make("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8) }, confirm)
local function stopBuild()
	Build.machine, Build.pointer, Build.cell = nil, nil, nil
	if Build.ghost then Build.ghost:Destroy() Build.ghost = nil end
	confirm.Visible = false
end
local function placeGhost()
	if not (Build.machine and Build.cell) then return end
	local c = Build.cell
	local result = send("PlaceMachine", { machine = Build.machine, gx = c.gx, gz = c.gz, floor = c.floor, rot = Build.rot })
	if result.ok then toast(Machines[Build.machine].name .. " gebaut", C.ok) end
end
button("⟳", confirm, function() Build.rot = (Build.rot + 1) % 4 end).Size = UDim2.new(0, 64, 0, 52)
button("✓", confirm, placeGhost, C.ok).Size = UDim2.new(0, 64, 0, 52)
button("X", confirm, stopBuild, C.bad).Size = UDim2.new(0, 64, 0, 52)

local function pointerPosition()
	if UserInputService.TouchEnabled and not UserInputService.MouseEnabled then
		-- touch: the last spot tapped on the floor; before the first tap the screen centre
		if Build.pointer then return Build.pointer end
		local cam = workspace.CurrentCamera
		return Vector2.new(cam.ViewportSize.X / 2, cam.ViewportSize.Y / 2)
	end
	return UserInputService:GetMouseLocation()
end
UserInputService.TouchTapInWorld:Connect(function(position, processed)
	if Build.machine and not processed then Build.pointer = position end
end)
-- First workshop floor under a screen point.  The ray passes the own character (which stands in the
-- middle of the screen on a phone), machines and walls.
local function floorUnder(pos)
	local cam = workspace.CurrentCamera
	local ray = cam:ViewportPointToRay(pos.X, pos.Y)
	local ignore = { Build.ghost, player.Character }
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	local from = ray.Origin
	for _ = 1, 8 do
		params.FilterDescendantsInstances = ignore
		local hit = workspace:Raycast(from, ray.Direction * 500, params)
		if not hit then return nil end
		if hit.Instance:GetAttribute("ArcaneFloor") then return hit end
		ignore[#ignore + 1] = hit.Instance
	end
	return nil
end
RunService.RenderStepped:Connect(function()
	local s = Net.snapshot
	if not (Build.machine and s and s.workshop and s.room) then
		if Build.ghost then stopBuild() end
		return
	end
	confirm.Visible = true
	local hit = floorUnder(pointerPosition())
	if not hit then return end
	local def = Machines[Build.machine]
	local w, d = Grid.size(def, Build.rot)
	local half = s.workshop.cells * Config.cellSize / 2
	local gx = math.floor((hit.Position.X - s.room.x + half) / Config.cellSize)
	local gz = math.floor((hit.Position.Z - s.room.z + half) / Config.cellSize)
	local floor = hit.Instance:GetAttribute("ArcaneFloor")
	Build.cell = { gx = gx, gz = gz, floor = floor }
	if not Build.ghost then
		Build.ghost = make("Part", { Anchored = true, CanCollide = false, CanQuery = false, Transparency = 0.5, Material = Enum.Material.Neon,
			Color = C.ok, Name = "ArcaneGhost" }, workspace)
		make("Part", { Name = "Front", Anchored = true, CanCollide = false, CanQuery = false, Color = C.brass, Material = Enum.Material.Neon,
			Size = Vector3.new(0.6, 0.6, 1.6) }, Build.ghost)
	end
	local cs = Config.cellSize
	local centre = Vector3.new(s.room.x - half + gx * cs + w * cs / 2, s.room.y + (floor - 1) * Config.floorHeight + 1.5, s.room.z - half + gz * cs + d * cs / 2)
	Build.ghost.Size = Vector3.new(w * cs, 3, d * cs)
	Build.ghost.Position = centre
	local front = (Build.rot % 4)
	Build.ghost.Front.CFrame = CFrame.new(centre + Vector3.new(Grid.DX[front] * w * cs / 2, 1.8, Grid.DZ[front] * d * cs / 2))
		* CFrame.Angles(0, math.rad(-90 * Build.rot), 0)
	-- red when the cells are taken or outside (the server decides in the end)
	local blocked = gx < 0 or gz < 0 or gx + w > s.workshop.cells or gz + d > s.workshop.cells
	for _, e in ipairs(s.workshop.entities) do
		local ew, ed = Grid.size(Machines[e.machine], e.rot)
		if e.floor == floor and Machines[e.machine].layer == def.layer and gx < e.gx + ew and e.gx < gx + w and gz < e.gz + ed and e.gz < gz + d then
			blocked = true
		end
	end
	Build.ghost.Color = blocked and C.bad or C.ok
end)
UserInputService.InputBegan:Connect(function(input, processed)
	if processed or not Build.machine then return end
	if input.KeyCode == Enum.KeyCode.R then Build.rot = (Build.rot + 1) % 4
	elseif input.KeyCode == Enum.KeyCode.Escape or input.KeyCode == Enum.KeyCode.X then stopBuild()
	elseif input.UserInputType == Enum.UserInputType.MouseButton1 then placeGhost() end
end)

-- ---------------------------------------------------------------- prompts, snapshots, notifications
ProximityPromptService.PromptTriggered:Connect(function(prompt)
	local uid = prompt.Parent and prompt.Parent:GetAttribute("ArcaneUid")
	if uid then
		selectedUid = uid
		open("machine", Machines[prompt.Parent:GetAttribute("ArcaneMachine")].name, renderMachine)
	end
end)
Net.on("OpenMarket", function(id)
	local merchant = Market.merchants[id]
	if not merchant then return end
	local buying = false
	open("market", merchant.name, function(s)
		heading(merchant.trade)
		label(merchant.line, scroll)
		for _, offer in ipairs(merchant.offers) do
			local description = amount(offer.item, offer.amount) .. " · " .. offer.coins .. " Münzen"
			if s.market and s.market[offer.item] then
				row(description, "Kaufen", function()
					if buying then return end
					buying = true
					local result = send("BuyMarketOffer", { merchant = id, item = offer.item })
					buying = false
					if result.ok and result.code == "OK" then
						toast("Gekauft: " .. amount(result.payload.item, result.payload.amount), C.ok)
					end
				end)
			else
				local rule = offer.unlock
				local research = rule and rule.research and Research[rule.research]
				local quest = rule and rule.quest and Quests.main[rule.quest]
				row(description .. "\nFreischalten: " .. (research and research.name or quest and quest.title or "Fortschritt"), nil, nil, C.dim)
			end
		end
	end)
end)
Net.on("OpenLocation", function(id)
	local loc = Locations.locations[id]
	local services = table.concat(loc.services, ",")
	if string.find(services, "research") then open("research", loc.name .. " – Forschung", renderResearch)
	else open("orders", loc.name, renderOrders) end
end)
Net.on("ActionResult", function(result)
	if result.ok and result.payload and result.payload.item then
		toast("+ " .. amount(result.payload.item, result.payload.amount), C.ok)
	else
		local msg = Net.message(result)
		if msg then toast(msg, C.bad) end
	end
end)
Net.on("Status", function(data)
	if data.status == "failed" or data.status == "locked" or data.status == "corrupt" then
		toast("Spielstand konnte nicht geladen werden. Du kannst dich umsehen; bitte später neu verbinden.", C.bad)
	end
end)
Net.on("Saved", function(data)
	hudSave.Text = (data.ok and data.persistent) and "Gespeichert" or "Speichern fehlgeschlagen – wird erneut versucht"
end)

local NOTE = {
	quest_done = function(n) return "Auftrag erledigt: " .. Quests.main[n.quest].title end,
	discovery = function(n) return "Neues Rezept entdeckt: +" .. n.knowledge .. " Wissen" end,
	order_done = function(n) return "Lieferung angenommen: +" .. n.coins .. " Münzen" end,
	chain_step = function() return "Danke für die Lieferung!" end,
	project_done = function() return "Das Dorfprojekt ist fertig!" end,
	visit = function(n) return "Entdeckt: " .. Locations.locations[n.at].name end,
	coop = function(n) return "Werkstatt-Einladung: Rolle " .. n.role end,
}
-- ---------------------------------------------------------------- signposts
-- Two markers that are visible through everything: the own workshop and the place the current
-- main quest sends the player to.  Positions come from the server snapshot.
local function signpost(color)
	local anchor = make("Part", { Name = "ArcaneSignpost", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false,
		Transparency = 1, Size = Vector3.new(1, 1, 1) }, workspace)
	local board = make("BillboardGui", { Size = UDim2.new(0, 180, 0, 46), AlwaysOnTop = true, MaxDistance = 100000, Enabled = false,
		StudsOffsetWorldSpace = Vector3.new(0, 14, 0) }, anchor)
	local text = make("TextLabel", { Size = UDim2.new(1, 0, 1, 0), BackgroundColor3 = color, BackgroundTransparency = 0.15,
		TextColor3 = C.cream, Font = Enum.Font.GothamBold, TextScaled = true, Text = "" }, board)
	corner(text, 10)
	make("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8), PaddingTop = UDim.new(0, 4), PaddingBottom = UDim.new(0, 4) }, text)
	return { anchor = anchor, board = board, text = text, label = "" }
end
local posts = { home = signpost(C.wood), quest = signpost(C.ok) }
local function setPost(post, target, labelText)
	post.board.Enabled = target ~= nil
	if target then
		post.anchor.Position = Vector3.new(target.x, target.y, target.z)
		post.label = labelText
	end
end
local postAcc = 0
RunService.Heartbeat:Connect(function(dt)
	postAcc = postAcc + dt
	if postAcc < 0.25 then return end
	postAcc = 0
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	for _, post in pairs(posts) do
		if post.board.Enabled then
			local distance = root and math.floor((root.Position - post.anchor.Position).Magnitude) or nil
			post.text.Text = distance and (post.label .. "  ·  " .. distance .. " m") or post.label
			-- close by the marker would only be in the way
			post.text.Visible = not distance or distance > 14
		end
	end
end)

Net.onSnapshot(function(s)
	local atHome = s.inWorkshop == s.userId
	local questAtHome = s.guide and s.guide.home
	setPost(posts.home, (not atHome and not questAtHome) and s.home or nil, "Deine Werkstatt")
	setPost(posts.quest, (s.guide and not (questAtHome and atHome)) and s.guide or nil, s.guide and ("Auftrag: " .. s.guide.label) or "")
	hudMoney.Text = s.wallet .. " Münzen   " .. s.knowledge .. " Wissen   Ruf " .. s.repLevel
	if s.quest then
		hudQuest.Text = s.quest.title
		hudHint.Text = s.quest.hint
	else
		hudQuest.Text, hudHint.Text = "Alle Hauptaufträge erledigt", "Baue deine Fabrik weiter aus."
	end
	if s.safeMode then hudSave.Text = "Nur-Ansehen-Modus: Spielstand nicht geladen"
	elseif s.persistent == false then hudSave.Text = "Achtung: Fortschritt wird in dieser Sitzung nicht gespeichert" end
	for _, n in ipairs(s.notes or {}) do
		local f = NOTE[n.kind]
		if f then toast(f(n), C.ok) end
	end
	refresh()
end)
Net.send("RequestSnapshot")
