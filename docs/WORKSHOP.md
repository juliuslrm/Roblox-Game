# Trankbrauer-Werkstatt

Die Fassade nutzt den Standort des Fachwerkhauses am Markt. Ein Bogenportal,
ein Flaschenschild, ein seitlicher Kräuteranbau und ein Fenster mit Flaschen
und kupferfarbenen Rohren kennzeichnen die Werkstatt. Das vorhandene Portal
führt in den separaten Produktionsraum.

| Datei | Zweck |
|---|---|
| `assets/workshop/ArcaneVillage_Workshop.blend` | Drei editierbare Szenen mit gepackter Palettentextur |
| `exports/glb/workshop/workshop_facade.glb` | Fassade mit Dorf-Pivot und den vorhandenen Exportachsen |
| `exports/glb/workshop/workshop_interior_32.glb` | Modulare Startfläche mit Wänden, Boden, Balken, Tür, Deko und separatem Dach |
| `exports/glb/workshop/mach_kettle.glb` | Braukessel mit Messinggriffen |
| `previews/workshop/` | Ansichten vom Dorfweg, vom Eingang und als Fabrikschnitt |
| `blender/build_workshop.py` | Reproduziert Szene, Exporte, Fassadenmetadaten und Renderbilder |

## Generieren

Mit den Repository-Python-Abhängigkeiten im Projektordner

```bash
.venv/bin/python blender/build_workshop.py
```

Oder mit Blender als ausführbarem Programm und einem zu dessen Python-Version
passenden `lupa` im Python-Suchpfad

```bash
blender -b --python-use-system-env --python-exit-code 1 -P blender/build_workshop.py
```

`--no-render` überspringt die PNGs. Beim Aufruf über Blender Argumente hinter
`--` angeben. Die Außenansicht verwendet Teile der vorhandenen Welt-GLBs,
die auf die Position des Fachwerkhauses ausgerichtet werden.

## In Roblox Studio

1. `exports/roblox/ArcaneVillage.rbxlx` öffnen oder den aktuellen Code mit Rojo synchronisieren.
2. Die bestehende Dorf- und Geländebibliothek nach `ServerStorage.VillageAssets` importieren.
   Dort zusätzlich die Fassade als `workshop_facade` ablegen. Beim Start setzt der
   Dorf-Builder sie an den Standort mit der bisherigen Asset-ID und Ausrichtung.
   Bei fehlender neuer Vorlage bleibt das bisherige Fachwerkhaus verfügbar.
3. In `ServerStorage.ArcaneAssets` die Maschinenbibliothek und die neue Vorlage
   `mach_kettle` ablegen. Bei zwei Vorlagen mit diesem Namen die ältere entfernen.
4. Play drücken. Das Marktportal führt in den Innenraum. Roblox erzeugt Boden, Wände,
   Treppen, Dekoration und Lichter aus `WorkshopArchitecture.lua`. Das Innenraum-GLB
   ist ein separat nutzbares Modell der 32-Stud-Version. Im Spiel übernimmt der
   serverseitige Bau den Ausbau auf 48, 64 und 80 Studs sowie bis zu drei Etagen.
5. Der Fabrikschnitt zeigt ein Ausbau-Beispiel mit Minze aus der Starterkiste und
   per Hand aufgefüllten Fläschchen. Die Vorlage gibt dem Spieler beim Start
   Kessel, Kiste und Verkaufsregal. Vorhandene gespeicherte Platzierungen bleiben
   an ihren Koordinaten.

## Lokal geprüft

- Fassade und Portal auf der vorhandenen Ausrichtung. Der Portalpunkt liegt rund
  7 Studs von der Mitte der Straße entfernt.
- 32 × 32 Studs auf einem 2-Stud-Raster. Die Beispielplatzierung hält drei
  durchgängige Rasterspalten als 6 Studs breiten Laufweg frei.
- Zwölf Kombinationen aus Raumgröße und Etagenzahl. Kollisionsböden der Obergeschosse
  lassen die reservierte Treppenöffnung frei.
- Die im Fabrikschnitt gezeigten Komponenten wurden über die echte
  Platzierungslogik gesetzt. Die Simulation hat in 120 Sekunden vier abgefüllte
  Tonika in die Ausgabekiste geliefert.
- Die GLBs enthalten Normalen, UVs und die eingebettete gemeinsame Palette.
  Die Fassade liegt unter dem projektüblichen Einzelmesh-Budget.

## In Roblox Studio noch zu prüfen

- Importname, Maßstab, Textur und Laufweg vom Dorf durch das Werkstattportal.
- Platzierung und Kollision des importierten Kessels, Kamera am Eingang und in Raumecken.
- Treppenaufstieg und Rückweg, Platzieren auf den geteilten Obergeschossböden.
- Licht und Bedienbarkeit auf einem Mobilgerät.
