# Händler-Überarbeitung: QA-Bericht

Stand: Place-Version 35 (2026-11-19).

- **Vorher:** Commit `bb97683` / Place 32.
- **Bilder:**
  - `previews/characters/before/` und `after/`: je Händler `_views.png` (12 Ansichten) und `_motion.png` (8 Momente der Idle-Schleife);
  - `after/<rolle>_face.png`: neutral und jede Gesichtspose, frontal und Dreiviertel;
  - `previews/characters/compare_<rolle>.png`: Vorher/Nachher mit gleichen Kameras.
- **Render-Hinweis:** Die Bögen zeigen Vertexfarben ohne gebackene Textur und mit neutralem Licht. Helle Hauttöne (Esme, Nyra) überstrahlen darin; das ist eine Schwäche des Prüflichts, nicht der Figur. In Roblox kommen Textur und AO dazu, aber das ist dort nicht gesehen.

## Was sich geändert hat (alle Händler)

| Bereich | Vorher | Nachher | Beleg |
|---|---|---|---|
| Kleidungskanten | gezackt, zerfranst | exakt geschnitten, glatte Säume | compare-Bögen, Spalten 1, 2 und 6 |
| Augen | dicker schwarzer Lidstrich, verschlafen | einzelne Wimpern, offene Lider, weichere Augenschatten | compare-Bögen, Spalte 4 |
| Haare | Bänder wie Papier oder Späne | Volumen mit Locken- bzw. Feinstruktur, auslaufender Haaransatz; Nyras lange Strähnen rund und hinter den Schultern | compare-Bögen, Spalte 3 |
| Bart (Aron) | Bandsträhnen | dichter Vollbart als Volumen, Lippen frei, bewegt sich mit dem Kiefer | `compare_aron.png` |
| Haltung | symmetrisch, steif | Standbein, Beckenkippung, Gegenneigung der Wirbelsäule, gebeugtes Spielbein | Rückansichten in `_views.png` |
| Leder (Latz, Westen) | zeichnete die Bauchmuskeln nach | liegt flacher auf | `after/aron_views.png` |
| Gesicht | unbeweglich | 16 Gesichtsknochen; blinzeln, lächeln, Brauen, konzentrieren, sprechen, skeptisch | `after/<rolle>_face.png` |
| Finger | eingebacken, keine Knochen | 30 Fingerknochen, Griff als Ruhepose | Place-Messung: 73 Bones |
| Animation | 8 Bilder/s, Halt an jedem Schlüssel, eine Schleife, kein Blick | Schlüssel exakt ausgewertet, monoton kubisch; zwei Idle-Clips; Begrüßen; Blick, Augen, Blinzeln, Mimik; Detailstufen | `docs/CHARACTER_ANIMATION_SPEC.md` |

## PBR-Oberflächen (Version 35)

**Probe (gemessen):** Ein FBX, dessen Material Normal-, Rauheits-, Metall- und Alphakarte hat, wird von Roblox beim Upload in eine `SurfaceAppearance` übersetzt:

- `ColorMap`, `NormalMap`, `RoughnessMap` und `MetalnessMap` werden als eigene Bild-Assets angelegt.
- Ein Material mit Alpha-Anschluss erhält `AlphaMode = Transparency`.
- Das gilt auch für skinned Meshes.
- Skripte können die Karten nicht lesen, sie liegen aber im Asset.

**Seitdem backt `build_characters.py` je Mesh zusätzlich:**

| Karte | Inhalt |
|---|---|
| Normalkarte | Relief je Material: Hautporen, Stofffasern, Ledernarbung, Filz, Haarsträhnen |
| Rauheit | Augen und Glas glatt, Haut mit Schwankung, Stoff und Filz matt |
| Metall | Messing |

- **Detailgrenze:** Das Relief ist gröber als ein Texel gehalten; feinere Gewebe erzeugten Moiré.
- **Gemessen im Place:** 51 von 51 Händler-Meshes haben eine `SurfaceAppearance` mit Normalkarte.
- **Bild:** `previews/market/05-gesichter-pbr.png` (texturiert, Cycles).
- **Offen:**
  - Haarkarten mit Alpha sind möglich, aber noch nicht gebaut.
  - Das Strähnenrelief läuft quer statt entlang des Haars; beim Bart fällt das als Streifen auf.
  - Lios und Esmes Westen haben noch kleine Kerben an den Rändern.
  - Wie Roblox die Karten auf Geräten mit niedriger Grafikstufe darstellt, ist ungesehen.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis | Status |
