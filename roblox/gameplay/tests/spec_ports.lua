-- Inlet / outlet sides of machines, automatic outlets and a complete production line.
-- Mirrors the acceptance scenarios of the production rework. Returns { passed, failed, names }.
local D = loadModule("server/Data")
local Game = loadModule("server/Game")
local Place = loadModule("server/PlacementService")
local Profile = loadModule("server/ProfileService")
local Sim = loadModule("server/WorkshopSimulation")
local Bot = loadModule("tests/bot")
local Config, Machines, Ports, Grid = D.Config, D.Machines, D.MachinePorts, D.GridMath

local results = { passed = 0, failed = {}, names = {} }
local function test(group, name, fn)
	local okk, err = pcall(fn)
	if okk then
		results.passed = results.passed + 1
		results.names[#results.names + 1] = group .. ": " .. name
	else
		results.failed[#results.failed + 1] = group .. ": " .. name .. " -> " .. tostring(err)
	end
end
local function eq(a, b, msg)
	if a ~= b then error((msg or "values differ") .. ": got " .. tostring(a) .. ", expected " .. tostring(b), 2) end
end

-- A roomy workshop with everything unlocked and nothing in it.
local function workshop()
	local P = Profile.new(4242)
	P.workshop.layout, P.workshop.buffers, P.workshop.nextUid = {}, {}, 1
	P.workshop.sizeTier = 2
	P.wallet = 100000
	P.items = {}
	for id in pairs(D.Research) do P.research[id] = true end
	return P
end
local function place(P, machine, gx, gz, rot)
	local e, code = Place.place(P, machine, gx, gz, 1, rot or 0)
	if not e then error("cannot place " .. machine .. " at " .. gx .. "," .. gz .. ": " .. tostring(code), 2) end
	return e
end
-- cell in front of the connection of `side` and the direction leading away from the machine
local function beyond(e, side)
	local def = Machines[e.machine]
	local x, z, dir = Ports.cell(def, e, side)
	return x + Grid.DX[dir], z + Grid.DZ[dir], dir
end
local function outSide(e) local _, o = Ports.sides(Machines[e.machine], e) return o end
local function inSide(e) local i = Ports.sides(Machines[e.machine], e) return i end
local function run(P, rt, seconds)
	rt.dirty = true
	for _ = 1, math.ceil(seconds / Config.sim.tick) do Sim.step(P, rt, Config.sim.tick) end
end
-- every mint leaf and every pinch of powder anywhere (2 mint -> 2 powder, so the sum is constant)
local function census(P)
	local n = (P.items.herb_mint or 0) + (P.items.mint_powder or 0)
	for uid in pairs(P.workshop.buffers) do
		local all = Place.contents(P, uid)
		n = n + (all.herb_mint or 0) + (all.mint_powder or 0)
	end
	return n
end

test("ports", "defaults: inlet at the back, outlet at the front, automatic; old saves keep them", function()
	local P = workshop()
	local g = place(P, "grinder", 10, 10)
	eq(inSide(g), 2) eq(outSide(g), 0) eq(Ports.isAuto(g), true)
	eq(g.inSide, nil) eq(g.outSide, nil)                    -- nothing stored: same data as an old save
	local loaded = Profile.load(Profile.serialize(P, 1), 4242)
	local lg = Place.find(loaded, g.uid)
	eq(inSide(lg), 2) eq(outSide(lg), 0) eq(Ports.isAuto(lg), true)
end)

test("ports", "a belt leading away from a connection becomes the automatic outlet; other belts do not", function()
	local P = workshop()
	local g = place(P, "grinder", 10, 10)
	local x, z, dir = beyond(g, 1)                           -- right side
	-- wrong: runs towards the machine, runs past sideways (both ways)
	for _, rot in ipairs({ (dir + 2) % 4, (dir + 1) % 4, (dir + 3) % 4 }) do
		local b = place(P, "wooden_belt", x, z, rot)
		eq(outSide(g), 0, "belt with rot " .. rot .. " must not attract the outlet")
		Place.remove(P, b.uid)
	end
	-- wrong: next to the machine, but not at the connection cell (the other cell of that edge)
	local side = place(P, "wooden_belt", x, z + 1, dir)
	eq(outSide(g), 0)
	-- wrong: diagonal
	local diag = place(P, "wooden_belt", x, z - 1, dir)
	eq(outSide(g), 0)
	Place.remove(P, side.uid) Place.remove(P, diag.uid)
	-- right: straight in front of the connection, leading away
	place(P, "wooden_belt", x, z, dir)
	eq(outSide(g), 1) eq(Ports.isAuto(g), true)
end)

test("ports", "manual outlet stays through new belts and a reload; automatic takes over again", function()
	local P = workshop()
	local g = place(P, "grinder", 10, 10)
	local res = Place.setPorts(P, g.uid, nil, 3, nil)        -- player picks the left side
	eq(res.outSide, 3) eq(res.auto, false)
	local x, z, dir = beyond(g, 1)
	place(P, "wooden_belt", x, z, dir)                        -- a perfectly suitable belt on the right
	eq(outSide(g), 3)
	local loaded = Profile.load(Profile.serialize(P, 5), 4242)
	local lg = Place.find(loaded, g.uid)
	eq(outSide(lg), 3) eq(Ports.isAuto(lg), false)
	place(loaded, "wooden_belt", 20, 20, 0)                   -- any change re-checks the outlets
	eq(outSide(lg), 3)
	res = Place.setPorts(loaded, lg.uid, nil, nil, true)
	eq(res.auto, true) eq(res.outSide, 1) eq(outSide(lg), 1)
end)

test("ports", "choosing the side of the other connection swaps them; fluid sides and bad values are refused", function()
	local P = workshop()
	local g = place(P, "grinder", 10, 10)
	local res = Place.setPorts(P, g.uid, 0, nil, nil)        -- inlet onto the outlet side
	eq(res.inSide, 0) eq(res.outSide, 2)
	res = Place.setPorts(P, g.uid, nil, 0, nil)              -- outlet back onto the inlet side
	eq(res.inSide, 2) eq(res.outSide, 0) eq(res.auto, false)
	local _, code = Place.setPorts(P, g.uid, 1, 1, nil)
	eq(code, "BAD_REQUEST")
	_, code = Place.setPorts(P, g.uid, 4, nil, nil)
	eq(code, "BLOCKED")
	local k = place(P, "kettle", 14, 14)                     -- water comes in on the left
	_, code = Place.setPorts(P, k.uid, nil, 3, nil)
	eq(code, "BLOCKED")
	local sides = Ports.solidSides(Machines.kettle)
	eq(#sides, 3)
	local belt = place(P, "wooden_belt", 3, 3, 0)
	_, code = Place.setPorts(P, belt.uid, 1, nil, nil)
	eq(code, "NOT_FOUND")
end)

test("ports", "same result in both building orders, for a turned 3 x 2 machine", function()
	for _, rot in ipairs({ 0, 1, 2, 3 }) do
		local A = workshop()
		local saw = place(A, "saw", 10, 10, rot)
		local x, z, dir = beyond(saw, 1)
		place(A, "wooden_belt", x, z, dir)
		eq(outSide(saw), 1, "machine first, rot " .. rot)
		-- the connection is the middle cell of the turned edge
		local w, d = Grid.size(Machines.saw, rot)
		local px, pz = Ports.cell(Machines.saw, saw, 1)
		eq(px >= 10 and px < 10 + w and pz >= 10 and pz < 10 + d, true, "connection cell inside the footprint")

		local B = workshop()
		place(B, "wooden_belt", x, z, dir)
		local saw2 = place(B, "saw", 10, 10, rot)
		eq(outSide(saw2), 1, "belt first, rot " .. rot)
	end
end)

test("ports", "the chosen sides turn with the machine", function()
	local P = workshop()
	local g = place(P, "grinder", 10, 10)
	Place.setPorts(P, g.uid, 3, 1, nil)
	local _, _, dirBefore = Ports.cell(Machines.grinder, g, 1)
	Place.rotate(P, g.uid)
	eq(inSide(g), 3) eq(outSide(g), 1)
	local _, _, dirAfter = Ports.cell(Machines.grinder, g, 1)
	eq(dirAfter, (dirBefore + 1) % 4)
end)

test("ports", "two suitable belts: the current outlet stays; removing it moves the outlet on", function()
	local P = workshop()
	local g = place(P, "grinder", 10, 10)
	local x1, z1, d1 = beyond(g, 1)
	local right = place(P, "wooden_belt", x1, z1, d1)
	eq(outSide(g), 1)
	local x0, z0, d0 = beyond(g, 0)
	local front = place(P, "wooden_belt", x0, z0, d0)        -- the definition's default side, also suitable
	eq(outSide(g), 1, "current automatic side stays while valid")
	Place.remove(P, right.uid)
	eq(outSide(g), 0, "falls back to the default side first")
	Place.remove(P, front.uid)
	eq(outSide(g), 0, "without any belt the outlet stays where it is")
	-- turning a belt is re-checked as well
	local again = place(P, "wooden_belt", x1, z1, (d1 + 1) % 4)
	eq(outSide(g), 0)
	for _ = 1, 3 do Place.rotate(P, again.uid) end
	eq(again.rot, d1) eq(outSide(g), 1)
end)

test("ports", "full line crate -> hopper -> belt -> mill -> belt -> crate; blocking loses and creates nothing", function()
	local P = workshop()
	local rt = Sim.newRuntime()
	local mill = place(P, "grinder", 12, 10)
	mill.recipe = "r06"                                       -- 2 mint -> 2 mint powder
	Place.setPorts(P, mill.uid, 3, nil, nil)                  -- inlet on the left
	local ix, iz, idir = beyond(mill, 3)
	place(P, "wooden_belt", ix, iz, (idir + 2) % 4)           -- leads into the mill
	place(P, "input_hopper", ix - 1, iz, (idir + 2) % 4)
	local source = place(P, "storage_crate", ix - 3, iz)
	P.workshop.buffers[source.uid].inv.herb_mint = 60       -- more than fits behind a blocked outlet
	local ox, oz, odir = beyond(mill, 1)
	place(P, "wooden_belt", ox, oz, odir)
	place(P, "wooden_belt", ox + 1, oz, odir)
	local target = place(P, "storage_crate", ox + 2, oz)
	eq(outSide(mill), 1) eq(Ports.isAuto(mill), true)
	local total = census(P)
	eq(total, 60)

	run(P, rt, 60)
	local mb = P.workshop.buffers[mill.uid]
	eq(census(P), total, "after 60 s")
	eq((P.workshop.buffers[target.uid].inv.mint_powder or 0) > 0, true, "powder arrives in the target crate")

	-- block the outlet: take the target crate away (its contents go to the player's bag)
	Place.remove(P, target.uid)
	run(P, rt, 240)
	eq(census(P), total, "while blocked")
	eq(mb.state, "OutputBlocked")
	eq(mb.out.mint_powder, Config.machine.outputCap)
	eq(mb.job ~= nil and mb.job.remaining == 0, true, "the finished batch waits inside the machine")

	-- free it again
	local target2 = place(P, "storage_crate", ox + 2, oz)
	run(P, rt, 900)
	eq(census(P), total, "after the release")
	eq(P.workshop.buffers[source.uid].inv.herb_mint, nil, "all mint was used")
	eq((P.workshop.buffers[target2.uid].inv.mint_powder or 0) + (P.items.mint_powder or 0), 60, "every leaf became powder")
	eq(mb.state, "WaitingForInputs") eq(mb.waiting, "herb_mint")
end)

test("ports", "the action is checked on the server and the view reports sides, progress and reasons", function()
	local bot = Bot.new()
	for id in pairs(D.Research) do bot.P.research[id] = true end
	bot.P.wallet = 5000
	bot:enter()
	local kettle = bot:entitiesOf("kettle")[1]
	local res = bot:act("SetMachinePorts", { uid = kettle.uid, outSide = 1 })
	eq(res.outSide, 1) eq(res.auto, false)
	eq(bot:try("SetMachinePorts", { uid = kettle.uid, outSide = 3 }).code, "BLOCKED")       -- water inlet
	eq(bot:try("SetMachinePorts", { uid = kettle.uid, inSide = 9 }).code, "BLOCKED")
	eq(bot:try("SetMachinePorts", { uid = "nope" }).code, "NOT_FOUND")
	eq(bot:act("SetMachinePorts", { uid = kettle.uid, auto = true }).auto, true)
	local function view()
		for _, v in ipairs(Game.snapshot(bot.world, bot.session).workshop.entities) do
			if v.uid == kettle.uid then return v end
		end
	end
	local v = view()
	eq(v.inSide, 2) eq(v.outSide, 1) eq(v.outAuto, true)
	-- a guest without building rights may not change connections
	local guest = Bot.new(bot.world, 2002)
	bot:act("InviteCoOp", { user = guest.userId, role = "visitor" })
	guest:goTo("workshop_door")
	guest:act("EnterWorkshop", { owner = bot.userId })
	eq(guest:try("SetMachinePorts", { uid = kettle.uid, outSide = 0 }).code, "FORBIDDEN")
	-- progress and the reason for standing still
	bot.P.items.herb_mint, bot.P.items.water = 2, 1000
	bot:act("StartManualCraft", { uid = kettle.uid, recipe = "r01" })
	bot:tick(3)
	v = view()
	eq(v.state, "Running") eq(v.job.total, 8) eq(v.job.remaining < 8 and v.job.remaining > 0, true)
	bot:tick(8)
	v = view()
	eq(v.out.tonic_minor, 1) eq(v.state, "WaitingForInputs") eq(v.waiting ~= nil, true)
end)

local BeltPath = D.BeltPath
test("belts", "a line runs along the longer axis first, every belt points to the next, one corner", function()
	local cells = BeltPath.cells(2, 3, 7, 5, 1, false)
	eq(#cells, 8)
	eq(cells[1].gx, 2) eq(cells[1].gz, 3) eq(cells[1].rot, 1)
	eq(cells[5].gx, 6) eq(cells[5].rot, 1)
	eq(cells[6].gx, 7) eq(cells[6].gz, 3) eq(cells[6].rot, 0)          -- the corner turns to +z
	eq(cells[8].gx, 7) eq(cells[8].gz, 5) eq(cells[8].rot, 0)
	local back = BeltPath.cells(2, 3, 7, 5, 1, true)                   -- reversed flow
	eq(back[1].gx, 7) eq(back[1].gz, 5) eq(back[1].rot, 2)
	eq(back[8].gx, 2) eq(back[8].gz, 3) eq(back[8].rot, 3)
	local one = BeltPath.cells(4, 4, 4, 4, 3, false)
	eq(#one, 1) eq(one[1].rot, 3)
	eq(BeltPath.cells(4, 4, 4, 4, 3, true)[1].rot, 1)
	eq(BeltPath.cells(0, 0, 70, 0, 1, false), nil)                     -- longer than MAX
end)

test("belts", "a line is placed completely or not at all", function()
	local P = workshop()
	place(P, "storage_crate", 10, 6)                                    -- in the way of the line
	local wallet, before = P.wallet, #P.workshop.layout
	local uids, code, index = Place.placeLine(P, "wooden_belt", 1, BeltPath.cells(6, 6, 14, 6, 1, false))
	eq(uids, nil) eq(code, "BLOCKED") eq(index, 5)
	eq(P.wallet, wallet) eq(#P.workshop.layout, before)
	uids = Place.placeLine(P, "wooden_belt", 1, BeltPath.cells(6, 8, 14, 8, 1, false))
	eq(#uids, 9) eq(P.wallet, wallet - 9 * Machines.wooden_belt.cost)
	eq(select(2, Place.placeLine(P, "grinder", 1, BeltPath.cells(6, 12, 8, 12, 1, false))), "BAD_REQUEST")
end)

test("belts", "goods run through a placed line with a corner, from a hopper into a crate", function()
	local P = workshop()
	local rt = Sim.newRuntime()
	local source = place(P, "storage_crate", 2, 10)
	P.workshop.buffers[source.uid].inv.herb_mint = 6
	place(P, "input_hopper", 4, 10, 1)
	assert(Place.placeLine(P, "wooden_belt", 1, BeltPath.cells(5, 10, 10, 14, 1, false)))
	local target = place(P, "storage_crate", 10, 15)
	run(P, rt, 120)
	eq(P.workshop.buffers[target.uid].inv.herb_mint, 6)
end)

test("belts", "the line action is checked on the server", function()
	local bot = Bot.new()
	for id in pairs(D.Research) do bot.P.research[id] = true end
	bot.P.wallet = 5000
	bot:enter()
	local r = bot:act("PlaceBelts", { machine = "wooden_belt", floor = 1, cells = BeltPath.cells(5, 10, 8, 10, 1, false) })
	eq(#r.uids, 4)
	eq(bot:try("PlaceBelts", { machine = "wooden_belt", floor = 1, cells = { { gx = 1, gz = 8, rot = 7 } } }).code, "BAD_REQUEST")
	eq(bot:try("PlaceBelts", { machine = "wooden_belt", floor = 1, cells = {} }).code, "BAD_REQUEST")
	eq(bot:try("PlaceBelts", { machine = "wooden_belt", floor = 1, cells = { { gx = 1, gz = 8 } } }).code, "BAD_REQUEST")
	eq(bot:try("PlaceBelts", { machine = "wooden_belt", floor = 1, cells = "x" }).code, "BAD_REQUEST")
	local guest = Bot.new(bot.world, 2002)
	bot:act("InviteCoOp", { user = guest.userId, role = "visitor" })
	guest:goTo("workshop_door")
	guest:act("EnterWorkshop", { owner = bot.userId })
	eq(guest:try("PlaceBelts", { machine = "wooden_belt", floor = 1, cells = BeltPath.cells(5, 12, 6, 12, 1, false) }).code, "FORBIDDEN")
end)

return results
