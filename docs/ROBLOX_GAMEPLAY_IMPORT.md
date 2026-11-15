# Gameplay in Roblox Studio einrichten

> Ungeprüft in Studio. Voraussetzung ist die importierte Dorfwelt nach `docs/ROBLOX_IMPORT.md`
> (insbesondere `ServerStorage.VillageWorld.WorldLayout`).

## 0. Schnellstart mit der fertigen Place-Datei

`exports/roblox/ArcaneVillage.rbxlx` in Roblox Studio öffnen (Datei → Von Datei öffnen) und Play
drücken. Die Datei enthält alle Skripte am richtigen Platz; die Schritte 1 und 2 entfallen.

Beim Start baut `VillageAutoBuild` das Dorf selbst:

| Zustand | Ergebnis |
|---|---|
| keine Meshes importiert | Voxel-Gelände aus der Höhenkarte, je Gebäude ein farbiger Block in Originalgröße und -lage („Greybox") |
| `ServerStorage.VillageAssets` vorhanden, ohne Geländekacheln | echte Modelle auf Voxel-Gelände |
| `VillageAssets` mit Geländekacheln | vollständiges Dorf wie in den Vorschauen |

Das Spiel (Sammeln, Werkstatt, Maschinen, Verkauf) läuft in allen drei Zuständen mit denselben
Koordinaten. Die Datei wird mit `python scripts/build_place.py` neu erzeugt. Sie ist wohlgeformtes
XML im rbxlx-Aufbau, wurde aber nie in Studio geöffnet.

## 1. Skripte

Mit Rojo: `rojo serve` im Repository, in Studio verbinden. `default.project.json` legt an:

| Ziel | Quelle |
|---|---|
| `ReplicatedStorage.ArcaneShared` | `roblox/gameplay/shared` |
| `ServerScriptService.ArcaneServer` | `roblox/gameplay/server` (`Bootstrap.server.lua` wird ein Script) |
| `StarterPlayer.StarterPlayerScripts.ArcaneClient` | `roblox/gameplay/client` (`Bootstrap.client.lua` wird ein LocalScript) |
| `ServerStorage.VillageWorld` | wie bisher |

Ohne Rojo: dieselben Ordner von Hand anlegen; alle Dateien außer den beiden `Bootstrap` als
ModuleScript, Namen ohne `.lua`.

## 2. Maschinen-Meshes (optional, sonst Quader)

`exports/library/arcane_machines.glb` (ersatzweise `.fbx`) importieren und das Model nach
`ServerStorage.ArcaneAssets` legen. Die MeshParts müssen `mach_<id>` bzw. `logi_<id>` heißen.

## 3. Einstellungen

- *Game Settings → Security → Enable Studio Access to API Services* einschalten, sonst wird nicht
  gespeichert (der Server meldet das und der Client zeigt es im HUD).
- Zum Testen einen eigenen Test-Place verwenden; der DataStore heißt `ArcaneVillage_v1`.
- Steht das Dorf nicht im Ursprung: `workspace:SetAttribute("VillageOrigin", <CFrame>)` mit demselben
  Wert wie `origin` beim Welt-Builder.

## 4. Testmatrix

| # | Schritt | Erwartung |
|---|---|---|
| a | Play starten | Ausgabe „[Arcane] server ready", keine Fehler; Spawn auf dem Marktplatz |
| b | Zu einem grünen Marker am Platz gehen, „Sammeln" | Meldung „+ 2 × Minze", Bestand im Beutel |
| c | Goldener Marker vor dem Fachwerkhaus, „Betreten" | Innenraum mit Kessel, Kiste, Regal; q01 erledigt |
| d | Kessel „Öffnen" → Rezept „Herstellen" | Status „läuft", nach 8 s „Fertig: 1 × Kleines Tonikum" |
| e | Entnehmen, Regal „Öffnen" → „Einfüllen" | nach 15–25 s Münzen, q03 erledigt |
| f | „Bauen" → Kräutermühle (nach Forschung) | Ghost grün, nach ✓ steht die Maschine, Münzen abgezogen |
| g | Kiste → Trichter → Band → Mühle bauen, Minze in die Kiste | Pulver entsteht ohne weiteres Zutun |
| h | Stop, erneut Play | Layout, Puffer, Münzen wie zuvor |
| i | 2 Spieler (Test → Clients and Servers) | jeder in seinem eigenen Innenraum |
| j | Gerätesimulation Handy | alle Schaltflächen bedienbar |

Abweichungen bitte mit der Nummer aus `docs/BLOCKERS_STUDIO.md` zurückmelden.

## 5. Fehlersuche

| Symptom | Ursache |
|---|---|
| „WorldLayout not found – village services are disabled" | Dorf-Skripte fehlen in `ServerStorage.VillageWorld` |
| „location without building: …" | Layout enthält die Instanz nicht (Welt neu generiert?) – `spec_adapter` prüfen |
| HUD zeigt „nicht gespeichert" | API-Zugriff in Studio aus |
| Marker schweben oder stecken im Boden | Dorf noch nicht aufgebaut, als der Server startete (Raycast traf nichts) |
| Maschine erscheint gedreht zum Ghost | Vorzeichen der Drehung in `WorkshopWorld.entityModel` anpassen (Blocker 7) |
