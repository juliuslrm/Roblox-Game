-- Smooth motion of the goods on conveyors, as each client draws it.  Pure Lua, no Roblox API.
--
-- The server only says, per conveyor part, which item lies on it, since when (server time) and in
-- which direction it came in.  An item crosses a part on this path, in exactly the time the server
-- needs to pass it on:
--
--   entry edge  --(first half of the period)-->  cell centre  --(second half)-->  exit edge
--
-- The goods are drawn DELAY seconds in the past.  By then the server update that tells where an
-- item went has arrived, so a hand-over from part to part is known before it is drawn: the item
-- glides through without the stop that waiting for the update would cause, and nothing has to be
-- guessed or taken back.  (For goods on a conveyor half a second of delay is not noticeable; the
-- machine window shows contents without delay.)
--
-- An item stays one visual object on its way: when a part gets an item that the part behind it
-- has just given up, the visual is handed over.
--
-- Usage (see client/GoodsAnimator.client.lua):
--   local m = GoodsMotion.new(cellSize)
--   m:setCarrier(id, { room, floor, gx, gz, x, y, z, out = dir | -1, period })
--   m:setState(id, item | nil, arrivedAt, inDir | nil)      -- whenever the server data changes
--   m:step(now, dt)                                         -- every frame, now = server time
--   m.visuals: serial -> { item, x, y, z, yaw, scale }       -- what to draw
local GoodsMotion = {}
GoodsMotion.__index = GoodsMotion

local DX = { [0] = 0, [1] = 1, [2] = 0, [3] = -1 }
local DZ = { [0] = 1, [1] = 0, [2] = -1, [3] = 0 }
GoodsMotion.DX, GoodsMotion.DZ = DX, DZ
local atan2 = math.atan2 or math.atan   -- Luau has atan2, plain Lua 5.4+ only the two-argument atan

GoodsMotion.DELAY = 0.6      -- seconds the goods are drawn in the past (> update interval + latency)
local LATENCY = 0.15         -- assumed age of a server update when it arrives
local SAME_AT = 0.3          -- arrival times closer than this belong to the same item
local VANISH = 0.4           -- seconds an item needs to slide into a machine and disappear
local SMOOTH = 25            -- 1/s: how fast drawn positions follow remaining corrections

function GoodsMotion.key(room, floor, gx, gz)
	return tostring(room) .. ":" .. floor .. ":" .. gx .. ":" .. gz
end

function GoodsMotion.new(cellSize)
	return setmetatable({ cs = cellSize, carriers = {}, byKey = {}, vis = {}, leaving = {}, visuals = {}, serial = 0 }, GoodsMotion)
end

function GoodsMotion:setCarrier(id, c)
	local old = self.carriers[id]
	if old and self.byKey[old.key] == id then self.byKey[old.key] = nil end
	c.id = id
	c.key = GoodsMotion.key(c.room, c.floor, c.gx, c.gz)
	self.carriers[id] = c
	self.byKey[c.key] = id
end

function GoodsMotion:removeCarrier(id)
	local c = self.carriers[id]
	if not c then return end
	self.vis[id] = nil
	for i = #self.leaving, 1, -1 do
		if self.leaving[i].carrier == id then table.remove(self.leaving, i) end
	end
	if self.byKey[c.key] == id then self.byKey[c.key] = nil end
	self.carriers[id] = nil
end

-- now: current server time, used to date the moment an item disappears
function GoodsMotion:setState(id, item, at, inDir, now)
	local c = self.carriers[id]
	if not c then return end
	if c.item and not item then c.goneAt = (now or c.seenAt or 0) - LATENCY end
	c.item, c.at, c.inDir = item, item and at or nil, item and inDir or nil
end

function GoodsMotion:_neighbour(c, dir)
	local id = self.byKey[GoodsMotion.key(c.room, c.floor, c.gx + DX[dir], c.gz + DZ[dir])]
	return id and self.carriers[id] or nil
end

local function current(v, c)
	return c.item ~= nil and c.item == v.item and math.abs(c.at - v.at) < SAME_AT
end

