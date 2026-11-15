-- Server-owned gathering nodes shared by all players of a server.
local D = require(script.Parent.Data)
local Inv = require(script.Parent.InventoryService)
local Locations = D.Locations
local Res = {}
function Res.new()
	local nodes = {}
	for id, def in pairs(Locations.nodes) do nodes[id] = { remaining = def.capacity, timer = 0 } end
	return nodes
end
function Res.step(nodes, dt)
	for id, state in pairs(nodes) do
		local def = Locations.nodes[id]
		if state.remaining < def.capacity then
			state.timer = state.timer + dt
			while state.timer >= def.respawnSec and state.remaining < def.capacity do
				state.timer = state.timer - def.respawnSec
				state.remaining = math.min(def.capacity, state.remaining + def.amount)
			end
		else
			state.timer = 0
		end
	end
end
-- Returns gained amount or nil, code. Takes at most one portion; never more than is left or fits.
function Res.gather(nodes, P, nodeId)
	local def, state = Locations.nodes[nodeId], nodes[nodeId]
	if not def then return nil, "NOT_FOUND" end
	if state.remaining <= 0 then return nil, "NOT_READY" end
	local n = math.min(def.amount, state.remaining, Inv.room(P.items, def.item, Inv.PLAYER))
	if n <= 0 then return nil, "NO_SPACE" end
	state.remaining = state.remaining - n
	Inv.add(P.items, { [def.item] = n })
	return n
end
return Res
