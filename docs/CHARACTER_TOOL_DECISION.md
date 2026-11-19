# Charakter-Pipeline: Werkzeugentscheidung

Stand 2026-11-19. Anlass: Die prozedural aus Code gebauten Händler erreichen den gewünschten realistischen Eindruck nicht (`docs/CHARACTER_QA_REPORT.md`). Neue Händler sollen aus einer professionellen Charakterbasis entstehen.

## Rahmenbedingungen dieser Arbeitsumgebung (geprüft)

- Linux-Container ohne GPU und ohne Desktop: Blender läuft nur als Python-Modul (`bpy`). Windows- und Mac-Programme mit Oberfläche laufen hier nicht.
- Netz: Die Seiten von Reallusion, Meshy, Human Generator, Mixamo, Sketchfab, Poly Haven und die MakeHuman-Assetserver sind durch die Netzwerkregeln der Umgebung gesperrt (Proxy-Antwort 403). GitHub-Repositories lassen sich klonen.
- Ich kann keine Lizenzen kaufen und keine Konten anlegen.

## Vergleich

Quellen: Herstellerseiten, Dokumentation und Fachpresse (Links unten). Alle Preise sind Recherche-Stand und vor dem Kauf zu prüfen.

| Werkzeug | Erreichbare Qualität | Anatomie, Gesicht, Hände | Fantasy-Kleidung | Automatisierung | Export Blender / Roblox | Lizenz / Kosten | Nacharbeit |
|---|---|---|---|---|---|---|---|
| **Character Creator 5** (Reallusion) | sehr hoch, Standard für realistische Spiel-NPCs | ausmodellierte Basis mit Fingern, Gesichtsrig, hochwertige Haut; mit Headshot individuelle Gesichter aus Fotos | großer Kleidungs- und Haar-Store, Import aus Marvelous Designer und Blender | kaum (Desktop-Programm mit Oberfläche, Windows/Mac) | FBX, OBJ, USD; offizielle Blender-Brücke. Roblox nicht offiziell genannt; FBX → Blender → Roblox ist der Weg | unbefristet ≈ 299 $ (Standard) / 479 $ (Deluxe), zeitweise rabattiert; Abo-Option. Laut EULA dürfen Modelle **eingebettet in Spiele** verteilt werden; verboten sind Charakter-Generatoren und die Weitergabe von Rohdateien | Reduktion auf ≤ 20 000 Dreiecke je Mesh, Haarkarten, Bone-Mapping, Griffe |
| **Human Generator Ultimate** (Blender-Add-on) | hoch (realistische Haut, Haare, Kleidung) | gute Körper und Gesichter, Rigify-Rig mit Fingern, Ausdrücke | Kleidungsbibliothek; eigene Kleidung in Blender | **Python-API** ab V4 („in Entwicklung“), läuft in Blender; Betrieb ohne Oberfläche nicht dokumentiert | nativ Blender, dann FBX → Roblox | kommerziell ≈ 128 $, privat ≈ 68 $. Assets dürfen in Spielen (geschlossenes Format) verteilt werden, FBX-Dateien nicht weitergegeben werden | Haarpartikel → Haarkarten, Reduktion, Bone-Mapping |
| **MPFB2** (MakeHuman für Blender) | mittel; derselbe MakeHuman-Grundkörper wie bisher, aber bessere Skin-Shader, Wimpern, Brauen, Haar- und Kleidungs-Proxies | gleiche Basis wie die verworfenen Figuren | Community-Proxies (CC0/CC-BY gemischt) | Python im Blender-Add-on, Open Source | nativ Blender | Code GPL, Kern-Assets CC0, Community-Assets teils CC-BY: kostenlos, kommerziell nutzbar | Assetserver hier gesperrt; Qualitätsgrenze der Basis bleibt |
| **Meshy** (KI Text/Bild → 3D) | für Requisiten brauchbar; realistische Gesichter und Hände unzuverlässig, Topologie für Verformung ungeeignet | – | ja, aber eingebacken | REST-API (Bezahlplan ab ≈ 20 $/Monat) | GLB/FBX | Bezahlpläne kommerziell; kostenlos nur CC BY 4.0 | hoch (Retopologie, Rig, Hände) |
| **Mixamo** (Adobe) | nur Rigging und Animation | – | – | keine offizielle API (Web-Oberfläche) | FBX | kostenlos, kommerziell lizenzfrei; keine Weitergabe von Rohdateien | ergänzt jede Basis um Animationen |
| **Asset-Shops** (Fab, CGTrader, TurboSquid, Sketchfab) | sehr unterschiedlich | je nach Modell | selten passend zum eigenen Stil | – | FBX | je Modell verschieden. **MetaHuman ist ausgeschlossen** (nur für Unreal Engine lizenziert) | Lizenz je Asset prüfen, Stil passt selten zu fünf Händlern |

## Entscheidung (aktualisiert: nur kostenlose Werkzeuge und Assets)

Vorgabe des Auftraggebers: **nichts bezahlen.** Damit fallen Character Creator 5, Human Generator und die Bezahlpläne von Meshy weg.

