# Lio – Referenzfigur der neuen Charakter-Pipeline

Stand 2026-11-20 (Place-Version 37). Werkzeugentscheidung: `docs/CHARACTER_TOOL_DECISION.md`; Lizenzen: `docs/CREDITS.md`.

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
| `belt` | `previews/lio/04-belt.png` | Gürtel von vier Seiten |

Alles läuft als Code; vom CharMorph-Add-on wird nichts ausgeführt, nur die Daten werden geladen.

| Teil | Datei | Kern |
|---|---|---|
| Körper, Haut | `blender/village/reom.py` | Reom-Mesh, Morphs (Ethnie, Muskel, Kiefer, Brauenbogen …), Hautshader mit Melanin, Rötung und Lippentönung |
| Haare | `blender/village/hair.py` | Brauen aus Reoms Leitsträhnen (+10 Kinder je Strähne), krauses Kopfhaar als Helix-Strähnen auf der Kopfhautmaske |
| Rig | `blender/village/reom_rig.py` | 167 Deform-Knochen aus Rigify-Metarig und Gelenkdaten, alle Finger, Gesicht, eigene Augenknochen |
| Kleidung | `blender/village/garments.py` | Schnitt an Iso-Linien, Abstand zu darunterliegenden Lagen, Stoffsimulation mit eingezogenen Rändern (Hemd, Hose), Schürze als hängende Fläche, prozedurale Materialien |
| Posen, Griff | `blender/village/posing.py` | analytische Arm-IK, Fingerschluss bis Kontakt, Kalibrierung der Achsen je Hand, Blick, Messung am verformten Mesh |

## Gemessene Griffe (`03-reference.json`, `exports/library/trader_lio.json`)

Die Flasche hängt im Spiel starr an der rechten Hand. Deshalb hält rechts in jeder Pose; links poliert.

| Pose | Finger mit Kontakt | Tiefste Hautdurchdringung | Handgelenk-Knick |
|---|---|---|---|
| Gegen das Licht | alle 4 + Daumen | 2,6 mm | 15–16° |
| Anbieten | alle 4 + Daumen | 2,6 mm | 6–7° |
| Polieren | rechts alle 4 + Daumen, links alle 4 + Daumen | 2,6 mm | 7,5° |

„Kontakt“ heißt: Ein Fingerknochen liegt innerhalb von 8,5 mm Fingerradius an der Flaschenwand.

Zwei Verbesserungen gegenüber dem ersten Stand:

- **Weniger Knick:** Die Handfläche dreht sich je Pose um die Flaschenachse, bis der Knick am kleinsten ist (vorher bis 61°).
- **Gegen das Licht:** Ellbogen auf Schulterhöhe, Flasche um etwa 20° geneigt; Pose und Neigung aus einer Suche über 64 Varianten.

## Gürtel

**Erster Stand (Rückmeldung „der Gürtel sitzt nicht“):** Der Gürtel war ein starrer Ring um den nackten Körper. Gemessen an 72 Punkten schwebte er bis 16 mm über der Hose und lag an 11 Punkten bis 6 mm in der Schürze.

**Jetzt:**

- Hosenbund und Schürze werden im Gürtelband an die Taille gezogen. Volle Wirkung über die Gürtelbreite, nach oben und unten über 4 cm auslaufend.
- Der Gürtel liegt auf der äußersten Schicht unter seiner ganzen Breite, vorne 1,2 cm tiefer.
- Oberhalb des Gürtels folgt die Schürze dem Oberkörper und hängt erst darunter frei.

**Gemessen an 96 Punkten:** 0 Punkte in der Kleidung, Luft 1,6–10,6 mm. Die größeren Werte liegen über Hosenfalten am Rücken.

## Roblox (Händler-ID `lio`)

```
/opt/bpyenv/bin/python blender/export_lio.py -- --tex 1024     # FBX, Texturen, trader_lio.json (~20 min)
/opt/bpyenv/bin/python blender/build_characters.py -- --motion-only   # MarketMotion.lua, TraderArt.lua
```

`build_characters.py` baut die alte Lio-Figur nicht mehr; es übernimmt Lios Einträge aus `exports/library/trader_lio.json`. Die Daten der anderen vier Händler sind nachweislich unverändert (Vergleich der Lua-Tabellen vorher/nachher).

**Export (`blender/export_lio.py`):**

- **Ruhepose:** Ruhepose des Rigs ist die Polierpose, so steht Lio auch mit pausierter Animation (fern der Kamera) natürlich.
- **Schlüsselposen:** sechs gelöste Schlüsselposen, nämlich Polieren, Polieren mit gleitender Hand, Gegen das Licht (zwei Drehstellungen) und Anbieten (zwei).
  - Clips: `idle` 8,4 s, `idle2` 7 s, `greet` additiv (Nicken und Lächeln).
  - 28 Kanäle, einer je bewegtem Knochen inklusive Finger, im Format von `MarketPose`.
