# Skill: `ha-quality-scale-audit`

Status: draft

## Kontext

`ha/quality-scale` definiert HAs Tier-Framework (🥉 Bronze / 🥈 Silver / 🥇 Gold / 🏆 Platinum) samt der zweistufigen Deklaration: ein `quality_scale:`-Schlüssel in der `manifest.json` benennt das erreichte Tier, eine begleitende `quality_scale.yaml` führt pro Regel den Status (`done` / `exempt` mit `comment` / `todo`). Eine bestehende Integration kann ein Tier in der `manifest.json` deklarieren, das die `quality_scale.yaml` und der tatsächliche Code gar nicht tragen — die kumulative Semantik (ein Tier verlangt *alle* eigenen Regeln plus alle darunter) wird leicht überschätzt, und einzelne `done`-Regeln driften nach Refactorings vom Code weg.

Dieser Skill auditiert eine Integration gegen `ha/quality-scale`: Er liest das deklarierte Tier, parsed `quality_scale.yaml`, prüft die kumulative Erfüllung des deklarierten Tiers, verifiziert die Schlüssel-Regeln gegen Code-Evidenz (über das Tier-zu-Spec-Mapping) und meldet pro Regel ein Finding. Er **schreibt nichts** — die Behebung bleibt manuell oder via einen anderen Skill (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-translation-sync`, `ha-test-harness-augment`).

## Scope

Read-only Audit. Der Skill liest `manifest.json`, `quality_scale.yaml` und die Code-Dateien der Integration, führt `grep`-basierte Pattern-Checks aus und vergleicht die deklarierten Regel-Status gegen Code-Evidenz. Er macht keine destruktiven Operationen, kein Auto-Fix, kein Commit. Er ist die Quality-Scale-Schwester von `ha-security-audit`.

## Ziele

- Vollständigkeits-Bericht über das deklarierte Tier samt aller darunterliegenden Tiers pro auditierter Integration
- Differenz zwischen **deklariertem** Tier (`manifest.json`), **dokumentiertem** Tier (`quality_scale.yaml`-Status) und **verifiziertem** Tier (Code-Evidenz) sichtbar machen
- Pro Finding: Regel, Pfad-Datei-Zeilen-Referenz, Klassifikation (high / medium / low), Remediation-Vorschlag (welcher Skill behebt es, welche manuelle Edit-Aktion)
- Tier-zu-Spec-Traceability: jede Schlüssel-Regel mit Sibling-Spec gegen die im Mapping gelistete Spec und ihre Code-Evidenz zurückführen
- `exempt`-Disziplin: jede ausgenommene Regel braucht einen `comment`; ein `exempt` ohne Begründung ist ein Finding

## Nicht-Ziele

- Auto-Fix der Findings — die Behebung läuft über die Edit-Skills oder manuell
- Pflege der HA-Checklist-PR für ein Tier-Upgrade gegen das HA-Core-Repo — das ist ein Beitrags-Workflow, kein Plugin-Artefakt
- Ein vollwertiger `hassfest`-Ersatz, der jede der ~45 Regeln semantisch gegen den Code beweist — der Skill verifiziert die Schlüssel-Regeln mit Sibling-Spec heuristisch; tiefere Regeln werden gegen die `quality_scale.yaml`-Deklaration geprüft
- Security-Audit (`ha/security-hardening`) — eigener Skill `ha-security-audit`
- Code-Quality-Audit (Ruff, Type-Hints, Test-Coverage) — eigene Tools / Skills (`strict-typing` wird nur als Platinum-Regel-Status, nicht durch echtes Type-Checking geprüft)

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „run a quality-scale audit on the integration"
  - „audit the integration against the quality scale"
  - „which quality-scale tier does this integration reach"
  - „prüfe die Integration gegen die Quality-Scale"
  - „welches Quality-Scale-Tier erreicht die Integration"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root)
- **KANN [MAY]** erfassen: `target_tier` (`bronze` / `silver` / `gold` / `platinum`); ohne Angabe wird das in der `manifest.json` deklarierte Tier als Ziel angenommen, ersatzweise `bronze`
- **KANN [MAY]** erfassen: `severity_threshold` (`low` / `medium` / `high`); Default `low` (alle Findings melden)

### Pre-Flight

- **MUSS [MUST]** prüfen:
  1. `target_dir` ist git-Repo
  2. `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` daraus lesen
  3. `target_dir/custom_components/<domain>/quality_scale.yaml` existiert (oder Skill notiert das Fehlen als erstes high-Finding und auditiert weiter gegen Code-Evidenz)

### Audit-Checks

#### Tier-Deklaration (`manifest.json`)

- **MUSS [MUST]** den `quality_scale:`-Schlüssel aus `manifest.json` lesen und gegen `{bronze, silver, gold, platinum}` validieren
- **Finding wenn**: `quality_scale` fehlt → high (neue Integration MUSS mindestens Bronze deklarieren); Wert ist `no_score` / `internal` / `legacy` / `custom` bei einer Custom Integration auf der gestuften Skala → high

#### `quality_scale.yaml`-Form

- **MUSS [MUST]** prüfen, dass die Datei existiert und unter `rules:` pro Regel einen Status (`done`, oder `status: exempt` mit `comment`, oder `todo`) führt
- **MUSS [MUST]** jede `exempt`-Regel auf einen nichtleeren `comment` prüfen
- **Finding wenn**: `quality_scale.yaml` fehlt → high; eine `exempt`-Regel ohne `comment` → high; eine im Tier-Regelsatz erwartete Regel fehlt ganz in der Datei → medium

#### Kumulative Tier-Erfüllung

- **MUSS [MUST]** für das Ziel-Tier (`target_tier` bzw. deklariertes Tier) den Regelsatz dieses Tiers **und aller darunterliegenden Tiers** bilden und prüfen, dass jede Regel `done` oder begründet `exempt` ist
- **Finding wenn**: eine Regel des Ziel-Tiers (oder eines darunterliegenden) ist `todo` / fehlt / unbegründet `exempt` → high (das deklarierte Tier ist überdeklariert)

#### Bronze-Baseline

- **MUSS [MUST]** unabhängig vom deklarierten Tier prüfen, dass alle Bronze-Pflichtregeln aus `ha/quality-scale` `done` oder begründet `exempt` sind (`action-setup`, `appropriate-polling`, `brands`, `common-modules`, `config-flow-test-coverage`, `config-flow`, `dependency-transparency`, `docs-*`, `entity-event-setup`, `entity-unique-id`, `has-entity-name`, `runtime-data`, `test-before-configure`, `test-before-setup`, `unique-config-entry`)
- **MUSS [MUST]** den `has-entity-name`-Subcheck per `grep` nach `_attr_has_entity_name = True` (bzw. `has_entity_name` in der EntityDescription) in den Plattform-Modulen verifizieren
- **MUSS [MUST]** den `config-flow`-Subcheck prüfen: `data_description` in `strings.json`/`translations` vorhanden und `ConfigEntry.data` vs. `ConfigEntry.options` sauber getrennt
- **Finding wenn**: eine Bronze-Regel nicht erfüllt → medium (oder high, falls Bronze das deklarierte Tier ist — dann greift bereits die kumulative Prüfung)

#### Schlüssel-Regel-Traceability (Code-Evidenz)

- **MUSS [MUST]** jede als `done` deklarierte Schlüssel-Regel mit Sibling-Spec gegen Code-Evidenz prüfen:

  | Regel | Spec | Evidenz-Check |
  |---|---|---|
  | `runtime-data` | `ha/runtime-data-pattern` | `entry.runtime_data` genutzt, **kein** `hass.data[DOMAIN]` |
  | `config-flow`, `test-before-setup`, `unique-config-entry` | `ha/config-flow-patterns` | `config_flow.py` vorhanden; `_abort_if_unique_id_configured`; Setup-Tests |
  | `parallel-updates` | `ha/entity-architecture`, `ha/coordinator-patterns` | `PARALLEL_UPDATES`-Konstante pro Plattform-Modul |
  | `entity-translations`, `exception-translations` | `ha/translations` | Einträge in `strings.json` |
  | `diagnostics` | `ha/diagnostics` | `diagnostics.py` mit `async_get_config_entry_diagnostics` |
  | `discovery`, `discovery-update-info` | `ha/zeroconf-discovery` | `zeroconf` in `manifest.json` + `async_step_zeroconf` |
  | `reauthentication-flow` | `ha/coordinator-patterns` | `async_step_reauth` in `config_flow.py` |
  | `integration-owner` | `ha/integration-manifest` | nichtleeres `codeowners` in `manifest.json` |

- **Finding wenn**: eine Regel ist in `quality_scale.yaml` `done`, die Code-Evidenz fehlt aber → medium (Deklarations-Drift); umgekehrt Evidenz vorhanden, Regel aber `todo`/fehlend → low (untererfasst)

#### Silver-Regeln (bei Ziel-Tier ≥ Silver)

- **MUSS [MUST]** zusätzlich die Silver-Regeln prüfen: `action-exceptions` (`ServiceValidationError` / `HomeAssistantError` in Service-Handlern), `config-entry-unloading` (`async_unload_entry`), `entity-unavailable`, `log-when-unavailable`, `parallel-updates`, `reauthentication-flow`, `integration-owner`, `test-coverage`, `docs-configuration-parameters`, `docs-installation-parameters`
- **Finding wenn**: eine Silver-Regel ist bei deklariertem Silver nicht erfüllt → high; bei nur empfohlenem (verbindungsbasiertem) Silver nicht erfüllt → low

### Bericht-Format

- **MUSS [MUST]** den Bericht als nach Severity (high → medium → low) sortierte Markdown-Liste ausgeben mit pro Finding:
  - `id` — Finding-Nummer
  - `rule` — die `ha/quality-scale`-Regel (oder das Deklarations-Artefakt)
  - `tier` — das Tier, zu dem die Regel gehört (Bronze / Silver / Gold / Platinum)
  - `severity` — high / medium / low
  - `path` — Datei + Zeilennummer (oder das fehlende Artefakt)
  - `evidence` — Code-Snippet bzw. `quality_scale.yaml`-Auszug (max. 5 Zeilen)
  - `remediation` — empfohlener Fix; bei Skill-fixbaren Findings den Skill-Namen referenzieren
- **MUSS [MUST]** am Ende eine Zusammenfassung enthalten: Anzahl Findings pro Severity, plus eine **Tier-Stand-Zeile**, die das deklarierte, das dokumentierte und das verifizierte Tier gegenüberstellt (z. B. `deklariert: silver / dokumentiert: silver / verifiziert: bronze ✓ · silver ✗`)

### Verbote

- **MUSS NICHT [MUST NOT]** Code, `manifest.json` oder `quality_scale.yaml` modifizieren — read-only Audit
- **MUSS NICHT [MUST NOT]** ein höheres Tier als „verifiziert" ausweisen, als die Code-Evidenz und die kumulative Regel-Erfüllung tragen
- **MUSS NICHT [MUST NOT]** False-Positives still unterdrücken — wenn eine Regel `exempt` ist und der `comment` plausibel, das Finding als „prüfen" markieren statt es zu verschweigen

## Akzeptanzkriterien

- [ ] Skill liest `manifest.json` und `quality_scale.yaml` und die referenzierten Code-Dateien
- [ ] Skill meldet ein fehlendes `quality_scale`-Schlüssel oder eine fehlende `quality_scale.yaml` als high-Finding
- [ ] Skill prüft das Ziel-Tier kumulativ (alle Regeln darunter)
- [ ] Skill verifiziert jede Schlüssel-Regel mit Sibling-Spec gegen Code-Evidenz und meldet Deklarations-Drift
- [ ] Jede `exempt`-Regel ohne `comment` ist ein high-Finding
- [ ] Findings sind nach Severity (high → low) sortiert
- [ ] Skill macht keine Datei-Modifikationen (`git status` unverändert nach Lauf)
- [ ] Skill-Output enthält die Tier-Stand-Zeile (deklariert / dokumentiert / verifiziert)

## Offene Fragen

- **Tiefe der Code-Verifikation**: Der Skill verifiziert nur die Schlüssel-Regeln mit Sibling-Spec gegen Code; die übrigen ~30 Regeln werden gegen die `quality_scale.yaml`-Deklaration geprüft. Ab wann lohnt ein tieferer, `hassfest`-naher Check?
- **`quality_scale.yaml`-Drift-Gate**: Soll der Skill als CI-Hook konsumierbar sein (Exit-Code != 0, wenn deklariertes ≠ verifiziertes Tier)? Aktuell nur interaktiv.
- **Marker-Synchronisierung**: Soll der Skill auch die Quality-Scale-Marker der Sibling-Specs gegen das HA-`tiers.json` prüfen, oder bleibt das Review-Aufgabe?
- **Auto-Remediation-Kette**: Lohnt eine Verkettung, die high-Findings direkt an den jeweils zuständigen Edit-Skill weiterreicht? Aktuell jedes Finding manuell zu dispatchen.
