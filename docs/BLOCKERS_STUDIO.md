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

## Nachtrag 2026-11-16 (5): graue Geländestücke – eigentliche Ursache

Der Spielerbericht aus Nachtrag (4) meinte etwas anderes: Geländestücke verlieren beim Laufen ihre
Farbe und werden grau. Die Deutung „Detailstufen" war falsch.

- Ursache (im Place bestätigt): `MeshPart:ApplyMesh` übernimmt auch die leere `TextureID` des mit
  `CreateMeshPartAsync` erzeugten Teils. Die Hintergrund-Verfeinerung (seit Place-Version 8) hat so
  ein Geländestück nach dem anderen entfärbt.
- Behoben in Version 13: `Auto.refineGround` sichert die Textur vor `ApplyMesh` und setzt sie
  danach wieder. Gemessen: 0 von 54 Bodenteilen ohne Textur.
- Die Änderungen aus (4) bleiben (exakte Darstellung, exakte Kollision, geschlossene Löcher).

## Nachtrag 2026-11-16 (6): Rohstoffe als Modelle statt Kreise

- 15 Rohstoffmodelle (`blender/village/resources.py`, eines je Rohstoff, 196–1 600 Dreiecke) ersetzen
  die Kreise an den 22 Sammelstellen. `ResourceWorld.lua` stellt sie auf; der „Sammeln"-Prompt hängt
  am Modell, ein leerer Vorrat wird durchscheinend und lässt sich nicht ernten.