-- 1. visuals that no longer match their part come loose, 2. parts take over a loose visual from the
-- part behind them, 3. parts still without one get a new visual, 4. the rest leaves (into a machine).
function GoodsMotion:_reconcile(now)
	local ids = {}
	for id in pairs(self.carriers) do ids[#ids + 1] = id end
	table.sort(ids, function(a, b) return self.carriers[a].key < self.carriers[b].key end)
	local loose = {}
	for _, id in ipairs(ids) do
		local v, c = self.vis[id], self.carriers[id]
		if v then
			if current(v, c) then
				v.inDir = c.inDir or v.inDir
			else
				self.vis[id] = nil
				v.carrier = id
				v.goneAt = c.goneAt or (now - LATENCY)
				loose[#loose + 1] = v
			end
		end
	end
	for _, l in ipairs(self.leaving) do loose[#loose + 1] = l end
	local taken = {}
	for _, id in ipairs(ids) do
		local c = self.carriers[id]
		if c.item and not self.vis[id] then
			local inDir = c.inDir or (c.out >= 0 and c.out or 0)
			local src = self:_neighbour(c, (inDir + 2) % 4)
			local adopt
			if src then
				for i, v in ipairs(loose) do
					if not taken[i] and v.carrier == src.id and v.item == c.item and v.at < c.at then
						adopt = i
						break
					end
				end
			end
			if adopt then
				local v = loose[adopt]
				taken[adopt] = true
				v.prev = { carrier = src.id, at = v.at, inDir = v.inDir }
				v.at, v.inDir, v.carrier, v.goneAt = c.at, c.inDir, nil, nil
				self.vis[id] = v
			else
				self.serial = self.serial + 1
				self.vis[id] = { serial = self.serial, item = c.item, at = c.at, inDir = c.inDir }
			end
		end
	end
	self.leaving = {}
	for i, v in ipairs(loose) do
		if not taken[i] and self.carriers[v.carrier] then self.leaving[#self.leaving + 1] = v end
	end
end

-- Point on the path of part `c` at progress p (0 = entry edge, 0.5 = centre, 1 = exit edge, > 1
-- slides on beyond the exit).  outDir overrides the exit (splitters decide per item).
function GoodsMotion:_point(c, inDir, outDir, p)
	local h = self.cs / 2
	if p <= 0.5 then
		local k = p / 0.5
		return c.x + DX[inDir] * h * (k - 1), c.y, c.z + DZ[inDir] * h * (k - 1), inDir
	end
	local k = (p - 0.5) / 0.5
	return c.x + DX[outDir] * h * k, c.y, c.z + DZ[outDir] * h * k, outDir
end

-- where a visual is at render time r: x, y, z, travel direction, scale (nil = not to be drawn yet)
function GoodsMotion:_place(v, c, r)
	if v.goneAt then                                                -- leaving: rest of the way, then into the machine
		local out = c.out >= 0 and c.out or (v.inDir or 0)
		local p = math.min(1, (r - v.at) / c.period)
		local scale = 1
		if r > v.goneAt then
			-- slides on at belt speed into the machine and shrinks away
			local k = math.min(1, (r - v.goneAt) / VANISH)
			p, scale = math.max(p, 1) + (math.min(r, v.goneAt + VANISH) - v.goneAt) / c.period, 1 - 0.8 * k
		end
		local x, y, z, dir = self:_point(c, v.inDir or out, out, p)
		return x, y, z, dir, scale
	end
	if r < v.at then
		local prev = v.prev and self.carriers[v.prev.carrier]
		if not prev then return nil end                             -- arrives later (e.g. out of a machine)
		local inDir = v.prev.inDir or (prev.out >= 0 and prev.out or 0)
		local out = v.inDir or (prev.out >= 0 and prev.out or inDir)  -- leaves towards the part it went to
		local x, y, z, dir = self:_point(prev, inDir, out, math.min(1, math.max(0, (r - v.prev.at) / prev.period)))
		return x, y, z, dir, 1
	end
	v.prev = nil
	local inDir = v.inDir or (c.out >= 0 and c.out or 0)
	local p = math.max(0, (r - v.at) / c.period)
	p = (c.out < 0) and math.min(p, 0.5) or math.min(p, 1)
	local x, y, z, dir = self:_point(c, inDir, c.out >= 0 and c.out or inDir, p)
	return x, y, z, dir, 1
end

function GoodsMotion:step(now, dt)
	self:_reconcile(now)
	local r = now - GoodsMotion.DELAY
	local follow = 1 - math.exp(-SMOOTH * math.max(dt or 0, 0))
	local seen = {}
	local function draw(v, c)
		local x, y, z, dir, scale = self:_place(v, c, r)
		if not x then return end
		local yaw = atan2(DX[dir], DZ[dir])
		if not v.x then
			v.x, v.y, v.z, v.yaw = x, y, z, yaw
		else
			v.x = v.x + (x - v.x) * follow
			v.y = v.y + (y - v.y) * follow
			v.z = v.z + (z - v.z) * follow
			local d = (yaw - v.yaw + math.pi) % (2 * math.pi) - math.pi
			v.yaw = v.yaw + d * follow
		end
		v.scale = scale
		seen[v.serial] = v
	end
	for id, v in pairs(self.vis) do draw(v, self.carriers[id]) end
	local keep = {}
	for _, v in ipairs(self.leaving) do
		local c = self.carriers[v.carrier]
		if c and r < v.goneAt + VANISH then
			draw(v, c)
			keep[#keep + 1] = v
		end
	end
	self.leaving = keep
	self.visuals = seen
end

return GoodsMotion
