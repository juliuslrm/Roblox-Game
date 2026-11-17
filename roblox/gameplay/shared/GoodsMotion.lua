-- Smooth motion of the goods on conveyors, as each client draws it.  Pure Lua, no Roblox API.
--
-- The server only says, per conveyor part, which item lies on it, since when (server time) and in
-- which direction it came in.  An item crosses a part from the entry edge to the exit edge - straight,
-- or on a quarter circle where it turns - in exactly the time the server needs to pass it on.
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
--   m:setCarrier(id, { room, floor, gx, gz, x, y, z, out = dir | -1, period, next?, rise?, warp? })
--   m:setState(id, item | nil, arrivedAt, inDir | nil)      -- whenever the server data changes
--   m:step(now, dt)                                         -- every frame, now = server time
--   m.visuals: serial -> { item, x, y, z, yaw, spin, scale }  -- what to draw
local Grid = require(script.Parent.GridMath)
local GoodsMotion = {}
GoodsMotion.__index = GoodsMotion

-- Where goods go after part `e` (server and tests use this to describe a part to the client):
--   next  = { gx, floor, gz } cell the goods are handed to (single-exit parts only)
--   rise  = floors the goods climb on the way (lift)
--   warp  = { gx, floor, gz, out } partner gate the goods reappear at, and its exit direction
function GoodsMotion.links(def, e, partner)
	local outs = {}
	for _, p in ipairs(def.ports or {}) do
		if p.mode == "out" then outs[#outs + 1] = p end
	end
	if #outs ~= 1 then return {} end
	local px, pz, dir = Grid.port(def, outs[1], e.gx, e.gz, e.rot)
	if def.kind == "lift" then
		return { next = { gx = px + Grid.DX[dir], floor = e.floor + 1, gz = pz + Grid.DZ[dir] }, rise = 1 }
	elseif def.kind == "gate" then
		if not partner then return {} end
		local qx, qz, qdir = Grid.port(def, outs[1], partner.gx, partner.gz, partner.rot)
		return { next = { gx = qx + Grid.DX[qdir], floor = partner.floor, gz = qz + Grid.DZ[qdir] },
			warp = { gx = partner.gx, floor = partner.floor, gz = partner.gz, out = qdir } }
	end
	return { next = { gx = px + Grid.DX[dir], floor = e.floor, gz = pz + Grid.DZ[dir] } }
end

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

-- c.next = { gx, floor, gz } (optional), c.rise = height to climb in studs (lift, optional),
-- c.warp = { x, y, z, out } surface point and exit direction of the partner gate (optional)
function GoodsMotion:setCarrier(id, c)
	local old = self.carriers[id]
	if old and self.byKey[old.key] == id then self.byKey[old.key] = nil end
	c.id = id
	c.key = GoodsMotion.key(c.room, c.floor, c.gx, c.gz)
	c.nextKey = c.next and GoodsMotion.key(c.room, c.next.floor, c.next.gx, c.next.gz) or nil
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
			for i, v in ipairs(loose) do
				local from = self.carriers[v.carrier]
				if not taken[i] and from and v.item == c.item and v.at < c.at
					and (from.nextKey == c.key or (src and from.id == src.id and from.nextKey == nil)) then
					adopt = i
					break
				end
			end
			if adopt then
				local v = loose[adopt]
				taken[adopt] = true
				v.prev = { carrier = v.carrier, at = v.at, inDir = v.inDir }
				v.at, v.inDir, v.carrier, v.goneAt = c.at, c.inDir, nil, nil
				self.vis[id] = v
			else
				-- comes out of a machine or hopper (or the client has just started watching)
				self.serial = self.serial + 1
				self.vis[id] = { serial = self.serial, item = c.item, at = c.at, inDir = c.inDir, emerge = now - c.at < 1.5 }
			end
		end
	end
	self.leaving = {}
	for i, v in ipairs(loose) do
		if not taken[i] and self.carriers[v.carrier] then self.leaving[#self.leaving + 1] = v end
	end
end

-- Point on the way across one cell (centre cx, cz, half width h) from the entry edge to the exit
-- edge at fraction f (0..1): straight through, or a quarter circle around the inner corner when
-- the goods turn.  Returns x, z and the travel heading (yaw, radians).  Shared with the moving
-- cleats of the belt surface (GoodsAnimator), so goods and belt run on the same line.
function GoodsMotion.pathPoint(cx, cz, h, inDir, outDir, f)
	local ix, iz, ox, oz = DX[inDir], DZ[inDir], DX[outDir], DZ[outDir]
	if ix * ox + iz * oz == 0 then
		-- turn: pivot in the inner corner, radius = half a cell
		local px, pz = cx + (ox - ix) * h, cz + (oz - iz) * h
		local a = f * math.pi / 2
		local ex, ez = cx - ix * h - px, cz - iz * h - pz          -- pivot -> entry
		local qx, qz = cx + ox * h - px, cz + oz * h - pz          -- pivot -> exit
		local x = px + ex * math.cos(a) + qx * math.sin(a)
		local z = pz + ez * math.cos(a) + qz * math.sin(a)
		local tx, tz = -ex * math.sin(a) + qx * math.cos(a), -ez * math.sin(a) + qz * math.cos(a)
		return x, z, atan2(tx, tz)
	end
	if ix * ox + iz * oz < 0 then outDir, ox, oz = inDir, ix, iz end   -- (cannot happen on a conveyor)
	if f <= 0.5 then
		local k = f / 0.5 - 1
		return cx + ix * h * k, cz + iz * h * k, atan2(ix, iz)
	end
	local k = (f - 0.5) / 0.5
	return cx + ox * h * k, cz + oz * h * k, atan2(ox, oz)
end

-- Pose on the path of part `c` at progress p (0 = entry edge, 1 = exit edge):
-- x, y, z, heading (yaw), scale, spin (extra turn in radians).  outDir overrides the exit
-- (splitters decide per item).
--   lift: into the shaft, up one floor, out at the top
--   gate: into the portal (shrinks and swirls), out of the partner gate (grows), on to its exit
function GoodsMotion:_pose(c, inDir, outDir, p)
	local h = self.cs / 2
	local function edge(x, y, z, dir, k) return x + DX[dir] * h * k, y, z + DZ[dir] * h * k, atan2(DX[dir], DZ[dir]) end
	if c.rise and c.rise ~= 0 then
		if p <= 0.3 then
			local x, y, z, yaw = edge(c.x, c.y, c.z, inDir, p / 0.3 - 1)
			return x, y, z, yaw, 1, 0
		elseif p <= 0.8 then
			local k = (p - 0.3) / 0.5
			k = k * k * (3 - 2 * k)                                  -- eases in and out of the climb
			return c.x, c.y + c.rise * k, c.z, atan2(DX[inDir], DZ[inDir]), 1, k * math.pi
		end
		local x, y, z, yaw = edge(c.x, c.y + c.rise, c.z, outDir, (p - 0.8) / 0.2)
		return x, y, z, yaw, 1, 0
	end
	if c.warp then
		local w = c.warp
		if p <= 0.5 then
			local x, y, z, yaw = edge(c.x, c.y, c.z, inDir, p / 0.5 - 1)
			return x, y, z, yaw, 1, 0
		elseif p <= 0.72 then                                         -- swirls into the portal
			local k = (p - 0.5) / 0.22
			return c.x, c.y + 0.6 * k, c.z, atan2(DX[inDir], DZ[inDir]), 1 - k, k * 3 * math.pi
		elseif p <= 0.86 then                                         -- and out of the partner
			local k = (p - 0.72) / 0.14
			return w.x, w.y + 0.6 * (1 - k), w.z, atan2(DX[w.out], DZ[w.out]), k, (1 - k) * 3 * math.pi
		end
		local x, y, z, yaw = edge(w.x, w.y, w.z, w.out, (p - 0.86) / 0.14)
		return x, y, z, yaw, 1, 0
	end
	local x, z, yaw = GoodsMotion.pathPoint(c.x, c.z, h, inDir, outDir, p)
	return x, c.y, z, yaw, 1, 0
end

-- where a visual is at render time r: x, y, z, heading, scale, spin (nil = not drawn yet)
function GoodsMotion:_place(v, c, r)
	if v.goneAt then
		-- leaving into a machine or crate: to the exit at belt speed, on into the opening, then a small
		-- hop and down - as if dropped into the funnel - shrinking and turning a little
		local out = c.out >= 0 and c.out or (v.inDir or 0)
		local p = math.min(1, (r - v.at) / c.period)
		local x, y, z, yaw, scale, spin = self:_pose(c, v.inDir or out, out, p)
		if r > v.goneAt then
			local k = math.min(1, (r - v.goneAt) / VANISH)
			local slide = (math.min(r, v.goneAt + VANISH) - v.goneAt) / c.period * self.cs
			x, z = x + DX[out] * slide, z + DZ[out] * slide
			y = y + 0.35 * math.sin(k * math.pi) - 0.6 * k * k
			scale, spin = scale * (1 - 0.85 * k), spin + k * 1.2
		end
		return x, y, z, yaw, scale, spin
	end
	if r < v.at then
		local prev = v.prev and self.carriers[v.prev.carrier]
		if not prev then return nil end                             -- arrives later (e.g. out of a machine)
		local inDir = v.prev.inDir or (prev.out >= 0 and prev.out or 0)
		local out = prev.out >= 0 and prev.out or (v.inDir or inDir)   -- splitters: towards where it went
		return self:_pose(prev, inDir, out, math.min(1, math.max(0, (r - v.prev.at) / prev.period)))
	end
	v.prev = nil
	local inDir = v.inDir or (c.out >= 0 and c.out or 0)
	local p = math.max(0, (r - v.at) / c.period)
	p = (c.out < 0) and math.min(p, 0.5) or math.min(p, 1)
	local x, y, z, yaw, scale, spin = self:_pose(c, inDir, c.out >= 0 and c.out or inDir, p)
	if v.emerge then
		-- pushed out of the machine: rises out of the opening and grows to full size
		local k = math.min(1, (r - v.at) / (c.period * 0.25))
		if k >= 1 then v.emerge = nil end
		y, scale = y - 0.5 * (1 - k), scale * (0.25 + 0.75 * k)
	end
	return x, y, z, yaw, scale, spin
end

function GoodsMotion:step(now, dt)
	self:_reconcile(now)
	local r = now - GoodsMotion.DELAY
	local follow = 1 - math.exp(-SMOOTH * math.max(dt or 0, 0))
	local seen = {}
	local function draw(v, c)
		local x, y, z, yaw, scale, spin = self:_place(v, c, r)
		if not x then return end
		if not v.x then
			v.x, v.y, v.z, v.yaw = x, y, z, yaw
		else
			v.x = v.x + (x - v.x) * follow
			v.y = v.y + (y - v.y) * follow
			v.z = v.z + (z - v.z) * follow
			local d = (yaw - v.yaw + math.pi) % (2 * math.pi) - math.pi
			v.yaw = v.yaw + d * follow
		end
		v.scale, v.spin = scale, spin or 0
		-- a jump of the target (portal) is taken over at once, not smoothed across the workshop
		if (x - v.x) ^ 2 + (z - v.z) ^ 2 > (self.cs * 1.5) ^ 2 then v.x, v.y, v.z = x, y, z end
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
