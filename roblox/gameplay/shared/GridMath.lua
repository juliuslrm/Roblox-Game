-- Grid geometry of the workshop. Cells are integers; direction 0=+z 1=+x 2=-z 3=-x.
local GridMath = {}
GridMath.DX = { [0] = 0, [1] = 1, [2] = 0, [3] = -1 }
GridMath.DZ = { [0] = 1, [1] = 0, [2] = -1, [3] = 0 }
function GridMath.key(floor, x, z)
	return floor * 1000000 + x * 1000 + z
end
function GridMath.size(def, rot)
	if rot % 2 == 0 then return def.w, def.d end
	return def.d, def.w
end
-- local cell (lx, lz) of a w x d footprint -> offset inside the rotated footprint
function GridMath.rotateCell(lx, lz, w, d, rot)
	if rot == 0 then return lx, lz
	elseif rot == 1 then return lz, w - 1 - lx
	elseif rot == 2 then return w - 1 - lx, d - 1 - lz
	end
	return d - 1 - lz, lx
end
function GridMath.cells(def, gx, gz, rot)
	local w, d = GridMath.size(def, rot)
	local out = {}
	for x = 0, w - 1 do
		for z = 0, d - 1 do out[#out + 1] = { gx + x, gz + z } end
	end
	return out
end
-- world cell and facing of a port for an entity placed at (gx, gz) with rotation rot
function GridMath.port(def, port, gx, gz, rot)
	local ox, oz = GridMath.rotateCell(port.x, port.z, def.w, def.d, rot)
	local dir = (port.dir + rot) % 4
	return gx + ox, gz + oz, dir
end
function GridMath.opposite(dir)
	return (dir + 2) % 4
end
return GridMath
