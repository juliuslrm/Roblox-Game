-- Customers buy real stock from the shop shelves of a workshop. Sole writer of shelf sales.
local D = require(script.Parent.Data)
local Eco = require(script.Parent.EconomyService)
local Config, Machines, Items, Util = D.Config, D.Machines, D.Items, D.Util
local Shop = {}

local function rand(P)
	local s, r = Util.nextRandom(P.shop.rng)
	P.shop.rng = s
	return r
end

function Shop.shelves(P)
	local list = {}
	for _, e in ipairs(P.workshop.layout) do
		if Machines[e.machine].kind == "shelf" then list[#list + 1] = e.uid end
	end
	return list
end

function Shop.stock(P)
	local stock = {}
	for _, uid in ipairs(Shop.shelves(P)) do
		for item, n in pairs(P.workshop.buffers[uid].inv) do stock[item] = (stock[item] or 0) + n end
	end
	return stock
end

function Shop.rerollDemand(P)
	local lo, hi = Config.shop.demandMin * 100, Config.shop.demandMax * 100
	for _, id in ipairs(Util.sortedKeys(Items)) do
		if Items[id].type == "product" then P.shop.demand[id] = math.floor(lo + rand(P) * (hi - lo) + 0.5) end
	end
end

-- One purchase: stock, wallet, statistics and the sale event change together or not at all.
function Shop.sell(P, item, qty, emit)
	local left = qty
	local shelves = Shop.shelves(P)
	local have = 0
	for _, uid in ipairs(shelves) do have = have + (P.workshop.buffers[uid].inv[item] or 0) end
	if have < qty or qty < 1 or Items[item].type ~= "product" then return nil end
	for _, uid in ipairs(shelves) do
		local inv = P.workshop.buffers[uid].inv
		local take = math.min(left, inv[item] or 0)
		if take > 0 then
			inv[item] = inv[item] - take
			if inv[item] == 0 then inv[item] = nil end
			left = left - take
		end
	end
	local price = Eco.priceFor(P, item, Items[item].sellBase)
	local coins = price * qty
	Eco.earn(P, coins)
	P.stats.sold = P.stats.sold + qty
	P.shop.serial = (P.shop.serial or 0) + 1
	local sale = { type = "sell", item = item, n = qty, coins = coins, price = price, id = P.shop.serial }
	emit(sale)
	return sale
end

function Shop.step(P, dt, emit)
	local shop = P.shop
	if next(shop.demand) == nil then Shop.rerollDemand(P) end
	shop.demandIn = (shop.demandIn or 0) - dt
	if shop.demandIn <= 0 then
		Shop.rerollDemand(P)
		shop.demandIn = Config.shop.demandDriftSec
	end
	shop.nextIn = shop.nextIn - dt
	if shop.nextIn > 0 then return end
	local shelves = #Shop.shelves(P)
	local speed = 1 + 0.15 * math.max(0, shelves - 1) + 0.05 * Eco.repLevel(P)
	shop.nextIn = (Config.shop.customerMinSec + rand(P) * (Config.shop.customerMaxSec - Config.shop.customerMinSec)) / speed
	local stock = Shop.stock(P)
	local ids, total = Util.sortedKeys(stock), 0
	for _, id in ipairs(ids) do total = total + (shop.demand[id] or 100) end
	if total == 0 then
		emit({ type = "customer_left" })
		return
	end
	local pick, acc, chosen = rand(P) * total, 0, ids[#ids]
	for _, id in ipairs(ids) do
		acc = acc + (shop.demand[id] or 100)
		if pick <= acc then chosen = id break end
	end
	local qty = math.min(stock[chosen], (rand(P) < 0.35) and 2 or 1)
	Shop.sell(P, chosen, qty, emit)
end
return Shop
