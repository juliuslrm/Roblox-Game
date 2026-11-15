---
id: AV-RBX-001
name: Arcane Village
kind: implementation-master-spec
version: 1.0.0
language: de
status: proposed-design-not-implemented
repo: juliuslrm/Roblox-Game
base_branch: claude/roblox-village-blender-xekw0z
reference_game: Alchemy Factory (D5 Copperhead; inspiration, not source assets/code)
objective: playable original Roblox alchemy-automation game integrated with existing generated village
priority: correct-playable-systems > visual-polish > content-scale
---
# ARCANE VILLAGE — Game Design + Technical Implementation Contract

> **AN CLAUDE CODE:** Dies ist ein ausführbarer Projektauftrag und eine verbindliche Design-Spezifikation, keine Ideensammlung. Lies zuerst `docs/AI_HANDOFF.md`, `docs/ROBLOX_IMPORT.md`, `world/level_summary.md`, `blender/village/plan.py`, `roblox/VillageWorldBuilder.lua`, `default.project.json`. Verifiziere tatsächliche Dateien/Branch. Setze anschließend die unter **BUILD ORDER** beschriebenen Systeme in testbaren, integrierten Inkrementen um. Nicht nur planen oder UI-Mockups erzeugen. Was mangels Roblox Studio nicht verifiziert werden kann, klar als `UNVERIFIED_IN_STUDIO` dokumentieren. Keine fehlerfreien Tests erfinden. Fasse Fortschritt in `docs/IMPLEMENTATION_STATUS.md` nach jeder Phase zusammen. **Kontextbudget:** Beim Arbeiten nicht jedes Mal die gesamte Spezifikation laden: per Überschriftenindex (`rg "^## "`) die für die aktuelle Phase nötigen Abschnitte gezielt lesen; globale Invarianten aus §1 immer beachten.

## 0 | Ziel, Herkunft, Abgrenzung

**Elevator pitch:** Ein Spieler erbt eine winzige Alchemie-Werkstatt in einem lebendigen Fachwerkdorf. Er sammelt Kräuter, braut Tränke, verkauft im Dorf, erforscht Rezepte, baut Förderband-/Rohrnetzwerke und wächst von der Handarbeit zur intelligenten, mehrstöckigen Magiefabrik. Das Dorf ist **Wirtschaft, Tutorial, Auftragssystem, Rohstoffwelt, soziale Bühne und Progressionskarte** — keine bloße Kulisse.

**Vorbild:** Das PC-Spiel *Alchemy Factory* nutzt Crafting, Förderbänder, Flüssigkeitslogistik, Shops, Forschung, mehrstöckige Fabriken und Co-op. **Eigenständiges Roblox-Spiel** entwickeln; keine Übernahme von Originalnamen, Quests, exakten Originalrezepten/-balancing, UI, Art, Text, Audio, Marken, Code oder geschützten Assets. Projektname `Arcane Village` ist Arbeitstitel. Eigenes Dorf, eigener Weltbezug, eigene Rezepte und Mechaniken. Keine 1:1-Kopie.

**Pillars [P1–P6]:** P1 greifbare Transformation von Ressourcen; P2 echte nachvollziehbare Automatisierung mit Engpässen; P3 Dorf/NPCs haben ökonomischen Nutzen; P4 Fortschritt bedeutet neue Entscheidungen statt reine Zahlen; P5 zugänglich am Handy, anspruchsvoll für Optimierer; P6 Solo vollständig, Co-op optional.

**Ergebnis/Definition Done:** Von Spawn bis späte Forschung ist eine echte durchspielbare Schleife vorhanden: sammeln → herstellen → transportieren → lagern → verkaufen → freischalten → bauen → automatisieren → verbessern → speichern → wieder aufnehmen. Alle essentiellen Systeme real funktional. Keine Dummy-Buttons, leeren Endgame-Menüs oder nur animierten Deko-Förderbänder.

## 1 | IST-ZUSTAND: bestehende Welt verbindlich erhalten

Repository `juliuslrm/Roblox-Game`, Ausgangsbranch `claude/roblox-village-blender-xekw0z` (aktuellen Zustand prüfen; neuen Feature-Branch vom geprüften Stand anlegen). Bisher: 91 wiederverwendbare Assets (18 Häuser, 7 Landmarks, 33 Natur, 33 Props); 50 Weltmeshes; 1.889 Instanzen; ~602k Dreiecke (340k Natur); 768×768 Studs; 25 platzierte Gebäude; 11 Straßen. Blender/bpy generiert Gebäude und Welt; Roblox-Importer/Builder existieren, aber **noch nicht real in Studio getestet**. Gebäude sind Außenhüllen, nicht begehbar. 34 bestehende Prüfungen bestanden laut Übergabe, NICHT gleichbedeutend mit echtem Studio-Test.

**Invarianten:**
- Blender `(x,y,z)` → Roblox `(x,z,-y)`; 1 Blender unit = 1 Stud; Blender Z-Yaw = Roblox Y-Yaw; Modellvorderseite Blender −Y / Roblox +Z.
- Palette `exports/textures/village_palette.png`; `palette.COLORS` nie umsortieren, nur erweitern. Kein beliebiges Überschreiben von exportierten `.glb`, `.blend`, `world/world_layout.json`, `roblox/WorldLayout.lua`, `roblox/WorldHeightmap.lua`: editierbare Python-Quellen ändern, neu generieren.
- `blender/village/plan.py` enthält `ROADS`, `ALONG`, `SITES`, Platzierung; `VillageWorldBuilder.lua` baut Instanzen. Welt- und Spielsysteme **entkoppelt**; Builder darf auch ohne Gameplay funktionieren. Existing Builder + Lua-5.1-kompatible Module nicht beiläufig brechen (keine Typannotationen/`continue`/`+=` in diesen kompatiblen Modulen).
- Erst **Adapter** bauen statt großer Terrain-/Asset-Rewrites. Bestehende 25 Gebäude mit ihren Positionen erhalten; funktionale Rollen über Registry und Interaktionsanker daran hängen.
- Noch offen: tatsächlicher Import, Name/Größe/Textur, Studio-Luau, CollisionFidelity, Mobile-Performance. Keine Funktionalität als „fertig in Studio“ deklarieren, die nur mit Mock lief.

## 2 | Spielerfahrung (minutengenau + langfristig)

**Onboarding 0–2 min:** Spawn auf Dorfplatz; deutlich sichtbarer Auftrag „Deine Werkstatt wartet“. Wegmarker zum kleinen Werkstatteingang; NPC gibt 60 Münzen + Basiswerkzeuge; mit ProximityPrompt/E-Taste/Touch betreten; Tutorial führt zu Tisch, Kräuterkiste, Wasserquelle, Kessel. Braue 1 `tonic_minor` (2 Minze + 1 Wasser), stelle es ins Verkaufsregal und verkaufe an ersten Kunden. Keine unausweichliche Zwischensequenz.

**2–10 min:** Weitere Kräuter sammeln; 3 Basisrezepte lernen; Verkaufsregal bestücken; 1 NPC-Auftrag; Handwerk + erste zusätzliche Mühle. Spieler sieht, was produziert, was verbraucht und warum eine Maschine wartet. Erste 3 Freischaltungen garantiert erreichbar ohne Idle-Grind.

**10–30 min:** Förderband + Kiste + 1 Verarbeiter + 1 Trankfüller. Bauen auf Raster, Maschinenport verbinden, erste echte automatische Kette. Auftrag zeigt Durchsatz-Mangel. Werkstatt erweitern; neue Quellen am Bach/Mühlenweg nutzen.

**30–90 min:** Farmbeet + Wasserpumpe + Destillation + Flüssigkeitsrohre + Sortierer; 2 parallele Fertigungslinien, Kassenautomatisierung, seltene Rezeptfreischaltung. Dorfaufträge und Ruf statt reines „größerer Preis“.

**Mehrere Sessions:** Forschungspfade, Legierungs-/Runenprodukte, mehrere Stockwerke, modulare Blueprints, spezialisierte Distrikte, größere Aufträge, Produktionsstatistik, effizientere Logistik, hochwertige Dekoration, kosmetische Prestigeprojekte. Kein harter Story-Endpunkt; nach Endgame Verbesserung und kreative Fabrikgestaltung.

**Emotionale Ziele:** Anfang: „Ich kann einen Trank brauen.“ Mitte: „Meine Maschinen arbeiten selbst.“ Spät: „Ich habe eine elegante Fabrik gebaut und das Dorf lebt von meinem Betrieb.“

## 3 | Dorf wird Spielsystem: Karte, Orte, Ziele

