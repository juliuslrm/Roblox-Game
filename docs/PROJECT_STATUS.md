# Projektstand

Stand: erste vollständige Dorfversion (Layout-Version 1).

## Ziel und Umfang

Eine eigenständige, stilisierte Dorf-Spielwelt für Roblox, komplett in der Cloud mit Blender/Python
erzeugt, die später über einen maschinenlesbaren Levelplan in ein bestehendes Roblox-Spiel
eingesetzt wird. Kein Zugriff auf Roblox Studio während der Entwicklung.

## Technische Entscheidungen

| Entscheidung | Grund | Nachteil |
|---|---|---|
| Blender als Python-Modul (`bpy` 5.3), Cycles auf CPU | läuft headless ohne GPU, reproduzierbar | Rendern dauert Minuten statt Sekunden; EEVEE nicht nutzbar |
| Alles prozedural aus Code, feste Seeds | jede Datei ist neu erzeugbar und per Diff nachvollziehbar | Änderungen brauchen Python statt Maus |
| Eine Palettentextur, ein Material, ein Mesh pro Asset | passt zum Roblox-MeshPart (eine Textur), sehr günstig auf Mobilgeräten | keine Detailtexturen (Maserung, Putzstruktur) |
| 1 Blender-Einheit = 1 Stud | keine Umrechnungsfehler im Plan | Blender-Datei „denkt" in Metern, die Zahlen sind Studs |
| Gelände als Mesh-Kacheln im 4-Stud-Raster | sieht aus wie in den Vorschauen, passt 1:1 auf Roblox-Voxel | braucht in Roblox präzise Kollision (manuell setzen) |
| Builder misst Import-Maßstab und Pivot selbst nach | Import-Einstellungen konnten nicht getestet werden | funktioniert nur bei aufrecht importierten Meshes |
| Kollision über einfache Proxy-Körper | stabil und billig, man läuft unter Baumkronen durch | Proxys sind grob (Box je Gebäudeflügel) |
| Luau nur im Lua-5.1-Teilumfang | dadurch außerhalb von Roblox ausführbar und testbar | keine Typannotationen |
| ≤ 10 000 Dreiecke pro Mesh | konservativ, da das echte Importlimit nicht nachschlagbar war | Rathaus und Gasthaus mussten Details abgeben |

## Fertig

- Mesh-Baukasten, Architektur-Baukasten, Palette
- 18 Häuser, 7 Orientierungsbauten, 33 Naturmodelle, 33 Dekorationen (91 Assets, 137 000 Dreiecke)
- Gelände mit Hügeln, Bach, Teich; Straßennetz; Marktplatz
- Levelplan mit 1 889 Instanzen, Lageplan, Höhenkarte
- Exporte: `.blend` je Asset, `.glb` je Asset, Sammeldateien `.glb` + `.fbx`, zusammengesetzte Weltszene
- Roblox: Builder, generierte Layout-Daten, optionaler Voxel-Terrain-Builder, Rojo-Projektdatei
- Automatische Prüfungen und Luau-Tests
- Vorschauen: 11 Weltansichten, 9 Kontaktbögen, Referenzhaus

## Tatsächlich geprüft

- `blender/validate.py`: 34 Prüfungen bestanden, 0 fehlgeschlagen (`docs/validation_report.md`)
- `blender/audit_backfaces.py`: alle 141 Meshes aus je zehn Richtungen auf sichtbare Rückseiten
  geprüft; übrig sind 1–4 Einzelpixel bei 10 Meshes (Abtastrauschen an Kanten)
- `tests/test_roblox_builder.py`: Builder dreimal vollständig ausgeführt (Ursprung, verschoben und
  um 90° bzw. 33° gedreht), größte Abweichung einer Bounding-Box 0,0002 Studs; Gruppenfilter,
  fehlende und verzerrte Vorlagen, Schalter, Höhenkarten-Dekodierung
- Sichtprüfung aller Kontaktbögen und Weltansichten; dabei gefundene und behobene Fehler:
  durchstoßende Eckpfosten an steilen Dächern, gezackte Geländefarben, zu dichte Vegetation
- Die Prüfskripte fanden vier Fehler, die in den Vorschauen unsichtbar waren (alle behoben):
  fehlende Rückseiten an Fahnen und Mühlenflügeln, verdrehte Dreiecke an Walmdach-Firsten,
  aus schmalen Giebeln herausragende Kehlbalken mit offener Rückseite und gefaltete Straßenenden

## Nicht geprüft / offen

- **Import in Roblox Studio**: Annahme von `.glb`, Namenserhalt, Texturübernahme, Maßstab,
  Dreieckslimit – siehe Kontrollliste in `docs/ROBLOX_IMPORT.md`
- **Echte Luau-Laufzeit**: Die Skripte liefen unter Lua 5.5 mit einem selbst geschriebenen
  API-Mock, nicht in Roblox. Der Download der offiziellen Luau-CLI wurde in der
  Entwicklungsumgebung nicht zugelassen.
- **Leistung auf Mobilgeräten**: nicht gemessen. 602 000 Dreiecke insgesamt, 340 000 davon Vegetation.
- **`VillageTerrainBuilder`** (Voxel-Gelände): nur Aufrufmuster und Dekodierung getestet.
- Roblox-Dokumentation war aus der Umgebung nicht erreichbar; Aussagen zum Importer beruhen auf
  Vorwissen und sind entsprechend vorsichtig formuliert.

## Bekannte Einschränkungen

- Gebäude haben keine Innenräume.
- Zaun- und Mauersegmente sind starr (8 Studs) und folgen Hängen nur über ihre Höhe, nicht über Neigung.
- Die Wasserfläche ist ein flaches Mesh; am Teich überlappen sich in der Innenkurve einzelne Flächen.
- Kein LOD-Satz: Roblox' automatische `RenderFidelity` muss das übernehmen.
- Vorschau-Himmel ist einfarbig; die Lichtstimmung in Roblox wird abweichen.

## Nächster Schritt

Import in Studio nach `docs/ROBLOX_IMPORT.md`, Kontrollliste abarbeiten, Ergebnis des Builders
(`report.warnings`, `report.missing`) zurückmelden. Danach je nach Befund: Exportparameter
anpassen, Dichte der Vegetation für Mobilgeräte einstellen, Innenräume oder LODs ergänzen.
