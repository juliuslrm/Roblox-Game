-- Village locations and resource nodes. Positions are NOT stored here: VillageAdapter derives
-- every anchor from the generated WorldLayout (asset id of the unique building instance).
-- unlock: nil (always) | { research = id } | { quest = id } | { rep = level }
local L = { locations = {}, nodes = {} }
local function loc(id, asset, name, npc, services, unlock, extra)
	local e = { id = id, asset = asset, name = name, npc = npc, services = services, unlock = unlock,
		radius = 16, markerStyle = "service" }
	if extra then for k, v in pairs(extra) do e[k] = v end end
	L.locations[id] = e
end
loc("plaza", "fountain", "Marktplatz", "npc_herald", { "spawn", "tutorial", "project" }, nil, { radius = 30, markerStyle = "hub" })
loc("workshop_door", "house_01_timber_cottage", "Deine Werkstatt", "npc_mentor", { "workshop" }, nil, { markerStyle = "home" })
loc("town_hall", "lm_town_hall", "Rathaus", "npc_mayor", { "main_quests", "plot", "reputation" })
loc("market_hall", "lm_market_hall", "Markthalle", "npc_broker", { "orders", "research" }, nil, { interior = "market" })
loc("tavern", "lm_tavern", "Gasthaus Zum Goldenen Krug", "npc_innkeeper", { "stories", "coop" })
loc("smithy", "lm_smithy", "Schmiede", "npc_smith", { "stories", "license" })
loc("bakery", "house_05_bakery", "Bäckerei", "npc_baker", { "stories" })
loc("showcase", "house_11_stair_house", "Treppenhaus-Werkstatt", "npc_tinkerer", { "stories" }, { research = "belt_basics" })
loc("farm", "house_04_farmhouse", "Bauernhaus", "npc_farmer", { "stories", "seeds" })
loc("barn", "house_17_red_barn", "Rote Scheune", "npc_storekeeper", { "logistics" }, { research = "storage" })
loc("windmill", "lm_windmill", "Windmühle", "npc_miller", { "stories", "milling" })
loc("chapel", "lm_chapel", "Kapelle", "npc_priest", { "stories", "runes" }, { research = "rune_study" })
loc("watchtower", "lm_watchtower", "Wachturm", "npc_watchman", { "stories", "map" }, { quest = "q11" })
loc("fisher", "house_13_fisher_hut", "Fischerhütte", "npc_fisher", { "stories" })
loc("pond", "dock", "Teich und Bootssteg", nil, { "water" }, nil, { radius = 24, markerStyle = "nature" })
loc("bridge", "bridge_stone", "Steinbrücke", nil, { "water" }, nil, { markerStyle = "nature" })

-- Resource nodes: gathered by hand. offset = studs in the location's local frame
-- (x = right of the entrance, z = away from the building, i.e. towards the street).
local function node(id, item, at, ox, oz, amount, capacity, respawn, unlock)
	L.nodes[id] = { id = id, item = item, at = at, ox = ox, oz = oz, amount = amount, capacity = capacity,
		respawnSec = respawn, unlock = unlock }
end
node("n_mint_plaza", "herb_mint", "plaza", -20, 18, 2, 6, 20)
node("n_mint_door", "herb_mint", "workshop_door", 10, 6, 2, 6, 20)
node("n_mint_pond", "herb_mint", "pond", -12, 4, 3, 9, 25)
node("n_sunleaf_plaza", "herb_sunleaf", "plaza", 22, 16, 2, 6, 22)
node("n_sunleaf_bakery", "herb_sunleaf", "bakery", -9, 7, 2, 6, 22)
node("n_water_fountain", "water", "plaza", 0, 13, 1000, 6000, 6)
node("n_water_pond", "water", "pond", 0, -3, 2000, 12000, 6)
node("n_water_bridge", "water", "bridge", 0, 10, 1000, 6000, 8)
node("n_mushroom_tavern", "mushroom_gloom", "tavern", -16, 8, 1, 4, 30)
node("n_mushroom_fisher", "mushroom_gloom", "fisher", 8, 8, 1, 4, 30)
node("n_berry_farm", "berry_red", "farm", 14, 8, 2, 8, 30, { research = "craftsman" })
node("n_wood_mill", "wood_log", "windmill", 16, 10, 1, 6, 25, { research = "craftsman" })
node("n_stone_mill", "stone", "windmill", -16, 10, 2, 8, 25, { research = "craftsman" })
node("n_sand_pond", "sand", "pond", 12, 5, 2, 8, 25, { research = "craftsman" })
node("n_charcoal_smithy", "fuel_charcoal", "smithy", -12, 8, 2, 8, 30, { research = "craftsman" })
node("n_copper_tower", "ore_copper", "watchtower", 14, 6, 2, 8, 35, { quest = "q11" })
node("n_iron_tower", "ore_iron", "watchtower", -14, 6, 2, 8, 35, { quest = "q11" })
node("n_crystal_tower", "crystal_raw", "watchtower", 0, 18, 1, 4, 45, { research = "rune_study" })
node("n_crystal_chapel", "crystal_raw", "chapel", 16, 8, 1, 4, 45, { research = "rune_study" })
node("n_moonleaf_chapel", "herb_moonleaf", "chapel", -16, 8, 2, 6, 40, { research = "moonbotany" })
node("n_seed_mint_farm", "seed_mint", "farm", -12, 8, 1, 3, 60, { research = "farming" })
node("n_seed_sun_farm", "seed_sunleaf", "farm", -16, 12, 1, 3, 60, { research = "farming" })
return L