Die weltweiten Koordinaten in `world/level_summary.md` sind Referenz, **nicht** hier noch einmal hart codieren. Map-Integrationskonfiguration soll `assetId` + deterministische `instance.id`/`name` nutzen; beim Build aus aktuellem Layout Position/Pivot ableiten, statt Copy-Paste-Koordinaten. Wenn der vorhandene Welt-Build neu generiert wird, müssen Anker dadurch mitwandern. Nur nach Platzierungs-/Pfadprüfung neue Plätze hinzufügen.

| Bestehender Ort/Asset | Gameplay-Funktion | Freischaltung/Interaction |
|---|---|---|
| Marktplatz (0,0) + Brunnen | Spawn, Tutorial, Verkaufsfläche, Wegweiser; öffentlicher Quest-Hub | sofort |
| Rathaus `lm_town_hall` | Rufstufen, Baukonzession, Grundstücksrechte, Hauptquests | früh |
| Markthalle `lm_market_hall` | Bestellungen, Sonderaufträge, lokale Nachfrage, wöchentliche Ziele | sofort |
| Gasthaus `lm_tavern` | NPC-Kundengeschichten, optionale Quests, Social/Co-op-Match | früh |
| Schmiede `lm_smithy` | Metallverarbeitung, Geräte-/Werkzeugpläne, Reparaturdesign | T2 |
| Bäckerei `house_05_bakery` | Konsumentenbedarf (Vitaltränke), kleinere Lieferaufträge | T1 |
| Fachwerkhaus am Markt `house_01_timber_cottage` | Einführung in eigenes Werkstattportal / sichtbare Fassade | sofort |
| Treppenhaus-Werkstatt `house_11_stair_house` | Fortschrittsshowcase für Maschinen, spätere Fachquests | T2 |
| Bauernhaus `house_04_farmhouse` | Kräuteranbau, Saatgut, Dünger und automatische Gewächshäuser | T1 |
| Rote Scheune `house_17_red_barn` | Lagertechnik, Logistik, Großaufträge | T2 |
| Windmühle `lm_windmill` | Holz/Getreide-/Pulver-Verarbeitung, Mühlenwissen, Förderbandpläne | T1 |
| Kapelle `lm_chapel` | seltene Essenzen, Alchemie-Wissen, Runenbaum | T3 |
| Wachturm `lm_watchtower` | Kartensicht, Erkundungsquests, neue Sammelgebiete | T2 |
| Fischerhütte `house_13_fisher_hut` | Wasser-/Bach-Quests, Pipeline-Bau | T2 |
| Teich/Bach und Brücke | Ressource Wasser, technische Pumpen, Umgebungsatmosphäre | sofort/T2 |
| Dorftore/Straßen | Kapitel-Wegeführung, später Karren-Lieferlogistik | T3 |
| restliche Wohnhäuser | NPC-Häuser, Ruf-Anfragen, sichtbare Dorfbevölkerung | phasenweise |

**Interaktion:** `LocationRegistry` definiert `locationId`, `anchor`, `npcId`, `services`, `radius`, `markerStyle`, `unlockRule`, `interiorScene`. Server prüft Nähe/Unlock bei jedem Besuch, Kauf, Quest und Interaktions-Remote. Einfache `ProximityPrompt` + Touch-Button; keine unsichtbare Interaktion über die gesamte Map.

**Achtung Außenhüllen:** Gebäude derzeit ohne Innenraum! **Nicht** durch geschlossenes Mesh laufen lassen. Für v1: Beim Eingang eine Portaltür/Interaktionszone auf Gehweg-/Außenfassadenposition setzen; beim Betreten an eine **separate begehbare Werkstatt-Inneninstanz** teleportieren (innerhalb desselben Places in isolierter Region, nicht zwangsläufig Roblox TeleportService). Außenkörper unverändert, Innenraum eigenständig via Blender/Roblox-Part-Baukasten. Für Servicegebäude v1 vorerst Außenstation/NPC am Eingang statt falschem Innenraumversprechen. Mindestens Spielerwerkstatt und Markt-Innenraum als echte separate Räume; später stufenweise vollständige Innenräume. Beim Rückweg wieder zum korrekten Eingang/Spawn; respawn/failure fallback. Kollisionskörper um Portale herum so anpassen, dass kein Spieler eingesperrt wird.

**Weltplatzierung/Griefing:** Dorf ist gemeinsamer, **nicht frei bebaubarer** Hub; freie Maschinen sind ausschließlich in privat reservierten Werkstattzonen platzierbar. Dorf-Deko bleibt unzerstörbar. Keine unautorisierten Änderungen an Welt anderer Spieler.

## 4 | Server-, Instanz- und Co-op-Modell

**V1:** 1 gemeinsames Dorf/Server, Ziel 4 aktive Spieler (später skalierbar); jeder Spieler sieht seine eigene Werkstatt. Individuelle Werkstatt-Innenräume als isolierte Build-Zonen in derselben Roblox-Place-Session (Koordinaten werden dynamisch vom Server zugeteilt, außerhalb der sichtbaren Dorfkulisse; keine festen magic offsets in Clientcode). Distanz, Streaming und Licht/Skybox so gestalten, dass andere Taschenräume nicht sichtbar sind. Eigenes `WorkshopInstanceService` weist Interior-Slot zu, führt sichere Teleportation, bindet `ownerUserId`, lädt/entlädt Instanz. Co-op **nicht** voraussetzen: Solo kann alles schaffen.

**Co-op Phase 2:** Besitzer kann Mitspieler als Besucher oder Editor einladen. Rechte `visitor < operator < builder < owner`; Besucher schaut zu, Operator bedient Maschinen, Builder baut, Owner verwaltet Rechte/Verkauf/Forschung. Owner offline = kein persistent gehosteter Betrieb in v1; Friend-Join nur auf laufender Session. Berechtigungen serverseitig; Spielwirtschaft und Fortschritt gehören Owner; keine gemeinsamen Duplizierungs-/Trade-Loops. Bei Host-Leave Session schließen, Änderungen speichern, Besucher sicher zurück in Hub; kein automatischer Owner-Transfer.

**Keine Echtzeit-Persistenz ohne Host:** Außerhalb laufender Server keine Fabriksimulation. Optional spätere, streng begrenzte Offline-Erträge nur als klar definiertes Feature; **nicht** im ersten Release. Komplette Fabrik wird beim Login aus Daten rekonstruiert.

## 5 | Ressourcen und Rezeptsystem: vollständige Datenbasis v1

**Inventar-Regeln:** Alle Gegenstände haben stabile `itemId`, `type` (`raw|intermediate|product|fuel|equipment`), `stackLimit`, `icon`, `rarity`, `sellBase`, `tags`, `unlockTier`, optional `unit`. Keine UI-Strings als Daten-IDs. Feststoffe als ganzzahlige Stücke, Flüssigkeit in **ganzzahligen ml**; Standardportion = 1000 ml. Flüssigkeits-IDs `water`, `herbal_extract`, `solar_extract`, `lunar_extract`, `shadow_essence`; in Rezepttabellen steht für diese IDs immer die tatsächliche ml-Menge, **niemals** eine Stückzahl. Kein clientseitiger Item-Mint. Verarbeitete Produkte separat von Rohstoffen; Rezepte konsumieren Inputs **atomar** erst beim erfolgreichen Jobstart und schreiben Outputs atomar bei Jobende; Ausgabe blockiert bei vollem Zielpuffer.

**Rohstoffe v1:** `herb_mint`, `herb_sunleaf`, `herb_moonleaf`, `mushroom_gloom`, `berry_red`, `wood_log`, `stone`, `sand`, `ore_copper`, `ore_iron`, `crystal_raw`, `water` (ml), `seed_mint`, `seed_sunleaf`, `fuel_charcoal`. Start: 60 coins, 4 `herb_mint`, 2 `herb_sunleaf`, 3000 ml water, 2 slots free in inventory. Mengen sind **Designvorschläge**, per Config balancierbar.

**Mindest-Spielbalance:** 30 Rezepte in vier Wertschöpfungsstufen; `t` = Basisverarbeitungszeit bei Effizienz 1, `n` feste Stückzahl, `W` = 1000 ml Wasser. Bei leerem Treibstoff-/Wassertank wird keine Produktion gestartet. `-` bedeutet keinen Input, *nicht* Gratisproduktion. Die Preise unten sind anfängliche Testwerte, keine Behauptung über das Vorbild.

