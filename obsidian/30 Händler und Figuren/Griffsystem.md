---
title: Griffsystem
tags: [händler, griffe, blender]
---

# Griffsystem

Zurück: [[Die fünf Händler]] · Code: `blender/village/grips.py`, `characters.grip_prop`, `handheld.py`
· Diagnose: `docs/GRIP_DIAGNOSIS.md`

> [!quote] Auslöser
> Nutzerfeedback zu einem Screenshot: „wo greift der sauber“ – die Hand lag neben dem Korbbügel.
> Daraus wurde der Auftrag „NPC GRIP & ANIMATION RECONSTRUCTION“ mit festen Verboten:
> keine schwebenden Flaschen, kein Werkzeug durch die Hand, nicht am falschen Ende halten,
> keine unrealistischen Handgelenkdrehungen, keine ungeprüften Testbehauptungen.

## Prop-Raum (Konvention für jeden Gegenstand)
- **+Y** läuft entlang des gegriffenen Teils von der Daumen-/Zeigefingerseite zum kleinen Finger.
- **−Z** ist die Richtung, in die die offenen Finger zeigen.
- **Ursprung** = Mitte des Griffs.
- Beim rechten Hand-Prop-Raum liegt die Handfläche auf +X.

## Griffprofile (`grips.PROFILES`)

| Gegenstand | Typ | Griffbereich (y) | Verboten |
|---|---|---|---|
| herb_bundle | bundle | −0,2 … 0,2 | Blüten/Blätter −1,0 … −0,28 |
| basket | hook | −0,2 … 0,2 | – |
| crystal | power | −0,3 … 0,22 | Spitze −0,6 … −0,4 |
| lantern | hook | −0,3 … 0,3 | – |
| potion_bottle | power | −0,3 … 0,16 | Korken −0,48 … −0,39, Hals −0,39 … −0,325 |
| cloth | – | −0,6 … 0,6 | – (weich, ganzes Tuch) |
| hammer | power | −0,58 … 0,42 | Kopf |
| ore | ball | – | – |
| axe | power | −0,2 … 0,46 | Kopf |
| folding_rule | pinch | – | – |

Zuordnung `grips.HELD`: Selma R Kräuter / L Korb · Nyra R Kristall / L Laterne · Lio R Flasche /
L Tuch · Aron R Hammer / L Erz · Esme R Axt / L Zollstock.

## Wie der Löser greift (`grip_prop`)
1. Gegenstand in der Handfläche platzieren; **vier Lagen** entlang der Hand werden probiert
   (`GRIP_ALONG = −0,01, 0,025, 0,06, 0,095` Studs, von der Knöchellinie zum Handgelenk).
2. Je Finger: Raster- und Feinsuche über die **drei Gelenkwinkel**, maximiert die Zahl der
   Glieder mit Kontakt (Gewichte 1 / 1,5 / 2 für Grund-, Mittel-, Endglied).
3. Ausgeschlossen: Glied dringt in den Griff oder in die eigene Handfläche ein
   (`PENETRATION` 0,004 Studs, an Gelenkfalten +0,016).
4. Daumen schließt danach von der Gegenseite (`_close`, sequentiell).
5. Gelenkgrenzen: Finger 95/110/85°, Daumen 50/65/75°. Kontakt = Abstand < `TOUCH` 0,012 Studs.

## Die Flasche (Kernfall)

> [!example] Vorher → nachher
> **Vorher:** Griffursprung am Hals, kugeliger Körper (zu groß), Zeige- und Mittelfinger auf dem
> Korken, 14 Kontaktpunkte am Korken.
> **Nachher:** Zylindrischer Körper ≈ 6 cm Ø, 11 cm hoch (ganze Flasche 18 cm), Ursprung 1,6 cm
> unter der Körpermitte, Korken zur Daumenseite → steht oben, wenn er die Flasche vor dem Körper
> hält. Eine geschlossene Glasoberfläche, Inhalt nur als Farbe (keine innere Fläche, die den
> Kontakttest verwirrt).

![[previews/grips/after/lio_R_potion_bottle.png]]

Weiter: [[Arm-IK und Bewegungsschleifen]] · [[Griffvalidierung und Ergebnisse]]
