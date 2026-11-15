# Technische Pipeline

## Umgebung

- Blender läuft als Python-Modul: `pip install bpy==5.3.0` (Python 3.13). Kein installiertes
  Blender, keine GPU nötig.
- Gerendert wird mit **Cycles auf der CPU**. EEVEE funktioniert in Containern ohne GPU/EGL nicht.
- Zusätzlich: `numpy` (Gelände), `matplotlib` (Lageplan), `lupa` (Lua-Interpreter für die Tests).
- Einrichtung: `scripts/setup_env.sh`. Das Projekt lässt sich so in jeder Linux-Cloud-Umgebung
  (Codespaces, CI-Runner, VM) neu bauen.

## Aufbau des Codes (`blender/village/`)

| Modul | Aufgabe |
|---|---|
| `palette.py` | Farbpalette, schreibt die Palettentextur, liefert UVs |
| `meshkit.py` | `MeshBuilder`: Primitive (Box, Balken, Loft, Rotationskörper, Blob, Fläche), Transformstapel, Kollisions-Proxys, Lichtanker |
| `building.py` | Architektur-Baukasten: Fundament, Geschosse, Fachwerk, Stein-/Bretterwände, Fenster, Türen, Sattel-/Walm-/Zeltdach, Gauben, Schornsteine, Anbauten |
| `houses.py`, `landmarks.py`, `nature.py`, `props.py` | die Asset-Rezepte, je eine Funktion pro Asset |
| `registry.py` | Liste aller Assets, Dreiecksbudgets, deterministische Seeds |
| `terrain.py` | Höhenmodell, Kurven, Distanzfelder (nur numpy) |
| `plan.py` | **der Levelplan**: Straßen, Bach, Gebäudestandorte, Gärten, Regeln für die Naturverteilung |
| `worldmesh.py` | Geländekacheln, Straßenbänder, Platzpflaster, Wasser, Ufer |
| `planmap.py` | zeichnet `world/level_plan.png` |
| `coords.py`, `export.py`, `luadata.py`, `scene.py` | Koordinatenumrechnung, Exporte, Luau-Serialisierung, Render-Setup |

## Ein Material, eine Textur

Alle Meshes teilen sich das Material `VillagePalette` und die Textur
`exports/textures/village_palette.png` (1024 × 64 px). Jede der 64 Farben belegt einen 16 px breiten
Streifen, der von unten nach oben von einem kühlen Schattenton über die Grundfarbe zu einem warmen
Glanzlicht verläuft. U wählt die Farbe, V den Ton. So entstehen handgemalt wirkende Verläufe
(Wände unten dunkler, Baumkronen oben heller) ohne zusätzliche Texturen.

Folgen für Roblox: ein MeshPart pro Asset, eine Textur für die ganze Welt, keine Vertexfarben
(sie würden mit der Textur multipliziert).

Die Reihenfolge der Farben in `palette.COLORS` darf nur ergänzt, nie umsortiert werden.

## Konventionen für Assets

- Einheiten sind Studs, Z ist oben, der Ursprung liegt am Boden in der Mitte der Grundfläche.
- Die Vorderseite zeigt nach −Y.
- Fundamente reichen 4 Studs unter den Ursprung, damit Häuser am Hang nicht schweben.
- Jedes Primitiv ist ein geschlossener Körper; `MeshBuilder.add(closed=True)` prüft das
  vorzeichenbehaftete Volumen und dreht falsch gewickelte Flächen um. Hintergrund: Roblox zeichnet
  keine Rückseiten, Cycles schon – der Fehler wäre in den Vorschauen unsichtbar.
- Offene Flächen (Fensterglas, Fahnen) werden mit `facing=` ausgerichtet oder mit `double=True`
  doppelseitig angelegt.
- Zufall kommt aus `mb.rng` mit festem Seed pro Asset: jeder Build liefert dieselben Dateien.

## Ein neues Haus anlegen

