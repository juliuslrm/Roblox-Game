# Gameplay-Architektur

```
Client (StarterPlayerScripts.ArcaneClient)        Server (ServerScriptService.ArcaneServer)
  NetworkClient ── RemoteFunction ArcaneRequest ──▶ Bootstrap.server ─▶ Actions.handle ─▶ Services
  Bootstrap.client ◀─ RemoteEvent ArcaneEvent ───── (Snapshot 1/s, Meldungen)
                                                    Heartbeat ─▶ Game.tick ─▶ WorkshopSimulation.step
                                                    WorkshopWorld (Instanzen)   ProfileStore (DataStore)
Shared (ReplicatedStorage.ArcaneShared): reine Datentabellen + GridMath, Protocol, Validator
```

## Schichten

| Schicht | Dateien | Roblox-API? | Getestet |
|---|---|---|---|
| Daten | `shared/Config, Items, Recipes, Machines, Research, Quests, Locations` | nein | `test_data.py` |
| Domain | `server/*Service.lua`, `Actions`, `Game`, `WorkshopSimulation`, `CoOpPermissions`, `VillageAdapter`, `ProfileStore` | nein | `spec_*.lua` |
| Adapter | `server/Bootstrap.server.lua`, `server/WorkshopWorld.lua` | ja | nur Syntax |
| Client | `client/NetworkClient.lua`, `client/Bootstrap.client.lua` | ja | nur Syntax |

Die Domain-Module laden einander mit `require(script.Parent.X)` und die Daten über
`game:GetService("ReplicatedStorage").ArcaneShared`. Der Test-Harness (`tests/harness.py`) stellt
dafür minimale `script`/`game`-Objekte bereit – es laufen dieselben Dateien wie in Roblox.

## Wer schreibt was (genau ein Schreiber pro Datenart)

| Daten | Modul |
|---|---|
| Münzen, Wissen, Ruf | `EconomyService` |
| Item-Bestände (Beutel, Puffer) | `InventoryService` (Regeln), bewegt durch `Actions`, `LogisticsService`, `ProductionService` |
| Werkstatt-Layout, Blueprints | `PlacementService` |
| Jobs, Rezeptverbrauch, Ausgaben | `ProductionService` |
| Transport fest/flüssig | `LogisticsService` |
| Regalverkäufe | `ShopService` |
| Quests, Aufträge, Stränge | `QuestService` |
| Forschung | `ResearchService` |
| Sammelknoten | `ResourceService` |
| Profil laden/speichern | `ProfileService` (Form), `ProfileStore` (DataStore) |
| Co-op-Rechte | `CoOpPermissions` |

## Ablauf einer Anfrage

`Actions.handle(world, session, action, payload, ctx)`:

1. `SecurityService.validate` – nur deklarierte Felder mit geprüftem Typ (`Protocol.actions`),
   Ganzzahlen begrenzt, IDs als kurze Wörter, keine Instanzpfade
2. Rate-Limit pro Spieler und Aktion (Token-Bucket)
3. Wiederholungsschutz über `actionId` (letzte 64)
4. Safe-Mode-Sperre, wenn das Profil nicht geladen werden konnte
5. Handler: Rechte (Co-op-Rolle), Nähe (Position kommt vom Server), Freischaltung, Kosten
6. Ergebnis `{ ok, code, version, payload }`; der Server hängt den aktuellen Snapshot an

Der Client sendet nie Positionen, Preise, Mengen an Geld oder Objektpfade.

## Simulationsschritt (`WorkshopSimulation.step`, 0,25 s)

Graph bei Layoutänderung neu bauen → feste Güter bewegen → Flüssigkeiten bewegen → Jobs starten,
fortschreiben, abschließen → Kunden → Kennzahlen. `dt` ist auf 1 s begrenzt, pro Maschine höchstens
4 Zyklen je Schritt. Kein Offline-Fortschritt: Jobs frieren beim Speichern ein und laufen nach dem
Laden weiter.

## Transportregeln

- Zellen 2 × 2 Studs; Richtung 0 = +z (vorn), 1 = +x, 2 = −z, 3 = −x; Drehung dreht die Ports mit.
- Maschinen: fester Eingang hinten Mitte, Ausgang vorn Mitte; Flüssigkeit links rein, rechts raus.
- Bänder nehmen von hinten und von den Seiten, geben nach vorn ab; 1 Stück je 2 s.
- Kisten/Regale nehmen von allen Seiten an; nur der Trichter entnimmt (aus Kiste oder Maschinenausgang).
- Rohre sind ungerichtet; ein Netz hat ein Budget von 500 ml/s; Tanks halten genau einen Typ.
- Aufzug gibt eine Etage höher nach vorn ab; Tore brauchen einen Partner (`SetFilter { link }`).

## Dorf-Anbindung

`VillageAdapter.computeAnchors(layout)` findet zu jedem Ort die Instanz über die Asset-ID und setzt
den Anker 5 Studs vor die Vorderseite. Sammelknoten liegen relativ dazu (`Locations.nodes`). Wird
die Welt neu generiert, wandern alle Anker mit. Der Welt-Builder kennt das Gameplay nicht.
