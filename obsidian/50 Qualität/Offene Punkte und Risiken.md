---
title: Offene Punkte und Risiken
tags: [qualität, offen, todo]
---

# Offene Punkte und Risiken

Zurück: [[Arcane Village – Übersicht]] · Quelle: `docs/BLOCKERS_STUDIO.md`, `docs/IMPLEMENTATION_STATUS.md`

## Am Gerät / in Studio nie gesehen
- [ ] Aussehen der ganzen Welt in Roblox (Licht, Farben, Vegetation)
- [ ] Client-UI auf dem Handy: HUD, Beutel, Maschinenfenster, Handeln-Dialog, Seitenknöpfe
- [ ] Bauen per Touch (Tippen, Bandstrecke, Hologramm-Leuchten)
- [ ] Ware auf Bändern, Querstege, Aufzug/Tor-Animation
- [ ] Hautverformung der Händler, besonders an den Handgelenken
- [ ] Kamera in der Werkstatt, Treppen, Etagen
- [ ] 2–4 Spieler gleichzeitig, Co-op-Rechte live
- [ ] StreamingEnabled-Verhalten
- [ ] **Leistung auf einem Mittelklasse-Handy** (602 000 Dreiecke Welt, 340 000 davon Vegetation; Händler je ~95 000)

## Funktionen, die fehlen
- [ ] Markt-Innenraum (Servicegebäude sind Außenstationen)
- [ ] Sichtbare Kunden-NPCs (Kauf läuft nur logisch)
- [ ] Dorfprojekt verändert die Welt nicht sichtbar
- [ ] Weltkarte, Rezept-Codex, ausführliche Kennzahlen
- [ ] Bedienoberfläche für Co-op-Einladungen und Blueprints
- [ ] Sound, Partikel/VFX, englische Texte
- [ ] `StateDelta` statt Snapshots (bewusst verschoben, D10)
- [ ] Monetarisierung (bewusst nicht enthalten)
- [ ] Händler: Gegenstand wechseln, Gehen (feststehende Figuren, keine Fingerknochen)

## Bekannte Mängel
| Mangel | Wo |
|---|---|
| 0,9 % der Bodenpunkte > 1,5 Studs Kollisionsabweichung, schlimmster 24 Studs | Bachufer/Weltrand, Ursache offen |
| Nyras Kristallspitze an den Haaren | Haare nicht in der Kollisionsprüfung |
| Lio verdeckt schräg von rechts sein Auge beim „Licht“ | Pose |
| Aron: Ellbogen beim Ausholen weit seitlich | Pose |
| Esme: Stielende nah am Kinn, Handgelenk seitlich am Limit | Pose |
| Kisten-Test: linker kleiner Finger nur 1 Glied am Griff | Testszene |
| Zaunsegmente starr 8 Studs, folgen Hängen nur über die Höhe | Welt |
| Kein eigener LOD-Satz | Welt |
| Gebäude ohne Innenräume | Welt |
| Alte Geländebibliothek liegt noch im Roblox-Konto (nicht geladen) | Konto |

## Annahmen, die falsch sein können
- `workspace:GetServerTimeNow()`, `ProximityPrompt.Triggered`, `Model:PivotTo`, `UIScale`,
  `AutomaticCanvasSize` wurden aus dem Gedächtnis verwendet (Server-Teil inzwischen im Place
  gelaufen, Client-Teil nicht).
- Interiors bei x, z ≥ 6000 / y = 800 (frühere Variante) vs. Streaming und Licht.
