-- ROBLOX CLIENT: the window of one production machine - its own little workplace.
--
--   +---------------------------------------------------------------+
--   | Kräutermühle                                   läuft      [X] |
--   | [Zutaten]        [ Motiv  ====>  Fortschritt ]     [Ergebnis] |
--   | Anschlüsse:  Draufsicht mit Einlauf / Auslauf, Automatisch    |
--   | Rezepte, Brennstoff, Drehen, Abbauen (scrollt)                |
--   +---------------------------------------------------------------+
--
-- Everything shown comes from the server snapshot of exactly this machine instance; every change
-- (filling, taking out, choosing sides) is a server action.  Only the progress bar is advanced
-- locally between two snapshots.
local RunService = game:GetService("RunService")
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("ArcaneShared")
local Items = require(Shared.Items)
local Recipes = require(Shared.Recipes)
local Machines = require(Shared.Machines)
local Research = require(Shared.Research)
local Icons = require(Shared.ItemIcons)
local Ports = require(Shared.MachinePorts)

local Window = {}

local PARCHMENT, PARCHMENT_DARK = Color3.fromRGB(241, 231, 208), Color3.fromRGB(226, 212, 182)
local WOOD, WOOD_LIGHT = Color3.fromRGB(74, 48, 32), Color3.fromRGB(122, 84, 56)
local BRASS, INK = Color3.fromRGB(201, 154, 60), Color3.fromRGB(46, 36, 30)
local OK, WARN, BAD = Color3.fromRGB(79, 138, 85), Color3.fromRGB(206, 122, 59), Color3.fromRGB(193, 67, 59)
local IN_COLOR, OUT_COLOR, FLUID_COLOR = Color3.fromRGB(63, 138, 106), Color3.fromRGB(201, 154, 60), Color3.fromRGB(96, 150, 190)

local function amountText(id, n)
	if Items[id] and Items[id].unit == "ml" then return n .. " ml" end
	return tostring(n)
end

-- Why does the machine stand still?  Concrete, in the player's words.
function Window.reason(e)
	local s = e.state
	if e.paused or s == "Paused" then return "Pausiert", WARN end
	if not e.recipe then return "Kein Rezept gewählt", WARN end
	if s == "OutputBlocked" then return "Auslauf voll", BAD end
	if s == "NoFuel" then return "Holzkohle fehlt", BAD end
	if s == "WaitingForInputs" then
		local it = e.waiting and Items[e.waiting]
		return (it and it.name or "Zutat") .. " fehlt", WARN
	end
	if s == "Running" then return "Läuft", OK end
	return "Bereit", OK
end

