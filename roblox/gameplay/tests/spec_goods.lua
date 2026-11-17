-- Goods gliding over conveyors: the real workshop simulation plays the server, its data reaches a
-- simulated client with update interval and network delay, and GoodsMotion draws at 60 frames per
-- second.  Measured: no jumps, no stops in a moving line, no duplicates, nothing lost.
local D = loadModule("server/Data")
local Place = loadModule("server/PlacementService")
local Profile = loadModule("server/ProfileService")
local Sim = loadModule("server/WorkshopSimulation")
local GoodsMotion = loadModule("shared/GoodsMotion")
local Config, Machines = D.Config, D.Machines

local results = { passed = 0, failed = {}, names = {}, info = {} }
local function test(group, name, fn)
	local okk, err = pcall(fn)
	if okk then
		results.passed = results.passed + 1
		results.names[#results.names + 1] = group .. ": " .. name
	else
		results.failed[#results.failed + 1] = group .. ": " .. name .. " -> " .. tostring(err)
	end
end
local function check(cond, msg) if not cond then error(msg, 2) end end

local CARRIER = { belt = true, splitter = true, merger = true, sorter = true, lift = true, gate = true }
local PERIOD = { belt = "beltSecondsPerItem", lift = "liftSecondsPerItem", gate = "gateSecondsPerItem" }
local CS = Config.cellSize
local FPS = 60

-- crate -> hopper -> 5 belts east -> belt turning north (side entry) -> 3 belts north -> crate
local function line()
	local P = Profile.new(77)
	P.workshop.layout, P.workshop.buffers, P.workshop.nextUid = {}, {}, 1
	P.workshop.sizeTier, P.wallet, P.items = 2, 100000, {}
	for id in pairs(D.Research) do P.research[id] = true end
	local function put(m, gx, gz, rot)
		local e, code = Place.place(P, m, gx, gz, 1, rot)
		if not e then error("cannot place " .. m .. ": " .. tostring(code)) end
		return e
	end
	local source = put("storage_crate", 2, 10, 0)
	P.workshop.buffers[source.uid].inv.herb_mint = 40
	put("input_hopper", 4, 10, 1)
	for x = 5, 9 do put("wooden_belt", x, 10, 1) end
	put("wooden_belt", 10, 10, 0)
	for z = 11, 13 do put("wooden_belt", 10, z, 0) end
	local target = put("storage_crate", 10, 14, 0)
	return P, source, target
end

-- the client: carriers registered like GoodsAnimator does from the part attributes
local function client(P)
	local m = GoodsMotion.new(CS)
	for _, e in ipairs(P.workshop.layout) do
		local def = Machines[e.machine]
		if CARRIER[def.kind] then
			local outs, out = 0, e.rot % 4
			for _, p in ipairs(def.ports) do
				if p.mode == "out" then
					outs = outs + 1
					if outs == 1 then out = (p.dir + e.rot) % 4 end
				end
			end
			local partner
			for _, other in ipairs(P.workshop.layout) do if other.uid == e.link then partner = other end end
			local links = GoodsMotion.links(def, e, partner)
			local c = { room = 1, floor = e.floor, gx = e.gx, gz = e.gz, x = e.gx * CS + CS / 2, y = (e.floor - 1) * Config.floorHeight,
				z = e.gz * CS + CS / 2, out = outs == 1 and out or -1, next = links.next,
				rise = links.rise and links.rise * Config.floorHeight or nil,
				period = PERIOD[def.kind] and Config.sim[PERIOD[def.kind]] or 0.5 }
			if links.warp then
				local w = links.warp
				c.warp = { x = w.gx * CS + CS / 2, y = (w.floor - 1) * Config.floorHeight, z = w.gz * CS + CS / 2, out = w.out }
			end
			m:setCarrier(e.uid, c)
		end
	end
	return m
end

-- runs server and client together; observe(frame) is called after every client frame
local function run(P, rt, m, state, seconds, observe)
	local frames = math.floor(seconds * FPS + 0.5)
	for _ = 1, frames do
		state.t = state.t + 1 / FPS
		while state.simT + Config.sim.tick <= state.t + 1e-9 do
			state.simT = state.simT + Config.sim.tick
			Sim.step(P, rt, Config.sim.tick)
		end
		if state.t - state.lastSync >= 0.2 - 1e-9 then          -- server: WorkshopWorld:syncGoods
			state.lastSync = state.t
			state.n = state.n + 1
			local latency = 0.08 + 0.12 * ((state.n * 7) % 10) / 10
			for _, e in ipairs(P.workshop.layout) do
				if CARRIER[Machines[e.machine].kind] then
					local b = P.workshop.buffers[e.uid]
					local pub = state.pub[e.uid] or {}
					local at = b.item and (state.simT - (b.t or 0)) or nil
					if b.item ~= pub.item or (b.item and math.abs(at - pub.at) > 0.25) then
						pub = { item = b.item, at = at, inDir = b.inDir }
						state.pub[e.uid] = pub
						state.queue[#state.queue + 1] = { due = state.t + latency, uid = e.uid, item = pub.item, at = pub.at, inDir = pub.inDir }
					end
				end
			end
		end
		local keep = {}
		for _, msg in ipairs(state.queue) do                   -- network: in order per part
			if msg.due <= state.t then m:setState(msg.uid, msg.item, msg.at, msg.inDir, state.t)
			else keep[#keep + 1] = msg end
		end
		state.queue = keep
		m:step(state.t, 1 / FPS)
		observe()
	end
end

-- measures the drawn motion
local function meter(m)
	local s = { last = {}, maxStep = 0, frames = 0, still = 0, moving = 0, maxCount = 0, minGap = math.huge }
	function s.observe()
		local list = {}
		for serial, v in pairs(m.visuals) do
			list[#list + 1] = v
			local last = s.last[serial]
			if last then
				local d = math.sqrt((v.x - last.x) ^ 2 + (v.z - last.z) ^ 2)
				s.maxStep = math.max(s.maxStep, d)
				-- inside the moving part of the line (between the first and the last belt)
				if v.z > 20 and v.z < 22 and v.x > 12 and v.x < 19 then
					s.moving = s.moving + 1
					if d < 0.3 * CS / Config.sim.beltSecondsPerItem / FPS then s.still = s.still + 1 end
				end
			end
			s.last[serial] = { x = v.x, z = v.z }
		end
		for i = 1, #list do
			for j = i + 1, #list do
				s.minGap = math.min(s.minGap, math.sqrt((list[i].x - list[j].x) ^ 2 + (list[i].z - list[j].z) ^ 2))
			end
		end
		s.maxCount = math.max(s.maxCount, #list)
		s.frames = s.frames + 1
	end
	return s
end

local function onCarriers(P)
	local n = 0
	for _, e in ipairs(P.workshop.layout) do
		if CARRIER[Machines[e.machine].kind] and P.workshop.buffers[e.uid].item then n = n + 1 end
	end
	return n
end

test("goods", "a full belt glides: no stop, no jump, one visual per item", function()
	local P = line()
	local rt = Sim.newRuntime()
	local m = client(P)
	local state = { t = 0, simT = 0, lastSync = -1, n = 0, pub = {}, queue = {} }
	run(P, rt, m, state, 20, function() end)                    -- fill the line
	local s = meter(m)
	run(P, rt, m, state, 40, s.observe)
	local nominal = CS / Config.sim.beltSecondsPerItem / FPS   -- studs per frame
	results.info[#results.info + 1] = string.format("full line: %d frames, largest step %.4f studs (nominal %.4f), %d of %d moving-section samples standing, %d visuals at most, %d items on belts, smallest gap %.2f studs",
		s.frames, s.maxStep, nominal, s.still, s.moving, s.maxCount, onCarriers(P), s.minGap)
	check(s.moving > 1000, "the line moved")
	check(s.maxStep < nominal * 2.2, "a visual jumped")
	check(s.still == 0, "a visual stopped inside the moving line")
	check(s.maxCount <= onCarriers(P) + 1, "more visuals than items")
	-- one cell apart along the path; at the corner that is sqrt(2) studs in a straight line
	check(s.minGap > CS * 0.65, "two visuals overlap")
end)

test("goods", "blocking and releasing the end: the queue stops in place and starts again without jumps", function()
	local P, _, target = line()
	local rt = Sim.newRuntime()
	local m = client(P)
	local state = { t = 0, simT = 0, lastSync = -1, n = 0, pub = {}, queue = {} }
	run(P, rt, m, state, 20, function() end)
	Place.remove(P, target.uid)                                 -- the end of the line is blocked now
	rt.dirty = true
	local s = meter(m)
	run(P, rt, m, state, 30, s.observe)
	local count = 0
	for _ in pairs(m.visuals) do count = count + 1 end
	check(s.maxStep < CS / Config.sim.beltSecondsPerItem / FPS * 2.2, "jump while blocked")
	check(count == onCarriers(P), "visuals " .. count .. " vs items " .. onCarriers(P))
	local before = {}
	for serial, v in pairs(m.visuals) do before[serial] = { x = v.x, z = v.z } end
	run(P, rt, m, state, 2, function() end)
	for serial, v in pairs(m.visuals) do
		local b = before[serial]
		check(b and math.abs(b.x - v.x) + math.abs(b.z - v.z) < 1e-3, "a blocked item still moves")
	end
	Place.place(P, "storage_crate", 10, 14, 1, 0)               -- free the end again
	rt.dirty = true
	local s2 = meter(m)
	run(P, rt, m, state, 30, s2.observe)
	results.info[#results.info + 1] = string.format("blocked: %d visuals = %d items, largest step %.4f; released: largest step %.4f, %d standing samples",
		count, onCarriers(P), s.maxStep, s2.maxStep, s2.still)
	check(s2.maxStep < CS / Config.sim.beltSecondsPerItem / FPS * 2.2, "jump after release")
	check(s2.moving > 500, "the line moves again")
end)

test("goods", "the server moves a full line in one tick (transfer order)", function()
	local P = line()
	local rt = Sim.newRuntime()
	for _ = 1, 100 do Sim.step(P, rt, Config.sim.tick) end
	local belts = {}
	for _, e in ipairs(P.workshop.layout) do
		if e.machine == "wooden_belt" then belts[#belts + 1] = P.workshop.buffers[e.uid] end
	end
	-- in a full, moving line all items arrived in the same tick: equal time on their belt
	local t0 = belts[1].t
	for _, b in ipairs(belts) do
		check(b.item ~= nil, "line is full")
		check(math.abs(b.t - t0) < 1e-9, "belts out of step: " .. b.t .. " vs " .. t0)
	end
end)

-- crate -> hopper -> belts -> (lift up one floor | gate to a partner gate) -> belts -> crate
local function special(kind)
	local P = Profile.new(78)
	P.workshop.layout, P.workshop.buffers, P.workshop.nextUid = {}, {}, 1
	P.workshop.sizeTier, P.workshop.floors, P.wallet, P.items = 2, 2, 100000, {}
	for id in pairs(D.Research) do P.research[id] = true end
	local function put(m, gx, gz, floor, rot)
		local e, code = Place.place(P, m, gx, gz, floor, rot)
		if not e then error("cannot place " .. m .. " at " .. gx .. "," .. gz .. "/" .. floor .. ": " .. tostring(code)) end
		return e
	end
	local source = put("storage_crate", 4, 8, 1, 0)
	P.workshop.buffers[source.uid].inv.herb_mint = 12
	put("input_hopper", 6, 8, 1, 1)
	put("wooden_belt", 7, 8, 1, 1)
	put("wooden_belt", 8, 8, 1, 1)
	local floor2, x0 = 1, 10
	if kind == "lift" then
		put("vertical_lift", 9, 8, 1, 1)                     -- hands over on floor 2, at (10, 8)
		floor2 = 2
	else
		local a = put("magical_gate", 9, 8, 1, 1)
		local b = put("magical_gate", 14, 14, 1, 1)          -- somewhere else; goods leave it to (15, 14)
		a.link = b.uid
		x0 = 15
	end
	local z0 = (kind == "lift") and 8 or 14
	for x = x0, x0 + 2 do put("wooden_belt", x, z0, floor2, 1) end
	put("storage_crate", x0 + 3, z0, floor2, 0)
	return P
end

for _, kind in ipairs({ "lift", "gate" }) do
	test("goods", "goods travel through the " .. kind .. " as one object, without jumping", function()
		local P = special(kind)
		local rt = Sim.newRuntime()
		local m = client(P)
		local state = { t = 0, simT = 0, lastSync = -1, n = 0, pub = {}, queue = {} }
		local last, through, worst, smallest, rose = {}, 0, 0, 1, 0
		local entered = {}
		run(P, rt, m, state, 40, function()
			for serial, v in pairs(m.visuals) do
				local l = last[serial]
				if l then
					local d = math.sqrt((v.x - l.x) ^ 2 + (v.y - l.y) ^ 2 + (v.z - l.z) ^ 2)
					-- the portal may move an object only while it is (almost) invisible
					if d > CS * 1.5 then check(l.scale < 0.1 or v.scale < 0.1, "visible jump of " .. d) else worst = math.max(worst, d) end
				end
				if v.x < 19 then entered[serial] = true end
				if entered[serial] and (v.x > 20.5 and (kind == "gate" and v.z > 25 or v.y > Config.floorHeight - 0.5)) then
					if not (l and l.counted) then through = through + 1 end
					v.counted = true
				end
				smallest = math.min(smallest, v.scale)
				rose = math.max(rose, v.y)
				last[serial] = { x = v.x, y = v.y, z = v.z, scale = v.scale, counted = v.counted or (l and l.counted) }
			end
		end)
		results.info[#results.info + 1] = string.format("%s: %d items carried through as the same object, largest step %.3f studs, smallest scale %.2f, highest point %.1f studs",
			kind, through, worst, smallest, rose)
		check(through >= 5, "goods carried through as the same object")
		check(worst < 0.3, "jump of " .. worst)
		if kind == "gate" then check(smallest < 0.05, "shrinks into the portal") end
		if kind == "lift" then check(rose > Config.floorHeight - 0.5, "climbs one floor") end
	end)
end

return results
