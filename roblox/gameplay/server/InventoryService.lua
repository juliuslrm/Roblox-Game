-- Sole writer of item stores. A store is a plain map itemId -> integer amount (pieces or ml).
-- Player inventory: limited slots for solids, capacity per liquid. Containers: slot limited.
local D = require(script.Parent.Data)
local Items, Config, Util = D.Items, D.Config, D.Util
local Inv = {}

local function slotsUsed(store)
	local n = 0
	for id, amount in pairs(store) do
		local it = Items[id]
		if it and it.unit ~= "ml" and amount > 0 then n = n + math.ceil(amount / it.stackLimit) end
	end
	return n
end
Inv.slotsUsed = slotsUsed

function Inv.count(store, id) return store[id] or 0 end

function Inv.has(store, items)
	for id, n in pairs(items) do
		if (store[id] or 0) < n then return false, id end
	end
	return true
end

-- How many units of `id` still fit. opts = { slots, liquidCap, only = function(id) }
function Inv.room(store, id, opts)
	local it = Items[id]
	if not it then return 0 end
	if opts.only and not opts.only(id) then return 0 end
	if it.unit == "ml" then
		if not opts.liquidCap then return 0 end
		return math.max(0, opts.liquidCap - (store[id] or 0))
	end
	local have = store[id] or 0
	local freeSlots = opts.slots - slotsUsed(store)
	local inStack = (math.ceil(have / it.stackLimit) * it.stackLimit) - have
	return math.max(0, inStack + freeSlots * it.stackLimit)
end

function Inv.canAdd(store, items, opts)
	local trial = {}
	for k, v in pairs(store) do trial[k] = v end
	for id, n in pairs(items) do
		if not Items[id] or not Util.isInt(n) or n < 0 then return false, id end
		if Inv.room(trial, id, opts) < n then return false, id end
		trial[id] = (trial[id] or 0) + n
	end
	return true
end

function Inv.add(store, items)
	for id, n in pairs(items) do
		if n > 0 then store[id] = (store[id] or 0) + n end
	end
end

-- Atomic: removes everything or nothing.
function Inv.remove(store, items)
	local ok, missing = Inv.has(store, items)
	if not ok then return false, missing end
	for id, n in pairs(items) do
		local left = store[id] - n
		if left <= 0 then store[id] = nil else store[id] = left end
	end
	return true
end

Inv.PLAYER = { slots = Config.inventory.slots, liquidCap = Config.inventory.liquidCap }
function Inv.playerOpts() return Inv.PLAYER end
function Inv.total(store)
	local n = 0
	for _, v in pairs(store) do n = n + v end
	return n
end
return Inv
