# Griff-Diagnose der Markthändler

Stand vor der Überarbeitung (Commit `bcf8da2`, Place-Version 31). Gemessen mit
`blender/validate_grips.py -- --out previews/grips/before`. Messwerte stehen in
`previews/grips/before/grip_validation.json`, die Bogen mit 14 Ansichten je Griff in
`previews/grips/before/<händler>_<hand>_<gegenstand>.png`.

## Aufbau der Figuren (Ist-Zustand, aus Code und Place gemessen)

| Frage | Befund |
|---|---|
| Rig | Kein R6 oder R15, sondern ein eigenes Rig: MakeHuman-Basismodell (CC0) als skinned Mesh, 9 MeshParts, 26 Knochen in Roblox (`RootPart` mit Bones, `AnimationController`, kein `Humanoid`) |
| Gelenke in Roblox | Hüfte, 5 Wirbel, 2 Halswirbel, Kopf, je Seite Schlüsselbein, Ober- und Unterarm, Handgelenk, Becken, Ober- und Unterschenkel, Fuß |
| Finger | Beim Bauen in Blender je Finger 3 Glieder, Daumen 3 Glieder. Der Griff wird gelöst und fest ins Mesh gebacken; danach werden die Fingerknochen mit dem Handgelenk verschmolzen. In Roblox gibt es keine Fingerknochen. |
| Handgelenk | Vorhanden, wird aber nie animiert (in der Ruhepose gerade zum Unterarm) |
| Gelenktyp | Bones, gesetzt über `Bone.Transform` im Client (`MarketIdle.client.lua`); kein `Motor6D`, kein Animator-Clip, kein IK |
| Animationen | Je Händler eine geschlossene Schleife (6–8 s) über 8 Knochen: Wirbelsäule, Hals, Kopf, Ober- und Unterarme; keine Lauf-, Aufnehm- oder Abstellzustände (die Händler stehen fest am Stand) |
| Befestigung der Gegenstände | Eigenes Mesh je Gegenstand, zu 100 % auf den Handgelenkknochen gewichtet; kann relativ zur Hand nicht verrutschen |

Folgerungen:
- Der Griff selbst ist nicht durch Armdrehung entstanden, sondern durch echte Fingergelenke beim Bauen.
- Fehler entstehen an drei Stellen: an der Wahl der Griffstelle am Gegenstand (Griffprofil), an der Form des Gegenstands und an der Armhaltung der Schleifen.
- `Tool` und `RightGrip` setzen einen `Humanoid` voraus und passen nicht zu diesen Figuren. `IKControl` bräuchte einen `Animator` und lohnt bei feststehenden Figuren nicht. Die Armhaltungen werden deshalb beim Bauen mit IK gelöst und als Schleife eingebacken. Das ist günstiger auf Mobilgeräten und reproduzierbar prüfbar.

## Befunde je Griff (vorher)

Einheiten: 1 Stud = 27 cm (Maßstab der Figuren), also 0,01 Stud ≈ 2,7 mm. Grenzwerte relativ zur gemessenen Fingerdicke t (0,060–0,066 Studs ≈ 1,6–1,8 cm): Kontakt < 0,2 t, Durchdringung höchstens 0,3 t, Verrutschen < 0,1 t.

### Lio – rechte Hand – Flasche (Kernfall)
1. **Sieht falsch aus:**
   - Die Hand hält den Flaschenhals.
   - Zeige- und Mittelfinger liegen auf dem Korken.
   - Der kugelige Flaschenkörper hängt unter dem kleinen Finger.
   - Beim „gegen das Licht halten“ ist die Flasche direkt vor dem Mund, wie beim Trinken.
2. **Ursache:**
   - Das Flaschenmodell hat seinen Griffursprung am Hals.
   - Der Körper ist eine Kugel mit 9 cm Durchmesser, zu groß für einen Faustgriff. Ein Flaschenkörper, den eine Hand umfassen kann, war im Modell nicht vorhanden.
   - Gemessen: 14 Kontaktpunkte auf dem Korken, nur 51 % des Kontakts am Flaschenkörper → Pflichtverletzung.
3. **Nötig:**
   - Neues Flaschenmodell: zylindrischer Körper, 6 cm Durchmesser, 11 cm hoch.
   - Griffursprung in der Mitte des Körpers, Korken zur Daumenseite (beim Halten oben).
   - Armhaltung so, dass die Flasche vor der Brust aufrecht steht.
4. **Fehlende Rig-Teile:** keine. Die Fingerglieder reichen für einen zylindrischen Kraftgriff.
5. **Richtige Haltung:**
   - Vier Finger gekrümmt um den Körper, der Daumen gegenüber, die Handfläche am Glas.
   - Die Flasche aufrecht, der Ellbogen gebeugt.
   - Zum Prüfen gegen das Licht seitlich vor dem Gesicht, nicht vor dem Mund.
6. **Prüfung:** Griffbereich (Kontakt nur am Körper), Korken und Hals verboten, Bogen aus 14 Ansichten.

### Esme – rechte Hand – Axt
1. **Sieht falsch aus:**
   - Der Griff am Stiel ist korrekt.
   - Die Axt steht aber senkrecht vor Brust und Gesicht, der Kopf ragt über die Hutkrempe.
   - Laut Schleife „liegt sie auf der Schulter“, sie berührt die Schulter aber nirgends.
