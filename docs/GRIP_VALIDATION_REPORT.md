# Griff-Validierung

Erzeugt von `blender/validate_grips.py`. Automatische Werte aus `blender/village/gripcheck.py`; die
visuelle Wertung stammt aus `docs/grip_reviews.json` und wurde nach Ansicht der Bogen in
`previews/grips/after/` eingetragen. Status:

- **PASS_AUTOMATED**: alle Messungen ohne Pflichtverletzung, automatische Punkte ≥ 76/85.
- **PASS_VISUAL**: zusätzlich angesehen und ≥ 90/100 gesamt.
- **FAIL**: Pflichtverletzung oder zu wenig Punkte.
- **UNVERIFIED_IN_STUDIO**: gilt für alle: Hautverformung und Darstellung in Roblox sind nicht gesehen.

| Händler | Hand | Gegenstand | Lage | Finger | Arm | Halt | Bewegung | Visuell | Summe | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| selma | L | basket | 20.0 | 18.8 | 15 | 15 | 15 | 14 | 98 | PASS_AUTOMATED, PASS_VISUAL |
| selma | R | herb_bundle | 19.5 | 20.0 | 15 | 15 | 15 | 14 | 98 | PASS_AUTOMATED, PASS_VISUAL |
| nyra | L | lantern | 20.0 | 20.0 | 15 | 15 | 15 | 14 | 99 | PASS_AUTOMATED, PASS_VISUAL |
| nyra | R | crystal | 20.0 | 17.7 | 15 | 15 | 15 | 11 | 94 | PASS_AUTOMATED, PASS_VISUAL |
| lio | L | cloth | 20.0 | 18.8 | 15 | 15 | 15 | 13 | 97 | PASS_AUTOMATED, PASS_VISUAL |
| lio | R | potion_bottle | 19.8 | 18.8 | 15 | 15 | 15 | 12 | 96 | PASS_AUTOMATED, PASS_VISUAL |
| aron | L | ore | 20.0 | 17.7 | 15 | 15 | 15 | 13 | 96 | PASS_AUTOMATED, PASS_VISUAL |
| aron | R | hammer | 20.0 | 20.0 | 15 | 15 | 15 | 11 | 96 | PASS_AUTOMATED, PASS_VISUAL |
| esme | L | folding_rule | 20.0 | 18.8 | 15 | 15 | 15 | 13 | 97 | PASS_AUTOMATED, PASS_VISUAL |
| esme | R | axe | 18.4 | 18.8 | 15 | 15 | 15 | 12 | 94 | PASS_AUTOMATED, PASS_VISUAL |

## Einzelheiten

### selma – L – basket

- Aufgabe: carry by the bail with the arm down, the basket hangs below the hand
- Fingerdicke 0.0577 Studs, Handlänge 0.675 Studs
- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): [1, 3, 3, 3, 2], Handfläche 0.0124 Studs
- Tiefste Durchdringung -0.004 Studs; Kontakt auf dem Griffbereich: 100% (Kontakt bei y [-0.198, 0.127])
- Handgelenk gebeugt 1.5° / seitlich 1.0°, in sich verdreht 0.0°, Unterarm gedreht 0.3°, Ellbogen 8.9–14.5°, Oberarm max. 18.5° gehoben
- Verrutschen in der Schleife: 0.0 Studs; größter Handschritt 0.033 Studs, Drehung 1.3°, Naht 0.006
- Abstand Gegenstand ↔ Körper in der Schleife: 0.0907 Studs
- Probleme: keine; Pflichtverletzungen: keine
- Visuelle Prüfung: Hakengriff am Korbbügel, Arm hängt locker, Korb hängt unter der Hand und frei vom Rock.
- Bogen: `previews/grips/after/selma_L_basket.png`

### selma – R – herb_bundle

- Aufgabe: hold the bundle by the tied stems, flowers up; smell it
- Fingerdicke 0.0581 Studs, Handlänge 0.675 Studs
- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): [1, 3, 3, 3, 3], Handfläche 0.0101 Studs
- Tiefste Durchdringung -0.0042 Studs; Kontakt auf dem Griffbereich: 97% (Kontakt bei y [-0.225, 0.132])
- Handgelenk gebeugt 1.5° / seitlich 1.0°, in sich verdreht 0.0°, Unterarm gedreht 4.0°, Ellbogen 54.1–98.1°, Oberarm max. 45.6° gehoben
- Verrutschen in der Schleife: 0.0 Studs; größter Handschritt 0.128 Studs, Drehung 6.8°, Naht 0.016
- Abstand Gegenstand ↔ Körper in der Schleife: 0.0285 Studs
- Probleme: keine; Pflichtverletzungen: keine
- Visuelle Prüfung: Faust um die gebundenen Stängel, Blüten oben, zum Riechen vor die Nase gehalten; Finger liegen auf dem Bindfaden, kein Blattkontakt sichtbar.
- Bogen: `previews/grips/after/selma_R_herb_bundle.png`

