---
title: Designentscheidungen D1–D17
aliases: [Designentscheidungen, Decisions]
tags: [entscheidungen, referenz]
---

# Designentscheidungen D1–D17

Zurück: [[Arcane Village – Übersicht]] · Quelle: `docs/DESIGN_DECISIONS.md`

| # | Entscheidung | Kurz-Grund |
|---|---|---|
| D1 | Arbeit auf `claude/roblox-village-blender-xekw0z` | Cloud darf nur dorthin pushen; Gameplay sauber unter `roblox/gameplay/` |
| D2 | Domain-Logik als reines Lua 5.1, Roblox nur in Adaptern | außerhalb von Studio testbar |
| D3 | Ein Einstieg `Actions.handle` | eine Stelle für Typen, Rate-Limit, Idempotenz, Rechte |
| D4 | Bänder nehmen von hinten **und** seitlich | Kurven in beide Richtungen ohne Spiegelteil |
| D5 | Kisten/Regale passiv, nur Trichter entnimmt | keine Kiste↔Kiste-Schleifen |
| D6 | Rohre ungerichtet, ein Typ je Netz | kontaminationssicher, einfach |
| D7 | Holzkohle ist Sammelrohstoff | Spec nennt sie als Rohstoff |
| D8 | Raster 2 × 2 Studs | Spec §6 |
| D9 | Kräuterbeet gibt Saatgut zurück | keine Gratisproduktion |
| D10 | Vollständiger Snapshot 1/s statt Deltas | einfacher, für 4 Spieler genug |
| D11 | Servicegebäude als Außenstationen | Spec erlaubt es |
| D12 | > 2 Kisten erst nach „Lagerhaltung“ | erste Forschung sofort nützlich |
| D13 | Offene Werkstatt auf eigenem Grundstück, hineinlaufen | Wunsch des Auftraggebers; ersetzt Teleport |
| D14 | Wählbare Ein-/Auslaufseite, Auto-Auslauf | Auftrag vom 2026-11-16 |
| D15 | Item-Symbole als Emoji-Kacheln (später Bildbogen) | keine gemalten Bilder vorhanden |
| D16 | Ware nur auf dem Client, 0,6 s verzögert | flüssig ohne Vorhersagefehler → [[Ware auf Förderbändern]] |
| D17 | Förderteile vom Linienende her abarbeiten | kein Ruckeln auf vollen Bändern |

## Spätere Entscheidungen (Händler, nicht nummeriert)
- **Eigenes Skelett statt R15/Humanoid:** Händler sind MakeHuman-Rigs mit `AnimationController`.
  `Tool`/`RightGrip` brauchen einen Humanoid und passen nicht. → [[Händler-Animation in Roblox]]
- **Kein `IKControl` zur Laufzeit:** braucht einen Animator, lohnt bei feststehenden Figuren nicht.
  Armhaltungen werden in Blender per IK gelöst und eingebacken → [[Arm-IK und Bewegungsschleifen]].
- **Finger eingebacken:** In Roblox gibt es keine Fingerknochen; der Griff wird beim Bauen gelöst.