|---|---|---|
| `scripts/check_all.sh` (Gameplay, Place, Registry, Griffe/Handgelenke über alle Clips, Lua = Python, Weltvalidierung) | alle bestanden | PASS_AUTOMATED |
| `tests/test_market_pose.py`: 14 400 Knochenrotationen und Gesichtsgewichte, Lua gegen Python | größte Abweichung 0,00000° bzw. 1e-16 | PASS_AUTOMATED |
| `blender/validate_grips.py`: 10 Griffe | 0 Pflichtverletzungen; Arons Hammer trifft das Erz zweimal mit 0,0037 Studs (≈ 1 mm) | PASS_AUTOMATED |
| Build-Checks (`build_characters.py`): Dreiecke je Mesh ≤ 19 500, ≤ 4 Einflüsse, Werkzeug nicht in der Haut über alle Clips und das Begrüßen | 0 Probleme. Arons Hammerstiel kommt der Haut beim Übergang zum Ausholen bis 0,018 Studs (≈ 5 mm) nahe, Grenze 0,03 | PASS_AUTOMATED |
| Upload der 5 FBX, Laden im Place, Serverstart | 5 Rigs, je 9–12 skinned + texturierte Meshes, 73 Knochen, Füße auf dem Boden | PASS_IMPORT |
| Posen-Nachbau auf dem Roblox-Server mit `MarketPose` (`idle`, `idle2`, Begrüßen) | Handgelenke höchstens 0,0001 Studs neben Blender | PASS_RUNTIME (nur Server-Mathematik und Knochenhierarchie) |
| Client-Animation (Überblendung, Blick, Augen, Blinzeln, Mimik, Detailstufen) | nur Syntax- und Mock-Prüfung | UNVERIFIED |
| Hautverformung von Gesicht, Fingern und Handgelenken in Roblox | nicht gesehen (Roblox rechnet sie nur beim Rendern) | UNVERIFIED |
| Leistung (78 000–138 000 Dreiecke je Händler, 73 Knochen, Client-Rechenzeit) | nicht gemessen | UNVERIFIED |

## Qualitätsmatrix (eigene Bewertung nach Ansicht der Bögen)

Gewichte laut Auftrag: Anatomie 15, Gesicht 20, Hände 20, Bewegung 20, Kleidung 10, Identität 10, Technik 5. Das ist ein internes Schema und kein Nachweis von Realismus. Bewegung wurde nur in Blender (Kontaktbögen) und als Zahlenvergleich gesehen, nicht laufend in Roblox.

| Händler | Anatomie | Gesicht | Hände | Bewegung | Kleidung | Identität | Technik | Summe | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Lio | 11 | 15 | 15 | 12 | 7 | 7 | 4 | **71** | FAIL (Ziel 90) |
| Esme | 11 | 14 | 14 | 11 | 7 | 7 | 4 | **68** | FAIL (Ziel 90) |
| Selma | 11 | 14 | 15 | 11 | 8 | 8 | 4 | **71** | FAIL (Ziel 90) |
| Nyra | 11 | 14 | 13 | 11 | 7 | 8 | 4 | **68** | FAIL (Ziel 90) |
| Aron | 12 | 13 | 15 | 12 | 7 | 8 | 4 | **71** | FAIL (Ziel 90) |

Begründung der Abzüge (für alle ähnlich):

- **Gesicht:**
  - Die Form ist MakeHuman-Durchschnitt: glaubwürdig, aber ohne skulptierte Einzelheiten wie Poren, Falten oder Lippenrelief.
  - Keine Normal-Maps; die Mimik wirkt nur in der Nähe.
  - Arons Mund wirkt durch die Bartgrenze leicht geöffnet.
- **Hände:** Griffe gemessen und gerendert. Finger in Roblox beweglich, aber zur Laufzeit nicht animiert; keine Nägel als eigene Form.
- **Bewegung:** Systematisch stark verbessert, aber in Roblox nie laufend gesehen. Die Schleifen sind von Hand gesetzte Schlüssel, keine Bewegungsaufnahme.
- **Kleidung:** Saubere Kanten, aber keine echten Stofffalten aus Simulation, keine Nähte, keine Material-Maps.
- **Lio:** Bei „gegen das Licht“ verdeckt die Hand aus der Schrägansicht das Auge.
- **Esme:**
  - Das Stielende läuft ≈ 3,9 cm vor dem Kinn vorbei. Der Ellbogen steht an seiner Grenze von 140°; tiefer geht die Hand nur mit einem Griff weiter unten am Stiel (neues Griffprofil).
  - Helle Haut überstrahlt im Prüflicht.
- **Nyra:**
  - Der Haaransatz unter der Kapuze ist unruhig.
  - Die Kristallspitze reicht an die Haare.
  - Die Handfläche liegt 1,2 cm vom Kristall entfernt.

## Was für das 90-Punkte-Ziel fehlt (konkret)

1. **Oberflächendetail** (seit Version 35 teilweise erfüllt: prozedurale Normal- und Rauheitskarten; ein skulptierter Hochdetail-Bake fehlt weiter):
   - Normal- und Roughness-Maps für Haut, Stoff und Leder aus einem hochauflösenden Sculpt gebacken.
   - In Roblox über `SurfaceAppearance`, das laut Doku per Skript fast nicht setzbar ist. Ob der FBX-Import eine `SurfaceAppearance` anlegt, muss mit einem Probe-Asset getestet werden.
2. **Haare als Karten mit Alpha:** Nur mit `SurfaceAppearance.AlphaMode`, also abhängig von Punkt 1.
3. **Sichtprüfung im laufenden Spiel** (Studio oder Gerät): Hautverformung, Mimik, Blick, Überblendung, Leistung.
4. **Fingeranimation** für Übergänge und Gesten (Knochen vorhanden).
5. **Bewegungen** mit mehr Gewichtsverlagerung über Becken und Beine; dafür braucht es Bein-IK, sonst rutschen die Füße.

## Grenzen dieser Umgebung

- Kein Roblox Studio und kein Gerät. Gemessen wird per Open Cloud nur auf dem Server; alles Clientseitige ist UNVERIFIED.
- Blender läuft ohne GPU (Cycles auf der CPU). Ein Händler-Build mit Texturen dauert ~25 min.
