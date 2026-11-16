-- SNAPSHOT for scripts/roblox_exec.py: embeds copies of roblox/VillageAutoBuild.server.lua and
-- roblox/gameplay/server/Bootstrap.server.lua (state of 2026-11-16). Re-embed them after changes.
-- Runs both server start scripts inside the place and reports what exists afterwards.
local __errors = {}
local function __run(name, fn)
	task.spawn(function()
		local ok, err = xpcall(fn, function(e) return tostring(e) .. "\n" .. debug.traceback() end)
		if not ok then __errors[#__errors + 1] = name .. ": " .. tostring(err) end
	end)
end
__run("VillageAutoBuild", function()
	local script = game:GetService("ServerScriptService").VillageAutoBuild
-- Runs VillageAutoBuild once when the server starts (UNVERIFIED_IN_STUDIO).
-- Characters are held back until the ground exists, so nobody falls into the void.
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")
local folder = ServerStorage:WaitForChild("VillageWorld")

Players.CharacterAutoLoads = false
local ok, err = pcall(function()
	local Auto = require(folder:WaitForChild("VillageAutoBuild"))
	-- Fetch the uploaded model libraries; without them the village is built from placeholder blocks.
	local loadOk, loaded = pcall(function()
		return require(folder:WaitForChild("VillageAssetLoader")).load({
			ids = require(folder:WaitForChild("VillageAssetIds")),
			insertService = game:GetService("InsertService"),
			parent = ServerStorage,
		})
	end)
	if loadOk then
		print(string.format("[Village] assets: %d libraries loaded, %d failed, %d mesh parts, %d retextured",
			loaded.loaded, #loaded.failed, loaded.meshParts, loaded.retextured))
		for _, message in ipairs(loaded.failed) do warn("[Village] asset load failed: " .. message) end
	else
		warn("[Village] asset loader failed: " .. tostring(loaded))
	end
	local origin = workspace:GetAttribute("VillageOrigin")
	if typeof(origin) ~= "CFrame" then origin = CFrame.new() end
	local facade = folder:FindFirstChild("WorkshopFacade")
	local layout = require(folder:WaitForChild("WorldLayout"))
	local builder = require(folder:WaitForChild("VillageWorldBuilder"))
	-- Use the meshes only if their names match the level plan; otherwise say what arrived and
	-- fall back to placeholder blocks instead of building an empty world.
	local templates = ServerStorage:FindFirstChild("VillageAssets")
	if templates then
		local found, missing = builder.checkTemplates(templates, layout)
		print(string.format("[Village] templates: %d found, %d missing", #found, #missing))
		if #found == 0 then
			local names = {}
			for _, d in ipairs(templates:GetDescendants()) do
				if #names >= 20 then break end
				names[#names + 1] = d.ClassName .. ":" .. d.Name
			end
			warn("[Village] no template name matches the level plan. First instances: " .. table.concat(names, ", "))
			templates = nil
		end
	end
	local report = Auto.run({
		layout = layout,
		heightmap = require(folder:WaitForChild("WorldHeightmap")),
		workshopFacade = facade and require(facade),
		builder = builder,
		terrainBuilder = require(folder:WaitForChild("VillageTerrainBuilder")),
		templates = templates,
		-- The time of day is fixed to the afternoon; 76 lantern and window lights on top of the
		-- sunlight made the village glow.  Switch back on once there is a day/night cycle.
		createLights = false,
		origin = origin,
	})
	if layout.lighting then builder.applyLighting(layout.lighting) end
	print(string.format("[Village] built in mode '%s': %d objects placed, %d missing, %d terrain cells",
		report.mode, report.placed, report.missing, report.terrainCells))
	if report.mode == "greybox" then
		print("[Village] No meshes in ServerStorage.VillageAssets - showing placeholder blocks. See docs/ROBLOX_IMPORT.md.")
	elseif #report.missingTerrain > 0 then
		warn("[Village] Using voxel terrain. Missing or empty terrain templates: " .. table.concat(report.missingTerrain, ", "))
	end
	for _, message in ipairs(report.warnings) do
		warn("[Village] " .. message)
	end
	local precise = {}
	for name in pairs(report.needsPreciseCollision) do
		precise[#precise + 1] = name
	end
	if #precise > 0 then
		table.sort(precise)
		warn("[Village] Check CollisionFidelity in Studio for: " .. table.concat(precise, ", "))
	end
end)
if not ok then warn("[Village] auto build failed: " .. tostring(err)) end
workspace:SetAttribute("VillageReady", true)
-- Exact ground collision takes about a minute; do it while people already play.
task.spawn(function()
	local village = workspace:FindFirstChild("Village")
	if not village or not village:FindFirstChild("terrain") then return end
	local okRefine, converted, failed, lastError = pcall(function()
		return require(folder:WaitForChild("VillageAutoBuild")).refineCollision(village, game:GetService("AssetService"))
	end)
	if okRefine then
		print(string.format("[Village] precise ground collision: %d parts converted, %d failed %s", converted, failed, tostring(lastError or "")))
	else
		warn("[Village] precise ground collision failed: " .. tostring(converted))
	end
end)
Players.CharacterAutoLoads = true
for _, player in ipairs(Players:GetPlayers()) do
	task.spawn(function() player:LoadCharacter() end)
end
Players.PlayerAdded:Connect(function(player)
	if not player.Character then player:LoadCharacter() end
end)

end)
local __t = os.clock()
while not workspace:GetAttribute("VillageReady") and os.clock() - __t < 60 do task.wait(0.5) end
__run("Bootstrap", function()
	local script = game:GetService("ServerScriptService").ArcaneServer.Bootstrap
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
local workshops = WorkshopWorld.new(workspace, ServerStorage:FindFirstChild("ArcaneAssets"))

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
	if root and not session.rt.inWorkshop then
		local x, z = toLocal(root.Position)
		Game.updatePosition(world, session, x, z)
	end
	local result = Actions.handle(world, session, action, payload, { now = workspace:GetServerTimeNow() })
	if result.ok and action == "EnterWorkshop" then
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
	if id == "workshop_door" then
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
	end
end
Players.PlayerAdded:Connect(onPlayer)
for _, player in ipairs(Players:GetPlayers()) do task.spawn(onPlayer, player) end
Players.PlayerRemoving:Connect(function(player) saveAndRemove(player, true) end)
game:BindToClose(function()
	for _, player in ipairs(Players:GetPlayers()) do saveAndRemove(player, true) end
end)

-- ---- main loop: fixed simulation tick, 1 s position / snapshot / visuals, periodic autosave ----
local simAcc, slowAcc, saveAcc = 0, 0, 0
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
				if session.rt.inWorkshop then
					-- fell out of the interior? bring the player back instead of leaving him in the void
					local room = workshops.rooms[session.rt.inWorkshop]
					if room and (root.Position - room.origin).Magnitude > 400 then teleport(player, workshops:spawnCFrame(room)) end
				else
					local x, z = toLocal(root.Position)
					Game.updatePosition(world, session, x, z)
				end
			end
			if session and not session.safeMode then
				workshops:sync(Game.workshopView(world, player.UserId))
			end
			push(player)
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

end)
task.wait(12)
local out = {}
local function p(...) out[#out + 1] = string.format(...) end
p("VillageReady=%s after %.1fs, errors=%d", tostring(workspace:GetAttribute("VillageReady")), os.clock() - __t, #__errors)
for _, e in ipairs(__errors) do p("ERROR %s", e) end
local names = {}
for _, c in ipairs(workspace:GetChildren()) do names[#names + 1] = c.ClassName .. ":" .. c.Name end
p("workspace: %s", table.concat(names, ", "))
for _, c in ipairs(game:GetService("ReplicatedStorage"):GetChildren()) do p("ReplicatedStorage child %s:%s", c.ClassName, c.Name) end
local market = workspace:FindFirstChild("ArcaneMarket")
if market then
	for _, f in ipairs(market:GetChildren()) do
		local parts = {}
		for _, d in ipairs(f:GetChildren()) do
			if d:IsA("MeshPart") then
				local _, ry = d.CFrame:ToOrientation()
				parts[#parts + 1] = string.format("%s pos(%.1f,%.1f,%.1f) yaw %.0f size(%.1f,%.1f,%.1f)", d.Name, d.Position.X, d.Position.Y, d.Position.Z, math.deg(ry), d.Size.X, d.Size.Y, d.Size.Z)
			elseif d.Name == "TradePrompt" then
				parts[#parts + 1] = string.format("prompt(%.1f,%.1f,%.1f)", d.Position.X, d.Position.Y, d.Position.Z)
			else parts[#parts + 1] = d.Name end
		end
		p("market %s: %s", f.Name, table.concat(parts, " | "))
	end
else p("no ArcaneMarket in workspace") end
local village = workspace:FindFirstChild("Village")
if village then
	local b = village:FindFirstChild("buildings")
	local cottage = b and b:FindFirstChild("house_01_timber_cottage", true)
	if cottage then
		local mp = cottage:FindFirstChildWhichIsA("MeshPart", true)
		p("cottage slot: %s mesh=%s size(%.1f,%.1f,%.1f)", cottage.Name, mp and mp.Name or "?", mp and mp.Size.X or 0, mp and mp.Size.Y or 0, mp and mp.Size.Z or 0)
	end
	local old = village:FindFirstChild("market")
	p("old market stalls left: %d", old and #old:GetChildren() or 0)
end
return table.concat(out, "\n")
