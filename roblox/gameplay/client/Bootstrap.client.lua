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
local MachineWindow = require(script.Parent:WaitForChild("MachineWindow"))
local Ports = require(Shared.MachinePorts)
local BeltPath = require(Shared.BeltPath)
local Hologram = require(script.Parent:WaitForChild("Hologram"))
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
local machineWindow                -- created further down; only one window is open at a time
local function open(name, title, render)
	if machineWindow and machineWindow.isOpen() then machineWindow.close() end
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

-- Storage and transport parts (crates, shelves, tanks, belts ...) keep the simple list panel;
-- production machines have their own window (MachineWindow.lua).
local selectedUid = nil
local function renderStorage(s)
	local e
	for _, x in ipairs(s.workshop and s.workshop.entities or {}) do if x.uid == selectedUid then e = x end end
	if not e then row("Dieses Bauteil gibt es nicht mehr, oder du stehst nicht in der Werkstatt.") return end
	local def = Machines[e.machine]
	heading("Inhalt")
	local any = false
	local function contents(store, slot, title)
		for id, n in pairs(store or {}) do
			any = true
			row(title .. ": " .. amount(id, n), "Entnehmen", function()
				send("TransferStack", { from = e.uid, to = "inv", item = id, amount = n, slot = slot })
			end)
		end
	end
	contents(e.inv, "in", "Lager") contents(e.fluids, "in", "Flüssigkeit") contents(e.out, "out", "Fertig")
	if e.item then any = true row("Auf dem Band: " .. amount(e.item, 1)) end
	if not any then row("Leer.") end
	if def.kind == "crate" or def.kind == "shelf" or def.kind == "tank" then
		heading("Aus dem Beutel einfüllen")
		for id, n in pairs(s.items) do
			local fits = (def.kind == "crate" and Items[id].unit ~= "ml")
				or (def.kind == "shelf" and Items[id].type == "product")
				or (def.kind == "tank" and Items[id].unit == "ml")
			if fits then
				row(amount(id, n), "Einfüllen", function()
					if def.kind == "shelf" then send("StockShelf", { uid = e.uid, item = id, amount = n })
					else send("TransferStack", { from = "inv", to = e.uid, item = id, amount = n }) end
				end)
			end
		end
	end
	heading("Bauteil")
	row("Drehen (90°)", "Drehen", function() send("RotateMachine", { uid = e.uid }) end)
	row("Abbauen – Inhalt kommt in den Beutel, 60 % der Kosten zurück", "Abbauen", function()
		if send("RemoveMachine", { uid = e.uid }).ok then closePanel() end
	end, C.bad)
end

local Build = { machine = nil, rot = 0, ghost = nil, cell = nil }
local startBuild                   -- defined with the build mode further down
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
					startBuild(id)
					closePanel()
					if Machines[id].kind == "belt" and id ~= "belt_turn" then
						toast("Bandstrecke: Anfang antippen, Ende antippen, ✓ baut. ⟳ kehrt die Richtung um. Am PC: ziehen.", C.wood)
					else
						toast("Tippe auf den Werkstattboden, um den Platz zu wählen. ⟳ dreht, ✓ baut, X bricht ab.", C.wood)
					end
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
-- Marks at the connections of the machines (made invisible by the server): shown while building
-- and while a machine window is open.
local marksShown = false
local function showPortMarks(on)
	if on == marksShown then return end
	marksShown = on
	local root = workspace:FindFirstChild("ArcaneWorkshops")
	if not root then return end
	for _, d in ipairs(root:GetDescendants()) do
		if d:IsA("BasePart") and d:GetAttribute("ArcanePortMark") then
			d.Transparency = on and 0.1 or 1
			local label = d:FindFirstChild("PortLabel")
			if label then label.Enabled = on end
		end
	end
end
workspace.DescendantAdded:Connect(function(d)
	if marksShown and d:IsA("BasePart") then
		task.defer(function()
			if marksShown and d:GetAttribute("ArcanePortMark") then
				d.Transparency = 0.1
				local label = d:FindFirstChild("PortLabel")
				if label then label.Enabled = true end
			end
		end)
	end
end)

local clearLine                                   -- defined with the line building below
-- removes the hologram of a single part (its glowing group and its arrows)
local function dropGhost()
	if Build.ghost then Build.ghost:Destroy() Build.ghost = nil end
	if Build.arrowFolder then Build.arrowFolder:Destroy() Build.arrowFolder = nil end
	Build.body, Build.plate, Build.ghostFor, Build.shown = nil, nil, nil, nil
