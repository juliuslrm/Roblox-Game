# Händler am Marktplatz

Für die Trankbrauerei, Versorgung und Verzauberung gibt es 15 Grundressourcen
inklusive Wasser und Holzkohle. Alle 15 sind bereits an erneuerbaren Sammelpunkten
verfügbar. Die Kaufangebote verkürzen den Weg zwischen Sammlung und Werkstatt.
Die fünf Händler übernehmen die vorhandenen Marktstände am Brunnen.

| NPC | Beruf und Gestaltung | Sortiment |
|---|---|---|
| **Selma Wurzelbund** | Kräuterhexe mit Mooshut, Schürze, Samentasche und Kräuterkorb | Minze, Sonnenblatt, Rote Beeren, Minzsaat, Sonnenblattsaat |
| **Nyra Dämmerhut** | Nachtsammlerin mit pflaumenfarbenem Mantel, Mondbrosche und Laterne | Dämmerpilz, Mondblatt, Rohkristall |
| **Lio Glasfunke** | Glasbläser mit Messingbrille, Fläschchen an der Schürze und Blasrohr | Sand und leere Phiolen |
| **Aron Glutbart** | Erz- und Kohlehändler mit breiter Lederschürze, Schmiedehammer und Bartspangen | Holzkohle, Kupfererz, Eisenerz |
| **Esme Eichenmaß** | Holz- und Steinlieferantin mit Federhut, Winkelmaß und Beil | Holzscheite und Stein |

## Waren und Freischaltungen

| Händler | Bündel | Münzen | Freischaltung |
|---|---|---:|---|
| Selma | 2 × Minze | 26 | Start |
| Selma | 2 × Sonnenblatt | 32 | Start |
| Selma | 2 × Rote Beere | 48 | Handwerk |
| Selma | 1 × Minzsaat | 24 | Kräuteranbau |
| Selma | 1 × Sonnenblattsaat | 29 | Kräuteranbau |
| Nyra | 1 × Dämmerpilz | 32 | Start |
| Nyra | 1 × Rohkristall | 58 | Runenkunde |
| Nyra | 2 × Mondblatt | 44 | Mondbotanik |
| Lio | 4 × Sand | 20 | Handwerk |
| Lio | 4 × Phiole | 32 | Glashütte |
| Aron | 4 × Holzkohle | 24 | Handwerk |
| Aron | 2 × Kupfererz | 34 | Nach Hauptauftrag q11 |
| Aron | 2 × Eisenerz | 42 | Nach Hauptauftrag q11 |
| Esme | 2 × Holzscheit | 18 | Handwerk |
| Esme | 4 × Stein | 20 | Handwerk |

**Wasser** bleibt kostenlos am Marktbrunnen, Steg und an der Brücke.
Ein eigener Brunnen in der Werkstatt kann es später automatisch fördern.
**Phiolen** sind das einzige kaufbare Zwischenprodukt. Damit kann die
Abfüllanlage laufen, bevor der Spieler eine eigene Glaslinie aufgebaut hat.
Glas, Pulver, Extrakte, Barren und Runenrohlinge entstehen in der Werkstatt.
Die 14 verkaufbaren Produkte verdienen Münzen im Spielerregal und in Aufträgen.
Kaufbündel haben feste Startpreise. Die Freischaltungen der 14 Rohwaren
entsprechen ihren Sammelpunkten.

## Figuren (Fassung vom 2026-11-18: realistische Charaktere mit Skelett)

Die Händler sind keine Gliederfiguren mehr, sondern realistische Menschen mit verformbarer Haut
(Skinned Meshes) an einem Skelett, so wie Figuren in aktuellen Spielen gebaut werden.

- **Körper:** Basis ist das MakeHuman-Grundmodell (Assets unter CC0, Daten in
  `assets/thirdparty/makehuman`, siehe dortige `LICENSE.md`). Eigener Code mischt die Makro-Formen
  (Geschlecht, Alter, Muskeln, Gewicht, Herkunft) je Figur: Selma (≈ 40 J.), Nyra (≈ 60 J., schlank),
  Lio (≈ 22 J.), Aron (≈ 43 J., kräftig), Esme (≈ 33 J., sportlich). Ruhepose: Arme hängend,
  Ellbogen leicht gebeugt, Schultern entspannt, Füße zusammen.
