-- Sole writer of quest state: main quests, NPC chains, repeatable orders.
local D = require(script.Parent.Data)
local Eco = require(script.Parent.EconomyService)
local Inv = require(script.Parent.InventoryService)
local Metrics = require(script.Parent.MetricsService)
local Config, Quests, Recipes, Items, Locations, Util = D.Config, D.Quests, D.Recipes, D.Items, D.Locations, D.Util
local Q = {}

local mainIndex = {}
for i, id in ipairs(Quests.mainOrder) do mainIndex[id] = i end

function Q.current(P) return Quests.main[Quests.mainOrder[P.quest.main]] end
function Q.isDone(P, questId) return (mainIndex[questId] or math.huge) < P.quest.main end

function Q.ruleMet(P, rule)
	if not rule then return true end
	if rule.research and not P.research[rule.research] then return false end
	if rule.quest and not Q.isDone(P, rule.quest) then return false end
	if rule.rep and Eco.repLevel(P) < rule.rep then return false end
	return true
end
function Q.locationUnlocked(P, locationId)
	local loc = Locations.locations[locationId]
	return loc ~= nil and Q.ruleMet(P, loc.unlock)
end

local function pay(P, rw)
	Eco.earn(P, rw.coins or 0)
	Eco.addKnowledge(P, rw.knowledge or 0)
	Eco.addRep(P, rw.rep or 0)
end

local function objectiveDone(P, rt, o)
	if o.visit and not P.quest.visited[o.visit] then return false end
	local t = o.type
	if t == "enter_workshop" then return P.quest.progress >= 1
	elseif t == "craft" or t == "sell" then return P.quest.progress >= (o.count or 1)
	elseif t == "piped" then return P.quest.progress >= o.ml
	elseif t == "research" then return P.research[o.id] == true
	elseif t == "floors" then return P.workshop.floors >= o.count
	elseif t == "lines" then return rt ~= nil and Metrics.autoProductLines(rt.stats, rt.clock, o.windowSec) >= o.count
	elseif t == "rate" then
		return rt ~= nil and rt.clock >= o.windowSec and Metrics.rate(rt.stats, rt.clock, o.windowSec) >= o.perMin
	end
	return false   -- deliver: only through claim
end

-- Feeds simulation / action events into quest progress and first-craft discoveries.
function Q.onEvents(P, events, notify)
	for _, ev in ipairs(events) do
		if ev.type == "craft" and ev.recipe and not P.discoveries[ev.recipe] then
			P.discoveries[ev.recipe] = true
			local k = Recipes[ev.recipe].knowledgeRewardFirstCraft or 0
			Eco.addKnowledge(P, k)
			if notify and k > 0 then notify({ kind = "discovery", recipe = ev.recipe, knowledge = k }) end
		end
		if ev.type == "visit" then P.quest.visited[ev.at] = true end
		local q = Q.current(P)
		if q then
			local o = q.objective
			if o.type == "enter_workshop" and ev.type == "enter_workshop" then
				P.quest.progress = 1
			elseif o.type == "craft" and ev.type == "craft" and (o.item == nil or o.item == ev.item)
				and (not o.auto or ev.auto) then
				P.quest.progress = P.quest.progress + ev.n
			elseif o.type == "sell" and ev.type == "sell" then
				P.quest.progress = P.quest.progress + ev.n
			elseif o.type == "piped" and ev.type == "piped" then
				P.quest.progress = P.quest.progress + ev.ml
			end
		end
	end
end

local function advance(P, q, notify)
	pay(P, q.rewards)
	P.quest.main = P.quest.main + 1
	P.quest.progress = 0
	if notify then notify({ kind = "quest_done", quest = q.id, rewards = q.rewards }) end
end

-- Completes every main quest whose (non-delivery) objective is fulfilled. Each reward is paid once.
function Q.evaluate(P, rt, notify)
	local guard = 0
	while guard < 25 do
		guard = guard + 1
		local q = Q.current(P)
		if not q or q.objective.type == "deliver" or not objectiveDone(P, rt, q.objective) then break end
		advance(P, q, notify)
	end
