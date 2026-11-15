-- Item database. Liquids are counted in integer millilitres (unit = "ml").
local Items = {}
local function add(id, type_, name, sell, tier, extra)
	local it = { id = id, type = type_, name = name, sellBase = sell or 0, unlockTier = tier or 0,
		stackLimit = 50, rarity = "common", icon = "icon_" .. id, tags = {} }
	if extra then for k, v in pairs(extra) do it[k] = v end end
	Items[id] = it
end
local liquid = { unit = "ml", stackLimit = 20000, tags = { "liquid" } }
-- raw
add("herb_mint", "raw", "Minze", 0, 0)
add("herb_sunleaf", "raw", "Sonnenblatt", 0, 0)
add("herb_moonleaf", "raw", "Mondblatt", 0, 3, { rarity = "rare" })
add("mushroom_gloom", "raw", "Dämmerpilz", 0, 0)
add("berry_red", "raw", "Rote Beere", 0, 1)
add("wood_log", "raw", "Holzscheit", 0, 1)
add("stone", "raw", "Stein", 0, 1)
add("sand", "raw", "Sand", 0, 1)
add("ore_copper", "raw", "Kupfererz", 0, 2)
add("ore_iron", "raw", "Eisenerz", 0, 2)
add("crystal_raw", "raw", "Rohkristall", 0, 2, { rarity = "rare" })
add("water", "raw", "Wasser", 0, 0, liquid)
add("seed_mint", "raw", "Minzsaat", 0, 2)
add("seed_sunleaf", "raw", "Sonnenblattsaat", 0, 2)
add("fuel_charcoal", "fuel", "Holzkohle", 0, 1)
-- intermediates
add("plank", "intermediate", "Brett", 0, 1)
add("stone_dust", "intermediate", "Steinmehl", 0, 1)
add("mint_powder", "intermediate", "Minzpulver", 0, 1)
add("sunleaf_powder", "intermediate", "Sonnenblattpulver", 0, 1)
add("glass", "intermediate", "Glas", 0, 1)
add("vial", "intermediate", "Phiole", 0, 1)
add("herbal_extract", "intermediate", "Kräuterextrakt", 0, 2, liquid)
add("solar_extract", "intermediate", "Sonnenextrakt", 0, 2, liquid)
add("lunar_extract", "intermediate", "Mondextrakt", 0, 3, liquid)
add("shadow_essence", "intermediate", "Schattenessenz", 0, 3, liquid)
add("rune_blank", "intermediate", "Runenrohling", 0, 2)
add("copper_ingot", "intermediate", "Kupferbarren", 0, 2)
add("iron_ingot", "intermediate", "Eisenbarren", 0, 2)
add("moon_powder", "intermediate", "Mondpulver", 0, 3)
add("berry_mash", "intermediate", "Beerenmus", 0, 2)
add("crystal_core", "intermediate", "Kristallkern", 0, 4, { rarity = "rare" })
-- products (sellable)
add("tonic_minor", "product", "Kleines Tonikum", 18, 0)
add("vitality_draught", "product", "Vitaltrunk", 22, 0)
add("night_ink", "product", "Nachttinte", 28, 0)
add("tonic_bottled", "product", "Abgefülltes Tonikum", 46, 2)
add("potion_vigor", "product", "Trank der Tatkraft", 60, 2)
add("berry_tonic", "product", "Beerentonikum", 35, 2)
add("charm_luck", "product", "Glücksamulett", 92, 3, { rarity = "uncommon" })
add("ring_warding", "product", "Schutzring", 115, 3, { rarity = "uncommon" })
add("dream_draught", "product", "Traumtrunk", 110, 3, { rarity = "uncommon" })
add("twilight_relic", "product", "Zwielichtrelikt", 220, 4, { rarity = "rare" })
add("twin_elixir", "product", "Zwillingselixier", 250, 4, { rarity = "rare" })
add("charm_focus", "product", "Fokusamulett", 380, 4, { rarity = "rare" })
add("void_seed", "product", "Leerensaat", 450, 5, { rarity = "epic" })
add("elixir_master", "product", "Meisterelixier", 850, 5, { rarity = "epic" })
return Items