### nyra – L – lantern

- Aufgabe: carry by the bail with the arm down, the lantern hangs below the hand
- Fingerdicke 0.0592 Studs, Handlänge 0.699 Studs
- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): [2, 3, 3, 3, 3], Handfläche 0.0055 Studs
- Tiefste Durchdringung -0.0044 Studs; Kontakt auf dem Griffbereich: 100% (Kontakt bei y [-0.189, 0.127])
- Handgelenk gebeugt 1.5° / seitlich 1.0°, in sich verdreht 0.0°, Unterarm gedreht 0.3°, Ellbogen 10.7–14.5°, Oberarm max. 15.7° gehoben
- Verrutschen in der Schleife: 0.0 Studs; größter Handschritt 0.027 Studs, Drehung 1.0°, Naht 0.027
- Abstand Gegenstand ↔ Körper in der Schleife: 0.1613 Studs
- Probleme: keine; Pflichtverletzungen: keine
- Visuelle Prüfung: Hakengriff am Laternenbügel, Arm unten, Laterne hängt senkrecht neben dem Mantel.
- Bogen: `previews/grips/after/nyra_L_lantern.png`

### nyra – R – crystal

- Aufgabe: hold the crystal by its body, the point free; turn it in the light
- Fingerdicke 0.0572 Studs, Handlänge 0.699 Studs
- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): [1, 2, 3, 3, 2], Handfläche 0.0451 Studs
- Tiefste Durchdringung -0.0039 Studs; Kontakt auf dem Griffbereich: 100% (Kontakt bei y [-0.255, 0.14])
- Handgelenk gebeugt 5.0° / seitlich 20.1°, in sich verdreht 20.2°, Unterarm gedreht 20.5°, Ellbogen 76.1–125.0°, Oberarm max. 10.7° gehoben
- Verrutschen in der Schleife: 0.0 Studs; größter Handschritt 0.071 Studs, Drehung 3.9°, Naht 0.03
- Abstand Gegenstand ↔ Körper in der Schleife: 0.4665 Studs
- Probleme: ['palm 0.045 studs from the crystal (power grip needs it on the handle)']; Pflichtverletzungen: keine
- Visuelle Prüfung: Kristall am Körper gegriffen, Spitze frei, vor der rechten Brust. Abzug: Die Spitze steht fast senkrecht und reicht bis an die Haarsträhnen (Haare sind nicht Teil der Kollisionsprüfung); die Handfläche liegt 0,045 Studs (≈1,2 cm) vom Kristall ab.
- Bogen: `previews/grips/after/nyra_R_crystal.png`

### lio – L – cloth

- Aufgabe: a crumpled cloth in the fist; rub the bottle with it
- Fingerdicke 0.0638 Studs, Handlänge 0.774 Studs
- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): [2, 2, 3, 3, 3], Handfläche 0.0126 Studs
- Tiefste Durchdringung -0.0039 Studs; Kontakt auf dem Griffbereich: 100% (Kontakt bei y [-0.22, 0.154])
- Handgelenk gebeugt 1.5° / seitlich 1.5°, in sich verdreht 8.3°, Unterarm gedreht 26.6°, Ellbogen 36.2–118.9°, Oberarm max. 25.1° gehoben
- Verrutschen in der Schleife: 0.0 Studs; größter Handschritt 0.185 Studs, Drehung 10.2°, Naht 0.045
- Abstand Gegenstand ↔ Körper in der Schleife: 0.2585 Studs
- Probleme: keine; Pflichtverletzungen: keine
- Visuelle Prüfung: Tuch zwischen Fingern und Daumen, reibt die Flasche; in der Pause hängt die Hand mit dem Tuch locker. Tuchfalten sind grob.
- Bogen: `previews/grips/after/lio_L_cloth.png`

### lio – R – potion_bottle

