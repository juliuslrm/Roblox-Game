---
title: Fehlerchronik – gelernte Lektionen
aliases: [Lessons learned, Fehlerchronik]
tags: [qualität, fehler, lektionen]
---

# Fehlerchronik – gelernte Lektionen

Zurück: [[Arcane Village – Übersicht]]

> [!tip] Muster
> Fast jeder ernste Fehler wurde erst durch **Messung im echten Place** oder durch **ein Bild**
> gefunden, nicht durch einen grünen Build. Darum: messen, rendern, ansehen.

## Welt und Roblox

> [!bug]- 180° gedrehter Import
> Roblox importiert FBX und GLB um 180° um die Hochachse gedreht. Jedes Geländestück lag verdreht.
> **Fix:** `importYaw` in `VillageAssetIds.lua`, `VillageAssetLoader` dreht zurück.

> [!bug]- Graue Geländestücke
> `ApplyMesh` übernahm die leere `TextureID`. Meine erste Deutung („Detailstufen“) war falsch.
> **Lektion:** Hypothese und bestätigte Ursache trennen. → [[Gelände, Kollision und Boden]]

> [!bug]- Löcher in präziser Kollision
> 90 von 36 481 Punkten ohne Boden. **Fix:** 652 unsichtbare Platten an den Löchern.

> [!bug]- Zu helle Beleuchtung
> Ambient 0,5, Brightness 2,6, 76 Lampen am Tag. Werte gesenkt, Lampen tagsüber aus.

> [!bug]- Maschinen halb im Boden / gespiegelt bei 90°/270°
> Pivot-Fehler in `WorkshopWorld`; Drehvorzeichen `−90°·rot` statt `+90°·rot`.

## Gameplay

> [!bug]- „Diese Maschine gibt es nicht mehr“
> Nutzer-IDs wurden als `"int"` ≤ 1 000 000 geprüft; echte Roblox-IDs sind Milliarden.
> **Lektion:** Tests mit realistischen Daten (Regressionstest mit echten ID-Größen).

> [!bug]- Menü sprang bei jedem Snapshot nach oben
> UI wurde 1×/s neu aufgebaut. Jetzt nur bei geänderter Signatur, Scrollposition bleibt.

> [!bug]- Bau-Platzhalter traf die eigene Figur
> Auf dem Handy zielte der Strahl auf die Bildschirmmitte = eigene Figur. Jetzt: zuletzt angetippte
> Stelle, Strahl ignoriert Figur, Maschinen, Wände.

> [!bug]- Statistik-Warteschlange mit `#` auf lückiger Tabelle
> Neue Einträge gingen verloren, q15/q18 wären nie erfüllbar gewesen.

> [!bug]- Client-Funktionen vor ihrer Definition benutzt
> Hätten zur Laufzeit `nil` gesehen. Gefunden mit einer Prüfung der Namensreihenfolge.

## Händler und Griffe

> [!bug]- Händler bewegten sich nie (v9)
> Upload legte die Bones aller Figuren in ein gemeinsames `RootPart`. **Fix:** ein Asset je Händler.

> [!bug]- `props.py` überschrieben
> Ich hatte die Dorf-Deko-Datei mit den Händler-Werkzeugen überschrieben. **Fix:** wiederhergestellt,
> Werkzeuge nach `handheld.py`, Registry-Test ergänzt.

> [!bug]- Flasche am Korken gehalten
> Griffursprung am Hals, Körper als zu große Kugel. **Fix:** neues Modell + Profil mit verbotenem
> Korken und Hals. → [[Griffsystem]]

> [!bug]- Handgelenk bis 115° verdreht
> Der Kanal `hand rz` ist reine Verdrehung; der alte Validator maß sie nicht.
> **Fix:** Swing-Twist-Messung, Grenze in IK und Test. → [[Arm-IK und Bewegungsschleifen]]

> [!bug]- „Drehen in der Hand“ schwenkte den Unterarm
> Euler-Schlüssel `fore rz` ≠ Unterarmdrehung bei gebeugtem Ellbogen. **Fix:** gelöste Drehposen.

> [!bug]- Hammerflächen-Normale zeigte in den Kopf
> Rückseite zum Erz, Kopf streifte seitlich. **Fix:** Vorzeichen; danach zwei saubere Treffer.

> [!bug]- Hammerstiel im Körper beim Ausholen
> IK prüfte nur den Kopf auf Körperkollision. **Fix:** Stielpunkte in die Prüfung; höchste
> Ausholpose gestrichen.

> [!bug]- Einheiten falsch berichtet
> Studs als cm angegeben. 1 Stud = 27 cm; korrigiert in `docs/GRIP_DIAGNOSIS.md`.

> [!bug]- Kleinere Solver-Fehler
> Brustziel enthielt die Hände (Ziel bewegte sich mit) → nur Rumpf; Schulterziel hing von sich
> selbst ab → Ruhe-Akromion; auf ganze Grad gerundete Winkel kosteten cm → eine Nachkommastelle;
> Erz aus überlappenden Blobs störte den Innen-Test → eine geschlossene Fläche.
