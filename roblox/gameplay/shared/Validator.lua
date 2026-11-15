-- Referential integrity checks over all data tables. Returns a list of error strings (empty = valid).
local Validator = {}
function Validator.run(D)
	local errs = {}
	local function e(msg) errs[#errs + 1] = msg end
	local Items, Recipes, Machines, Research, Quests, Locations, Config =
		D.Items, D.Recipes, D.Machines, D.Research, D.Quests, D.Locations, D.Config
	local function isInt(v) return type(v) == "number" and math.floor(v) == v end
	for id, it in pairs(Items) do
		if it.id ~= id then e("item id mismatch " .. id) end
		if not (isInt(it.sellBase) and it.sellBase >= 0) then e("item sellBase " .. id) end
		if it.type == "product" and it.sellBase <= 0 then e("product without price " .. id) end
		if it.type ~= "product" and it.sellBase ~= 0 then e("non-product is sellable " .. id) end
	end
	local unlockedBy = {}
	for id, n in pairs(Research) do
		if n.id ~= id then e("research id mismatch " .. id) end
		for _, p in ipairs(n.prereqs) do
			if not Research[p] then e("research " .. id .. " unknown prereq " .. p) end
		end
		for _, u in ipairs(n.unlocks) do
			if unlockedBy[u] then e("unlock " .. u .. " granted twice") end
			unlockedBy[u] = id
		end
	end
	-- DAG check (depth first)
	local state = {}
	local function visit(id)
		if state[id] == 2 then return end
		if state[id] == 1 then e("research cycle at " .. id) return end
		state[id] = 1
		for _, p in ipairs(Research[id].prereqs) do if Research[p] then visit(p) end end
		state[id] = 2
	end
	for id in pairs(Research) do visit(id) end
	for id, m in pairs(Machines) do
		if m.id ~= id then e("machine id mismatch " .. id) end
		if not Research[m.research] then e("machine " .. id .. " unknown research") end
		if unlockedBy[id] ~= m.research then e("machine " .. id .. " not unlocked by its research node") end
		if not (isInt(m.w) and isInt(m.d) and m.w >= 1 and m.d >= 1) then e("machine footprint " .. id) end
		if not (isInt(m.cost) and m.cost >= 0) then e("machine cost " .. id) end
		for _, p in ipairs(m.ports) do
			if p.x < 0 or p.x >= m.w or p.z < 0 or p.z >= m.d then e("port outside footprint " .. id) end
		end
	end
	local produced, crafting = {}, 0
	for id, r in pairs(Recipes) do
		if r.id ~= id then e("recipe id mismatch " .. id) end
		local m = Machines[r.machineId]
		if not m then e("recipe " .. id .. " unknown machine") end
		if not Research[r.requiredResearch] then e("recipe " .. id .. " unknown research")
		elseif unlockedBy[id] ~= r.requiredResearch then e("recipe " .. id .. " not unlocked by its research node") end
		if not (r.durationSec and r.durationSec > 0) then e("recipe duration " .. id) end
		if not r.supply then crafting = crafting + 1 end
		local n = 0
		for item, amount in pairs(r.inputs) do
			n = n + 1
			if not Items[item] then e("recipe " .. id .. " unknown input " .. item)
			elseif not (isInt(amount) and amount > 0) then e("recipe " .. id .. " bad amount " .. item)
			elseif Items[item].unit == "ml" and m then
				local ok = false
				for _, p in ipairs(m.ports) do if p.type == "fluid" and p.mode == "in" then ok = true end end
				if not ok then e("recipe " .. id .. " needs liquid but " .. r.machineId .. " has no fluid input") end
			end
		end
		if n == 0 and not r.source then e("recipe " .. id .. " has no inputs") end
		for item, amount in pairs(r.outputs) do
			if not Items[item] then e("recipe " .. id .. " unknown output " .. item)
			elseif not (isInt(amount) and amount > 0) then e("recipe " .. id .. " bad output amount") end
			produced[item] = true
			if Items[item] and Items[item].unit == "ml" and m then
				local ok = false
				for _, p in ipairs(m.ports) do if p.type == "fluid" and p.mode == "out" then ok = true end end
				if not ok then e("recipe " .. id .. " makes liquid but " .. r.machineId .. " has no fluid output") end
			end
		end
		if r.fuelUnits and m and not m.usesFuel then e("recipe " .. id .. " needs fuel but machine has no fuel slot") end
	end
	if crafting < 30 then e("fewer than 30 crafting recipes") end
	local gathered = {}
	for id, n in pairs(Locations.nodes) do
		if not Items[n.item] then e("node " .. id .. " unknown item") end
		if not Locations.locations[n.at] then e("node " .. id .. " unknown location") end
		gathered[n.item] = true
		if n.unlock and n.unlock.research and not Research[n.unlock.research] then e("node " .. id .. " unknown research") end
		if n.unlock and n.unlock.quest and not Quests.main[n.unlock.quest] then e("node " .. id .. " unknown quest") end
	end
	for id, it in pairs(Items) do
		if it.type == "raw" or it.type == "fuel" then
			if not gathered[id] then e("raw item without source " .. id) end
		elseif not produced[id] then e("item never produced " .. id) end
	end
	for id, l in pairs(Locations.locations) do
		if l.unlock and l.unlock.research and not Research[l.unlock.research] then e("location " .. id .. " unknown research") end
		if l.unlock and l.unlock.quest and not Quests.main[l.unlock.quest] then e("location " .. id .. " unknown quest") end
	end
	local function checkItems(tag, items)
		for item, n in pairs(items or {}) do
			if not Items[item] then e(tag .. " unknown item " .. item) end
			if not (isInt(n) and n > 0) then e(tag .. " bad count") end
		end
	end
	local function checkObjective(tag, o)
		if o.item and not Items[o.item] then e(tag .. " unknown item") end
		if o.at and not Locations.locations[o.at] then e(tag .. " unknown location") end
		if o.visit and not Locations.locations[o.visit] then e(tag .. " unknown visit location") end
		if o.type == "research" and not Research[o.id] then e(tag .. " unknown research") end
		checkItems(tag, o.items)
		for _, item in ipairs(o.anyOf or {}) do if not Items[item] then e(tag .. " unknown anyOf item") end end
	end
	if #Quests.mainOrder < 20 then e("fewer than 20 main quests") end
	for _, id in ipairs(Quests.mainOrder) do checkObjective("quest " .. id, Quests.main[id].objective) end
	local chains = 0
	for id, c in pairs(Quests.chains) do
		chains = chains + 1
		if not Locations.locations[c.at] then e("chain " .. id .. " unknown location") end
		for _, s in ipairs(c.steps) do checkObjective("chain " .. id, s.objective) end
	end
	if chains < 8 then e("fewer than 8 npc chains") end
	if #Quests.orders < 20 then e("fewer than 20 order templates") end
	for _, o in ipairs(Quests.orders) do
		checkItems("order " .. o.id, o.items)
		if o.need and not Research[o.need] then e("order " .. o.id .. " unknown research") end
	end
	for _, p in ipairs(Quests.projects) do
		if not Items[p.item] then e("project " .. p.id .. " unknown item") end
	end
	for item, n in pairs(Config.start.items) do
		if not Items[item] or not isInt(n) then e("start item " .. item) end
	end
	for _, t in ipairs(Config.plotTiers) do
		if t.research and not Research[t.research] then e("plot tier unknown research") end
	end
	return errs
end
return Validator
