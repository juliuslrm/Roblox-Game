---
title: Befehle – Spickzettel
aliases: [Commands, Spickzettel]
tags: [befehle, referenz]
---

# Befehle – Spickzettel

Zurück: [[Arcane Village – Übersicht]]

> [!tip] Python
> Lokal: `.venv/bin/python` (bpy 5.3, Python 3.13, einrichten mit `./scripts/setup_env.sh`).
> In der Cloud-Sitzung lief alles mit `/opt/bpyenv/bin/python`.
> Für `check_all.sh` dann: `VILLAGE_PYTHON=/opt/bpyenv/bin/python ./scripts/check_all.sh`.

## Alles prüfen
```bash
./scripts/check_all.sh          # Gameplay-Tests, Place-Datei, Registry, Griffe, Weltvalidierung
./scripts/check_all.sh --full   # zusätzlich Gameplay-/Item-/Rohstoff-Assets neu + Rückseiten-Audit
```

## Welt
```bash
./build.sh                                  # Assets + Welt bauen und prüfen (~6 min)
./build.sh --render                         # + Vorschauen (~15 min)
python blender/build_assets.py [--only well,bench]
python blender/build_world.py
python blender/render_previews.py world --views 03_market_square
python blender/audit_backfaces.py
python blender/validate.py                  # 34 Prüfungen
```

## Gameplay-Assets
```bash
python blender/build_gameplay_assets.py     # 31 Maschinen
python blender/build_item_assets.py --no-render
python blender/build_resource_assets.py
python blender/build_workshop.py [--no-render]
python blender/build_merchants.py           # Marktstände + Katalog
```

## Händler und Griffe
```bash
python blender/solve_poses.py -- esme aron nyra lio   # Arm-IK → world/solved_poses.json
python blender/validate_grips.py -- --out previews/grips/after [--only lio] [--no-render]
python blender/grip_test_crate.py                     # Zwei-Hand-Test (Kiste)
python blender/build_characters.py [--no-render] [--only ROLE] [--tex 1024]   # ~25 min
python tests/test_grip_profiles.py                    # schneller Griff-/Schleifentest
```
→ [[Arm-IK und Bewegungsschleifen]], [[Griffvalidierung und Ergebnisse]]

## Roblox
```bash
python scripts/build_place.py               # exports/roblox/ArcaneVillage.rbxlx
curl -X POST "https://apis.roblox.com/universes/v1/<universeId>/places/<placeId>/versions?versionType=Published" \
  -H "x-api-key: <key>" -H "Content-Type: application/xml" \
  --data-binary @exports/roblox/ArcaneVillage.rbxlx
python3 scripts/roblox_verify_server.py <universeId> <placeId>
```
→ [[Veröffentlichen und Open Cloud]]

## Lokale Tests einzeln
```bash
cd roblox/gameplay/tests
python test_data.py; python test_syntax.py; python run_tests.py   # spec_core, spec_progression, …
cd ../../..
python tests/test_roblox_builder.py
python tests/test_place_and_autobuild.py
python tests/test_asset_registry.py
```
