# Import in Roblox Studio

> **Wichtig:** Diese Anleitung wurde ohne Zugriff auf Roblox Studio geschrieben. Die Dateien sind
> auf Formatebene geprüft und die Skripte gegen einen API-Mock getestet, aber der Import selbst
> wurde nicht ausgeführt. Die Punkte unter [Beim ersten Import kontrollieren](#beim-ersten-import-kontrollieren)
> sind deshalb ernst gemeint.

## 1. Meshes importieren

Es gibt zwei gleichwertige Sammeldateien, jeweils als glTF-Binary und als FBX:

| Datei | Inhalt |
|---|---|
| `exports/library/village_assets.glb` / `.fbx` | 91 wiederverwendbare Assets, jedes als eigenes, benanntes Mesh |
| `exports/library/village_terrain.glb` / `.fbx` | 36 Geländekacheln, 11 Straßen, Platzpflaster, Uferband, Wasser |

1. In Studio einen Ordner `ServerStorage.VillageAssets` anlegen.
2. *Home → Import 3D* → `village_assets.glb` wählen (falls `.glb` nicht angenommen wird: `.fbx`).
3. Im Importdialog: **nicht** zu einem Mesh zusammenfassen; jedes Objekt muss ein eigenes MeshPart
   mit seinem Namen bleiben (`house_01_timber_cottage`, `tree_oak_a` …). Texturen mitimportieren.
4. Das importierte Model nach `ServerStorage.VillageAssets` verschieben.
5. Dasselbe für `village_terrain`.

Statt der Sammeldateien können auch einzelne Dateien aus `exports/glb/<kategorie>/` importiert
werden; der Builder sucht nur nach dem Namen, egal wie tief verschachtelt.

**Maßstab und Position beim Import sind unkritisch.** Der Builder kennt die Soll-Bounding-Box jedes
Assets, misst das importierte Mesh aus, rechnet den Importmaßstab zurück und legt den Pivot auf den
geplanten Ursprung. Voraussetzung: Die Meshes stehen aufrecht und sind nicht gedreht (Standard bei
diesen Dateien, Y ist oben).

## 2. Skripte einfügen

Nach `ServerStorage.VillageWorld` (Ordner) als **ModuleScripts**:

| Modul | Quelle | Zweck |
|---|---|---|
| `VillageWorldBuilder` | `roblox/VillageWorldBuilder.lua` | setzt die Welt zusammen |
| `WorldLayout` | `roblox/WorldLayout.lua` | generierte Layout-Daten (130 000 Zeichen) |
| `WorldHeightmap` | `roblox/WorldHeightmap.lua` | optional: Höhenkarte für Voxel-Terrain |
| `VillageTerrainBuilder` | `roblox/VillageTerrainBuilder.lua` | optional: schreibt das Gelände als Roblox-Terrain |

Mit [Rojo](https://rojo.space) erledigt das `default.project.json` im Repository-Wurzelverzeichnis.

## 3. Welt aufbauen

Inhalt von `roblox/BuildVillage.commandbar.lua` in die Befehlsleiste (*View → Command Bar*) kopieren
und ausführen. Ergebnis: `Workspace.Village` mit den Unterordnern `terrain`, `roads`, `water`,
`buildings`, `props`, `market`, `lights`, `nature`. Danach den Place speichern – die Welt muss nicht
bei jedem Spielstart neu aufgebaut werden.

Optionen von `Builder.build({...})`:

| Option | Standard | Wirkung |
|---|---|---|
| `origin` | `CFrame.new()` | verschiebt/dreht das ganze Dorf – so passt es in ein bestehendes Spiel |
| `parent`, `name` | `workspace`, `"Village"` | Zielordner |
| `includeGroups` / `excludeGroups` | – | z. B. `{ nature = true }` ausschließen |
| `createColliders` | `true` | unsichtbare Kollisionskörper für Häuser, Bäume, Zäune … |
| `createLights` | `true` | PointLights an Laternen und Fenstern |
| `applyLighting` | `false` | übernimmt die vorgeschlagene Tageslicht-Stimmung |
| `createSpawn` | `false` | SpawnLocation auf dem Marktplatz |
| `roadLift` | `0` | hebt die Straßen an (nur mit Voxel-Terrain nötig) |

Der Rückgabewert enthält `placed`, `missing`, `warnings` und `needsPreciseCollision`.

## 4. Kollision

Jedes Asset hat im Layout einen Kollisionsmodus:

| Modus | Bedeutung | Assets |
|---|---|---|
| `proxy` | Mesh kollidiert nicht; der Builder legt einfache Boxen/Zylinder an | Häuser, Türme, Bäume (nur Stamm – man läuft unter der Krone durch), Zäune, Laternen |
| `mesh` | das Mesh kollidiert mit der Standard-Genauigkeit | Felsen, Fässer, Kisten, Bänke |
| `mesh_precise` | braucht `CollisionFidelity = PreciseConvexDecomposition` | Geländekacheln, Straßen, Platz, Brücke |
| `none` | keine Kollision | Blumen, Gras, Büsche, Wasser, Uferband |

`CollisionFidelity` lässt sich von normalen Skripten nicht setzen. Der Builder versucht es und
listet am Ende, wo es nicht ging. Dann in Studio: Ordner `terrain` und `roads` sowie die Brücke
auswählen und in den Eigenschaften *CollisionFidelity → PreciseConvexDecomposition* einstellen.
Ohne diesen Schritt läuft die Spielfigur nicht sauber auf dem Gelände.

## 5. Alternative: Gelände als Roblox-Terrain

```lua
local scripts = game.ServerStorage.VillageWorld
require(scripts.VillageTerrainBuilder).build({ heightmap = require(scripts.WorldHeightmap) })
require(scripts.VillageWorldBuilder).build({
    templates = game.ServerStorage.VillageAssets,
    layout = require(scripts.WorldLayout),
    excludeGroups = { terrain = true, water = true },
    roadLift = 0.6,
})
```

Vorteil: native Kollision und echtes Wasser. Nachteil: Voxel haben 4 Studs Auflösung und werden
geglättet, die Oberfläche weicht also etwas vom Entwurf ab; der realistische Terrain-Look passt
weniger gut zur Palette. Diese Variante ist nur in der Mock-Umgebung gelaufen.

## Koordinaten und Maßstab

- 1 Blender-Einheit = 1 Stud. Türen sind ca. 4 × 7,4 Studs, ein Geschoss 9–11 Studs.
- Blender `(x, y, z)` → Roblox `(x, z, −y)`. Drehung um Blenders Z-Achse = gleiche Drehung um
  Roblox' Y-Achse: `CFrame.new(pos) * CFrame.Angles(0, math.rad(yaw), 0)`.
- Ursprung jedes Assets = Bodenkontaktpunkt in der Mitte der Grundfläche. Die Vorderseite
  (Haustür) zeigt nach Blender −Y = Roblox +Z.
- Der Dorfplatz liegt im Ursprung; Norden (Kapelle) ist Roblox −Z.

## Beim ersten Import kontrollieren

1. **Format**: Nimmt der Importer `.glb` an? Wenn nicht, `.fbx` verwenden.
2. **Namen**: Heißen die MeshParts wie die Asset-IDs? `Builder.checkTemplates(...)` listet fehlende.
3. **Textur**: Haben die Meshes die Palettentextur? Falls nicht, `exports/textures/village_palette.png`
   hochladen und als `TextureID` aller MeshParts setzen.
4. **Dreieckslimit**: Das größte Mesh hat 9 687 Dreiecke (Gasthaus). Ich habe konservativ auf
   ≤ 10 000 pro Mesh ausgelegt; das tatsächliche Importlimit konnte ich nicht nachschlagen.
5. **Warnungen des Builders**: „proportions differ" bedeutet, dass ein Mesh gedreht oder mit
   anderer Hochachse importiert wurde.
6. **Rückseiten**: Roblox zeichnet nur Vorderseiten. Die Prüfung stellt sicher, dass Normalen und
   Wickelrichtung übereinstimmen; trotzdem einmal um ein Haus und durch das Tor laufen.
7. **Leistung**: 602 000 Dreiecke in der ganzen Welt, davon 340 000 Vegetation. Für Mobilgeräte
   `StreamingEnabled` einschalten; bei Bedarf `excludeGroups = { nature = true }` und die Natur
   ausgedünnt selbst setzen oder die Dichte in `blender/village/plan.py` senken.
