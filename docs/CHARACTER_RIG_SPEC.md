# Händler-Rig: Spezifikation

Erzeugt von `blender/village/human.py` (Skelett) und `blender/build_characters.py` (Export).

## Skelett (72 Knochen je Händler)

| Gruppe | Knochen | Anzahl | Animiert von |
|---|---|---:|---|
| Wurzel | `Root` (ohne Gewichte, oberster Knochen), `hips` (MakeHuman `root`) | 2 | – |
| Rumpf | `spine05` … `spine01`, `neck01`, `neck02`, `head` | 8 | Clips (Kanäle `torso`, `head`), Atmen, Blickwendung |
| Schultern/Arme | `clavicle`, `upperarm01`, `lowerarm01`, `wrist` je Seite | 8 | Clips (`clav_*`, `upper_*`, `fore_*`, `hand_*`) |
| Finger | `finger1-1` … `finger5-3` je Seite | 30 | Ruhepose = gelöster Griff; zur Laufzeit derzeit nicht bewegt |
| Beine | `pelvis`, `upperleg01`, `lowerleg01`, `foot` je Seite | 8 | – (Standbein-Haltung ist eingebacken) |
| Gesicht | `jaw`, `eye.L/R`, `orbicularis03.L/R` (Oberlid), `orbicularis04.L/R` (Unterlid), `oculi01.L/R` (Braue), `oris03.L/R`, `oris07.L/R` (Mundwinkel oben/unten), `oris05` (Oberlippe), `oris01` (Unterlippe), `risorius03.L/R` (Wange) | 16 | Gesichtsposen, Blinzeln, Blick |

- Die Gesichtsknochen und ihre Hautgewichte stammen aus dem MakeHuman-Standardskelett (CC0); bisher wurden sie mit dem Kopf verschmolzen.
- Jeder Knochen hängt am nächsten behaltenen Vorfahren (Kopf bzw. Kiefer).
- Die Zwillingsknochen `upperarm02`/`lowerarm02` verteilen beim Posieren die Unterarmdrehung und werden danach verschmolzen.

## Gewichte

- Höchstens 4 Knochen je Vertex (Roblox-Vorgabe laut Doku „Max Influences 4“; `top4` im Export).
- Keine Gewichte auf `Root`.
- Augäpfel hängen zu 100 % am jeweiligen `eye`-Knochen.
- Wimpern übernehmen die Gewichte des nächsten Lidvertex.
- Brauen, Bart und Haare übernehmen die Gewichte der darunterliegenden Haut.
- Hüte und Brille hängen am Kopf.
- In Kleidungs- und Haarfeldern zählen Gesichtsknochen als Kopf und Fingerknochen als Hand (`wardrobe.Anatomy.weight/group`).

## Gesichtsposen (`characters.FACE_POSES`)

Je Pose und Knochen gibt es eine Drehung (Grad, Figurachsen, um den Knochenkopf) und/oder eine Verschiebung (Studs, Figurachsen). Einträge mit `.X` gelten gespiegelt für beide Seiten.

| Pose | Wirkung |
|---|---|
| `blink` | Oberlider 30° zu, Unterlider 7° hoch |
| `smile` | Mundwinkel nach außen, hinten und oben; Wangen hoch; Unterlid hebt sich |
| `brows_up` | Brauen hoch, Oberlid öffnet |
| `focus` | Brauen zusammen und tiefer, Augen verengt |
| `talk` | Kiefer 4° auf |
| `skeptic` | eine Braue hoch, die andere tiefer, ein Mundwinkel |

- **Export:** Quaternion `q` und Verschiebung `p` im Roblox-Rahmen der Figur. Der Client mischt die Posen mit Gewichten 0..1.
- **Geprüft:** Bogen `previews/characters/<stufe>/<rolle>_face.png` (neutral + jede Pose, frontal und Dreiviertel).

## Roblox

- Import als Rig-Modell: `RootPart` mit Knochen, skinned MeshParts, `AnimationController`, kein `Humanoid`; die Knochen kommen mit eigener Ruhe-Orientierung an.
- `Bone.Transform` = `Ruhe⁻¹ · Figur · (CFrame(p) · q) · Figur⁻¹ · Ruhe`. Die Formel hängt nicht davon ab, wie der Importer die Knochen ausrichtet.
- **UNVERIFIED_IN_STUDIO:** wie die Haut an den Gesichtsknochen und Fingern in Roblox verformt aussieht.
