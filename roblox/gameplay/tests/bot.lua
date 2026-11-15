-- Test bot: plays the game only through Actions.handle / Game.tick, like a client would.
local D = loadModule("server/Data")
local Game = loadModule("server/Game")
local Actions = loadModule("server/Actions")
local Place = loadModule("server/PlacementService")
local Logistics = loadModule("server/LogisticsService")
local Quest = loadModule("server/QuestService")
local Research = loadModule("server/ResearchService")
local Inv = loadModule("server/InventoryService")
local Config, Machines, Recipes, Items, Locations, Util = D.Config, D.Machines, D.Recipes, D.Items, D.Locations, D.Util
local Bot = {}
Bot.__index = Bot

function Bot.anchors()
	local anchors, nodeAnchors, i = {}, {}, 0
	for _, id in ipairs(Util.sortedKeys(Locations.locations)) do
		i = i + 1
		anchors[id] = { x = i * 200, z = 0 }
	end
	for _, id in ipairs(Util.sortedKeys(Locations.nodes)) do
		local n = Locations.nodes[id]
		nodeAnchors[id] = { x = anchors[n.at].x + n.ox, z = anchors[n.at].z + n.oz }
	end
	return anchors, nodeAnchors
end

function Bot.new(world, userId)
	local self = setmetatable({}, Bot)
	if not world then
		local a, n = Bot.anchors()
		world = Game.newWorld(a, n, 0)
	end
	self.world, self.userId = world, userId or 1001
	self.session = Game.addSession(world, self.userId)
	self.P = self.session.profile
	self.now, self.elapsed, self.log, self.seq = 1000000, 0, {}, 0
	return self
end

function Bot:try(action, payload)
	self.now = self.now + 0.4          -- a human needs time between clicks (keeps the rate limiter honest)
	self.elapsed = self.elapsed + 0.4
	return Actions.handle(self.world, self.session, action, payload or {}, { now = self.now })
end
function Bot:act(action, payload)
	local r = self:try(action, payload)
	if not r.ok then error("action " .. action .. " failed: " .. tostring(r.code), 2) end
	return r.payload
end
function Bot:tick(seconds)
	local steps = math.ceil(seconds / Config.sim.tick)
	for _ = 1, steps do
		self.now = self.now + Config.sim.tick
		self.elapsed = self.elapsed + Config.sim.tick
		Game.tick(self.world, Config.sim.tick, self.now)
	end
end
function Bot:moveTo(x, z)
	if self.session.rt.inWorkshop then self:act("LeaveWorkshop") end
	Game.updatePosition(self.world, self.session, x, z)
	self:tick(4)                       -- walking time
end
function Bot:goTo(locationId)
	local a = self.world.anchors[locationId]
	self:moveTo(a.x, a.z)
end
function Bot:enter()
	if self.session.rt.inWorkshop == self.userId then return end
	self:goTo("workshop_door")
	self:act("EnterWorkshop")
end
function Bot:count(item) return self.P.items[item] or 0 end
function Bot:quest() local q = Quest.current(self.P) return q and q.id or "done" end

-- ---- gathering ----
function Bot:gather(item, amount)
	local guard = 0
	while self:count(item) < amount do
		guard = guard + 1
		if guard > 400 then error("cannot gather " .. item) end
		local best
		for _, id in ipairs(Util.sortedKeys(Locations.nodes)) do
			local n = Locations.nodes[id]
			if n.item == item and Quest.ruleMet(self.P, n.unlock) and Quest.locationUnlocked(self.P, n.at) then
				if not best or self.world.nodes[id].remaining > self.world.nodes[best].remaining then best = id end
			end
		end
		if not best then error("no unlocked node for " .. item) end
		local a = self.world.nodeAnchors[best]
		self:moveTo(a.x, a.z)
		local r = self:try("GatherNode", { node = best })
		if not r.ok then
			if r.code == "NO_SPACE" then error("inventory full while gathering " .. item) end
			self:tick(6)
		end
	end
end

