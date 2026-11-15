-- Production statistics over sliding time windows (runtime only, not persisted).
local D = require(script.Parent.Data)
local Config, Items = D.Config, D.Items
local Metrics = {}
-- log is a queue with explicit head / tail indices (the # operator is unreliable once entries are pruned)
function Metrics.new() return { log = {}, head = 1, tail = 0 } end
function Metrics.record(stats, clock, ev)
	stats.tail = stats.tail + 1
	stats.log[stats.tail] = { t = clock, item = ev.item, n = ev.n, auto = ev.auto, kind = ev.type }
end
function Metrics.prune(stats, clock)
	local limit = clock - Config.sim.statsWindowSec
	local log = stats.log
	while stats.head <= stats.tail and log[stats.head].t < limit do
		log[stats.head] = nil
		stats.head = stats.head + 1
	end
	if stats.head > 4096 then            -- compact the array from time to time
		local fresh, n = {}, 0
		for i = stats.head, stats.tail do
			n = n + 1
			fresh[n] = log[i]
		end
		stats.log, stats.head, stats.tail = fresh, 1, n
	end
end
local function each(stats, clock, windowSec, fn)
	for i = stats.head, stats.tail do
		local r = stats.log[i]
		if r.t >= clock - windowSec then fn(r) end
	end
end
-- pieces per minute of crafted outputs (liquids count per 1000 ml)
function Metrics.rate(stats, clock, windowSec, item)
	local total = 0
	each(stats, clock, windowSec, function(r)
		if r.kind == "craft" and (item == nil or r.item == item) then
			total = total + ((Items[r.item].unit == "ml") and r.n / 1000 or r.n)
		end
	end)
	return total * 60 / windowSec
end
function Metrics.autoProductLines(stats, clock, windowSec)
	local seen, n = {}, 0
	each(stats, clock, windowSec, function(r)
		if r.kind == "craft" and r.auto and Items[r.item].type == "product" and not seen[r.item] then
			seen[r.item] = true
			n = n + 1
		end
	end)
	return n
end
function Metrics.perItem(stats, clock, windowSec)
	local out = {}
	each(stats, clock, windowSec, function(r)
		local key = r.kind .. ":" .. r.item
		out[key] = (out[key] or 0) + r.n
	end)
	return out
end
return Metrics