| id | tier | machine | input | output | t(s) |
|---|---:|---|---|---|---:|
| r01 | 0 | kettle | herb_mint:2,water:W | tonic_minor:1 | 8 |
| r02 | 0 | kettle | herb_sunleaf:2,water:W | vitality_draught:1 | 10 |
| r03 | 0 | kettle | mushroom_gloom:1,herb_mint:1,water:W | night_ink:1 | 12 |
| r04 | 1 | saw | wood_log:1 | plank:2 | 6 |
| r05 | 1 | crusher | stone:2 | stone_dust:2 | 7 |
| r06 | 1 | grinder | herb_mint:2 | mint_powder:2 | 6 |
| r07 | 1 | grinder | herb_sunleaf:2 | sunleaf_powder:2 | 6 |
| r08 | 1 | furnace | sand:2 | glass:2 | 12 |
| r09 | 1 | glassbench | glass:1 | vial:2 | 5 |
| r10 | 2 | extractor | mint_powder:1,water:W | herbal_extract:W | 12 |
| r11 | 2 | extractor | sunleaf_powder:1,water:W | solar_extract:W | 12 |
| r12 | 2 | bottler | vial:1,herbal_extract:W | tonic_bottled:1 | 7 |
| r13 | 2 | bottler | vial:1,solar_extract:W | potion_vigor:1 | 8 |
| r14 | 2 | runetable | stone_dust:1,crystal_raw:1 | rune_blank:1 | 14 |
| r15 | 2 | furnace | ore_copper:2 | copper_ingot:1 | 14 |
| r16 | 3 | enchanter | copper_ingot:1,rune_blank:1 | charm_luck:1 | 18 |
| r17 | 2 | furnace | ore_iron:2 | iron_ingot:1 | 15 |
| r18 | 3 | forge | iron_ingot:1,rune_blank:1 | ring_warding:1 | 18 |
| r19 | 3 | grinder | herb_moonleaf:2 | moon_powder:2 | 8 |
| r20 | 3 | extractor | moon_powder:1,water:W | lunar_extract:W | 14 |
| r21 | 3 | bottler | vial:1,lunar_extract:W | dream_draught:1 | 9 |
| r22 | 3 | mixer | mushroom_gloom:1,moon_powder:1,water:W | shadow_essence:W | 15 |
| r23 | 4 | enchanter | shadow_essence:W,rune_blank:1 | twilight_relic:1 | 21 |
| r24 | 2 | crusher | berry_red:2 | berry_mash:2 | 5 |
| r25 | 2 | mixer | berry_mash:1,water:W | berry_tonic:1 | 9 |
| r26 | 4 | infuser | potion_vigor:1,dream_draught:1 | twin_elixir:1 | 18 |
| r27 | 4 | crystal_refiner | crystal_raw:2 | crystal_core:1 | 18 |
| r28 | 4 | enchanter | crystal_core:1,copper_ingot:1,rune_blank:1 | charm_focus:1 | 24 |
| r29 | 5 | advanced_cauldron | crystal_core:1,shadow_essence:W | void_seed:1 | 30 |
| r30 | 5 | advanced_cauldron | void_seed:1,potion_vigor:1,dream_draught:1 | elixir_master:1 | 36 |

**Verkaufbare Produkte + Basisverkaufswerte (Coins pro Einheit):** `tonic_minor:18`, `vitality_draught:22`, `night_ink:28`, `tonic_bottled:46`, `potion_vigor:60`, `berry_tonic:35`, `charm_luck:92`, `ring_warding:115`, `dream_draught:110`, `twilight_relic:220`, `twin_elixir:250`, `charm_focus:380`, `void_seed:450`, `elixir_master:850`. Alle anderen Inputs **nicht direkt an Shopkunden verkaufbar** v1. Rarer Einsatz muss wirtschaftlich sinnvoll sein: Preis/Produktionsdauer/Rohstoff-Knappheit anhand Simulator-Balance-Tests prüfen. Keine Buy-Resell-Arbitrage.

**Rezept-Datenschema:** `{id,tier,machineId,inputs:{itemId:integer},outputs:{itemId:integer},durationSec,requiredResearch?,fuelUnits?,heatUnits?,knowledgeRewardFirstCraft?}`. Alle Rezepte müssen vollständig referentiell gültig sein; keine Zyklen ohne durch Rohstoffquellen gedeckten Input; Maschinen unterstützen mehrere Rezepte, UI zeigt kompatible.

**Rohstoff-Gewinnung:**
- Weltressourcen in Spawnnähe: Kräuter am Dorf-/Bachrand, Holz am Mühlenweg, Stein am Außenrand. Seltene Moonleaf/Crystals erst in freigeschalteten Zonen. Sammelobjekte serververwaltet (`nodeId`, remaining, cooldown, capacity, respawnAt); visueller Zustand repliziert, nicht lokal entschieden.
- Optionales Skill-/Timing-Minispiel **nur Bonus**, keine Pflicht. Auf Mobile ein Tap/Hold. Ressourcenknoten regenerieren, fair bei mehreren Spielern; niemals globale tägliche harte Blockade im Kernspiel.
- Automatische Versorgung später: `herb_grower` (Saatgut + Wasser -> Kräuter; definierte Laufzeit) und `well_pump` (Wasser mit Rate, Kapazitätslimit, Kosten/Bauplatz) sowie `quarry_drill` (Stein/Erz aus lizenzierter Quelle, langsame Rate). Kein kostenloser unendlicher High-Tier-Strom; Upkeep/Rate begrenzen.
- Zuerst Weltknoten als einfache Roblox-Parts/VFX mit korrekten ProximityPrompts, später Blender-Assets. Wiederholbare Ernte-Balance 3–5 min Startspiel ohne Softlock.

## 6 | Maschinen, Ports, Energie, Kapazität

**Werkstatt-Grid:** Rasterabstand 2 Studs, Rotationen 0/90/180/270°, definierte lokale Footprints in Grid-Zellen, eigene Layer: `floor`, `machine`, `belt`, `pipe`, `decoration`, `wall` (je nach Regel kollisionskompatibel). Startboden 32×32 Studs; später 48×48, 64×64 und 80×80; mehrstöckig ab T3 (Floorhöhe 12 Studs). Keine Überlappung von begehbaren Korridoren, Tür, Treppe, Ausgang oder Fluchtbereich. Erlaubte Produktion **nur** im eigenen Workshop. Entfernen erst nach vollständiger Rückgabe von nicht verbrauchten Items/bei sicherem Buffer-Handling.

**Maschinenschema:** `machineId,displayName,tier,cost,footprint:{x,z},allowedRecipes,ports:[{id,type:solid|fluid|fuel|power,direction,mode:in|out,capacity}],inputSlots,outputSlots,bufferCapacity,cyclesPerSec?,buildLimit?,modelAssetId,collisionProxy`. Maschinen-Instanzen: `instanceId,ownerId,machineId,gridPos,rotation,recipeId,jobProgress,inputBuffer,outputBuffer,heat,mode,priority`. Stabile IDs; keine im UI benutzten anzeigbaren Namen als Schlüssel.

| Maschine | T | Kosten | Raster (Studs) | Gameplay |
|---|---:|---:|---|---|
| `kettle` | 0 | starter/free | 4×4 | Handbrauen, optional nachfüllbarer Brennstoff |
| `grinder` | 1 | 45 | 4×4 | Kräuter zu Pulver |
| `saw` | 1 | 55 | 6×4 | Holz zu Brettern |
| `crusher` | 1 | 65 | 4×4 | Stein / Beeren verarbeiten |
| `furnace` | 1 | 110 | 6×4 | Glas / Metalle, verbraucht Fuel |
| `glassbench` | 1 | 65 | 4×4 | Glasgefäße |
| `extractor` | 2 | 170 | 6×4 | Extraktion, flüssiger Input |
| `bottler` | 2 | 135 | 4×4 | Abfüllung |
| `mixer` | 2 | 165 | 4×4 | Essenzmischung |
| `runetable` | 2 | 250 | 6×6 | Runenträger |
| `forge` | 3 | 300 | 6×6 | Ringe |
| `enchanter` | 3 | 420 | 6×6 | Verzauberung |
| `infuser` | 4 | 600 | 6×6 | Trankfusion |
| `crystal_refiner` | 4 | 680 | 6×6 | Kristallkern |
| `advanced_cauldron` | 5 | 1200 | 8×8 | Endgameprodukte |
| `herb_grower` | 2 | 210 | 6×6 | Automatischer Kräuteranbau |
| `well_pump` | 2 | 160 | 4×4 | Wasserquelle nur im erlaubten Slot |
| `quarry_drill` | 3 | 750 | 6×6 | Langsame Erzgewinnung, Lizenz nötig |

**Initiale Handwerkstische:** Der Spieler beginnt mit `kettle`, einer Startkiste, Regal, Hand-Interaktion (Rezept auswählen, Zutaten in UI, Craft bestätigen); andere Geräte erst nach Forschung und bezahltem Platzieren. Machine-Preis = Coins-Sink, keine kostenlosen Sofort-Rückerstattungen über Place/Remove-Exploit. Verkauf/Abbau: 60% Kaufpreis rückgeben, nur bei leeren Buffern, mit Bestätigungsdialog für riskante Aktionen.

