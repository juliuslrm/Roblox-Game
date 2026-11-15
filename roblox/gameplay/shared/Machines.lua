-- Placeable workshop entities: machines, storage and logistics.
-- Footprints are in grid cells (1 cell = 2 studs). Local frame: +z = front, +x = right.
-- Directions: 0 = +z (front), 1 = +x (right), 2 = -z (back), 3 = -x (left).
-- kind: machine | pump | crate | shelf | belt | turn | hopper | splitter | merger | sorter | pipe | tank | lift | gate
local M = {}
local function ports(w, d, fluidIn, fluidOut)
	local cx, cz = math.floor((w - 1) / 2), math.floor((d - 1) / 2)
	local p = { { id = "in", type = "solid", mode = "in", x = cx, z = 0, dir = 2 },
		{ id = "out", type = "solid", mode = "out", x = cx, z = d - 1, dir = 0 } }
	if fluidIn then p[#p + 1] = { id = "fin", type = "fluid", mode = "in", x = 0, z = cz, dir = 3 } end
	if fluidOut then p[#p + 1] = { id = "fout", type = "fluid", mode = "out", x = w - 1, z = cz, dir = 1 } end
	return p
end
local function machine(id, name, tier, cost, w, d, research, opt)
	opt = opt or {}
	M[id] = { id = id, name = name, kind = opt.kind or "machine", tier = tier, cost = cost, w = w, d = d,
		layer = "machine", research = research, ports = ports(w, d, opt.fluidIn, opt.fluidOut),
		usesFuel = opt.usesFuel, buildLimit = opt.buildLimit, modelAssetId = "mach_" .. id,
		category = opt.category or "machine" }
end
machine("kettle", "Braukessel", 0, 0, 2, 2, "starter_alchemy", { fluidIn = true, buildLimit = 1 })
machine("grinder", "Kräutermühle", 1, 45, 2, 2, "herbalism")
machine("saw", "Sägebank", 1, 55, 3, 2, "craftsman")
machine("crusher", "Stampfwerk", 1, 65, 2, 2, "craftsman")
machine("furnace", "Schmelzofen", 1, 110, 3, 2, "glassworks", { usesFuel = true })
machine("glassbench", "Glasbläsertisch", 1, 65, 2, 2, "glassworks")
machine("extractor", "Extraktor", 2, 170, 3, 2, "essence_craft", { fluidIn = true, fluidOut = true })
machine("bottler", "Abfüller", 2, 135, 2, 2, "essence_craft", { fluidIn = true })
machine("mixer", "Mischwerk", 2, 165, 2, 2, "fruit_mixing", { fluidIn = true, fluidOut = true })
machine("runetable", "Runentisch", 2, 250, 3, 3, "rune_study")
machine("forge", "Esse", 3, 300, 3, 3, "smithing", { usesFuel = true })
machine("enchanter", "Verzauberungspult", 3, 420, 3, 3, "enchantment", { fluidIn = true })
machine("infuser", "Infusor", 4, 600, 3, 3, "infusion")
machine("crystal_refiner", "Kristallschleifer", 4, 680, 3, 3, "crystal_mastery")
machine("advanced_cauldron", "Meisterkessel", 5, 1200, 4, 4, "arcane_depths", { fluidIn = true })
machine("herb_grower", "Kräuterbeet", 2, 210, 3, 3, "farming", { fluidIn = true })
machine("quarry_drill", "Erzbohrer", 3, 750, 3, 3, "licensed_mining", { usesFuel = true, buildLimit = 2 })
M.well_pump = { id = "well_pump", name = "Brunnenpumpe", kind = "pump", tier = 2, cost = 160, w = 2, d = 2,
	layer = "machine", research = "water_engineering", buildLimit = 4, modelAssetId = "mach_well_pump",
	category = "machine", fluid = "water",
	ports = { { id = "fout", type = "fluid", mode = "out", x = 1, z = 0, dir = 1 } } }

local function logi(id, name, kind, tier, cost, research, extra)
	local e = { id = id, name = name, kind = kind, tier = tier, cost = cost, w = 1, d = 1, layer = "belt",
		research = research, modelAssetId = "logi_" .. id, category = "transport", ports = {} }
	if extra then for k, v in pairs(extra) do e[k] = v end end
	M[id] = e
end
local IN_B = { id = "in", type = "solid", mode = "in", x = 0, z = 0, dir = 2 }
local IN_L = { id = "inl", type = "solid", mode = "in", x = 0, z = 0, dir = 3 }
local IN_R = { id = "inr", type = "solid", mode = "in", x = 0, z = 0, dir = 1 }
local OUT_F = { id = "out", type = "solid", mode = "out", x = 0, z = 0, dir = 0 }
local OUT_L = { id = "outl", type = "solid", mode = "out", x = 0, z = 0, dir = 3 }
local OUT_R = { id = "outr", type = "solid", mode = "out", x = 0, z = 0, dir = 1 }
logi("wooden_belt", "Holzförderband", "belt", 2, 4, "belt_basics", { ports = { IN_B, IN_L, IN_R, OUT_F } })
logi("belt_turn", "Bandkurve", "belt", 2, 5, "belt_basics", { ports = { IN_B, OUT_L } })
logi("input_hopper", "Entnahmetrichter", "hopper", 2, 20, "belt_basics", { ports = { OUT_F } })
logi("splitter", "Verteiler", "splitter", 2, 40, "flow_control", { ports = { IN_B, OUT_F, OUT_L, OUT_R } })
logi("merger", "Zusammenführer", "merger", 2, 40, "flow_control", { ports = { IN_B, IN_L, IN_R, OUT_F } })
logi("filter_sorter", "Filtersortierer", "sorter", 3, 90, "smart_sorting", { ports = { IN_B, OUT_F, OUT_L } })
logi("vertical_lift", "Lastenaufzug", "lift", 3, 150, "multi_floor", { ports = { IN_B, OUT_F } })
logi("magical_gate", "Magisches Tor", "gate", 5, 600, "portal_logistics", { ports = { IN_B, OUT_F }, buildLimit = 8 })
logi("pipe_straight", "Rohr", "pipe", 3, 6, "pipe_networks", { layer = "pipe", category = "transport" })
logi("pipe_bend", "Rohrbogen", "pipe", 3, 6, "pipe_networks", { layer = "pipe", category = "transport" })
M.fluid_tank = { id = "fluid_tank", name = "Flüssigkeitstank", kind = "tank", tier = 3, cost = 120, w = 2, d = 2,
	layer = "machine", research = "pipe_networks", ports = {}, capacity = 16000, modelAssetId = "logi_fluid_tank",
	category = "storage" }
M.storage_crate = { id = "storage_crate", name = "Lagerkiste", kind = "crate", tier = 0, cost = 25, w = 2, d = 2,
	layer = "machine", research = "starter_alchemy", ports = {}, slots = 30, modelAssetId = "logi_storage_crate",
	category = "storage" }
M.shop_shelf = { id = "shop_shelf", name = "Verkaufsregal", kind = "shelf", tier = 0, cost = 40, w = 3, d = 1,
	layer = "machine", research = "starter_alchemy", ports = {}, slots = 8, buildLimit = 3,
	modelAssetId = "logi_shop_shelf", category = "storage" }
return M