- Place-Version 14 gemessen: 22 Sammelstellen, 22 texturierte Modelle, 22 Prompts, kein Kreis mehr.
- Offen: `n_water_bridge` steht 2,8 Studs über dem Gelände (vermutlich auf der Brücke),
  `n_stone_mill` 1,4 Studs (steht vermutlich auf einem Objekt). Ob Modelle in Zäunen, Bäumen oder
  Deko stecken, ist nicht geprüft. Die Orts-Kreise („Ansprechen") bleiben, bis es NPC-Figuren gibt.
- Im Roblox-Konto liegt noch die alte Geländebibliothek (Asset 115718062572873, „VillageTerrain"),
  die nicht mehr geladen wird.

## Nachtrag 2026-11-16 (7): Bedienung, Markierungen, Bodenhöhen

Place-Version 17. Auf dem Server gemessen, Client-Änderungen nur per Syntaxprüfung und Durchsicht.

Behoben:
- Client: Das offene Menü wurde bei jedem Snapshot (1 ×/s) neu aufgebaut – Listen sprangen nach
  oben, Tipps auf Knöpfe gingen verloren. Jetzt nur bei geänderter Signatur des Spielstands (bzw.
  alle 2 s bei Menüs mit Timern), die Scrollposition bleibt erhalten.
- Client: Der Bau-Platzhalter zielte am Handy auf die Bildschirmmitte, wo die eigene Figur steht;
  der Strahl traf sie statt des Bodens. Jetzt zählt die zuletzt angetippte Stelle, und der Strahl
  geht durch Figur, Maschinen und Wände bis zum Werkstattboden.
- Server: Bodenhöhen für Sammelstellen, Ortsmarkierungen und Marktstände kamen aus Strahlen gegen
  die noch grobe Startkollision (bis 2,8 Studs zu hoch). Jetzt aus der Höhenkarte; auf Brücke und
  Steg zählt deren Oberseite. Gemessen: größte Lücke Modell–Boden 0,9 Studs (vorher 2,8).

Neu:
- Wegweiser auf dem Bildschirm zur eigenen Werkstatt und zum Ziel des Hauptauftrags, mit Entfernung
  (`snap.home`, `snap.guide`).
- Ortsmarkierungen: Pfosten mit Namensschild und ruhigem Bodenring statt leuchtender Scheiben,
  Farbe nach Art des Ortes. Gemessen: 16 Pfosten mit Schild und Prompt, kein Neon-Teil mehr.
- Namensschilder an den Rohstoffen; Hinweistexte nennen den Wegweiser.

Weiter offen: Händler-Animation, Aussehen und Bedienung auf dem Gerät (alle Client-Änderungen
dieser Runde), 0,9 % der Bodenpunkte mit mehr als 1,5 Studs Kollisionsabweichung.

## Nachtrag 2026-11-16 (8): Händler neu aufgebaut

Die Händler aus dem Import (ein skinned Mesh je Figur) haben sich in Roblox nie bewegt: Der
Asset-Upload legt die Bones aller Figuren in ein gemeinsames `RootPart`. Sie sind durch
Gliederfiguren aus sieben starren Teilen ersetzt (`docs/MARKET_MERCHANTS.md`); die Animation setzt
nur CFrames und braucht kein Skelett. Der alte Generator (`build_market.py`, `market_rig.py`,
`market_motion.py`, `MarketIdle.lua`) ist entfernt.

Place-Version 18 gemessen: 5 Figuren × 7 texturierte Teile, Serverstart fehlerfrei.
Offen: laufende Animation und Aussehen am Gerät.

## Nachtrag 2026-11-16 (9): „Diese Maschine gibt es nicht mehr" am Kessel

Spielerbericht. Ursache (lokal nachgestellt): `SecurityService` prüfte Nutzernummern als `"int"` mit
Grenze 1 000 000; echte Roblox-IDs liegen in den Milliarden. `EnterWorkshop { owner = <id> }` kam
deshalb als `BAD_REQUEST` zurück, niemand galt je als „in der Werkstatt": Maschinenmenü ohne
Maschine, kein Bauen, Auftrag q01 nicht erfüllbar. Die Tests nutzten nur kleine Testnummern.
Behoben in Version 19: eigener Feldtyp `"user"` für `EnterWorkshop`, `InviteCoOp`,
`SetCoOpPermission`; Regressionstest mit realistischen IDs.

## Nachtrag 2026-11-16 (10): Werkstatt-Produktion überarbeitet

Place-Version 20. Kernlogik lokal getestet (`spec_ports`, 9 Szenarien), Darstellung im Place gemessen,
Client nur syntaktisch geprüft.

- Server: wählbare Ein-/Auslaufseiten, automatischer Auslauf, Aktion `SetMachinePorts`,
  Speicherstand-Reparatur, Baupläne (`MachinePorts.lua`, `PlacementService`, `LogisticsService`).
- Behobener Altfehler: Maschinen und Bänder mit Drehung 90°/270° wurden gespiegelt dargestellt
  (`CFrame.Angles(0, -90°·rot, 0)` statt `+90°·rot`; im Place nachgerechnet).
- Welt: Bänder tragen einen Pfeil in echter Förderrichtung; Maschinen haben Ein-/Auslauf- und
  Rohrmarken an der Anschlusszelle (serverseitig unsichtbar, der Client blendet sie beim Bauen und
  bei offenem Maschinenfenster ein).
- Im Place gemessen: Band mit Drehung 1 → Pfeil (+1, 0); Bandkurve Drehung 0 → Pfeil (−1, 0);
  Auslaufmarke zeigt von der Maschine weg (0,95), Einlaufmarke hinein (−0,95); Marken unsichtbar.
- Client: `MachineWindow.lua` (Zutaten links, Fortschritt Mitte, Ergebnis rechts, Draufsicht der
  Anschlüsse, darunter Rezepte), Bandvorschau startet „rechts aus Spielersicht" und bleibt fest,
  Vorschaupfeile an der Anschlusszelle.

Am Gerät zu prüfen: Aussehen und Bedienung des Maschinenfensters (passt es ohne Scrollen, treffen
die Finger die Seitenknöpfe), Emoji-Symbole, flüssiger Fortschrittsbalken, Bandvorschau aus
mehreren Blickrichtungen, Sichtbarkeit der Marken, Zustand nach Wiederbeitritt.

## Nachtrag 2026-11-16 (11): Materialmodelle und Bilder

- 45 Item-Modelle (`blender/village/items.py`, 36–516 Dreiecke, zusammen rund 10 000), gebaut und
  geprüft mit `blender/build_item_assets.py` (Größe ≤ 1,6 Studs, Dreiecksbudget, Rückseiten-Audit).
- Daraus gerendert: Bildbogen `exports/textures/item_icons.png` (8 × 6 Felder à 128 px), als Decal
  hochgeladen; Bild-ID und Zellen in `ItemIconSheet.lua`. Das Maschinenfenster zeigt diese Bilder
  statt der Emoji-Kacheln (Emoji bleiben Rückfall, falls kein Bild hinterlegt ist).
- Modellbibliothek `arcane_items.fbx` hochgeladen (`ArcaneItemAssets`). `WorkshopWorld` legt auf
  jedes Förderteil das Modell der Ware, die es gerade trägt.
- Im Place gemessen (Version 21): 45 Modelle geladen; auf dem Band liegt `herb_mint` mit Textur,
  0,9 Studs breit; nach Warenwechsel `tonic_minor`; nach dem Weitergeben verschwunden.

Offen: Die Ware springt von Feld zu Feld (ein Schritt je Bandtakt); eine gleitende Bewegung wäre
ein Client-Effekt und ist nicht umgesetzt. Bilder im Beutel und in den Listen nutzen noch Text.
Aussehen am Gerät ungeprüft.

## Nachtrag 2026-11-17: Ware gleitet über die Bänder

- Server: `Game.goodsView` + `WorkshopWorld:syncGoods` veröffentlichen 5×/s je Förderteil
  `GoodsItem`, `GoodsAt`, `GoodsIn` (nur Änderungen); statisch `GoodsRoom`, `GoodsCell`,
  `GoodsSurface`, `GoodsOut`, `GoodsPeriod`. Die Item-Modelle werden nach `ReplicatedStorage.
  ArcaneItemModels` kopiert. Die Laufrichtung beim Auflegen (`inDir`) merkt sich `LogisticsService`.
- Simulation: volle Bänder rücken jetzt im selben Takt vor (D17).
- Client: `GoodsAnimator.client.lua` zeichnet je Ware ein Modell, Positionen aus `GoodsMotion`.
- Lokal gemessen (`spec_goods`: echte Simulation, Updates alle 0,2 s mit 80–200 ms Verzögerung,
  60 Bilder/s): volle Linie mit Kurve 40 s lang – größter Schritt 0,022 Studs je Bild bei
  0,0167 Sollwert, 0 von 8 396 Messpunkten im fahrenden Abschnitt stehend, nie mehr Modelle als
  Ware; blockiert: Schlange steht still, 9 Modelle = 9 Waren; freigegeben: fährt ohne Sprung an.
- Im Place gemessen (Version 23): Attribute korrekt, Auflagehöhe = Bandoberfläche (3,21),
  45 Modelle in ReplicatedStorage, keine servergezeichnete Ware mehr.
- Offen: Aufzug und Magisches Tor übergeben über Etagen bzw. Entfernung – dort verschwindet die
  Ware und taucht am Ziel neu auf. Aussehen am Gerät ungeprüft.

## Nachtrag 2026-11-17 (2): Animationen beim Hinein- und Hinausgehen

- In Maschinen und Kisten: Die Ware rutscht in Bandgeschwindigkeit in die Öffnung, macht einen
  kleinen Hüpfer, sinkt hinein, schrumpft und dreht sich dabei (0,4 s).
- Aus Maschinen und Trichtern: Die Ware steigt aus der Öffnung und wächst auf volle Größe
  (erstes Viertel der Bandzeit).
- Aufzug: hinein bis zur Schachtmitte, eine Etage hoch (weich beschleunigt, halbe Drehung), oben
  heraus aufs Band – ein durchgehendes Objekt.
- Magisches Tor: hinein, schrumpft wirbelnd im Portal, wächst wirbelnd am Partnertor wieder heraus
  und fährt weiter – ein durchgehendes Objekt.
- Server: `GoodsMotion.links` beschreibt je Förderteil Ziel (`GoodsNext`), Steighöhe (`GoodsRise`)
  und Partnertor (`GoodsWarp`, `GoodsWarpOut`); ein Tor wird neu gezeichnet, wenn sein Partner sich
  bewegt.
- Lokal gemessen (`spec_goods`): Aufzug und Tor je 12 von 12 Waren als dasselbe Objekt durch;
  Tor schrumpft bis 2 % und versetzt die Ware nur unsichtbar; Aufzug steigt 12 Studs.
  Schnellste Bewegung: der Aufzugshub, 0,3 Studs je Bild.
- Im Place gemessen (Version 24): Tor-Attribute stimmen (Ziel, Partnerposition, Höhe 3,21).
- Am Gerät ungeprüft.

## Nachtrag 2026-11-17 (3): Förderbänder – Optik und Platzieren

Optik:
- Neue Modelle (`machines.py`): gerades Band mit Holzwangen, Führungsschienen, Messingbeschlägen,
  Rollen und glatter Laufbahn; Kurve als echter Viertelbogen. Laufbahn auf exakt 0,69 Studs
  (`BELT_TOP`) – im Place gemessen: Ware liegt auf beiden Modellen ohne Abstand auf (0,000).
- Kein großer Pfeil mehr auf Bändern; die Richtung zeigen mitlaufende Querstege (Client,
  `GoodsAnimator`, 4 je Band, nur im Umkreis von 70 Studs) und Messingmarken an den Seitenwangen.
- Ware und Querstege fahren in Kurven einen Viertelbogen (`GoodsMotion.pathPoint`) – auch an Bändern,
  die Ware von der Seite aufnehmen. Bewegungstests unverändert ohne Halt und Sprung.

Platzieren (`BeltPath.lua`, Aktion `PlaceBelts`):
- Holzförderband wird als Strecke gebaut: Anfang und Ende wählen (PC: ziehen; Handy: antippen,
  antippen, ✓), höchstens eine Ecke, jedes Band zeigt zum nächsten. ⟳ kehrt die Richtung der
  Strecke um, X verwirft sie. Ein einzelnes Band startet weiter „nach rechts aus Spielersicht".
- Vorschau: je Feld Kasten + Pfeil, rot bei belegt/außerhalb/reserviert; Schild mit Anzahl, Preis,
  „zu teuer", Anschluss am Ende („→ Kräutermühle · Einlauf ✓" bzw. „⚠ hier ist kein Einlauf") und
  am Anfang („← … · Auslauf").
- Server: ganze Strecke oder nichts (`Place.placeLine`), Eingabe geprüft (Typ `cells`, max. 64).
- Lokal getestet: Streckenform, Umkehr, Alles-oder-nichts, Ware läuft durch eine Strecke mit Ecke
  vom Trichter in die Kiste, Rechte und ungültige Eingaben am Server.
- Behoben vor Auslieferung: zwei Client-Funktionen wurden vor ihrer Definition benutzt (hätten zur
  Laufzeit „nil" gesehen); gefunden mit einer Prüfung auf Namensreihenfolge.
- Am Gerät ungeprüft: Bedienung (Ziehen, Tippen), Aussehen der Querstege, Leistung.

## Nachtrag 2026-11-17 (4): Baumodus mit weißem Hologramm

- Vorschau zeigt das echte Modell des Geräts in Weiß (Textur entfernt, SmoothPlastic, leicht
  durchscheinend) mit leuchtendem Umriss (`Highlight`, schwache Füllung, damit die Form lesbar
  bleibt); rot, wenn der Platz belegt, außerhalb oder reserviert ist. Bodenplatte auf den belegten
  Feldern, kurzes Nachgleiten beim Feldwechsel. Ein- und Auslaufpfeile bzw. Flusspfeil bleiben.
- Bandstrecken: jedes Band der Strecke als weißes Hologramm in seiner Richtung, blockierte rot.
- Raster auf dem Boden der aktuellen Etage während des Bauens, reservierte Felder (Eingang, Treppe)
  rot schattiert.
- Eine Regel für beide: `PlacementPose.lua` (Server baut damit, Hologramm stellt sich damit auf).
  Maschinenmodelle werden dafür nach `ReplicatedStorage.ArcaneMachineModels` kopiert.
- Im Place gemessen (Version 26/27): Hologramm und gebautes Teil für Kessel, Mühle, Band, Kurve und
  zwei Tore deckungsgleich (größte Abweichung 0,0000 in Lage, Drehung, Größe); alle sechs mit echtem
  Modell, Textur entfernt; Raster 58 Teile auf 32 × 32 Studs.
- Am Gerät ungeprüft: wie der Leuchteffekt auf dem Handy wirkt. `previews/assets/build_hologram_mockup.png`
  ist eine Annäherung aus Blender, kein Roblox-Bild.