- **Halten der Werkzeuge:** Jedes Werkzeug ist in echter Größe gebaut (1 Stud = 0,27 m). Für vier
  Lagen des Griffs in der Handfläche sucht jeder Finger die Winkel seiner drei Gelenke, bei denen
  möglichst viele seiner Glieder den Griff berühren (Mittel- und Endglied zählen mehr). Ausgeschlossen
  sind Stellungen, in denen ein Glied in den Griff oder in die eigene Handfläche eindringt. Die Lage
  mit der besten Umschließung gewinnt; danach schließt der Daumen von der Gegenseite. Gemessen wird
  gegen die tatsächliche Werkzeuggeometrie. Der Build prüft: Jeder Finger berührt den Griff mit
  mindestens zwei Gliedern und steckt nirgends tiefer als 0,02 Studs darin. Korb und Laterne hängen
  an einem Bügel senkrecht unter der Hand (Hakengriff); die Arme, die sie tragen, bleiben unten.
- **Kleidung:** Anliegende Teile (Hemden, Kleider, Hosen, Westen, Latz) sind die Körperoberfläche,
  nach außen versetzt, mit Falten an Ellbogen, Knien und Taille, Saumdicke und glatten Schnittkanten.
  Stoff überbrückt Mulden und fällt vom breitesten Punkt (z. B. der Brust) nach unten. Röcke,
  Schürzen und Umhang folgen den gemessenen Körperquerschnitten. Stiefel sind über einem Leisten
  aufgebaut: Zehenkappe, Spann, Schaft, Rahmen und Sohle. Verdeckte Haut wird entfernt.
- **Kopf:** Augäpfel mit Iris, Pupille und dunklem Irisrand; Wimpern; Brauen aus einzelnen Härchen.
  Haare bestehen aus einer Haarkappe und hunderten Strähnen, die am Kopf entlang wachsen: Selma
  Zöpfe unter dem Spitzhut, Nyra silbernes langes Haar unter der Kapuze, Lio Locken mit
  Schutzbrille, Aron kurzes Haar mit Vollbart und Schiebermütze, Esme Pferdeschwanz unter dem
  Federhut.
- **Texturen:** Jedes Mesh hat eine eigene, in Blender gebackene Textur: Farbe mal Struktur (Gewebe,
  Leder, Filz, Hautporen, Haarsträhnen) mal Umgebungsverdeckung (Ambient Occlusion).
- **Griffprofile** (`blender/village/grips.py`): Je Gegenstand Grifftyp (Kraft-, Haken-, Bündel-,
  Kugel-, Spitzgriff), erlaubter Griffbereich und verbotene Teile (Korken und Hals der Flasche,
  Hammer- und Axtkopf, Kristallspitze, Blüten). Die Flasche wird am Körper gehalten, der Korken
  zeigt zur Daumenseite und steht damit oben.
- **Bewegungsschleifen** (6–8 s, geschlossen): Selma riecht an den Kräutern und legt sie Richtung
  Korb; Nyra hält den Kristall vor die Brust und dreht ihn; Lio poliert die Flasche vor dem Bauch
  und hält sie seitlich auf Augenhöhe gegen das Licht; Aron hält das Erz vor dem Bauch und trifft es
  zweimal mit der Hammerfläche; Esme trägt die Axt mit dem Stiel auf der rechten Schulter und peilt am
  Zollstock entlang. Bewegt werden Wirbelsäule, Hals, Kopf, Ober- und Unterarme und die
  Handgelenke.
- **Armhaltungen per IK** (`blender/solve_poses.py`, `blender/village/armik.py`): Die Armwinkel
  der Haltungen mit Gegenstand sind nicht geschätzt, sondern gelöst: Zielposition des Gegenstands,
  Gelenkgrenzen, Abstand zum Körper, Handgelenk höchstens 45° gebeugt / 20° seitlich / 20° in sich
  verdreht, Unterarmdrehung höchstens 80°. Drehen eines Gegenstands in der Hand ist eine gelöste
  Unterarmdrehung (ein Schlüssel auf einem Euler-Kanal würde den gebeugten Unterarm seitlich
  schwenken). Arons Schlag ist ein Pfad aus acht gelösten Haltungen entlang der Schlaglinie, eine je
  Animationsbild, damit der Kopf nie durch das Erz fährt. Ergebnis: `world/solved_poses.json`.
