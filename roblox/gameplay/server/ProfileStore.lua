-- Persistence adapter. `store` must offer GetAsync(key) and UpdateAsync(key, fn) like a Roblox
-- GlobalDataStore; tests inject a mock.  Rules (spec §13):
--   * a failed load never yields a fresh default profile that could overwrite the real one
--   * saves go through UpdateAsync, refuse to overwrite a newer revision and keep a session lock
--   * every call is wrapped in pcall with bounded retries
local D = require(script.Parent.Data)
local Profile = require(script.Parent.ProfileService)
local Store = {}
Store.__index = Store
Store.LOCK_STALE_SEC = 600
Store.RETRIES = 3

-- opts: { store, serverId, now = function() -> unix seconds, wait = function(seconds) }
function Store.new(opts)
	return setmetatable({ store = opts.store, serverId = opts.serverId, now = opts.now, wait = opts.wait or function() end,
		revisions = {} }, Store)
end

local function key(userId) return "player:" .. tostring(userId) end

function Store:_retry(fn)
	local lastErr
	for attempt = 1, Store.RETRIES do
		local ok, a, b = pcall(fn)
		if ok then return true, a, b end
		lastErr = a
		if attempt < Store.RETRIES then self.wait(0.5 * attempt + (attempt * 7 % 3) * 0.1) end
	end
	return false, lastErr
end

-- Returns profile, status. status: "new" | "ok" | "repaired" | "locked" | "failed" | "corrupt".
-- Only "new", "ok" and "repaired" return a profile that may be played and saved.
function Store:load(userId)
	local now = self.now()
	local status, data
	local ok, err = self:_retry(function()
		self.store:UpdateAsync(key(userId), function(old)
			if old == nil then
				status = "new"
				return nil
			end
			local lock = old.lock
			if type(lock) == "table" and lock.serverId ~= self.serverId and now - (lock.at or 0) < Store.LOCK_STALE_SEC then
				status = "locked"
				return nil
			end
			status, data = "ok", old
			old.lock = { serverId = self.serverId, at = now }
			return old
		end)
	end)
	if not ok then return nil, "failed", err end
	if status == "locked" then return nil, "locked" end
	if status == "new" then
		self.revisions[userId] = 0
		return Profile.new(userId), "new"
	end
	local P, report = Profile.load(data.profile, userId)
	if not P then return nil, "corrupt", report.fatal end
	self.revisions[userId] = data.revision or 0
	return P, (#report.fixed > 0) and "repaired" or "ok", report
end

-- Returns true or false, reason. release = drop the session lock (player leaves).
function Store:save(userId, P, release)
	local known = self.revisions[userId]
	if known == nil then return false, "not loaded" end
	local now = self.now()
	local conflict
	local ok, err = self:_retry(function()
		conflict = nil
		self.store:UpdateAsync(key(userId), function(old)
			if old ~= nil then
				if (old.revision or 0) > known then conflict = "newer revision exists" return nil end
				local lock = old.lock
				if type(lock) == "table" and lock.serverId ~= self.serverId and now - (lock.at or 0) < Store.LOCK_STALE_SEC then
					conflict = "locked by another server"
					return nil
				end
			end
			local doc = { revision = known + 1, savedAt = now, profile = Profile.serialize(P, now) }
			doc.profile.revision = known + 1
			if not release then doc.lock = { serverId = self.serverId, at = now } end
			return doc
		end)
	end)
	if not ok then return false, err end
	if conflict then return false, conflict end
	self.revisions[userId] = known + 1
	P.revision = known + 1
	if release then self.revisions[userId] = nil end
	return true
end
return Store
