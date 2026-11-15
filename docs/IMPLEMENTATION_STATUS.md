# Implementation status – Arcane Village

Statuswerte: `DONE` (implementiert und lokal getestet), `PARTIAL`, `OPEN`, `UNVERIFIED_STUDIO`
(Code vorhanden, läuft nur in Roblox Studio und wurde dort **nicht** ausgeführt).

Teststufen: `TESTED_LOCAL` = Lua 5.5 (lupa) + Python in der Cloud. **Keine einzige Funktion ist
`TESTED_STUDIO` oder `TESTED_DEVICE`.** Roblox Studio stand nicht zur Verfügung.

Ein Befehl für alle lokal ausführbaren Prüfungen: `./scripts/check_all.sh` (`--full` baut zusätzlich
die Gameplay-Assets neu und wiederholt den Rückseiten-Audit).

Letzter geprüfter Stand: siehe `git log` (dieser Commit). Ergebnis von `check_all.sh`:
data_integrity OK · 40 Lua-Dateien kompilieren · spec_core 33/33 · spec_progression 26/26 ·
spec_adapter 11/11 · Dorf-Builder-Mock bestanden · Weltvalidierung 34/34 · Gameplay-Assets 0 Probleme.

## Übersicht

| Phase | Inhalt | Domain-Logik | Roblox-Anbindung / UI |
|---|---|---|---|
| 0 | Audit, Baseline | DONE | – |
| 1 | Daten + Domain-Kern | DONE · TESTED_LOCAL | – |
| 2 | Dorf-Adapter, Werkstatt-Hülle | DONE (Anker) · TESTED_LOCAL | UNVERIFIED_STUDIO (Innenraum, Teleport, Marker). OPEN: Markt-Innenraum, Tutorial-NPC als Figur |
| 3 | Kernloop | DONE · TESTED_LOCAL | UNVERIFIED_STUDIO (HUD, Beutel, Maschinenfenster). OPEN: sichtbare Kunden-NPCs |
| 4 | Produktion, Automatisierung | DONE · TESTED_LOCAL | UNVERIFIED_STUDIO (Baumodus mit Ghost). PARTIAL: Warenanzeige nur als Marke auf Bändern |
| 5 | Dorfwirtschaft, Forschung | DONE · TESTED_LOCAL | UNVERIFIED_STUDIO (Forschungs- und Auftragsfenster). OPEN: Weltkarte |
| 6 | Flüssigkeiten, Etagen | DONE · TESTED_LOCAL | UNVERIFIED_STUDIO (Treppe, Etagenböden). PARTIAL: Kennzahlen-Fenster zeigt nur Durchsatz/Lager |
| 7 | High-Tier-Inhalte | DONE · TESTED_LOCAL | – |
| 8 | Co-op, Blueprints | DONE · TESTED_LOCAL | OPEN: keine Bedienoberfläche für Einladungen und Blueprints |
| 9 | Art, Polish, Performance | PARTIAL: 31 Maschinen-Meshes gebaut und geprüft | OPEN: Animation, Sound, VFX, Performance-Messung |
| 10 | Studio-Übergabe | DONE (Doku, `check_all.sh`) | BLOCKED pending Studio |

## Phase 0 – Repo audit: DONE

Ausgangsbranch `claude/roblox-village-blender-xekw0z` @ `4d3fc9c`; Baseline 34/34 und Builder-Mock
grün; Arbeitsbranch derselbe (Entscheidung D1 in `DESIGN_DECISIONS.md`); generierte Weltdateien
unverändert.

## Phase 1 – Daten und Domain-Kern: DONE

- Dateien: `roblox/gameplay/shared/*.lua` (Config, Items, Recipes, Machines, Research, Quests,
  Locations, Protocol, GridMath, Util, Validator), `roblox/gameplay/server/*Service.lua`,
  `Actions.lua`, `Game.lua`, `WorkshopSimulation.lua`
- Umfang: 45 Items, 30 Herstellrezepte + 5 Versorgungsrezepte, 18 Maschinen, 13 Lager-/Logistikteile,
  28 Forschungsknoten, 20 Hauptquests, 20 Auftragsvorlagen, 8 NPC-Stränge (24 Schritte),
  3 Dorfprojekte, 16 Orte, 22 Sammelknoten
- Test: `test_data.py`, `run_tests.py spec_core`
- Demo-Pfad: `spec_core.lua` „job reserves inputs …" (Start → erster Trank)

## Phase 2 – Dorf und Werkstatt-Hülle

- DONE/TESTED_LOCAL: `VillageAdapter.computeAnchors` leitet alle 16 Orte und 22 Knoten aus
  `WorldLayout.lua` ab; geprüft gegen die 25 echten Gebäudegrundrisse (`spec_adapter`).
- UNVERIFIED_STUDIO: `WorkshopWorld.lua` (begehbarer Raum aus Parts, Etagen, Treppe, Ausgangstür),
  `Bootstrap.server.lua` (Teleport hinein/hinaus, Rückholung bei Sturz, Marker mit ProximityPrompts).