-- ---- building ----
function Bot:entitiesOf(machineId)
	local list = {}
	for _, e in ipairs(self.P.workshop.layout) do
		if e.machine == machineId then list[#list + 1] = e end
	end
	return list
end

-- true if the cells in front of every port are free (room for hopper + crate, pump, belt)
local function portsOpen(P, def, gx, gz, rot, floor, ground)
	local Grid = D.GridMath
	local n = Place.cells(P)
	for _, port in ipairs(def.ports) do
		local px, pz, dir = Grid.port(def, port, gx, gz, rot)
		local depth = (port.type == "solid" and port.mode == "in") and 3 or (port.type == "fluid") and 2 or 1
		local width = (depth > 1) and 1 or 0
		local side = (dir + 1) % 4
		for k = 1, depth do
			for lat = 0, width do
				local x = px + Grid.DX[dir] * k + Grid.DX[side] * lat
				local z = pz + Grid.DZ[dir] * k + Grid.DZ[side] * lat
				if x < 0 or z < 0 or x >= n or z >= n or Place.reserved(P, floor, x, z)
					or ground[Grid.key(floor, x, z)] then return false end
			end
		end
	end
	return true
end

-- Finds a legal spot (optionally one that satisfies predicate(graph, uid) after a trial insert).
function Bot:findSpot(machineId, predicate, floor)
	local P = self.P
	local n = Place.cells(P)
	floor = floor or 1
	local ground = Place.occupancy(P)
	local def = Machines[machineId]
	for rot = 0, 3 do
		for gz = 0, n - 1 do
			for gx = 0, n - 1 do
				if Place.check(P, machineId, gx, gz, floor, rot) == nil then
					if not predicate then
						if def.kind ~= "machine" or portsOpen(P, def, gx, gz, rot, floor, ground) then return gx, gz, rot end
					else
						local e = { uid = "trial", machine = machineId, gx = gx, gz = gz, floor = floor, rot = rot }
						table.insert(P.workshop.layout, e)
						P.workshop.buffers.trial = Place.newBuffer()
						local good = predicate(Logistics.build(P), "trial")
						table.remove(P.workshop.layout)
						P.workshop.buffers.trial = nil
						if good then return gx, gz, rot end
					end
				end
			end
		end
	end
	return nil
end

-- Buys the next plot size (researching what it needs).
function Bot:expand()
	local nextTier = Config.plotTiers[self.P.workshop.sizeTier + 1]
	if not nextTier then error("workshop is full and cannot grow") end
	if nextTier.research then self:research(nextTier.research) end
	self:afford(nextTier.cost)
	self:enter()
	self:act("BuyUpgrade", { kind = "plot" })
end

function Bot:afford(coins)
	local guard = 0
	while self.P.wallet < coins do
		guard = guard + 1
		if guard > 300 then error("cannot earn " .. coins .. " coins") end
		self:sellBatch()
	end
end

function Bot:build(machineId, predicate, floor)
	self:enter()
	self:afford(Machines[machineId].cost)
	self:enter()
	local gx, gz, rot = self:findSpot(machineId, predicate, floor)
	if not gx then
		if predicate then error("no connecting spot for " .. machineId) end
		self:expand()
		return self:build(machineId, predicate, floor)
	end
	self:afford(Machines[machineId].cost)
	self:enter()
	return self:act("PlaceMachine", { machine = machineId, gx = gx, gz = gz, floor = floor or 1, rot = rot }).uid
end

-- A free-standing machine with room in front of its ports.
function Bot:machine(machineId)
	local list = self:entitiesOf(machineId)
	if list[1] then return list[1].uid end
	return self:build(machineId)
end

function Bot:research(id)
	if self.P.research[id] then return end
	for _, p in ipairs(D.Research[id].prereqs) do self:research(p) end
	if self.P.knowledge < D.Research[id].cost then
		error("not enough knowledge for " .. id .. " (" .. self.P.knowledge .. "/" .. D.Research[id].cost .. ") at " .. self:quest())
	end
	self:goTo("market_hall")
	self:act("UnlockResearch", { research = id })
end

-- ---- crafting by hand ----
function Bot:recipeFor(item)
	for _, id in ipairs(Util.sortedKeys(Recipes)) do
		if Recipes[id].outputs[item] and not Recipes[id].supply then return Recipes[id] end
	end
	return nil
end

-- Makes sure the inventory holds `amount` of `item`, gathering and crafting whatever is needed.
function Bot:ensure(item, amount, depth)
	depth = depth or 0
	if depth > 12 then error("recipe recursion for " .. item) end
	if self:count(item) >= amount then return end
	local r = self:recipeFor(item)
	if not r then return self:gather(item, amount) end
	self:research(r.requiredResearch)
	local per = r.outputs[item]
	local guard = 0
	while self:count(item) < amount do
		guard = guard + 1
		if guard > 200 then error("cannot craft " .. item) end
		for input, n in pairs(r.inputs) do self:ensure(input, n, depth + 1) end
		if r.fuelUnits then self:ensure("fuel_charcoal", r.fuelUnits, depth + 1) end
		local uid = self:machine(r.machineId)
		self:enter()
		local e = Place.find(self.P, uid)
		local b = self.P.workshop.buffers[uid]
		if e.recipe ~= r.id and b.job == nil then self:act("SetRecipe", { uid = uid, recipe = r.id }) end
		self:act("StartManualCraft", { uid = uid, recipe = r.id })
		self:tick(r.durationSec + 0.5)
		self:collect(uid)
	end
end

function Bot:collect(uid)
	self:enter()
	local b = self.P.workshop.buffers[uid]
	for _, store in ipairs({ b.out, b.outFluid }) do
		for _, item in ipairs(Util.sortedKeys(store)) do
			self:act("TransferStack", { from = uid, to = "inv", item = item, amount = store[item] })
		end
	end
end

-- Brews potions (self.sellItem, default the starter tonic), stocks the shelf and waits for customers.
function Bot:sellBatch()
	local best = self.sellItem or "tonic_minor"
	self:ensure(best, self:count(best) + 4)
	self:enter()
	local shelf = self:entitiesOf("shop_shelf")[1].uid
	self:act("StockShelf", { uid = shelf, item = best, amount = self:count(best) })
	local guard = 0
	while (self.P.workshop.buffers[shelf].inv[best] or 0) > 0 and guard < 60 do
		guard = guard + 1
		self:tick(10)
	end
end

-- ---- automation helpers ----
-- crate -> hopper -> machine. Returns crate uid.
function Bot:feedLine(machineUid)
	self:research("storage")           -- more than two crates need the storage research
	local hopper = self:build("input_hopper", function(G, uid) return G.solid[uid][1] == machineUid end)
	local crate = self:build("storage_crate", function(G) return G.hopperSrc[hopper] == "trial" end)
	return crate
end
function Bot:attachPump(machineUid)
	return self:build("well_pump", function(G, uid)
		for _, c in ipairs(G.comps) do
			if c.sources[1] == uid and c.sinks[1] == machineUid then return true end
		end
		return false
	end)
end
function Bot:put(uid, item, amount)
	self:enter()
	return self:act("TransferStack", { from = "inv", to = uid, item = item, amount = amount }).moved
end
return Bot
