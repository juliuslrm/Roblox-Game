---
title: Glossar
tags: [referenz, glossar]
---

# Glossar

Zurück: [[Arcane Village – Übersicht]]

Stud
: Roblox-Längeneinheit. Hier 1 Blender-Einheit; bei Figuren 0,27 m.

`bpy`
: Blender als Python-Modul (Version 5.3), läuft ohne GUI und ohne GPU.

Cycles (CPU)
: Renderer für alle Vorschauen. EEVEE funktioniert im Container nicht.

MeshBuilder
: Eigener Mesh-Baukasten (`blender/village/meshkit.py`): Box, Balken, Loft, Lathe, Blob, Transformstapel.

Levelplan
: `world/world_layout.json` / `roblox/WorldLayout.lua` – jede Instanz mit Position, Drehung, Gruppe. → [[Dorf und Levelplan]]

Anker
: Spielposition eines Ortes, vom `VillageAdapter` aus dem Levelplan berechnet (5 Studs vor der Vorderseite).

Open Cloud
: Roblox-Web-API: Assets hochladen, Place veröffentlichen, Luau auf dem Server ausführen. → [[Veröffentlichen und Open Cloud]]

Domain-Kern
: Reine Lua-Module ohne Roblox-API (Services, Simulation) – lokal testbar. → [[Gameplay-Architektur]]

Snapshot
: Vollständiger Spielzustand, den der Server 1×/s und nach jeder Aktion an den Client schickt (D10).

Hologramm / Ghost
: Weiße, durchscheinende Vorschau eines Geräts im Baumodus. → [[Werkstatt, Bauen und Logistik]]

Skinned Mesh
: Mesh, dessen Vertices an Knochen gewichtet sind und sich mit ihnen verformen. → [[Charakter-Pipeline (MakeHuman)]]

MakeHuman
: Open-Source-Menschmodell (CC0-Daten), Basis der Händlerkörper.

`Bone.Transform`
: Roblox-Eigenschaft, mit der der Client Knochen dreht. → [[Händler-Animation in Roblox]]

Griffprofil
: Beschreibung, wie und wo eine Hand einen Gegenstand hält. → [[Griffsystem]]

IK (inverse Kinematik)
: Aus einem Ziel (z. B. „Hammerfläche auf das Erz“) die Gelenkwinkel berechnen. → [[Arm-IK und Bewegungsschleifen]]

Swing-Twist
: Zerlegung einer Drehung in „Schwenken“ und „Verdrehen um eine Achse“ – damit wird die Handgelenks-Verdrehung gemessen.

Kraftgriff / Hakengriff / Spitzgriff
: Faust um einen Griff / Finger als Haken um einen Bügel / Gegenstand zwischen Fingerspitzen und Daumen.

Schleife (Loop)
: Geschlossene Idle-Animation (6–8 s) eines Händlers, 8 Bilder pro Sekunde.
