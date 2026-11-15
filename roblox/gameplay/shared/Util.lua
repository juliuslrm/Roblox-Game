-- Small pure helpers (Lua 5.1 compatible, no Roblox API).
local Util = {}
function Util.isInt(v)
	return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge and math.floor(v) == v
end
function Util.isFinite(v)
	return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end
function Util.deepCopy(v)
	if type(v) ~= "table" then return v end
	local out = {}
	for k, x in pairs(v) do out[k] = Util.deepCopy(x) end
	return out
end
function Util.count(t)
	local n = 0
	for _ in pairs(t) do n = n + 1 end
	return n
end
function Util.sortedKeys(t)
	local keys = {}
	for k in pairs(t) do keys[#keys + 1] = k end
	table.sort(keys, function(a, b) return tostring(a) < tostring(b) end)
	return keys
end
function Util.clamp(v, lo, hi)
	if v < lo then return lo elseif v > hi then return hi end
	return v
end
-- Deterministic generator (Park-Miller). state is an integer in [1, 2147483646].
function Util.nextRandom(state)
	local s = (state * 48271) % 2147483647
	return s, (s - 1) / 2147483646
end
return Util
