-- Single entry point for every client request (spec §12 protocol, §14 security).
-- handle(world, session, action, payload, ctx) -> { ok, code, version, payload }
-- ctx = { now = seconds (server clock) }.  The client never supplies positions, prices or amounts of money.
local D = require(script.Parent.Data)
local Inv = require(script.Parent.InventoryService)
local Eco = require(script.Parent.EconomyService)
local Place = require(script.Parent.PlacementService)
local Logistics = require(script.Parent.LogisticsService)
local Prod = require(script.Parent.ProductionService)
local Quest = require(script.Parent.QuestService)
local Research = require(script.Parent.ResearchService)
local Res = require(script.Parent.ResourceService)
local Sec = require(script.Parent.SecurityService)
local Co = require(script.Parent.CoOpPermissions)
local Game = require(script.Parent.Game)
local Config, Machines, Recipes, Items, Quests, Locations, Util =
	D.Config, D.Machines, D.Recipes, D.Items, D.Quests, D.Locations, D.Util
local Actions = {}
local H = {}

local function fail(code, payload) return { ok = false, code = code, payload = payload } end
local function ok(payload) return { ok = true, code = "OK", payload = payload } end

-- Workshop the player stands in, with the profile that owns it. role = minimum right needed.
local function workshop(world, session, role)
	local ownerId = session.rt.inWorkshop
	if not ownerId then return nil, nil, "TOO_FAR" end
	local owner = world.sessions[ownerId]
	if not owner then return nil, nil, "NOT_FOUND" end
	if not Co.atLeast(world, ownerId, session.userId, role) then return nil, nil, "FORBIDDEN" end
	return owner.profile, owner, nil
end

local function touched(owner, layoutChanged)
	owner.rt.version = owner.rt.version + 1
	if layoutChanged then owner.rt.dirty = true end
end

local function afterChange(world, owner, events)
	local function notify(n) Game.notify(owner, n) end
	Quest.onEvents(owner.profile, events or {}, notify)
	Quest.evaluate(owner.profile, owner.rt, notify)
end

function H.RequestSnapshot() return ok() end

function H.GatherNode(world, session, p)
	local def = Locations.nodes[p.node]
	if not def then return fail("NOT_FOUND") end
	local P = session.profile
	if session.rt.inWorkshop then return fail("TOO_FAR") end
	if not Quest.ruleMet(P, def.unlock) or not Quest.locationUnlocked(P, def.at) then return fail("LOCKED") end
	local a, pos = world.nodeAnchors[p.node], session.rt.pos
	if not a or not pos then return fail("TOO_FAR") end
	local dx, dz = pos.x - a.x, pos.z - a.z
	if dx * dx + dz * dz > Config.interactRadius * Config.interactRadius then return fail("TOO_FAR") end
	local n, code = Res.gather(world.nodes, P, p.node)
	if not n then return fail(code) end
	return ok({ item = def.item, amount = n, remaining = world.nodes[p.node].remaining })
end

function H.EnterWorkshop(world, session, p)
	local ownerId = p.owner or session.userId
	if session.rt.inWorkshop then return fail("BUSY") end
	if not Game.near(world, session, "workshop_door") then return fail("TOO_FAR") end
	if not world.sessions[ownerId] then return fail("NOT_FOUND") end
	if not Co.atLeast(world, ownerId, session.userId, "visitor") then return fail("FORBIDDEN") end
	session.rt.inWorkshop = ownerId
	if ownerId == session.userId then afterChange(world, session, { { type = "enter_workshop" } }) end
	return ok({ owner = ownerId })
end

function H.LeaveWorkshop(world, session)
	if not session.rt.inWorkshop then return fail("NOT_READY") end
	session.rt.inWorkshop = nil
	return ok()
end

function H.PlaceMachine(world, session, p)
	local P, owner, code = workshop(world, session, "builder")
	if not P then return fail(code) end
	local e, why = Place.place(P, p.machine, p.gx, p.gz, p.floor, p.rot)
	if not e then return fail(why) end
	touched(owner, true)
	afterChange(world, owner, { { type = "place", machine = p.machine } })
	return ok({ uid = e.uid })
end

function H.RemoveMachine(world, session, p)
	local P, owner, code = workshop(world, session, "builder")
	if not P then return fail(code) end
	local res, why = Place.remove(P, p.uid)
	if not res then return fail(why) end
	touched(owner, true)
	return ok(res)
