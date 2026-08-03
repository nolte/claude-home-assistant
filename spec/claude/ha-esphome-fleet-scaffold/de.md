# Skill: `ha-esphome-fleet-scaffold`

Status: draft

## Kontext

Die ESPHome-Achse startete mit dem Device-File-Slice (`ha-esphome-config-scaffold`, `ha-esphome-config-augment`), der ein Repository voraussetzt, das bereits so geformt ist, dass es Geräte aufnimmt. `spec/ha/esphome-project-structure` hat danach festgelegt, wie diese Form aussieht — Config-Root, `common/`-Package-Baum, `include/`, `archive/`, geschlüsselte Assets — und nichts hat sie operationalisiert. Dieser Skill schließt die Lücke: Er ist der strukturelle Einstiegspunkt der ESPHome-Familie, einmal pro Repository vor dem ersten Gerät ausgeführt und erneut, wenn eine organisch gewachsene Sammlung auf die Package-Architektur gebracht werden muss.

## Scope

Ein Repository pro Aufruf. Greenfield-Anlage des Baums samt Base- und Board-Package oder ein plan-gegateter Umbau einer bestehenden flachen Sammlung. Endet beim geschriebenen Baum, der Environment-Variablen-Dokumentation und einem Validierungsbericht; das Verfassen von Device-Files wird übergeben.

## Ziele

- Ein auffindbarer Einstiegspunkt für „wo lebt ESPHome-Konfiguration in diesem Repository“
- Ein Baum, der die Unterscheidung flashbar/eingebunden sichtbar macht, sodass jedes Gerät und jeder gemeinsame Block ohne Suchen auffindbar ist
- Base- und Board-Packages, die das Onboarding eines Geräts bekannter Art zu einer Ein-Datei-Änderung machen
- Credential-Handling, das ab dem ersten Commit korrekt ist: `!env_var`, Per-Device-API-Keys, dokumentierte Variablen, nichts eingecheckt
- Ein Umbau, der nie still passiert — jede Verschiebung wird gelistet und freigegeben, bevor sie geschieht

## Nicht-Ziele

- Die Device-Files selbst (Eigentum von `ha-esphome-config-scaffold` / `ha-esphome-config-augment`)
- Schnitt, Parameter oder Abweichungsform eines einzelnen Packages (Eigentum von `ha-esphome-package-author`)
- CI-Validierung (Eigentum von `ha-esphome-ci-scaffold`)
- Ein Konformitätsurteil über das Ergebnis (Eigentum des read-only `ha-esphome-fleet-reviewer`)
- Portfolio-weites Repository-Scaffolding ohne ESPHome-Bezug — Taskfile, pre-commit, Renovate, Docs, Release-Automation regeln die geerbten `project/`-Specs
- Compile, Flash und Fleet-OTA-Rollout

## Anforderungen

- **MUSS** `spec/ha/esphome-project-structure/en.md` lesen, bevor ein Layout vorgeschlagen wird, und `spec/ha/esphome-config-patterns/en.md` für alles, was in ein Device-File hineinreicht
- **MUSS** in einem Repository, das bereits Device-Files enthält, den aktuellen Baum, den Zielbaum und die Datei-für-Datei-Liste aus Verschieben/Anlegen/Ändern zur expliziten Freigabe vorlegen, bevor geschrieben wird
- **MUSS** Wiederverwendung als `packages:` in Mapping-Form ausgeben, nie einen `<<: !include`-Merge-Key einführen und bestehende Merge-Keys als Findings melden, statt sie zu erweitern
- **MUSS** `common/` nach Konsument gruppieren: Einstiegspunkte flach, Bausteine in ESPHome-Domänen-Unterverzeichnissen
- **MUSS** das Board-Package das Base-Package einziehen lassen, sodass ein Gerät ein Board plus seine Feature-Packages nennt
- **MUSS** Credentials als `!env_var` ausgeben, einen Per-Device-API-Encryption-Key als `${api_key}` konsumieren, ein passwortgeschütztes `ota:` und `.gitignore`-Einträge für `.esphome/`, Build-Ausgaben und `secrets.yaml`
- **MUSS** jede Environment-Variable, die die scaffoldeten Packages lesen, im selben Lauf dokumentieren
- **MUSS** jeder Komponente, die ein Gerät später erweitern oder entfernen könnte, ein explizites `id:` geben
- **MUSS** beim Scaffolden eines Board-Packages für bekannte Hardware die Device-Spec heranziehen (`spec/ha/esp32-s3-box/en.md`), statt ein generisches Template auszugeben
- **MUSS** jeden ausgegebenen Schema-Key gegen die offizielle ESPHome-Doku gemäß `spec/ha/upstream-docs-verification` verifizieren
- **MUSS** nach einem Umbau `esphome config` für jedes bestehende Device-File ausführen, wo die Toolchain verfügbar ist, und es sonst als offenen Schritt des Aufrufers melden
- **DARF NICHT** Device-Files verfassen und **DARF NICHT** eine Datei verschieben oder löschen, die der Operator nicht gelistet gesehen hat

## Akzeptanzkriterien

- [ ] Ein Greenfield-Lauf erzeugt einen Baum, der die Layout-Checkliste aus `spec/ha/esphome-project-structure` §Acceptance Criteria erfüllt
- [ ] Ein Umbau-Lauf schreibt nichts, bevor die Verschiebeliste freigegeben ist, und lässt Legacy-Merge-Keys unangetastet, während er sie meldet
- [ ] Das ausgegebene Base-Package trägt kein nacktes `api:` und keinen flottenweiten Encryption-Key
- [ ] Der Bericht nennt jede Environment-Variable, die die scaffoldeten Packages lesen

## Offene Fragen

_Derzeit keine — die Frage der Fixture-Remediation liegt bei der Grounding-Spec._
