-- Unit and scenario tests of the pure domain core. Returns { passed = n, failed = {..} }.
local D = loadModule("server/Data")
local Game = loadModule("server/Game")
local Actions = loadModule("server/Actions")
local Place = loadModule("server/PlacementService")
local Logistics = loadModule("server/LogisticsService")
local Inv = loadModule("server/InventoryService")
local Profile = loadModule("server/ProfileService")
local Shop = loadModule("server/ShopService")
local Sim = loadModule("server/WorkshopSimulation")
local Quest = loadModule("server/QuestService")
local Co = loadModule("server/CoOpPermissions")
local Bot = loadModule("tests/bot")
local Config, Machines, Recipes, Items, Util = D.Config, D.Machines, D.Recipes, D.Items, D.Util

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
local function truthy(v, msg) if not v then error(msg or "expected truthy", 2) end end

-- total amount of every item anywhere in a profile (inventory + all buffers + running jobs)
local function census(P)
	local all = {}
	for id, n in pairs(P.items) do all[id] = (all[id] or 0) + n end
	for _, e in ipairs(P.workshop.layout) do
		for id, n in pairs(Place.contents(P, e.uid)) do all[id] = (all[id] or 0) + n end
	end
	return all
end
local function give(bot, items) for id, n in pairs(items) do bot.P.items[id] = (bot.P.items[id] or 0) + n end end
local function unlockAll(bot) for id in pairs(D.Research) do bot.P.research[id] = true end end
local function rich(bot) bot.P.wallet = 100000 end

-- ============ inventory ============
test("inventory", "atomic remove never goes negative", function()
	local store = { herb_mint = 3, water = 500 }
	eq(Inv.remove(store, { herb_mint = 2, water = 1000 }), false)
	eq(store.herb_mint, 3) eq(store.water, 500)
	eq(Inv.remove(store, { herb_mint = 3 }), true)
	eq(store.herb_mint, nil)
end)
test("inventory", "slot and liquid capacity", function()
	local store = {}
	eq(Inv.room(store, "herb_mint", Inv.PLAYER), Config.inventory.slots * 50)
	eq(Inv.room(store, "water", Inv.PLAYER), Config.inventory.liquidCap)
	store.water = Config.inventory.liquidCap
	eq(Inv.canAdd(store, { water = 1 }, Inv.PLAYER), false)
	eq(Inv.canAdd(store, { bogus = 1 }, Inv.PLAYER), false)
	eq(Inv.canAdd(store, { herb_mint = -1 }, Inv.PLAYER), false)
end)
test("inventory", "transfers conserve the item census", function()
	local bot = Bot.new() bot:enter()
	give(bot, { herb_mint = 40, tonic_minor = 5 })
	local before = census(bot.P)
	local crate = bot:entitiesOf("storage_crate")[1].uid
	local shelf = bot:entitiesOf("shop_shelf")[1].uid
	bot:act("TransferStack", { from = "inv", to = crate, item = "herb_mint", amount = 17 })
	bot:act("TransferStack", { from = crate, to = "inv", item = "herb_mint", amount = 5 })
	bot:act("StockShelf", { uid = shelf, item = "tonic_minor", amount = 3 })
	eq(bot:try("StockShelf", { uid = shelf, item = "herb_mint", amount = 1 }).code, "BAD_REQUEST")
	eq(bot:try("TransferStack", { from = "inv", to = crate, item = "herb_mint", amount = -4 }).code, "BAD_REQUEST")
	local after = census(bot.P)
	for id, n in pairs(before) do eq(after[id], n, "census " .. id) end
	eq(bot.P.workshop.buffers[crate].inv.herb_mint, 12)
end)