**State Machine:** `Idle` → `WaitingForInputs` → `Running` → `OutputBlocked` → `Idle`; auch `NoFuel`, `NoPower`, `Paused`, `InvalidRecipe`. `Running` darf nur mit ausreichenden, vollständig reservierten Inputs beginnen. Tick verhält sich unabhängig von FPS: `remainingTime -= dt`, mehrere abgeschlossene Zyklen mit **festem upper bound** pro Tick nachholen, um Server-Spikes zu verhindern. Durchsatz `60/durationSec * efficiency * min(inputSupply/outputFlow)` in Einheiten/min; nicht ungedeckten Wert versprechen. UI zeigt deterministisch warum blockiert.

**Energie/Fuel:** V1 mit diskreten Brennstoffeinheiten (`fuel_charcoal` etc.) und `heatBudget`, nicht komplexes Stromnetz. Fuelverbrauch je Rezept in RecipeConfig; UI prognostiziert noch mögliche Zyklen. Energie-/Wartungssystem kann nach T4 separat ergänzt werden, darf Startspieler nicht blockieren.

**QoL:** Maschinen kopieren (Rezept+Rotation, nur eigene Freischaltung); Tab mit Liste der Inputs/Outputs; Warnsignal bei Stall; klare grüne/orange/rote Indikatoren **plus Text/Icons** (nicht Farbe allein). Output-Entnahme und UI-Update serverbestätigt.

## 7 | Logistik: echte funktionierende Automatisierung

**Transportdaten ≠ physische Einzelteile:** Ein Transport-Token ist ein serverseitiger Datensatz in einem gerichteten Graphen; clientseitig sichtbare Ware ist nur gepoolte Animation. Niemals tausende unanchored, kollidierende Parts für einzelne Items simulieren. Knoten: Maschine, Kiste, BeltSegment, Splitter, Merger, Sorter, Pump, Pipe, Shelf, Seller. Kanten durch geometrisch benachbarte, kompatible Ports in gleicher Höhe + Orientierung. Rotation transformiert Ports. Graph nach Bauen/Entfernen lokal neu verbinden; Zyklen sicher behandeln.

**Netzwerk:** Solid graph und fluid graph getrennt. Mengen werden atomar zwischen Puffern übertragen, nur wenn (a) Output vorhanden, (b) downstream Platz vorhanden, (c) Porttyp und erlaubte Items passen, (d) throughput/tick nicht überschritten. Eingangspriorität konfigurierbar; deterministische Fairness: Round-Robin bei konkurrierenden Kanten; kein unendliches Re-Tick-Loop / Duplizieren. Flüssigkeiten als integer ml. Flüssigkeit soll beim Übergang nicht aus einem anderen Fluid aus Versehen hergestellt werden; bei Mehrflüssigkeitsrohr später kontaminationssichere Typisierung.

| Infrastruktur | T | Funktion |
|---|---:|---|
| `wooden_belt` | 2 | 1 gerader 2-Stud-Segment, 1 Item / 2 sec |
| `belt_turn` | 2 | 90°-Segment |
| `input_hopper` | 2 | Übergabe Container→Band |
| `storage_crate` | 0 | Lager mit 30 Slots, einfache Stapelgrenzen |
| `splitter` | 2 | verteilt im Round-Robin |
| `merger` | 2 | vereinigt Eingänge ohne Verlust |
| `filter_sorter` | 3 | Zielroute nach Item-Whitelist |
| `pipe_straight`,`pipe_bend` | 3 | Flüssigkeitsnetz, begrenzt ml/sec |
| `fluid_tank` | 3 | Flüssigkeitspuffer, max Kapazität |
| `vertical_lift` | 3 | Etagenwechsel mit Rate/Porthöhe |
| `magical_gate` | 5 | Paarweises Teleportieren zwischen genehmigten Endpunkten, Energie/Rate-Limit |

**Betriebsbeispiel M2:** `storage_crate(herb_mint)` → `input_hopper` → `grinder(r06)` → `wooden_belt` → `extractor(r10)` + `well_pump` / Wasser → `bottler(r12)` + `vial` → `storage_crate(products)` → `shop_shelf`. Im Spiel visuell nachvollziehbar, kann ohne Handtransfer laufen. Keine magische Übergabe, wenn physischer Anschluss fehlt.

**Simulationstakt:** Produktionsnetz auf Server mit diskreter 0,2–0,5s-Tickbasis, Animation separat clientseitig. Beschränke pro Workshop Nodes/Links/Transfers je Tick; Dirty-graph-Update nur bei Topologieänderung; statische Bewegungen über parametrisierte Tween-/Interpolation. Fehlt nahe Spielerinteraktion, nur aggregierte Zustandssnapshots schicken. Wenn Rate gegen Performance verstößt, messbar reduzieren; logische Korrektheit vor jeder visuellen Animation.

**Baumenü:** selektiere Asset → Ghost auf Grid per Raycast → Snap+Rotation → serverseitige `Place`-Validierung → Confirm; Desktop: Maus/R-Taste/ESC, Mobile: Drag/Rotate/✓/X, Controller optional später. Zeige Ein-/Ausgangsport in Ghost. Neben bestehender Maschine muss Connect-Vorschau sichtbar sein. Rot/gesperrt bei falschem Grundstück/Overlap/kein Geld/Locked.

## 8 | Verkauf, Kunden, Ruf, Aufträge

**Shop v1:** In Werkstatt gibt es ein Regal, das nur durch echte Itemtransfers (Hand oder Belt/Storage) Ware erhält. Kunden kaufen nur Produkte aus Regal-Inventar; kein Verkauf unsichtbar erzeugter Items. Start mit Regal + Handkasse; später automatische Kasse + Lieferung vom Workshop zu Markthalle. `ShopService` verwaltet `stock`, `supply`, `demand`, `customerQueue`, `priceMultiplier`, `saleLedger`. Kauf atomar: stock−qty + wallet+coins + quest progress + stats in derselben serverseitigen Transaktion; bei Fehler null Änderung.

**Kundenlogik:** NPCs als stromsparende, sichtbare Repräsentationen; serverseitiger Käuferwunsch und Kaufentscheidung. Zu Beginn ~1 Kunde/15–25 s, Warteschlange max 4; Kauf 1–2 Stück, Produkte nach Freischaltung und Nachfrage gewichten. Kunde geht wieder, wenn nichts vorhanden; v1 ohne harte negative Strafen. Später bessere Regale/Kassen/Ruf erhöhen Sichtbarkeit, Nachfrage und max Durchsatz. NPCs durch sichtbaren Weg zum Regal, aber Fallback bei gestörter Navigation: Bestellung nicht doppelt abschließen; maximal 4 aktive NPC-Visuals. Hub-NPCs nicht für alle privaten Fabrikverkäufe einzeln durch Dorf navigieren lassen.

**Preisformel (Vorschlag):** `finalPrice = floor(baseSell * demandFactor * reputationFactor)`; `demandFactor ∈ [0.85,1.15]`, `reputationFactor = 1 + 0.04*repLevel` (repLevel 0..5), round integer. Multiplier öffentlich im UI sichtbar. Verkaufspreis unterliegt Limits, keine stündlichen wild schwankenden Werte; Offline keine spekulativen Kursgewinne.

**Ruf 0–5:** Auftrag/erste Verkäufe geben Rufpunkte, notwendige Punkte: `[0, 30, 100, 240, 480, 850]`. Ruf öffnet Dorfdienste, Kundenarten, kosmetische Schilder, neue Markthallenaufträge; Forschung selbst bleibt vorrangig an Skill/Tier gebunden. Wiederholbare Quests nicht unbegrenzt für Ruf farmbar.

**Eigenständiger Dorf-Kniff – Gildenversorgung:** Das Dorf profitiert sichtbar von Lieferungen statt nur als Preis-UI zu dienen. In jeder Session gibt es 1 optionales kollektives Dorfprojekt (z.B. Laternen mit `night_ink`, Kräuterbeet mit `vitality_draught`, Brückenschutz mit `ring_warding`): bis zu 4 Spieler liefern echte Waren, ein serverseitiger Fortschrittszähler nimmt jede Spende genau einmal an, alle Beitragsleistenden bekommen bei Abschluss begrenzte Ruf-/Kosmetikbelohnungen. Weltweites Deko-Upgrade gilt **nur für diese laufende Server-Session**, nicht irreführend als persistente globale Welt; persönlicher Fortschritt/Claim wird gespeichert. Kein Pflicht-Gate für Solo, im Einspielerfall auch allein abschließbar. In v1 zunächst 3 Projektvorlagen, später 12+.

**Aufträge:** öffentliche Tafel am Markt. Main Quest (einmalig, progressionsentscheidend), NPC-Order (Liefermenge/frische Produktionsketten), optionale Erkundung/Produktion/Design. Auftrag kann nur mit **wirklich vorhandener Menge** abgegeben werden; Items werden atomar entnommen, Belohnung genau einmal ausgezahlt. Ein Auftrag mit `id`, `owner`, `requirements`, `rewards`, `expiresAt?`, `status`, `claimedAt`. Keine Quest, deren Zutaten hinter derselben Quest gesperrt sind. Lieferscheine ersetzen keine realen Items.