2. **Ursache:**
   - Die Armwinkel der Schleife sind von Hand geschätzt.
   - Die Griffachse in der Hand liegt entlang der Knöchellinie; mit diesen Unterarmwinkeln steht sie senkrecht.
   - Gemessen: Griff am Stiel, Lage 18,4/20, keine Pflichtverletzung. Der Haltungsfehler war ohne Bild nicht erkennbar.
3. **Nötig:** Armwinkel per IK so lösen, dass der Stiel auf der rechten Schulter aufliegt, der Kopf hinter der Schulter ist, die Hand vor der Brust bleibt und nichts in Körper oder Kopf eindringt.
4. **Fehlende Rig-Teile:** keine.
5. **Richtige Haltung:** Kraftgriff am unteren Stieldrittel, Stiel schräg über der Schulter, Unterarm angewinkelt, Handgelenk gerade.
6. **Prüfung:** Abstand Stiel–Schulter, Axtkopf hinter der Schulter, Durchdringung mit dem Körper in der Schleife, Bogen.

### Aron – rechte Hand – Hammer, linke Hand – Erz (Werkzeuggebrauch)
1. **Sieht falsch aus:**
   - Er hält den Hammer vor das Gesicht.
   - Die „Schläge“ treffen das Erz nicht. Gemessen: Annäherungen bei 0,34/0,47 s auf 0,05–0,08 Studs (≈ 1,4–2,2 cm), dafür dringt der Hammerkopf bei t = 2,5–2,6 s bis zu 0,059 Studs (≈ 1,6 cm) in das Erz ein.
2. **Ursache:**
   - Die Schleife ist mit geschätzten Winkeln gebaut, ohne Ziel „Hammerfläche auf Erzoberseite“.
   - Das Profil „Hammer“ hatte einen zu engen Griffbereich (−0,15…0,42). Der Stiel reicht bis −0,6, der Kontakt bei y −0,24 liegt also auf dem Stiel. Diese Meldung war ein Profilfehler, kein Griffehler.
3. **Nötig:**
   - Erz in der linken Hand vor der unteren Brust.
   - Rechter Arm per IK: Hammerfläche über dem Erz (ausholen), dann genau auf der Erzoberseite (Schlag).
   - Griffbereich = ganzer Stiel.
4. **Fehlende Rig-Teile:** keine.
5. **Richtige Haltung:** Kraftgriff am Stiel, Schlag von oben auf das Erz in Brusthöhe, Blick auf das Erz.
6. **Prüfung:** Abstand Hammerkopf–Erz über die Schleife (Schlag erreicht 0 ± 0,01 Studs, nie tiefer), Bogen.

### Nyra – rechte Hand – Kristall
1. **Sieht falsch aus:**
   - Der Kristall wird vor das Auge gehalten und verdeckt Gesicht und Haare.
   - Die Handfläche liegt nicht am Kristall (0,045 Studs ≈ 1,2 cm Abstand).
2. **Ursache:** geschätzte Armwinkel. Den Kristall hält sie mit den Fingern und ohne Handfläche, was für einen kleinen Stein eher ein Präzisionsgriff ist.
3. **Nötig:** Kristall per IK vor die Brust halten, seitlich vom Gesicht, Blick darauf.
4. **Fehlende Rig-Teile:** keine.
5. **Richtige Haltung:** Kristall in Brust- bis Kinnhöhe vor dem Körper, Spitze frei.
6. **Prüfung:** Abstand Kristall–Kopf in der Schleife, Bogen.

### Selma – rechte Hand – Kräuterbund
1. **Sieht falsch aus:** fast korrekt. Zwei Kontaktpunkte eines Fingers liegen auf einem Blatt über dem Bindfaden.
2. **Ursache:** Die Blätter beginnen zu dicht über der Griffstelle.
3. **Nötig:** Blätter am Modell weiter nach oben setzen.
4. **Fehlende Rig-Teile:** keine.
5. **Richtige Haltung:** Faust um die gebundenen Stängel, Blüten oben, zum Riechen an die Nase.
6. **Prüfung:** Griffbereich ohne Blattkontakt.

### Lio – linke Hand – Tuch
- 78 % des Kontakts im Griffbereich ±0,2. Das Tuch ist weich und hat keinen „falschen“ Teil; die überhängenden Zipfel gehören zum Gegenstand.
- **Profilfehler:** Der Griffbereich muss das ganze Tuch umfassen.

### Selma – Korb, Nyra – Laterne, Aron – Erz, Esme – Zollstock
- Ohne Pflichtverletzung.
- Korb und Laterne hängen im Hakengriff am Bügel, der Arm ist unten.
- Visuell offen: wird im Nachher-Bogen geprüft.

## Was nicht zum Spiel gehört und warum

- **Gehen, Aufnehmen, Abstellen, Gegenstandswechsel:** Die Händler stehen fest am Stand und wechseln nie den Gegenstand. Dafür bräuchte es Fingerknochen in Roblox (je Hand 15) und eine Zustandsmaschine.
  - Das ist neues Spielverhalten, keine Griffkorrektur.
  - Der Zwei-Hand-Griff (Kiste) wird deshalb als Testszene in Blender geprüft, nicht im Spiel.
- **Stabilität des Gegenstands in der Hand:** In Roblox ist sie konstruktiv gesichert, weil der Gegenstand zu 100 % am Handgelenkknochen hängt. Gemessen wird trotzdem, ob die Finger dagegen verrutschen.
