# Händler-Animation: Spezifikation

## Daten (Blender → Roblox)

| Quelle | Inhalt |
|---|---|
| `characters.LOOPS[rolle]` | Clip `idle`: Schlüssel je Kanal (Grad, Figurachsen), geschlossene Schleife |
| `characters.IDLE2[rolle]` | Clip `idle2`: Versätze zur ersten Pose von `idle` (startet und endet dort) |
| `characters._greet(rolle)` | Clip `greet`: additiv (Nicken, leichte Verbeugung, Lächeln, Brauen), 2,4 s |
| `characters.FACE_POSES` | Gesichtsposen (siehe `CHARACTER_RIG_SPEC.md`) |
| `world/solved_poses.json` | per IK gelöste Armhaltungen (`blender/solve_poses.py`), Grundlage der Arm-Schlüssel |

- `build_characters.py` schreibt die Schlüssel unverändert nach `roblox/gameplay/shared/MarketMotion.lua`; das sind 22 KB statt bisher 90 KB abgetasteter Quaternionen.
- `MarketPose.lua` wertet sie in Roblox **exakt** wie Python aus.
- `tests/test_market_pose.py` vergleicht 14 400 Knochenrotationen und die Gesichtsgewichte. Größte Abweichung: 0,00000°.

## Interpolation

- **Monoton kubisch (Fritsch–Butland):** Zwischen Schlüsseln laufen Bewegungen ohne Halt durch; an Haltepunkten und Umkehrpunkten ist die Steigung null, und nichts schwingt über.
- **Loops:** Bei Schleifen wird die Naht wie jeder andere Schlüssel behandelt.
- **Vorher:** Smoothstep zwischen je zwei Schlüsseln. Die Bewegung hielt dadurch an **jedem** Schlüssel an (Stottern bei dichten Pfaden wie Arons Schlag), und 8 Bilder/s wurden linear verbunden.
- **Atmen:** auf `spine01`, ganzzahlig viele Atemzüge je Schleife (≈ 3,4 s), damit die Naht glatt bleibt.

## Zustände im Client (`MarketIdle.client.lua`)

```
Idle (idle | idle2, Wechsel an der Schleifengrenze, 0,4 s überblendet)
  + Greet (additiv, 2,4 s)      ← Server setzt Figure.GreetAt beim Öffnen des Handels;
                                  oder der Spieler tritt näher als 9 Studs heran (höchstens alle 25 s)
  + Look  (Kopf 40 % Hals / 60 % Kopf, ±38° seitlich, ±16° hoch/tief, geglättet 0,45 s)
          nur wenn der Spieler < 16 Studs entfernt und vor der Figur ist;
          Aufmerksamkeit wechselt: 2,5–6 s hinsehen, 1,2–3 s wegsehen (kein Dauerstarren)
  + Augen (führen den Kopf, ±22°/±14°, 0,06 s), sonst kleine Sakkaden alle 0,7–2,6 s
  + Blinzeln (alle 2,2–6 s, 15 % Doppelblinzeln, auch bei großer Kopfwendung)
  + Mimik (Gewichte aus den Clips: lächeln, konzentrieren, skeptisch …)
```

## Detailstufen nach Entfernung der Kamera

| Entfernung | Was läuft |
|---|---|
| < 40 Studs | alles (Körper, Blick, Augen, Blinzeln, Mimik), jedes Bild |
| 40–130 Studs | nur Körper-Clip, jedes dritte Bild |
| > 130 Studs | Ruhepose (einmal gesetzt) |

## Geprüft / offen

- **Lokal geprüft:**
  - Lua = Python (`test_market_pose.py`);
  - Clips geschlossen, `idle2` beginnt in der Startpose von `idle`;
  - Handgelenkgrenzen über alle Clips und das Begrüßen (`test_grip_profiles.py`);
  - Werkzeuge nicht im Körper über alle Clips (Build-Check `prop_clearance`);
  - Begrüßung wird beim Handel ausgelöst (Mock-Test).
- **UNVERIFIED_IN_STUDIO:** der Client selbst (Überblendung, Blick, Augen, Blinzeln, Detailstufen) läuft nur in Roblox und ist nur syntaktisch geprüft.
- **Nicht umgesetzt:** Gehen, Aufnehmen und Ablegen von Gegenständen. Die Händler stehen fest am Stand; die Fingerknochen sind für solche Übergänge vorbereitet.
