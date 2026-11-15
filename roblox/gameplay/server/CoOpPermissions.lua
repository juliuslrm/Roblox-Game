-- Session-scoped co-op rights. Nothing here is persisted (spec §4: no hosted factory without the owner).
local Co = {}
Co.RANK = { visitor = 1, operator = 2, builder = 3, owner = 4 }
function Co.role(world, ownerId, userId)
	if ownerId == userId then return "owner" end
	local grants = world.coop[ownerId]
	return grants and grants[userId] or nil
end
function Co.atLeast(world, ownerId, userId, role)
	local have = Co.role(world, ownerId, userId)
	return have ~= nil and Co.RANK[have] >= Co.RANK[role]
end
-- Owner grants or revokes ("none"). Ownership itself can never be transferred.
function Co.set(world, ownerId, userId, role)
	if userId == ownerId then return false end
	world.coop[ownerId] = world.coop[ownerId] or {}
	if role == "none" then
		world.coop[ownerId][userId] = nil
		return true
	end
	if role ~= "visitor" and role ~= "operator" and role ~= "builder" then return false end
	world.coop[ownerId][userId] = role
	return true
end
function Co.clearOwner(world, ownerId) world.coop[ownerId] = nil end
return Co