end

function H.RotateMachine(world, session, p)
	local P, owner, code = workshop(world, session, "builder")
	if not P then return fail(code) end
	local e, why = Place.rotate(P, p.uid)
	if not e then return fail(why) end
	touched(owner, true)
	return ok({ rot = e.rot })
end

local function recipeAllowed(P, e, recipeId)
	local r = Recipes[recipeId]
	if not r or r.machineId ~= e.machine then return nil, "NOT_FOUND" end
	if not P.research[r.requiredResearch] then return nil, "LOCKED" end
	return r
end

-- Returns inputs that do not belong to recipe `r` to the inventory (all or nothing).
local function flushForeign(P, b, r)
	local back = {}
	for item, n in pairs(b.inv) do if not (r and r.inputs[item]) then back[item] = n end end
	for item, n in pairs(b.fluids) do if not (r and r.inputs[item]) then back[item] = (back[item] or 0) + n end end
	if not Inv.canAdd(P.items, back, Inv.PLAYER) then return false end
	Inv.add(P.items, back)
	for item in pairs(back) do b.inv[item] = nil b.fluids[item] = nil end
	return true
end

function H.SetRecipe(world, session, p)
	local P, owner, code = workshop(world, session, "operator")
	if not P then return fail(code) end
	local e = Place.find(P, p.uid)
	if not e or Machines[e.machine].kind ~= "machine" then return fail("NOT_FOUND") end
	local b = P.workshop.buffers[e.uid]
	if b.job then return fail("BUSY") end
	local r = nil
	if p.recipe then
		local why
		r, why = recipeAllowed(P, e, p.recipe)
		if not r then return fail(why) end
	end
	if not flushForeign(P, b, r) then return fail("NO_SPACE") end
	e.recipe = p.recipe
	touched(owner, false)
	return ok()
end

function H.StartManualCraft(world, session, p)
	local P, owner, code = workshop(world, session, "operator")
	if not P then return fail(code) end
	local e = Place.find(P, p.uid)
	if not e or Machines[e.machine].kind ~= "machine" then return fail("NOT_FOUND") end
	local r, why = recipeAllowed(P, e, p.recipe)
	if not r then return fail(why) end
	local b = P.workshop.buffers[e.uid]
	if b.job and e.recipe ~= p.recipe then return fail("BUSY") end
	if e.recipe ~= p.recipe and not flushForeign(P, b, r) then return fail("NO_SPACE") end
	local need = {}
	for item, n in pairs(r.inputs) do
		local have = (Items[item].unit == "ml") and (b.fluids[item] or 0) or (b.inv[item] or 0)
		if have < n then need[item] = n - have end
	end
	if r.fuelUnits and b.fuel < r.fuelUnits then need.fuel_charcoal = (need.fuel_charcoal or 0) + r.fuelUnits - b.fuel end
	local has, missing = Inv.has(P.items, need)
	if not has then return fail("NO_ITEMS", { item = missing }) end
	Inv.remove(P.items, need)
	for item, n in pairs(need) do
		if item == "fuel_charcoal" and not r.inputs[item] then b.fuel = b.fuel + n
		elseif Items[item].unit == "ml" then b.fluids[item] = (b.fluids[item] or 0) + n
		else b.inv[item] = (b.inv[item] or 0) + n end
	end
	e.recipe = p.recipe
	b.auto = false
	touched(owner, false)
	return ok({ durationSec = r.durationSec })
end

-- Room of an entity slot for `item` when filled by hand.
local function entityRoom(P, e, b, item)
	local def, it = Machines[e.machine], Items[item]
	if def.kind == "crate" then return Inv.room(b.inv, item, def), b.inv end
	if def.kind == "shelf" then
		return (it.type == "product") and Inv.room(b.inv, item, def) or 0, b.inv
	end
	if def.kind == "tank" then
		local held = next(b.fluids)
		if it.unit ~= "ml" or (held and held ~= item) then return 0 end
		return def.capacity - (b.fluids[item] or 0), b.fluids
	end
	if def.kind == "machine" then
		if def.usesFuel and item == "fuel_charcoal" then return Config.machine.fuelCap - b.fuel, "fuel" end
		local r = e.recipe and Recipes[e.recipe]
		local need = r and r.inputs[item]
		if not need then return 0 end
		if it.unit == "ml" then return Config.machine.fluidCap - (b.fluids[item] or 0), b.fluids end
		return need * Config.machine.inputFactor - (b.inv[item] or 0), b.inv
	end
	return 0