-- ============ production ============
test("production", "job reserves inputs at start and writes outputs at the end", function()
	local bot = Bot.new() bot:enter()
	local kettle = bot:entitiesOf("kettle")[1].uid
	bot:act("StartManualCraft", { uid = kettle, recipe = "r01" })
	eq(bot:count("herb_mint"), 2) eq(bot:count("water"), 2000)
	bot:tick(1)
	local b = bot.P.workshop.buffers[kettle]
	truthy(b.job, "job running") eq(b.state, "Running") eq(b.inv.herb_mint, nil)
	eq(b.out.tonic_minor, nil)
	bot:tick(8)
	eq(b.out.tonic_minor, 1) eq(b.job, nil)
	eq(bot.P.discoveries.r01, true) eq(bot.P.knowledge >= 5, true)
end)
test("production", "waiting, blocked output, pause and resume", function()
	local bot = Bot.new() bot:enter() unlockAll(bot)
	local kettle = bot:entitiesOf("kettle")[1].uid
	bot:act("SetRecipe", { uid = kettle, recipe = "r01" })
	bot:tick(1)
	local b = bot.P.workshop.buffers[kettle]
	eq(b.state, "WaitingForInputs") truthy(b.waiting == "herb_mint" or b.waiting == "water")
	give(bot, { herb_mint = 60, water = 17000 })
	for _ = 1, 9 do
		bot:put(kettle, "herb_mint", 2) bot:put(kettle, "water", 1000)
		bot:tick(8.5)
	end
	eq(b.out.tonic_minor, Config.machine.outputCap) eq(b.state, "OutputBlocked")
	truthy(b.job and b.job.remaining == 0, "finished job waits for room")
	bot:act("TransferStack", { from = kettle, to = "inv", item = "tonic_minor", amount = 3 })
	bot:tick(1)
	eq(b.out.tonic_minor, Config.machine.outputCap - 2)
	bot:put(kettle, "herb_mint", 2) bot:put(kettle, "water", 1000)
	bot:tick(2)
	bot:act("ToggleMachine", { uid = kettle })
	local remaining = b.job.remaining
	bot:tick(5)
	eq(b.state, "Paused") eq(b.job.remaining, remaining)
	bot:act("ToggleMachine", { uid = kettle })
	bot:tick(1)
	eq(b.state, "Running")
end)
test("production", "recipe change only when idle; foreign inputs are returned", function()
	local bot = Bot.new() bot:enter()
	local kettle = bot:entitiesOf("kettle")[1].uid
	bot:act("StartManualCraft", { uid = kettle, recipe = "r01" })
	bot:tick(1)
	eq(bot:try("SetRecipe", { uid = kettle, recipe = "r02" }).code, "BUSY")
	eq(bot:try("StartManualCraft", { uid = kettle, recipe = "r02" }).code, "BUSY")
	bot:tick(8)
	bot:put(kettle, "herb_mint", 2)
	local before = bot:count("herb_mint")
	bot:act("SetRecipe", { uid = kettle, recipe = "r02" })
	eq(bot:count("herb_mint"), before + 2)
	eq(bot:try("SetRecipe", { uid = kettle, recipe = "r06" }).code, "NOT_FOUND")
end)
test("production", "furnace needs fuel", function()
	local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
	local furnace = bot:build("furnace")
	give(bot, { sand = 4 })
	bot:act("SetRecipe", { uid = furnace, recipe = "r08" })
	bot:put(furnace, "sand", 4)
	bot:tick(2)
	eq(bot.P.workshop.buffers[furnace].state, "NoFuel")
	give(bot, { fuel_charcoal = 2 })
	bot:put(furnace, "fuel_charcoal", 2)
	bot:tick(25)
	eq(bot.P.workshop.buffers[furnace].out.glass, 4)
	eq(bot.P.workshop.buffers[furnace].fuel, 0)
end)
test("production", "removing a machine returns its buffers or is refused", function()
	local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
	local grinder = bot:build("grinder")
	give(bot, { herb_mint = 6 })
	bot:act("SetRecipe", { uid = grinder, recipe = "r06" })
	bot:put(grinder, "herb_mint", 6)
	bot:tick(2)
	local before = census(bot.P)
	local wallet = bot.P.wallet
	local res = bot:act("RemoveMachine", { uid = grinder })
	eq(res.refund, math.floor(45 * Config.refundFactor))
	eq(bot.P.wallet, wallet + res.refund)
	local after = census(bot.P)
	for id, n in pairs(before) do eq(after[id], n, "census " .. id) end
	-- refuse when the inventory cannot take the contents
	local crate = bot:entitiesOf("storage_crate")[1].uid
	bot.P.workshop.buffers[crate].inv.stone = 50
	for i, id in ipairs(Util.sortedKeys(Items)) do
		if Items[id].unit ~= "ml" and i <= 40 then bot.P.items[id] = 50 end
	end
	eq(bot:try("RemoveMachine", { uid = crate }).code, "NO_SPACE")
	truthy(Place.find(bot.P, crate))
end)
test("production", "same inputs give the same result (determinism)", function()
	local function run()
		local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
		give(bot, { herb_mint = 40, water = 15000 })
		local kettle = bot:entitiesOf("kettle")[1].uid
		local shelf = bot:entitiesOf("shop_shelf")[1].uid
		for _ = 1, 6 do
			bot:act("StartManualCraft", { uid = kettle, recipe = "r01" })
			bot:tick(9) bot:collect(kettle)
		end
		bot:act("StockShelf", { uid = shelf, item = "tonic_minor", amount = 6 })
		bot:tick(240)
		return bot.P.wallet .. "/" .. bot.P.stats.sold .. "/" .. bot.P.shop.rng
	end
	eq(run(), run())
end)

