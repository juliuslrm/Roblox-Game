---
title: Arbeitsregeln und Konventionen
tags: [regeln, konventionen]
---

# Arbeitsregeln und Konventionen

Zurück: [[Arcane Village – Übersicht]]

> [!danger] Diese Regeln nicht verletzen
> 1. **Maßstab:** 1 Blender-Einheit = **1 Stud**. Bei Figuren: **1 Stud = 0,27 m**
>    (0,01 Stud ≈ 2,7 mm). Ich habe Studs einmal fälschlich als cm berichtet; korrigiert.
> 2. **Koordinaten:** Blender `(x, y, z)` → Roblox `(x, z, −y)`. Drehung um Blender‑Z = Drehung um
>    Roblox‑Y: `CFrame.new(pos) * CFrame.Angles(0, math.rad(a), 0)`. Norden = Blender +Y = Roblox −Z.
> 3. **Alles ist generiert.** `.glb`, `.blend`, `world_layout.json`, `WorldLayout.lua`,
>    `WorldHeightmap.lua`, `TraderArt.lua`, `MarketMotion.lua` nie von Hand ändern, sondern den
>    Python-Code ändern und neu bauen.
> 4. **Roblox zeichnet keine Rückseiten:** jedes Teil ein geschlossener, nach außen gewickelter
>    Körper (`MeshBuilder.add(closed=True)` prüft das).
> 5. **Luau nur im Lua‑5.1-Teilumfang** (kein `continue`, kein `+=`, keine Typannotationen), damit
>    es außerhalb von Roblox testbar bleibt.
> 6. **Eine Palettentextur** für die Dorf-Assets (1024 × 64 px, 64 Farbspalten). Farben nur
>    anhängen, nie umsortieren. (Händler und Item-Bilder haben eigene Texturen.)

## Asset-Ursprung
- Bodenkontaktpunkt in der Mitte der Grundfläche.
- Vorderseite (Haustür) zeigt nach Blender −Y = Roblox +Z.
- Fundamente reichen 4 Studs unter den Ursprung.
- Roblox importiert FBX/GLB **um 180° gedreht** → `importYaw` in `roblox/VillageAssetIds.lua`.

## Werkstatt-Raster
- Zellen **2 × 2 Studs**; Richtung 0 = +z (vorn), 1 = +x, 2 = −z, 3 = −x.
- Drehung dreht die Anschlüsse mit → [[Werkstatt, Bauen und Logistik]].

## Sprache und Stil
- Antworten und Doku **auf Deutsch**, Code und Bezeichner **auf Englisch**.
- Nichts als geprüft ausgeben, was nicht ausgeführt wurde. Unterscheiden: *implementiert* –
  *tatsächlich geprüft* – *unbestätigt*.

## Git
- Entwicklung und Push nur auf `claude/roblox-village-blender-xekw0z`, kein PR ohne Auftrag.
- Commits enden mit den Zeilen `Co-Authored-By: Claude …` und `Claude-Session: …`.

## Sicherheit
- Der Roblox-API-Key liegt **nicht** im Repository. Der Proxy der Cloud-Umgebung setzt ihn ein;
  im Code steht nur `x-api-key: dummy`.
- Persönliche Daten des Nutzers gehören nicht in Dateien oder externe Anfragen.
- Die Luau-CLI darf nicht heruntergeladen werden (wurde abgelehnt) – Tests laufen mit `lupa`.