end

local function moveToEntity(P, e, item, amount)
	local b = P.workshop.buffers[e.uid]
	local room, store = entityRoom(P, e, b, item)
	local n = math.min(amount, room, P.items[item] or 0)
	if (P.items[item] or 0) <= 0 then return nil, "NO_ITEMS" end
	if n <= 0 then return nil, "NO_SPACE" end
	Inv.remove(P.items, { [item] = n })
	if store == "fuel" then b.fuel = b.fuel + n else store[item] = (store[item] or 0) + n end
	if Machines[e.machine].kind == "machine" and store ~= "fuel" then b.auto = false end
	return n
end

local function moveFromEntity(P, e, item, amount, slot)
	local b = P.workshop.buffers[e.uid]
	local def, it = Machines[e.machine], Items[item]
	local store
	if slot == "fuel" then
		if item ~= "fuel_charcoal" then return nil, "BAD_REQUEST" end
		local n = math.min(amount, b.fuel, Inv.room(P.items, item, Inv.PLAYER))
		if n <= 0 then return nil, (b.fuel > 0) and "NO_SPACE" or "NO_ITEMS" end
		b.fuel = b.fuel - n
		Inv.add(P.items, { [item] = n })
		return n
	elseif Logistics.CARRIER[def.kind] then
		if b.item ~= item then return nil, "NO_ITEMS" end
		if Inv.room(P.items, item, Inv.PLAYER) < 1 then return nil, "NO_SPACE" end
		b.item = nil
		Inv.add(P.items, { [item] = 1 })
		return 1
	elseif def.kind == "machine" then
		if slot == "in" then store = (it.unit == "ml") and b.fluids or b.inv
		else store = (it.unit == "ml") and b.outFluid or b.out end
	elseif def.kind == "tank" or def.kind == "pump" then store = b.fluids
	else store = b.inv end
	local n = math.min(amount, store[item] or 0, Inv.room(P.items, item, Inv.PLAYER))
	if (store[item] or 0) <= 0 then return nil, "NO_ITEMS" end
	if n <= 0 then return nil, "NO_SPACE" end
	store[item] = store[item] - n
	if store[item] == 0 then store[item] = nil end
	Inv.add(P.items, { [item] = n })
	return n
end

function H.TransferStack(world, session, p)
	local P, owner, code = workshop(world, session, "operator")
	if not P then return fail(code) end
	if not Items[p.item] or p.amount < 1 then return fail("BAD_REQUEST") end
	if p.slot and p.slot ~= "in" and p.slot ~= "out" and p.slot ~= "fuel" then return fail("BAD_REQUEST") end
	local n, why
	if p.from == "inv" and p.to ~= "inv" then
		local e = Place.find(P, p.to)
		if not e then return fail("NOT_FOUND") end
		n, why = moveToEntity(P, e, p.item, p.amount)
	elseif p.to == "inv" and p.from ~= "inv" then
		local e = Place.find(P, p.from)
		if not e then return fail("NOT_FOUND") end
		n, why = moveFromEntity(P, e, p.item, p.amount, p.slot)
	else
		return fail("BAD_REQUEST")
	end
	if not n then return fail(why) end
	touched(owner, false)
	return ok({ moved = n })
end

function H.StockShelf(world, session, p)
	local P, owner, code = workshop(world, session, "operator")
	if not P then return fail(code) end
	local e = Place.find(P, p.uid)
	if not e or Machines[e.machine].kind ~= "shelf" then return fail("NOT_FOUND") end
	if not Items[p.item] or Items[p.item].type ~= "product" or p.amount < 1 then return fail("BAD_REQUEST") end
	local n, why = moveToEntity(P, e, p.item, p.amount)
	if not n then return fail(why) end
	touched(owner, false)
	return ok({ moved = n })
end