- Aufgabe: hold the bottle round its body, cork up; polish it, hold it to the light
- Fingerdicke 0.0671 Studs, Handlänge 0.774 Studs
- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): [2, 3, 3, 3, 2], Handfläche 0.0087 Studs
- Tiefste Durchdringung -0.0041 Studs; Kontakt auf dem Griffbereich: 99% (Kontakt bei y [-0.305, 0.145])
- Handgelenk gebeugt 5.0° / seitlich 20.0°, in sich verdreht 20.1°, Unterarm gedreht 36.9°, Ellbogen 95.3–118.1°, Oberarm max. 65.2° gehoben
- Verrutschen in der Schleife: 0.0 Studs; größter Handschritt 0.236 Studs, Drehung 5.7°, Naht 0.03
- Abstand Gegenstand ↔ Körper in der Schleife: 0.2372 Studs
- Probleme: keine; Pflichtverletzungen: keine
- Visuelle Prüfung: Kraftgriff um den Flaschenkörper, Korken frei und oben; beim Reiben aufrecht vor dem Bauch. Gegen das Licht seitlich auf Augenhöhe: von vorn ist das Gesicht frei, aus der Schrägansicht von rechts verdeckt die Hand das rechte Auge.
- Bogen: `previews/grips/after/lio_R_potion_bottle.png`

### aron – L – ore

- Aufgabe: weigh the lump in the hand
- Fingerdicke 0.0651 Studs, Handlänge 0.781 Studs
- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): [2, 2, 3, 2, 3], Handfläche 0.0004 Studs
- Tiefste Durchdringung -0.0031 Studs; Kontakt auf dem Griffbereich: 100% (Kontakt bei y [-0.174, 0.133])
- Handgelenk gebeugt 1.1° / seitlich 0.4°, in sich verdreht 2.8°, Unterarm gedreht 16.4°, Ellbogen 103.9–114.9°, Oberarm max. 14.3° gehoben
- Verrutschen in der Schleife: 0.0 Studs; größter Handschritt 0.053 Studs, Drehung 3.3°, Naht 0.012
- Abstand Gegenstand ↔ Körper in der Schleife: 0.4549 Studs
- Probleme: keine; Pflichtverletzungen: keine
- Visuelle Prüfung: Erz in der offenen Hand vor dem Bauch, Finger umfassen es von unten; ruhig, während der Hammer trifft.
- Bogen: `previews/grips/after/aron_L_ore.png`

### aron – R – hammer

- Aufgabe: power grip on the handle, head forwards; tap the ore
- Fingerdicke 0.0663 Studs, Handlänge 0.781 Studs
- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): [2, 3, 3, 3, 3], Handfläche -0.0129 Studs
- Tiefste Durchdringung -0.0129 Studs; Kontakt auf dem Griffbereich: 100% (Kontakt bei y [-0.24, 0.138])
- Handgelenk gebeugt 5.3° / seitlich 21.7°, in sich verdreht 18.2°, Unterarm gedreht 15.7°, Ellbogen 36.2–121.7°, Oberarm max. 73.3° gehoben
- Verrutschen in der Schleife: 0.0 Studs; größter Handschritt 0.195 Studs, Drehung 8.2°, Naht 0.03
- Abstand Gegenstand ↔ Körper in der Schleife: -0.0252 Studs
- Probleme: keine; Pflichtverletzungen: keine
- Visuelle Prüfung: Kraftgriff am Stiel, Schlagfläche trifft das Erz zweimal (Messung 0,004 Studs), ohne zu streifen. Abzug: Im Rückschwung steht der Ellbogen weit seitlich ab und die Hand bleibt tief (kurzer Schwung aus dem Unterarm); in Ruhe hängt der Hammer schräg vor der Schürze.
- Bogen: `previews/grips/after/aron_R_hammer.png`

### esme – L – folding_rule

- Aufgabe: hold the first leg; sight along the rule
- Fingerdicke 0.0573 Studs, Handlänge 0.687 Studs
- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): [1, 3, 3, 3, 2], Handfläche 0.0045 Studs
- Tiefste Durchdringung -0.0035 Studs; Kontakt auf dem Griffbereich: 100% (Kontakt bei y [-0.171, 0.125])
- Handgelenk gebeugt 1.5° / seitlich 1.1°, in sich verdreht 0.0°, Unterarm gedreht 2.0°, Ellbogen 32.2–60.1°, Oberarm max. 74.5° gehoben
- Verrutschen in der Schleife: 0.0 Studs; größter Handschritt 0.087 Studs, Drehung 2.9°, Naht 0.016
- Abstand Gegenstand ↔ Körper in der Schleife: 0.8117 Studs
- Probleme: keine; Pflichtverletzungen: keine
- Visuelle Prüfung: Zollstock im Spitzgriff vor der Brust beim Peilen; Glieder des Zollstocks schematisch.
- Bogen: `previews/grips/after/esme_L_folding_rule.png`

### esme – R – axe

