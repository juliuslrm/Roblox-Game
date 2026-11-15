-- Machine jobs: the only code that consumes recipe inputs and creates outputs.
local D = require(script.Parent.Data)
local Config, Machines, Recipes, Items, Util = D.Config, D.Machines, D.Recipes, D.Items, D.Util
local Prod = {}

local function storeFor(b, item)
	return (Items[item].unit == "ml") and b.fluids or b.inv
end

-- nil if the job can start, else state name and the missing item.
function Prod.missing(b, r)
	if r.fuelUnits and b.fuel < r.fuelUnits then return "NoFuel", "fuel_charcoal" end
	for _, item in ipairs(Util.sortedKeys(r.inputs)) do
		if (storeFor(b, item)[item] or 0) < r.inputs[item] then return "WaitingForInputs", item end
	end
	return nil
end

local function outputRoom(b, r)
	for item, n in pairs(r.outputs) do
		if Items[item].unit == "ml" then
			if (b.outFluid[item] or 0) + n > Config.machine.fluidCap then return false end
		elseif (b.out[item] or 0) + n > math.max(Config.machine.outputCap, n) then return false end
	end
	return true
end

function Prod.step(P, G, dt, emit)
	local buffers = P.workshop.buffers
	for _, uid in ipairs(G.order) do
		local e, b = G.ents[uid], buffers[uid]
		local def = Machines[e.machine]
		if def.kind == "pump" then
			b.acc = (b.acc or 0) + Config.sim.pumpMlPerSec * dt
			local add = math.floor(b.acc)
			b.acc = b.acc - add
			b.fluids.water = math.min(Config.machine.fluidCap, (b.fluids.water or 0) + add)
			b.state = (b.fluids.water >= Config.machine.fluidCap) and "OutputBlocked" or "Running"
		elseif def.kind == "machine" then
			if e.paused then
				b.state = "Paused"
			else
				local budget, cycles = dt, 0
				while true do
					if not b.job then
						local r = e.recipe and Recipes[e.recipe]
						if not r then b.state, b.waiting = "InvalidRecipe", nil break end
						local state, item = Prod.missing(b, r)
						if state then b.state, b.waiting = state, item break end
						for item2, n in pairs(r.inputs) do
							local store = storeFor(b, item2)
							store[item2] = store[item2] - n
							if store[item2] == 0 then store[item2] = nil end
						end
						if r.fuelUnits then b.fuel = b.fuel - r.fuelUnits end
						b.job = { recipe = r.id, remaining = r.durationSec, auto = (b.auto == true) or (r.source == true),
							inputs = Util.deepCopy(r.inputs) }
						b.waiting = nil
					end
					if b.job.remaining > budget then
						b.job.remaining = b.job.remaining - budget
						b.state = "Running"
						break
					end
					budget = budget - b.job.remaining
					b.job.remaining = 0
					local r = Recipes[b.job.recipe]
					if not outputRoom(b, r) then b.state = "OutputBlocked" break end
					for item, n in pairs(r.outputs) do
						if Items[item].unit == "ml" then b.outFluid[item] = (b.outFluid[item] or 0) + n
						else b.out[item] = (b.out[item] or 0) + n end
						emit({ type = "craft", item = item, n = n, auto = b.job.auto, recipe = r.id, uid = uid })
					end
					b.job = nil
					cycles = cycles + 1
					if cycles >= Config.sim.maxCyclesPerTick then b.state = "Running" break end
				end
			end
		end
	end
end
return Prod