**Beispiel Main-Quest-Reihe (alle als Daten, nicht festes UI):**
`q01` Werkstatt betreten → `q02` 1 tonic_minor → `q03` Regal verkaufen → `q04` 3 Standardtränke abliefern → `q05` Mühle besuchen + Pulver herstellen → `q06` 1 Glasfläschchen → `q07` Förderband freischalten → `q08` automatisierte 5 Stück produzieren → `q09` Wasserpumpe verbinden → `q10` Potion Vigor → `q11` Schmiedelizenz → `q12` Kupferbarren → `q13` Runenprodukt → `q14` Mehr-Etagen-Workshop → `q15` 2 Produktlinien gleichzeitig → `q16` seltene Mondessenz → `q17` Kristallveredelung → `q18` 10/min stabile Produktion (zeitlich gemessen, nicht Klick) → `q19` Void Seed → `q20` Master-Elixier + Dorfzeremonie`. Jede Quest spezifiziert unlocks, prerequisites, counts, dialogueKey, objectiveTracker. Mindestens 20 Hauptquests, 20 wiederholbare Auftragsvorlagen, 8 Charakter-Auftragsstränge zum v1-Finish.

**Anti-Exploit Shop:** Kunde zahlt nur aus Server-Stocks; Auftrag und Sale dürfen denselben Itembestand niemals gleichzeitig abziehen. Ledger mit deduplizierbarem `transactionId`/Idempotenzkey; Verkaufsergebnisse nicht von Client signieren lassen.

## 9 | Forschung, Gerätefreischaltung, Fortschritt

**Ressourcen:** `Coins` (Bauen/Kaufen/Lizenzen), `Knowledge` (erstmalige Produkte, Main-Quest, Experimente, begrenzte tägliche Challenges), `Reputation` (Dorfaufträge). Keine zweite Premium-Leistungswährung. `researchId`, prereqs, priceKnowledge, unlocks/items/machines/areas; Tech-Tree DAG: `tier_0→1→2→3→4→5`; Zweige Pflanzen/Mechanik/Metall/Runen/Logistik.

**Forscherlebnis:** Entdeckung ist sichtbar: erstmalige Rezeptproduktion gewährt Knowledge **einmal pro Account**; Wechsel auf neue Kette lohnt sich. Wiederholte Herstellung gibt Coins, aber kein unbegrenztes Knowledge. Beispiel: `firstCraft: +5`, `q05:+15`, `experiment:+3` mit festem Daily-Cap. Forschen via NPC/Workbench, serverseitig abgebuchte Punkte.

**Minimale Tech-Nodes, Datenformat `id: knowledgeCost -> unlock`:**
- T0 `starter_alchemy:0 -> kettle,tonic_minor,vitality_draught,night_ink`.
- T1 `herbalism:10 -> grinder,r06,r07`; `craftsman:12 -> saw,crusher,r04,r05,r24`; `glassworks:15 -> furnace,glassbench,r08,r09`; `storage:10 -> second_crate,workshop_48`.
- T2 `belt_basics:25 -> wooden_belt,belt_turn,input_hopper`; `flow_control:30 -> splitter,merger`; `essence_craft:30 -> extractor,bottler,r10-r13`; `fruit_mixing:20 -> mixer,r25`; `water_engineering:30 -> well_pump`; `farming:35 -> herb_grower`; `commission_contracts:20 -> order_board_tier2`.
- T3 `pipe_networks:50 -> pipes,tank`; `smart_sorting:45 -> filter_sorter`; `smithing:50 -> r15,r17,forge`; `rune_study:55 -> runetable,r14`; `enchantment:70 -> enchanter,r16,r18`; `multi_floor:60 -> workshop_floor_2,vertical_lift`; `licensed_mining:70 -> quarry_drill`.
- T4 `moonbotany:90 -> r19-r22`; `relic_weaving:100 -> r23`; `crystal_mastery:120 -> crystal_refiner,r27`; `infusion:105 -> infuser,r26`; `focus_charms:115 -> r28`.
- T5 `arcane_depths:180 -> advanced_cauldron,r29`; `masterwork:240 -> r30`; `portal_logistics:200 -> magical_gate`; `master_blueprints:130 -> larger blueprint slots`. Prereqs prüfen und als explizite IDs definieren, nicht aus Reihenfolge inferieren.

**Ausbaukosten:** 48² = 400 Coins; 64² = 1200; 80² = 3500; Etage 2 = 1800; Etage 3 = 4500 (erst bei Kapitelabschluss, technische Freigabe notwendig). Ein Plot darf nie größer werden als die reale Instanzzelle; Maschinen/Spieler dürfen nicht durch Außenwände. Zusätzliche Baufläche soll nützlich sein, aber kein Paywall-Ersatz.

**Eingebaute Balanceprüfung:** Automatisierte Tests rechnen für jede Quest benötigte Rezepte/Unlocks/Inputs, verfügbare Quellen, Min-/Max-Zeit; alle Progressionspfade müssen erreichbar sein; 10–30 min bis Erstautomatisierung als Ziel, kein Zwang zu 6h AFK. Kein Endgame-Produkt muss für weniger Coins verkauft werden als der nachweisbare Wert der nötigen nicht-tradbaren Vorprodukte (Preiswerte nach Simulation anpassen).

## 10 | Werkstattbau, Blueprint-System, Visuals

**Player workshop:** Stil des Dorfes fortführen: Alchemie-Fachwerk, Holzbalken, Backstein, Messing, Glas, Runensiegel, kleine magische Partikel. Außenfassade übernimmt Originalpalette; Maschinen erhalten passende Ergänzungsfarben, in `palette.COLORS` nur anhängen. Interior optisch modular und **sichtbar begehbar**, Rasterboden, Wände, Türen, Licht; bezahlte Wand-/Boden-/Dachvarianten sind später kosmetische Bauteile. Keine generische graue Part-Platte.

**Blender Pipeline erweitern:** `blender/village/machines.py`, `interiors.py`, optional `interactive_props.py` mit eigener `MACHINES`-/Interior-Registry, Bau-/Export-Einstieg über bestehende Modulstruktur. Pro Machine mindestens in/out Anchors, Surface/Collider-Proxies und optional Animation Pivot. Asset-IDs passen zu Config; ein Mesh pro Maschine wo möglich, bewegliche Teile separat. `blender/build_gameplay_assets.py` baut nur neue Assets. Tests auf gültige Normalen, Größen, gemeinsame Palette, triangle budgets, eindeutige Namen. **Nicht** unbemerkt die 91 alten Assets umbauen.

**Blueprints:** Spieler kann ausgewählte zusammenhängende Maschine/Belt/Pipe-Komponenten als kleines Layout speichern (`relativeGrid`, `rotation`, `machineId`, `recipe`, `settings`, `requiredUnlocks`, `estimateCost`). Vorschau vor Bau: fehlende Freischaltungen/Geld/Platz; Platzieren als **eine atomare Transaktion** (alles oder nichts), maximal z.B. 100 Bauteile/Blueprint und 10 Speicherplätze, limits konfigurierbar. Keine Übernahme von Shop-Inventaren/Fuel/Outputs, keine Gratisitems. Blueprints zunächst nur privat; Import/Share via validierte Codes erst als späteres Feature.

**Navigation & Animation:** NPCs/Werkstatt müssen in Smartphone-Ansicht gut navigierbar sein. Dritte-Person-Roblox-Standardkamera, keine eigens hart erzwungene First-Person-Pflicht; Mauern/Decke beim Blick-ins-Innere per lokaler Sichtbarkeitslogik; VFX gepoolt, bezahlbare Particle-Limits, Materialeffekte bei laufenden Maschinen. Interaktionszonen nicht unsichtbar klein.

## 11 | UI/UX: konkrete Screens und Zustände

**Mobile-first; PC vollständig.** UI optisch hochwertig wie Fantasy-Produktionssim: warmes Creme, dunkles Graphit, Messing, kategorisierte Icons, sparsame Akzente. Echte Roblox ScreenGuis, nicht nur Blender-Render. Skalierung per UIScale/Constraints, Safe-Area beachten; 44px-equivalent Touch-Ziele, Lokalisierung de/en über Keys. Klare Feedback-Texte, z.B. „Wartet auf 1 × Wasser“, nicht „Error“. Keine kritischen Aktionen in Microtext.

**HUD:** links oben Coins / Knowledge / Ruf; Questkarte; unten Actionbar Werkzeug+Build; rechts kompakter Maschinenstatus bzw. Wegmarker; mobile minimierter Aufbau mit aufklappbaren Menüs. Weltkarte mit Gebäudefunktionen + Fortschrittslock.

**Screens:**
1. Tutorial/Quest-Tracker (1 Ziel + 1 nachvollziehbare Aktion; Skip/Replay).
2. Inventar (Filter Rohstoffe/Produkte, Stack-Größen, Split/Transfer).
3. Machine inspector (Rezept, Input/Output, Geschwindigkeit, Status, Puffer, Pause, Transfer, Fehlerhilfe).
4. Build Catalogue (Tabs Maschine/Transport/Lager/Innenausbau, Suche, Preis, Unlock-Anforderung, Ghost/Rotate).
5. Recipe Codex (Baum aus Input→Prozess→Output; unbekannte Rezepte verdeckt, aber Anforderungen sichtbar).
6. Research Tree (Nodes, Kosten, Vorbedingungen, Unlock-Vorschau, Bestätigung).
7. Shop Manager (Regalbelegung, Wartezeit, Verkauf/Minute, Nachfrage, Engpass).
8. Order Board (Hauptquest, 3 begrenzte Aufträge, Rewards, Abgeben).
9. Production Insights (Durchsatz per min, Auslastung, Verbrauch, Bottleneck, Messzeitraum 1/5/15 min).
10. Workshop Menu (Erweiterungen, Einladungen/Rechte, Blueprint save/load, Settings, Exit).
11. Notifications/Help (mit De-Du-Sprache, kontextgebundene Tipps, Fehlerprotokoll).
12. Loading/Recovery UI (Fortschritt, fehlende Assets/DataStore-Ausfall, Retry, sichere Rückkehr).

**State:** Anzeigen basieren auf bestätigten Serverdaten; Client kann Optimistic Ghost anzeigen, aber Währung/Inventar/Unlock/Produktion **nur** aus Serverzustand ableiten. Remote-Antworten mit Result `{ok,code,version,payload}`; deduplizierte Aktions-IDs.

## 12 | Architektur: Roblox-Services, Daten, Events

**Zielstruktur neu (Beispiel; bestehendes Rojo-Projekt nicht ersetzen):**
```
roblox/
  VillageWorldBuilder.lua               # behalten
  WorldLayout.lua / WorldHeightmap.lua   # generiert, behalten
  gameplay/
    shared/       Config.lua, Items.lua, Recipes.lua, Machines.lua,
                  Research.lua, Quests.lua, Locations.lua, Types.lua,
                  GridMath.lua, Protocol.lua, Constants.lua
    server/       Bootstrap.server.lua, ProfileService.lua, EconomyService.lua,
                  InventoryService.lua, ResourceService.lua, WorkshopService.lua,
                  PlacementService.lua, MachineService.lua, LogisticsService.lua,
                  ProductionService.lua, ShopService.lua, QuestService.lua,
                  ResearchService.lua, NPCService.lua, VillageAdapter.lua,
                  CoOpPermissions.lua, SecurityService.lua, MetricsService.lua
    client/       Bootstrap.client.lua, HUDController.lua, InventoryUI.lua,
                  BuildController.lua, MachineUI.lua, ShopUI.lua,
                  ResearchUI.lua, QuestUI.lua, MapUI.lua,
                  CameraController.lua, AudioVFX.lua, NetworkClient.lua
    tests/        ... mocks and data-driven simulation tests ...
  gameplay_assets/ ... asset manifests for interior/machines ...
