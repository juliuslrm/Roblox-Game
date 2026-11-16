-- Sole writer of the workshop layout: grid rules, placing, removing, rotating, blueprints.
local D = require(script.Parent.Data)
local Inv = require(script.Parent.InventoryService)
local Eco = require(script.Parent.EconomyService)
local Config, Machines, Grid, Util, Recipes = D.Config, D.Machines, D.GridMath, D.Util, D.Recipes
local Ports = D.MachinePorts
local Place = {}

function Place.cells(P) return Config.plotTiers[P.workshop.sizeTier].cells end

-- Reserved cells: entrance (front edge, floor 1) and staircase (back-left corner, all floors).
function Place.reserved(P, floor, x, z)
	local n = Place.cells(P)
	if floor == 1 then
		local x0 = math.floor(n / 2) - math.floor(Config.door.width / 2)
		if x >= x0 and x < x0 + Config.door.width and z < Config.door.depth then return true end
	end
	if x < 3 and z >= n - 4 then return true end
	return false
end

function Place.find(P, uid)
	for i, e in ipairs(P.workshop.layout) do
		if e.uid == uid then return e, i end
	end
	return nil
end

-- Occupancy maps: ground (machines, belts) and pipe layer.
function Place.occupancy(P, skipUid)
	local ground, pipe = {}, {}
	for _, e in ipairs(P.workshop.layout) do
		if e.uid ~= skipUid then
			local def = Machines[e.machine]
			local map = (def.layer == "pipe") and pipe or ground
			for _, c in ipairs(Grid.cells(def, e.gx, e.gz, e.rot)) do
				map[Grid.key(e.floor, c[1], c[2])] = e.uid
			end
		end
	end
	return ground, pipe
end

local function countOf(P, machineId, kindCategory)
	local n, logistics, machines = 0, 0, 0
	for _, e in ipairs(P.workshop.layout) do
		if e.machine == machineId then n = n + 1 end
		if Machines[e.machine].category == "transport" then logistics = logistics + 1 else machines = machines + 1 end
	end
	return n, logistics, machines
end

function Place.unlocked(P, machineId)
	local def = Machines[machineId]
	return def ~= nil and P.research[def.research] == true
end

-- Returns nil if the placement is legal, otherwise a result code.
function Place.check(P, machineId, gx, gz, floor, rot, skipUid, ground, pipe)
	local def = Machines[machineId]
	if not def then return "NOT_FOUND" end
	if not (Util.isInt(gx) and Util.isInt(gz) and Util.isInt(floor) and Util.isInt(rot)) then return "BAD_REQUEST" end
	if rot < 0 or rot > 3 or floor < 1 or floor > P.workshop.floors then return "BLOCKED" end
	if not Place.unlocked(P, machineId) then return "LOCKED" end
	local n = Place.cells(P)
	if not ground then ground, pipe = Place.occupancy(P, skipUid) end
	for _, c in ipairs(Grid.cells(def, gx, gz, rot)) do
		local x, z = c[1], c[2]
		if x < 0 or z < 0 or x >= n or z >= n then return "BLOCKED" end
		if Place.reserved(P, floor, x, z) then return "BLOCKED" end
		local k = Grid.key(floor, x, z)
		if def.layer == "pipe" then
			if pipe[k] then return "BLOCKED" end
			local g = ground[k]
			if g then
				local other = Place.find(P, g)
				if Machines[other.machine].category ~= "transport" then return "BLOCKED" end
			end
		else
			if ground[k] then return "BLOCKED" end
			if def.category ~= "transport" and pipe[k] then return "BLOCKED" end
		end
	end
	if def.kind == "lift" and floor >= P.workshop.floors then return "BLOCKED" end
	return nil
end

function Place.limitCode(P, machineId)
	local def = Machines[machineId]
	local same, logistics, machines = countOf(P, machineId)
	if def.buildLimit and same >= def.buildLimit then return "LIMIT" end
	if machineId == "storage_crate" and not P.research.storage and same >= Config.limits.crateLimitStart then return "LIMIT" end
	if def.category == "transport" then
		if logistics >= Config.limits.logistics then return "LIMIT" end
	elseif machines >= Config.limits.machines then return "LIMIT" end
	return nil
end

