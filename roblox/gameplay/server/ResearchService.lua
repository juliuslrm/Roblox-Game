-- Sole writer of research unlocks.
local D = require(script.Parent.Data)
local Eco = require(script.Parent.EconomyService)
local Research = D.Research
local R = {}
function R.canUnlock(P, id)
	local node = Research[id]
	if not node then return "NOT_FOUND" end
	if P.research[id] then return "DUPLICATE" end
	for _, p in ipairs(node.prereqs) do
		if not P.research[p] then return "LOCKED" end
	end
	if P.knowledge < node.cost then return "NO_FUNDS" end
	return nil
end
function R.unlock(P, id)
	local code = R.canUnlock(P, id)
	if code then return nil, code end
	Eco.spendKnowledge(P, Research[id].cost)
	P.research[id] = true
	return Research[id]
end
return R
