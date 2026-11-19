---
title: Dorf und Levelplan
tags: [welt, leveldesign]
---

# Dorf und Levelplan

Zurück: [[Arcane Village – Übersicht]] · Code: `blender/village/plan.py` · Doku: `docs/LEVEL_DESIGN.md`

![[world/level_plan.png]]

## Leitidee
Ein gewachsenes Marktdorf in einer Talmulde. Vom Marktplatz aus sieht man in jeder Richtung einen
anderen Orientierungspunkt; die Hauptstraßen führen jeweils darauf zu. Man braucht keine Karte.

| Richtung | Orientierungspunkt | Lage |
|---|---|---|
| Mitte | Rathaus mit Uhrturm, Marktbrunnen | am Platz |
| Norden | Kapelle mit Schieferspitze | Kirchhügel (+25 Studs) |
| Nordwesten | Windmühle | Mühlenberg (+36), höchster Punkt |
| Osten | Wachturm | Rücken jenseits des Bachs (+30) |
| Südosten | Teich mit Steg | tiefster Punkt |
| Südwesten | rote Scheune, Weizenfeld | am Hofweg |

## Straßen
- **Hauptstraßen:** Südstraße (Dorftor), Kirchgasse (Norden), Mühlenweg (Westen), Bachstraße
  (Osten, Steinbrücke, Osttor).
- **Gassen (Schleifen):** Hintergasse, Feldgasse, Teichgasse, Kapellenstieg.
- **Pfade:** Turmpfad, Hofweg, Stegpfad.

## Gebäude und Bereiche
- 25 Gebäude: 18 Häuser + 7 Orientierungsbauten (Rathaus, Kapelle, Windmühle, Gasthaus, Schmiede,
  Wachturm, Markthalle).
- Marktplatz: Brunnen, fünf Marktstände (heute die [[Die fünf Händler|Händlerstände]]), Laternen,
  Bänke, Anschlagtafel.
- Gestaltung: massive Erdgeschosse, auskragendes Fachwerk, steile Dächer mit durchhängendem First;
  jedes Haus mit eigener Kombination aus Grundriss, Dachform und Farbe.
- Gebäude sind **Außenhüllen ohne Innenräume**.

## Werkstatt-Grundstücke (D13)
- Vier eingeebnete Grundstücke 84 × 84 Studs am Dorfrand (190–290 Studs vom Brunnen), je mit
  Zugangsweg (`plan.WORKSHOP_PLOTS`).
- Die Werkstatt ist offen (niedrige Mauern, 12 Studs Öffnung je Seite, kein Dach) → man läuft hinein.
- Die Fassade am Markt (ehemaliges Fachwerkhaus) ist nur noch der Ort „Deine Werkstatt“.
→ [[Werkstatt, Bauen und Logistik]]

## Datenformat `world_layout.json`

```json
{
  "meta": {}, "spawn": {"blender": [], "roblox": []}, "lighting": {}, "terrain": {"cell": 4},
  "roads":  [{"id": "south_road", "kind": "main|lane|path", "half_width": 7, "points_roblox": []}],
  "water":  {"points_roblox": [], "half_width": []},
  "assets": {"<id>": {"category": "houses|…", "collision": "proxy|mesh|mesh_precise|none",
                      "bounds_roblox": {}, "colliders": [], "lights": []}},
  "instances": [{"id": "house_01_timber_cottage#1", "asset": "…", "group": "buildings",
                 "roblox": {"position": [], "yaw_deg": 112.3, "scale": 1}}]
}
```
Gruppen: `terrain`, `roads`, `water`, `buildings`, `props`, `market`, `lights`, `nature`.

## Vom Plan zum Spiel
- `VillageWorldBuilder.lua` setzt die importierten Meshes nach dem Plan zusammen (sucht Vorlage per
  Name, misst Maßstab/Pivot, legt Kollisions-Proxys und Lichter an, klont je Instanz).
- `VillageAdapter.computeAnchors` leitet aus demselben Plan die **16 Orte** und **22
  Sammelstellen** ab → wird die Welt neu generiert, wandern alle Spielorte mit.

![[previews/world/03_market_square.png]]