-- Re-evaluates every automatic outlet.  Called after anything was placed, turned or removed, so
-- the result does not depend on the building order.  Returns the uids whose outlet moved.
function Place.refreshOutlets(P)
	local ground = Place.occupancy(P)
	local byUid = {}
	for _, e in ipairs(P.workshop.layout) do byUid[e.uid] = e end
	local function entAt(floor, x, z)
		local e = byUid[ground[Grid.key(floor, x, z)]]
		if e then return e, Machines[e.machine] end
		return nil
	end
	local moved = {}
	for _, e in ipairs(P.workshop.layout) do
		local def = Machines[e.machine]
		if Ports.isMachine(def) and Ports.isAuto(e) then
			local _, current = Ports.sides(def, e)
			local side = Ports.autoSide(def, e, entAt)
			if side ~= current then
				e.outSide = side
				moved[#moved + 1] = e.uid
			end
		end
	end
	return moved
end

-- Player choice of inlet / outlet in the machine window.
--   inSide / outSide: side 0..3 or nil (unchanged); auto: true switches the outlet back to automatic.
-- Choosing an outlet fixes it ("manual").  Choosing the side the other connection uses swaps the two.
function Place.setPorts(P, uid, inSide, outSide, auto)
	local e = Place.find(P, uid)
	local def = e and Machines[e.machine]
	if not e or not Ports.isMachine(def) then return nil, "NOT_FOUND" end
	if (inSide ~= nil and not Ports.allowed(def, inSide)) or (outSide ~= nil and not Ports.allowed(def, outSide)) then
		return nil, "BLOCKED"
	end
	if inSide ~= nil and inSide == outSide then return nil, "BAD_REQUEST" end
	local curIn, curOut = Ports.sides(def, e)
	if inSide ~= nil and inSide ~= curIn then
		if inSide == curOut then curOut = curIn end
		curIn = inSide
	end
	if outSide ~= nil then
		if outSide == curIn then curIn = curOut end
		curOut = outSide
		e.outAuto = false
	end
	e.inSide, e.outSide = curIn, curOut
	if auto == true then e.outAuto = nil end
	Place.refreshOutlets(P)
	local finalIn, finalOut = Ports.sides(def, e)
	return { inSide = finalIn, outSide = finalOut, auto = Ports.isAuto(e) }
end

local function newBuffer() return { inv = {}, out = {}, fluids = {}, outFluid = {}, fuel = 0 } end
Place.newBuffer = newBuffer

local function addEntity(P, machineId, gx, gz, floor, rot)
	local uid = "m" .. P.workshop.nextUid
	P.workshop.nextUid = P.workshop.nextUid + 1
	local e = { uid = uid, machine = machineId, gx = gx, gz = gz, floor = floor, rot = rot }
	P.workshop.layout[#P.workshop.layout + 1] = e
	P.workshop.buffers[uid] = newBuffer()
	return e
end

function Place.place(P, machineId, gx, gz, floor, rot, free)
	local code = Place.check(P, machineId, gx, gz, floor, rot)
	if code then return nil, code end
	code = Place.limitCode(P, machineId)
	if code then return nil, code end
	local cost = free and 0 or Machines[machineId].cost
	if not Eco.pay(P, cost) then return nil, "NO_FUNDS" end
	local e = addEntity(P, machineId, gx, gz, floor, rot)
	e.paid = cost
	Place.refreshOutlets(P)
	return e
end

-- Everything stored in an entity, as one item map (job inputs are refunded as well).
function Place.contents(P, uid)
	local b = P.workshop.buffers[uid]
	local all = {}
	if not b then return all end
	local function take(t) for id, n in pairs(t or {}) do all[id] = (all[id] or 0) + n end end
	take(b.inv) take(b.out) take(b.fluids) take(b.outFluid)
	if b.fuel and b.fuel > 0 then all.fuel_charcoal = (all.fuel_charcoal or 0) + b.fuel end
	if b.item then all[b.item] = (all[b.item] or 0) + 1 end
	if b.job and b.job.inputs then take(b.job.inputs) end
	return all
end

function Place.remove(P, uid)
	local e, index = Place.find(P, uid)
	if not e then return nil, "NOT_FOUND" end
	local contents = Place.contents(P, uid)
	if not Inv.canAdd(P.items, contents, Inv.PLAYER) then return nil, "NO_SPACE" end
	Inv.add(P.items, contents)
	table.remove(P.workshop.layout, index)
	P.workshop.buffers[uid] = nil
	local refund = math.floor((e.paid or 0) * Config.refundFactor)
	Eco.earn(P, refund)
	P.stats.coinsEarned = P.stats.coinsEarned - refund      -- a refund is not income
	for _, other in ipairs(P.workshop.layout) do
		if other.link == uid then other.link = nil end
	end
	Place.refreshOutlets(P)
	return { refund = refund, returned = contents }
end

function Place.rotate(P, uid)
	local e = Place.find(P, uid)
	if not e then return nil, "NOT_FOUND" end
	local rot = (e.rot + 1) % 4
	local code = Place.check(P, e.machine, e.gx, e.gz, e.floor, rot, uid)
	if code then return nil, code end
	e.rot = rot
	Place.refreshOutlets(P)
	return e
end

-- Starter layout: kettle, one crate and the shop shelf next to the entrance.
function Place.starter(P)
	local n = Place.cells(P)
	local mid = math.floor(n / 2)
	addEntity(P, "kettle", mid - 6, mid - 2, 1, 2).recipe = nil
	addEntity(P, "storage_crate", mid + 2, 3, 1, 0)
	addEntity(P, "shop_shelf", mid + 3, 1, 1, 2)
end

-- ---- blueprints ----
function Place.saveBlueprint(P, slot, name, uids)
	local maxSlots = P.research.master_blueprints and Config.limits.blueprintSlotsMaster or Config.limits.blueprintSlots
	if slot < 1 or slot > maxSlots then return nil, "LIMIT" end
	if #uids < 1 or #uids > Config.limits.blueprintParts then return nil, "LIMIT" end
	local parts, minX, minZ, floor, seen = {}, math.huge, math.huge, nil, {}
	for _, uid in ipairs(uids) do
		local e = Place.find(P, uid)
		if not e or seen[uid] then return nil, "NOT_FOUND" end
		seen[uid] = true
		floor = floor or e.floor
		if e.floor ~= floor then return nil, "BAD_REQUEST" end
		minX, minZ = math.min(minX, e.gx), math.min(minZ, e.gz)
	end
	local cost = 0
	for _, uid in ipairs(uids) do
		local e = Place.find(P, uid)
		parts[#parts + 1] = { machine = e.machine, dx = e.gx - minX, dz = e.gz - minZ, rot = e.rot, recipe = e.recipe,
			filter = e.filter and Util.deepCopy(e.filter) or nil,
			inSide = e.inSide, outSide = e.outSide, outAuto = e.outAuto }
		cost = cost + Machines[e.machine].cost
	end
	P.blueprints[tostring(slot)] = { name = string.sub(name, 1, 24), parts = parts, estimateCost = cost }
	return P.blueprints[tostring(slot)]
end

-- All or nothing: every part must be unlocked, affordable, within limits and free of overlaps.
function Place.placeBlueprint(P, slot, gx, gz, floor)
	local bp = P.blueprints[tostring(slot)]
	if not bp then return nil, "NOT_FOUND" end
	local backup = { layout = Util.deepCopy(P.workshop.layout), buffers = Util.deepCopy(P.workshop.buffers),
		nextUid = P.workshop.nextUid, wallet = P.wallet }
	local placed = {}
	for _, part in ipairs(bp.parts) do
		local e, code = Place.place(P, part.machine, gx + part.dx, gz + part.dz, floor, part.rot)
		if not e then
			P.workshop.layout, P.workshop.buffers = backup.layout, backup.buffers
			P.workshop.nextUid, P.wallet = backup.nextUid, backup.wallet
			return nil, code
		end
		if part.recipe and Recipes[part.recipe] and P.research[Recipes[part.recipe].requiredResearch] then
			e.recipe = part.recipe
		end
		e.filter = part.filter and Util.deepCopy(part.filter) or nil
		if Ports.isMachine(Machines[part.machine]) then
			if Ports.allowed(Machines[part.machine], part.inSide) then e.inSide = part.inSide end
			if Ports.allowed(Machines[part.machine], part.outSide) then e.outSide = part.outSide end
			if part.outAuto == false then e.outAuto = false end
		end
		placed[#placed + 1] = e.uid
	end
	Place.refreshOutlets(P)
	return placed
end
return Place
