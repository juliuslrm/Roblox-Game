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
local Config, Locations, Protocol, Items = D.Config, D.Locations, D.Protocol, D.Items

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

local function groundPosition(a)
	local p = origin * Vector3.new(a.x, a.y or 0, a.z)
	local hit = workspace:Raycast(p + Vector3.new(0, 200, 0), Vector3.new(0, -500, 0))
	return hit and hit.Position or p
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
local function marker(name, position, color, actionText, objectText, onTrigger)
	local p = Instance.new("Part")
	p.Name, p.Anchored, p.CanCollide, p.Shape = name, true, false, Enum.PartType.Cylinder
	p.Size, p.Color, p.Material, p.Transparency = Vector3.new(0.4, 5, 5), color, Enum.Material.Neon, 0.35
	p.CFrame = CFrame.new(position + Vector3.new(0, 0.3, 0)) * CFrame.Angles(0, 0, math.rad(90))
	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText, prompt.ObjectText, prompt.MaxActivationDistance, prompt.RequiresLineOfSight = actionText, objectText, 12, false
	prompt.HoldDuration = 0.15
	prompt.Triggered:Connect(onTrigger)
	prompt.Parent = p
	p.Parent = markers
	return p
end
for id, a in pairs(anchors) do
	local loc = Locations.locations[id]
	if id == "workshop_door" and not walkable then
		marker("Door", groundPosition(a), Color3.fromRGB(201, 154, 60), "Betreten", loc.name, function(player)
			perform(player, "EnterWorkshop", {})
			push(player)
		end)
	else
		marker("Location_" .. id, groundPosition(a), Color3.fromRGB(127, 178, 201), "Ansprechen", loc.name, function(player)
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
for id, a in pairs(nodeAnchors) do
	local node = Locations.nodes[id]
	local m = marker("Node_" .. id, groundPosition(a), Color3.fromRGB(95, 163, 67), "Sammeln", Items[node.item].name, function(player)
		local result = perform(player, "GatherNode", { node = id })
		event:FireClient(player, "ActionResult", result)
		push(player)
	end)
	m.Size = Vector3.new(0.4, 3, 3)
end

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
local simAcc, slowAcc, saveAcc, presenceAcc = 0, 0, 0, 0
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
