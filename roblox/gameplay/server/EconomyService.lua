-- Sole writer of wallet, knowledge and reputation.
local D = require(script.Parent.Data)
local Config, Util = D.Config, D.Util
local Eco = {}
function Eco.canPay(P, coins) return Util.isInt(coins) and coins >= 0 and P.wallet >= coins end
function Eco.pay(P, coins)
	if not Eco.canPay(P, coins) then return false end
	P.wallet = P.wallet - coins
	return true
end
function Eco.earn(P, coins)
	if Util.isInt(coins) and coins > 0 then
		P.wallet = P.wallet + coins
		P.stats.coinsEarned = P.stats.coinsEarned + coins
	end
end
function Eco.addKnowledge(P, n)
	if Util.isInt(n) and n > 0 then P.knowledge = P.knowledge + n end
end
function Eco.spendKnowledge(P, n)
	if not (Util.isInt(n) and n >= 0 and P.knowledge >= n) then return false end
	P.knowledge = P.knowledge - n
	return true
end
function Eco.addRep(P, n)
	if Util.isInt(n) and n > 0 then P.repPoints = P.repPoints + n end
end
function Eco.repLevel(P)
	local level = 0
	for i, need in ipairs(Config.reputation) do
		if P.repPoints >= need then level = i - 1 end
	end
	return level
end
function Eco.priceFor(P, itemId, baseSell)
	local demand = (P.shop.demand[itemId] or 100) / 100
	local rep = 1 + Config.shop.repPriceStep * Eco.repLevel(P)
	return math.floor(baseSell * demand * rep)
end
return Eco