end

-- Which items would a delivery objective take from the inventory? nil if not possible.
local function deliveryItems(P, o)
	if o.items then
		return Inv.has(P.items, o.items) and o.items or nil
	end
	local take, left = {}, o.count
	for _, id in ipairs(o.anyOf) do
		local n = math.min(left, P.items[id] or 0)
		if n > 0 then take[id] = n left = left - n end
	end
	return (left == 0) and take or nil
end

function Q.claimMain(P, questId, notify)
	local q = Q.current(P)
	if not q or q.id ~= questId or q.objective.type ~= "deliver" then return nil, "NOT_READY" end
	local take = deliveryItems(P, q.objective)
	if not take then return nil, "NO_ITEMS" end
	Inv.remove(P.items, take)
	advance(P, q, notify)
	return q
end

function Q.chainStep(P, chainId)
	local c = Quests.chains[chainId]
	if not c then return nil end
	return c.steps[(P.quest.chains[chainId] or 0) + 1], c
end

function Q.claimChain(P, chainId, notify)
	local step = Q.chainStep(P, chainId)
	if not step then return nil, "NOT_FOUND" end
	if not Inv.remove(P.items, step.objective.items) then return nil, "NO_ITEMS" end
	P.quest.chains[chainId] = (P.quest.chains[chainId] or 0) + 1
	pay(P, step.rewards)
	if notify then notify({ kind = "chain_step", chain = chainId, step = step.id, rewards = step.rewards }) end
	return step
end

-- ---- repeatable orders ----
local templateById = {}
for _, t in ipairs(Quests.orders) do templateById[t.id] = t end

function Q.orderReward(t)
	local coins = 0
	for item, n in pairs(t.items) do
		local base = Items[item].sellBase
		if base > 0 then coins = coins + base * n * t.coinFactor else coins = coins + n * t.coinFactor end
	end
	return math.floor(coins)
end

function Q.refreshOrders(P, now)
	local board = P.quest.orders
	if now >= board.nextRefresh then
		board.list = {}
		board.nextRefresh = now + Config.orders.refreshSec
	end
	local onBoard, eligible = {}, {}
	for _, o in ipairs(board.list) do onBoard[o.tpl] = true end
	for _, t in ipairs(Quests.orders) do
		if not onBoard[t.id] and (not t.need or P.research[t.need]) then eligible[#eligible + 1] = t.id end
	end
	local rng = board.rng or (P.userId % 100000 + 7)
	while #board.list < Config.orders.active and #eligible > 0 do
		local r
		rng, r = Util.nextRandom(rng)
		local pick = table.remove(eligible, math.floor(r * #eligible) + 1)
		board.serial = board.serial + 1
		board.list[#board.list + 1] = { id = "ord" .. board.serial, tpl = pick }
	end
	board.rng = rng
end

function Q.claimOrder(P, orderId, now, notify)
	local board = P.quest.orders
	for i, o in ipairs(board.list) do
		if o.id == orderId then
			local t = templateById[o.tpl]
			if not Inv.remove(P.items, t.items) then return nil, "NO_ITEMS" end
			table.remove(board.list, i)
			local coins = Q.orderReward(t)
			Eco.earn(P, coins)
			local day = math.floor(now / 86400)
			if board.repDay ~= day then board.repDay, board.repToday = day, 0 end
			local rep = math.min(t.rep, Config.orders.repPerOrderCapPerDay - board.repToday)
			if rep > 0 then
				Eco.addRep(P, rep)
				board.repToday = board.repToday + rep
			end
			Q.refreshOrders(P, now)
			if notify then notify({ kind = "order_done", order = t.id, coins = coins, rep = math.max(rep, 0) }) end
			return { coins = coins, rep = math.max(rep, 0), tpl = t.id }
		end
	end
	return nil, "NOT_FOUND"
end
Q.templateById = templateById
return Q
