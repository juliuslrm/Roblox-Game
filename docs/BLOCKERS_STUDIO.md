# Blocked pending Roblox Studio

Alles hier ist geschrieben, aber nie in Roblox gelaufen. Reihenfolge = sinnvolle Prüfreihenfolge.

| # | Zu prüfen | Datei | Risiko |
|---|---|---|---|
| 0 | `exports/roblox/ArcaneVillage.rbxlx` lässt sich öffnen; beim Start erscheint „[Village] built in mode …" | `scripts/build_place.py`, `VillageAutoBuild` | hoch – Dateiformat aus dem Gedächtnis |
| 1 | Rojo-Sync legt `ArcaneShared`, `ArcaneServer`, `ArcaneClient` richtig an; `Bootstrap` wird Script bzw. LocalScript | `default.project.json` | mittel |
| 2 | Server startet ohne Fehler, Meldung „[Arcane] server ready" | `Bootstrap.server.lua` | hoch – viele API-Aufrufe aus dem Gedächtnis |
| 3 | Marker stehen vor den Gebäuden auf dem Boden (Raycast), nicht darunter oder in Wänden | `Bootstrap.server.lua` | mittel |
| 4 | „Betreten" teleportiert in den Innenraum, „Verlassen" zurück vor die Tür | `WorkshopWorld.lua` | mittel |
| 5 | HUD und Fenster erscheinen, Schaltflächen sind am Handy treffbar | `Bootstrap.client.lua` | hoch |
| 6 | Maschinen-Prompt öffnet das Maschinenfenster; Brauen, Entnehmen, Regal füllen | Client + Server | mittel |
| 7 | Baumodus: Ghost folgt Maus bzw. Bildschirmmitte, Drehrichtung von Ghost, Server und Mesh stimmen überein | Client, `WorkshopWorld.lua` | hoch – Vorzeichen der Drehung ungeprüft |
| 8 | DataStore: Speichern, Verlassen, Wiederbeitritt; Verhalten ohne API-Zugriff in Studio | `ProfileStore.lua` | mittel |
| 9 | Maschinen-Meshes aus `arcane_machines.glb` in `ServerStorage.ArcaneAssets`: Name, Größe, Ausrichtung | `WorkshopWorld.lua` | mittel |
| 10 | 2–4 Spieler: getrennte Innenräume, Co-op-Rechte | Server | mittel |
| 11 | StreamingEnabled: Marker und Innenraum werden rechtzeitig geladen | – | unbekannt |
| 12 | Leistung auf einem Mittelklasse-Handy | – | unbekannt |

Bekannte Annahmen, die falsch sein können:

- `workspace:GetServerTimeNow()`, `ProximityPrompt.Triggered`, `Model:PivotTo`, `UIScale`,
  `AutomaticCanvasSize` sind aus dem Gedächtnis verwendet.
- Innenräume liegen bei x, z ≥ 6000 und y = 800; ob das mit Streaming und Beleuchtung harmoniert,
  ist offen.
- Ohne importierte Maschinen-Meshes zeigt der Server farbige Quader mit Beschriftung. Das ist
  eine Rückfallebene, kein Endzustand.

## Nachtrag 2026-11-16: erste Messungen im echten Place (Open Cloud)

Mit `scripts/roblox_exec.py` (Luau Execution API) lassen sich Skripte im veröffentlichten Place
ausführen. `scripts/roblox_verify_world.lua` baut das Dorf wie beim Serverstart und misst es.

Bestätigt (Place-Version 8):
- Die drei Modellbibliotheken laden per `InsertService:LoadAsset`: 172 MeshParts, Namen und Maßstab
  (1:1) stimmen, Palettentextur ist gesetzt.
- 140 von 140 Vorlagen gefunden, 1 889 von 1 889 Objekten platziert, 0 Warnungen.
- Bodenprüfung (2 304 Strahlen gegen die Höhenkarte): mittlere Abweichung 0,30 Studs nach der
  Kollisionsverfeinerung (vorher 0,48), 39 Punkte über 1,5 Studs, 2 ohne Treffer.

Gefundene und behobene Fehler:
- Roblox importiert die FBX-Bibliotheken um 180° um die Hochachse gedreht. Jedes Geländestück lag
  dadurch verdreht an seinem Platz (Lücken, schwebende Wege). `VillageAssetLoader` dreht zurück
  (`importYaw` in `VillageAssetIds.lua`).
- Beleuchtung zu hell (Ambient 0,5 als Standard, Brightness 2,6, 76 Lampen am Tag): Werte gesenkt,
  Lampen bis zu einem Tag-Nacht-Wechsel aus.
- Importierte MeshParts haben `CollisionFidelity.Default`; `Auto.refineCollision` ersetzt Gelände
  und Wege im Hintergrund durch präzise Kollision (ca. 40 s).
