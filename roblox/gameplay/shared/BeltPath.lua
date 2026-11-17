-- Conveyor lines: the cells and directions of a belt run from a start to an end cell, and the
-- reserved cells of a workshop.  Pure data logic, shared by the build preview and the server.
local BeltPath = {}
BeltPath.MAX = 64                      -- belts in one line

local function dirOf(dx, dz)
	if dz > 0 then return 0 elseif dx > 0 then return 1 elseif dz < 0 then return 2 end
	return 3
end
BeltPath.dirOf = dirOf

-- Cells from (sx, sz) to (ex, ez): first along the axis with the longer distance, then the other
-- one (one corner at most).  Every belt points to the next cell; the corner belt takes the goods in
-- from its side.  single: direction of a one-cell line.  flip: goods run from the end to the start.
-- Returns { { gx, gz, rot }, ... } in the order the goods travel, or nil if longer than MAX.
function BeltPath.cells(sx, sz, ex, ez, single, flip)
	local dx, dz = ex - sx, ez - sz
	local list = { { gx = sx, gz = sz } }
	local x, z = sx, sz
	local function walk(stepX, stepZ, count)
		for _ = 1, count do
			x, z = x + stepX, z + stepZ
			list[#list + 1] = { gx = x, gz = z }
		end
	end
	local sxn, szn = (dx > 0 and 1) or (dx < 0 and -1) or 0, (dz > 0 and 1) or (dz < 0 and -1) or 0
	if math.abs(dx) >= math.abs(dz) then
		walk(sxn, 0, math.abs(dx))
		walk(0, szn, math.abs(dz))
	else
		walk(0, szn, math.abs(dz))
		walk(sxn, 0, math.abs(dx))
	end
	if #list > BeltPath.MAX then return nil end
	if flip then
		local rev = {}
		for i = #list, 1, -1 do rev[#rev + 1] = list[i] end
		list = rev
	end
	if #list == 1 then
		list[1].rot = flip and (single + 2) % 4 or single
		return list
	end
	for i = 1, #list do
		local a, b = list[i], list[i + 1] or list[i]
		local p = list[i - 1]
		if list[i + 1] then a.rot = dirOf(b.gx - a.gx, b.gz - a.gz)
		else a.rot = dirOf(a.gx - p.gx, a.gz - p.gz) end
	end
	return list
end

-- Cells nobody may build on: the entrance (front edge, floor 1) and the staircase (back-left corner).
function BeltPath.reserved(cells, doorWidth, doorDepth, floor, x, z)
	if floor == 1 then
		local x0 = math.floor(cells / 2) - math.floor(doorWidth / 2)
		if x >= x0 and x < x0 + doorWidth and z < doorDepth then return true end
	end
	return x < 3 and z >= cells - 4
end

return BeltPath
