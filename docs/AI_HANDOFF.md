# KI-Übergabe: Stylized Village (Roblox-Dorf aus Blender)

Dieses Dokument ist eine eigenständige Zusammenfassung für eine andere KI. Es erklärt, was das
Projekt ist, wo was liegt und wie die Teile zusammenhängen. Alles hier Beschriebene existiert im
Repository `juliuslrm/Roblox-Game`, Branch `claude/roblox-village-blender-xekw0z`.

## 1. Worum es geht

- Eine komplette Dorf-Spielwelt für **Roblox**, erzeugt ausschließlich per **Python + Blender-API (`bpy`)**.
- Der Besitzer hatte während der Entwicklung **keinen Zugriff auf Roblox Studio**. Die Welt soll
  später in ein bestehendes Roblox-Spiel importiert werden.
- Stil: stilisiertes Low-Poly-Fachwerkdorf, flach schattiert, eine gemeinsame Farbpalette.

## 2. Zahlen

| Was | Wert |
|---|---|
| Wiederverwendbare Assets | 91 (18 Häuser, 7 Orientierungsbauten, 33 Natur, 33 Deko) |
| Weltspezifische Meshes | 50 (36 Geländekacheln, 11 Straßen, Platzpflaster, Uferband, Wasser) |
| Platzierte Instanzen | 1 889 |
| Dreiecke gesamt | ca. 602 000 (davon ca. 340 000 Vegetation) |
| Größtes Einzelmesh | knapp unter 10 000 Dreiecke (selbst gesetztes Limit) |
| Weltgröße | 768 × 768 Studs, Geländehöhe ca. −6 bis +36 Studs |

## 3. Wichtigste Regeln (bitte nicht verletzen)

1. **Maßstab:** 1 Blender-Einheit = 1 Roblox-Stud.
2. **Koordinaten:** Blender `(x, y, z)` → Roblox `(x, z, −y)`. Drehung um Blender-Z um Winkel a =
   Drehung um Roblox-Y um a: `CFrame.new(pos) * CFrame.Angles(0, math.rad(a), 0)`.
3. **Asset-Ursprung:** Bodenkontaktpunkt in der Mitte der Grundfläche. Vorderseite (Haustür) zeigt
   nach Blender −Y = Roblox +Z. Fundamente reichen 4 Studs unter den Ursprung.
4. **Ein Material, eine Textur:** Alle Meshes nutzen `exports/textures/village_palette.png`
   (1024 × 64 px, 64 Farbspalten à 16 px). U wählt die Farbe, V den Helligkeitston. Keine
   Vertexfarben. Die Reihenfolge der Farben in `palette.COLORS` nie ändern, nur anhängen.
5. **Roblox zeichnet keine Rückseiten.** Jedes Teil muss ein geschlossener, nach außen gewickelter
   Körper sein. `MeshBuilder.add(closed=True)` prüft das automatisch.
6. **Alles ist generiert.** Nie `.glb`, `.blend`, `world_layout.json`, `WorldLayout.lua` oder
   `WorldHeightmap.lua` von Hand ändern, sondern den Python-Code ändern und neu bauen.
7. **Luau nur im Lua-5.1-Teilumfang** (keine Typannotationen, kein `continue`, kein `+=`), damit
   die Skripte außerhalb von Roblox testbar bleiben.

## 4. Ordner

| Pfad | Inhalt |
|---|---|
| `blender/` | Einstiegsskripte + Paket `village/` |
| `assets/houses`, `assets/landmarks`, `assets/nature`, `assets/props` | eine `.blend`-Quelldatei pro Asset |
| `world/` | Levelplan, Höhenkarte, Lageplan, zusammengesetzte Szene |
| `exports/glb/<kategorie>/` | ein `.glb` pro Asset |
| `exports/library/` | Sammeldateien für den Roblox-Import |
| `exports/textures/` | die Palettentextur |
| `previews/world`, `previews/assets` | gerenderte Bilder |
| `roblox/` | Luau-Module |
| `tests/` | Roblox-API-Mock + Tests |
| `docs/` | Dokumentation |

## 5. Dateien im Detail