end
local function dropGrid()
	if Build.grid then Build.grid:Destroy() Build.grid, Build.gridKey = nil, nil end
end
local function stopBuild()
	if clearLine then clearLine() end
	Build.machine, Build.pointer, Build.cell = nil, nil, nil
	dropGhost()
	dropGrid()
	confirm.Visible = false
	showPortMarks(machineWindow ~= nil and machineWindow.isOpen())
end
local function placeGhost()
	if not (Build.machine and Build.cell) then return end
	local c = Build.cell
	local result = send("PlaceMachine", { machine = Build.machine, gx = c.gx, gz = c.gz, floor = c.floor, rot = Build.rot })
	if result.ok then toast(Machines[Build.machine].name .. " gebaut", C.ok) end
end
local onRotate, onConfirm, onCancel             -- defined with the line building below
button("⟳", confirm, function() onRotate() end).Size = UDim2.new(0, 64, 0, 52)
button("✓", confirm, function() onConfirm() end, C.ok).Size = UDim2.new(0, 64, 0, 52)
button("X", confirm, function() onCancel() end, C.bad).Size = UDim2.new(0, 64, 0, 52)

-- Grid direction (0 = +z, 1 = +x, 2 = -z, 3 = -x) that lies to the right of the current view.
-- The workshop grid is aligned with the world axes.
local function rightOfView()
	local cam = workspace.CurrentCamera
	local right = cam and cam.CFrame.RightVector or Vector3.new(1, 0, 0)
	local best, bestDot = 1, -math.huge
	for dir = 0, 3 do
		local dot = right.X * Grid.DX[dir] + right.Z * Grid.DZ[dir]
		if dot > bestDot then best, bestDot = dir, dot end
	end
	return best
end
-- Starts placing a part.  Conveyors start pointing to the right as the player sees it at this
-- moment; the direction is then kept until the player turns it, whatever the camera does.
startBuild = function(id)
	local def = Machines[id]
	local conveyor = def.category == "transport" and def.layer ~= "pipe"
	Build.machine, Build.pointer, Build.cell = id, nil, nil
	Build.rot = conveyor and rightOfView() or 0
	dropGhost()
	showPortMarks(true)
end

local function pointerPosition()
	if UserInputService.TouchEnabled and not UserInputService.MouseEnabled then
		-- touch: the last spot tapped on the floor; before the first tap the screen centre
		if Build.pointer then return Build.pointer end
		local cam = workspace.CurrentCamera
		return Vector2.new(cam.ViewportSize.X / 2, cam.ViewportSize.Y / 2)
	end
	return UserInputService:GetMouseLocation()
end
-- First workshop floor under a screen point.  The ray passes the own character (which stands in the
-- middle of the screen on a phone), machines and walls.
local function floorUnder(pos)
	local cam = workspace.CurrentCamera
	local ray = cam:ViewportPointToRay(pos.X, pos.Y)
	local ignore = { player.Character }                -- holograms, grid and arrows do not take part in queries
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

-- ghost: footprint box plus arrows that show exactly what the placed part will do
local GHOST_IN, GHOST_OUT = Color3.fromRGB(63, 138, 106), Color3.fromRGB(201, 154, 60)
local function ghostArrow(name, color, text)
	if not Build.arrowFolder then Build.arrowFolder = make("Folder", { Name = "ArcaneGhostArrows" }, workspace) end
	local folder = make("Folder", { Name = name }, Build.arrowFolder)
	local pieces = {}
	for i = 1, 3 do
		pieces[i] = make("Part", { Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = false,
			Material = Enum.Material.SmoothPlastic, Color = color, Size = (i == 1) and Vector3.new(0.3, 0.14, 1.3) or Vector3.new(0.3, 0.14, 0.75) }, folder)
	end
	if text then
		local gui = make("BillboardGui", { Size = UDim2.new(0, 96, 0, 22), StudsOffset = Vector3.new(0, 1.2, 0), AlwaysOnTop = true }, pieces[1])
		local label = make("TextLabel", { Size = UDim2.new(1, 0, 1, 0), BackgroundColor3 = color, BackgroundTransparency = 0.1, Text = text,
			TextColor3 = C.cream, Font = Enum.Font.GothamBold, TextScaled = true }, gui)
		corner(label, 6)
	end
	return pieces
