# Skill: `ha-translation-sync`

Status: draft

## Kontext

`ha/translations` schreibt vor: `strings.json` ist die englische Quelle der Wahrheit; jede `translations/<lang>.json` muss die Schlüsselstruktur 1:1 spiegeln. Drift zwischen den Dateien (fehlender Key in einer Sprache, andere Reihenfolge, gelöschter Key in einer Sprache) führt zu Mixed-Language-UI und ist als Fehlerzustand klassifiziert. Manuelles Pflegen vergisst regelmäßig Schlüssel — vor allem nach Refactors, die einen Translation-Key umbenennen oder hinzufügen.

Dieser Skill synchronisiert `strings.json` mit allen `translations/<lang>.json`-Dateien, ergänzt fehlende Keys mit `<TODO>`-Markern, entfernt verwaiste Keys (mit User-Bestätigung), und meldet alle Drifts als Bericht.

## Scope

Der Skill macht **Sync-Operationen** auf einer existierenden Translation-Struktur. Er erzeugt keine neuen Strings (das machen `ha-integration-scaffold`, `ha-entity-description-mapper`, `ha-service-definition-generator`, `ha-config-flow-augment`, `ha-coordinator-add`); er stellt nur sicher, dass das, was schon da ist, sprachübergreifend konsistent bleibt.

## Ziele

- Strukturelle Drift zwischen `strings.json` und `translations/<lang>.json` automatisch erkennen und beheben
- Verwaiste Keys (in Translation, aber nicht mehr in `strings.json`) sichtbar machen — mit User-Bestätigung entfernen
- Fehlende Keys in `translations/<lang>.json` mit `<TODO: translate '<EN-Wert>'>`-Markern auffüllen
- `icons.json`-Drift gegen `entity.<platform>.<key>`-Translation-Keys ebenfalls melden — Icon-Eintrag ohne Translation oder Translation ohne Icon ist ein Bug

## Nicht-Ziele

- Maschinelle Übersetzung (DeepL, Google Translate) — nicht im Scope; Translations bleiben User-/Reviewer-Aufgabe
- String-Inhalt ändern — der Skill ändert keine Werte, nur die Struktur
- Multi-Sprach-Erweiterung (`translations/fr.json` neu anlegen) — der Skill arbeitet auf existierenden Sprachen; eine neue Sprach-Anlage ist eine User-Entscheidung mit anderem Workflow
- Translation-Workflow-Tooling (crowdin, Lokalise) — externe Stacks

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „sync the translations"
  - „check translation drift"
  - „align strings.json with translations"
  - „prüfe Translation-Drift"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root)
- **SOLLTE [SHOULD]** erfassen: `mode` — `report` (nur Bericht, kein Schreibzugriff) oder `apply` (Sync durchführen); Default `report`

### Pre-Flight

- **MUSS [MUST]** prüfen:
  1. `target_dir` ist git-Repo, sauber (im `apply`-Mode; im `report`-Mode reicht Repo-Erkennung)
  2. `target_dir/custom_components/<domain>/strings.json` existiert
  3. `target_dir/custom_components/<domain>/translations/` enthält mindestens eine `*.json`-Datei

### Drift-Detection

- **MUSS [MUST]** für jede `translations/<lang>.json`-Datei prüfen:
  - **Fehlende Keys**: Schlüssel, die in `strings.json` existieren, aber in `<lang>.json` fehlen
  - **Verwaiste Keys**: Schlüssel, die in `<lang>.json` existieren, aber nicht (mehr) in `strings.json`
  - **Strukturelle Drift**: Top-Level-Sektionen (`config`, `options`, `entity`, `services`) fehlen in einer der Sprachen
- **MUSS [MUST]** zusätzlich prüfen:
  - `icons.json:entity.<platform>.<key>`-Einträge ohne korrespondierenden `strings.json:entity.<platform>.<key>.name`
  - `strings.json:entity.<platform>.<key>.name`-Einträge ohne korrespondierenden `icons.json:entity.<platform>.<key>.default`
  - `icons.json:services.<name>`-Einträge ohne korrespondierenden `strings.json:services.<name>.name`

### Sync-Operationen (`apply`-Mode)

- **MUSS [MUST]** für jede fehlende Key in `<lang>.json` einen Eintrag mit `<TODO: translate '<EN-Wert>'>` als Platzhalter ergänzen
- **MUSS [MUST]** verwaiste Keys vor dem Entfernen explizit auflisten und User-Bestätigung holen — kein silent delete
- **MUSS [MUST]** die Schlüssel-Reihenfolge in jeder `<lang>.json` an die von `strings.json` angleichen — JSON-Dictionaries sind in Python ungeordnet, aber Datei-Schreiber halten typisch die Insertion-Order
- **MUSS [MUST]** `icons.json`-Drift als separaten Bericht ausgeben — Sync von `icons.json` ist nicht Teil dieses Skills (separater Skill `ha-icons-sync` denkbar)

### Verbote

- **MUSS NICHT [MUST NOT]** existierende Translation-Werte überschreiben — der Skill berührt keine vorhandenen Werte; nur fehlende Keys werden ergänzt
- **MUSS NICHT [MUST NOT]** verwaiste Keys ohne User-Bestätigung entfernen
- **MUSS NICHT [MUST NOT]** maschinelle Übersetzungen einsetzen — `<TODO: …>` ist die einzige automatische Aktion

## Akzeptanzkriterien

- [ ] Skill-Output enthält Drift-Bericht mit fehlenden Keys, verwaisten Keys, strukturellen Lücken
- [ ] Skill-Output enthält `icons.json`-Drift-Bericht (separat)
- [ ] Im `apply`-Mode: jede `translations/<lang>.json` enthält jeden Key aus `strings.json` (als `<TODO>` falls Übersetzung fehlt)
- [ ] Verwaiste Keys werden vor Entfernung dem User vorgelegt
- [ ] Bestehende Translation-Werte sind nach `apply` unverändert
- [ ] `pytest tests/` läuft fehlerfrei (sofern Tests Translation-Strings konsumieren)

## Offene Fragen

- **Multi-Repo-Sync**: Wenn das Plugin auch Translation-Strings von anderen Konsumenten-Repos synchronisieren soll — eigene Spec?
- **Maschinelle-Übersetzungs-Pipeline**: Soll eine optionale Variante mit DeepL-API zugänglich werden? Aktuell explizites Nicht-Ziel.
- **Sprach-Liste-Verwaltung**: Wie wird eine neue Sprache (z. B. `translations/fr.json`) angelegt? Aktuell User-Aufgabe; eine geführte Variante wäre denkbar.
- **`icons.json`-Sync**: Eigener Skill `ha-icons-sync`, oder bleibt der Bericht reiner Hinweis?
