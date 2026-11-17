-- Player profile: creation, (de)serialisation, schema migration and repair. Pure data, no DataStore here.
local D = require(script.Parent.Data)
local Place = require(script.Parent.PlacementService)
local Inv = require(script.Parent.InventoryService)
local Config, Items, Machines, Recipes, Research, Util = D.Config, D.Items, D.Machines, D.Recipes, D.Research, D.Util
local Profile = {}

function Profile.new(userId)
	local P = {
		schemaVersion = Config.schemaVersion, userId = userId, revision = 0,
		wallet = Config.start.coins, knowledge = 0, repPoints = 0,
		items = Util.deepCopy(Config.start.items),
		research = { starter_alchemy = true }, discoveries = {},
		quest = { main = 1, progress = 0, visited = {}, chains = {}, orders = { list = {}, serial = 0, nextRefresh = 0, repDay = 0, repToday = 0 } },
		workshop = { sizeTier = 1, floors = 1, nextUid = 1, layout = {}, buffers = {} },
		shop = { rng = (userId % 2147483000) + 17, nextIn = 12, demand = {}, demandIn = 0 },
		blueprints = {}, claims = {}, experiment = { day = 0, count = 0 },
		stats = { sold = 0, crafted = 0, coinsEarned = 0 }, settings = {}, quarantine = {},
		lastSaveUnix = 0,
	}
	Place.starter(P)
	return P
end

-- Plain data only: a deep copy is the serialised form.
function Profile.serialize(P, now)
	local out = Util.deepCopy(P)
	out.lastSaveUnix = now or 0
	return out
end

Profile.migrations = {
	-- [fromVersion] = function(data) ... return data end
}

-- Returns profile, report. Never raises on bad content; invalid parts go to `quarantine`.
function Profile.load(data, userId)
	if type(data) ~= "table" then return nil, { fatal = "not a table" } end
	local report = { fixed = {} }
	local P = Util.deepCopy(data)
	local version = P.schemaVersion
	if type(version) ~= "number" or version > Config.schemaVersion then
		return nil, { fatal = "unknown schema version" }
	end
	while version < Config.schemaVersion do
		local step = Profile.migrations[version]
		if not step then return nil, { fatal = "no migration from " .. version } end
		P = step(P)
		version = version + 1
		P.schemaVersion = version
	end
	local fresh = Profile.new(userId)
	local function note(msg) report.fixed[#report.fixed + 1] = msg end
	for key, default in pairs(fresh) do
		if type(P[key]) ~= type(default) then
			P[key] = default
			note("reset " .. key)
		end
	end
	P.userId = userId
	local function cleanInt(v, lo) return Util.isInt(v) and v >= lo end
	if not cleanInt(P.wallet, 0) then P.wallet = 0 note("wallet") end
	if not cleanInt(P.knowledge, 0) then P.knowledge = 0 note("knowledge") end
	if not cleanInt(P.repPoints, 0) then P.repPoints = 0 note("rep") end
	local function cleanStore(store, where)
		for id, n in pairs(store) do
			if not Items[id] or not cleanInt(n, 1) then
				P.quarantine[#P.quarantine + 1] = { where = where, id = tostring(id), amount = tostring(n) }
				store[id] = nil
				note("item " .. tostring(id))
			end
		end
	end
	cleanStore(P.items, "inventory")
	for id in pairs(P.research) do
		if not Research[id] then P.research[id] = nil note("research " .. tostring(id)) end
	end
	P.research.starter_alchemy = true
	local w = P.workshop
	if not (cleanInt(w.sizeTier, 1) and Config.plotTiers[w.sizeTier]) then w.sizeTier = 1 note("sizeTier") end
	if not (cleanInt(w.floors, 1) and Config.floors[w.floors]) then w.floors = 1 note("floors") end
	-- rebuild the layout entity by entity; broken entries are dropped and their contents returned
	local old, oldBuffers = w.layout, w.buffers
	w.layout, w.buffers = {}, {}
	local maxUid = 0
	for _, e in ipairs(old) do
		local ok = type(e) == "table" and type(e.uid) == "string" and Machines[e.machine] ~= nil
			and not w.buffers[e.uid]
			and Place.check(P, e.machine, e.gx, e.gz, e.floor, e.rot) == nil
		local b = type(e) == "table" and oldBuffers[e.uid] or nil
		if ok then
			if e.recipe and not (Recipes[e.recipe] and Recipes[e.recipe].machineId == e.machine) then e.recipe = nil end
			-- inlet / outlet sides: older saves have none (definition defaults apply); impossible
			-- values are dropped, never the machine
			local def = Machines[e.machine]
			if D.MachinePorts.isMachine(def) then
				if e.inSide ~= nil and not D.MachinePorts.allowed(def, e.inSide) then e.inSide = nil note("inSide " .. e.uid) end
				if e.outSide ~= nil and not D.MachinePorts.allowed(def, e.outSide) then e.outSide = nil note("outSide " .. e.uid) end
				if e.inSide ~= nil and e.inSide == (e.outSide or D.MachinePorts.DEFAULT_OUT) then
					e.inSide, e.outSide = nil, nil
					note("ports " .. e.uid)
				end
				if e.outAuto ~= nil and e.outAuto ~= false then e.outAuto = nil end
			else
				e.inSide, e.outSide, e.outAuto = nil, nil, nil
			end
			w.layout[#w.layout + 1] = e
			local nb = Place.newBuffer()
			if type(b) == "table" then
				for _, key in ipairs({ "inv", "out", "fluids", "outFluid" }) do
					if type(b[key]) == "table" then nb[key] = b[key] cleanStore(nb[key], e.uid) end
				end
				if cleanInt(b.fuel, 0) then nb.fuel = b.fuel end
				if type(b.item) == "string" and Items[b.item] then
					nb.item, nb.t = b.item, 0
					if cleanInt(b.inDir, 0) and b.inDir <= 3 then nb.inDir = b.inDir end
				end
				if type(b.job) == "table" and Recipes[b.job.recipe] and Util.isFinite(b.job.remaining) then
					nb.job = { recipe = b.job.recipe, remaining = math.max(0, b.job.remaining), auto = b.job.auto == true,
						inputs = Util.deepCopy(Recipes[b.job.recipe].inputs) }
				end
				nb.auto = b.auto == true
				nb.rr = cleanInt(b.rr, 0) and b.rr or nil
			end
			w.buffers[e.uid] = nb
			local num = tonumber(string.match(e.uid, "^m(%d+)$"))
			if num and num > maxUid then maxUid = num end
		else
			note("entity " .. tostring(type(e) == "table" and e.uid or "?"))
			if type(b) == "table" then
				P.workshop.buffers.__tmp = b
				local contents = Place.contents(P, "__tmp")
				P.workshop.buffers.__tmp = nil
				for id, n in pairs(contents) do
					if Items[id] and cleanInt(n, 1) then P.items[id] = (P.items[id] or 0) + n end
				end
			end
		end
	end
	if not cleanInt(w.nextUid, maxUid + 1) then w.nextUid = maxUid + 1 end
	if not cleanInt(P.quest.main, 1) then P.quest.main = 1 note("quest") end
	return P, report
end
return Profile
