-- Connects the gameplay to the generated village WITHOUT changing it.
-- computeAnchors() is pure: it derives every interaction point from WorldLayout (asset id of the
-- unique building instance), so anchors follow the buildings when the world is regenerated.
local D = require(script.Parent.Data)
local Locations = D.Locations
local Adapter = {}

-- layout = require(WorldLayout). Returns anchors, nodeAnchors, missing (location ids without instance).
-- Anchor fields: x, y, z (y = ground height of the instance origin), fx, fz (unit vector pointing
-- away from the building), yaw (degrees).
function Adapter.computeAnchors(layout)
	local index = {}
	for i, name in ipairs(layout.assetNames) do index[name] = i end
	local byAsset = {}
	for _, row in ipairs(layout.instances) do
		local name = layout.assetNames[row[1]]
		if not byAsset[name] then byAsset[name] = row end
	end
	local anchors, nodeAnchors, missing = {}, {}, {}
	for id, loc in pairs(Locations.locations) do
		local row, def = byAsset[loc.asset], layout.assets[loc.asset]
		if row and def then
			local yaw = math.rad(row[5])
			local fx, fz = math.sin(yaw), math.cos(yaw)                 -- model front (+Z) in world space
			local reach = def.center[3] + def.size[3] / 2 + (loc.standoff or 5)
			if id == "plaza" then reach = def.size[3] / 2 + 6 end
			anchors[id] = { x = row[2] + fx * reach, y = row[3], z = row[4] + fz * reach, fx = fx, fz = fz,
				yaw = row[5], originX = row[2], originZ = row[4] }
		else
			missing[#missing + 1] = id
		end
	end
	for id, node in pairs(Locations.nodes) do
		local a = anchors[node.at]
		if a then
			local rx, rz = a.fz, -a.fx                                  -- right-hand side when looking at the door
			nodeAnchors[id] = { x = a.x + rx * node.ox + a.fx * node.oz, y = a.y, z = a.z + rz * node.ox + a.fz * node.oz }
		end
	end
	return anchors, nodeAnchors, missing
end
return Adapter