### Einstiegsskripte (`blender/`)

| Datei | Aufgabe | Erzeugt |
|---|---|---|
| `build_assets.py` | baut alle 91 Assets | `assets/**.blend`, `exports/glb/**`, `exports/library/village_assets.glb/.fbx`, `world/asset_manifest.json` |
| `build_world.py` | berechnet Gelände + Levelplan, setzt die Welt zusammen | `world/world_layout.json`, `world/heightmap.json`, `world/level_plan.png`, `world/level_summary.md`, `world/village_world.blend`, `exports/glb/terrain/**`, `exports/library/village_terrain.glb/.fbx`, `roblox/WorldLayout.lua`, `roblox/WorldHeightmap.lua` |
| `render_previews.py` | rendert Vorschauen (`world`, `assets`, `hero`) | `previews/**` |
| `audit_backfaces.py` | sucht nach innen gewickelte Flächen | `world/backface_audit.json` |
| `validate.py` | 34 automatische Prüfungen | `docs/validation_report.md` |

### Paket `blender/village/`

| Modul | Aufgabe |
|---|---|
| `palette.py` | Farbliste, schreibt die Textur, liefert UVs je Farbe |
| `meshkit.py` | `MeshBuilder`: Box, Balken, Loft, Rotationskörper, Blob, Fläche; Transformstapel; Kollisions-Proxys; Lichtanker |
| `building.py` | Architektur-Baukasten: `Wing` (Gebäudeflügel), Geschosse, Fachwerk, Fenster, Türen, Dächer, Gauben, Schornsteine, Anbauten |
| `houses.py` | 18 Hausrezepte, Dictionary `HOUSES` |
| `landmarks.py` | 7 Orientierungsbauten, Dictionary `LANDMARKS` |
| `nature.py` | Bäume, Büsche, Felsen, Blumen, Dictionary `NATURE` |
| `props.py` | Dekorationen, Dictionary `PROPS` |
| `registry.py` | alle Assets + Dreiecksbudgets + feste Seeds |
| `terrain.py` | Höhenmodell, Kurven, Distanzfelder (nur numpy) |
| `plan.py` | **der Levelplan**: Tabellen `ROADS`, `STREAM_PTS`, `ALONG`, `SITES` + Platzierungsregeln |
| `worldmesh.py` | Geländekacheln, Straßenbänder, Platz, Wasser, Ufer |
| `planmap.py` | zeichnet den 2D-Lageplan |
| `coords.py` | Blender ↔ Roblox Umrechnung |
| `export.py` | GLB/FBX/.blend-Export, Manifest-Eintrag |
| `luadata.py` | Python → Luau-Tabelle, Höhenkarten-Kodierung |
| `scene.py` | Kamera, Licht, Render-Einstellungen |

### Roblox (`roblox/`)

| Datei | Art | Aufgabe |
|---|---|---|
| `VillageWorldBuilder.lua` | handgeschrieben | setzt die Welt aus importierten Meshes zusammen |
| `WorldLayout.lua` | **generiert** | Layout-Daten als Luau-Tabelle |
| `WorldHeightmap.lua` | **generiert** | Höhenkarte (optional) |
| `VillageTerrainBuilder.lua` | handgeschrieben, optional | schreibt das Gelände als Roblox-Voxel-Terrain |
| `BuildVillage.commandbar.lua` | Snippet | zum Einfügen in die Studio-Befehlsleiste |

`default.project.json` im Wurzelverzeichnis ist die Rojo-Konfiguration dafür.

## 6. Datenformate

### `world/world_layout.json`