```python
# blender/village/houses.py
def house_19_example(mb):
    wg = Wing(mb, 22, 16, found=1.4)                       # Grundfläche 22 x 16 Studs
    wg.storey(10, style="stone", openings={
        "front": [door(0.3, arch=True, lantern=1), win(0.75, shutters="cloth_green")]})
    wg.storey(9, style="timber", color="plaster_cream", jetty=1.0, openings={
        "front": wins(2, z=2.8)})
    wg.gable("roof_red", ridge="x", pitch=52, gable_win="round")
    wg.chimney(-5, 2.5)
    finish(mb, wg.z + wg.roof_h)

HOUSES["house_19_example"] = house_19_example
```

Danach in `plan.py` einen Standort eintragen – entweder an einer Straße
(`ALONG`: Asset, Straße, Abstand vom Straßenanfang, Seite, Rücksprung, Name) oder frei (`SITES`) –
und `./build.sh` ausführen. `validate.py` meldet Überschneidungen, Budgetüberschreitungen und
Geometriefehler.

## Wie der Levelplan entsteht (`plan.build_plan`)

1. Grundgelände aus Hügeln, Randanhebung und Rauschen; der Dorfkern wird abgeflacht.
2. Straßen sind Catmull-Rom-Kurven durch handgesetzte Kontrollpunkte. Ihr Höhenprofil ist das
   geglättete Gelände; Enden werden an den Platz oder an kreuzende Straßen angeglichen.
3. Gebäude stehen relativ zu Straßen oder an festen Koordinaten und drehen ihre Tür zur Straße.
   Unter jedem Gebäude wird das Gelände zu einer ebenen Fläche überblendet.
4. Straßen schneiden sich ins Gelände ein, der Bach gräbt sein Bett; sein Wasserspiegel fällt
   monoton von Nord nach Süd. Wo die Bachstraße ihn kreuzt, sitzt die Brücke.
5. Handplatzierte Requisiten (Marktplatz, Gärten, Hof, Mühle), dann regelbasierte Natur:
   Wald am Rand und auf Höhen, Obstgarten, Blumen im Dorf, Felsen an Hängen und Ufern.
6. Alle Höhen stammen aus demselben Raster und derselben Triangulierung wie das Gelände-Mesh,
   deshalb stehen Objekte exakt auf der sichtbaren Oberfläche.

## Prüfungen

`blender/validate.py` (Bericht: `docs/validation_report.md`):

- GLB-Struktur: ein Mesh, ein Primitiv, POSITION/NORMAL/TEXCOORD_0, eingebettete Palette, keine
  Knotentransformation, Knotenname = Asset-ID
- Geometrie: keine NaN, keine Nullflächen-Dreiecke, Einheitsnormalen, Wickelrichtung passt zu den
  Normalen, Indizes gültig
- UVs innerhalb der Textur und mittig auf einem belegten Palettenstreifen
- Dreiecksbudgets je Kategorie und hartes Limit 10 000 pro Mesh
- Maßstab und Ursprung: plausible Höhen/Grundflächen, Bodenkontakt, Manifest = Export
- FBX-Header, `.blend`-Quellen, Sammeldateien vollständig
- Levelplan: eindeutige IDs, Koordinatenumrechnung, keine Gebäudeüberschneidung, kein Gebäude auf
  Straße oder im Wasser, alle Objekte auf dem Gelände, 15–25 Häuser
- Luau: Größenlimit der Skripte, Ausführung gegen den Roblox-Mock

`blender/audit_backfaces.py` (Ergebnis: `world/backface_audit.json`) schließt eine Lücke, die
weder Vorschauen noch Formatprüfungen abdecken: Roblox zeichnet nur Vorderseiten, Cycles beide.
Der Audit rendert jedes Asset aus zehn Richtungen mit einem Diagnosematerial (Vorderseiten weiß,
Rückseiten magenta) und zählt magentafarbene Pixel. Bodenmeshes werden nur von oben betrachtet.
Einzelne Pixel an Kanten gelten als Abtastrauschen (Grenze: 8 Pixel bzw. 0,01 % der Fläche).

`tests/test_roblox_builder.py` führt `VillageWorldBuilder` mit simulierten Importen aus
(verschiedene Maßstäbe 0,01 … 100, verschobene Positionen, in Models verpackt) und vergleicht die
Bounding-Box jeder platzierten Instanz mit dem Sollwert, der unabhängig aus den
Blender-Transformationen berechnet wird.
