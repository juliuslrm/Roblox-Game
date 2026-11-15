-- Global tuning values. Pure data (Lua 5.1 compatible).
return {
	schemaVersion = 1,
	cellSize = 2,                 -- studs per workshop grid cell
	floorHeight = 12,             -- studs between workshop floors
	liquidPortion = 1000,         -- ml
	start = { coins = 60, items = { herb_mint = 4, herb_sunleaf = 2, water = 3000 } },
	inventory = { slots = 24, liquidCap = 20000 },
	-- workshop size tiers: cells per side, cost, required research / quest
	plotTiers = {
		{ cells = 16, cost = 0 },
		{ cells = 24, cost = 400, research = "storage" },
		{ cells = 32, cost = 1200, research = "belt_basics" },
		{ cells = 40, cost = 3500, research = "multi_floor" },
	},
	floors = {
		{ cost = 0 },
		{ cost = 1800, research = "multi_floor" },
		{ cost = 4500, research = "crystal_mastery", quest = "q14" },
	},
	door = { width = 4, depth = 3 },          -- reserved cells at the entrance (front edge centre)
	limits = { machines = 150, logistics = 400, blueprintParts = 100, blueprintSlots = 10,
		blueprintSlotsMaster = 20, crateLimitStart = 2, layoutBytes = 200000 },
	sim = { tick = 0.25, maxDt = 1.0, maxCyclesPerTick = 4, beltSecondsPerItem = 2, hopperSecondsPerItem = 1,
		pipeMlPerSec = 500, pumpMlPerSec = 250, liftSecondsPerItem = 2, gateSecondsPerItem = 1,
		statsWindowSec = 900 },
	machine = { inputFactor = 4, outputCap = 8, fluidCap = 4000, fuelCap = 16 },
	refundFactor = 0.6,
	shop = { customerMinSec = 15, customerMaxSec = 25, queueMax = 4, demandMin = 0.85, demandMax = 1.15,
		repPriceStep = 0.04, demandDriftSec = 120 },
	reputation = { 0, 30, 100, 240, 480, 850 },   -- points needed for level 0..5
	knowledge = { firstCraft = 5, experiment = 3, experimentDailyCap = 5 },
	orders = { active = 3, refreshSec = 300, repPerOrderCapPerDay = 60 },
	rate = { default = { burst = 12, perSec = 6 }, GatherNode = { burst = 4, perSec = 2 },
		PlaceBlueprint = { burst = 2, perSec = 0.5 } },
	interactRadius = 14,
	autosaveSec = 90,
	maxPlayers = 4,
}
