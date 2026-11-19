---
title: Werkstatt, Bauen und Logistik
tags: [gameplay, werkstatt, logistik, bauen]
---

# Werkstatt, Bauen und Logistik

Zurück: [[Arcane Village – Übersicht]] · Doku: `docs/WORKSHOP.md` · Verwandt: [[Ware auf Förderbändern]]

![[previews/workshop/03-fabrikausbau.png]]

## Die Werkstatt
- Offenes Gebäude auf einem eigenen Grundstück (D13); Größen **32 / 48 / 64 / 80 Studs**,
  **1–3 Etagen**, Treppe mit reservierter Öffnung.
- Der Server erkennt aus der Position, in wessen Werkstatt eine Figur steht
  (`WorkshopWorld:ownerAt`, `world.plotPresence`).
- Startausstattung: Kessel, Kiste, Verkaufsregal.
- Gemessen (Place): Boden 0,6 Studs über Plan, alle vier Öffnungen frei, Kessel steht auf dem Boden.

## Raster und Richtungen
- Zellen 2 × 2 Studs (D8); Richtung 0 = +z, 1 = +x, 2 = −z, 3 = −x.
- Standard: fester Eingang hinten Mitte, Ausgang vorn Mitte; Flüssigkeit links rein, rechts raus.

## Wählbare Anschlüsse (D14, `MachinePorts.lua`)
- Einlauf- und Auslaufseite wählbar, Auslauf „Automatisch“ oder „Manuell“.
- **Automatik:** Der Auslauf wandert zu einer Seite, an der ein Förderteil direkt wegführt.
  Bewertung nach jedem Setzen/Drehen/Entfernen → Baureihenfolge egal.
- Alte Spielstände verhalten sich wie bisher (hinten rein, vorn raus).

## Transportregeln

| Teil | Regel |
|---|---|
| Band | nimmt von hinten **und den Seiten** (D4), gibt nach vorn, 1 Stück je 2 s |
| Kurve `belt_turn` | hinten rein, seitlich raus, echter Viertelbogen |
| Kiste / Regal | nimmt von allen Seiten, hat keinen Ausgang (D5) |
| Trichter | entnimmt aus Kiste oder Maschinenausgang |
| Rohr | ungerichtet; Netz 500 ml/s; ein Flüssigkeitstyp je Netz (D6) |
| Tank | genau ein Typ, ml-genau |
| Aufzug | gibt eine Etage höher nach vorn ab |
| Magisches Tor | braucht einen Partner (`SetFilter { link }`) |

- Volle Linien rücken im selben Takt vor: Abarbeitung vom Ende der Linie her (D17).

## Bauen
- Platzieren, Abbauen (60 % Erstattung), Drehen; Kosten werden serverseitig geprüft.
- **Bandstrecken** (`BeltPath.lua`, Aktion `PlaceBelts`): Anfang und Ende wählen (PC ziehen, Handy
  antippen–antippen–✓), höchstens eine Ecke, ⟳ kehrt um, X verwirft. Server baut **ganz oder gar
  nicht** (max. 64 Zellen).
- **Weißes Hologramm:** echtes Modell weiß, SmoothPlastic, leicht durchscheinend, `Highlight`-Umriss;
  rot bei belegt/außerhalb/reserviert. Raster auf der aktuellen Etage.
- Eine gemeinsame Regel `PlacementPose.lua` für Server und Hologramm → gemessen deckungsgleich
  (Abweichung 0,0000).

## Maschinenfenster (`MachineWindow.lua`)
Zutaten links, Fortschritt Mitte, Ergebnis rechts, Draufsicht der Anschlüsse, darunter Rezepte.
Item-Bilder aus einem gerenderten Bildbogen (`ItemIconSheet.lua`), Emoji nur als Rückfall (D15).

> [!bug] Gespiegelte Drehung (behoben)
> Maschinen mit 90°/270° wurden gespiegelt dargestellt: `CFrame.Angles(0, −90°·rot, 0)` statt
> `+90°·rot`. Im Place nachgerechnet und korrigiert.

> [!warning] Am Gerät ungeprüft
> Bedienung des Fensters auf Touch, Ziehen/Tippen beim Bandbau, Wirkung des Leuchteffekts.
