-- Symbol and tile colour of every item and a motif for every production machine.
-- There are no painted item images in the project yet (Items[id].icon only holds placeholder
-- names); until there are, the UI draws a coloured tile with a symbol.  Pure data.
local I = { items = {}, machines = {} }
local function item(id, symbol, r, g, b) I.items[id] = { symbol = symbol, color = { r, g, b } } end
-- raw materials
item("herb_mint", "🌿", 111, 176, 96)
item("herb_sunleaf", "🌻", 226, 186, 72)
item("herb_moonleaf", "🍃", 108, 168, 176)
item("mushroom_gloom", "🍄", 134, 96, 160)
item("berry_red", "🍒", 196, 72, 80)
item("wood_log", "🪵", 150, 104, 68)
item("stone", "🪨", 142, 140, 136)
item("sand", "⏳", 222, 200, 150)
item("ore_copper", "🟠", 196, 122, 70)
item("ore_iron", "⚫", 110, 116, 128)
item("crystal_raw", "💎", 128, 178, 214)
item("water", "💧", 92, 156, 208)
item("seed_mint", "🌱", 132, 186, 110)
item("seed_sunleaf", "🌱", 214, 190, 96)
item("fuel_charcoal", "🔥", 74, 70, 70)
-- intermediates
item("mint_powder", "🧂", 150, 196, 140)
item("sunleaf_powder", "🧂", 230, 204, 120)
item("moon_powder", "🧂", 150, 190, 200)
item("stone_dust", "🧂", 170, 168, 164)
item("plank", "🪵", 196, 158, 110)
item("glass", "🔷", 160, 206, 226)
item("vial", "🧪", 176, 214, 230)
item("herbal_extract", "💧", 112, 176, 110)
item("solar_extract", "💧", 226, 186, 72)
item("lunar_extract", "💧", 120, 160, 200)
item("shadow_essence", "💧", 104, 84, 134)
item("berry_mash", "🍯", 190, 90, 110)
item("copper_ingot", "🧱", 204, 134, 82)
item("iron_ingot", "🧱", 138, 144, 156)
item("rune_blank", "🔶", 180, 164, 140)
item("crystal_core", "🔮", 140, 150, 220)
-- products
item("tonic_minor", "🧪", 122, 190, 130)
item("vitality_draught", "🧪", 232, 190, 84)
item("night_ink", "🧪", 96, 86, 140)
item("tonic_bottled", "🍾", 122, 190, 130)
item("berry_tonic", "🧪", 206, 96, 112)
item("potion_vigor", "🧪", 214, 132, 70)
item("dream_draught", "🧪", 150, 130, 204)
item("twin_elixir", "⚗️", 120, 180, 200)
item("elixir_master", "⚗️", 214, 170, 70)
item("charm_focus", "📿", 110, 160, 200)
item("charm_luck", "🍀", 110, 180, 110)
item("ring_warding", "💍", 200, 180, 120)
item("twilight_relic", "🏺", 130, 110, 170)
item("void_seed", "🌑", 90, 80, 120)

local function machine(id, motif) I.machines[id] = motif end
machine("kettle", "🍲") machine("grinder", "⚙️") machine("saw", "🪚") machine("crusher", "🔨")
machine("furnace", "🔥") machine("glassbench", "🔮") machine("extractor", "💧") machine("bottler", "🧪")
machine("mixer", "🌀") machine("runetable", "✨") machine("forge", "⚒️") machine("enchanter", "📖")
machine("infuser", "🧿") machine("crystal_refiner", "💎") machine("advanced_cauldron", "⚗️")
machine("herb_grower", "🌱") machine("quarry_drill", "⛏️")

function I.item(id) return I.items[id] or { symbol = "❔", color = { 150, 140, 130 } } end
function I.machine(id) return I.machines[id] or "⚙️" end
return I