```json
{
  "meta":     { "units": "...", "world_size": 768, "coordinate_systems": { ... }, "counts": { ... } },
  "spawn":    { "blender": [x, y, z], "roblox": [x, y, z] },
  "lighting": { ... },
  "terrain":  { "cell": 4, "vertices_per_side": 193, ... },
  "roads":    [ { "id": "south_road", "name": "...", "kind": "main|lane|path", "half_width": 7, "points_roblox": [[x,y,z], ...] } ],
  "water":    { "points_roblox": [...], "half_width": [...] },
  "assets":   { "<asset_id>": { "category": "houses|landmarks|nature|props|terrain",
                                "triangles": 0, "collision": "proxy|mesh|mesh_precise|none",
                                "bounds_blender": { "min": [], "max": [] },
                                "bounds_roblox":  { "min": [], "max": [], "size": [], "center": [] },
                                "colliders": [ { "shape": "box|cylinder", ... } ],
                                "lights":    [ { "position": [], "color": [], "brightness": 1, "range": 22 } ] } },
  "instances": [ { "id": "house_01_timber_cottage#1", "asset": "house_01_timber_cottage",
                   "group": "buildings", "name": "Fachwerkhaus am Markt",
                   "blender": { "location": [x, y, z], "rotation_z_deg": 112.3, "scale": 1 },
                   "roblox":  { "position": [x, y, z], "yaw_deg": 112.3, "scale": 1 } } ]
}
```

Gruppen: `terrain`, `roads`, `water`, `buildings`, `props`, `market`, `lights`, `nature`.

### `roblox/WorldLayout.lua`

Gleicher Inhalt, kompakt. Instanzzeile:
`{ assetIndex, x, y, z, yawDegrees, scale, groupIndex [, displayName] }`
mit `assetNames[assetIndex]` und `groupNames[groupIndex]`.

### Kollisionsmodi

| Modus | Bedeutung |
|---|---|
| `proxy` | Mesh kollidiert nicht, Builder legt unsichtbare Boxen/Zylinder an (Häuser, Bäume, Zäune) |
| `mesh` | Mesh kollidiert mit Standardgenauigkeit (Felsen, Fässer) |
| `mesh_precise` | braucht `PreciseConvexDecomposition`, muss in Studio von Hand gesetzt werden (Gelände, Straßen, Brücke) |
| `none` | keine Kollision (Blumen, Gras, Wasser) |

## 7. So funktioniert der Roblox-Builder

```lua
local Builder = require(game.ServerStorage.VillageWorld.VillageWorldBuilder)
local report = Builder.build({
    templates = game.ServerStorage.VillageAssets,          -- importierte Meshes
    layout    = require(game.ServerStorage.VillageWorld.WorldLayout),
    origin    = CFrame.new(0, 0, 0),                       -- ganzes Dorf verschieben/drehen
    -- optional: includeGroups, excludeGroups, createColliders, createLights,
    --           applyLighting, createSpawn, roadLift
})
-- report.placed, report.missing, report.warnings, report.needsPreciseCollision
```

Ablauf pro Asset: Vorlage per Name suchen (MeshPart oder Model, beliebig tief) → Bounding-Box
messen → Importmaßstab = gemessene Größe / Sollgröße → Vorlage auf den geplanten Ursprung
zentrieren und auf Sollmaßstab bringen → Kollisions-Proxys und Lichtanker anlegen → für jede
Instanz klonen und mit `origin * CFrame(pos) * Angles(0, yaw, 0)` platzieren.

Voraussetzung: Meshes sind aufrecht und ungedreht importiert, Namen entsprechen den Asset-IDs.

## 8. Befehle

```bash
./scripts/setup_env.sh                              # .venv mit bpy 5.3.0 (Python 3.13)
./build.sh                                          # alles bauen + prüfen
.venv/bin/python blender/build_assets.py            # nur Assets
.venv/bin/python blender/build_assets.py --only well,bench
.venv/bin/python blender/build_world.py             # nur Welt
.venv/bin/python blender/render_previews.py world --views 03_market_square
.venv/bin/python blender/validate.py
.venv/bin/python tests/test_roblox_builder.py
```

## 9. Typische Änderungen

