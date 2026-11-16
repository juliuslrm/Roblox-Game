-- Inlet and outlet sides of production machines.  Pure data logic, shared by server and client.
--
-- A side is a direction in the machine's own frame (0 = front +z, 1 = right +x, 2 = back -z,
-- 3 = left -x); it turns with the machine.  The connection cell of a side is the middle cell of
-- that edge of the footprint.  Solid goods may use every side that carries no fluid connection.
--   entity.inSide   chosen inlet side   (nil = definition default: back)
--   entity.outSide  current outlet side (nil = definition default: front)
--   entity.outAuto  false = the player fixed the outlet; anything else = automatic
-- Automatic outlet: the outlet moves to a side where a conveyor leads away from the connection.
local Grid = require(script.Parent.GridMath)
local MP = {}

MP.DEFAULT_IN, MP.DEFAULT_OUT = 2, 0
MP.SIDE_NAME = { [0] = "vorn", [1] = "rechts", [2] = "hinten", [3] = "links" }
-- things that carry solid goods onwards and take them in at their back
MP.CARRIER = { belt = true, splitter = true, merger = true, sorter = true, lift = true, gate = true }

function MP.isMachine(def) return def ~= nil and def.kind == "machine" end

-- local port (x, z, dir) of a side: middle cell of that edge
function MP.sidePort(def, side)
	local cx, cz = math.floor((def.w - 1) / 2), math.floor((def.d - 1) / 2)
	if side == 0 then return { x = cx, z = def.d - 1, dir = 0 }
	elseif side == 1 then return { x = def.w - 1, z = cz, dir = 1 }
	elseif side == 2 then return { x = cx, z = 0, dir = 2 }
	end
	return { x = 0, z = cz, dir = 3 }
end

-- side -> "fluidIn" | "fluidOut" for sides taken by a pipe connection
function MP.fluidSides(def)
	local taken = {}
	for _, p in ipairs(def.ports or {}) do
		if p.type == "fluid" then taken[p.dir] = (p.mode == "in") and "fluidIn" or "fluidOut" end
	end
	return taken
end

-- sides solid goods may use, in the fixed search order: definition default first, then clockwise
function MP.solidSides(def)
	local taken, out = MP.fluidSides(def), {}
	for _, side in ipairs({ 0, 1, 2, 3 }) do
		if not taken[side] then out[#out + 1] = side end
	end
	return out
end

local function allowed(def, side)
	if type(side) ~= "number" or side % 1 ~= 0 or side < 0 or side > 3 then return false end
	return MP.fluidSides(def)[side] == nil
end
MP.allowed = allowed

-- Resolved sides of an entity; repairs impossible stored values instead of failing.
function MP.sides(def, e)
	local inSide = allowed(def, e.inSide) and e.inSide or MP.DEFAULT_IN
	local outSide = allowed(def, e.outSide) and e.outSide or MP.DEFAULT_OUT
	if inSide == outSide then
		inSide, outSide = MP.DEFAULT_IN, MP.DEFAULT_OUT
	end
	return inSide, outSide
end

function MP.isAuto(e) return e.outAuto ~= false end

-- World cell of the connection of `side` and the direction pointing out of the machine.
function MP.cell(def, e, side)
	return Grid.port(def, MP.sidePort(def, side), e.gx, e.gz, e.rot)
end

-- Does a conveyor lead away from the connection of `side`?  entAt(floor, x, z) -> entity, def.
-- It must stand in the cell straight in front of the connection and take goods in at its back;
-- one that runs towards the machine, passes sideways or stands diagonally does not count.
function MP.leadsAway(def, e, side, entAt)
	local x, z, dir = MP.cell(def, e, side)
	local n, ndef = entAt(e.floor, x + Grid.DX[dir], z + Grid.DZ[dir])
	return n ~= nil and MP.CARRIER[ndef.kind] == true and n.rot % 4 == dir
end

-- Side an automatic outlet should use: the current one while it still has a conveyor, otherwise
-- the first suitable side in the fixed order, otherwise unchanged.
function MP.autoSide(def, e, entAt)
	local inSide, outSide = MP.sides(def, e)
	if MP.leadsAway(def, e, outSide, entAt) then return outSide end
	for _, side in ipairs(MP.solidSides(def)) do
		if side ~= inSide and side ~= outSide and MP.leadsAway(def, e, side, entAt) then return side end
	end
	return outSide
end

return MP