-- ctx: { gui, make, corner, send, toast, Net, onClose }
function Window.create(ctx)
	local make, corner, send = ctx.make, ctx.corner, ctx.send
	local self = { uid = nil, sig = nil, live = nil, mode = "out" }

	local frame = make("Frame", { Name = "MachineWindow", Size = UDim2.new(0, 480, 1, -96), Position = UDim2.new(1, -492, 0, 12),
		BackgroundColor3 = WOOD, Visible = false }, ctx.gui)
	corner(frame, 12)
	make("UIStroke", { ApplyStrokeMode = Enum.ApplyStrokeMode.Border, Color = BRASS, Thickness = 2 }, frame)
	local sheet = make("Frame", { Size = UDim2.new(1, -12, 1, -52), Position = UDim2.new(0, 6, 0, 46), BackgroundColor3 = PARCHMENT }, frame)
	corner(sheet, 8)
	local title = make("TextLabel", { Size = UDim2.new(1, -190, 0, 40), Position = UDim2.new(0, 14, 0, 3), BackgroundTransparency = 1,
		Font = Enum.Font.GothamBold, TextSize = 21, TextColor3 = PARCHMENT, TextXAlignment = Enum.TextXAlignment.Left, Text = "" }, frame)
	local chip = make("TextLabel", { Size = UDim2.new(0, 124, 0, 28), Position = UDim2.new(1, -182, 0, 9), BackgroundColor3 = OK,
		Font = Enum.Font.GothamBold, TextSize = 14, TextColor3 = PARCHMENT, Text = "" }, frame)
	corner(chip, 14)
	local close = make("TextButton", { Size = UDim2.new(0, 44, 0, 36), Position = UDim2.new(1, -50, 0, 5), BackgroundColor3 = BAD,
		Font = Enum.Font.GothamBold, TextSize = 18, TextColor3 = PARCHMENT, Text = "X" }, frame)
	corner(close, 8)

	-- fixed part: process row and connection row (never scrolls)
	local process = make("Frame", { Size = UDim2.new(1, -12, 0, 150), Position = UDim2.new(0, 6, 0, 6), BackgroundColor3 = PARCHMENT_DARK }, sheet)
	corner(process, 8)
	local portsRow = make("Frame", { Size = UDim2.new(1, -12, 0, 124), Position = UDim2.new(0, 6, 0, 162), BackgroundColor3 = PARCHMENT_DARK }, sheet)
	corner(portsRow, 8)
	local scroll = make("ScrollingFrame", { Size = UDim2.new(1, -12, 1, -298), Position = UDim2.new(0, 6, 0, 292), BackgroundTransparency = 1,
		CanvasSize = UDim2.new(0, 0, 0, 0), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 8, BorderSizePixel = 0 }, sheet)
	make("UIListLayout", { Padding = UDim.new(0, 6) }, scroll)

	local function clear(holder)
		for _, child in ipairs(holder:GetChildren()) do
			if not (child:IsA("UIListLayout") or child:IsA("UICorner")) then child:Destroy() end
		end
	end
	local function act(action, payload)
		local result = send(action, payload)
		self.sig = nil                                  -- redraw with the confirmed state
		return result
	end
	local function textButton(text, parent, size, position, color, onClick)
		local b = make("TextButton", { Text = text, Size = size, Position = position, BackgroundColor3 = color or BRASS, TextColor3 = INK,
			Font = Enum.Font.GothamBold, TextSize = 14, TextWrapped = true, AutoButtonColor = true }, parent)
		corner(b, 7)
		local busy = false
		b.Activated:Connect(function()
			if busy then return end
			busy = true
			local ok, err = pcall(onClick)
			if not ok then warn(err) end
			busy = false
		end)
		return b
	end

	-- one material slot: tile with symbol, amount and name; optional tap action
	local function slot(parent, x, y, id, line, missing, onTap)
		local icon = Icons.item(id)
		local tile = make(onTap and "TextButton" or "Frame", { Size = UDim2.new(0, 66, 0, 66), Position = UDim2.new(0, x, 0, y),
			BackgroundColor3 = Color3.fromRGB(icon.color[1], icon.color[2], icon.color[3]) }, parent)
		if onTap then tile.Text, tile.AutoButtonColor = "", true end
		corner(tile, 8)
		make("UIStroke", { ApplyStrokeMode = Enum.ApplyStrokeMode.Border, Color = missing and BAD or WOOD_LIGHT, Thickness = missing and 3 or 1.5 }, tile)
		make("TextLabel", { Size = UDim2.new(1, 0, 0, 36), Position = UDim2.new(0, 0, 0, 2), BackgroundTransparency = 1, Text = icon.symbol,
			TextSize = 28, Font = Enum.Font.GothamBold, TextColor3 = INK }, tile)
		local count = make("TextLabel", { Size = UDim2.new(1, -4, 0, 16), Position = UDim2.new(0, 2, 0, 36), BackgroundColor3 = PARCHMENT,
			BackgroundTransparency = 0.15, Text = line, TextSize = 12, Font = Enum.Font.GothamBold, TextColor3 = missing and BAD or INK,
			TextScaled = false }, tile)
		corner(count, 4)
		make("TextLabel", { Size = UDim2.new(1, 8, 0, 14), Position = UDim2.new(0, -4, 1, 1), BackgroundTransparency = 1,
			Text = Items[id] and Items[id].name or id, TextSize = 10, Font = Enum.Font.Gotham, TextColor3 = INK,
			TextTruncate = Enum.TextTruncate.AtEnd }, tile)
		if onTap then tile.Activated:Connect(onTap) end
		return tile
	end

	local function drawProcess(e, def, s)
		clear(process)
		local r = e.recipe and Recipes[e.recipe]
		make("TextLabel", { Size = UDim2.new(0, 150, 0, 16), Position = UDim2.new(0, 8, 0, 4), BackgroundTransparency = 1, Text = "Zutaten",
			Font = Enum.Font.GothamBold, TextSize = 12, TextColor3 = WOOD, TextXAlignment = Enum.TextXAlignment.Left }, process)
		make("TextLabel", { Size = UDim2.new(0, 150, 0, 16), Position = UDim2.new(1, -158, 0, 4), BackgroundTransparency = 1, Text = "Ergebnis",
			Font = Enum.Font.GothamBold, TextSize = 12, TextColor3 = WOOD, TextXAlignment = Enum.TextXAlignment.Right }, process)
		-- left: what the recipe needs and what is inside
		local inputs = {}
		if r then
			for id in pairs(r.inputs) do inputs[#inputs + 1] = id end
			table.sort(inputs)
		end
		local index = 0
		local function place(i) return 8 + (i % 2) * 72, 22 + math.floor(i / 2) * 84 end
		for _, id in ipairs(inputs) do
			local liquid = Items[id].unit == "ml"
			local have = (liquid and e.fluids[id] or e.inv[id]) or 0
			local need = r.inputs[id]
			local x, y = place(index)
			index = index + 1
			slot(process, x, y, id, amountText(id, have) .. "/" .. need, have < need, function()
				local lack = math.max(need - have, liquid and 1000 or 1)
				local inBag = s.items[id] or 0
				if inBag <= 0 then ctx.toast((Items[id].name) .. " fehlt im Beutel", BAD) return end
				act("TransferStack", { from = "inv", to = e.uid, item = id, amount = math.min(lack, inBag) })
			end)
		end
		if def.usesFuel and index < 4 then
			local need = r and r.fuelUnits or 1
			local x, y = place(index)
			slot(process, x, y, "fuel_charcoal", e.fuel .. "/" .. need, e.fuel < need, function()
				local inBag = s.items.fuel_charcoal or 0
				if inBag <= 0 then ctx.toast("Holzkohle fehlt im Beutel", BAD) return end
				act("TransferStack", { from = "inv", to = e.uid, item = "fuel_charcoal", amount = math.min(4, inBag) })
			end)
		end
		if not r then
			make("TextLabel", { Size = UDim2.new(0, 150, 0, 60), Position = UDim2.new(0, 8, 0, 40), BackgroundTransparency = 1, TextWrapped = true,
				Text = "Wähle unten ein Rezept.", Font = Enum.Font.Gotham, TextSize = 13, TextColor3 = INK }, process)
		end
		-- middle: motif, progress arrow, reason
		local mid = make("Frame", { Size = UDim2.new(0, 150, 0, 124), Position = UDim2.new(0.5, -75, 0, 18), BackgroundTransparency = 1 }, process)
		make("TextLabel", { Size = UDim2.new(1, 0, 0, 44), BackgroundTransparency = 1, Text = Icons.machine(e.machine), TextSize = 36,
			Font = Enum.Font.GothamBold, TextColor3 = INK }, mid)
		local track = make("Frame", { Size = UDim2.new(1, -26, 0, 18), Position = UDim2.new(0, 4, 0, 50), BackgroundColor3 = WOOD_LIGHT }, mid)
		corner(track, 5)
		local fill = make("Frame", { Size = UDim2.new(0, 0, 1, 0), BackgroundColor3 = BRASS }, track)
		corner(fill, 5)
		make("TextLabel", { Size = UDim2.new(0, 24, 0, 28), Position = UDim2.new(1, -24, 0, 45), BackgroundTransparency = 1, Text = "▶",
			TextSize = 22, Font = Enum.Font.GothamBold, TextColor3 = BRASS }, mid)
		local status = make("TextLabel", { Size = UDim2.new(1, 0, 0, 40), Position = UDim2.new(0, 0, 0, 74), BackgroundTransparency = 1, Text = "",
			TextWrapped = true, Font = Enum.Font.GothamBold, TextSize = 14, TextColor3 = INK }, mid)
		self.live = { fill = fill, status = status }
		-- right: finished goods in the output buffer (tap to take them out)
		local outputs, seen = {}, {}
		for id in pairs(e.out or {}) do outputs[#outputs + 1], seen[id] = id, true end
		for id in pairs(e.outFluid or {}) do outputs[#outputs + 1], seen[id] = id, true end
		if r then
			for id in pairs(r.outputs) do
				if not seen[id] then outputs[#outputs + 1] = id end
			end
		end
		table.sort(outputs)
		for i, id in ipairs(outputs) do
			if i > 4 then break end
			local n = (e.out and e.out[id]) or (e.outFluid and e.outFluid[id]) or 0
			local col, rowIndex = (i - 1) % 2, math.floor((i - 1) / 2)
			local tile = slot(process, 0, 22 + rowIndex * 84, id, amountText(id, n), false, n > 0 and function()
				act("TransferStack", { from = e.uid, to = "inv", item = id, amount = n, slot = "out" })
			end or nil)
			tile.Position = UDim2.new(1, -74 - col * 72, 0, 22 + rowIndex * 84)
		end
	end

	-- top view of the machine in its own frame: front at the bottom, like standing in front of it
	local SIDE_AT = { [0] = { 0.5, 1 }, [1] = { 1, 0.5 }, [2] = { 0.5, 0 }, [3] = { 0, 0.5 } }
	local function drawPorts(e, def)
		clear(portsRow)
		local fluid = Ports.fluidSides(def)
		make("TextLabel", { Size = UDim2.new(0, 200, 0, 16), Position = UDim2.new(0, 8, 0, 4), BackgroundTransparency = 1, Text = "Anschlüsse (Draufsicht)",
			Font = Enum.Font.GothamBold, TextSize = 12, TextColor3 = WOOD, TextXAlignment = Enum.TextXAlignment.Left }, portsRow)
		local view = make("Frame", { Size = UDim2.new(0, 96, 0, 96), Position = UDim2.new(0, 34, 0, 24), BackgroundTransparency = 1 }, portsRow)
		local body = make("Frame", { Size = UDim2.new(0, 52, 0, 52), Position = UDim2.new(0.5, -26, 0.5, -26), BackgroundColor3 = WOOD_LIGHT }, view)
		corner(body, 6)
		make("TextLabel", { Size = UDim2.new(1, 0, 1, 0), BackgroundTransparency = 1, Text = Icons.machine(e.machine), TextSize = 24,
			Font = Enum.Font.GothamBold, TextColor3 = PARCHMENT }, body)
		for side = 0, 3 do
			local at = SIDE_AT[side]
			local text, color, enabled = "", PARCHMENT, true
			if fluid[side] then
				text, color, enabled = "💧", FLUID_COLOR, false
			elseif side == e.inSide then
				text, color = "Ein", IN_COLOR
			elseif side == e.outSide then
				text, color = "Aus", OUT_COLOR
			end
			local b = make("TextButton", { Size = UDim2.new(0, 40, 0, 26), AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.new(at[1], (at[1] - 0.5) * -8, at[2], (at[2] - 0.5) * -6), BackgroundColor3 = color, Text = text,
				Font = Enum.Font.GothamBold, TextSize = 13, TextColor3 = (text == "") and INK or PARCHMENT, AutoButtonColor = enabled, Active = enabled }, view)
			corner(b, 6)
			make("UIStroke", { ApplyStrokeMode = Enum.ApplyStrokeMode.Border, Color = WOOD, Thickness = 1.5 }, b)
			if enabled then
				b.Activated:Connect(function()
					if self.mode == "in" then act("SetMachinePorts", { uid = e.uid, inSide = side })
					else act("SetMachinePorts", { uid = e.uid, outSide = side }) end
				end)
			end
		end
		make("TextLabel", { Size = UDim2.new(0, 96, 0, 12), Position = UDim2.new(0, 34, 1, -14), BackgroundTransparency = 1, Text = "Vorderseite",
			Font = Enum.Font.Gotham, TextSize = 10, TextColor3 = WOOD }, portsRow)
		-- right of the view: which connection a tap sets, and the outlet mode
		local x0 = 172
		make("TextLabel", { Size = UDim2.new(1, -x0 - 8, 0, 16), Position = UDim2.new(0, x0, 0, 6), BackgroundTransparency = 1,
			Text = "Seite antippen setzt:", Font = Enum.Font.Gotham, TextSize = 12, TextColor3 = INK, TextXAlignment = Enum.TextXAlignment.Left }, portsRow)
		local function modeButton(label, mode, x, color)
			local on = self.mode == mode
			local b = textButton(label, portsRow, UDim2.new(0, 136, 0, 30), UDim2.new(0, x, 0, 26), on and color or PARCHMENT, function()
				self.mode = mode
				self.sig = nil
			end)
			b.TextColor3 = on and PARCHMENT or INK
			make("UIStroke", { ApplyStrokeMode = Enum.ApplyStrokeMode.Border, Color = color, Thickness = 2 }, b)
		end
		modeButton("Einlauf", "in", x0, IN_COLOR)
		modeButton("Auslauf", "out", x0 + 144, OUT_COLOR)
		local auto = e.outAuto ~= false
		make("TextLabel", { Size = UDim2.new(1, -x0 - 8, 0, 32), Position = UDim2.new(0, x0, 0, 60), BackgroundTransparency = 1, TextWrapped = true,
			Text = "Einlauf " .. Ports.SIDE_NAME[e.inSide] .. " · Auslauf " .. Ports.SIDE_NAME[e.outSide] .. "\nAuslauf: "
				.. (auto and "Automatisch (folgt dem Band)" or "Manuell (fest)"),
			Font = Enum.Font.GothamMedium, TextSize = 12, TextColor3 = INK, TextXAlignment = Enum.TextXAlignment.Left }, portsRow)
		local b = textButton(auto and "Automatisch ✓" or "Automatisch", portsRow, UDim2.new(0, 136, 0, 26), UDim2.new(0, x0, 0, 94),
			auto and OK or BRASS, function()
				if not auto then act("SetMachinePorts", { uid = e.uid, auto = true }) end
			end)
		b.TextColor3 = auto and PARCHMENT or INK
		if next(fluid) then
			make("TextLabel", { Size = UDim2.new(0, 140, 0, 26), Position = UDim2.new(0, x0 + 144, 0, 94), BackgroundTransparency = 1, TextWrapped = true,
				Text = "💧 Rohranschluss, fest", Font = Enum.Font.Gotham, TextSize = 11, TextColor3 = FLUID_COLOR,
				TextXAlignment = Enum.TextXAlignment.Left }, portsRow)
		end
	end

	local function listRow(text, actionText, onClick, color)
		local f = make("Frame", { Size = UDim2.new(1, -10, 0, 44), BackgroundColor3 = PARCHMENT_DARK, AutomaticSize = Enum.AutomaticSize.Y }, scroll)
		corner(f, 6)
		make("TextLabel", { Text = text, Size = UDim2.new(1, actionText and -128 or -14, 0, 40), Position = UDim2.new(0, 8, 0, 2),
			BackgroundTransparency = 1, TextColor3 = color or INK, Font = Enum.Font.Gotham, TextSize = 13, TextWrapped = true,
			TextXAlignment = Enum.TextXAlignment.Left, AutomaticSize = Enum.AutomaticSize.Y }, f)
		if actionText then textButton(actionText, f, UDim2.new(0, 112, 0, 36), UDim2.new(1, -118, 0, 4), nil, onClick) end
	end
	local function heading(text)
		make("TextLabel", { Text = text, Size = UDim2.new(1, -10, 0, 20), BackgroundTransparency = 1, TextColor3 = WOOD,
			Font = Enum.Font.GothamBold, TextSize = 13, TextXAlignment = Enum.TextXAlignment.Left }, scroll)
	end
	local function itemList(map)
		local parts = {}
		for id, n in pairs(map or {}) do
			parts[#parts + 1] = amountText(id, n) .. (Items[id].unit == "ml" and " " or " × ") .. Items[id].name
		end
		table.sort(parts)
		return table.concat(parts, ", ")
	end
	local function drawList(e, def, s)
		local keep = scroll.CanvasPosition
		clear(scroll)
		heading("Rezepte")
		local ids = {}
		for id, r in pairs(Recipes) do if r.machineId == e.machine then ids[#ids + 1] = id end end
		table.sort(ids)
		for _, id in ipairs(ids) do
			local r = Recipes[id]
			local line = itemList(r.inputs) .. "  →  " .. itemList(r.outputs) .. "  (" .. r.durationSec .. " s)"
			if not s.research[r.requiredResearch] then
				listRow("🔒 " .. line .. "\nForschung: " .. Research[r.requiredResearch].name, nil, nil, Color3.fromRGB(138, 127, 115))
			else
				listRow(((e.recipe == id) and "● " or "") .. line, "Herstellen", function()
					act("StartManualCraft", { uid = e.uid, recipe = id })
				end)
			end
		end
		heading("Maschine")
		listRow(e.paused and "Die Maschine ist pausiert." or "Die Maschine arbeitet, sobald Zutaten da sind.", e.paused and "Fortsetzen" or "Pause",
			function() act("ToggleMachine", { uid = e.uid }) end)
		listRow("Drehen (90°) – Ein- und Auslauf drehen sich mit", "Drehen", function() act("RotateMachine", { uid = e.uid }) end)
		listRow("Abbauen – Inhalt kommt in den Beutel, 60 % der Kosten zurück", "Abbauen", function()
			if act("RemoveMachine", { uid = e.uid }).ok then self.close() end
		end, BAD)
		if e.machine == "kettle" then
			listRow("Experiment: 1 Kraut + 1000 ml Wasser → +3 Wissen (max. 5 pro Tag)", "Forschen", function() act("Experiment", { uid = e.uid }) end)
		end
		task.defer(function() scroll.CanvasPosition = keep end)
	end

	local function find(s)
		for _, e in ipairs(s and s.workshop and s.workshop.entities or {}) do
			if e.uid == self.uid then return e end
		end
		return nil
	end
	-- fingerprint of everything drawn statically (progress is animated separately)
	local function signature(e, s)
		local parts = { e.machine, tostring(e.recipe), tostring(e.state), tostring(e.waiting), tostring(e.paused), e.fuel or 0,
			tostring(e.inSide), tostring(e.outSide), tostring(e.outAuto), e.rot, self.mode }
		for _, store in ipairs({ e.inv or {}, e.fluids or {}, e.out or {}, e.outFluid or {} }) do
			local ids = {}
			for id in pairs(store) do ids[#ids + 1] = id end
			table.sort(ids)
			for _, id in ipairs(ids) do parts[#parts + 1] = id .. "=" .. store[id] end
			parts[#parts + 1] = "/"
		end
		local r = e.recipe and Recipes[e.recipe]
		if r then for id in pairs(r.inputs) do parts[#parts + 1] = id .. ":" .. (s.items[id] or 0) end end
		local n = 0
		for _ in pairs(s.research) do n = n + 1 end
		parts[#parts + 1] = n
		for i = 1, #parts do parts[i] = tostring(parts[i]) end
		return table.concat(parts, "|")
	end

	function self.isOpen() return frame.Visible end
	function self.close()
		if not frame.Visible then return end
		frame.Visible = false
		self.uid, self.sig, self.live, self.job = nil, nil, nil, nil
		if ctx.onClose then ctx.onClose() end
	end
	close.Activated:Connect(self.close)

	-- called with every snapshot and after own actions
	function self.update(s)
		if not frame.Visible then return end
		local e = find(s)
		if not e then
			-- left the workshop or the machine was removed by someone else
			self.close()
			return
		end
		local def = Machines[e.machine]
		title.Text = def.name
		local text, color = Window.reason(e)
		chip.Text, chip.BackgroundColor3 = text, color
		-- progress as confirmed by the server, stamped with the local time it arrived
		self.job = e.job and { remaining = e.job.remaining, total = e.job.total, at = os.clock(), running = e.state == "Running" } or nil
		self.reason, self.reasonColor = text, color
		local sig = signature(e, s)
		if sig ~= self.sig then
			self.sig = sig
			drawProcess(e, def, s)
			drawPorts(e, def)
			drawList(e, def, s)
		end
	end

	function self.open(uid)
		self.uid, self.sig, self.mode = uid, nil, "out"
		frame.Visible = true
		scroll.CanvasPosition = Vector2.new(0, 0)
		self.update(ctx.Net.snapshot)
	end

	-- smooth progress between two confirmed updates
	RunService.RenderStepped:Connect(function()
		if not (frame.Visible and self.live) then return end
		if self.sig == nil and ctx.Net.snapshot then self.update(ctx.Net.snapshot) end
		local live, job = self.live, self.job
		if not live or not live.fill.Parent then return end
		if job and job.total > 0 then
			local remaining = job.remaining
			if job.running then remaining = math.max(0, remaining - (os.clock() - job.at)) end
			live.fill.Size = UDim2.new(math.clamp(1 - remaining / job.total, 0, 1), 0, 1, 0)
			if job.running then
				live.status.Text = string.format("Läuft · noch %d s", math.ceil(remaining))
				live.status.TextColor3 = OK
			else
				live.status.Text, live.status.TextColor3 = self.reason or "", self.reasonColor or INK
			end
		else
			live.fill.Size = UDim2.new(0, 0, 1, 0)
			live.status.Text, live.status.TextColor3 = self.reason or "", self.reasonColor or INK
		end
	end)

	return self
end

return Window
