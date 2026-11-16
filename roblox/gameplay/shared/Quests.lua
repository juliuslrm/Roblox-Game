-- Quest data. Objective types:
--   enter_workshop | craft{item,count,auto?} | sell{count} | deliver{items,at} | visit{at}
--   research{id} | place{machine} | piped{ml} | floors{count} | lines{count,windowSec} | rate{perMin,windowSec}
-- rewards: coins, knowledge, rep, flag
local Q = { main = {}, mainOrder = {}, chains = {}, orders = {}, projects = {} }
local function main(id, title, hint, objective, coins, knowledge, rep, giver)
	Q.main[id] = { id = id, title = title, dialogueKey = "main." .. id, hint = hint, objective = objective,
		rewards = { coins = coins, knowledge = knowledge, rep = rep }, giver = giver or "town_hall",
		prerequisite = Q.mainOrder[#Q.mainOrder] }
	Q.mainOrder[#Q.mainOrder + 1] = id
end
main("q01", "Deine Werkstatt wartet", "Folge dem Wegweiser „Deine Werkstatt“ und geh hinein.", { type = "enter_workshop" }, 0, 5, 0, "plaza")
main("q02", "Der erste Trank", "Braue am Kessel 1 Kleines Tonikum (2 Minze + Wasser).", { type = "craft", item = "tonic_minor", count = 1 }, 10, 8, 0, "workshop_door")
main("q03", "Ware ins Regal", "Stelle einen Trank ins Verkaufsregal und warte auf Kundschaft.", { type = "sell", count = 1 }, 15, 10, 2, "workshop_door")
main("q04", "Drei für die Markthalle", "Liefere 3 Tränke deiner Wahl in der Markthalle ab.", { type = "deliver", at = "market_hall", anyOf = { "tonic_minor", "vitality_draught", "night_ink" }, count = 3 }, 60, 15, 6)
main("q05", "Mühlenwissen", "Besuche die Windmühle, erforsche Kräuterkunde und mahle Minzpulver.", { type = "craft", item = "mint_powder", count = 2, visit = "windmill" }, 50, 25, 4)
main("q06", "Glas für Phiolen", "Erforsche Handwerk und Glashütte, schmilz Sand und blase 1 Phiole.", { type = "craft", item = "vial", count = 1 }, 80, 25, 4)
main("q07", "Bänder statt Beine", "Erforsche Förderbänder in der Markthalle.", { type = "research", id = "belt_basics" }, 100, 30, 4)
main("q08", "Die erste Kette", "Lass eine Maschine 5 Stück herstellen, die über Trichter und Band beliefert wird.", { type = "craft", count = 5, auto = true }, 120, 40, 8)
main("q09", "Wasser marsch", "Baue eine Brunnenpumpe und leite 3000 ml Wasser direkt in eine Maschine.", { type = "piped", ml = 3000 }, 140, 45, 6)
main("q10", "Tatkraft in Flaschen", "Stelle 1 Trank der Tatkraft her (Extraktor + Abfüller).", { type = "craft", item = "potion_vigor", count = 1 }, 180, 50, 8)
main("q11", "Die Schmiedelizenz", "Sprich mit dem Schmied und erforsche Schmiedekunst.", { type = "research", id = "smithing", visit = "smithy" }, 200, 55, 8)
main("q12", "Kupfer fließt", "Schmilz 1 Kupferbarren.", { type = "craft", item = "copper_ingot", count = 1 }, 220, 60, 8)
main("q13", "Runen und Glück", "Fertige 1 Glücksamulett (Runentisch + Verzauberungspult).", { type = "craft", item = "charm_luck", count = 1 }, 320, 70, 12)
main("q14", "Hoch hinaus", "Erforsche Etagenbau und kaufe im Rathaus die zweite Etage.", { type = "floors", count = 2 }, 300, 80, 12)
main("q15", "Zwei Linien", "Lass innerhalb von 3 Minuten zwei verschiedene Produkte automatisch entstehen.", { type = "lines", count = 2, windowSec = 180 }, 400, 90, 14)
main("q16", "Mondessenz", "Erforsche Mondbotanik und gewinne 1000 ml Mondextrakt.", { type = "craft", item = "lunar_extract", count = 1000 }, 450, 110, 14)
main("q17", "Kristallveredelung", "Schleife 1 Kristallkern.", { type = "craft", item = "crystal_core", count = 1 }, 500, 130, 16)
main("q18", "Stabiler Betrieb", "Erreiche 10 hergestellte Teile pro Minute, gemessen über eine volle Minute.", { type = "rate", perMin = 10, windowSec = 60 }, 600, 150, 18)
main("q19", "Die Leerensaat", "Stelle 1 Leerensaat im Meisterkessel her.", { type = "craft", item = "void_seed", count = 1 }, 800, 180, 20)
main("q20", "Das Meisterelixier", "Braue das Meisterelixier und bring es zur Dorfzeremonie ins Rathaus.", { type = "deliver", at = "town_hall", items = { elixir_master = 1 } }, 2500, 0, 60)

-- NPC story chains: 8 characters, 3 deliveries each, strictly in order.
local function chain(id, npc, at, name, steps)
	local c = { id = id, npc = npc, at = at, name = name, steps = {} }
	for i, s in ipairs(steps) do
		c.steps[i] = { id = id .. "_" .. i, title = s[1], objective = { type = "deliver", at = at, items = s[2] },
			rewards = { coins = s[3], knowledge = s[4], rep = s[5] } }
	end
	Q.chains[id] = c
end
chain("c_baker", "npc_baker", "bakery", "Die müde Bäckerin", {
	{ "Wach bleiben", { vitality_draught = 2 }, 70, 8, 6 }, { "Beerenglasur", { berry_tonic = 3 }, 180, 12, 8 },
	{ "Festtagsbrot", { potion_vigor = 4 }, 420, 18, 12 } })
chain("c_innkeeper", "npc_innkeeper", "tavern", "Der Goldene Krug", {
	{ "Hausmarke", { tonic_minor = 4 }, 110, 8, 6 }, { "Tinte fürs Gästebuch", { night_ink = 3 }, 140, 10, 8 },
	{ "Traumzimmer", { dream_draught = 3 }, 520, 20, 14 } })
chain("c_miller", "npc_miller", "windmill", "Mühlstein und Minze", {
	{ "Mahlprobe", { mint_powder = 4 }, 60, 10, 6 }, { "Bretter fürs Mühlrad", { plank = 6 }, 120, 12, 8 },
	{ "Feines Steinmehl", { stone_dust = 8 }, 200, 16, 10 } })
chain("c_farmer", "npc_farmer", "farm", "Saat und Ernte", {
	{ "Stärkung fürs Feld", { vitality_draught = 3 }, 100, 8, 6 }, { "Beerenernte", { berry_mash = 6 }, 150, 12, 8 },
	{ "Gesunde Beete", { tonic_bottled = 4 }, 320, 18, 12 } })
chain("c_smith", "npc_smith", "smithy", "Feuer und Eisen", {
	{ "Kupfer für Beschläge", { copper_ingot = 3 }, 260, 14, 10 }, { "Eisen für den Amboss", { iron_ingot = 3 }, 300, 16, 10 },
	{ "Schutz für die Wache", { ring_warding = 2 }, 520, 24, 16 } })
chain("c_fisher", "npc_fisher", "fisher", "Am Bach", {
	{ "Gegen die Kälte", { tonic_minor = 3 }, 80, 8, 6 }, { "Netzknoten", { plank = 4 }, 100, 10, 6 },
	{ "Glück beim Fang", { charm_luck = 1 }, 240, 20, 12 } })
chain("c_priest", "npc_priest", "chapel", "Licht der Kapelle", {
	{ "Runensteine", { rune_blank = 2 }, 220, 16, 10 }, { "Nachtwache", { dream_draught = 2 }, 380, 20, 12 },
	{ "Das Relikt", { twilight_relic = 1 }, 620, 30, 20 } })
chain("c_watchman", "npc_watchman", "watchtower", "Der Blick ins Tal", {
	{ "Wache halten", { potion_vigor = 2 }, 200, 12, 8 }, { "Ein klarer Kopf", { charm_focus = 1 }, 700, 28, 16 },
	{ "Zwillingswacht", { twin_elixir = 1 }, 520, 26, 16 } })

-- Repeatable order templates for the market hall board. tier = highest unlockTier of the items.
local function order(id, title, items, coinFactor, rep, need)
	Q.orders[#Q.orders + 1] = { id = id, title = title, items = items, coinFactor = coinFactor, rep = rep, need = need }
end
order("o01", "Tonikum für den Markt", { tonic_minor = 4 }, 1.25, 3)
order("o02", "Vitaltrunk für die Bäckerei", { vitality_draught = 3 }, 1.25, 3)
order("o03", "Tinte für das Rathaus", { night_ink = 3 }, 1.25, 3)
order("o04", "Gemischte Kiste", { tonic_minor = 2, vitality_draught = 2 }, 1.3, 4)
order("o05", "Minzpulver für die Küche", { mint_powder = 6 }, 9, 2, "herbalism")
order("o06", "Bretter für den Zaun", { plank = 8 }, 8, 2, "craftsman")
order("o07", "Phiolen für den Bader", { vial = 6 }, 14, 3, "glassworks")
order("o08", "Abgefülltes Tonikum", { tonic_bottled = 4 }, 1.3, 5, "essence_craft")
order("o09", "Tatkraft für die Erntehelfer", { potion_vigor = 4 }, 1.3, 6, "essence_craft")
order("o10", "Beerentonikum fürs Fest", { berry_tonic = 5 }, 1.3, 5, "fruit_mixing")
order("o11", "Kupfer für den Kesselflicker", { copper_ingot = 4 }, 40, 5, "smithing")
order("o12", "Eisenbarren", { iron_ingot = 4 }, 45, 5, "smithing")
order("o13", "Runenrohlinge", { rune_blank = 3 }, 45, 6, "rune_study")
order("o14", "Glücksbringer", { charm_luck = 3 }, 1.3, 8, "enchantment")
order("o15", "Schutzringe für die Torwache", { ring_warding = 2 }, 1.3, 8, "enchantment")
order("o16", "Traumtrunk", { dream_draught = 3 }, 1.3, 9, "moonbotany")
order("o17", "Zwielichtrelikt für die Kapelle", { twilight_relic = 1 }, 1.35, 10, "relic_weaving")
order("o18", "Zwillingselixier", { twin_elixir = 2 }, 1.35, 12, "infusion")
order("o19", "Fokusamulett für den Gelehrten", { charm_focus = 1 }, 1.35, 12, "focus_charms")
order("o20", "Großauftrag der Gilde", { potion_vigor = 6, tonic_bottled = 6 }, 1.4, 14, "commission_contracts")

-- Village projects (one per server session, shared by all players).
Q.projects = {
	{ id = "p_lanterns", title = "Laternen für die Südstraße", item = "night_ink", count = 12, rep = 20, cosmetic = "sign_lantern" },
	{ id = "p_herbbed", title = "Kräuterbeet am Brunnen", item = "vitality_draught", count = 14, rep = 20, cosmetic = "sign_herb" },
	{ id = "p_bridgeward", title = "Schutz für die Steinbrücke", item = "ring_warding", count = 6, rep = 40, cosmetic = "sign_ward" },
}
return Q
