-- Recipes. Liquid amounts are millilitres. `research` is the tech node that unlocks the recipe.
local W = 1000
local R = {}
local function add(id, tier, machine, inputs, outputs, t, research, extra)
	local r = { id = id, tier = tier, machineId = machine, inputs = inputs, outputs = outputs, durationSec = t,
		requiredResearch = research, knowledgeRewardFirstCraft = 5 }
	if extra then for k, v in pairs(extra) do r[k] = v end end
	R[id] = r
end
add("r01", 0, "kettle", { herb_mint = 2, water = W }, { tonic_minor = 1 }, 8, "starter_alchemy")
add("r02", 0, "kettle", { herb_sunleaf = 2, water = W }, { vitality_draught = 1 }, 10, "starter_alchemy")
add("r03", 0, "kettle", { mushroom_gloom = 1, herb_mint = 1, water = W }, { night_ink = 1 }, 12, "starter_alchemy")
add("r04", 1, "saw", { wood_log = 1 }, { plank = 2 }, 6, "craftsman")
add("r05", 1, "crusher", { stone = 2 }, { stone_dust = 2 }, 7, "craftsman")
add("r06", 1, "grinder", { herb_mint = 2 }, { mint_powder = 2 }, 6, "herbalism")
add("r07", 1, "grinder", { herb_sunleaf = 2 }, { sunleaf_powder = 2 }, 6, "herbalism")
add("r08", 1, "furnace", { sand = 2 }, { glass = 2 }, 12, "glassworks", { fuelUnits = 1 })
add("r09", 1, "glassbench", { glass = 1 }, { vial = 2 }, 5, "glassworks")
add("r10", 2, "extractor", { mint_powder = 1, water = W }, { herbal_extract = W }, 12, "essence_craft")
add("r11", 2, "extractor", { sunleaf_powder = 1, water = W }, { solar_extract = W }, 12, "essence_craft")
add("r12", 2, "bottler", { vial = 1, herbal_extract = W }, { tonic_bottled = 1 }, 7, "essence_craft")
add("r13", 2, "bottler", { vial = 1, solar_extract = W }, { potion_vigor = 1 }, 8, "essence_craft")
add("r14", 2, "runetable", { stone_dust = 1, crystal_raw = 1 }, { rune_blank = 1 }, 14, "rune_study")
add("r15", 2, "furnace", { ore_copper = 2 }, { copper_ingot = 1 }, 14, "smithing", { fuelUnits = 1 })
add("r16", 3, "enchanter", { copper_ingot = 1, rune_blank = 1 }, { charm_luck = 1 }, 18, "enchantment")
add("r17", 2, "furnace", { ore_iron = 2 }, { iron_ingot = 1 }, 15, "smithing", { fuelUnits = 1 })
add("r18", 3, "forge", { iron_ingot = 1, rune_blank = 1 }, { ring_warding = 1 }, 18, "enchantment", { fuelUnits = 1 })
add("r19", 3, "grinder", { herb_moonleaf = 2 }, { moon_powder = 2 }, 8, "moonbotany")
add("r20", 3, "extractor", { moon_powder = 1, water = W }, { lunar_extract = W }, 14, "moonbotany")
add("r21", 3, "bottler", { vial = 1, lunar_extract = W }, { dream_draught = 1 }, 9, "moonbotany")
add("r22", 3, "mixer", { mushroom_gloom = 1, moon_powder = 1, water = W }, { shadow_essence = W }, 15, "moonbotany")
add("r23", 4, "enchanter", { shadow_essence = W, rune_blank = 1 }, { twilight_relic = 1 }, 21, "relic_weaving")
add("r24", 2, "crusher", { berry_red = 2 }, { berry_mash = 2 }, 5, "craftsman")
add("r25", 2, "mixer", { berry_mash = 1, water = W }, { berry_tonic = 1 }, 9, "fruit_mixing")
add("r26", 4, "infuser", { potion_vigor = 1, dream_draught = 1 }, { twin_elixir = 1 }, 18, "infusion")
add("r27", 4, "crystal_refiner", { crystal_raw = 2 }, { crystal_core = 1 }, 18, "crystal_mastery")
add("r28", 4, "enchanter", { crystal_core = 1, copper_ingot = 1, rune_blank = 1 }, { charm_focus = 1 }, 24, "focus_charms")
add("r29", 5, "advanced_cauldron", { crystal_core = 1, shadow_essence = W }, { void_seed = 1 }, 30, "arcane_depths")
add("r30", 5, "advanced_cauldron", { void_seed = 1, potion_vigor = 1, dream_draught = 1 }, { elixir_master = 1 }, 36, "masterwork")
-- supply machines (not part of the 30 crafting recipes). `source` recipes need no solid input.
local S = { knowledgeRewardFirstCraft = 0, supply = true }
add("g01", 2, "herb_grower", { seed_mint = 1, water = W }, { herb_mint = 4, seed_mint = 1 }, 24, "farming", S)
add("g02", 2, "herb_grower", { seed_sunleaf = 1, water = W }, { herb_sunleaf = 4, seed_sunleaf = 1 }, 28, "farming", S)
add("d01", 3, "quarry_drill", {}, { stone = 1 }, 20, "licensed_mining", { knowledgeRewardFirstCraft = 0, supply = true, fuelUnits = 1, source = true })
add("d02", 3, "quarry_drill", {}, { ore_copper = 1 }, 30, "licensed_mining", { knowledgeRewardFirstCraft = 0, supply = true, fuelUnits = 1, source = true })
add("d03", 3, "quarry_drill", {}, { ore_iron = 1 }, 30, "licensed_mining", { knowledgeRewardFirstCraft = 0, supply = true, fuelUnits = 1, source = true })
return R