```
**Rojo:** `default.project.json` minimal-invasiv aktualisieren, `gameplay/shared`→`ReplicatedStorage` und server modules→`ServerScriptService`, client→`StarterPlayerScripts`, server model templates→`ServerStorage`. `VillageWorldBuilder` bleibt unter erwarteter `ServerStorage.VillageWorld`. Robuste `require`-Pfade; auf `Workspace.Village` nur zugreifen, wenn verfügbar. Nicht alle Großdaten in `ReplicatedStorage` replizieren.

**Service ownership:** Ein Service besitzt pro Datenart die **einzige schreibende Autorität**; Wallet: Economy, Inventar: Inventory, Layout: Workshop, Jobs: Production, Transport: Logistics, Quest: Quest, DB: Profile. Kein „ein Remote verändert beliebige Datentabelle“. Datenkonfiguration immutable und reiner Lua-5.1-kompatibler Datentabellenstil wo machbar; persistente IDs nie umbenennen ohne Migration.

**Protocol (ausreichende feste Aktionen):**
- Client→Server `RequestAction`: `GatherNode`, `EnterWorkshop`, `LeaveWorkshop`, `PlaceMachine`, `RemoveMachine`, `RotateMachine`, `SetRecipe`, `StartManualCraft`, `TransferStack`, `SetFilter`, `ToggleMachine`, `BuyUpgrade`, `UnlockResearch`, `StockShelf`, `ClaimOrder`, `InviteCoOp`, `SetCoOpPermission`, `SaveBlueprint`, `PlaceBlueprint`, `RequestSnapshot`.
- Server→Client `StateSnapshot`, `StateDelta`, `ActionResult`, `WorldMarker`, `Notification`, `ProductionFX`.
- `RequestAction` Payloaden als per-action explizit validierte Formate; harte Typ-, Zahlen-, ID-, Koordinaten-, Größen-, Rate-, Berechtigungs- und Distanzprüfung; `version` für konkurrierende Aktionen. Kein arbitrary Model/Instance Path vom Client akzeptieren. Server generiert Object-IDs; der Client sendet nur bekannte `instanceId`.

**Simulation:** `WorkshopSimulation.step(workshop,dt)` deterministisch, `dt` begrenzt, Reihenfolge: pending build changes → input transport → start possible jobs → advance jobs → output transport → stock/sale requests → publish compact metrics. Bei Jobfertigstellung Zielpuffer/Blockzustand sauber. Service zentral periodisch statt einen Coroutine-/Heartbeat-Handler pro Item/Maschine. Domain-Logik als **pure Lua-Module** ohne Roblox-APIs wo möglich (in normalen Lua-Tests ausführbar); Roblox-API in Adaptern.

**Client-Streaming:** Workspace StreamingEnabled bei echten Studiotests prüfen/konfigurieren; `WaitForChild` mit Timeouts/fallback, `CollectionService`/Tags für Interaktionsobjekte, `GetInstanceAddedSignal` bei stream-in, kein einmaliges `workspace.Descendants()` als einzige Bindung. 25 Dorfgebäude und 1.500 Naturinstanzen als visuelle Welt, mehr Clients nicht jeder die Fremdwerkstätten rendern.

## 13 | Persistenz und Fehlerfälle

`DataStoreService` serverseitig; Studio-Test nur auf **separatem Test-Place/Datastore**. Key `player:{UserId}`; `UpdateAsync` mit `pcall`, Retry+Jitter, Budget prüfen, Konflikte/Session-Lock vermeiden, niemals yielding callback. DataStore wird gelegentlich fehlschlagen: UI darf dann nichts als „erfolgreich gespeichert“ behaupten. Autosave etwa 60–120 s + PlayerRemoving + BindToClose (nach Budget, ohne endlose Schleife). Ein zentrales Profil pro Spieler, Schema-Version/Migrationen. Bei Ladefehler **kein überschreibbarer leerer Default-Save**; Safe Mode/Rejoin.

**Persistenzschema (konzeptionell):**
```
{
 schemaVersion=1, userId=123, revision=14, wallet=250, knowledge=30, rep=1,
 items={herb_mint=10,water=2000,...},
 unlocks={research={...},plotTier=2,extraFloors=0},
 discoveries={r01=true,...}, questState={...}, achievementState={...},
 workshop={sizeTier=2,layout={ {uid="m1",machine="grinder",gx=4,gz=3,floor=1,
            rot=90,recipe="r06",filter=nil,...},... },
            buffers={m1={in={...},out={...},job={recipe="r06",remaining=3.8}}}},
 shelfStock={tonic_minor=3}, blueprintSlots={...}, settings={...},
 lastSaveUnix=..., lastServerId=...
}
```
Keine Roblox-Instances, Vektoren oder CFrames direkt speichern. Strings/Integers/Booleans/Arrays/Maps. Speichergröße und Anzahl Maschinen/Blueprints begrenzen. Beim Laden Maschinen/Graph anhand gültiger IDs und Unlocks neu konstruieren; defekte Einträge in Quarantäne/Log und dem Spieler ggf. als sichere Ressourcen zurückgeben. Kein stiller Verlust. Quest- und Geldänderungen transaktional (in-memory, atomare Domain-Operation, dann persistieren); Dupes per wiederholten Remotes, reconnect, Exit während Craft, Race zwischen zwei Servern testen.

**Offline:** Produktionsfortschritt eingefroren, nicht beim erneuten Login minutenlang „nachsimulieren“; keine Arbitrage über Systemzeit. Optionen für später separat implementieren.

## 14 | Sicherheit, Limits, Fairness

- Server autoritativ für Coins, Items, Craft-Fertigstellung, Verkauf, Research, Quests, Platzieren, Zugriff auf Workshop. Alle Remotes strikt prüfen. Pro-Spieler/per-Action Rate-Limits; negative/NaN/Infinity/out-of-range ablehnen.
- Build auf gültigen Grundstückskoordinaten; Raster, Rotation, Lock, Kosten, Overlap, Collider, Stock/Port, Maschinenanzahl, Einheiten-Floors, max 100-Blueprint-Komponenten validieren.
- Keine direkte Client-Kontrolle über `DataStoreService`, Spielzeit, Verkaufspreis, Materialsupply, Itemtransfer, Forschungsstatus. Nicht authentifizierte fremde Owner-IDs ignorieren.
- Co-op Freigaben befristet, Owner kann entziehen; Besucher können nie Wallet von Owner selbst manipulieren; Operatoraktionen gelten für Owner-Bilanz und werden geloggt.
- Monetarisierung **nicht** nötig für Kernspiel; optional kosmetische Skins, Dekoration, Bauschilder, Animationen über echte Roblox Gamepasses/Developer Products mit serverseitigem Receipt-Handling und robuster Idempotenz. Keine Echtgeld-Glücksspiele/Pay-to-Win-Vorteile, keine künstlichen Blockadezeiten, keine Pflicht-Robux.
- Exploit-Tests: Spam Craft/Place/Claim; gleichzeitiges Shop + Quest aus gleichem Regal; Itemtransfer zwischen zwei Slots; doppelte `PurchaseReceipt`; Owner left while friend editing; ungültige itemId; negative amounts; NaN coords; Replay eines Action-IDs.

## 15 | Performance und visuelle Darstellung

**Kritische Baseline:** vorhandene 602k Dreiecke / 1.889 Instanzen, 340k Vegetation sind ohne echte Mobile-Messung **nicht automatisch okay**. Keine pauschale FPS-Behauptung. In Blender vegetative Assets auf Wiederverwendbarkeit, Silhouetten, LOD-/Far-distance-Varianten prüfen; Roblox Studio später Performance/MicroProfiler, Speicher, Drawcalls/Texture budgets verifizieren. Landschaft als Hintergrund anders behandeln als interaktive Werkstätten.

**Zielwerte (Prototyp-Testziele, keine Plattformgrenzen):** spielbar auf Mittelklasse-Mobilgerät mit ~30 FPS unter 1–2 produktiven Fabriken in Nähe, PC ~60 FPS; p95 serverseitiger Simulations-Step pro Workshop ≤ 5 ms (bei Ziel-Maxlayout, später mit Profiler bestätigen); UI-Reaktion lokal ≤ 100 ms, netzwerkbedingte Serverbestätigung klar anzeigen. Keine genaue Garantie aus Cloud-Mocks.

**Budgets initial:** pro Workshop soft cap 150 Machines + 400 belt/pipe segments + 8 floors? V1 nur 3 Etagen; 1 Shop+4 NPC-Visuals; max 200 graph nodes wird schnell überschritten bei 400 belts, deshalb Segmente zu längeren Kanten/Run-Lengths komprimieren. Simulation nur aktive Werkstätten; bei vollem Server Ziel 4 aktive Workshops; clientseitige Item-Visuals capped 50 sichtbare / Workshop. Größenordnung an realer Profiling-Messung anpassen, nicht als garantiertes Limit formulieren.

**Tech:** Meshes anchored, CollisionGroups, keine unnötigen `.Touched`-Hooks, keine pro-Item-Physik, Partikel-Recycling, Animation in Client, rein logische Server-Nodes. Liquid routing aggregieren; nur Daten-Deltas senden. Geräusch-/Lighting-Effekte skalierbar durch Grafikoptionen. Bei Streaming-Grenzen funktionieren Portale und Shopstatus trotzdem.

## 16 | Teststrategie / Acceptance Contract

**WICHTIG:** Cloud kann Lua-/Python-/Blender-/JSON-Tests ausführen, aber Roblox Studio nicht ohne explizite verfügbare Instanz. Deshalb 3 Teststufen getrennt ausweisen: `TESTED_LOCAL` (Python/Lua-mock), `TESTED_STUDIO` (Studio), `TESTED_DEVICE` (echte Mobile-Sessions). Ohne Studio-Testrun bleibt entsprechendes Flag `UNVERIFIED_IN_STUDIO`.

**Automatische Tests mindestens:**
- `data_integrity`: alle Items/Recipes/Machines/Research/Quests/Location-IDs eindeutig und referentiell gültig; Quests erreichbar; Unlock-DAG azyklisch; Startressourcen genügen für Tutorial; Gewinn-/Kosten-Sanity.
- `mesh_world`: bestehende 34 Checks weiterhin grün; neue Gameplay-Meshes exportieren; Pivot/Portal/Collider sauber; keine versehentlich geänderten generierten Quellen.
- `shop`: Sale nur wenn Stock, 2 parallele Käufer kaufen nie dieselben 1 Stück doppelt, Preise positiv, Auftrag+Sale race korrekt.
- `inventory`: Transfer erhält Summe aller Items (abgesehen von definiertem Verbrauch/Output), niemals negative Bestände.
- `production`: Jobstart reserviert korrekt, Pause/Resume, OutputBlocked, NoFuel, Rezeptwechsel, Entfernen mit Buffern; deterministische Simulation bei gleicher Inputfolge.
- `logistics`: Graph nach Rotation richtig, kaputte/verstopfte Leitung stoppt, Splitter fairness, Kreise ohne unendlich, Fluid bleibt 1000ml-genau, Removal sendet keine Duplikate.
- `placement`: nur erlaubte Zellen, Rotation, keine Overlaps, max building bounds, atomic Blueprint placement.
- `progression`: q01→q20 mit geskripteter Spielersimulation lösbar; T0→T5 ohne Robux und ohne illegale Rohstoffquelle.
- `save`: serialize→deserialize roundtrip, migration, Abbruch/Restart, concurrent UpdateAsync (Mock), Save-Failure schützt Daten, profile corruption recovery.
- `network`: malformed payload, rate limits, wrong owner, friend without access, idempotency/replay.
- `integration`: Spawn, Ortsanker am realen Layout, Fenster/Tore/Collision-Proxys, Exportnamen → Template-Matching.

**Manual Studio-Playtest später:** (a) import all templates, check `report.missing==0`; (b) spawn on street not underground; (c) enter/exit workshop; (d) full first sale; (e) build linked machines, walk around them, move item; (f) save, quit, rejoin; (g) join with 2–4 players; (h) phone GUI/controls in real device; (i) performance with target scale; (j) `WorldLayout.lua` compatibility. Im Report jede Abweichung festhalten.

**Definition of Done per Feature:** A. Daten + B. Servercode + C. Roblox UI/Anker + D. Tests + E. Dokumentation + F. Integration in Demo ohne Dummy. Eine Funktion ohne nachvollziehbaren nutzbaren Weg ist **nicht fertig**. Bei untestbaren Studio-Schritten den Status „blocked pending Studio“ vergeben, nicht behaupten, sie seien live.

## 17 | BUILD ORDER (konkret, ohne Placeholder-Finish)

**Phase 0 — Repo Audit & Safety:** Ausgangsbranch verifizieren; Read-only Bestandsaufnahme; Git-Branch `feat/arcane-village-gameplay`; Konfiguration/Rojo und Exportpfade auditieren, bestehenden Build laufen lassen; `docs/IMPLEMENTATION_STATUS.md` erzeugen (`DONE|IN_PROGRESS|BLOCKED|UNVERIFIED_STUDIO`, commit IDs, Testbefehl). Keine destruktive Migration.

**Phase 1 — Deterministische Daten + Domain-Core:** Items/Machines/Recipes/Research/Quests/LocationConfig; Validator; pure Lua Economy/Inventory/Crafting; automatisierte Testsimulation Start→erste Trankproduktion. Erst wenn alle Tests laufen weiter.

**Phase 2 — Dorf & Workshop-Hülle:** `VillageAdapter` registriert reale 25 Gebäude + Teleporter-Anker; Workshop-Instanz mit echtem Raum, Boden, Wänden, Ausgang; Spawn/Tutorial-NPC; serverseitiges Enter/Leave; Roblox-Luau-Skripte und Workshop-Generator. Bestehenden Weltbuilder nicht ersetzen.

**Phase 3 — Kernloop spielbar:** Sammeln (Minze/Wasser/Sonnenblatt), Starterkessel, Inventar, UI, Regal, NPC-Käufer, Coins, erste 5 Quests, Save/Load. Vollständiger Manual-Loop, keine Fake-Kunden. `starter_playthrough` als Test dokumentieren.

**Phase 4 — Produktion/Automatisierung:** Grid + Ghost/Place/Remove/Rotate, MachineJobs, Crates, Belts, Hopper, Splitter, ConnectorGraph, Visuals und Backpressure; eine nachweislich automatische Kette bis Regal inkl. Wiederanlauf nach Save.

**Phase 5 — Dorfwirtschaft & Forschung:** Rathaus-/Markthallenaufträge, Reputation, Research DAG, T0–T3, neue Resource-Nodes, Farm, Brennstoff, Schmiede, Farbkarten/Markers; vollständige UI/Questgeber.

**Phase 6 — Flüssigkeiten & vertikales Bauen:** Pumpen/Tanks/Pipes, Multi-Floor, Lifts, Sorter, robuste Maschinenports, UI-Simulation/Throughput; Save/Load komplexer Netzwerke.

**Phase 7 — High-Tier Content:** T4–T5, 30 vollständige Rezepte, 20 Hauptquests, 20 Repeatable Templates, 8 NPC-Queststränge, seltene Ressourcen, Endgame-Produkt, Master-Abschluss ohne Grind-Sackgassen.

**Phase 8 — Co-op & Blueprints:** Owner/Visitor/Operator/Builder Permissions, Invite, Leave, abbruchsichere Server-Transaktionen, private Blueprints; Multiplayer-Tests.

**Phase 9 — Art, Polish, Performance:** Blender-Maschinen, echte Innenräume, Animation/Sound/VFX, NPC-Wege/Shop, robustes Mobile-UI, Datenoptimierungen, Build-/Terrain-/World-Checks. Alles mit originalem Stylized Village visuell integrieren.

**Phase 10 — Studio handoff:** `docs/ROBLOX_GAMEPLAY_IMPORT.md` mit exakten Studio-Einrichtungs-/Rojo-/Asset-/Place-Test-Schritten, fehlende Voraussetzungen, Troubleshooting, Testmatrix. Ein Skript `scripts/check_all.sh` oder äquivalenter CI-Befehl für ausführbare Cloud-Prüfungen; Exportmanifest, Preview, Testreports. Nach tatsächlichem Studio-Test Fehlerberichte verarbeiten; keine Veröffentlichung auf eigenmächtige Art.

**Arbeitsmodus:** Jede Phase in kleine commits, jede Teilfunktion vollständig end-to-end; nach bestandenem Test zur nächsten Aufgabe statt auf neue Nutzeranweisung zu warten, sofern Berechtigungen/Ressourcen vorhanden. Keine Schein-Komplettlösung (z.B. nur 800 Zeilen Platzhaltercode). Bei Cloud-Limitations dokumentierte Alternative und vorhandene Tasks fortsetzen. Bestehende stabile Funktionen nie zugunsten schnellerer Implementierung entfernen.

## 18 | Wichtige Edge Cases und Designentscheidungen

- Kein Player-Softlock: Minze/Wasser zu Beginn mehrfach regenerierbar; fehlende Coins dürfen Sammlung und Handbrauen niemals blockieren. Falls inventar voll, sichtbare Feedbackmeldung + Kiste als Abwurf.
- Keine durch Mob/Hub-NPC verursachte Factory-Blockade; NPCs dürfen nicht Maschinen zerstören/Player verdrängen.
- Beim Maschinenabbau: Puffer auf sicheren Inventory-/Overflow-Container übertragen oder Abbau verweigern. Keine still gelöschten wertvollen Items.
- Workshoptür muss Spawn/Exit nach WorldBuilder-Neubau noch finden, auch wenn Layoutposition geändert wird.
- Client-Rounding kann Verkauf nicht mehrfach triggern; Server sendet autoritativen Wert.
- Vial- und Bottle-Rezepte brauchen im Tutorial keine unmöglichen Inputs; handgemachte r01-r03 existieren ohne Glas, ab T2 abgefüllte Spezialprodukte.
- Kapazität & Priorität: Bereits laufender Craft wird nicht überschrieben, wenn Rezept im UI gewechselt; Wechsel nur bei Idle oder nach klarer Cancel-Regel.
- Flüssigkeitsrohre können keine Solid Items transportieren; beim Umkonfigurieren Restfluid sichern/Entleerung verlangen.
- Die Werkstatt braucht 3 räumliche Zustände: 32² / 48² / 64² / 80²; nicht permanent unsichtbar blockiert durch unskalierte Collider.
- Shop-NPCs keine dauerhafte Heavyweight-AI; Queue/Checkout wird logisch geführt, Darstellung darf vereinfacht sein.
- Charakter-Ruf/Town-Demand nicht als künstliches Idle/Robux-Gate einsetzen.
- Mehrstöckige Fabrik: Lift braucht beide Endports, Etagen-Freischaltung, ordentliche Spieler-Treppe; kein Teleport von Items ohne Pipeline.
- Save-Migrationen dürfen neue Rezept-IDs hinzufügen, aber alte IDs nicht still entfernen.
- Studienstatus: Ohne Roblox Studio keine Aussage „importiert, spielbar und performant auf iPhone“.

## 19 | Lieferobjekte & Übergabe an nächste KI

**Obligatorisch:** komplette Lua/Luau-Daten- und Gameplaymodule + Starter-UI und Innenräume; per Blender generierte passende Assets/GLBs/Previews; aktualisierte Rojo-Config; Test-Suites; alle relevanten Builds; `docs/IMPLEMENTATION_STATUS.md`; `docs/GAMEPLAY_ARCHITECTURE.md` (Services/Abhängigkeiten); `docs/ROBLOX_GAMEPLAY_IMPORT.md`; `docs/CHANGELOG_GAMEPLAY.md`; ggfs. `docs/BLOCKERS_STUDIO.md`. Dieser Master-Spec bleibt unverändert, Änderungen als versionierte Entscheidung in `docs/DESIGN_DECISIONS.md` festhalten.

**Progress Report pro Phase (kurz):** `phase | implemented files | test command/result | gameplay demo path | known blockers | next phase`. Zum Schluss: reale „Start→1. Verkauf→erste automatische Kette→Save/Reload→Endgame“-Teststrecke, offene echte Studio-Checks separat, exakte Commit-ID.

**Exit Criteria Gesamtprojekt:** keine gesperrten Pflichtquests; mindestens 30 implementierte, ausführbare Rezepte, 15+ funktionierende Maschinen, 10+ Logistikkomponenten, 20 Hauptquests, 20+ Nebenaufträge, 8 NPC-Stränge; Dorfrollen aktiv; Solo bis Master-Endgame; Benutzer kann Werkstatt bauen, seine Produktion beobachten, Lager & Shop nutzen, Forschung freischalten, speichern und nach Login fortfahren. Co-op/Blueprints gemäß Phasen. Mobile-UI tatsächlich am Gerät zu prüfen, sobald Studio-Zugriff da ist.

## 20 | Quellenstatus, technische Belege

**Mechanische Inspiration, nicht nachzuprogrammierende Originaldaten:** offizielles Steam-Spielprofil `https://store.steampowered.com/app/3669570/Alchemy_Factory/` (Förderbänder, Rohre, Produktion, Multi-Level, Laden, Freunde, Blueprints); offizielle Developer-Patchnotes `https://steamcommunity.com/app/3669570/allnews/` (u.a. Wagon-System, Shops, Forschung). Unsere Rezeptnamen/-preise/-Quests sind **eigene Entwurfswerte**, nicht als Alchemy-Factory-Kanon zu verstehen.

