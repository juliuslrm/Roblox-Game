-- Payload validation, rate limiting and replay protection for client requests.
local D = require(script.Parent.Data)
local Config, Protocol, Util = D.Config, D.Protocol, D.Util
local Sec = {}
local INT_LIMIT = 1000000

local function validId(v)
	return type(v) == "string" and #v >= 1 and #v <= 48 and string.find(v, "^[%w_#]+$") ~= nil
end

local function check(kind, v)
	if kind == "int" then return Util.isInt(v) and v >= -INT_LIMIT and v <= INT_LIMIT
	-- Roblox user ids are far above INT_LIMIT (currently in the billions); allow every positive
	-- integer a double represents exactly
	elseif kind == "user" then return Util.isInt(v) and v >= 1 and v <= 9007199254740991
	elseif kind == "num" then return Util.isFinite(v)
	elseif kind == "bool" then return type(v) == "boolean"
	elseif kind == "str" then return type(v) == "string" and #v <= 64
	elseif kind == "id" then return validId(v)
	elseif kind == "ids" then
		if type(v) ~= "table" then return false end
		local n = 0
		for k, x in pairs(v) do
			n = n + 1
			if not Util.isInt(k) or k < 1 or n > 128 or not validId(x) then return false end
		end
		return #v == n
	elseif kind == "cells" then
		if type(v) ~= "table" then return false end
		local n = 0
		for k, c in pairs(v) do
			n = n + 1
			if not Util.isInt(k) or k < 1 or n > 64 or type(c) ~= "table" then return false end
			if not (Util.isInt(c.gx) and Util.isInt(c.gz) and Util.isInt(c.rot)) then return false end
			if math.abs(c.gx) > 1000 or math.abs(c.gz) > 1000 or c.rot < 0 or c.rot > 3 then return false end
		end
		return n >= 1 and #v == n
	end
	return false
end

-- Returns a clean copy that only contains declared fields, or nil.
function Sec.validate(action, payload)
	local spec = Protocol.actions[action]
	if not spec or type(payload) ~= "table" then return nil end
	local clean = {}
	for field, kind in pairs(spec) do
		local optional = string.sub(field, -1) == "?"
		local name = optional and string.sub(field, 1, -2) or field
		local v = payload[name]
		if v == nil then
			if not optional then return nil end
		elseif not check(kind, v) then
			return nil
		else
			if kind == "cells" then
				local copy = {}
				for i, c in ipairs(v) do copy[i] = { gx = c.gx, gz = c.gz, rot = c.rot } end
				clean[name] = copy
			else
				clean[name] = (kind == "ids") and Util.deepCopy(v) or v
			end
		end
	end
	if payload.actionId ~= nil then
		if not validId(payload.actionId) then return nil end
		clean.actionId = payload.actionId
	end
	return clean
end

function Sec.allow(session, action, now)
	local rule = Config.rate[action] or Config.rate.default
	local buckets = session.rt.buckets
	local b = buckets[action]
	if not b then
		b = { tokens = rule.burst, at = now }
		buckets[action] = b
	end
	b.tokens = math.min(rule.burst, b.tokens + math.max(0, now - b.at) * rule.perSec)
	b.at = now
	if b.tokens < 1 then return false end
	b.tokens = b.tokens - 1
	return true
end

function Sec.replayed(session, actionId)
	return actionId and session.rt.recent[actionId] or nil
end
function Sec.remember(session, actionId, result)
	if not actionId then return end
	local rt = session.rt
	rt.recent[actionId] = result
	rt.recentOrder[#rt.recentOrder + 1] = actionId
	if #rt.recentOrder > 64 then
		rt.recent[table.remove(rt.recentOrder, 1)] = nil
	end
end
return Sec