- Aufgabe: power grip at the lower third of the handle; rest the handle on the shoulder
- Fingerdicke 0.0581 Studs, Handlänge 0.687 Studs
- Glieder mit Kontakt (Daumen, Zeige-, Mittel-, Ring-, kleiner Finger): [1, 3, 3, 3, 2], Handfläche 0.0114 Studs
- Tiefste Durchdringung -0.0038 Studs; Kontakt auf dem Griffbereich: 92% (Kontakt bei y [-0.235, 0.131])
- Handgelenk gebeugt 2.1° / seitlich 20.5°, in sich verdreht 2.0°, Unterarm gedreht 8.6°, Ellbogen 139.6–140.6°, Oberarm max. 35.4° gehoben
- Verrutschen in der Schleife: 0.0 Studs; größter Handschritt 0.011 Studs, Drehung 0.6°, Naht 0.003
- Abstand Gegenstand ↔ Körper in der Schleife: 0.1434 Studs
- Probleme: keine; Pflichtverletzungen: keine
- Visuelle Prüfung: Kraftgriff am unteren Stiel, Stiel liegt auf der rechten Schulter, Axtkopf hinter dem Rücken. Abzug: Das Stielende ragt nah am Kinn vorbei (Hautabstand 0,14 Studs ≈ 3,9 cm), Handgelenk seitlich am Grenzwert (20°).
- Bogen: `previews/grips/after/esme_R_axe.png`

## Werkzeuggebrauch (Testfall D)

- aron: Hammerkopf ↔ Erz über die Schleife (32 Proben/s): kleinster Abstand 0.0043 Studs, Treffer (lokale Minima unter 0,15 Studs) bei [(0.69, 0.0764), (0.75, 0.0674), (1.75, 0.0043), (2.62, 0.0043), (3.5, 0.0674), (3.56, 0.0764)]. Ein Treffer gilt, wenn er 0 ± 0,01 Studs erreicht und der Kopf nie tiefer als 0,01 Studs ins Erz geht.

## Vorher / nachher (automatische Punkte von 85, Pflichtverletzungen)

Vorher = Commit `bcf8da2` (`previews/grips/before/`), gemessen vor Einführung der Messung „Handgelenk in sich verdreht / Unterarmdrehung“; diese Spalte fehlt dort.

| Händler | Hand | vorher | nachher | Pflicht vorher | Pflicht nachher |
|---|---|---|---|---|---|
| selma | L | basket 83.8 | basket 83.8 | – | – |
| selma | R | herb_bundle 65.0 | herb_bundle 84.5 | the hand holds the flowers and leaves (2 contact points); only 85% of the contact lies on the grip region (-0.16, 0.2) (y -0.23..0.13) | – |
| nyra | L | lantern 85.0 | lantern 85.0 | – | – |
| nyra | R | crystal 82.7 | crystal 82.7 | – | – |
| lio | L | cloth 79.4 | cloth 83.8 | only 78% of the contact lies on the grip region (-0.2, 0.2) (y -0.22..0.15) | – |
| lio | R | vial 61.5 | potion_bottle 83.6 | the hand holds the cork (14 contact points); only 51% of the contact lies on the grip region (0.12, 0.47) (y -0.30..0.18) | – |
| aron | L | ore 83.8 | ore 82.7 | – | – |
| aron | R | hammer 79.2 | hammer 85.0 | only 71% of the contact lies on the grip region (-0.15, 0.42) (y -0.24..0.14) | – |
| esme | L | folding_rule 83.8 | folding_rule 83.8 | – | – |
| esme | R | axe 82.2 | axe 82.2 | – | – |

Werkzeuggebrauch aron vorher: {'closest': -0.0589, 'taps': [[0.34, 0.0781], [0.47, 0.0492], [2.5, -0.0411], [2.59, -0.0589]]} (negativ = im Erz).

## Zwei-Hand-Griff (Testfall C, Testszene `blender/grip_test_crate.py`)

- Linke Hand ↔ ihr Kistengriff: 0.001 Studs
- Rechter Arm: {'elbow_flexion': 101.9, 'arm_lift': 27.9, 'wrist_bend': 4.6, 'wrist_sideways': 7.0, 'wrist_twist': 17.2, 'forearm_rotation': 19.8, 'cost': 0.0131}
- Linker Arm: {'elbow_flexion': 107.9, 'arm_lift': 42.2, 'wrist_bend': 5.4, 'wrist_sideways': 17.6, 'wrist_twist': -20.1, 'forearm_rotation': 19.5, 'cost': 0.3671}
- Probleme: ['L finger 5: 1 links on the bar']
- Bogen: `previews/grips/after/crate_two_hands.png`

