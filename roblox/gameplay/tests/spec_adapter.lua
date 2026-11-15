-- save (DataStore adapter with a mock store) and integration (anchors on the real generated layout).
local D = loadModule("server/Data")
local Store = loadModule("server/ProfileStore")
local Profile = loadModule("server/ProfileService")
local Adapter = loadModule("server/VillageAdapter")
local Game = loadModule("server/Game")
local Actions = loadModule("server/Actions")
local Locations, Util = D.Locations, D.Util
local results = { passed = 0, failed = {}, names = {}, info = {} }
local function test(group, name, fn)
	local okk, err = pcall(fn)
	if okk then results.passed = results.passed + 1 results.names[#results.names + 1] = group .. ": " .. name
	else results.failed[#results.failed + 1] = group .. ": " .. name .. " -> " .. tostring(err) end
end
local function eq(a, b, msg) if a ~= b then error((msg or "differs") .. ": got " .. tostring(a) .. ", expected " .. tostring(b), 2) end end

local function mockStore()
	local s = { data = {}, failNext = 0, calls = 0 }
	function s:UpdateAsync(key, fn)
		self.calls = self.calls + 1
		if self.failNext > 0 then self.failNext = self.failNext - 1 error("DataStore request failed (mock)") end
		local new = fn(Util.deepCopy(self.data[key]))
		if new ~= nil then self.data[key] = Util.deepCopy(new) end
		return new
	end
	return s
end
local clock = 1000
local function newStore(mock, serverId)
	return Store.new({ store = mock, serverId = serverId, now = function() return clock end })
end

test("save", "first load is new, save + reload returns the same data", function()
	local mock = mockStore()
	local st = newStore(mock, "A")
	local P, status = st:load(7)
	eq(status, "new")
	P.wallet = 321 P.items.stone = 9
	eq(st:save(7, P, true), true)
	local P2, status2 = newStore(mock, "B"):load(7)
	eq(status2, "ok") eq(P2.wallet, 321) eq(P2.items.stone, 9) eq(mock.data["player:7"].revision, 1)
end)
test("save", "a failing DataStore never produces an overwriting default profile", function()
	local mock = mockStore()
	local st = newStore(mock, "A")
	local P = st:load(7) P.wallet = 999
	st:save(7, P, true)
	mock.failNext = 99
	local st2 = newStore(mock, "B")
	local P2, status = st2:load(7)
	eq(P2, nil) eq(status, "failed")
	local okSave, reason = st2:save(7, Profile.new(7), true)
	eq(okSave, false) eq(reason, "not loaded")
	mock.failNext = 0
	eq(mock.data["player:7"].profile.wallet, 999)
end)
test("save", "transient errors are retried, a failed save reports failure", function()
	local mock = mockStore()
	local st = newStore(mock, "A")
	local P = st:load(7)
	mock.failNext = 2
	eq(st:save(7, P), true)
	mock.failNext = 5
	local okSave = st:save(7, P)
	eq(okSave, false) eq(mock.data["player:7"].revision, 1)
	mock.failNext = 0
	eq(st:save(7, P), true) eq(mock.data["player:7"].revision, 2)
end)
test("save", "session lock: a second server cannot load or overwrite, stale locks expire", function()
	local mock = mockStore()
	local a, b = newStore(mock, "A"), newStore(mock, "B")
	local P = a:load(7) a:save(7, P)
	local P2, status = b:load(7)
	eq(P2, nil) eq(status, "locked")
	clock = clock + Store.LOCK_STALE_SEC + 1
	local P3, status3 = b:load(7)
	eq(status3, "ok") P3.wallet = 5
	eq(b:save(7, P3), true)
	P.wallet = 77777                       -- server A still holds an old copy
	local okSave, reason = a:save(7, P)
	eq(okSave, false) eq(reason, "newer revision exists")
	eq(mock.data["player:7"].profile.wallet, 5)
end)
test("save", "corrupt documents are refused, damaged ones repaired and reported", function()
	local mock = mockStore()
	mock.data["player:8"] = { revision = 3, profile = "broken" }
	local P, status = newStore(mock, "A"):load(8)
	eq(P, nil) eq(status, "corrupt")
	local good = Profile.serialize(Profile.new(9))
	good.wallet = -1
	mock.data["player:9"] = { revision = 1, profile = good }
	local P9, status9 = newStore(mock, "A"):load(9)
	eq(status9, "repaired") eq(P9.wallet, 0)
end)
test("save", "save during a running craft and rejoin on another server loses nothing", function()
	local mock = mockStore()
	local a = newStore(mock, "A")
	local world = Game.newWorld({ workshop_door = { x = 0, z = 0 } }, {})
	local s = Game.addSession(world, 7, (a:load(7)))
	Game.updatePosition(world, s, 0, 0)
	Actions.handle(world, s, "EnterWorkshop", {}, { now = 1 })
	Actions.handle(world, s, "StartManualCraft", { uid = "m1", recipe = "r01" }, { now = 2 })
	for _ = 1, 12 do Game.tick(world, 0.25, 3) end
	eq(a:save(7, s.profile, true), true)             -- player quits 3 s into an 8 s craft
	local P2 = newStore(mock, "B"):load(7)
	local job = P2.workshop.buffers.m1.job
	eq(job.recipe, "r01") eq(job.remaining, 5)
	eq(P2.items.herb_mint, 2) eq(P2.items.tonic_minor, nil)
	local world2 = Game.newWorld({}, {})
	Game.addSession(world2, 7, P2)
	for _ = 1, 24 do Game.tick(world2, 0.25, 4) end
	eq(P2.workshop.buffers.m1.out.tonic_minor, 1)
end)

-- ---- integration with the generated village ----
local layout = WORLD_LAYOUT
local anchors, nodeAnchors, missing = Adapter.computeAnchors(layout)
test("integration", "every location has a building instance in the generated layout", function()
	eq(#missing, 0, "missing: " .. table.concat(missing, ","))
	eq(Util.count(anchors), Util.count(Locations.locations))
	eq(Util.count(nodeAnchors), Util.count(Locations.nodes))
end)
-- oriented footprints of all buildings (Roblox space) for clearance checks
local footprints = {}
for _, row in ipairs(layout.instances) do
	local name = layout.assetNames[row[1]]
	local def = layout.assets[name]
	if def.category == "houses" or def.category == "landmarks" then
		footprints[#footprints + 1] = { name = name, x = row[2], z = row[4], yaw = math.rad(row[5]),
			cx = def.center[1], cz = def.center[3], hx = def.size[1] / 2, hz = def.size[3] / 2 }
	end
end
local function insideBuilding(x, z, margin, skip)
	for _, f in ipairs(footprints) do
		if f.name ~= skip then
			local dx, dz = x - f.x, z - f.z
			local lx = dx * math.cos(f.yaw) - dz * math.sin(f.yaw) - f.cx
			local lz = dx * math.sin(f.yaw) + dz * math.cos(f.yaw) - f.cz
			if math.abs(lx) < f.hx + margin and math.abs(lz) < f.hz + margin then return f.name end
		end
	end
	return nil
end
test("integration", "anchors stand in front of their building, outside every building, inside the world", function()
	local half = layout.worldSize / 2
	for id, a in pairs(anchors) do
		local hit = insideBuilding(a.x, a.z, 0.5, nil)
		if id == "plaza" or id == "pond" or id == "bridge" then hit = insideBuilding(a.x, a.z, 0.5, nil) end
		eq(hit, nil, "anchor " .. id .. " inside building")
		assert(math.abs(a.x) < half - 8 and math.abs(a.z) < half - 8, "anchor " .. id .. " outside world")
		local own = Locations.locations[id].asset
		local d = math.sqrt((a.x - a.originX) ^ 2 + (a.z - a.originZ) ^ 2)
		assert(d < 60, "anchor " .. id .. " too far from " .. own)
	end
end)
test("integration", "resource nodes are reachable: outside buildings, inside the world, apart from each other", function()
	local half = layout.worldSize / 2
	local ids = Util.sortedKeys(nodeAnchors)
	for i, id in ipairs(ids) do
		local n = nodeAnchors[id]
		eq(insideBuilding(n.x, n.z, 1.0, nil), nil, "node " .. id .. " inside building")
		assert(math.abs(n.x) < half - 8 and math.abs(n.z) < half - 8, "node " .. id .. " outside world")
		for j = i + 1, #ids do
			local m = nodeAnchors[ids[j]]
			assert((n.x - m.x) ^ 2 + (n.z - m.z) ^ 2 > 9, "nodes " .. id .. " and " .. ids[j] .. " overlap")
		end
	end
end)
test("integration", "spawn, workshop door and starter resources are close together", function()
	local sx, sz = layout.spawn[1], layout.spawn[3]
	local door = anchors.workshop_door
	local dDoor = math.sqrt((door.x - sx) ^ 2 + (door.z - sz) ^ 2)
	assert(dDoor < 140, "door is " .. dDoor .. " studs from spawn")
	for _, id in ipairs({ "n_mint_plaza", "n_sunleaf_plaza", "n_water_fountain", "n_mint_door" }) do
		local n = nodeAnchors[id]
		assert(math.sqrt((n.x - sx) ^ 2 + (n.z - sz) ^ 2) < 160, id .. " too far from spawn")
	end
	results.info[#results.info + 1] = string.format("spawn -> workshop door: %.0f studs; %d building footprints checked", dDoor, #footprints)
end)
test("integration", "the real anchors drive a full first sale", function()
	local world = Game.newWorld(anchors, nodeAnchors)
	local s = Game.addSession(world, 11)
	local now = 100
	local function act(action, payload)
		now = now + 1
		local r = Actions.handle(world, s, action, payload or {}, { now = now })
		assert(r.ok, action .. " " .. tostring(r.code))
		return r.payload
	end
	local a = nodeAnchors.n_mint_plaza
	Game.updatePosition(world, s, a.x, a.z)
	act("GatherNode", { node = "n_mint_plaza" })
	Game.updatePosition(world, s, anchors.workshop_door.x, anchors.workshop_door.z)
	act("EnterWorkshop")
	act("StartManualCraft", { uid = "m1", recipe = "r01" })
	for _ = 1, 40 do Game.tick(world, 0.25, now) end
	act("TransferStack", { from = "m1", to = "inv", item = "tonic_minor", amount = 1 })
	act("StockShelf", { uid = "m3", item = "tonic_minor", amount = 1 })
	for _ = 1, 400 do Game.tick(world, 0.25, now) end
	eq(s.profile.stats.sold, 1)
	assert(s.profile.quest.main >= 4, "tutorial quests q01-q03 done")
end)
return results