function H.SetFilter(world, session, p)
	local P, owner, code = workshop(world, session, "operator")
	if not P then return fail(code) end
	local e = Place.find(P, p.uid)
	if not e then return fail("NOT_FOUND") end
	local kind = Machines[e.machine].kind
	if kind == "gate" then
		if p.link then
			local other = Place.find(P, p.link)
			if not other or other.uid == e.uid or Machines[other.machine].kind ~= "gate" then return fail("NOT_FOUND") end
		end
		e.link = p.link
	elseif kind == "sorter" or kind == "hopper" then
		local items = p.items or {}
		if #items > 8 then return fail("LIMIT") end
		for _, id in ipairs(items) do
			if not Items[id] or Items[id].unit == "ml" then return fail("BAD_REQUEST") end
		end
		e.filter = (#items > 0) and items or nil
	else
		return fail("BAD_REQUEST")
	end
	touched(owner, true)
	return ok()
end

function H.ToggleMachine(world, session, p)
	local P, owner, code = workshop(world, session, "operator")
	if not P then return fail(code) end
	local e = Place.find(P, p.uid)
	if not e or Machines[e.machine].kind ~= "machine" then return fail("NOT_FOUND") end
	e.paused = (not e.paused) or nil
	touched(owner, false)
	return ok({ paused = e.paused == true })
end

function H.Experiment(world, session, p)
	local P, owner, code = workshop(world, session, "owner")
	if not P then return fail(code) end
	local e = Place.find(P, p.uid)
	if not e or e.machine ~= "kettle" then return fail("NOT_FOUND") end
	local day = math.floor(session.rt.now / 86400)
	if P.experiment.day ~= day then P.experiment.day, P.experiment.count = day, 0 end
	if P.experiment.count >= Config.knowledge.experimentDailyCap then return fail("LIMIT") end
	local herb
	for _, id in ipairs({ "herb_mint", "herb_sunleaf", "mushroom_gloom", "herb_moonleaf" }) do
		if (P.items[id] or 0) >= 1 then herb = id break end
	end
	if not herb or (P.items.water or 0) < Config.liquidPortion then return fail("NO_ITEMS") end
	Inv.remove(P.items, { [herb] = 1, water = Config.liquidPortion })
	P.experiment.count = P.experiment.count + 1
	Eco.addKnowledge(P, Config.knowledge.experiment)
	touched(owner, false)
	return ok({ knowledge = Config.knowledge.experiment, left = Config.knowledge.experimentDailyCap - P.experiment.count })
end

-- Owner-only economy actions always work on the caller's own profile.
local function ownContext(world, session, locationId)
	if session.rt.inWorkshop == session.userId then return true end
	if not session.rt.inWorkshop and locationId and Game.near(world, session, locationId) then return true end
	return false
end

function H.BuyUpgrade(world, session, p)
	local P = session.profile
	if not ownContext(world, session, "town_hall") then return fail("TOO_FAR") end
	local list, key
	if p.kind == "plot" then list, key = Config.plotTiers, "sizeTier"
	elseif p.kind == "floor" then list, key = Config.floors, "floors"
	else return fail("BAD_REQUEST") end
	local nextTier = list[P.workshop[key] + 1]
	if not nextTier then return fail("LIMIT") end
	if nextTier.research and not P.research[nextTier.research] then return fail("LOCKED") end
	if nextTier.quest and not Quest.isDone(P, nextTier.quest) then return fail("LOCKED") end
	if not Eco.pay(P, nextTier.cost) then return fail("NO_FUNDS") end
	if key == "sizeTier" then
		-- the entrance and the staircase move with the plot size: grow around the old layout
		local old = Place.cells(P)
		P.workshop.sizeTier = P.workshop.sizeTier + 1
		local shift = math.floor((Place.cells(P) - old) / 2)
		for _, e in ipairs(P.workshop.layout) do e.gx, e.gz = e.gx + shift, e.gz end
	else
		P.workshop.floors = P.workshop.floors + 1
	end
	touched(session, true)
	afterChange(world, session, {})
	return ok({ sizeTier = P.workshop.sizeTier, floors = P.workshop.floors })
end

function H.UnlockResearch(world, session, p)
	local P = session.profile
	if not ownContext(world, session, "market_hall") then return fail("TOO_FAR") end
	local node, code = Research.unlock(P, p.research)
	if not node then return fail(code) end
	touched(session, false)
	afterChange(world, session, { { type = "research", id = p.research } })
	return ok({ unlocks = node.unlocks })
end

function H.ClaimOrder(world, session, p)
	local P = session.profile
	if session.rt.inWorkshop then return fail("TOO_FAR") end
	local function notify(n) Game.notify(session, n) end
	local res, code
	if p.kind == "main" then
		local q = Quest.current(P)
		if not q or q.id ~= p.id or q.objective.type ~= "deliver" then return fail("NOT_READY") end
		if not Game.near(world, session, q.objective.at) then return fail("TOO_FAR") end
		res, code = Quest.claimMain(P, p.id, notify)
	elseif p.kind == "chain" then
		local c = Quests.chains[p.id]
		if not c then return fail("NOT_FOUND") end
		if not Quest.locationUnlocked(P, c.at) then return fail("LOCKED") end
		if not Game.near(world, session, c.at) then return fail("TOO_FAR") end
		res, code = Quest.claimChain(P, p.id, notify)
	elseif p.kind == "order" then
		if not Game.near(world, session, "market_hall") then return fail("TOO_FAR") end
		res, code = Quest.claimOrder(P, p.id, session.rt.now, notify)
	else
		return fail("BAD_REQUEST")
	end
	if not res then return fail(code) end
	touched(session, false)
	afterChange(world, session, {})
	return ok()
end

function H.DonateProject(world, session, p)
	local P, project = session.profile, world.project
	if session.rt.inWorkshop or not Game.near(world, session, "plaza") then return fail("TOO_FAR") end
	local def
	for _, d in ipairs(Quests.projects) do if d.id == project.id then def = d end end
	if project.done then return fail("LIMIT") end
	local n = math.min(p.amount, def.count - project.progress, P.items[def.item] or 0)
	if p.amount < 1 then return fail("BAD_REQUEST") end
	if n <= 0 then return fail("NO_ITEMS") end
	Inv.remove(P.items, { [def.item] = n })
	project.progress = project.progress + n
	project.contributors[session.userId] = (project.contributors[session.userId] or 0) + n
	if project.progress >= def.count then
		project.done = true
		for userId in pairs(project.contributors) do
			local s = world.sessions[userId]
			if s and not s.profile.claims[def.id] then
				s.profile.claims[def.id] = true
				Eco.addRep(s.profile, def.rep)
				Game.notify(s, { kind = "project_done", project = def.id, rep = def.rep, cosmetic = def.cosmetic })
			end
		end
	end
	touched(session, false)
	return ok({ progress = project.progress, done = project.done })
end

local function setRole(world, session, p)
	if not world.sessions[p.user] then return fail("NOT_FOUND") end
	if not Co.set(world, session.userId, p.user, p.role) then return fail("BAD_REQUEST") end
	if p.role == "none" then
		local guest = world.sessions[p.user]
		if guest.rt.inWorkshop == session.userId then guest.rt.inWorkshop = nil end
	end
	Game.notify(world.sessions[p.user], { kind = "coop", owner = session.userId, role = p.role })
	return ok()
end
H.InviteCoOp = setRole
H.SetCoOpPermission = setRole

function H.SaveBlueprint(world, session, p)
	local P, owner, code = workshop(world, session, "owner")
	if not P then return fail(code) end
	local bp, why = Place.saveBlueprint(P, p.slot, p.name, p.uids)
	if not bp then return fail(why) end
	touched(owner, false)
	return ok({ parts = #bp.parts, estimateCost = bp.estimateCost })
end

function H.PlaceBlueprint(world, session, p)
	local P, owner, code = workshop(world, session, "owner")
	if not P then return fail(code) end
	local placed, why = Place.placeBlueprint(P, p.slot, p.gx, p.gz, p.floor)
	if not placed then return fail(why) end
	touched(owner, true)
	return ok({ uids = placed })
end

function Actions.handle(world, session, action, payload, ctx)
	local now = ctx and ctx.now or 0
	session.rt.now = now
	local handler = H[action]
	local clean = handler and Sec.validate(action, payload)
	local result
	if not clean then
		result = fail("BAD_REQUEST")
	elseif not Sec.allow(session, action, now) then
		result = fail("RATE_LIMITED")
	else
		local previous = Sec.replayed(session, clean.actionId)
		if previous then
			result = { ok = previous.ok, code = previous.ok and "DUPLICATE" or previous.code, payload = previous.payload }
		elseif session.safeMode and action ~= "RequestSnapshot" then
			result = fail("SAFE_MODE")
		else
			result = handler(world, session, clean)
			Sec.remember(session, clean.actionId, result)
		end
	end
	result.version = session.rt.version
	result.action = action
	return result
end
Actions.handlers = H
return Actions
