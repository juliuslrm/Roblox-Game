# Händler-Überarbeitung: Audit (Phase A)

Stand vor der Überarbeitung: Commit `bb97683`, Place-Version 32.

- **Belege:** `previews/characters/before/<rolle>_views.png` mit 12 Ansichten (Vorderseite, Seite, Rückseite, Dreiviertel, Kopf frontal, Kopf Dreiviertel, Augen, rechte Hand, linke Hand, Kleidung, Gegenstand in Benutzung, Stimmungslicht) und `<rolle>_motion.png` mit 8 Momenten der Schleife.
- **Erzeugt von:** `blender/render_character_qa.py`, mit neutralem Licht und festen Kameras, damit Vorher- und Nachher-Bögen vergleichbar sind.
- **Vertexfarben statt Textur:** Die Bögen zeigen Vertexfarben ohne gebackene Textur. Beurteilt werden Form, Proportion und Verformung, nicht das Backen.

Status je Befund:

| Status | Bedeutung |
|---|---|
| **VERIFIED** | im Bild oder per Messung gesehen |
| **INFERRED** | aus dem Code geschlossen |
| **UNTESTED** | nicht geprüft |
| **BLOCKED** | ohne Studio oder Gerät nicht prüfbar |

## 1. Pipeline (alle Händler)

| Bereich | Befund | Status |
|---|---|---|
| Basismodell | MakeHuman hm08 (CC0), ~13 000 Vertices, anatomisch plausibler Körper und Kopf: Schlüsselbeine, Knie, Hände mit Fingergliedern, Gesicht mit Lidern und Lippen. Das Basismodell ist **nicht** die Schwachstelle. | VERIFIED (Bögen) |
| Skelett | Auf 26 Knochen reduziert. Gesichts- und Fingerknochen wurden mit dem Kopf bzw. Handgelenk verschmolzen: **keine Mimik, kein Blinzeln, keine Augenbewegung, keine beweglichen Finger** in Roblox. | VERIFIED (Code, Place-Messung: 26 Bones) |
| Gesichtsdaten | Das MakeHuman-Skelett enthält gewichtete Gesichtsknochen für Lider, Augen, Brauen, Lippen, Mundwinkel, Wangen und Kiefer. Sie wurden bisher verworfen. | VERIFIED (`default.mhskel`, Gewichte) |
| Kleidungskanten | Kleidung = Körperfläche nach außen versetzt. Die Randvertices wurden auf den **Mittelwert** mehrerer Schnittpunkte geschoben, Eck-Faces fielen zusammen → gezackte, zerrissen wirkende Kanten an Westen, Kragen, Ausschnitten und Schürzenlätzen. | VERIFIED (alle Bögen) |
| Augen | Die Wimpern sind die MakeHuman-Hilfsstreifen (Karten für Alpha-Texturen). Massiv schwarz gefärbt wirken sie als **dicker Lidstrich**. Dazu kommt eine 12-%-Abdunklung ums Auge: verschlafener, geschminkter Blick. | VERIFIED |
| Haare | Bandförmige Strähnen auf einer Kappe. Aus der Nähe wirken sie wie zerrissenes Papier oder Späne (Lio, Esme), dazu ein helmartiger Rand. | VERIFIED |
| Haltung | Exakt symmetrisch, Füße parallel, Knie gestreckt, Becken gerade: statuenhaft. | VERIFIED |
| Animation | 8 Bilder/s, zwischen den Samples linear interpoliert: Knicke in der Geschwindigkeit. Eine einzige Schleife je Figur, kein Atmen unabhängig von der Schleife, keine Zustände (Begrüßen, Handeln), keine Reaktion auf Spieler, kein Blinzeln. | VERIFIED (Code `MarketIdle.client.lua`, `MarketMotion.lua`) |
| Gesichtsausdruck | Keiner möglich (kein Gesichts-Rig). | VERIFIED |
| Hände | Gute Grundform, Finger verjüngt, Griffe gemessen und gerendert (`docs/GRIP_VALIDATION_REPORT.md`). Finger in Roblox nicht beweglich (eingebacken). | VERIFIED |
| Material | Eine Albedo-Textur je Mesh (Farbe × Struktur × AO), in Roblox als `TextureID`. Keine Normal- oder Roughness-Maps. `SurfaceAppearance` lässt sich laut Doku per Skript fast nicht setzen und müsste im Asset liegen. | VERIFIED (Doku, Code) / Import-Weg UNTESTED |
| Roblox-Darstellung | Haut, Verformung und Licht in Roblox nie gesehen. | BLOCKED (kein Studio, kein Gerät) |

## 2. Je Händler