test("production", "statistics queue survives pruning (rate over a sliding window)", function()
	local Metrics = loadModule("server/MetricsService")
	local st = Metrics.new()
	for i = 1, 6000 do
		Metrics.record(st, i, { type = "craft", item = "tonic_minor", n = 1, auto = (i % 2 == 0) })
		Metrics.prune(st, i)
	end
	truthy(Metrics.rate(st, 6000, 60) >= 60 and Metrics.rate(st, 6000, 60) <= 61)
	eq(Metrics.autoProductLines(st, 6000, 60), 1)
	truthy(st.tail - st.head <= Config.sim.statsWindowSec + 1)
end)

-- ============ placement ============
test("placement", "bounds, overlap, reserved cells, rotation, locks, funds", function()
	local bot = Bot.new() bot:enter()
	local n = Place.cells(bot.P)
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = 0, gz = 0, floor = 1, rot = 0 }).code, "LOCKED")
	bot.P.research.herbalism = true
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = n - 1, gz = 0, floor = 1, rot = 0 }).code, "BLOCKED")
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = -1, gz = 0, floor = 1, rot = 0 }).code, "BLOCKED")
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = n / 2, gz = 0, floor = 1, rot = 0 }).code, "BLOCKED")   -- door
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = 0, gz = n - 2, floor = 1, rot = 0 }).code, "BLOCKED")   -- stairs
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = 0, gz = 0, floor = 2, rot = 0 }).code, "BLOCKED")
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = 0, gz = 0, floor = 1, rot = 7 }).code, "BLOCKED")
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = 0.5, gz = 0, floor = 1, rot = 0 }).code, "BAD_REQUEST")
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = 0 / 0, gz = 0, floor = 1, rot = 0 }).code, "BAD_REQUEST")
	local uid = bot:act("PlaceMachine", { machine = "grinder", gx = 0, gz = 0, floor = 1, rot = 0 }).uid
	eq(bot.P.wallet, 60 - 45)
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = 1, gz = 1, floor = 1, rot = 0 }).code, "BLOCKED")
	eq(bot:try("PlaceMachine", { machine = "grinder", gx = 4, gz = 0, floor = 1, rot = 0 }).code, "NO_FUNDS")
	eq(bot:try("PlaceMachine", { machine = "kettle", gx = 4, gz = 0, floor = 1, rot = 0 }).code, "LIMIT")
	bot.P.research.craftsman = true bot.P.wallet = 1000
	local saw = bot:act("PlaceMachine", { machine = "saw", gx = 2, gz = 0, floor = 1, rot = 0 }).uid
	eq(bot:try("RotateMachine", { uid = saw }).code, "OK")           -- 3x2 -> 2x3 still fits
	bot:act("PlaceMachine", { machine = "grinder", gx = 4, gz = 0, floor = 1, rot = 0 })
	eq(bot:try("RotateMachine", { uid = saw }).code, "BLOCKED")      -- back to 3x2 would overlap
	eq(bot:act("RotateMachine", { uid = uid }).rot, 1)
