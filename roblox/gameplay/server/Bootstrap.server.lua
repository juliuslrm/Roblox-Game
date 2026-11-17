-- ROBLOX ADAPTER (UNVERIFIED_IN_STUDIO): wires the pure game core to players, remotes, the village
-- and the DataStore.  Place under ServerScriptService.ArcaneServer (see default.project.json).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local DataStoreService = game:GetService("DataStoreService")

local D = require(script.Parent.Data)
local Game = require(script.Parent.Game)
local Actions = require(script.Parent.Actions)
local ProfileStore = require(script.Parent.ProfileStore)
local VillageAdapter = require(script.Parent.VillageAdapter)
local WorkshopWorld = require(script.Parent.WorkshopWorld)
local MarketWorld = require(script.Parent.MarketWorld)
local ResourceWorld = require(script.Parent.ResourceWorld)
local Config, Locations, Protocol = D.Config, D.Locations, D.Protocol

-- wait until the village (or its greybox stand-in) exists, otherwise ground raycasts hit nothing
if game:GetService("ServerScriptService"):FindFirstChild("VillageAutoBuild") then
	local waited = 0
	while not workspace:GetAttribute("VillageReady") and waited < 180 do
		waited = waited + task.wait(0.25)
	end
end

do
	local errors = D.Validator.run(D)
	for _, e in ipairs(errors) do warn("[Arcane] data error: " .. e) end
end

-- ---- village anchors (the village itself is built by VillageWorldBuilder, independently) ----
local origin = workspace:GetAttribute("VillageOrigin")
if typeof(origin) ~= "CFrame" then origin = CFrame.new() end
local layout
do
	local folder = ServerStorage:FindFirstChild("VillageWorld")
	local module = folder and folder:FindFirstChild("WorldLayout")
	if module then
		local ok, result = pcall(require, module)
		if ok then layout = result else warn("[Arcane] WorldLayout failed to load: " .. tostring(result)) end
	end
end
local anchors, nodeAnchors = {}, {}
if layout then
	local missing
	anchors, nodeAnchors, missing = VillageAdapter.computeAnchors(layout)
	for _, id in ipairs(missing) do warn("[Arcane] location without building: " .. id) end
else
	warn("[Arcane] ServerStorage.VillageWorld.WorldLayout not found - village services are disabled")
end

-- Ground height under a village-local point.  Taken from the height map of the level plan, not from
-- a ray: at server start the ground meshes still have their coarse default collision, and rays
-- put objects up to 2.8 studs too high (measured in the place).  Without a height map (plain test
-- place) a ray is the fallback.
local heightAt
do
	local worldFolder = ServerStorage:FindFirstChild("VillageWorld")
	local hmModule = worldFolder and worldFolder:FindFirstChild("WorldHeightmap")
	local tbModule = worldFolder and worldFolder:FindFirstChild("VillageTerrainBuilder")
	if hmModule and tbModule then
		local hm = require(hmModule)
		local heights = require(tbModule).decodeHeights(hm)
		local n, cell = hm.verticesPerSide, hm.cell
		heightAt = function(x, z)
			local fx = math.clamp((x - hm.originX) / cell, 0, n - 1.001)
			local fz = math.clamp((hm.originZ - z) / cell, 0, n - 1.001)
			local i, j = math.floor(fx), math.floor(fz)
			local u, v = fx - i, fz - j
			local h00, h10 = heights[j * n + i + 1], heights[j * n + i + 2]
			local h01, h11 = heights[(j + 1) * n + i + 1], heights[(j + 1) * n + i + 2]
			return (h00 * (1 - u) + h10 * u) * (1 - v) + (h01 * (1 - u) + h11 * u) * v
		end
	end
end
local function groundPosition(a)
	if heightAt then return origin * Vector3.new(a.x, heightAt(a.x, a.z) + 0.1, a.z) end
	local p = origin * Vector3.new(a.x, a.y or 0, a.z)
	local hit = workspace:Raycast(p + Vector3.new(0, 200, 0), Vector3.new(0, -500, 0))
	return hit and hit.Position or p
