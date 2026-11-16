-- Shared room geometry for Roblox and the Blender workshop generator.
-- Positions are part centres in room-local Roblox coordinates.
local Architecture = {}

-- open = true builds the walkable outdoor variant that stands on a plot in the village: low stone
-- walls instead of closed ones, a 12 stud opening in the middle of every ground floor wall, no
-- door, no wall decoration and no roof, so the room can be entered and looked into from all sides.
Architecture.OPENING = 12

function Architecture.build(size, floors, height, open)
	local parts, lights = {}, {}
	local h = size / 2
	local function box(name, color, x, y, z, w, t, d, collides, floor, roll)
		parts[#parts + 1] = { name = name, color = color, position = { x, y, z },
			size = { w, t, d }, collides = collides == true, floor = floor, roll = roll }
	end
	local function light(x, y, z, strength, range)
		lights[#lights + 1] = { position = { x, y, z }, strength = strength, range = range }
	end
	local function panel(name, color, x, y, z, w, t, d, roll)
		box(name, color, x, y, z, w, t, d, false, nil, roll)
	end
	for floor = 1, floors do
		local y = (floor - 1) * height
		if floor == 1 then
			box("Floor", "wood_pale", 0, y - 0.5, 0, size, 1, size, true, floor)
		else
			-- The two slabs leave the reserved 6 × 8 stair opening clear.
			box("Floor", "wood_pale", 0, y - 0.5, -4, size, 1, size - 8, true, floor)
			box("FloorLanding", "wood_pale", 3, y - 0.5, h - 4, size - 6, 1, 8, true, floor)
		end
		local function wall(name, x, z, w, d)
			if open then
				box(name, "stone_warm", x, y + 1.2, z, w, 2.4, d, true)
			else
				box(name, "plaster_cream", x, y + height / 2, z, w, height, d, true)
				panel(name .. "StoneSkirt", "stone_warm", x, y + 1.2, z, w + 0.12, 2.4, d + 0.12)
			end
			panel(name .. "SillBeam", "wood_dark", x, y + 2.65, z, w + 0.16, 0.48, d + 0.16)
			panel(name .. "EavesBeam", "wood_dark", x, y + height - 0.46, z, w + 0.2, 0.9, d + 0.2)
		end
		if open and floor == 1 then
			-- every side: two wall pieces with an opening between them, a beam above the opening
			local gap = Architecture.OPENING
			local piece = (size - gap) / 2
			local offset = gap / 2 + piece / 2
			for s = -1, 1, 2 do
				wall("WestWall", -h - 0.5, s * offset, 1, piece)
				wall("EastWall", h + 0.5, s * offset, 1, piece)
				wall("RearWall", s * (offset + 0.5), h + 0.5, piece + 1, 1)
				wall("FrontWall", s * (offset + 0.5), -h - 0.5, piece + 1, 1)
				for _, side in ipairs({ -1, 1 }) do
					panel("GatePost", "wood_dark", s * (h + 0.5), y + height / 2, side * gap / 2, 0.9, height, 0.9)
					panel("GatePost", "wood_dark", side * gap / 2, y + height / 2, s * (h + 0.5), 0.9, height, 0.9)
				end
				panel("GateBeam", "wood_dark", s * (h + 0.5), y + height - 0.46, 0, 1.2, 0.9, gap)
				panel("GateBeam", "wood_dark", 0, y + height - 0.46, s * (h + 0.5), gap, 0.9, 1.2)
			end
		else
			wall("WestWall", -h - 0.5, 0, 1, size)
			wall("EastWall", h + 0.5, 0, 1, size)
			wall("RearWall", 0, h + 0.5, size + 2, 1)
		end
		if open and floor == 1 then
			-- walls and openings are complete
		elseif floor == 1 then
			local width = h - 3
			wall("FrontWallLeft", -(3 + width / 2), -h - 0.5, width, 1)
			wall("FrontWallRight", 3 + width / 2, -h - 0.5, width, 1)
			box("Lintel", "wood_dark", 0, height - 1, -h - 0.5, 6.5, 2, 1, true)
			box("ExitDoor", "wood_red", 0, 4.3, -h - 0.12, 5.9, 8.6, 0.48, true)
			panel("DoorPanel", "wood_mid", 0, 4.5, -h + 0.14, 4.9, 7.4, 0.14)
			panel("DoorBrace", "iron", 0, 3.2, -h + 0.23, 5.1, 0.26, 0.14)
			panel("DoorBrace", "iron", 0, 6.1, -h + 0.23, 5.1, 0.26, 0.14)
			panel("DoorHandle", "brass", 1.65, 4.1, -h + 0.32, 0.34, 0.36, 0.24)
		else
			wall("FrontWall", 0, -h - 0.5, size + 2, 1)
		end
		for s = -1, 1, 2 do
			for p = -h + 7, h - 5, 8 do
				if not (open and floor == 1 and math.abs(p) < Architecture.OPENING / 2 + 0.5) then
					panel("WallPost", "wood_dark", s * (h + 0.18), y + height / 2, p, 0.54, height, 0.62)
				end
				if floor == 1 and s == 1 and p < -2 and not open then
					panel("WindowFrame", "wood_dark", h - 0.12, y + 6.6, p + 3.3, 0.22, 4.6, 5.3)
					panel("AmberWindow", "glass_lit", h - 0.27, y + 6.6, p + 3.3, 0.12, 3.8, 4.5)
					panel("WindowMullion", "wood_dark", h - 0.4, y + 6.6, p + 3.3, 0.2, 4, 0.24)
					panel("WindowCrossbar", "wood_dark", h - 0.4, y + 6.6, p + 3.3, 0.2, 0.27, 4.5)
					panel("WindowSill", "wood_mid", h - 0.34, y + 4.4, p + 3.3, 0.66, 0.25, 5.6)
				end
			end
			panel("CornerPost", "wood_dark", s * h, y + height / 2, -h, 0.9, height, 0.9)
			panel("CornerPost", "wood_dark", s * h, y + height / 2, h, 0.9, height, 0.9)
		end
		-- The braces sit against the plaster so the room stays clear below them.
		local bays = math.floor(size / 8)
		local bayWidth = size / bays
		for i = 1, open and 0 or bays do
			local x = -h + (i - 0.5) * bayWidth
			local rise = 3.75
			local span = bayWidth - 0.65
			local angle = math.deg(math.atan(rise / span))
			local beamLength = math.sqrt(span * span + rise * rise)
			panel("RearTrim", "plaster_sage", x, y + 7.25, h - 0.04, span + 0.1, 4.45, 0.14)
			panel("RearBeam", "wood_dark", x, y + 7.25, h - 0.15, beamLength, 0.3, 0.24, angle)
			panel("RearBeam", "wood_mid", x, y + 7.25, h - 0.2, beamLength, 0.25, 0.24, -angle)
			panel("RearPost", "wood_dark", x - bayWidth / 2, y + height / 2, h - 0.13, 0.57, height, 0.6)
		end
		if not open then
			panel("RearBeam", "wood_dark", 0, y + 5.03, h - 0.14, size, 0.35, 0.44)
			panel("RearBeam", "wood_dark", 0, y + 9.45, h - 0.14, size, 0.35, 0.44)
		end
		for z = -h + 4, h - 2, 8 do
			panel("Rafter", "wood_dark", 0, y + height - 0.5, z, size, 0.7, 0.65)
		end
		local lamps = math.max(2, math.floor(size / 14))
		for i = 1, lamps do
			local z = -h + i * size / (lamps + 1)
			for _, x in ipairs({ -h * 0.6, h * 0.6 }) do
				panel("LampMount", "iron", x, y + height - 0.7, z, 0.18, 1, 0.18)
				panel("Lamp", "glass_lit", x, y + height - 1.36, z, 0.64, 0.8, 0.64)
				panel("LampCap", "iron", x, y + height - 0.88, z, 0.8, 0.19, 0.8)
				light(x, y + height - 1.5, z, 0.9, 20)
			end
		end
		if floor < floors then
			-- Walk up along the west edge of the stairwell and turn onto the upper landing.
			for i = 1, 12 do
				local t = i * height / 12
				box("StairTread", "wood_mid", -h + 2, y + t - 0.5, h - 8 + (i - 0.5) * 8 / 12,
					4, 1, 8 / 12 + 0.04, true)
			end
			box("StairLanding", "wood_mid", -h + 5, y + height - 0.5, h - 0.55, 2, 1, 1.1, true)
		end
	end

	if open then return parts, lights end

	-- Plaster recess and shelf anchored to the outer wall, outside the machine grid.
	panel("HearthStone", "stone_dark", -h + 0.02, 4.9, -1, 0.16, 5.1, 7.4)
	for row = 0, 4 do
		for col = 0, 3 do
			panel("HearthBlock", (row + col) % 3 == 0 and "stone_light" or "stone_warm",
				-h + 0.15, 2.9 + row * 0.94, -3.72 + col * 1.7 + (row % 2) * 0.34,
				0.2, 0.77, 1.54)
		end
	end
	panel("HerbRail", "wood_mid", h - 0.08, 8.85, -h + 9, 0.34, 0.3, 5.2)
	panel("BottleLedge", "wood_mid", h - 0.16, 5.5, -h + 9, 0.55, 0.22, 5.2)
	for i = 1, 4 do
		local z = -h + 7 + i * 0.8
		panel("HerbStem", "wood_pale", h - 0.29, 8.45, z, 0.13, 0.66, 0.12)
		panel("DriedHerbs", i % 2 == 0 and "leaf_dark" or "leaf_teal", h - 0.37, 7.95, z, 0.29, 0.61, 0.36)
		panel("Bottle", i % 2 == 0 and "glass_light" or "roof_purple", h - 0.26, 5.95, z, 0.26, 0.56, 0.39)
		panel("BottleLabel", "plaster_cream", h - 0.41, 5.91, z, 0.05, 0.18, 0.3)
		panel("BottleCork", "wood_pale", h - 0.26, 6.29, z, 0.19, 0.17, 0.19)
	end
	light(h - 1, 7, -h + 4, 1.6, 22)
	light(-h + 3, 6, -1, 1.15, 18)
	return parts, lights
end

return Architecture
