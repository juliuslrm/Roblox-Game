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
| `ServerStorage.VillageAssets` mit fehlenden oder leeren Gelände-/Wasser-Vorlagen | echte Modelle auf durchgehendem Voxel-Gelände |
| `VillageAssets` mit vollständigen Gelände- und Wasser-Vorlagen | importiertes Mesh-Gelände |

Im Studio-Output unter `[Village]` stehen die fehlenden Geländevorlagen, Warnungen zu
Dorfmodellen und die Asset-Namen, deren `CollisionFidelity` geprüft werden muss.

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

Die neue Trankbrauer-Fassade und der Braukessel werden in [WORKSHOP.md](WORKSHOP.md) eingerichtet.

## 2. Maschinen-Meshes (optional, sonst Quader)

`exports/library/arcane_machines.glb` (ersatzweise `.fbx`) importieren und das Model nach
`ServerStorage.ArcaneAssets` legen. Die MeshParts müssen `mach_<id>` bzw. `logi_<id>` heißen.

Für die fünf Markt-NPCs und ihre Stände siehe [MARKET_MERCHANTS.md](MARKET_MERCHANTS.md).

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

## Upload ohne Studio (Open Cloud)

Die Place-Datei lässt sich ohne Roblox Studio direkt in ein bestehendes Spiel hochladen
(API-Key mit System `universe-places`, Operation Write):

```bash
curl -X POST "https://apis.roblox.com/universes/v1/<universeId>/places/<placeId>/versions?versionType=Published" \
  -H "x-api-key: <key>" -H "Content-Type: application/xml" \
  --data-binary @exports/roblox/ArcaneVillage.rbxlx
```

- Tatsächlich geprüft (2026-11-16): Antwort `HTTP 200 {"versionNumber":…}`.
- Die Datei muss exakt mit `</roblox>` enden. Schon ein Zeilenumbruch danach führt zu
  `400 Invalid Content stream` (`scripts/build_place.py` und der Test stellen das sicher).
- `versionType=Saved` speichert nur, ohne zu veröffentlichen.
- Der Key gehört nicht ins Repository.

## Modelle ohne Studio (Open Cloud Assets API)

Die Sammeldateien aus `exports/library/*.fbx` und die Palettentextur wurden über
`POST https://apis.roblox.com/assets/v1/assets` (API-System `assets`, Read + Write) als Assets
hochgeladen. Die IDs stehen in `roblox/VillageAssetIds.lua`. Beim Serverstart lädt
`roblox/VillageAssetLoader.lua` sie mit `InsertService:LoadAsset` nach `ServerStorage.VillageAssets`
und `ServerStorage.ArcaneAssets`; passen keine Namen zum Levelplan, bleibt es bei der Blockversion.

- Tatsächlich geprüft (2026-11-16): Upload aller vier Assets, Moderation „Approved".
- UNVERIFIED_IN_STUDIO: ob `LoadAsset` die Meshes mit den erwarteten Namen und der Textur liefert.
  Die Konsole meldet dazu `[Village] assets: …` und `[Village] templates: …`.
