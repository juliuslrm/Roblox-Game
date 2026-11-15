# Blocked pending Roblox Studio

Alles hier ist geschrieben, aber nie in Roblox gelaufen. Reihenfolge = sinnvolle Prüfreihenfolge.

| # | Zu prüfen | Datei | Risiko |
|---|---|---|---|
| 1 | Rojo-Sync legt `ArcaneShared`, `ArcaneServer`, `ArcaneClient` richtig an; `Bootstrap` wird Script bzw. LocalScript | `default.project.json` | mittel |
| 2 | Server startet ohne Fehler, Meldung „[Arcane] server ready" | `Bootstrap.server.lua` | hoch – viele API-Aufrufe aus dem Gedächtnis |
| 3 | Marker stehen vor den Gebäuden auf dem Boden (Raycast), nicht darunter oder in Wänden | `Bootstrap.server.lua` | mittel |
| 4 | „Betreten" teleportiert in den Innenraum, „Verlassen" zurück vor die Tür | `WorkshopWorld.lua` | mittel |
| 5 | HUD und Fenster erscheinen, Schaltflächen sind am Handy treffbar | `Bootstrap.client.lua` | hoch |
| 6 | Maschinen-Prompt öffnet das Maschinenfenster; Brauen, Entnehmen, Regal füllen | Client + Server | mittel |
| 7 | Baumodus: Ghost folgt Maus bzw. Bildschirmmitte, Drehrichtung von Ghost, Server und Mesh stimmen überein | Client, `WorkshopWorld.lua` | hoch – Vorzeichen der Drehung ungeprüft |
| 8 | DataStore: Speichern, Verlassen, Wiederbeitritt; Verhalten ohne API-Zugriff in Studio | `ProfileStore.lua` | mittel |
| 9 | Maschinen-Meshes aus `arcane_machines.glb` in `ServerStorage.ArcaneAssets`: Name, Größe, Ausrichtung | `WorkshopWorld.lua` | mittel |
| 10 | 2–4 Spieler: getrennte Innenräume, Co-op-Rechte | Server | mittel |
| 11 | StreamingEnabled: Marker und Innenraum werden rechtzeitig geladen | – | unbekannt |
| 12 | Leistung auf einem Mittelklasse-Handy | – | unbekannt |

Bekannte Annahmen, die falsch sein können:

- `workspace:GetServerTimeNow()`, `ProximityPrompt.Triggered`, `Model:PivotTo`, `UIScale`,
  `AutomaticCanvasSize` sind aus dem Gedächtnis verwendet.
- Innenräume liegen bei x, z ≥ 6000 und y = 800; ob das mit Streaming und Beleuchtung harmoniert,
  ist offen.
- Ohne importierte Maschinen-Meshes zeigt der Server farbige Quader mit Beschriftung. Das ist
  eine Rückfallebene, kein Endzustand.
