# Lio – Referenzfigur der neuen Charakter-Pipeline

Stand 2026-11-19. Werkzeugentscheidung: `docs/CHARACTER_TOOL_DECISION.md`; Lizenzen: `docs/CREDITS.md`.

## Bau

```
scripts/fetch_charmorph_db.sh                 # Reom-Daten (CC-BY) nach assets/thirdparty/charmorph-db
/opt/bpyenv/bin/python blender/build_lio.py -- --stage poses --samples 64
```

Die Stufen bauen aufeinander auf:

| Stufe | Ergebnis | Inhalt |
|---|---|---|
| `face` | `previews/lio/00-face.png` | Kopf vorne, Dreiviertel, hinten |
| `dressed` | `previews/lio/02-dressed.png` | bekleidet in A-Pose |
| `poses` | `previews/lio/03-reference.png` und `03-reference.json` | A-Pose, Hände, drei Posen, Griffmessung |

Alles läuft als Code; vom CharMorph-Add-on wird nichts ausgeführt, nur die Daten werden geladen.

| Teil | Datei | Kern |
|---|---|---|
| Körper, Haut | `blender/village/reom.py` | Reom-Mesh, Morphs (Ethnie, Muskel, Kiefer, Brauenbogen …), Hautshader mit Melanin, Rötung und Lippentönung |
| Haare | `blender/village/hair.py` | Brauen aus Reoms Leitsträhnen (+10 Kinder je Strähne), krauses Kopfhaar als Helix-Strähnen auf der Kopfhautmaske |
| Rig | `blender/village/reom_rig.py` | 167 Deform-Knochen aus Rigify-Metarig und Gelenkdaten, alle Finger, Gesicht, eigene Augenknochen |
| Kleidung | `blender/village/garments.py` | Schnitt an Iso-Linien, Abstand zu darunterliegenden Lagen, Stoffsimulation mit eingezogenen Rändern (Hemd, Hose), Schürze als hängende Fläche, prozedurale Materialien |
| Posen, Griff | `blender/village/posing.py` | analytische Arm-IK, Fingerschluss bis Kontakt, Kalibrierung der Achsen je Hand, Blick, Messung am verformten Mesh |

## Gemessene Griffe (`03-reference.json`)

| Pose | Finger mit Kontakt | Tiefste Hautdurchdringung | Handgelenk-Knick |
|---|---|---|---|
| Gegen das Licht | alle 4 + Daumen | 3,0 mm | 61° |
| Anbieten | alle 4 + Daumen | 1,7 mm | 7° |
| Polieren (zweihändig) | alle 4 + Daumen, beide Hände | 1,8 mm | 50° / 56° |

„Kontakt“ heißt: Ein Fingerknochen liegt innerhalb von 8,5 mm Fingerradius an der Flaschenwand. In der Hautmessung liegen die Fingerglieder dann zwischen −1,8 und +3 mm an der Oberfläche.

## Eigene Einschätzung (nach Ansicht der Bilder)

**Gut:**

- Körper, Hände mit Nägeln und Venen, Hautstruktur und das krause Haar wirken menschlich und deutlich hochwertiger als die bisherigen prozeduralen Händler.
- Die Finger umschließen die Flasche sichtbar.

**Noch nicht auf dem Niveau aktueller realistischer Fantasy-Spielfiguren:**

- **Kleidung:**
  - Prozedurale Materialien ohne Nähte, Säume und Abnutzung; das Leder wirkt eher wie Kunststoff.
  - Die Stiefel sind klumpig.
  - Der Halsausschnitt ist ein glatter Schnitt ohne Kragen.
- **Haut scheint durch:** Am gehobenen Arm („Gegen das Licht“) drückt die Schulter durch das Hemd und erscheint als dunkler Fleck.
- **Gesicht:**
  - Glaubwürdig, aber der Ausdruck bleibt starr.
  - Das Lächeln beim Anbieten ist kaum sichtbar.
  - Die Augenwinkel sind sehr rot.
  - An den Mundwinkeln bleibt eine Glanzlinie.
- **Handgelenke:** Bei „Gegen das Licht“ und „Polieren“ ist das Handgelenk mit 50–61° stark abgeknickt.
- **Daumen:** Er liegt nur mit der Spitze an.
- **Roblox:** noch nicht umgesetzt.
  - Reduktion auf ≤ 20 000 Dreiecke je Mesh fehlt.
  - Haare und Materialien sind noch nicht in Texturen gebacken.
  - Die 4 Einflüsse je Vertex sind noch nicht durchgesetzt (622 Vertices haben mehr).
  - Abbildung auf die `MarketPose`-Kanäle und der Upload fehlen.

## Nächste Schritte nach Freigabe

1. Rückmeldung zu Gesicht, Kleidung und Posen einarbeiten.
2. Roblox-Konvertierung: Dezimierung, Texturbacken (Farbe, Normal, Rauheit), Haarkarten, Gewichte auf 4 begrenzen, Bone-Mapping, Animation als Schlüssel unter der bestehenden Händler-ID `lio`.
3. Erst danach Esme, Selma, Nyra, Aron.
