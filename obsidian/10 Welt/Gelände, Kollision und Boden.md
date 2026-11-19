---
title: Gelände, Kollision und Boden
tags: [welt, roblox, kollision]
---

# Gelände, Kollision und Boden

Zurück: [[Arcane Village – Übersicht]] · Verwandt: [[Fehlerchronik – gelernte Lektionen]]

## Gelände
- 768 × 768 Studs, Höhe ca. −6 bis +36 Studs, **36 Mesh-Kacheln** im 4-Stud-Raster.
- Drei Hügel, ansteigender Rand, Bach von Nord nach Süd, der sich zum Teich weitet.
- Dorfkern fast eben (±1 Stud); unter Gebäuden eingeebnet; Straßen leicht eingeschnitten.
- Optional: `VillageTerrainBuilder.lua` schreibt das Gelände als Voxel-Terrain (nur Aufruf getestet).

## Kollisionsmodi

| Modus | Bedeutung |
|---|---|
| `proxy` | Mesh kollidiert nicht, unsichtbare Boxen/Zylinder (Häuser, Bäume, Zäune) |
| `mesh` | Mesh mit Standardkollision (Felsen, Fässer) |
| `mesh_precise` | `PreciseConvexDecomposition` (Gelände, Straßen, Brücke) |
| `none` | keine Kollision (Blumen, Gras, Wasser) |

## Was im echten Place passiert ist

> [!bug] Graue Geländestücke (behoben in v13)
> **Symptom:** Geländestücke verloren beim Laufen ihre Farbe.
> **Ursache:** `MeshPart:ApplyMesh` übernimmt auch die leere `TextureID` des per
> `CreateMeshPartAsync` erzeugten Teils.
> **Fix:** `Auto.refineGround` sichert die Textur vor `ApplyMesh` und setzt sie danach wieder.
> Meine erste Deutung („Detailstufen/RenderFidelity“) war falsch.

> [!bug] Löcher in präziser Kollision
> Präzise Kollision hatte Löcher (90 von 36 481 Punkten ohne Boden). Lösung: Nach jedem
> Geländeteil wird sein Quadrat im 2-Stud-Raster abgetastet, jedes Loch bekommt eine unsichtbare
> Platte auf Höhenkarten-Niveau (**652 Platten**).

## Messwerte (Place v32)
- 54 Bodenteile `Precise/PreciseConvexDecomposition`, 0 ohne Textur.
- 36 481 Bodenstrahlen: **0 ohne Treffer**, mittlere Abweichung 0,26 Studs, 322 Punkte (0,9 %) über
  1,5 Studs, schlimmster 23,99 (Ursache offen, vermutlich Bachufer/Weltrand).
- Verfeinerung läuft im Hintergrund ab dem Spawn, ca. 40 s.
- Höhen für Sammelstellen, Markierungen, Stände kommen aus der **Höhenkarte**, nicht aus Strahlen
  gegen die grobe Startkollision (auf Brücke/Steg zählt deren Oberseite).
