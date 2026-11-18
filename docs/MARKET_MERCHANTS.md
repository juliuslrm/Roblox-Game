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
- **Halten der Werkzeuge:** Jedes Werkzeug ist in echter Größe gebaut (1 Stud = 0,27 m) und liegt
  wie bei einem Kraftgriff in der Handfläche, der Stiel leicht schräg. Die Finger schließen sich
  Gelenk für Gelenk, bis sie die tatsächliche Werkzeuggeometrie berühren (Abstandsmessung gegen das
  Modell, Daumen von der Gegenseite). Der Build prüft: jeder Finger höchstens 0,025 Studs
  (≈ 7 mm) vom Werkzeug entfernt und nirgends tiefer als 0,02 Studs darin. Korb und Laterne hängen
  an einem breiten Bügel senkrecht unter der Faust; die Arme, die sie tragen, bleiben unten.
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
- **Bewegungsschleifen** (6–8 s, geschlossen): Selma riecht an den Kräutern und legt sie Richtung
  Korb; Nyra hält den Kristall ins Laternenlicht und dreht ihn; Lio poliert die Flasche und hält sie
  gegen das Licht; Aron wiegt das Erz und klopft zweimal mit dem Hammer darauf; Esme trägt die Axt
  auf der Schulter und peilt am Zollstock entlang. Alle atmen leicht. Bewegt werden Wirbelsäule,
  Hals, Kopf, Ober- und Unterarme; die Haut verformt sich an den Gelenken weich mit.

## Dateien und Aufbau

- `blender/village/human.py`: MakeHuman-Daten laden, Formen mischen, Skelett reduzieren,
  Linear Blend Skinning.
- `blender/village/characters.py`: Figuren je Händler, Ruhepose, Greif-Löser, Montage und
  Bewegungsschleifen.
- `blender/village/props.py`: Werkzeuge in echter Größe.
- `blender/village/wardrobe.py`, `outfits.py`: Kleidungstechnik und die Outfits.
- `blender/village/heads.py`, `looks.py`: Augen, Haare, Bärte, Hüte, Kapuze, Brille.
- `blender/build_characters.py` baut alles, backt die Texturen, prüft und schreibt:
  - `exports/library/trader_<rolle>.fbx`: Rig, Meshes und Texturen, je ein Roblox-Asset.
  - `exports/textures/traders/*.png`.
  - `roblox/gameplay/server/TraderArt.lua`: Meshes, Höhe und Referenzposen.
  - `roblox/gameplay/shared/MarketMotion.lua`: lokale Knochenrotationen, 8 Bilder pro Sekunde.
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

Im Place gemessen (Version 30, `scripts/roblox_verify_server.py`):
- Je Händler 9 Meshes, alle skinned und texturiert, und 26 Knochen. Die Füße stehen auf dem Boden.
- Höhen 6,41–6,76 Studs, Gesamtdreiecke 88 000–100 000 je Figur.
- Der Server stellt die Schleife mit derselben Formel wie der Client für mehrere Zeitpunkte nach.
  Die Handgelenke liegen dabei höchstens 0,0005 Studs neben den in Blender berechneten Positionen.

Nicht gesehen: die laufende Animation und die Hautverformung auf einem echten Gerät. Die
Hautverformung rechnet Roblox nur beim Rendern, auf dem Server lässt sie sich nicht messen.
