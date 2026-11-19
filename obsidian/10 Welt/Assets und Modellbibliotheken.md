---
title: Assets und Modellbibliotheken
tags: [welt, assets, roblox]
---

# Assets und Modellbibliotheken

Zurück: [[Arcane Village – Übersicht]] · Verwandt: [[Blender-Pipeline]], [[Veröffentlichen und Open Cloud]]

## Bestand

| Gruppe | Anzahl | Quelle | Bemerkung |
|---|---:|---|---|
| Häuser | 18 | `houses.py` | individuell |
| Orientierungsbauten | 7 | `landmarks.py` | Rathaus, Kapelle, Mühle … |
| Natur | 33 | `nature.py` | 11 Baumarten, Büsche, Felsen, Blumen |
| Dekoration | 33 | `props.py` | Brunnen, Laternen, Zäune, Brücke, Steg |
| Weltmeshes | 50 | `worldmesh.py` | 36 Geländekacheln, 11 Straßen, Platz, Ufer, Wasser |
| Maschinen/Logistik | 31 | `machines.py` | 146–2 564 Dreiecke, Budget 4 500 |
| Items (Materialien) | 45 | `items.py` | 36–516 Dreiecke, ≤ 1,6 Studs, Bildbogen 8 × 6 |
| Rohstoffmodelle | 15 | `resources.py` | für 22 Sammelstellen |
| Werkstatt | Fassade, Innenraum, Kessel | `workshop.py` | `build_workshop.py` |
| Marktstände | 5 | `market.py` | `arcane_market.fbx` |
| Händler | 5 Rigs | `characters.py` | → [[Charakter-Pipeline (MakeHuman)]] |

![[previews/assets/machines_1.png]]

## Bibliotheken in Roblox
- Jede Bibliothek ist ein FBX/GLB, per Open Cloud als Modell-Asset hochgeladen.
- IDs stehen in `roblox/VillageAssetIds.lua` (z. B. `ArcaneMarketAssets` = 5 Händler + Stände,
  `ArcaneResourceAssets`, `ArcaneItemAssets`, Maschinen, Gelände, Dorf).
- `VillageAssetLoader` lädt per `InsertService:LoadAsset` und dreht den 180°-Importfehler zurück.
- Gemessen: 13 Bibliotheken geladen, 0 fehlgeschlagen, 287 MeshParts, 144 von 144 Vorlagen.

> [!warning] Unfall (behoben)
> Ich hatte einmal `blender/village/props.py` (Dorf-Deko) mit den Händler-Werkzeugen
> überschrieben. Wiederhergestellt; die Werkzeuge liegen jetzt in `handheld.py`.
> `tests/test_asset_registry.py` prüft seitdem, dass jedes exportierte Asset seinen Builder hat.
