-- World state of one server: sessions, shared nodes, village project, ticking and snapshots.
-- Pure Lua; the Roblox adapters (Bootstrap) feed positions, time and network into it.
local D = require(script.Parent.Data)
local Profile = require(script.Parent.ProfileService)
local Sim = require(script.Parent.WorkshopSimulation)
local Quest = require(script.Parent.QuestService)
local Res = require(script.Parent.ResourceService)
local Shop = require(script.Parent.ShopService)
local Eco = require(script.Parent.EconomyService)
local Metrics = require(script.Parent.MetricsService)
local Co = require(script.Parent.CoOpPermissions)
local Prod = require(script.Parent.ProductionService)
local Config, Quests, Locations, Machines, Recipes = D.Config, D.Quests, D.Locations, D.Machines, D.Recipes
local Game = {}

-- anchors: { [locationId] = {x=, z=} }, nodeAnchors: { [nodeId] = {x=, z=} } in world studs.
function Game.newWorld(anchors, nodeAnchors, seed, marketAnchors)
	local project = Quests.projects[((seed or 0) % #Quests.projects) + 1]
	return { sessions = {}, nodes = Res.new(), anchors = anchors or {}, nodeAnchors = nodeAnchors or {},
		marketAnchors = marketAnchors or {}, coop = {},
		project = { id = project.id, progress = 0, contributors = {}, done = false } }
end

function Game.addSession(world, userId, profile, safeMode)
	local session = { userId = userId, profile = profile or Profile.new(userId), safeMode = safeMode == true }
	local rt = Sim.newRuntime()
	rt.buckets, rt.recent, rt.recentOrder, rt.version, rt.notes = {}, {}, {}, 0, {}
	session.rt = rt
	world.sessions[userId] = session
	return session
end

-- Returns the visitors that must be sent back to the hub because their host left.
function Game.removeSession(world, userId)
	local evicted = {}
	for id, s in pairs(world.sessions) do
		if id ~= userId and s.rt.inWorkshop == userId then
			s.rt.inWorkshop = nil
			evicted[#evicted + 1] = id
		end
	end
	Co.clearOwner(world, userId)
	world.sessions[userId] = nil
	return evicted
end

function Game.notify(session, note)
	local notes = session.rt.notes
	notes[#notes + 1] = note
	if #notes > 40 then table.remove(notes, 1) end
end

function Game.near(world, session, locationId, extra)
	local a, p = world.anchors[locationId], session.rt.pos
	if not a or not p then return false end
	local loc = Locations.locations[locationId]
	local dx, dz = p.x - a.x, p.z - a.z
	local r = (loc and loc.radius or Config.interactRadius) + (extra or 0)
	return dx * dx + dz * dz <= r * r
end

-- Called with the server-side character position. Marks unlocked locations as visited.
function Game.updatePosition(world, session, x, z)
	session.rt.pos = { x = x, z = z }
	if session.rt.inWorkshop or session.safeMode then return end
	local P = session.profile
	for id in pairs(Locations.locations) do
		if not P.quest.visited[id] and Quest.locationUnlocked(P, id) and Game.near(world, session, id) then
			Quest.onEvents(P, { { type = "visit", at = id } })
			Game.notify(session, { kind = "visit", at = id })
		end
	end
end

-- Advances everything by dt seconds. Returns { [userId] = events } for client effects.
function Game.tick(world, dt, now)
	Res.step(world.nodes, dt)
	local out = {}
	for userId, session in pairs(world.sessions) do
		if not session.safeMode then
			local P = session.profile
			local events = Sim.step(P, session.rt, dt)
			local function notify(n) Game.notify(session, n) end
			Quest.onEvents(P, events, notify)
			Quest.evaluate(P, session.rt, notify)
			Quest.refreshOrders(P, now or 0)
			out[userId] = events
		end
	end
	return out
end

local function entityView(P, e)
	local b = P.workshop.buffers[e.uid]
	local v = { uid = e.uid, machine = e.machine, gx = e.gx, gz = e.gz, floor = e.floor, rot = e.rot,
		recipe = e.recipe, paused = e.paused, filter = e.filter, link = e.link, state = b.state, waiting = b.waiting,
		inv = b.inv, out = b.out, fluids = b.fluids, outFluid = b.outFluid, fuel = b.fuel, item = b.item }
	if b.job then
		v.job = { recipe = b.job.recipe, remaining = b.job.remaining, total = Recipes[b.job.recipe].durationSec }
	end
	local def = Machines[e.machine]
	if D.MachinePorts.isMachine(def) then
		v.inSide, v.outSide = D.MachinePorts.sides(def, e)
		v.outAuto = D.MachinePorts.isAuto(e)
	end
	return v
end

function Game.workshopView(world, ownerId)
	local s = world.sessions[ownerId]
	if not s then return nil end
	local P = s.profile
	local ents = {}
	for i, e in ipairs(P.workshop.layout) do ents[i] = entityView(P, e) end
	return { owner = ownerId, sizeTier = P.workshop.sizeTier, cells = Config.plotTiers[P.workshop.sizeTier].cells,
		floors = P.workshop.floors, entities = ents, version = s.rt.version,
		ratePerMin = Metrics.rate(s.rt.stats, s.rt.clock, 60), perItem5 = Metrics.perItem(s.rt.stats, s.rt.clock, 300),
		stock = Shop.stock(P), demand = P.shop.demand, nextCustomerIn = P.shop.nextIn }
end

-- Everything the owning client may know. Built from server state only.
function Game.snapshot(world, session)
	local P = session.profile
	local q = Quest.current(P)
	local chains = {}
	for id, c in pairs(Quests.chains) do
		local step = Quest.chainStep(P, id)
		chains[id] = { done = P.quest.chains[id] or 0, total = #c.steps, at = c.at, name = c.name,
			unlocked = Quest.locationUnlocked(P, c.at), step = step and { id = step.id, title = step.title,
				items = step.objective.items, rewards = step.rewards } or nil }
	end
	local orders = {}
	for i, o in ipairs(P.quest.orders.list) do
		local t = Quest.templateById[o.tpl]
		orders[i] = { id = o.id, title = t.title, items = t.items, coins = Quest.orderReward(t), rep = t.rep }
	end
	local nodes = {}
	for id, st in pairs(world.nodes) do
		nodes[id] = { remaining = st.remaining, unlocked = Quest.ruleMet(P, Locations.nodes[id].unlock) }
	end
	local locations = {}
	for id in pairs(Locations.locations) do
		locations[id] = { unlocked = Quest.locationUnlocked(P, id), visited = P.quest.visited[id] == true }
	end
	local project = nil
	for _, p in ipairs(Quests.projects) do
		if p.id == world.project.id then
			project = { id = p.id, title = p.title, item = p.item, count = p.count, progress = world.project.progress,
				done = world.project.done, mine = world.project.contributors[session.userId] or 0,
				claimed = P.claims[p.id] == true }
		end
	end
	local market = {}
	for _, id in ipairs(D.Market.order) do
		for _, offer in ipairs(D.Market.merchants[id].offers) do
			market[offer.item] = Quest.ruleMet(P, offer.unlock)
		end
	end
	local notes = session.rt.notes
	session.rt.notes = {}
	return {
		userId = session.userId, safeMode = session.safeMode, version = session.rt.version,
		wallet = P.wallet, knowledge = P.knowledge, repPoints = P.repPoints, repLevel = Eco.repLevel(P),
		items = P.items, research = P.research, discoveries = P.discoveries, stats = P.stats,
		quest = q and { id = q.id, title = q.title, hint = q.hint, objective = q.objective, progress = P.quest.progress,
			giver = q.giver, rewards = q.rewards } or nil,
		questIndex = P.quest.main, market = market, chains = chains, orders = orders, nodes = nodes, locations = locations,
		project = project, blueprints = P.blueprints, inWorkshop = session.rt.inWorkshop,
		workshop = session.rt.inWorkshop and Game.workshopView(world, session.rt.inWorkshop) or nil,
		coop = world.coop[session.userId] or {}, notes = notes,
	}
end
return Game
