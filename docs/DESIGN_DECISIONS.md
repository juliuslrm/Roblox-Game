# Design decisions (Arcane Village)

Versionierte Entscheidungen, die die Master-Spezifikation (`ARCANE_VILLAGE_CLAUDE_MASTER_SPEC.md`,
bleibt unverändert) konkretisieren oder von ihr abweichen.

| # | Entscheidung | Grund |
|---|---|---|
| D1 | Entwicklung auf `claude/roblox-village-blender-xekw0z` statt auf einem neuen Branch `feat/arcane-village-gameplay` | Die Cloud-Sitzung darf nur auf diesen Branch pushen. Der Gameplay-Code liegt vollständig unter `roblox/gameplay/` und ist damit sauber vom Welt-Code getrennt; ein Feature-Branch kann jederzeit daraus erzeugt werden. |
| D2 | Domain-Logik als reine Lua-5.1-Module ohne Roblox-API (`roblox/gameplay/server/*Service.lua`), Roblox-Zugriffe nur in Adaptern (`Bootstrap.server.lua`, `VillageAdapter.lua`, `WorkshopWorld.lua`, `ProfileStore.lua`, Client) | Spec §12: außerhalb von Studio testbar. Die Adapter sind `UNVERIFIED_IN_STUDIO`. |
| D3 | Ein zentraler Einstieg `Actions.handle(session, action, payload)` für alle Client-Anfragen | eine Stelle für Typprüfung, Rate-Limit, Idempotenz und Rechte (Spec §12, §14). |
| D4 | Förderbänder nehmen Ware von hinten **und von beiden Seiten** an und geben nach vorn ab | Kurven in beide Richtungen ohne gespiegeltes Bauteil; `belt_turn` bleibt als eigenes Bauteil (hinten rein, links raus). |
| D5 | Kisten und Regale haben passive Eingänge auf allen Seiten und keinen eigenen Ausgang; nur `input_hopper` entnimmt | entspricht „Übergabe Container→Band" (Spec §7), verhindert Schleifen Kiste↔Kiste. |
| D6 | Rohre sind ungerichtet; ein zusammenhängendes Rohrnetz transportiert pro Tick genau einen Flüssigkeitstyp, Tanks im Netz sind gemeinsamer Puffer | einfache, kontaminationssichere Typisierung (Spec §7). |
| D7 | `fuel_charcoal` ist ein Sammelrohstoff (Meiler an der Schmiede), nicht kaufbar | Spec nennt ihn als Rohstoff; kein Kauf-/Verkaufskreislauf. |
| D8 | Zellen des Werkstattrasters sind 2 × 2 Studs; Footprints in der Spec (Studs) werden durch 2 geteilt | Spec §6: Rasterabstand 2 Studs. |
| D9 | Das Kräuterbeet gibt das Saatgut im Ausgang zurück; es läuft nur dauerhaft, wenn das Saatgut zurückgeführt wird | hält die Regel „keine Gratisproduktion" ein und macht den Anbau zu einer kleinen Logistikaufgabe. |
| D10 | Der Client erhält einmal pro Sekunde und nach jeder Aktion einen vollständigen Snapshot statt `StateDelta` | einfacher und für 4 Spieler ausreichend; Deltas sind eine spätere Optimierung. |
| D11 | Servicegebäude haben in v1 Außenstationen (Marker mit Prompt), nur die Spielerwerkstatt hat einen Innenraum | Spec §3 erlaubt Außenstationen; der Markt-Innenraum ist als offen vermerkt. |
| D12 | Mehr als zwei Kisten erfordern die Forschung „Lagerhaltung" (10 Wissen) | macht die erste Forschung nach dem Tutorial sofort nützlich; die erste Förderkette braucht sie. |
