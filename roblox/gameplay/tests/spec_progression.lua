-- progression: a scripted solo player completes q01 -> q20 using only client actions,
-- starting from a fresh profile, without any injected items, coins or unlocks.
local D = loadModule("server/Data")
local Bot = loadModule("tests/bot")
local Quest = loadModule("server/QuestService")
local Place = loadModule("server/PlacementService")
local Profile = loadModule("server/ProfileService")
local Game = loadModule("server/Game")
local Config, Recipes, Util = D.Config, D.Recipes, D.Util

local results = { passed = 0, failed = {}, names = {}, info = {} }
local bot = Bot.new()
local times = {}
local function expect(questId)
	if bot:quest() ~= questId then
		error("expected quest " .. questId .. ", bot is at " .. bot:quest(), 2)
	end
end
local function waitFor(nextQuest, maxSec)
	local t = 0
	while bot:quest() ~= nextQuest and t < maxSec do
		bot:tick(2)
		t = t + 2
	end
	expect(nextQuest)
end
local function stage(id, fn)
	local okk, err = pcall(function()
		expect(id)
		fn()
		if bot:quest() == id then error("quest " .. id .. " not completed") end
	end)
	if okk then
		results.passed = results.passed + 1
		times[id] = bot.elapsed
		results.names[#results.names + 1] = string.format("%s done after %5.1f min   coins %5d  knowledge %4d  rep %3d",
			id, bot.elapsed / 60, bot.P.wallet, bot.P.knowledge, bot.P.repPoints)
	else
		results.failed[#results.failed + 1] = id .. " -> " .. tostring(err)
	end
	return okk
end

local kettle = bot:entitiesOf("kettle")[1].uid
local shelf = bot:entitiesOf("shop_shelf")[1].uid
local grinderCrate, kettleCrate, mixerCrate

local plan = {
	{ "q01", function() bot:enter() end },
	{ "q02", function() bot:ensure("tonic_minor", 1) end },
	{ "q03", function()
		bot:act("StockShelf", { uid = shelf, item = "tonic_minor", amount = 1 })
		waitFor("q04", 120)
	end },
	{ "q04", function()
		bot:ensure("tonic_minor", 3)
		bot:goTo("market_hall")
		bot:act("ClaimOrder", { kind = "main", id = "q04" })
	end },
	{ "q05", function()
		bot:goTo("windmill")
		bot:research("herbalism")
		bot:ensure("mint_powder", bot:count("mint_powder") + 2)
	end },
	{ "q06", function() bot:ensure("vial", bot:count("vial") + 1) end },
	{ "q07", function() bot:research("belt_basics") end },
	{ "q08", function()
		local grinder = bot:machine("grinder")
		grinderCrate = bot:feedLine(grinder)
		kettleCrate = bot:feedLine(kettle)
		bot:gather("herb_mint", 6)
		bot:enter()
		if Place.find(bot.P, grinder).recipe ~= "r06" then bot:act("SetRecipe", { uid = grinder, recipe = "r06" }) end
		bot:put(grinderCrate, "herb_mint", 6)
		waitFor("q09", 120)
		bot:collect(grinder)
	end },
	{ "q09", function()
		bot:research("water_engineering")
		bot:attachPump(kettle)
		bot:enter()
		bot:act("SetRecipe", { uid = kettle, recipe = "r01" })
		waitFor("q10", 60)
	end },
	{ "q10", function() bot:ensure("potion_vigor", 1) bot.sellItem = "potion_vigor" end },
	{ "q11", function() bot:goTo("smithy") bot:research("smithing") end },
	{ "q12", function() bot:ensure("copper_ingot", bot:count("copper_ingot") + 1) end },
	{ "q13", function() bot:ensure("charm_luck", 1) end },
	{ "q14", function()
		bot:research("multi_floor")
		bot:afford(Config.floors[2].cost)
		bot:goTo("town_hall")
		bot:act("BuyUpgrade", { kind = "floor" })
	end },
	{ "q15", function()
		bot:research("fruit_mixing")
		local mixer = bot:machine("mixer")
		mixerCrate = bot:feedLine(mixer)
		bot:attachPump(mixer)
		bot:ensure("berry_mash", 4)
		bot:gather("herb_mint", 4)
		bot:enter()
		bot:act("SetRecipe", { uid = mixer, recipe = "r25" })
		if Place.find(bot.P, kettle).recipe ~= "r01" then bot:act("SetRecipe", { uid = kettle, recipe = "r01" }) end
		bot:put(mixerCrate, "berry_mash", 4)
		bot:put(kettleCrate, "herb_mint", 4)
		waitFor("q16", 170)
		bot:collect(mixer) bot:collect(kettle)
	end },
	{ "q16", function() bot:ensure("lunar_extract", bot:count("lunar_extract") + 1000) end },
	{ "q17", function() bot:ensure("crystal_core", bot:count("crystal_core") + 1) end },
	{ "q18", function()
		local grinder = bot:machine("grinder")
		-- a steady rate needs somewhere for the output to go: a crate directly at the grinder's exit
		bot:build("storage_crate", function(G) return G.solid[grinder][1] == "trial" end)
		bot:gather("herb_mint", 26)
		bot:enter()
		if Place.find(bot.P, grinder).recipe ~= "r06" then bot:act("SetRecipe", { uid = grinder, recipe = "r06" }) end
		bot:put(grinderCrate, "herb_mint", 26)
		waitFor("q19", 150)
		bot:collect(grinder)
	end },
	{ "q19", function() bot:ensure("void_seed", 1) end },
	{ "q20", function()
		bot:ensure("elixir_master", 1)
		bot:goTo("town_hall")
		bot:act("ClaimOrder", { kind = "main", id = "q20" })
	end },
}
for _, step in ipairs(plan) do
	if not stage(step[1], step[2]) then break end
end

local function check(name, fn)
	local okk, err = pcall(fn)
	if okk then
		results.passed = results.passed + 1
		results.names[#results.names + 1] = name
	else
		results.failed[#results.failed + 1] = name .. " -> " .. tostring(err)
	end
end

if #results.failed == 0 then
	check("all 20 main quests completed, nothing was injected", function()
		assert(bot:quest() == "done")
		assert(bot.P.research.masterwork and bot.P.discoveries.r30)
	end)
	check("first sale within 10 min, first automatic chain within 30 min", function()
		assert(times.q03 <= 600, "first sale after " .. times.q03 .. " s")
		assert(times.q08 <= 1800, "first automation after " .. times.q08 .. " s")
	end)
	check("all 8 NPC chains (24 steps) can be finished after the main story", function()
		bot.sellItem = "potion_vigor"
		for _, id in ipairs(Util.sortedKeys(D.Quests.chains)) do
			local c = D.Quests.chains[id]
			for _ = 1, #c.steps do
				local step = Quest.chainStep(bot.P, id)
				for item, n in pairs(step.objective.items) do bot:ensure(item, n) end
				bot:goTo(c.at)
				bot:act("ClaimOrder", { kind = "chain", id = id })
			end
			assert(Quest.chainStep(bot.P, id) == nil)
		end
	end)
	check("every crafting recipe was produced at least once", function()
		for _, id in ipairs(Util.sortedKeys(Recipes)) do
			local r = Recipes[id]
			if not r.supply and not bot.P.discoveries[id] then
				for item, n in pairs(r.outputs) do bot:ensure(item, bot:count(item) + n) end
			end
			if not r.supply then assert(bot.P.discoveries[id], "recipe " .. id .. " never crafted") end
		end
	end)
	check("the finished save survives a reload and keeps running", function()
		local data = Profile.serialize(bot.P, 1)
		local P2, report = Profile.load(data, bot.userId)
		assert(P2 and #report.fixed == 0, "reload needed repairs: " .. table.concat(report.fixed, ", "))
		local world = Game.newWorld(Bot.anchors())
		Game.addSession(world, bot.userId, P2)
		for _ = 1, 200 do Game.tick(world, 0.25, 5) end
		assert(P2.wallet >= bot.P.wallet)
	end)
	check("no endgame product sells below the value of its sellable inputs", function()
		for id, r in pairs(Recipes) do
			local inValue, outValue = 0, 0
			for item, n in pairs(r.inputs) do inValue = inValue + D.Items[item].sellBase * n end
			for item, n in pairs(r.outputs) do outValue = outValue + D.Items[item].sellBase * n end
			if outValue > 0 then assert(outValue > inValue, "recipe " .. id .. " destroys value") end
		end
	end)
	results.info[#results.info + 1] = string.format("playthrough: %.1f h simulated, %d machines/parts placed, plot %dx%d cells, %d floors",
		bot.elapsed / 3600, #bot.P.workshop.layout, Place.cells(bot.P), Place.cells(bot.P), bot.P.workshop.floors)
	results.info[#results.info + 1] = string.format("final: coins %d, knowledge left %d, reputation %d (level %d), sold %d, crafted %d",
		bot.P.wallet, bot.P.knowledge, bot.P.repPoints, loadModule("server/EconomyService").repLevel(bot.P), bot.P.stats.sold, bot.P.stats.crafted)
end
return results
