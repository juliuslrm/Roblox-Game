# Changelog Gameplay

## 0.1.1 – detaillierte Maschinen

- Alle 31 Werkstatt-Bauteile neu modelliert: Detail-Baukasten (Rohre mit Flanschen, Zahnräder,
  Handräder, Manometer, Eisenbänder mit Nieten, Einzelbohlen, Pflastersockel, Kristalle, Runen)
- Jede Maschine zeigt ihre Anschlüsse: Trichter hinten (Eingang), Rutsche vorn (Ausgang),
  Rohrstutzen links mit blauem Ring (Flüssigkeit rein), rechts mit orangem Ring (raus)
- Dreiecksbudget je Bauteil von 1 500 auf 4 500 angehoben; Summe 34 668

## 0.1.0 – erste durchgängige Version (nur lokal getestet)

- Datenbasis: 45 Items, 30 Rezepte (+5 Versorgung), 18 Maschinen, 13 Logistik-/Lagerteile,
  28 Forschungsknoten, 20 Hauptquests, 20 Auftragsvorlagen, 8 NPC-Stränge, 3 Dorfprojekte
- Domain-Kern in reinem Lua: Inventar, Wirtschaft, Platzierung, Produktion, Logistik (fest und
  flüssig), Laden, Quests, Forschung, Sammelknoten, Co-op-Rechte, Blueprints
- Zentraler Aktions-Dispatcher mit Validierung, Rate-Limit, Wiederholungsschutz, Safe Mode
- Persistenz mit Sitzungs-Lock und Revisionsprüfung
- Dorf-Adapter: Anker aus dem generierten Layout
- Roblox-Anbindung (Server, Innenraum, Client-UI) – ungeprüft in Studio
- 31 Maschinen-Meshes aus Blender
- Tests: 33 Kern-, 26 Fortschritts-, 11 Adaptertests, Datenintegrität, Syntax

### Beim Testen gefundene und behobene Fehler

- Statistik-Warteschlange nutzte `#` auf einer Tabelle mit Lücken; nach dem ersten Aufräumen
  gingen neue Einträge verloren (q15/q18 wären nie erfüllbar gewesen)
- Extraktor-Mesh ragte aus seiner Rasterfläche, Rohr-Meshes lagen nicht auf dem Boden

### Bewusste Abweichungen

Siehe `docs/DESIGN_DECISIONS.md`.