end
-- Like groundPosition, but on top of the bridge or the dock where one of them is above the point
-- (places and water sources there would otherwise end up in the stream).
local decks
local function standPosition(a)
	local ground = groundPosition(a)
	if not decks then
		decks = {}
		local village = workspace:FindFirstChild("Village")
		for _, d in ipairs(village and village:GetDescendants() or {}) do
			if d:IsA("Model") and (d.Name == "bridge_stone" or d.Name == "dock") then decks[#decks + 1] = d end
		end
	end
	if #decks == 0 then return ground end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = decks
	local hit = workspace:Raycast(ground + Vector3.new(0, 60, 0), Vector3.new(0, -60, 0), params)
	return (hit and hit.Position.Y > ground.Y) and hit.Position or ground
end
-- the pure core works in village-local coordinates; convert character positions back into them
local function toLocal(position)
	local p = origin:PointToObjectSpace(position)
	return p.X, p.Z
end

local world = Game.newWorld(anchors, nodeAnchors, os.time(), D.Market.anchors(layout))
-- Walkable workshops: one open building per player on a levelled plot of the village.  Without a
-- level plan (plain test place) the old closed interiors with teleport stay in use.
local plotPositions = {}
if layout and layout.workshopPlots then
	for _, p in ipairs(layout.workshopPlots.plots) do
		plotPositions[#plotPositions + 1] = origin * Vector3.new(p[1], p[2], p[3])
	end
end
local walkable = #plotPositions > 0
local workshops = WorkshopWorld.new(workspace, ServerStorage:FindFirstChild("ArcaneAssets"), plotPositions,
	layout and layout.workshopPlots and layout.workshopPlots.half)
-- Models every client needs: the items (goods on the belts, GoodsAnimator) and the machines (white
-- hologram of the build preview).
for from, to in pairs({ ArcaneItemAssets = "ArcaneItemModels", ArcaneAssets = "ArcaneMachineModels" }) do
	local source = ServerStorage:FindFirstChild(from)
	if source and not ReplicatedStorage:FindFirstChild(to) then
		local copy = source:Clone()
		copy.Name = to
		copy.Parent = ReplicatedStorage
	end
end
if walkable then world.plotPresence = {} end

-- ---- persistence ----
local persistent, store = true, nil
do
	local ok, result = pcall(function() return DataStoreService:GetDataStore("ArcaneVillage_v1") end)
	if ok then
		store = result
	else
		persistent = false
		warn("[Arcane] DataStore unavailable (" .. tostring(result) .. ") - progress will NOT be saved in this session")
		local memory = {}
		store = { UpdateAsync = function(_, key, fn)
			local new = fn(memory[key])
			if new ~= nil then memory[key] = new end
			return new
		end }
	end
end
local profiles = ProfileStore.new({ store = store, serverId = game.JobId ~= "" and game.JobId or "studio",
	now = os.time, wait = task.wait })

-- ---- remotes ----
local request = Instance.new("RemoteFunction")
request.Name = Protocol.remoteName
request.Parent = ReplicatedStorage
local event = Instance.new("RemoteEvent")
event.Name = Protocol.eventName
event.Parent = ReplicatedStorage

local function snapshotFor(player)
	local session = world.sessions[player.UserId]
	if not session then return nil end
	local snap = Game.snapshot(world, session)
	snap.persistent = persistent
	if snap.workshop then
		local room = workshops.rooms[snap.workshop.owner]
		if room then snap.room = { x = room.origin.X, y = room.origin.Y, z = room.origin.Z } end
	end
	-- where the player's own workshop stands and where the current main quest sends him: the client
	-- shows both as signposts on screen
	local home = walkable and workshops.rooms[player.UserId]
	if home then snap.home = { x = home.origin.X, y = home.origin.Y, z = home.origin.Z } end
	local o = snap.quest and snap.quest.objective
	if o then
		local at = o.at or o.visit or (o.type == "research" and "market_hall") or nil
		if at and anchors[at] then
			local pos = groundPosition(anchors[at])
			snap.guide = { x = pos.X, y = pos.Y, z = pos.Z, label = Locations.locations[at].name }
		elseif snap.home then
			snap.guide = { x = snap.home.x, y = snap.home.y, z = snap.home.z, label = "Deine Werkstatt", home = true }
		end
	end
	return snap
end
local function push(player)
	local snap = snapshotFor(player)
	if snap then event:FireClient(player, "Snapshot", snap) end
end

local function teleport(player, cframe)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if root then character:PivotTo(cframe) end
end
local function sendHome(player)
	if walkable then return end -- nobody is locked in: leaving a plot is just walking away
	local a = anchors.workshop_door or anchors.plaza
	if a then
		teleport(player, CFrame.new(groundPosition(a) + Vector3.new(0, 4, 0)))
	elseif layout then
		teleport(player, origin * CFrame.new(layout.spawn[1], layout.spawn[2] + 4, layout.spawn[3]))
	end
end

local function perform(player, action, payload)
	local session = world.sessions[player.UserId]
	if not session then return { ok = false, code = "NOT_READY" } end
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if action == "BuyMarketOffer" and not root then return { ok = false, code = "NOT_READY" } end
	if root and (walkable or not session.rt.inWorkshop) then
		local x, z = toLocal(root.Position)
		Game.updatePosition(world, session, x, z)
	end
	local result = Actions.handle(world, session, action, payload, { now = workspace:GetServerTimeNow() })
	if result.ok and action == "EnterWorkshop" and not walkable then
		local view = Game.workshopView(world, session.rt.inWorkshop)
		local room = workshops:sync(view)
		teleport(player, workshops:spawnCFrame(room))
	elseif result.ok and action == "LeaveWorkshop" then
		sendHome(player)
	elseif result.ok and (action == "SetCoOpPermission" or action == "InviteCoOp") and payload.role == "none" then
		local guest = Players:GetPlayerByUserId(payload.user)
		if guest then sendHome(guest) end
	end
	return result
end

request.OnServerInvoke = function(player, action, payload)
	if type(action) ~= "string" then return { ok = false, code = "BAD_REQUEST" } end
	local ok, result = pcall(perform, player, action, payload)
	if not ok then
		warn("[Arcane] action " .. action .. " failed: " .. tostring(result))
		return { ok = false, code = "BAD_REQUEST" }
	end
	result.snapshot = snapshotFor(player)
	return result
end

-- ---- world markers: prompts at locations, nodes and the workshop door ----
local markers = Instance.new("Folder")
markers.Name = "ArcaneMarkers"
markers.Parent = workspace
-- A place to talk to someone: a lamp post with a name plate that always faces the camera and a
-- quiet ring on the ground.  (Replaces the glowing discs of the first version.)
local function marker(name, position, color, actionText, objectText, onTrigger)
	local folder = Instance.new("Folder")
	folder.Name = name
	local function piece(props)
		local q = Instance.new("Part")
		q.Anchored, q.CanCollide, q.CanTouch, q.CanQuery, q.CastShadow = true, false, false, false, false
		q.TopSurface, q.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
		for k, v in pairs(props) do q[k] = v end
		q.Parent = folder
		return q
	end
	local segments, radius = 14, 3.2
	for i = 1, segments do
		local angle = (i - 1) / segments * math.pi * 2
		piece({ Name = "Ring", Size = Vector3.new(0.95, 0.12, 0.3), Color = color, Material = Enum.Material.SmoothPlastic,
			Transparency = 0.25,
			CFrame = CFrame.new(position + Vector3.new(math.cos(angle) * radius, 0.08, math.sin(angle) * radius))
				* CFrame.Angles(0, -angle + math.pi / 2, 0) })
	end
	local wood = Color3.fromRGB(91, 58, 38)
	piece({ Name = "Post", Size = Vector3.new(0.45, 6.4, 0.45), Color = wood, Material = Enum.Material.Wood,
		Position = position + Vector3.new(0, 3.2, 0), CastShadow = true })
	piece({ Name = "Cap", Size = Vector3.new(0.8, 0.2, 0.8), Color = wood, Material = Enum.Material.Wood,
		Position = position + Vector3.new(0, 6.5, 0) })
	local gem = piece({ Name = "Gem", Size = Vector3.new(0.9, 0.9, 0.9), Shape = Enum.PartType.Ball, Color = color,
		Material = Enum.Material.Glass, Transparency = 0.1, Position = position + Vector3.new(0, 7.1, 0), CanQuery = true })
	local plate = Instance.new("BillboardGui")
	plate.Name, plate.Size, plate.StudsOffset = "Name", UDim2.new(0, 190, 0, 34), Vector3.new(0, 1.5, 0)
	plate.MaxDistance, plate.AlwaysOnTop = 110, false
	local text = Instance.new("TextLabel")
	text.Size, text.BackgroundColor3, text.BackgroundTransparency = UDim2.new(1, 0, 1, 0), Color3.fromRGB(241, 235, 221), 0.1
	text.TextColor3, text.Font, text.TextScaled, text.Text = Color3.fromRGB(60, 40, 28), Enum.Font.GothamBold, true, objectText
	local round = Instance.new("UICorner")
	round.CornerRadius = UDim.new(0, 8)
	round.Parent = text
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft, pad.PaddingRight, pad.PaddingTop, pad.PaddingBottom = UDim.new(0, 8), UDim.new(0, 8), UDim.new(0, 5), UDim.new(0, 5)
	pad.Parent = text
	text.Parent = plate
	plate.Parent = gem
	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText, prompt.ObjectText, prompt.MaxActivationDistance, prompt.RequiresLineOfSight = actionText, objectText, 12, false
	prompt.HoldDuration = 0.15
	prompt.Triggered:Connect(onTrigger)
	prompt.Parent = gem
	folder.Parent = markers
	return folder
end
local MARKER_COLORS = { hub = Color3.fromRGB(201, 154, 60), home = Color3.fromRGB(193, 120, 70),
	service = Color3.fromRGB(96, 150, 190), nature = Color3.fromRGB(95, 163, 110) }
for id, a in pairs(anchors) do
	local loc = Locations.locations[id]
	if id == "workshop_door" and not walkable then
		marker("Door", groundPosition(a), Color3.fromRGB(201, 154, 60), "Betreten", loc.name, function(player)
			perform(player, "EnterWorkshop", {})
			push(player)
		end)
	else
		marker("Location_" .. id, standPosition(a), MARKER_COLORS[loc.markerStyle] or MARKER_COLORS.service, "Ansprechen", loc.name, function(player)
			local session = world.sessions[player.UserId]
			if session then
				local x, z = toLocal(player.Character.HumanoidRootPart.Position)
				Game.updatePosition(world, session, x, z)
			end
			event:FireClient(player, "OpenLocation", id)
			push(player)
		end)
	end
end
-- resource nodes: a model of the resource itself, harvested through its own prompt
local resources
resources = ResourceWorld.build(workspace, nodeAnchors, origin, ServerStorage:FindFirstChild("ArcaneResourceAssets"),
	standPosition, function(player, id)
		local result = perform(player, "GatherNode", { node = id })
		event:FireClient(player, "ActionResult", result)
		push(player)
		resources:update(world.nodes)
	end)

MarketWorld.build(workspace, world.marketAnchors, origin, ServerStorage:FindFirstChild("ArcaneMarketAssets"), groundPosition,
	function(player, id)
		local session = world.sessions[player.UserId]
		local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if not session or not root or session.rt.inWorkshop then return end
		local x, z = toLocal(root.Position)
		if D.Market.near(world.marketAnchors[id], { x = x, z = z }) then
			push(player)
			event:FireClient(player, "OpenMarket", id)
		end
	end)

-- ---- players ----
local function onPlayer(player)
	local profile, status = profiles:load(player.UserId)
	local safe = profile == nil
	if safe then warn("[Arcane] profile of " .. player.Name .. " not available (" .. tostring(status) .. ") - safe mode") end
	Game.addSession(world, player.UserId, profile, safe)
	player.CharacterAdded:Connect(function()
		task.wait(0.2)
		local session = world.sessions[player.UserId]
		if session then session.rt.inWorkshop = nil end
		if layout then
			teleport(player, origin * CFrame.new(layout.spawn[1], layout.spawn[2] + 4, layout.spawn[3]))
		end
	end)
	event:FireClient(player, "Status", { status = status, persistent = persistent })
	push(player)
end
local function saveAndRemove(player, release)
	local session = world.sessions[player.UserId]
	if not session then return end
	if not session.safeMode then
		local ok, reason = profiles:save(player.UserId, session.profile, release)
		if not ok then warn("[Arcane] save failed for " .. player.Name .. ": " .. tostring(reason)) end
		if not release then event:FireClient(player, "Saved", { ok = ok, persistent = persistent }) end
	end
	if release then
		for _, guestId in ipairs(Game.removeSession(world, player.UserId)) do
			local guest = Players:GetPlayerByUserId(guestId)
			if guest then sendHome(guest) end
		end
		workshops:removeRoom(player.UserId)
		if world.plotPresence then world.plotPresence[player.UserId] = nil end
	end
end
Players.PlayerAdded:Connect(onPlayer)
for _, player in ipairs(Players:GetPlayers()) do task.spawn(onPlayer, player) end
Players.PlayerRemoving:Connect(function(player) saveAndRemove(player, true) end)
game:BindToClose(function()
	for _, player in ipairs(Players:GetPlayers()) do saveAndRemove(player, true) end
end)

-- ---- main loop: fixed simulation tick, 1 s position / snapshot / visuals, periodic autosave ----
local simAcc, slowAcc, saveAcc, presenceAcc, goodsAcc = 0, 0, 0, 0, 0
RunService.Heartbeat:Connect(function(dt)
	simAcc = simAcc + math.min(dt, 1)
	local guard = 0
	while simAcc >= Config.sim.tick and guard < 8 do
		simAcc = simAcc - Config.sim.tick
		guard = guard + 1
		Game.tick(world, Config.sim.tick, os.time())
	end
	slowAcc = slowAcc + dt
	if slowAcc >= 1 then
		slowAcc = 0
		resources:update(world.nodes)
		for _, player in ipairs(Players:GetPlayers()) do
			local session = world.sessions[player.UserId]
			local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
			if session and root then
				if walkable then
					local x, z = toLocal(root.Position)
					Game.updatePosition(world, session, x, z)
				elseif session.rt.inWorkshop then
					-- fell out of the interior? bring the player back instead of leaving him in the void
					local room = workshops.rooms[session.rt.inWorkshop]
					if room and (root.Position - room.origin).Magnitude > 400 then teleport(player, workshops:spawnCFrame(room)) end
				else
					local x, z = toLocal(root.Position)
					Game.updatePosition(world, session, x, z)
				end
			end
			if session and not session.safeMode then
				workshops:sync(Game.workshopView(world, player.UserId), "Werkstatt von " .. player.DisplayName)
			end
			push(player)
		end
	end
	-- walkable workshops: whoever stands on a plot is "in" that workshop, nobody is teleported
	presenceAcc = presenceAcc + dt
	if walkable and presenceAcc >= 0.25 then
		presenceAcc = 0
		local now = workspace:GetServerTimeNow()
		for _, player in ipairs(Players:GetPlayers()) do
			local session = world.sessions[player.UserId]
			local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
			if session and not session.safeMode then
				local owner = root and workshops:ownerAt(root.Position) or nil
				world.plotPresence[player.UserId] = owner
				local changed = false
				if session.rt.inWorkshop and session.rt.inWorkshop ~= owner then
					Actions.handle(world, session, "LeaveWorkshop", {}, { now = now })
					changed = true
				end
				-- a refused entry (no permission from the owner) is retried only every 3 seconds
				if owner and not session.rt.inWorkshop and (session.rt.enterRetry or 0) <= now then
					local result = Actions.handle(world, session, "EnterWorkshop", { owner = owner }, { now = now })
					if result.ok then changed = true else session.rt.enterRetry = now + 3 end
				end
				if changed then push(player) end
			end
		end
	end
	-- goods on the conveyors, several times a second, so clients can let them glide without stops
	goodsAcc = goodsAcc + dt
	if goodsAcc >= 0.2 then
		goodsAcc = 0
		local now = workspace:GetServerTimeNow()
		for _, player in ipairs(Players:GetPlayers()) do
			local session = world.sessions[player.UserId]
			if session and not session.safeMode then
				workshops:syncGoods(player.UserId, Game.goodsView(world, player.UserId), now)
			end
		end
	end
	saveAcc = saveAcc + dt
	if saveAcc >= Config.autosaveSec then
		saveAcc = 0
		for _, player in ipairs(Players:GetPlayers()) do task.spawn(saveAndRemove, player, false) end
	end
end)

-- exit prompts of the interiors
workspace.DescendantAdded:Connect(function(inst)
	if inst:IsA("ProximityPrompt") and inst.Parent and inst.Parent.Name == "ExitDoor" then
		inst.Triggered:Connect(function(player)
			perform(player, "LeaveWorkshop", {})
			push(player)
		end)
	end
end)
print("[Arcane] server ready - persistent saves: " .. tostring(persistent))
