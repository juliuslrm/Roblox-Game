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

## Entscheidung

**Character Creator 5 als Werkzeug für die Charakterbasis, danach meine automatische Blender → Roblox-Strecke.**

**Begründung:**

- CC5 erzeugt die beste menschliche Anatomie, Gesichter und Hände der geprüften Werkzeuge.
- CC5 bringt Fantasy-Kleidung und -Haare mit oder nimmt sie auf.
- Die Lizenz erlaubt eingebettete Modelle in Spielen.

**Nachteil:**

- CC5 läuft nur am Desktop mit Oberfläche. Die Gestaltung von Körper, Gesicht und Kleidung macht deshalb der Auftraggeber oder ein Charakter-Artist in CC5, nicht ich.
- Ob Roblox als „Spiel“ im Sinn der EULA gilt, ist nicht schriftlich bestätigt: Die Assets liegen privat im eigenen Roblox-Konto und sind nur in diesem Spiel eingebettet. Vor dem Kauf sollte Reallusion das kurz bestätigen.

**Alternative**, wenn alles in meiner Automatisierung laufen soll: **Human Generator Ultimate** (kommerzielle Lizenz).

- Es läuft in Blender und hat eine Python-API, ich könnte Lio skriptgesteuert erzeugen.
- Dafür müssen Add-on und Inhaltspakete in diese Umgebung kommen: Upload durch den Auftraggeber, nicht ins Repository, da Lizenzinhalt.
- Ob es ohne Oberfläche läuft, ist erst nach einem Test bekannt.

**Nicht gewählt:**

- **MPFB2:** gleiche Basis wie die verworfenen Figuren.
- **Meshy:** Gesichter und Hände unzuverlässig, Topologie.
- **Mixamo:** nur Ergänzung.
- **Asset-Shops:** Stil und Lizenz je Modell.

## Was ich übernehme, sobald eine Basis vorliegt

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