- **Meshes:**
  - Kopf, sichtbare Haut, Haarkappe, Kleidung (2), Zubehör, Glas: 7 Meshes mit höchstens 19 468 Dreiecken je Mesh, zusammen 55 749.
  - Höchstens 4 Knochen je Vertex.
  - Haut unter der Kleidung entfernt (2 338 Flächen); Hornhautkappen vor der Iris geöffnet.
- **Haare und Brauen:** Das Kopfhaar wird als Kappe mit weichem Haaransatz (Alpha) gebacken. Die Augenbrauen werden Härchen für Härchen in die Gesichtstextur gemalt.
- **Texturen:** Farbe mit Umgebungsverdeckung, Normal-, Rauheits- und Metallkarte (1024 px, Kleinteile 512 px); Glas halbtransparent.
- **Gesichtsposen:** Blinzeln, Lächeln und Brauen heben über die Rigify-Gesichtsknochen (`previews/lio/09-roblox-face.png`).
- **Laufzeit:** `MarketPose`, `MarketIdle` und das Server-Prüfskript nehmen jetzt je Händler eigene Kanäle sowie Atem-, Hals-, Kopf-, Augen- und Handgelenksknochen. Ohne diese Angaben gelten die alten Namen.

| Prüfung | Ergebnis | Status |
|---|---|---|
| Schlüssel reproduzieren die gelösten Posen (Vorwärtskinematik) | höchstens 0,011 mm Abweichung | PASS_AUTOMATED |
| Flasche liegt in allen Posen gleich in der Hand | 0,00 mm | PASS_AUTOMATED |
| Flasche über beide Schleifen nie im Körper (15 Proben/s, Hände ausgenommen) | 0,0 mm | PASS_AUTOMATED |
| `test_market_pose.py`: Lua = Python für Lio | 1 344 Rotationen, höchstens 0,0001° | PASS_AUTOMATED |
| `scripts/check_all.sh` | alle bestanden | PASS_AUTOMATED |
| Upload (Asset 131339803075041), Laden im Place 37 | 7 Meshes, alle skinned und texturiert, alle mit Normalkarte; 167 Knochen; Höhe 6,48 Studs | PASS_IMPORT |
| Posen auf dem Roblox-Server mit `MarketPose` nachgestellt | Handgelenke höchstens 0,0001 Studs neben Blender | PASS_RUNTIME |
| Darstellung im Client (Haut, Haarkappe, Glas, Gesichtsposen, Blick, Leistung mit 167 Knochen) | ohne Studio/Gerät nicht gesehen | UNVERIFIED |

Bei der Server-Prüfung gefunden und behoben: Der Atemknochen stand in keinem Kanal. Client und Server registrieren nur Knochen aus Kanälen, also hätte Lio im Spiel nicht geatmet. Die Handgelenke lagen dadurch 0,032 Studs daneben.

## Eigene Einschätzung (nach Ansicht der Bilder)

**Gut:**

- Körper, Hände mit Nägeln und Venen, Hautstruktur und Haar wirken menschlich und deutlich hochwertiger als die bisherigen prozeduralen Händler.
- Die Finger umschließen die Flasche sichtbar; die Posen wirken natürlicher als im ersten Stand.

**Schwächen:**

- **Haarkappe im Spielmodell:** Sie wirkt dunkelgrau wie Filz statt wie krauses Haar, weil der Glanz jeder Oberfläche die fast schwarze Farbe aufhellt. Die Strähnen der Blender-Bilder gibt es im Spiel nicht.
- **Gesicht im Spielmodell:** Es ist heller und flacher als im Blender-Bild, weil die Subsurface-Streuung beim Backen wegfällt.
- **Kleidung:**
  - Prozedurale Materialien ohne Nähte; das Leder wirkt eher wie Kunststoff.
  - Die Stiefel sind klumpig.
  - Der Halsausschnitt hat keinen Kragen.
- **Gesicht:**
  - Der Ausdruck bleibt starr.
  - Das Lächeln ist schwach.
  - Die Augenwinkel sind sehr rot.
- **Daumen:** Er liegt nur mit der Spitze an.
- **Füße:** Sie stehen im Place 0,03 Studs unter dem Bodenpunkt (≈ 8 mm).

## Nächste Schritte

1. Sichtprüfung im Spiel (Studio oder Gerät) und Rückmeldung.
2. Danach Esme, Selma, Nyra, Aron mit derselben Strecke.