**Gewählt: Reom aus der CharMorph-Datenbank (CC-BY) als Körper-, Gesichts- und Hautbasis; Bau, Kleidung, Rig, Griffe und Roblox-Strecke in meiner Blender-Automatisierung.**

| Kriterium | Reom (CharMorph-db) |
|---|---|
| Qualität | realistisch skulptierter Körper (≈ 8 400 Vertices, sauber in Quads), 4K/8K-Hauttexturen für helle und dunkle Haut mit Poren-, Rauheits- und Höhenkanälen, Augen mit Iris, Hornhaut und Tränenkarunkel |
| Gesicht, Hände | eigene Gesichtsform, 52 ARKit-Gesichtsformen (Blinzeln, Kiefer, Lächeln …), Hände mit getrennten Fingern, Nägeln und Venen |
| Anpassung | Hunderte Morphs (Ethnie, Muskel, Fett, Kiefer, Wangen, Lippen …), Augenbrauen als Haarsträhnen |
| Rig | Rigify-Gewichte für 165 Deform-Knochen inklusive aller Finger und des Gesichts |
| Automatisierung | reine Daten (`.blend`, `.npz`, Bilder): ich lade sie mit `bpy`, ohne Add-on-Code auszuführen |
| Lizenz, Kosten | **CC-BY**, kostenlos, kommerziell nutzbar mit Namensnennung (Mesh: ComplexAce; Morphs und Texturen: Hope), siehe `docs/CREDITS.md` |
| Nacharbeit | Kleidung, Kopfhaar, Rig-Übertragung auf `MarketPose`, Reduktion und Texturbacken für Roblox (≤ 20 000 Dreiecke je Mesh) |

**Nachteil:** Kleidung und Kopfhaar bringt Reom nicht mit; die baue ich in Blender (Kleidung über den Körper geformt, Haar als Strähnen, für Roblox gebacken). Ein Profi-Werkzeug wie CC5 würde hier mehr fertige Fantasy-Kleidung liefern.

**Ausgeschlossen:**

- **MB-Lab-Figuren** (in derselben Datenbank): erzeugte Modelle stehen unter AGPL-3, für ein geschlossenes Spiel ungeeignet.
- **MPFB2 / MakeHuman:** kostenlos und CC0, aber dieselbe Basis wie die verworfenen Figuren.
- **Blender Studio Human Base Meshes (CC0):** wären geeignet, der Download ist in dieser Umgebung durch die Netzregeln gesperrt.
- **Meshy Free:** Ergebnisse stehen unter CC BY 4.0, aber Gesichter, Hände und Topologie taugen nicht für verformbare Figuren.
- **Mixamo:** kostenlos und lizenzfrei, aber ohne API und nur über die Weboberfläche; ich animiere über die eigenen Posen-Kanäle.

Die Vergleichstabelle oben enthält weiter die Bezahlwerkzeuge; die frühere Empfehlung (CC5, Alternative Human Generator) ist nicht mehr der Plan.

## Strecke ab der Basis

1. **Import und Prüfung:** Skelett mit Fingern, Gewichte, Dreiecke, Texturen; ein Bericht mit Messwerten.
2. **Optimierung für Roblox:**
   - höchstens 20 000 Dreiecke je Mesh, Haare als Karten mit Alpha;
   - Karten (Farbe, Normal, Rauheit, Metall) für die `SurfaceAppearance`, die laut Probe beim FBX-Import entsteht;
   - höchstens 4 Einflüsse je Vertex.
3. **Rig-Abgleich** auf die Kanäle von `MarketPose` (Körper, Hände, Finger, Gesicht).
4. **Griffe:**
   - Lios Flasche mit den echten Fingerknochen der neuen Basis lösen und messen;
   - A-Pose, dann die Marktposen;
   - Renderbögen: vorne, hinten, Seite, Gesicht, beide Hände, Hand mit Flasche, drei Animationsposen.
5. **Roblox:** Upload, Einbau unter den bestehenden Händler-IDs, Server-Prüfung.

## Quellen

- [Character Creator 5 – Preis und Pläne (Reallusion)](https://www.reallusion.com/plan-and-pricing/individual/perpetual/character-creator-5-3101)
- [CG Channel: Reallusion releases Character Creator 5](https://www.cgchannel.com/2025/08/reallusion-releases-character-creator-5/)
- [Reallusion Software EULA](https://www.reallusion.com/Content/EULA/AP/EULA_AP.htm)
- [Reallusion Content License Policy](https://www.reallusion.com/license/content.html)
- [Human Generator – Preise](https://humgen3d.com/pricing)
- [Human Generator – License FAQ](https://help.humgen3d.com/license)
- [Human Generator – API Overview](https://help.humgen3d.com/API/Overview)
- [CG Channel: MPFB 2](https://www.cgchannel.com/2025/03/check-out-open-source-blender-character-generation-plugin-mpfb-2/)
- [MakeHuman – Can I sell models made with MPFB?](https://static.makehumancommunity.org/mpfb/faq/can_i_sell_models.html)
- [Meshy – Pricing & Credits](https://docs.meshy.ai/en/webapp/pricing)
- [Adobe – Mixamo FAQ](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html)