- Maschinenmodelle standen zur Hälfte im Boden (`WorkshopWorld`).

Weiter ungeprüft: Aussehen (kein Bild aus dem Place), `Bootstrap.server.lua`, Client-UI.
Offen: Ursache der 39 Abweichungen über 1,5 Studs (Rand, Bachufer) ist nicht geklärt.

## Nachtrag 2026-11-16 (2): Markt, Werkstatt und Serverstart im echten Place

Place-Version 9, geprüft mit `scripts/roblox_verify_server.py` (führt beide Server-Startskripte
im Place aus):

- `VillageAutoBuild` und `Bootstrap.server.lua` laufen ohne Fehler durch; `[Arcane] server ready -
  persistent saves: true`. RemoteFunction/RemoteEvent, Werkstätten, Marker und Markt entstehen.
- `ArcaneMarket.glb`, `workshop_facade.glb` und `mach_kettle.glb` sind als Assets hochgeladen
  (IDs in `roblox/VillageAssetIds.lua`); GLB kommt wie FBX um 180° gedreht an.
- Alle fünf Händler und Stände stehen als importierte Meshes an ihren Plätzen, die alten
  Marktstände sind ersetzt.

Offen:
- Händler-Animation: Roblox legt die 40 Bones aller fünf Figuren in ein gemeinsames `RootPart`
  statt in die MeshParts. `MarketWorld`/`MarketIdle` finden deshalb kein Skelett, die Händler stehen
  still. Ansatz: die fünf `merchant_*.glb` einzeln hochladen und das ganze Rig-Modell platzieren.
- Nicht nachgemessen: ob die Werkstattfassade das Fachwerkhaus ersetzt hat, Blickrichtung der
  Figuren, Aussehen allgemein, gesamte Client-UI (Handeln-Dialog auf Touch).

## Nachtrag 2026-11-16 (3): begehbare Werkstätten

Place-Version 10, gemessen mit `scripts/roblox_verify_server.py`:

- Serverstart fehlerfrei; neue Geländebibliothek (mit Grundstücken und Zugangswegen) lädt,
  144 von 144 Vorlagen, 1 879 Objekte.
- Auf jedem der vier Grundstücke baut `WorkshopWorld` eine offene Werkstatt (getestet 32–80 Studs,
  1–3 Etagen). Boden 0,6 Studs über Plan-Niveau, Kessel steht auf dem Boden, alle vier Öffnungen
  frei (Strahl in Brusthöhe trifft nichts), neben der Öffnung steht Mauer.
- `ownerAt` erkennt innen und in der Öffnung den Besitzer, 6 Studs außerhalb niemanden.

Offen:
- Automatisches Betreten/Verlassen mit einer echten Spielfigur (Heartbeat-Schleife in
  `Bootstrap.server.lua`) ist nur über die Kernlogik und `ownerAt` geprüft, nicht mit einem Spieler.
- Grundstück 4: Bodenstrahlen melden vor der Kollisionsverfeinerung bis 3,8 statt 0,8 Studs
  (vermutlich grobe Standardkollision am steilen Hang daneben) – nach der Verfeinerung nicht
  nachgemessen.
- Aussehen, Kamera im Gebäude, Bauen per Touch: nur am Gerät prüfbar.

## Nachtrag 2026-11-16 (4): Boden verändert sich beim Laufen

Spielerbericht mit Screenshot (Handy): Boden und Wege verändern beim Laufen ihre Form.
Deutung (nicht am Gerät bestätigt): `RenderFidelity.Automatic` ersetzt die großen Geländemeshes
auf Distanz durch gröbere Stufen.

- `Auto.refineGround` setzt Gelände, Wege und Wasser im Hintergrund auf `RenderFidelity.Precise`
  und präzise Kollision, beginnend am Spawn (54 Teile, ca. 40 s; parallel wird es nicht schneller).
- Gemessen: Präzise Kollision hat Löcher – 90 von 36 481 Punkten im 4-Stud-Raster ohne Boden, auch
  auf dem Dorfplatz. Die Standardkollision hat keine Löcher, liegt aber an 5 % der Punkte um mehr
  als 1,5 Studs daneben. Lösung: nach jedem Geländeteil wird sein Quadrat im 2-Stud-Raster
  abgetastet und jedes Loch mit einer unsichtbaren Platte auf Höhenkarten-Niveau geschlossen
  (652 Platten).
- Ergebnis im Place: 0 von 36 481 Punkten ohne Boden, mittlere Abweichung 0,26 Studs, 322 Punkte
  (0,9 %) über 1,5 Studs, größte 24 (Ursache offen, vermutlich Bachufer/Weltrand).
- Offen: ob die per `ApplyMesh` gesetzte Kollision und Darstellung auch auf dem Client ankommen.