end)
test("placement", "plot expansion keeps the layout legal", function()
	local bot = Bot.new() bot:enter()
	eq(bot:try("BuyUpgrade", { kind = "plot" }).code, "LOCKED")
	bot.P.research.storage = true
	eq(bot:try("BuyUpgrade", { kind = "plot" }).code, "NO_FUNDS")
	bot.P.wallet = 500
	bot:act("BuyUpgrade", { kind = "plot" })
	eq(Place.cells(bot.P), 24) eq(bot.P.wallet, 100)
	for _, e in ipairs(bot.P.workshop.layout) do
		eq(Place.check(bot.P, e.machine, e.gx, e.gz, e.floor, e.rot, e.uid), nil, "entity " .. e.uid)
	end
	eq(bot:try("BuyUpgrade", { kind = "floor" }).code, "LOCKED")
end)
test("placement", "blueprint placement is all-or-nothing", function()
	local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
	local a = bot:act("PlaceMachine", { machine = "grinder", gx = 0, gz = 0, floor = 1, rot = 0 }).uid
	local b = bot:act("PlaceMachine", { machine = "wooden_belt", gx = 0, gz = 2, floor = 1, rot = 0 }).uid
	local c = bot:act("PlaceMachine", { machine = "storage_crate", gx = 0, gz = 3, floor = 1, rot = 0 }).uid
	bot:act("SetRecipe", { uid = a, recipe = "r06" })
	give(bot, { herb_mint = 4 }) bot:put(a, "herb_mint", 4)
	eq(bot:act("SaveBlueprint", { slot = 1, name = "Mahl-Linie", uids = { a, b, c } }).estimateCost, 45 + 4 + 25)
	eq(bot:try("SaveBlueprint", { slot = 99, name = "x", uids = { a } }).code, "LIMIT")
	local count, wallet = #bot.P.workshop.layout, bot.P.wallet
	-- overlaps the original at the second part -> nothing may remain
	eq(bot:try("PlaceBlueprint", { slot = 1, gx = 3, gz = 0, floor = 1 }).ok, true)
	eq(#bot.P.workshop.layout, count + 3) eq(bot.P.wallet, wallet - 74)
	local copy = bot.P.workshop.layout[count + 1]
	eq(copy.recipe, "r06") eq(next(bot.P.workshop.buffers[copy.uid].inv), nil, "no free items in blueprint")
	count, wallet = #bot.P.workshop.layout, bot.P.wallet
	eq(bot:try("PlaceBlueprint", { slot = 1, gx = 4, gz = 1, floor = 1 }).code, "BLOCKED")
	eq(#bot.P.workshop.layout, count) eq(bot.P.wallet, wallet)
	bot.P.wallet = 50
	bot.now = bot.now + 30
	eq(bot:try("PlaceBlueprint", { slot = 1, gx = 12, gz = 10, floor = 1 }).code, "NO_FUNDS")
	eq(#bot.P.workshop.layout, count) eq(bot.P.wallet, 50)
end)

-- ============ logistics ============
local function line(bot)
	-- crate(0,0) -> hopper(0,2) -> belt(0,3) -> grinder(0,4) -> belt(0,6) -> crate(0,7)
	local ids = {}
	ids.src = bot:act("PlaceMachine", { machine = "storage_crate", gx = 0, gz = 0, floor = 1, rot = 0 }).uid
	ids.hopper = bot:act("PlaceMachine", { machine = "input_hopper", gx = 0, gz = 2, floor = 1, rot = 0 }).uid
	ids.belt1 = bot:act("PlaceMachine", { machine = "wooden_belt", gx = 0, gz = 3, floor = 1, rot = 0 }).uid
	ids.grinder = bot:act("PlaceMachine", { machine = "grinder", gx = 0, gz = 4, floor = 1, rot = 0 }).uid
	ids.belt2 = bot:act("PlaceMachine", { machine = "wooden_belt", gx = 0, gz = 6, floor = 1, rot = 0 }).uid
	ids.dst = bot:act("PlaceMachine", { machine = "storage_crate", gx = 0, gz = 7, floor = 1, rot = 0 }).uid
	bot:act("SetRecipe", { uid = ids.grinder, recipe = "r06" })
	return ids
end
test("logistics", "crate -> hopper -> belt -> machine -> belt -> crate runs without hands", function()
	local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
	local ids = line(bot)
	bot.P.items.herb_mint = 12
	bot:put(ids.src, "herb_mint", 12)
	local before = census(bot.P)
	bot:tick(90)
	eq(bot.P.workshop.buffers[ids.dst].inv.mint_powder, 12)
	eq(bot.P.workshop.buffers[ids.src].inv.herb_mint, nil)
	local after = census(bot.P)
	eq(after.mint_powder, 12) eq(after.herb_mint, nil) eq(before.herb_mint, 12)
end)
test("logistics", "a missing link stops the flow, backpressure blocks without loss", function()
	local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
	local ids = line(bot)
	bot:act("RemoveMachine", { uid = ids.belt2 })
	bot.P.items.herb_mint = 40
	bot:put(ids.src, "herb_mint", 40)
	bot:tick(120)
	local g = bot.P.workshop.buffers[ids.grinder]
	eq(g.state, "OutputBlocked") eq(g.out.mint_powder, Config.machine.outputCap)
	eq(bot.P.workshop.buffers[ids.dst].inv.mint_powder, nil)
	local all = census(bot.P)
	eq((all.herb_mint or 0) + (all.mint_powder or 0), 40, "nothing lost or duplicated")
	-- rotating the feeding belt away breaks the chain as well
	bot:act("RotateMachine", { uid = ids.belt1 })
	local G = Logistics.build(bot.P)
	eq(G.solid[ids.belt1][1], false)
end)
test("logistics", "splitter distributes round-robin, merger loses nothing", function()
	local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
	local function p(m, x, z, r) return bot:act("PlaceMachine", { machine = m, gx = x, gz = z, floor = 1, rot = r or 0 }).uid end
	local src = p("storage_crate", 2, 0)
	p("input_hopper", 2, 2) local sp = p("splitter", 2, 3)
	local c1 = p("storage_crate", 2, 4)       -- front
	local c2 = p("storage_crate", 3, 2)       -- right (+x), touches the splitter at (3,3)
	local c3 = p("storage_crate", 0, 2)       -- left (-x), touches the splitter at (1,3)
	give(bot, { stone = 30 }) bot:put(src, "stone", 30)
	bot:tick(60)
	local a, b, c = bot.P.workshop.buffers[c1].inv.stone, bot.P.workshop.buffers[c2].inv.stone, bot.P.workshop.buffers[c3].inv.stone
	eq(a + b + c, 30) eq(a, 10) eq(b, 10) eq(c, 10)
	truthy(sp)
end)
test("logistics", "belt loops do not duplicate or hang", function()
	local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
	local function p(m, x, z, r) return bot:act("PlaceMachine", { machine = m, gx = x, gz = z, floor = 1, rot = r }).uid end
	local b1 = p("wooden_belt", 0, 0, 0) p("wooden_belt", 0, 1, 1) p("wooden_belt", 1, 1, 2) p("wooden_belt", 1, 0, 3)
	bot.P.workshop.buffers[b1].item = "stone"
	bot:tick(40)
	local n = 0
	for _, e in ipairs(bot.P.workshop.layout) do
		if bot.P.workshop.buffers[e.uid].item == "stone" then n = n + 1 end
	end
	eq(n, 1)
end)
test("logistics", "liquids stay exact in ml and never mix types", function()
	local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
	local function p(m, x, z, r) return bot:act("PlaceMachine", { machine = m, gx = x, gz = z, floor = 1, rot = r or 0 }).uid end
	-- pump(0,0) -> pipes -> tank(4,0) and extractor fluid input
	local pump = p("well_pump", 0, 0)            -- fluid out at (1,0) facing +x
	p("pipe_straight", 2, 0) p("pipe_straight", 3, 0)
	local tank = p("fluid_tank", 4, 0)
	p("pipe_straight", 3, 1) p("pipe_straight", 3, 2) p("pipe_straight", 3, 3)
	local ex = p("extractor", 4, 3)              -- fluid in at local (0,0) facing -x -> neighbour (3,3)
	bot:act("SetRecipe", { uid = ex, recipe = "r10" })
	give(bot, { mint_powder = 3 }) bot:put(ex, "mint_powder", 3)
	bot:tick(80)
	local eb, tb = bot.P.workshop.buffers[ex], bot.P.workshop.buffers[tank]
	eq(eb.outFluid.herbal_extract, 3000)
	eq(next(tb.fluids), "water")
	truthy(tb.fluids.water % 1 == 0 and eb.fluids.water % 1 == 0, "integer ml")
	-- a solid cannot enter a pipe, a liquid cannot enter a belt
	eq(bot:try("TransferStack", { from = "inv", to = tank, item = "stone", amount = 1 }).code, "NO_ITEMS")
	give(bot, { herb_mint = 2, herbal_extract = 1000 })
	eq(bot:try("TransferStack", { from = "inv", to = tank, item = "herb_mint", amount = 1 }).code, "NO_SPACE")
	eq(bot:try("TransferStack", { from = "inv", to = tank, item = "herbal_extract", amount = 1000 }).code, "NO_SPACE")
	truthy(pump)
end)
test("logistics", "lift moves items one floor up, sorter routes by whitelist", function()
	local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
	bot.P.workshop.floors = 2
	local function p(m, x, z, f, r) return bot:act("PlaceMachine", { machine = m, gx = x, gz = z, floor = f, rot = r or 0 }).uid end
	local src = p("storage_crate", 6, 4, 1)
	p("input_hopper", 6, 6, 1)
	local sorter = p("filter_sorter", 6, 7, 1)
	p("vertical_lift", 6, 8, 1)                  -- front (+z) on floor 2
	local up = p("storage_crate", 6, 9, 2)
	local side = p("storage_crate", 4, 7, 1)     -- left of the sorter (-x)
	bot:act("SetFilter", { uid = sorter, items = { "stone" } })
	give(bot, { stone = 5, sand = 5 })
	bot:put(src, "sand", 5) bot:put(src, "stone", 5)
	bot:tick(80)
	eq(bot.P.workshop.buffers[up].inv.stone, 5)
	eq(bot.P.workshop.buffers[side].inv.sand, 5)
	eq(bot.P.workshop.buffers[up].inv.sand, nil)
end)

-- ============ shop ============
test("shop", "customers only buy real stock; money matches the ledger", function()
	local bot = Bot.new() bot:enter()
	local shelf = bot:entitiesOf("shop_shelf")[1].uid
	local wallet = bot.P.wallet
	bot:tick(120)
	eq(bot.P.wallet, wallet) eq(bot.P.stats.sold, 0)
	give(bot, { tonic_minor = 3 })
	bot:act("StockShelf", { uid = shelf, item = "tonic_minor", amount = 3 })
	local earned = 0
	for _ = 1, 600 do
		bot.now = bot.now + 0.25
		for _, ev in ipairs(Game.tick(bot.world, 0.25, bot.now)[bot.userId]) do
			if ev.type == "sell" then
				earned = earned + ev.coins
				truthy(ev.price >= math.floor(18 * 0.85) and ev.price <= math.floor(18 * 1.15 * 1.2), "price in range")
			end
		end
	end
	eq(bot.P.stats.sold, 3) eq(bot.P.wallet, wallet + earned)
	eq(bot.P.workshop.buffers[shelf].inv.tonic_minor, nil)
end)
test("shop", "two buyers never get the same last piece; order and sale cannot share stock", function()
	local bot = Bot.new() bot:enter()
	local shelf = bot:entitiesOf("shop_shelf")[1].uid
	bot.P.workshop.buffers[shelf].inv.tonic_minor = 1
	local sales = {}
	local function emit(ev) sales[#sales + 1] = ev end
	truthy(Shop.sell(bot.P, "tonic_minor", 1, emit))
	eq(Shop.sell(bot.P, "tonic_minor", 1, emit), nil)
	eq(#sales, 1) eq(Shop.sell(bot.P, "tonic_minor", 0, emit), nil)
	-- the same three potions cannot be delivered and sold
	bot.P.quest.main = 4
	give(bot, { tonic_minor = 3 })
	bot:act("StockShelf", { uid = shelf, item = "tonic_minor", amount = 3 })
	bot:goTo("market_hall")
	eq(bot:try("ClaimOrder", { kind = "main", id = "q04" }).code, "NO_ITEMS")
	eq(bot.P.quest.main, 4)
end)

-- ============ quests / orders ============
test("quests", "delivery takes real items once and pays once", function()
	local bot = Bot.new()
	bot.P.quest.main = 4
	give(bot, { tonic_minor = 2, night_ink = 2 })
	eq(bot:try("ClaimOrder", { kind = "main", id = "q04" }).code, "TOO_FAR")
	bot:goTo("market_hall")
	local wallet = bot.P.wallet
	bot:act("ClaimOrder", { kind = "main", id = "q04", actionId = "a1" })
	eq(bot.P.wallet, wallet + 60) eq(bot:count("tonic_minor"), 0) eq(bot:count("night_ink"), 1)
	eq(bot:try("ClaimOrder", { kind = "main", id = "q04", actionId = "a1" }).code, "DUPLICATE")
	eq(bot:try("ClaimOrder", { kind = "main", id = "q04" }).code, "NOT_READY")
	eq(bot.P.wallet, wallet + 60)
end)
test("quests", "order board: three offers, real items, reputation cap per day", function()
	local bot = Bot.new() bot:tick(1)
	eq(#bot.P.quest.orders.list, Config.orders.active)
	bot:goTo("market_hall")
	local o = bot.P.quest.orders.list[1]
	eq(bot:try("ClaimOrder", { kind = "order", id = o.id }).code, "NO_ITEMS")
	local repBefore = bot.P.repPoints
	for _ = 1, 40 do
		local order = bot.P.quest.orders.list[1]
		give(bot, Quest.templateById[order.tpl].items)
		bot:act("ClaimOrder", { kind = "order", id = order.id })
		eq(#bot.P.quest.orders.list, Config.orders.active)
	end
	eq(bot.P.repPoints - repBefore, Config.orders.repPerOrderCapPerDay)
end)
test("quests", "village project counts every donation once and rewards contributors once", function()
	local a = Bot.new()
	local b = Bot.new(a.world, 2002)
	local def
	for _, d in ipairs(D.Quests.projects) do if d.id == a.world.project.id then def = d end end
	give(a, { [def.item] = def.count }) give(b, { [def.item] = 5 })
	a:goTo("plaza") b:goTo("plaza")
	b:act("DonateProject", { amount = 2 })
	eq(a.world.project.progress, 2)
	a:act("DonateProject", { amount = 999 })
	eq(a.world.project.done, true) eq(a:count(def.item), 2) eq(b:count(def.item), 3)
	eq(a.P.repPoints, def.rep) eq(b.P.repPoints, def.rep) eq(a.P.claims[def.id], true)
	eq(b:try("DonateProject", { amount = 1 }).code, "LIMIT")
end)

-- ============ network / security ============
test("network", "malformed payloads are rejected without side effects", function()
	local bot = Bot.new() bot:enter()
	local snapshot = Profile.serialize(bot.P)
	local bad = {
		{ "PlaceMachine", { machine = 5, gx = 0, gz = 0, floor = 1, rot = 0 } },
		{ "PlaceMachine", { machine = "grinder", gx = "0", gz = 0, floor = 1, rot = 0 } },
		{ "PlaceMachine", { machine = "grinder", gx = math.huge, gz = 0, floor = 1, rot = 0 } },
		{ "PlaceMachine", { machine = "grinder", gx = 0, gz = 0, floor = 1 } },
		{ "TransferStack", { from = "inv", to = "m1", item = "herb_mint", amount = 0 / 0 } },
		{ "TransferStack", { from = "inv", to = "m1", item = "herb_mint", amount = 1e12 } },
		{ "TransferStack", { from = "workspace.Baseplate", to = "inv", item = "herb_mint", amount = 1 } },
		{ "SaveBlueprint", { slot = 1, name = "x", uids = { 1, 2 } } },
		{ "SaveBlueprint", { slot = 1, name = "x", uids = { a = "m1" } } },
		{ "GatherNode", {} }, { "Nope", {} }, { "GatherNode", "node" },
		{ "UnlockResearch", { research = string.rep("a", 200) } },
	}
	for _, case in ipairs(bad) do
		eq(bot:try(case[1], case[2]).code, "BAD_REQUEST", case[1])
	end
	local after = Profile.serialize(bot.P)
	eq(after.wallet, snapshot.wallet) eq(#after.workshop.layout, #snapshot.workshop.layout)
	eq(Inv.total(after.items), Inv.total(snapshot.items))
end)
test("network", "rate limit and replay protection", function()
	local bot = Bot.new() bot:enter()
	local codes = {}
	for _ = 1, 40 do
		local r = Actions.handle(bot.world, bot.session, "RequestSnapshot", {}, { now = bot.now })
		codes[r.code] = (codes[r.code] or 0) + 1
	end
	eq(codes.OK, Config.rate.default.burst) eq(codes.RATE_LIMITED, 40 - Config.rate.default.burst)
	bot.now = bot.now + 10
	local kettle = bot:entitiesOf("kettle")[1].uid
	local first = bot:try("StartManualCraft", { uid = kettle, recipe = "r01", actionId = "craft1" })
	eq(first.ok, true)
	local mint = bot:count("herb_mint")
	for _ = 1, 5 do
		eq(bot:try("StartManualCraft", { uid = kettle, recipe = "r01", actionId = "craft1" }).code, "DUPLICATE")
	end
	eq(bot:count("herb_mint"), mint)
end)
test("network", "gathering needs proximity, unlocks and respects node stock", function()
	local bot = Bot.new()
	eq(bot:try("GatherNode", { node = "n_mint_plaza" }).code, "TOO_FAR")
	eq(bot:try("GatherNode", { node = "n_copper_tower" }).code, "LOCKED")
	local a = bot.world.nodeAnchors.n_mint_plaza
	Game.updatePosition(bot.world, bot.session, a.x, a.z)
	local got = 0
	for _ = 1, 10 do
		bot.now = bot.now + 1
		local r = Actions.handle(bot.world, bot.session, "GatherNode", { node = "n_mint_plaza" }, { now = bot.now })
		if r.ok then got = got + r.payload.amount end
	end
	eq(got, D.Locations.nodes.n_mint_plaza.capacity)
	eq(bot:try("GatherNode", { node = "n_mint_plaza" }).code, "NOT_READY")
	bot:tick(25)
	eq(bot:try("GatherNode", { node = "n_mint_plaza" }).ok, true)
end)
test("network", "co-op: rights are checked on the server, the owner's wallet is safe", function()
	local owner = Bot.new()
	local guest = Bot.new(owner.world, 2002)
	owner:enter()
	guest:goTo("workshop_door")
	eq(guest:try("EnterWorkshop", { owner = owner.userId }).code, "FORBIDDEN")
	eq(guest:try("EnterWorkshop", { owner = 424242 }).code, "NOT_FOUND")
	eq(guest:try("InviteCoOp", { user = guest.userId, role = "builder" }).code, "BAD_REQUEST")
	owner:act("InviteCoOp", { user = guest.userId, role = "visitor" })
	guest:act("EnterWorkshop", { owner = owner.userId })
	local kettle = owner:entitiesOf("kettle")[1].uid
	eq(guest:try("StartManualCraft", { uid = kettle, recipe = "r01" }).code, "FORBIDDEN")
	eq(guest:try("RemoveMachine", { uid = kettle }).code, "FORBIDDEN")
	owner:act("SetCoOpPermission", { user = guest.userId, role = "operator" })
	local guestItems = Inv.total(guest.P.items)
	guest:act("StartManualCraft", { uid = kettle, recipe = "r01" })
	eq(owner:count("herb_mint"), 2, "operator uses the owner's stock")
	eq(Inv.total(guest.P.items), guestItems)
	eq(guest:try("RemoveMachine", { uid = kettle }).code, "FORBIDDEN")
	eq(guest:try("SaveBlueprint", { slot = 1, name = "x", uids = { kettle } }).code, "FORBIDDEN")
	eq(guest:try("UnlockResearch", { research = "herbalism" }).code, "TOO_FAR")
	owner:act("SetCoOpPermission", { user = guest.userId, role = "builder" })
	owner.P.research.herbalism = true owner.P.wallet = 100
	guest:act("PlaceMachine", { machine = "grinder", gx = 0, gz = 0, floor = 1, rot = 0 })
	eq(owner.P.wallet, 55) eq(guest.P.wallet, 60)
	owner:act("SetCoOpPermission", { user = guest.userId, role = "none" })
	eq(guest.session.rt.inWorkshop, nil)
	guest:goTo("workshop_door")
	eq(guest:try("EnterWorkshop", { owner = owner.userId }).code, "FORBIDDEN")
	-- host leaves: visitors are sent home, grants vanish
	owner:act("InviteCoOp", { user = guest.userId, role = "builder" })
	guest:act("EnterWorkshop", { owner = owner.userId })
	local evicted = Game.removeSession(owner.world, owner.userId)
	eq(evicted[1], guest.userId) eq(guest.session.rt.inWorkshop, nil)
	eq(Co.role(owner.world, owner.userId, guest.userId), nil)
end)

-- ============ save ============
test("save", "serialize -> load roundtrip keeps a running factory", function()
	local bot = Bot.new() bot:enter() unlockAll(bot) rich(bot)
	local ids = line(bot)
	give(bot, { herb_mint = 20 }) bot:put(ids.src, "herb_mint", 20)
	bot:tick(17.25)
	local data = Profile.serialize(bot.P, 123)
	local before = census(bot.P)
	local P2, report = Profile.load(data, bot.userId)
	truthy(P2) eq(#report.fixed, 0, table.concat(report.fixed, ","))
	local after = census(P2)
	for id, n in pairs(before) do eq(after[id], n, "census " .. id) end
	eq(#P2.workshop.layout, #bot.P.workshop.layout)
	-- the reloaded factory finishes the job without help; no offline progress was invented
	local world2 = Game.newWorld(Bot.anchors())
	local s2 = Game.addSession(world2, bot.userId, P2)
	for _ = 1, 400 do Game.tick(world2, 0.25, 0) end
	eq(P2.workshop.buffers[ids.dst].inv.mint_powder, 20)
	truthy(s2)
end)
test("save", "corrupt data is repaired or refused, never silently lost", function()
	local bot = Bot.new() bot:enter()
	local data = Profile.serialize(bot.P)
	data.wallet = -500
	data.items.bogus_item = 9
	data.items.herb_mint = 0 / 0
	data.workshop.layout[2].machine = "does_not_exist"
	data.workshop.buffers[data.workshop.layout[2].uid].inv = { stone = 7 }
	data.workshop.layout[#data.workshop.layout + 1] = { uid = "m77", machine = "kettle", gx = 9999, gz = 0, floor = 1, rot = 0 }
	data.research.fake_node = true
	local P2, report = Profile.load(data, bot.userId)
	truthy(P2) eq(P2.wallet, 0) eq(P2.items.bogus_item, nil) eq(P2.research.fake_node, nil)
	eq(P2.items.stone, 7, "contents of a dropped entity are returned")
	truthy(#P2.quarantine >= 2) truthy(#report.fixed >= 4)
	eq(Profile.load("garbage", 1), nil)
	eq(Profile.load({ schemaVersion = 999 }, 1), nil)
	eq(Profile.load({}, 1), nil)
end)
test("save", "safe mode blocks every mutation", function()
	local a, n = Bot.anchors()
	local world = Game.newWorld(a, n)
	local s = Game.addSession(world, 5, nil, true)
	eq(Actions.handle(world, s, "EnterWorkshop", {}, { now = 1 }).code, "SAFE_MODE")
	eq(Actions.handle(world, s, "RequestSnapshot", {}, { now = 1 }).ok, true)
	local wallet = s.profile.wallet
	Game.tick(world, 0.25, 2)
	eq(s.profile.wallet, wallet) eq(Game.snapshot(world, s).safeMode, true)
end)
return results
