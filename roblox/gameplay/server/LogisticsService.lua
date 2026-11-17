-- Transport graph (solids and fluids) of one workshop and its deterministic transfer step.
-- Tokens are data only; nothing here creates Roblox instances.
local D = require(script.Parent.Data)
local Place = require(script.Parent.PlacementService)
local Inv = require(script.Parent.InventoryService)
local Config, Machines, Recipes, Items, Grid, Util = D.Config, D.Machines, D.Recipes, D.Items, D.GridMath, D.Util
local Ports = D.MachinePorts
local L = {}
local CARRIER = { belt = true, splitter = true, merger = true, sorter = true, lift = true, gate = true }
L.CARRIER = CARRIER

function L.build(P)
	local G = { ents = {}, order = {}, solid = {}, solidDir = {}, hopperSrc = {}, comps = {} }
	local ground, pipe = Place.occupancy(P)
	G.ground, G.pipe = ground, pipe
	for _, e in ipairs(P.workshop.layout) do
		G.ents[e.uid] = e
		G.order[#G.order + 1] = e.uid
	end
	local function entAt(floor, x, z)
		local uid = ground[Grid.key(floor, x, z)]
		return uid and G.ents[uid] or nil
	end
	local function solidTarget(floor, x, z, dir)
		local t = entAt(floor, x, z)
		if not t then return false end
		local def = Machines[t.machine]
		if def.kind == "crate" or def.kind == "shelf" then return t.uid end
		if def.kind == "machine" then
			-- production machines take solid goods only at their chosen inlet side
			local inSide = Ports.sides(def, t)
			local px, pz, pd = Ports.cell(def, t, inSide)
			return (px == x and pz == z and pd == Grid.opposite(dir)) and t.uid or false
		end
		for _, p in ipairs(def.ports) do
			if p.type == "solid" and p.mode == "in" then
				local px, pz, pd = Grid.port(def, p, t.gx, t.gz, t.rot)
				if px == x and pz == z and pd == Grid.opposite(dir) then return t.uid end
			end
		end
		return false
	end
	-- fluid network: union-find over pipes and tanks
	local parent = {}
	local function find(a)
		while parent[a] ~= a do
			parent[a] = parent[parent[a]]
			a = parent[a]
		end
		return a
	end
	local function union(a, b) parent[find(a)] = find(b) end
	for _, e in ipairs(P.workshop.layout) do
		local kind = Machines[e.machine].kind
		if kind == "pipe" or kind == "tank" then parent[e.uid] = e.uid end
	end
	for _, e in ipairs(P.workshop.layout) do
		if Machines[e.machine].kind == "pipe" then
			for dir = 0, 3 do
				local k = Grid.key(e.floor, e.gx + Grid.DX[dir], e.gz + Grid.DZ[dir])
				if pipe[k] then union(e.uid, pipe[k]) end
				local g = ground[k] and G.ents[ground[k]]
				if g and Machines[g.machine].kind == "tank" then union(e.uid, g.uid) end
			end
		end
	end
	local compOf = {}
	local function comp(root)
		if not compOf[root] then
			compOf[root] = { sources = {}, sinks = {}, tanks = {} }
			G.comps[#G.comps + 1] = compOf[root]
		end
		return compOf[root]
	end
	for _, e in ipairs(P.workshop.layout) do
		local def = Machines[e.machine]
		if def.kind == "tank" then
			local c = comp(find(e.uid))
			c.tanks[#c.tanks + 1] = e.uid
		end
		local outs, dirs = {}, {}           -- dirs[i]: direction goods travel when they leave through outs[i]
		if def.kind == "machine" then
			-- production machines hand solid goods over at their current outlet side
			local _, outSide = Ports.sides(def, e)
			local px, pz, dir = Ports.cell(def, e, outSide)
			outs[1], dirs[1] = solidTarget(e.floor, px + Grid.DX[dir], pz + Grid.DZ[dir], dir), dir
		end
		for _, p in ipairs(def.ports) do
			local px, pz, dir = Grid.port(def, p, e.gx, e.gz, e.rot)
			local nx, nz = px + Grid.DX[dir], pz + Grid.DZ[dir]
			if p.type == "solid" and def.kind == "machine" then
				-- handled above through the chosen sides
			elseif p.type == "solid" and p.mode == "out" then
				local floor = e.floor
				if def.kind == "lift" then floor = floor + 1 end
				if def.kind == "gate" then
					local partner = e.link and G.ents[e.link]
					if partner and Machines[partner.machine].kind == "gate" and partner.uid ~= e.uid then
						local qx, qz, qdir = Grid.port(def, p, partner.gx, partner.gz, partner.rot)
						outs[#outs + 1] = solidTarget(partner.floor, qx + Grid.DX[qdir], qz + Grid.DZ[qdir], qdir)
						dirs[#outs] = qdir
					else
						outs[#outs + 1] = false
						dirs[#outs] = dir
					end
				else
					outs[#outs + 1] = solidTarget(floor, nx, nz, dir)
					dirs[#outs] = dir
				end
			elseif p.type == "fluid" then
				local k = Grid.key(e.floor, nx, nz)
				local n = ground[k] and G.ents[ground[k]]
				local root
				if pipe[k] then root = find(pipe[k])
				elseif n and Machines[n.machine].kind == "tank" then root = find(n.uid) end
				if root then
					local c = comp(root)
					local list = (p.mode == "out") and c.sources or c.sinks
					list[#list + 1] = e.uid
				elseif n and p.mode == "out" then
					for _, q in ipairs(Machines[n.machine].ports) do
						if q.type == "fluid" and q.mode == "in" then
							local qx, qz, qd = Grid.port(Machines[n.machine], q, n.gx, n.gz, n.rot)
							if qx == nx and qz == nz and qd == Grid.opposite(dir) then
								G.comps[#G.comps + 1] = { sources = { e.uid }, sinks = { n.uid }, tanks = {} }
							end
						end
					end
				end
			end
		end
		G.solid[e.uid], G.solidDir[e.uid] = outs, dirs
		if def.kind == "hopper" then
			local front = e.rot % 4
			local src = entAt(e.floor, e.gx - Grid.DX[front], e.gz - Grid.DZ[front])
			if src then
				local kind = Machines[src.machine].kind
				if kind == "crate" or kind == "machine" then G.hopperSrc[e.uid] = src.uid end
			end
		end
	end
	-- Transfer order: parts closest to the end of a line first.  A full belt then moves forward in
	-- one tick (the front item leaves, every item behind follows at once) instead of each item
	-- waiting one tick for the one in front.  Parts at the same distance share one group, inside
	-- which the start rotates every tick (fair merging).
	local depth = {}
	for _, uid in ipairs(G.order) do depth[uid] = 0 end
	for _ = 1, #G.order do
		local changed = false
		for _, uid in ipairs(G.order) do
			local best = 0
			for _, t in ipairs(G.solid[uid] or {}) do
				if t and CARRIER[Machines[G.ents[t].machine].kind] then
					local d = depth[t] + 1
					if best == 0 or d < best then best = d end
				end
			end
			if best ~= depth[uid] and best <= #G.order then depth[uid], changed = best, true end
		end
		if not changed then break end
	end
	local groups, levels = {}, {}
	for _, uid in ipairs(G.order) do
		local d = depth[uid]
		if not groups[d] then groups[d] = {} levels[#levels + 1] = d end
		local g = groups[d]
		g[#g + 1] = uid
	end
	table.sort(levels)
	G.groups = {}
	for _, d in ipairs(levels) do G.groups[#G.groups + 1] = groups[d] end
	return G
end

-- Which slot of entity `uid` would take one `item`? nil = not accepted now.
function L.accepts(P, G, uid, item)
	local e = G.ents[uid]
	local def, b = Machines[e.machine], P.workshop.buffers[uid]
	local it = Items[item]
	if not it or it.unit == "ml" then return nil end
	if def.kind == "crate" then
		return Inv.room(b.inv, item, def) >= 1 and "inv" or nil
	elseif def.kind == "shelf" then
		return (it.type == "product" and Inv.room(b.inv, item, def) >= 1) and "inv" or nil
	elseif def.kind == "machine" then
		if def.usesFuel and item == "fuel_charcoal" then
			return b.fuel < Config.machine.fuelCap and "fuel" or nil
		end
		local r = e.recipe and Recipes[e.recipe]
		local need = r and r.inputs[item]
		if need and (b.inv[item] or 0) < need * Config.machine.inputFactor then return "inv" end
		return nil
	elseif CARRIER[def.kind] then
		return b.item == nil and "item" or nil
	end
	return nil
end

-- dir: direction the item travelled into `uid` (only kept for conveyors: where it is drawn entering)
function L.give(P, uid, slot, item, viaLogistics, dir)
	local b = P.workshop.buffers[uid]
	if slot == "item" then
		b.item, b.t, b.inDir = item, 0, dir
	elseif slot == "fuel" then
		b.fuel = b.fuel + 1
	else
		b.inv[item] = (b.inv[item] or 0) + 1
		if viaLogistics then b.auto = true end
	end
end

local function takeOne(store, item)
	local left = store[item] - 1
	if left <= 0 then store[item] = nil else store[item] = left end
end

local function inFilter(e, item)
	if not e.filter then return false end
	for _, id in ipairs(e.filter) do if id == item then return true end end
	return false
end

-- Moves solid tokens. Returns the number of transfers.
function L.stepSolids(P, G, dt, tickIndex)
	local buffers, sim = P.workshop.buffers, Config.sim
	local n = #G.order
	if n == 0 then return 0 end
	for i = 1, n do
		local b = buffers[G.order[i]]
		b.t = math.min((b.t or 0) + dt, 60)
	end
	local moved = 0
	local sequence = {}
	for _, group in ipairs(G.groups) do
		local m = #group
		local start = tickIndex % m
		for i = 1, m do sequence[#sequence + 1] = group[((start + i - 1) % m) + 1] end
	end
	for i = 1, n do
		local uid = sequence[i]
		local e, b = G.ents[uid], buffers[uid]
		local kind = Machines[e.machine].kind
		local outs = G.solid[uid]
		if kind == "machine" then
			local target = outs[1]
			if target and b.t >= 0.5 then
				for _, item in ipairs(Util.sortedKeys(b.out)) do
					local slot = L.accepts(P, G, target, item)
					if slot then
						takeOne(b.out, item)
						L.give(P, target, slot, item, true, G.solidDir[uid][1])
						b.t, moved = 0, moved + 1
						break
					end
				end
			end
		elseif kind == "hopper" then
			local src, target = G.hopperSrc[uid], outs[1]
			if src and target and b.t >= sim.hopperSecondsPerItem then
				local sb = buffers[src]
				local store = (Machines[G.ents[src].machine].kind == "crate") and sb.inv or sb.out
				for _, item in ipairs(Util.sortedKeys(store)) do
					if (not e.filter or inFilter(e, item)) then
						local slot = L.accepts(P, G, target, item)
						if slot then
							takeOne(store, item)
							L.give(P, target, slot, item, true, G.solidDir[uid][1])
							b.t, moved = 0, moved + 1
							break
						end
					end
				end
			end
		elseif CARRIER[kind] and b.item then
			local period = 0.5
			if kind == "belt" then period = sim.beltSecondsPerItem
			elseif kind == "lift" then period = sim.liftSecondsPerItem
			elseif kind == "gate" then period = sim.gateSecondsPerItem end
			if b.t >= period then
				local target, index = nil, 1
				if kind == "splitter" then
					local count = #outs
					for k = 0, count - 1 do
						local idx = ((b.rr or 0) + k) % count + 1
						if outs[idx] and L.accepts(P, G, outs[idx], b.item) then
							target, index = outs[idx], idx
							b.rr = idx % count
							break
						end
					end
				elseif kind == "sorter" then
					index = inFilter(e, b.item) and 1 or 2
					target = outs[index]
				else
					target = outs[1]
				end
				local slot = target and L.accepts(P, G, target, b.item)
				if slot then
					local item = b.item
					b.item, b.inDir = nil, nil
					L.give(P, target, slot, item, true, G.solidDir[uid][index])
					moved = moved + 1
				end
			end
		end
	end
	return moved
end

local function fluidSource(P, G, uid)
	local e, b = G.ents[uid], P.workshop.buffers[uid]
	if Machines[e.machine].kind == "pump" then return b.fluids, true end
	return b.outFluid, false
end

-- Moves liquids (integer ml) inside every fluid component. emit(event) reports piped water.
function L.stepFluids(P, G, dt, emit)
	local buffers = P.workshop.buffers
	for _, c in ipairs(G.comps) do
		local budget = math.floor(Config.sim.pipeMlPerSec * dt)
		for _, sinkUid in ipairs(c.sinks) do
			local e, b = G.ents[sinkUid], buffers[sinkUid]
			local r = e.recipe and Recipes[e.recipe]
			if r then
				for _, item in ipairs(Util.sortedKeys(r.inputs)) do
					if Items[item].unit == "ml" then
						local function pull(store, countsAsPiped)
							local room = Config.machine.fluidCap - (b.fluids[item] or 0)
							local n = math.min(room, store[item] or 0, budget)
							if n > 0 then
								store[item] = store[item] - n
								if store[item] == 0 then store[item] = nil end
								b.fluids[item] = (b.fluids[item] or 0) + n
								budget = budget - n
								if countsAsPiped and item == "water" then emit({ type = "piped", ml = n }) end
							end
						end
						for _, srcUid in ipairs(c.sources) do
							local store, isPump = fluidSource(P, G, srcUid)
							pull(store, isPump)
						end
						for _, tankUid in ipairs(c.tanks) do pull(buffers[tankUid].fluids, true) end
					end
				end
			end
		end
		-- surplus of producers goes into tanks (one liquid type per tank)
		for _, srcUid in ipairs(c.sources) do
			local store = fluidSource(P, G, srcUid)
			for _, item in ipairs(Util.sortedKeys(store)) do
				for _, tankUid in ipairs(c.tanks) do
					local tb = buffers[tankUid]
					local held = next(tb.fluids)
					if held == nil or held == item then
						local cap = Machines[G.ents[tankUid].machine].capacity
						local n = math.min(cap - (tb.fluids[item] or 0), store[item] or 0, budget)
						if n > 0 then
							store[item] = store[item] - n
							if store[item] == 0 then store[item] = nil end
							tb.fluids[item] = (tb.fluids[item] or 0) + n
							budget = budget - n
						end
					end
				end
			end
		end
	end
end
return L