- OPEN: eigener Markthallen-Innenraum; NPC-Figuren (bisher leuchtende Marker mit Prompt).

## Phase 3 – Kernloop

- DONE/TESTED_LOCAL: Sammeln mit Knotenbestand und Nachwachsen, Handbrauen, Beutel, Regal,
  Kundenkäufe aus echtem Bestand, Münzen, Quests q01–q05, Speichern/Laden (`ProfileService`,
  `ProfileStore` mit Sitzungs-Lock, Revisionsprüfung, Wiederholungen).
- `starter_playthrough`: `spec_adapter` „the real anchors drive a full first sale" und
  `spec_progression` q01–q04.
- UNVERIFIED_STUDIO: `client/Bootstrap.client.lua` (HUD, Beutel, Maschinenfenster, Meldungen).

## Phase 4 – Automatisierung

- DONE/TESTED_LOCAL: Raster 2 Studs, Platzieren/Abbauen/Drehen mit Kosten und 60 % Erstattung,
  Zustandsmaschine der Maschinen, Kisten, Bänder, Trichter, Verteiler, Zusammenführer,
  Transportgraph, Rückstau, deterministischer Tick, Wiederanlauf nach Laden.
- Demo-Pfad: `spec_core` „crate -> hopper -> belt -> machine -> belt -> crate runs without hands".

## Phase 5 – Dorfwirtschaft und Forschung

- DONE/TESTED_LOCAL: Auftragstafel (3 Angebote, Tageslimit für Ruf), 8 NPC-Stränge, Ruf 0–5 mit
  Preisfaktor, Forschungs-DAG mit Vorbedingungen, Knoten-Freischaltungen, Brennstoff, Kräuterbeet,
  Dorfprojekt (sitzungsweit, jede Spende einmal gezählt).
- PARTIAL: Ruf wirkt bisher auf Preise und Kundenfrequenz, schaltet aber noch keine eigenen
  Dorfdienste frei.

## Phase 6 – Flüssigkeiten und Etagen

- DONE/TESTED_LOCAL: Pumpe, Rohre, Tanks (ein Flüssigkeitstyp je Tank, ml-genau), Etagenkauf,
  Aufzug, Filtersortierer, Durchsatzmessung über gleitende Fenster.

## Phase 7 – High-Tier-Inhalte

- DONE/TESTED_LOCAL: alle 30 Rezepte, T4–T5, Endprodukt; ein Bot löst q01→q20, alle 24
  Strangschritte und stellt jedes Rezept mindestens einmal her – nur über Client-Aktionen, ohne
  injizierte Items (`spec_progression`).
- Hinweis: Die Zeiten des Bots (54 min bis q20) sind eine Untergrenze bei perfektem Spiel mit
  4 s Laufweg; echte Spielzeiten liegen deutlich höher.

## Phase 8 – Co-op und Blueprints

- DONE/TESTED_LOCAL: Rollen visitor < operator < builder < owner serverseitig, Einladen/Entziehen,
  Host verlässt → Gäste werden ausgeworfen, Blueprints speichern und atomar platzieren.
- OPEN: Bedienoberfläche dafür im Client.

## Phase 9 – Art und Performance

- DONE/TESTED_LOCAL: 31 Maschinen-/Logistik-Meshes (`blender/village/machines.py`,
  `blender/build_gameplay_assets.py`), 5 264 Dreiecke gesamt, Footprint-, glTF-, UV- und
  Rückseitenprüfung ohne Befund; Vorschau `previews/assets/machines_1.png`, `machines_2.png`.
- OPEN: Animationen, Sound, Partikel, NPC-Wege, englische Lokalisierung, Performance-Messung.

## Phase 10 – Studio-Übergabe

- DONE: `docs/ROBLOX_GAMEPLAY_IMPORT.md`, `docs/GAMEPLAY_ARCHITECTURE.md`,
  `docs/BLOCKERS_STUDIO.md`, `docs/CHANGELOG_GAMEPLAY.md`, `scripts/check_all.sh`.
- BLOCKED pending Studio: Import, erster Start, alle Punkte der Testmatrix.

## Offene Punkte gegenüber der Spezifikation

| Spec | Fehlt |
|---|---|
| §3 | Markt-Innenraum; Kollisionsanpassung um Portale ist ungeprüft |
| §8 | sichtbare Kunden-NPCs (Kauf läuft logisch); Dorfprojekt verändert die Welt noch nicht sichtbar |
| §10 | Blueprint-Bedienung, Innenausbau-Varianten |
| §11 | Screens Weltkarte, Rezept-Codex, Production Insights (nur Basiswerte), Loading/Recovery nur als Meldung; Texte nur Deutsch |
| §12 | Client in zwei statt zwölf Dateien; `StateDelta` nicht umgesetzt (vollständige Snapshots, 1/s) |
| §15 | keine Messung; Bandsegmente werden nicht zu Läufen komprimiert |
| §14 | Monetarisierung bewusst nicht enthalten |