end
local function aimArrow(pieces, tip, dir)
	local look = CFrame.lookAt(tip, tip + dir)
	pieces[1].CFrame = look * CFrame.new(0, 0, 0.85)
	pieces[2].CFrame = look * CFrame.Angles(0, math.rad(140), 0) * CFrame.new(0, 0, -0.3)
	pieces[3].CFrame = look * CFrame.Angles(0, math.rad(-140), 0) * CFrame.new(0, 0, -0.3)
end

-- ---------------------------------------------------------------- belt lines
-- Belts are laid as whole lines: first cell, last cell, and the line runs between them (one corner
-- at most, the corner belt takes the goods in from its side).  Mouse: press on the first cell, drag,
-- release.  Touch: tap the first cell, tap the last cell (tap again to move it), then ✓.
-- ⟳ reverses the flow of a line (a single belt turns), X drops the line (or leaves building).
local function lineCapable(id) local def = Machines[id] return def and def.kind == "belt" and id ~= "belt_turn" end
local Line = { start = nil, flip = false, pool = {}, folder = nil, label = nil, plan = nil, hover = nil }
local function cellAt(s, hit)
	local cs = Config.cellSize
	local half = s.workshop.cells * cs / 2
	return { gx = math.floor((hit.Position.X - s.room.x + half) / cs), gz = math.floor((hit.Position.Z - s.room.z + half) / cs),
		floor = hit.Instance:GetAttribute("ArcaneFloor") }
end
clearLine = function()
	if Line.folder then Line.folder:Destroy() end
	for _, group in pairs(Line.groups or {}) do group:Destroy() end
	Line.folder, Line.pool, Line.label, Line.plan, Line.start, Line.flip, Line.groups = nil, {}, nil, nil, nil, false, nil
end
-- holograms of the belts of a line: free cells glow white, taken ones red
local function lineGroups()
	if not Line.groups then
		Line.groups = { ok = Hologram.group("ArcaneLineGhost", Hologram.WHITE), bad = Hologram.group("ArcaneLineGhostBlocked", Hologram.RED) }
	end
	return Line.groups
end
local function lineGhost(i)
	local g = Line.pool[i]
	if g then return g end
	if not Line.folder then Line.folder = make("Folder", { Name = "ArcaneLineArrows" }, workspace) end
	local body = Hologram.body(Build.machine)
	body.part.Parent = lineGroups().ok
	local box = body.part
	local arrow = {}
	for k = 1, 3 do
		arrow[k] = make("Part", { Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = false,
			Material = Enum.Material.SmoothPlastic, Color = C.cream, Size = (k == 1) and Vector3.new(0.22, 0.1, 0.9) or Vector3.new(0.22, 0.1, 0.55) }, Line.folder)
	end
	g = { box = box, body = body, arrow = arrow }
	Line.pool[i] = g
	return g