- **Griffprüfung:** `blender/validate_grips.py` misst jeden Griff über die ganze Schleife (Kontakt,
  Durchdringung, Griffbereich, Gelenke, Verrutschen, Sprünge), rendert je Griff 14 Ansichten nach
  `previews/grips/after/` und schreibt `docs/GRIP_VALIDATION_REPORT.md`. Der schnelle Teil
  (Profile, geschlossene Schleifen, Handgelenkgrenzen) läuft in `scripts/check_all.sh`
  (`tests/test_grip_profiles.py`). Diagnose des alten Zustands: `docs/GRIP_DIAGNOSIS.md`.

## Dateien und Aufbau

- `blender/village/human.py`: MakeHuman-Daten laden, Formen mischen, Skelett reduzieren,
  Linear Blend Skinning.
- `blender/village/characters.py`: Figuren je Händler, Ruhepose, Greif-Löser, Montage und
  Bewegungsschleifen.
- `blender/village/handheld.py`: Werkzeuge in echter Größe (`props.py` enthält die Dorf-Requisiten).
- `blender/village/grips.py`, `gripcheck.py`, `armik.py`: Griffprofile, Griffmessung, Arm-IK.
- `blender/village/wardrobe.py`, `outfits.py`: Kleidungstechnik und die Outfits.
- `blender/village/heads.py`, `looks.py`: Augen, Haare, Bärte, Hüte, Kapuze, Brille.
- `blender/build_characters.py` baut alles, backt die Texturen, prüft und schreibt:
  - `exports/library/trader_<rolle>.fbx`: Rig, Meshes und Texturen, je ein Roblox-Asset.
  - `exports/textures/traders/*.png`.
  - `roblox/gameplay/server/TraderArt.lua`: Meshes, Höhe und Referenzposen.
  - `roblox/gameplay/shared/MarketMotion.lua`: lokale Knochenrotationen (10 Knochen inkl.
    Handgelenke), 8 Bilder pro Sekunde.
  - `previews/market/01-haendler.png`, `02-bewegung.png`, `03-haende.png`.
- `blender/build_merchants.py` baut die Marktstände und prüft den Katalog.
- `roblox/gameplay/server/MarketWorld.lua` klont das Rig an den Stand und verankert es.
  `roblox/gameplay/client/MarketIdle.client.lua` setzt auf jedem Client `Bone.Transform` nach der
  Formel `Ruhe⁻¹ · Figur · q · Figur⁻¹ · Ruhe`. Diese Formel hängt nicht davon ab, wie der Importer
  die Knochen ausrichtet.

Prüfungen beim Bauen:
- Griffe: jeder Finger am Werkzeug.
- Höchstens 19 500 Dreiecke je Mesh (Roblox-Grenze 20 000).
- Höchstens 4 Knochen je Vertex.
- Schleifen ohne Sprung.
- Werkzeuge dringen während der Schleife nicht in den Körper ein.

## In Roblox

Jeder Händler ist ein eigenes Modell-Asset (IDs in `roblox/VillageAssetIds.lua`, Ordner
`ArcaneMarketAssets`). Beim Serverstart wird es nach `ServerStorage.ArcaneMarketAssets` geladen.
Fehlt ein Rig, erscheint eine einfache Ersatzfigur.

Im Place gemessen (Version 32, `scripts/roblox_verify_server.py`):
- Je Händler 9 Meshes, alle skinned und texturiert, und 26 Knochen. Die Füße stehen auf dem Boden.
- Höhen 6,41–6,76 Studs, Gesamtdreiecke 88 000–100 000 je Figur.
- Der Server stellt die Schleife mit derselben Formel wie der Client für mehrere Zeitpunkte nach.
  Die Handgelenke (jetzt selbst animiert) liegen dabei höchstens 0,0005 Studs neben den in Blender
  berechneten Positionen.

Nicht gesehen: die laufende Animation und die Hautverformung auf einem echten Gerät. Die
Hautverformung rechnet Roblox nur beim Rendern, auf dem Server lässt sie sich nicht messen.
