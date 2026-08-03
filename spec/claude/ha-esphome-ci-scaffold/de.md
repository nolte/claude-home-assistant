# Skill: `ha-esphome-ci-scaffold`

Status: draft

## Kontext

`spec/ha/esphome-project-structure` §Validation formuliert die Regel, die ein Fleet-Repository von einem Ordner voller Dateien unterscheidet: `esphome config` läuft für **jedes** Device-File bei jeder Änderung, weil eine Package-Änderung Geräte kaputt macht, deren Dateien niemand angefasst hat — und sie hält fest, dass das eigene Fixture-Repository des Portfolios das nicht tut, weshalb ein nicht auflösbarer Include in einer Device-Config überleben konnte. Dieser Skill ist die Operationalisierung dieser Regel und das ESPHome-Gegenstück zu `ha-integration-ci-scaffold`.

## Scope

Ein Repository pro Aufruf: der Pull-Request-Validierungs-Workflow, der separat getaktete Compile-Workflow, die statischen Checks daneben, der Versions-Pin und die Environment-Variablen-Strategie, mit der ein Validierungslauf Credentials ohne echtes Secret auflöst.

## Ziele

- Die flottenweite Validierung zum Normalfall machen statt einer Diff-basierten Matrix, die genau den charakteristischen Fehler verfehlt
- Den schnellen Schema-Durchlauf vom langsamen Compile trennen, damit die Kosten pro Pull Request mit wachsender Flotte begrenzt bleiben
- Credentials in CI einen benannten, dokumentierten Auflösungspfad geben, der für Schema-Validierung nie ein echtes Secret verlangt
- Workflows ausgeben, die den geerbten GitHub-Actions-Regeln genügen, statt handgeschriebenem YAML
- Ehrlich benennen, was die entstehende Pipeline beweist und was nicht

## Nicht-Ziele

- Repository-Layout und Package-Architektur (Eigentum von `ha-esphome-fleet-scaffold`)
- Das Beheben dessen, was CI findet (Eigentum von `ha-esphome-package-author` / `ha-esphome-config-augment`)
- Die Triage eines roten Laufs (Eigentum von `workflow-health-triage`)
- Das Auditieren einer bestehenden Pipeline (Eigentum von `cicd-pipeline-reviewer` und `ha-esphome-fleet-reviewer`)
- Flashen und OTA-Rollout aus CI — die Grounding-Spec stellt Fleet-Rollout außerhalb des Scopes

## Anforderungen

- **MUSS** `spec/ha/esphome-project-structure/en.md` §Validation sowie die geerbten `spec/project/github-actions-best-practices/` und `spec/project/continuous-integration/` lesen, bevor ein Workflow ausgegeben wird
- **MUSS** einen Validierungs-Job ausgeben, der `esphome config` für **jedes** Device-File bei jeder Änderung ausführt, nie für eine Diff-basierte Teilmenge
- **MUSS** `esphome compile` auf eine geplante oder Pre-Release-Taktung trennen
- **MUSS** die von CI verwendete ESPHome-Version pinnen und benennen, dass ein Anheben eine geprüfte Änderung ist
- **MUSS** dokumentieren, wie `!env_var`-Credentials in CI aufgelöst werden, und **DARF NICHT** zulassen, dass ein Platzhalter-Credential in ein flashbares Artefakt gelangt
- **MUSS** die geerbten Workflow-Regeln befolgen: per Digest gepinnte Actions, minimale Permissions, eine Concurrency-Gruppe, keine ungeprüften Eingaben in einem `run:`-Block und Cache-Keys, die einen Fehler nicht verdecken können
- **MUSS** den Job bei jedem nicht validierbaren Device-File fehlschlagen lassen und **DARF NICHT** eines still überspringen
- **MUSS** melden, was die statischen Checks tatsächlich abdecken, statt zu suggerieren, ein Whitespace-Hook oder ein Security-Scanner validiere YAML
- **DARF NICHT** einen Deploy-, Flash- oder OTA-Rollout-Schritt ausgeben

## Akzeptanzkriterien

- [ ] Der ausgegebene Validierungs-Workflow iteriert jedes Device-File im Config-Root und schlägt beim ersten ungültigen fehl, meldet aber die übrigen weiterhin
- [ ] Der Compile-Job läuft in eigener Taktung und nutzt denselben Versions-Pin und dieselbe Environment-Strategie
- [ ] Der Bericht nennt jede Environment-Variable, die CI setzt, und woher ihr Wert stammt
- [ ] Der Bericht benennt, was die Pipeline nicht beweist — allen voran das Verhalten am Gerät

## Offene Fragen

_Derzeit keine._