**Roblox-Richtlinien/Technik:** Servervalidierung `https://create.roblox.com/docs/scripting/security/client-server-boundary`; DataStores `https://create.roblox.com/docs/cloud-services/data-stores`; Performance/Streaming `https://create.roblox.com/docs/performance-optimization/improve`; Monetarisierung `https://create.roblox.com/docs/production/monetization/passes`. Vor Umsetzung der jeweiligen Roblox-API aktuelle Developer-Doku und verfügbare Laufzeit prüfen.

**Bestehendes Projekt:** `docs/AI_HANDOFF.md`, `docs/ROBLOX_IMPORT.md`, `world/level_summary.md`, `blender/village/plan.py`, `roblox/VillageWorldBuilder.lua` im geprüften GitHub-Branch. Neue Spezifikation behauptet keine bereits umgesetzten Gameplay-Funktionen.

---
**STARTBEFEHL FÜR CLAUDE:** Prüfe Branch und Projektdokumente, erstelle einen neuen Feature-Branch, führe Baseline-Tests aus, beginne bei Phase 0 und implementiere danach Phase 1 vollständig. Arbeite inkrementell durch alle Phasen; publiziere jeweils Quellcode, Tests und Status. Wenn Roblox Studio nicht erreichbar ist, entwickle und prüfe alles, was über Lua-/Python-/Blender-Mocks ausführbar ist, und markiere exakt, was später in Studio validiert werden muss. Keine Rückfrage bei aus diesem Dokument eindeutig bestimmbaren Designentscheidungen.
