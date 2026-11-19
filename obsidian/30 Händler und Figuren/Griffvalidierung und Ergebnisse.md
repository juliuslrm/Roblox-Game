---
title: Griffvalidierung und Ergebnisse
tags: [händler, griffe, qualität, test]
---

# Griffvalidierung und Ergebnisse

Zurück: [[Die fünf Händler]] · Bericht: `docs/GRIP_VALIDATION_REPORT.md` · Bewertungen:
`docs/grip_reviews.json` · Code: `blender/village/gripcheck.py`, `blender/validate_grips.py`

## Was gemessen wird (je Griff, über die ganze Schleife)
Grenzwerte relativ zur gemessenen Fingerdicke **t** (≈ 0,058–0,066 Studs ≈ 1,6–1,8 cm).

| Kürzel | Prüfung | Grenze |
|---|---|---|
| A Kontakt | Glieder je Finger am Gegenstand, Handfläche | Kontakt < 0,2 t |
| B Durchdringung | tiefster Punkt | ≤ 0,3 t |
| C Griffbereich | Anteil Kontakt im erlaubten Bereich, nichts im verbotenen | |
| D Gelenke | Finger in Grenzen; Handgelenk ≤ 50° / 25° seitlich; **Verdrehung ≤ 45°, Unterarm ≤ 95°**; Ellbogen 5–145° | |
| E Stabilität | Verrutschen Finger ↔ Gegenstand | < 0,1 t |
| F Bewegung | Handschritt, Drehung, Naht der Schleife, Ruck | |
| + | Gegenstand ↔ Körper (ohne Arme) | > −0,5 t |

**Punkte:** Lage 20, Finger 20, Handgelenk/Arm 15, Halt 15, Bewegung 15, **visuell 15** (nur aus
der Sichtprüfung). Status: `FAIL` bei Pflichtverletzung oder < 76 automatisch; `PASS_AUTOMATED`;
`PASS_VISUAL` wenn angesehen und ≥ 90 gesamt. `UNVERIFIED_IN_STUDIO` gilt für alle.

Jeder Griff bekommt einen **Bogen mit 14 Ansichten**: 3 Ganzkörper, Nahaufnahme, 6 Ansichten nur
Hand + Gegenstand, 4 Zeitpunkte der Schleife.

## Ergebnis (Place v32)

| Händler | Hand | Gegenstand | automatisch /85 | visuell /15 | Summe | Status |
|---|---|---|---:|---:|---:|---|
| selma | L | basket | 83,8 | 14 | 98 | PASS_VISUAL |
| selma | R | herb_bundle | 84,5 | 14 | 98 | PASS_VISUAL |
| nyra | L | lantern | 85,0 | 14 | 99 | PASS_VISUAL |
| nyra | R | crystal | 82,7 | 11 | 94 | PASS_VISUAL |
| lio | L | cloth | 83,8 | 13 | 97 | PASS_VISUAL |
| lio | R | potion_bottle | 83,6 | 12 | 96 | PASS_VISUAL |
| aron | L | ore | 82,7 | 13 | 96 | PASS_VISUAL |
| aron | R | hammer | 85,0 | 11 | 96 | PASS_VISUAL |
| esme | L | folding_rule | 83,8 | 13 | 97 | PASS_VISUAL |
| esme | R | axe | 82,2 | 12 | 94 | PASS_VISUAL |

> [!note] Die visuelle Wertung ist mein eigenes Urteil
> Sie steht mit Begründung in `docs/grip_reviews.json`. Abzüge:
> - **Nyra:** Kristallspitze reicht an die Haarsträhnen (Haare nicht in der Kollisionsprüfung),
>   Handfläche 0,045 Studs (≈ 1,2 cm) vom Kristall.
> - **Lio:** schräg von rechts verdeckt die Hand beim „Licht“ das rechte Auge.
> - **Aron:** Ellbogen beim Ausholen weit seitlich, kurzer Schwung.
> - **Esme:** Stielende 3,9 cm am Kinn vorbei, Handgelenk seitlich am Grenzwert (20°).

## Vorher → nachher (automatisch, von 85)

| Griff | vorher | nachher | Pflichtverletzung vorher |
|---|---:|---:|---|
| Selma Kräuter | 65,0 | 84,5 | hält Blüten/Blätter |
| Lio Flasche | 61,5 | 83,6 | hält den Korken (14 Punkte) |
| Lio Tuch | 79,4 | 83,8 | Profilfehler (Bereich zu eng) |
| Aron Hammer | 79,2 | 85,0 | Profilfehler (Bereich zu eng) |
| Aron Hammer → Erz | bis 1,6 cm **im** Erz | zwei Treffer bei 0,0043 Studs | |

> [!warning] Nicht umgesetzt
> - **Testfall E (Gegenstand wechseln)** und **Gehen mit Gegenstand:** Händler stehen fest am Stand;
>   in Roblox gibt es keine Fingerknochen. Das wäre neues Spielverhalten.
> - Hautverformung am Handgelenk in Roblox: nicht gesehen.
