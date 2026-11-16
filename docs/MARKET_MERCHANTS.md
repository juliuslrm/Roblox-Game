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

## Dateien und Aufbau

- `assets/market/ArcaneVillage_Market.blend` enthält drei editierbare Szenen
  mit Händlerübersicht, Dorfplatz und Exportmodellen. Die verwendeten Bilder
  sind in der Datei gepackt.
- `exports/glb/market/ArcaneMarket.glb` enthält alle fünf Figuren und Stände.
  Die fünf `merchant_*.glb` erlauben Einzelimporte.
- `previews/market/` enthält die Händlerübersicht, Marktansicht und Nahaufnahme der Standanimation mit allen fünf Griffen als MP4.
- `roblox/gameplay/shared/MarketCatalog.lua` definiert Waren, Preise und
  Marktpositionen. Die Standorte leiten sich aus `WorldLayout.lua` ab.
- `blender/build_market.py` reproduziert die Modelle, Render und Roblox-Maße.
  Benötigt die vorhandenen Dorfexporte und `lupa`.

```bash
blender -b --python-use-system-env --python-exit-code 1 -P blender/build_market.py
```

`-- --no-render` erstellt die Modelle und Blender-Datei ohne neue PNGs.
Die Platzierung nutzt 1 Blender-Einheit je Stud, Bodenpivot und die
Dorf-Achsen Blender −Y / Roblox +Z. Die Figuren sind stationäre Händler
mit erwachsenen Körperproportionen, geformten Gesichtern und abgerundeter
Kleidung. Ihre Grundhöhe liegt bei etwa sieben bis siebeneinhalb Kopfhöhen.
Die achtsekündigen Standanimationen lassen Selma Kräuter sortieren, Nyra
einen Kristall im Laternenlicht drehen, Lio seine Phiole am Blasrohr prüfen,
Aron den Hammer absenken und nicken und Esme ihr Maß anheben. Esme hält
die Axt seitlich mit der Schneide nach unten und greift das Klappmaß
am schmalen Anfang. Nyra fasst den Kristall am schmalen Ende. Lios
linke Hand folgt dem Griffpunkt auf dem Blasrohr über den gesamten Loop.
Handfläche und Finger richten sich an Griff und Unterarm aus. Die
Manschetten verformen sich am Übergang zum Handgelenk.

Jede Figur hat ein Skelett mit einem Root-Bone, einem Kopf-Bone und je
drei Bones für Oberarm, Unterarm und Hand. Der Generator berechnet die
Ellbogenposition per Zwei-Knochen-IK und schreibt die Posen als Keyframes
in die Blender-Timeline. In den beiden Vorschauszenen lassen sich die
Werkzeuge als eigene Objekte bearbeiten. Im GLB liegen Körper und Requisiten
in einem skinned Mesh. Jeder Griff ist vollständig an den zugehörigen
Hand-Bone gewichtet. Füße, Stand und Handelspunkt bleiben am Platz.

Die GLBs enthalten die gebackenen Animationen. Das Projekt spielt dieselben
Keyframes beim Händler über `MarketIdle.client.lua` und `Bone.Transform`
ab. Dafür braucht der Spielstand keine hochgeladenen Animations-IDs.

## Roblox Studio

1. `exports/roblox/ArcaneVillage.rbxlx` öffnen oder mit Rojo synchronisieren.
2. In ServerStorage den Ordner `ArcaneMarketAssets` anlegen.
3. `ArcaneMarket.glb` über den 3D Importer mit **Import Only As Model** und
   **Rig Type: Custom** importieren. **Merge Meshes** ausgeschaltet lassen.
   Das importierte Modell in `ArcaneMarketAssets` verschieben und beim Upgrade die frühere Gruppe
   aus dem Ordner entfernen. Die Figur muss als skinned MeshPart
   (z. B. `merchant_esme`) mit Bone-Hierarchie (beginnend mit `root`)
   vorliegen. Die Stände heißen z. B. `stall_esme`. Für den direkten
   Einsatz der importierten Clips über einen `Animator` müssten die Clips
   in Studio separat veröffentlicht werden.
4. Play starten. Die Stände nutzen die fünf vorgesehenen Plätze. Bei fehlenden
   Importen nutzt das Spiel vereinfachte runde Ersatzfiguren.
   Über **Handeln** lassen sich der Katalog und die verfügbaren Waren öffnen.
5. Für den Test Minze bei Selma kaufen, dann Beutel und Münzen kontrollieren.
   Ein Kauf entfernt nur den im Katalog gespeicherten Betrag und wird im
   bestehenden Profil gesichert.

Lokal geprüft werden Zutatenabdeckung, Marktpositionen, Bündelgrößen,
Freischaltungen, Distanz, Inventar, Münzen, doppelte Anfragen und Profilrundlauf.
Die Werkzeugmeshes wurden in Blender Frame für Frame gegen die Körper- und
Kopfmeshes geprüft.
In Roblox Studio stehen der GLB-Import mit der echten Roblox-Runtime,
das Abspielen der Standanimationen, die Abstände an den Ständen und der Handel auf einem Touchgerät zur Prüfung aus.
