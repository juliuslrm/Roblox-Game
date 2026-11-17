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

## Figuren (Fassung vom 2026-11-17, realistisch)

Die Händler haben realistische Proportionen (rund 7,5 Kopfhöhen, 6,3–6,9 Studs groß) und bestehen
weiterhin aus sieben starren Teilen je Figur, die sich in Kugelgelenken drehen (kein Skelett, kein
Skinning). Jede Figur hat rund 16 600–18 500 Dreiecke, kein Teil mehr als 9 500:

| Teil | Inhalt | Gelenk |
|---|---|---|
| `lower` | Hüfte, Beine, Stiefel mit Sohle, Absatz und Schnürung bzw. Schnalle; Rock mit Falten bzw. Hose, Tunika, Kniebschurz | fest |
| `torso` | Oberkörper mit Kragen, Knopfleiste, Gürtel, Tasche; Schürzenlatz, Weste, Schnürung, Umhang je Rolle | Taille |
| `head` | modellierter Schädel mit Nase, Brauenbogen, Augenhöhlen, Wangen, Lippen und Kinn; Ohren, Haare, Hut, Kapuze, Bart | Hals |
| `upper_l`, `upper_r` | Oberarm mit Schultermuskel, Ärmel (bei Aron hochgekrempelt) | Schulter |
| `fore_l`, `fore_r` | Unterarm, Hand, Werkzeug | Ellbogen |

- **Gesicht:** Augäpfel mit Iris, Pupille, Glanzpunkt und Lidern, Brauen mit eigenem Ausdruck,
  Lippen als eigene Wülste mit Mundlinie, Ohren mit Muschel; Frauen- und Männerkopf unterscheiden
  sich in Kiefer, Brauenbogen und Lippen.
- **Hände:** Handfläche, vier Finger mit je drei Gliedern und Nägeln, Daumen; um den Werkzeuggriff
  gekrümmt. Werkzeuge sind auf Handgröße skaliert.
- **In der Hand:** Selma Kräuterzweig und Korb, Nyra Kristall und Laterne, Lio Phiole und Poliertuch,
  Aron Hammer und Erzbrocken, Esme Axt und Zollstock. Korb und Laterne hängen bei vorgestrecktem
  Unterarm senkrecht.
- **Bewegungsschleifen** (6–8 s, weich überblendet, geschlossen): Selma riecht am Zweig und legt
  ihn zum Korb; Nyra hebt die Laterne und dreht den Kristall in ihrem Licht; Lio poliert die Phiole
  und hält sie gegen das Licht; Aron wiegt das Erz und klopft zweimal mit dem Hammer darauf; Esme
  trägt die Axt auf der Schulter und peilt am Zollstock entlang.

## Dateien und Aufbau

- `blender/village/merchants.py` – Figuren, Werkzeuge und Schleifen (Gelenkwinkel als Keyframes).
- `blender/village/market.py` – Marktstände und Auslagen.
- `blender/build_merchants.py` – baut alles, prüft und schreibt:
  `exports/glb/market/*.glb`, `exports/library/arcane_market.{glb,fbx}`,
  `assets/market/arcane_market.blend`, `roblox/gameplay/server/MarketArt.lua` (Maße, Gelenke),
  `roblox/gameplay/shared/MarketMotion.lua` (Schleifen, 8 Bilder pro Sekunde als Gelenkrahmen),
  `previews/market/01-haendler.png`, `02-bewegung.png`.
- `roblox/gameplay/server/MarketWorld.lua` stellt Stand und Figur auf (Ruhepose),
  `roblox/gameplay/client/MarketIdle.client.lua` spielt die Schleife auf jedem Client ab:
  `Teil = Standpunkt * Rahmen(t) * CFrame.new(-Gelenk) * Ruhelage`.

Prüfungen beim Bauen: Katalog gegen Spieldaten, Dreiecksbudget (≤ 32 000 je Figur, ≤ 9 500 je Teil), Rückseiten-Audit,
Schleifen ohne Sprung, und die exportierten Roblox-Rahmen ergeben dieselben Posen wie Blender
(Abweichung 0,0001 Studs).

## In Roblox

Die Bibliothek `arcane_market.fbx` ist als Asset hochgeladen (ID in `roblox/VillageAssetIds.lua`) und
wird beim Serverstart nach `ServerStorage.ArcaneMarketAssets` geladen. Fehlt ein Teil, erscheint eine
einfache Ersatzfigur.

Im Place gemessen (Version 28, neue Figuren): fünf Figuren mit je sieben texturierten Teilen, Füße auf dem Boden,
Höhen wie in Blender; die Schleifendaten ergeben dort Handwege von 0,7 bis 4,8 Studs pro Durchlauf.
Nicht gesehen: die laufende Animation und das Aussehen auf einem Gerät.