| Wunsch | Wo ändern | Danach |
|---|---|---|
| Neues Haus | Funktion in `houses.py` + Eintrag in `HOUSES`; Standort in `plan.py` (`ALONG` oder `SITES`) | `build_assets.py`, `build_world.py`, `validate.py` |
| Haus verschieben | `plan.py`, Tabelle `ALONG` (Straße, Abstand, Seite, Rücksprung) oder `SITES` (x, y) | `build_world.py` |
| Straße ändern | `plan.py`, Tabelle `ROADS` (Kontrollpunkte) | `build_world.py` |
| Weniger Bäume | `plan.py`, Funktion `scatter_nature` (`dens`, `step`, `sprinkle`-Zahlen) | `build_world.py` |
| Neue Farbe | `palette.py`, an `COLORS` anhängen | alles neu bauen |
| Hügel ändern | `terrain.py`, Liste `HILLS` | `build_world.py` |

Beispiel für ein Hausrezept:

```python
def house_19_example(mb):
    wg = Wing(mb, 22, 16, found=1.4)
    wg.storey(10, style="stone", openings={
        "front": [door(0.3, arch=True, lantern=1), win(0.75, shutters="cloth_green")]})
    wg.storey(9, style="timber", color="plaster_cream", jetty=1.0,
              openings={"front": wins(2, z=2.8)})
    wg.gable("roof_red", ridge="x", pitch=52, gable_win="round")
    wg.chimney(-5, 2.5)
    finish(mb, wg.z + wg.roof_h)
```

## 10. Aufbau des Dorfs

- Marktplatz im Ursprung mit Brunnen, Marktständen, Rathaus (Norden), Gasthaus (Südosten).
- Vier Hauptstraßen: `south_road` (Dorftor), `north_road` (zur Kapelle auf dem Hügel),
  `west_road` (zur Windmühle, höchster Punkt), `east_road` (über die Steinbrücke zum Osttor).
- Vier Gassen als Verbindungsschleifen, drei Erdpfade (Wachturm, Hof, Bootssteg).
- Bach von Nord nach Süd östlich des Dorfs, weitet sich zum Teich.
- Wald wird zum Kartenrand hin dichter und begrenzt die Welt.
- Norden = Blender +Y = Roblox −Z.

## 11. Stand: geprüft / nicht geprüft

**Geprüft**
- `validate.py`: 34 von 34 Prüfungen bestanden.
- Rückseiten-Audit über alle 141 Meshes ohne Befund (nur einzelne Rauschpixel).
- `VillageWorldBuilder.lua` lief vollständig gegen einen selbst geschriebenen Roblox-API-Mock
  (Lua 5.5 über `lupa`); Abweichung vom Blender-Plan unter 0,001 Studs.

**Nicht geprüft**
- Der tatsächliche Import in Roblox Studio (Annahme von `.glb`, Namen, Textur, Maßstab).
- Ausführung in der echten Roblox-Luau-Laufzeit.
- Das reale Dreieckslimit des Importers (Roblox-Doku war nicht erreichbar).
- Leistung auf Mobilgeräten.
- `VillageTerrainBuilder.lua` in Studio.
- `./build.sh` und `./scripts/setup_env.sh` als Ganzes (nur die Einzelschritte liefen).

**Bekannte Einschränkungen**
- Gebäude sind Außenhüllen ohne Innenräume.
- Zaunsegmente sind starr (8 Studs) und folgen Hängen nur über die Höhe.
- Kein eigener LOD-Satz.

## 12. Nächster Schritt

Import in Roblox Studio nach `docs/ROBLOX_IMPORT.md`, danach `report.warnings` und
`report.missing` des Builders auswerten und bei Bedarf Exportparameter in
`blender/village/export.py` anpassen.

## 13. Welche Dateien man einer KI mitgeben sollte

Reihenfolge nach Nutzen, falls nur wenige Uploads möglich sind:

1. `docs/AI_HANDOFF.md` (diese Datei)
2. `world/level_plan.png` und `previews/world/01_overview_southwest.png` (Bild der Welt)
3. `roblox/VillageWorldBuilder.lua`
4. `blender/village/plan.py`
5. `blender/village/building.py` und `blender/village/meshkit.py`
6. `world/level_summary.md` (Tabelle aller Gebäude mit Koordinaten)
7. `docs/ROBLOX_IMPORT.md`

Nicht hochladen: `world/world_layout.json`, `roblox/WorldLayout.lua`, `roblox/WorldHeightmap.lua`
(groß, generiert, das Format steht oben in Abschnitt 6).
