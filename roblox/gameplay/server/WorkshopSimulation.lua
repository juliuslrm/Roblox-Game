-- One deterministic simulation step of a workshop (spec §12 order of operations).
local D = require(script.Parent.Data)
local Logistics = require(script.Parent.LogisticsService)
local Production = require(script.Parent.ProductionService)
local Shop = require(script.Parent.ShopService)
local Metrics = require(script.Parent.MetricsService)
local Config = D.Config
local Sim = {}

function Sim.newRuntime()
	return { clock = 0, tick = 0, dirty = true, graph = nil, stats = Metrics.new() }
end

-- Returns the list of events of this step (craft, sell, piped, customer_left).
function Sim.step(P, rt, dt)
	if not (dt == dt) or dt <= 0 then return {} end
	if dt > Config.sim.maxDt then dt = Config.sim.maxDt end
	if rt.dirty or not rt.graph then
		rt.graph = Logistics.build(P)
		rt.dirty = false
	end
	local events = {}
	local function emit(ev) events[#events + 1] = ev end
	rt.clock = rt.clock + dt
	rt.tick = rt.tick + 1
	Logistics.stepSolids(P, rt.graph, dt, rt.tick)
	Logistics.stepFluids(P, rt.graph, dt, emit)
	Production.step(P, rt.graph, dt, emit)
	Shop.step(P, dt, emit)
	for _, ev in ipairs(events) do
		if ev.type == "craft" then
			P.stats.crafted = P.stats.crafted + 1
			Metrics.record(rt.stats, rt.clock, ev)
		elseif ev.type == "sell" then
			Metrics.record(rt.stats, rt.clock, ev)
		end
	end
	Metrics.prune(rt.stats, rt.clock)
	return events
end
return Sim