end
-- what the line connects to: text for the label, and whether the end really feeds something
local function connections(s, plan)
	local ents = s.workshop.entities
	local function at(floor, x, z)
		for _, e in ipairs(ents) do
			local def = Machines[e.machine]
			if e.floor == floor and def.layer ~= "pipe" then
				local w, d = Grid.size(def, e.rot)
				if x >= e.gx and x < e.gx + w and z >= e.gz and z < e.gz + d then return e, def end
			end
		end
	end
	local first, last = plan.cells[1], plan.cells[#plan.cells]
	local floor = plan.floor
	local text = {}
	-- end: the cell the last belt hands to
	local nx, nz = last.gx + Grid.DX[last.rot], last.gz + Grid.DZ[last.rot]
	local e, def = at(floor, nx, nz)
	if e then
		if def.kind == "crate" or def.kind == "shelf" then
			text[#text + 1] = "→ " .. def.name
		elseif Ports.isMachine(def) then
			local inSide = e.inSide or Ports.DEFAULT_IN
			local px, pz, pdir = Ports.cell(def, e, inSide)
			if px + Grid.DX[pdir] == last.gx and pz + Grid.DZ[pdir] == last.gz and (pdir + 2) % 4 == last.rot then
				text[#text + 1] = "→ " .. def.name .. " · Einlauf ✓"
			else
				text[#text + 1] = "⚠ " .. def.name .. ": hier ist kein Einlauf"
			end
		elseif def.category == "transport" then
			text[#text + 1] = "→ " .. def.name
		end
	end
	-- start: something that feeds the first belt
	for _, o in ipairs(ents) do
		local odef = Machines[o.machine]
		if o.floor == floor and Ports.isMachine(odef) then
			local _, outSide = Ports.sides(odef, o)
			local px, pz, pdir = Ports.cell(odef, o, outSide)
			if px + Grid.DX[pdir] == first.gx and pz + Grid.DZ[pdir] == first.gz then
				table.insert(text, 1, "← " .. odef.name .. " · Auslauf")
			end
		elseif o.floor == floor and odef.kind == "hopper" then
			local f = o.rot % 4
			if o.gx + Grid.DX[f] == first.gx and o.gz + Grid.DZ[f] == first.gz then table.insert(text, 1, "← " .. odef.name) end
		end
	end
	return table.concat(text, "\n")
end
local function lineFrame(s)
	local hit = floorUnder(pointerPosition())
	if not hit then return end
	local cell = cellAt(s, hit)
	Line.hover = cell
	local start = Line.start or cell
	local cells = BeltPath.cells(start.gx, start.gz, cell.gx, cell.gz, Build.rot, Line.flip)
	if not cells then return end
	local plan = { floor = start.floor, cells = cells }
	Line.plan = plan
	local cs = Config.cellSize
	local half = s.workshop.cells * cs / 2
	local floorY = s.room.y + (plan.floor - 1) * Config.floorHeight
	local taken = {}
	for _, e in ipairs(s.workshop.entities) do
		local def = Machines[e.machine]
		if e.floor == plan.floor and def.layer ~= "pipe" then
			for _, c in ipairs(Grid.cells(def, e.gx, e.gz, e.rot)) do taken[c[1] .. ":" .. c[2]] = true end
		end
	end
	local blocked = 0
	for i, c in ipairs(cells) do
		local g = lineGhost(i)
		local bad = c.gx < 0 or c.gz < 0 or c.gx >= s.workshop.cells or c.gz >= s.workshop.cells or taken[c.gx .. ":" .. c.gz]
			or BeltPath.reserved(s.workshop.cells, Config.door.width, Config.door.depth, plan.floor, c.gx, c.gz)
		if bad then blocked = blocked + 1 end
		local centre = Vector3.new(s.room.x - half + (c.gx + 0.5) * cs, floorY + 0.35, s.room.z - half + (c.gz + 0.5) * cs)
		-- the belt model where and how it will sit
		Hologram.place(g.body, { gx = c.gx, gz = c.gz, floor = plan.floor, rot = c.rot }, Hologram.cellCenter(s.room, s.workshop.cells))
		local group = bad and lineGroups().bad or lineGroups().ok
		if g.box.Parent ~= group then g.box.Parent = group end
		g.box.Color, g.box.Transparency = bad and Hologram.RED or Hologram.WHITE, 0.15
		local dir = Vector3.new(Grid.DX[c.rot], 0, Grid.DZ[c.rot])
		local tip = centre + Vector3.new(0, 0.4, 0) + dir * 0.55
		local look = CFrame.lookAt(tip, tip + dir)
		g.arrow[1].CFrame = look * CFrame.new(0, 0, 0.5)
		g.arrow[2].CFrame = look * CFrame.Angles(0, math.rad(140), 0) * CFrame.new(0, 0, -0.22)
		g.arrow[3].CFrame = look * CFrame.Angles(0, math.rad(-140), 0) * CFrame.new(0, 0, -0.22)
		for _, a in ipairs(g.arrow) do a.Transparency = 0 end
	end
	for i = #cells + 1, #Line.pool do
		local g = Line.pool[i]
		g.box.Parent = nil                           -- unused holograms stay out of the glowing groups
		for _, a in ipairs(g.arrow) do a.Transparency = 1 end
	end
	-- label over the last belt: count, price, what it connects
	local last = Line.pool[#cells].box
	if not last.Parent then last.Parent = lineGroups().ok end
	if not Line.label then
		Line.label = make("BillboardGui", { Size = UDim2.new(0, 230, 0, 64), StudsOffset = Vector3.new(0, 3, 0), AlwaysOnTop = true }, last)
		local t = make("TextLabel", { Name = "Text", Size = UDim2.new(1, 0, 1, 0), BackgroundColor3 = C.ink, BackgroundTransparency = 0.15,
			TextColor3 = C.cream, Font = Enum.Font.GothamBold, TextScaled = true, Text = "" }, Line.label)
		corner(t, 8)
		make("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8), PaddingTop = UDim.new(0, 4), PaddingBottom = UDim.new(0, 4) }, t)
	end
	Line.label.Adornee, Line.label.Parent = last, last
	local cost = #cells * Machines[Build.machine].cost
	local head = string.format("%d %s · %d Münzen", #cells, #cells == 1 and "Band" or "Bänder", cost)
	if blocked > 0 then head = head .. " · " .. blocked .. " blockiert" end
	if cost > s.wallet then head = head .. " · zu teuer" end
	local info = connections(s, plan)
	Line.label.Text.Text = (info ~= "") and (head .. "\n" .. info) or head
	Line.label.Text.TextColor3 = (blocked > 0 or cost > s.wallet) and Color3.fromRGB(255, 190, 170) or C.cream
end
local function placeLine()
	local plan = Line.plan
	if not (Build.machine and plan) then return end
	local result = send("PlaceBelts", { machine = Build.machine, floor = plan.floor, cells = plan.cells })
	if result.ok then
		toast(#plan.cells == 1 and "Band gebaut" or (#plan.cells .. " Bänder gebaut"), C.ok)
		Line.start, Line.flip = nil, false
	elseif result.payload and result.payload.index then
		toast("Band " .. result.payload.index .. " der Strecke ist blockiert", C.bad)
	end
end
onRotate = function()
	if Build.machine and lineCapable(Build.machine) and Line.start then Line.flip = not Line.flip
	else Build.rot = (Build.rot + 1) % 4 end
end
onConfirm = function()
	if Build.machine and lineCapable(Build.machine) then placeLine() else placeGhost() end
end
onCancel = function()
	if Line.start then Line.start, Line.flip = nil, false else clearLine() stopBuild() end
end
UserInputService.TouchTapInWorld:Connect(function(position, processed)
	if not Build.machine or processed then return end
	Build.pointer = position
	-- belts: the first tap fixes the start of the line, every further tap moves its end
	if lineCapable(Build.machine) and not Line.start then
		local s = Net.snapshot
		local hit = s and s.workshop and s.room and floorUnder(position)
		if hit then Line.start = cellAt(s, hit) end
	end
end)

RunService.RenderStepped:Connect(function()
	local s = Net.snapshot
	if not (Build.machine and s and s.workshop and s.room) then
		if Build.machine or Build.ghost then stopBuild() end
		if Line.folder then clearLine() end
		return
	end
	confirm.Visible = true
	-- grid on the floor that is being built on
	local gridFloor = (Line.start and Line.start.floor) or (Line.hover and Line.hover.floor) or (Build.cell and Build.cell.floor) or 1
	local key = s.room.x .. ":" .. s.room.z .. ":" .. s.workshop.cells .. ":" .. gridFloor
	if Build.gridKey ~= key then
		dropGrid()
		Build.grid, Build.gridKey = Hologram.grid(s.room, s.workshop.cells, gridFloor), key
	end
	if lineCapable(Build.machine) then
		if Build.ghost then dropGhost() end
		lineFrame(s)
		return
	elseif Line.folder then
		clearLine()
	end
	local hit = floorUnder(pointerPosition())
	if not hit then return end
	local def = Machines[Build.machine]
	local w, d = Grid.size(def, Build.rot)
	local cs = Config.cellSize
	local half = s.workshop.cells * cs / 2
	local gx = math.floor((hit.Position.X - s.room.x + half) / cs)
	local gz = math.floor((hit.Position.Z - s.room.z + half) / cs)
	local floor = hit.Instance:GetAttribute("ArcaneFloor")
	Build.cell = { gx = gx, gz = gz, floor = floor }
	if not Build.ghost or Build.ghostFor ~= Build.machine then
		dropGhost()
		-- the real model of the part, in white
		Build.ghost = Hologram.group("ArcaneBuildGhost", Hologram.WHITE)
		Build.body = Hologram.body(Build.machine)
		Build.body.part.Parent = Build.ghost
		Build.plate = Hologram.plate()
		Build.plate.Parent = Build.ghost
		Build.ghostFor, Build.arrows, Build.blocked = Build.machine, {}, false
		if Ports.isMachine(def) then
			Build.arrows.inlet = ghostArrow("In", GHOST_IN, "Einlauf")
			Build.arrows.outlet = ghostArrow("Out", GHOST_OUT, "Auslauf")
		elseif def.category == "transport" and def.layer ~= "pipe" then
			Build.arrows.flow = ghostArrow("Flow", GHOST_OUT, nil)
		end
	end
	local floorY = s.room.y + (floor - 1) * Config.floorHeight
	local function cellCentre(x, z)
		return Vector3.new(s.room.x - half + (x + 0.5) * cs, floorY, s.room.z - half + (z + 0.5) * cs)
	end
	-- exactly where the built part would sit (same rule as the server), then a short glide there
	local centerOf = Hologram.cellCenter(s.room, s.workshop.cells)
	local target = { gx = gx, gz = gz, rot = Build.rot, floor = floor }
	Hologram.place(Build.body, target, centerOf)
	Hologram.placePlate(Build.plate, Build.machine, target, centerOf)
	local goal = Build.body.part.Position
	Build.shown = Build.shown and Build.shown:Lerp(goal, 0.35) or goal
	local shift = Build.shown - goal
	if shift.Magnitude > 0.001 then
		Build.body.part.CFrame = Build.body.part.CFrame + shift
		Build.plate.CFrame = Build.plate.CFrame + shift
	end
	local ghostEntity = { gx = gx, gz = gz, rot = Build.rot, floor = floor }
	if Build.arrows.inlet then
		-- a new machine starts with the definition's sides: inlet at the back, outlet at the front
		for key, side in pairs({ inlet = Ports.DEFAULT_IN, outlet = Ports.DEFAULT_OUT }) do
			local x, z, dir = Ports.cell(def, ghostEntity, side)
			local out = Vector3.new(Grid.DX[dir], 0, Grid.DZ[dir])
			local at = cellCentre(x, z) + out * cs + Vector3.new(0, 0.2, 0)
			if key == "inlet" then aimArrow(Build.arrows.inlet, at - out * 0.75, -out)
			else aimArrow(Build.arrows.outlet, at + out * 0.75, out) end
		end
	elseif Build.arrows.flow then
		-- the arrow points where goods will actually leave this part
		local outDir = Build.rot % 4
		for _, p in ipairs(def.ports or {}) do
			if p.mode == "out" then outDir = (p.dir + Build.rot) % 4 break end
		end
		local flow = Vector3.new(Grid.DX[outDir], 0, Grid.DZ[outDir])
		aimArrow(Build.arrows.flow, cellCentre(gx, gz) + Vector3.new(0, 3.1, 0) + flow * 0.7, flow)
	end
	-- red when the cells are taken or outside (the server decides in the end)
	local blocked = gx < 0 or gz < 0 or gx + w > s.workshop.cells or gz + d > s.workshop.cells
	for _, e in ipairs(s.workshop.entities) do
		local ew, ed = Grid.size(Machines[e.machine], e.rot)
		if e.floor == floor and Machines[e.machine].layer == def.layer and gx < e.gx + ew and e.gx < gx + w and gz < e.gz + ed and e.gz < gz + d then
			blocked = true
		end
	end
	if blocked ~= Build.blocked then
		Build.blocked = blocked
		Hologram.tint(Build.ghost, blocked and Hologram.RED or Hologram.WHITE)
	end
end)
UserInputService.InputBegan:Connect(function(input, processed)
	if processed or not Build.machine then return end
	if input.KeyCode == Enum.KeyCode.R then onRotate()
	elseif input.KeyCode == Enum.KeyCode.Escape or input.KeyCode == Enum.KeyCode.X then onCancel()
	elseif input.KeyCode == Enum.KeyCode.Return then onConfirm()
	elseif input.UserInputType == Enum.UserInputType.MouseButton1 then
		if lineCapable(Build.machine) then Line.start = Line.hover          -- press: first cell of the line
		else placeGhost() end
	end
end)
UserInputService.InputEnded:Connect(function(input)
	-- release: last cell; the line is built at once
	if input.UserInputType == Enum.UserInputType.MouseButton1 and Build.machine and lineCapable(Build.machine) and Line.start then
		placeLine()
		Line.start = nil
	end
end)

-- ---------------------------------------------------------------- prompts, snapshots, notifications
machineWindow = MachineWindow.create({ gui = gui, make = make, corner = corner, send = send, toast = toast, Net = Net,
	onClose = function() showPortMarks(Build.machine ~= nil) end })
ProximityPromptService.PromptTriggered:Connect(function(prompt)
	local uid = prompt.Parent and prompt.Parent:GetAttribute("ArcaneUid")
	if not uid then return end
	local def = Machines[prompt.Parent:GetAttribute("ArcaneMachine")]
	if Ports.isMachine(def) then
		closePanel()
		machineWindow.open(uid)
		showPortMarks(true)
	else
		selectedUid = uid
		open("machine", def.name, renderStorage)
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
	machineWindow.update(s)
end)
Net.send("RequestSnapshot")