### Lio (Glas)
- **Stärken:** glaubwürdige Gesichtsproportionen; Flaschengriff um den Körper, Korken oben; Hände gut geformt (VERIFIED).
- **Schwächen:**
  - Weste und Hemdkragen zerfranst; der Hemdausschnitt reicht als nackte Brust bis zum Gürtel (VERIFIED).
  - Haare wie Papierfetzen (VERIFIED).
  - Lidstrich-Wimpern (VERIFIED).
  - Starre symmetrische Haltung (VERIFIED).
  - Beim „gegen das Licht halten“ verdeckt die Hand aus der Schrägansicht das Auge (VERIFIED, aus der Griffvalidierung bekannt).
- **Rig/Animation:** siehe Pipeline.
- **Roblox:** Hautverformung an Schultern und Ellbogen ungesehen (BLOCKED).

### Esme (Holz und Stein)
- **Stärken:** Axt am Stiel im Kraftgriff, Zollstock im Spitzgriff (VERIFIED).
- **Schwächen:**
  - Weste vorne und hinten zerfranst, darunter nackte Haut sichtbar (VERIFIED).
  - Haare als Späne (VERIFIED).
  - Lidstrich (VERIFIED).
  - Der Axtstiel läuft in der Seitenansicht vor dem Mund vorbei (VERIFIED).
  - Unter neutralem Licht stark überstrahlt: helle Haut, sehr gesättigtes Türkis (VERIFIED, Farbwahl).
  - Haltung symmetrisch (VERIFIED).

### Selma (Kräuter)
- **Stärken:** Zöpfe glaubwürdig, Korb im Hakengriff, Kräuterbund (VERIFIED).
- **Schwächen:** Lidstrich (VERIFIED); Schürzenlatz mit zerfranster Kante (VERIFIED); Haltung symmetrisch (VERIFIED).

### Nyra (Kristalle)
- **Stärken:** Silhouette mit Kapuze und Umhang klar erkennbar (VERIFIED).
- **Schwächen:**
  - Lange Haare als Bänder (VERIFIED).
  - Kristallspitze an den Haarsträhnen (VERIFIED, Griffbericht).
  - Lidstrich (INFERRED, gleiche Pipeline).

### Aron (Erz)
- **Stärken:** kräftige Statur, Bart, Schürze; Hammerschläge treffen das Erz (VERIFIED, Messung).
- **Schwächen:** Ellbogen beim Ausholen weit seitlich (VERIFIED); Bart/Haare als Bänder (VERIFIED); Haltung symmetrisch (VERIFIED).

## 3. Zielarchitektur (Entscheidung)

| Komponente | Entscheidung | Grund | Nachteil |
|---|---|---|---|
| Körper | MakeHuman-Basis **behalten**, Haltung asymmetrisch (Standbein, Beckenkippung, Gegenbewegung der Wirbelsäule) | Anatomie ist gut; der Fehler lag in Haltung und Ausarbeitung | Gesichtstopologie bleibt die von MakeHuman (keine eigene Skulptur) |
| Kleidung | **Exakter Polygon-Schnitt** an der Nulllinie des Feldes (geteilte Schnittvertices) | beseitigt die Zacken an der Ursache | Ngons, die beim Export trianguliert werden |
| Augen, Wimpern | Einzelne, spitz zulaufende Wimpern an der Lidkante; schwächere Abdunklung | kein Lidstrich mehr | Wimpern als Geometrie, ~1 300 Dreiecke |
| Haare | Kurze Krauslocken als Volumen statt Bänder; übrige Frisuren schrittweise | Bänder wirken aus der Nähe wie Papier | Volumen ohne Einzelsträhnen |
| Gesichts-Rig | 16 MakeHuman-Gesichtsknochen bleiben im Rig; Ausdrücke als Knochenposen (Drehung + Verschiebung) | Roblox spielt Knochen ab, keine Shape-Key-Animation aus eigenen Skripten | Mimik grober als mit Blendshapes |
| Finger | 30 Fingerknochen bleiben im Rig; der Griff ist ihre Ruhepose | Übergänge und Gesten möglich | 72 statt 26 Knochen je Figur |
| Animation | Mehrere Clips je Figur (Idle, Idle-Variante, Begrüßen), höhere Abtastrate, kubische Interpolation, Überblendung; Atmen, Blinzeln, Blick und Kopfwendung prozedural im Client | natürlicher, nicht synchron, reagiert auf Spieler | mehr Client-Rechenzeit (begrenzt durch Entfernung) |
| Laufzeit-IK | **nicht** verwendet; Armhaltungen weiter offline gelöst | feststehende Figuren, messbar, günstig | keine dynamische Anpassung an Objekte |
| PBR | `SurfaceAppearance` erst nach einem Import-Test mit einem Probe-Asset | Doku: per Skript fast nicht setzbar | bis dahin nur Albedo |
| Detailstufen | Gesicht, Finger, Atmen und Blick nur in der Nähe; weiter weg nur Körperschleife; ganz weit ruhig | spart Client-Zeit | Übergänge der Stufen ungesehen |
