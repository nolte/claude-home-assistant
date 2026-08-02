# Skill: `ha-esphome-config-scaffold`

Status: draft

## Kontext

Die ESPHome-Achse war in `AUDIENCES.md` von Anfang an deklariert, lieferte aber keine Artefakte; das Skills-&-Agents-Audit 2026-07 markierte die Lücke, und der Operator entschied, zuerst den Device-YAML-Schnitt zu bauen, geschärft am Round-Trip-Fixture `nolte/esphome-configs`. Dieser Skill ist der Greenfield-Einstiegspunkt dieses Schnitts: er macht aus „neues ESPHome-Gerät" genau eine spec-konforme YAML-Datei gemäß `spec/ha/esphome-config-patterns/de.md`.

## Scope

Ein Gerät, eine neue YAML-Datei pro Aufruf, im Device-Config-Root des Consumer-Repositories. Die Komposition bevorzugt geteilte `packages:`; Credentials bleiben `!env_var`-Referenzen; der Skill endet bei der geschriebenen Datei plus einem Validierungs-Schritt-Report.

## Ziele

- Ein auffindbarer Einstiegspunkt (`/claude-home-assistant:ha-esphome-config-scaffold`) für neue Device-Configs
- Interaktives Erheben von Gerätename, Board-Familie, geteilten Concerns und initialen Plattformen vor jedem Write
- Pre-flight, der Kollisionen und fehlendes Secrets-Scaffolding vor der Komposition fängt
- Output, der konstruktionsbedingt HA-ready ist: verschlüsselte native api, ota, AP-Fallback-wifi — alles secret-referenziert

## Nicht-Ziele

- Erweitern bestehender Device-Dateien (gehört `ha-esphome-config-augment`)
- ESPHome-Custom-Component-Authoring (C++/Python) und HA-Add-ons — spätere Achsen
- Compile/Flash/Deploy und Fleet-Rollout — gehören der ESPHome-Toolchain und dem Operator

## Anforderungen

- **MUSS** vor der Komposition `spec/ha/esphome-config-patterns/de.md` lesen und jedes dortige MUSS erfüllen (Naming, packages-statt-Merge-Keys, Credentials, api-Encryption, ota)
- **MUSS** zusätzlich `spec/ha/esphome-project-structure/de.md` lesen und die Datei entsprechend platzieren: Device-Dateien flach im Config-Root, Wiederverwendung aus einem Board-Package komponiert statt kopierter Blöcke, und das Substitutions-Trio `name` / `id` / `comment` vorhanden
- **SOLLTE** beim Scaffolding für bekannte Hardware die Geräte-Spec heranziehen (`spec/ha/esp32-s3-box/de.md` für die BOX-Familie), damit generationsspezifische Pins und Codecs aus der Spec statt aus einer generischen Vorlage stammen
- **MUSS** jeden emittierten Schema-Key gemäß `spec/ha/upstream-docs-verification` gegen die offiziellen ESPHome-Docs verifizieren
- **MUSS** den Pre-flight (Config-Root-Erkennung, Kollisions-Check, Secrets-Inventar, Operator-Bestätigung) vor dem Schreiben ausführen
- **MUSS** die vom Operator zu füllenden Secrets-Keys reporten und `secrets.yaml.example` erweitern, wenn das Repo eine mitführt
- **SOLLTE** `esphome config <file>`-Validierung anbieten, wenn die Toolchain vorhanden ist; andernfalls als nächsten Caller-Schritt reporten
- **DARF NICHT** mehr als die eine Device-Datei (plus optionale Example-Datei-Erweiterung) pro Lauf schreiben

## Akzeptanzkriterien

- [ ] Ein Scaffold-Lauf gegen das Fixture-Layout erzeugt eine Datei, die jeden Checklist-Punkt von `spec/ha/esphome-config-patterns` §Akzeptanzkriterien erfüllt
- [ ] Ein erneuter Lauf mit demselben Gerätenamen bricht am Kollisions-Pre-flight ab statt zu überschreiben
- [ ] Der Report benennt jede Umgebungsvariable, die die generierte Datei referenziert

## Offene Fragen

_Derzeit keine — die Versions-Pin-Frage liegt bei der Grounding-Spec._
