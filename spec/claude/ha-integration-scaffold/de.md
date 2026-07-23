# Skill: `ha-integration-scaffold`

Status: draft

## Kontext

Ein Greenfield-Setup einer Home-Assistant Custom Integration besteht aus etwa zwölf Pflicht-Dateien (siehe `ha/integration-architecture`), deren Inhalte voneinander abhängen: `manifest.json:domain` matched den Ordnernamen, der Translation-Key in `strings.json` matched `_attr_translation_key` in den Plattformen, der Icon-Eintrag in `icons.json` matched denselben Translation-Key, das `runtime_data`-Type-Alias in `__init__.py` matched die Imports in den Plattformen. Manuelles Scaffolding produziert systematisch Drift an genau diesen Schnittstellen — der Translation-Key ist im Code anders geschrieben als in `strings.json`, das Icon-Mapping vergisst eine Plattform, der Coordinator-Lookup-Schlüssel weicht zwischen `__init__.py` und `sensor.py` ab.

Dieser Skill destilliert die nolte-Konventionen (kodifiziert in den `spec/ha/*`-Specs) zu einem deterministischen Generator, der ein vollständiges Custom-Integration-Skelett in einem Aufwasch produziert, ohne dass Konsumenten danach Cross-File-Konsistenz manuell verifizieren müssen.

## Scope

Der Skill scaffolded ein **Greenfield-Skelett** für eine HA Custom Integration. Er verändert kein existierendes `custom_components/<domain>/`, refaktorisiert keine bestehende Integration und macht keine Migration von einem alten Stand auf den nolte-Stil. Reine Edits an einer existierenden Integration laufen über die jeweilige Detail-Spec (`ha/config-flow-patterns`, `ha/coordinator-patterns`, …) plus Code-Editier­schritte; sie sind nicht Aufgabe dieses Skills.

## Ziele

- Ein Custom-Integration-Skelett produzieren, das alle in `spec/ha/*` als MUSS markierten Patterns auf Anhieb erfüllt — Bronze/Silver der HA-Quality-Scale ist out-of-the-box erreicht
- Cross-File-Konsistenz garantieren: derselbe `domain`, derselbe `translation_key`, derselbe Coordinator-Schlüssel über manifest.json, `__init__.py`, `const.py`, `config_flow.py`, `coordinator.py`, `sensor.py`, `strings.json`, `translations/`, `icons.json`, `diagnostics.py`, Tests
- Den Konsumenten in einen lauffähigen, lint-sauberen, test-laufenden Zustand bringen, ohne dass er die Detail-Specs erst durchlesen muss — die Specs bleiben die kanonische Quelle, der Skill ist der Werkzeug-Einstieg
- Eine `plan.md`-Annotation ausgeben, die dem Konsumenten zeigt, welche Datei welche Spec verkörpert — Mapping zwischen Code und `spec/ha/*`-Patterns

## Nicht-Ziele

- Backend-API-Client-Logik — der Skill liefert ein API-Client-Skelett mit Path-Whitelist und Bearer-Gating (siehe `ha/security-hardening`); die konkrete API-Operation-Logik (welche Endpoints, welches JSON-Schema) bleibt Konsumenten-Aufgabe
- HACS-Distribution-Setup — `hacs.json` wird optional erzeugt, aber der HACS-Submission-Prozess (Repo-Listing bei HACS) ist außerhalb
- ESPHome- oder Add-on-Scaffolding — eigene Folge-Skills (`ha-esphome-component-scaffold`, `ha-addon-scaffold`)
- Lovelace-Card-Scaffolding — separater Skill (`ha-lovelace-card-scaffold`); die Cards landen unter `custom_components/<domain>/www/`, werden aber von einem dedizierten Skill produziert
- Migration einer existierenden YAML-konfigurierten Integration auf Config-Flow — eigene Folge-Skill, falls überhaupt nötig
- Multi-Tenant-spezifische Setup-Logik — der Skill scaffolded den User-Step plus optionalen Tenant-Step als generischen Multi-Step-Flow; tenant-spezifische Logik füllt der Konsument

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „scaffold a new HA Custom Integration"
  - „create a Home Assistant integration"
  - „neue HA-Integration scaffolden"
  - „skeleton einer HA Custom Integration anlegen"
  - „bootstrap a new HACS-compatible integration"
- **MUSS NICHT [MUST NOT]** aktivieren bei:
  - reinen Edits an einer existierenden Integration (Domain bereits unter `custom_components/`)
  - Lovelace-Card-Erzeugung (anderer Skill)
  - Blueprint-/Automation-Erzeugung (anderer Skill)
  - ESPHome-Custom-Component (anderer Skill)
  - Migration einer YAML-Konfig-Integration auf Config-Flow (anderer Skill)

### Eingaben

- **MUSS [MUST]** folgende Pflicht-Eingaben erfassen, bevor er etwas schreibt:
  - `domain` — lowercase ASCII slug (`[a-z0-9_]+`); identifiziert die Integration eindeutig in HA-Frontend, Service-Namespace und Translation-Key-Präfix
  - `name` — menschenlesbarer Display-Name (z. B. „Acme Plant Manager")
  - `description` — 1–2-Satz-Beschreibung für `manifest.json` und `README.md`
  - `codeowner` — GitHub-Handle mit `@`-Präfix (mindestens einer)
  - `integration_type` — eines von `hub`, `device`, `service` (siehe `ha/integration-architecture`)
  - `iot_class` — eines von `local_polling`, `local_push`, `cloud_polling`, `cloud_push`, `assumed_state`, `calculated`
  - `target_dir` — der Repository-Wurzel-Pfad, in den scaffolded wird (typisch ein leeres oder neu angelegtes Konsumenten-Repo)
- **SOLLTE [SHOULD]** folgende Optionen erfassen, bevor er schreibt — Defaults wenn der User nicht antwortet:
  - `hacs` (Default `true`) — `hacs.json` mit erzeugen
  - `zeroconf` (Default `false`) — Zeroconf-Discovery-Step in `config_flow.py` mit erzeugen; setzt zusätzlich `manifest.json:zeroconf`
  - `auth` (Default `true`) — Reauth-Flow erzeugen; falls `false`, wird kein Reauth-Step generiert
  - `platforms` (Default `["sensor"]`) — Liste der HA-Plattformen, die scaffolded werden sollen
- **MUSS NICHT [MUST NOT]** Defaults verwenden, ohne sie dem User in der Output-Zusammenfassung explizit zu nennen

### Pre-Flight (vor jedem Lauf)

- **MUSS [MUST]** in dieser Reihenfolge prüfen und bei jedem fehlgeschlagenen Schritt abbrechen:
  1. `target_dir` ist ein git-Repository (`git rev-parse --is-inside-work-tree`)
  2. Working tree in `target_dir` ist sauber (keine uncommitted Changes)
  3. `target_dir/custom_components/<domain>/` existiert noch nicht — Kollisions­vermeidung; auf Treffer abbrechen mit Pfad-Quote
  4. `target_dir/manifest.json` (auf Repository-Wurzel-Ebene) existiert nicht — eine `manifest.json` im Wurzel ist ein anderes Layout (typisch ein Add-on) und wäre Konflikt
- **MUSS NICHT [MUST NOT]** das Repository für den User initialisieren oder committen — der Konsument ist verantwortlich für git-Init und initialen Commit

### Generator-Choreographie

Der Skill schreibt diese Dateien in einem Aufwasch (kein User-Approval pro Datei — Bulk-Approval implizit durch Skill-Aufruf):

- **Pflicht (immer)**:
  - `custom_components/<domain>/manifest.json` — alle Pflichtfelder aus `ha/integration-architecture`
  - `custom_components/<domain>/__init__.py` — `async_setup_entry` + `async_unload_entry` mit `runtime_data` (siehe `ha/runtime-data-pattern`)
  - `custom_components/<domain>/const.py` — `DOMAIN`, `PLATFORMS`, `CONF_*`-Keys, `DEFAULT_POLL_*`/`MIN_POLL_*`-Defaults
  - `custom_components/<domain>/api.py` — API-Client-Skelett mit `_API_PATH_RE`-Whitelist und `_with_auth`-Helper (siehe `ha/security-hardening`)
  - `custom_components/<domain>/config_flow.py` — User-Flow plus Reauth (sofern `auth=true`) plus Reconfigure plus Options-Flow (siehe `ha/config-flow-patterns`)
  - `custom_components/<domain>/coordinator.py` — eine `<Domain>Coordinator`-Klasse mit Error-Mapping (siehe `ha/coordinator-patterns`)
  - `custom_components/<domain>/entity.py` — Base-Entity-Klasse plus DeviceInfo-Factory-Funktionen (siehe `ha/entity-architecture` und `ha/device-registry`)
  - `custom_components/<domain>/<platform>.py` für jede Plattform aus `platforms` — `EntityDescription`-Tupel-Liste plus generische Entity-Klasse und eine modul-weite `PARALLEL_UPDATES`-Konstante (Silver `parallel-updates`) (siehe `ha/entity-architecture`)
  - `custom_components/<domain>/strings.json` — Englische Quell-Strings für Config-Flow, Entitäten, ggf. Services (siehe `ha/translations`)
  - `custom_components/<domain>/translations/en.json` — Spiegel von `strings.json`
  - `custom_components/<domain>/translations/de.json` — Deutsche Übersetzung
  - `custom_components/<domain>/icons.json` — Icon-Mappings für Entitäten (siehe `ha/icons`)
  - `custom_components/<domain>/diagnostics.py` — Redaction-Hook mit `TO_REDACT`-Set (siehe `ha/diagnostics`)
  - `tests/conftest.py` — geteilte Fixtures (`mock_config_entry_data`, `mock_api`) (siehe `ha/test-harness`)
  - `tests/test_config_flow.py` — Happy-/Sad-Path-Tests für User-Flow
  - `tests/test_coordinator.py` — Error-Mapping-Tests
  - `tests/test_init.py` — Lifecycle-Test für Setup/Unload
  - `tests/test_diagnostics.py` — Redaction-Test
  - `tests/fixtures/health.json` — Beispiel-API-Response als Test-Fixture
  - `pytest.ini` (oder Anhang an `pyproject.toml`) — `asyncio_mode = auto`
- **Optional je nach Eingabe**:
  - `hacs.json` (wenn `hacs=true`) — `name`, `render_readme: true`, `homeassistant: <version>`
  - `services.yaml` plus Service-Handler-Stub in `__init__.py` (wenn `platforms` mindestens einen Service-emittierenden Plattform-Typ enthält oder der User explizit Services anfordert)
  - `__init__.py`-Auto-Registrierung-Block für Lovelace-Cards (wenn `lovelace=true` — Default `false`)

### Cross-File-Konsistenz

- **MUSS [MUST]** denselben `<domain>`-Wert über alle generierten Dateien verwenden:
  - Ordnername unter `custom_components/`
  - `manifest.json:domain`
  - `DOMAIN`-Konstante in `const.py`
  - `domain`-Class-Attribut in `ConfigFlow`
  - Logger-Name (`custom_components.<domain>`)
- **MUSS [MUST]** den-/dieselbe Coordinator-Schlüssel zwischen `__init__.py` (`runtime_data.coordinators["<key>"]`) und Plattform-Modulen (`entry.runtime_data.coordinators["<key>"]`) verwenden
- **MUSS [MUST]** den-/dieselbe Translation-Key zwischen `EntityDescription.translation_key` (in den Plattform-Modulen), `strings.json` (`entity.<platform>.<key>.name`) und `icons.json` (`entity.<platform>.<key>.default`) verwenden
- **MUSS [MUST]** denselben `unique_id`-Format-String über alle Plattform-Module verwenden: `f"{entry.entry_id}_<resource>_<slug>_<descriptor>"`

### `plan.md`-Annotation

- **MUSS [MUST]** nach Abschluss des Scaffoldings eine `plan.md` im Wurzel des `target_dir` schreiben, die folgende Abschnitte enthält:
  - **Spec-Abdeckung** — Mapping „<Datei> erfüllt <spec/ha/*-Slug> Anforderung X" für jede generierte Datei
  - **Quality-Scale-Stand** — was Bronze/Silver/Gold-konform aus dem Skelett ist und was der Konsument noch füllen muss
  - **Nächste Schritte** — die konkrete Liste der Edits (API-Endpoints in `api.py` füllen, Plattform-`EntityDescription`-Tupel mit echten Datapoints füllen, Backend-Tests in `tests/fixtures/` ergänzen)
  - **Open Questions** — die übernommenen Open-Question-Items aus den involvierten `spec/ha/*`-Specs, die Konsumenten-Entscheidung verlangen

### Boundaries zu Nachbar-Skills

- **API-Client-Spezifik** (echte Endpoints, echte Schemas, echte Validierungs-Logik) → kein dedizierter Skill geplant; Konsumenten-Aufgabe
- **Config-Flow-Anpassungen** über das Default hinaus (Multi-Step-Tenants, Custom-Discovery) → eigener Skill `ha-config-flow-augment`
- **Coordinator-Topologie-Erweiterung** über den Single-Coordinator hinaus → eigener Skill `ha-coordinator-add`
- **Lovelace-Card-Scaffold** → eigener Skill `ha-lovelace-card-scaffold`
- **Test-Coverage über das Default-Skelett hinaus** → eigener Skill `ha-test-harness-augment`
- **Deploy/Verify in den Kind-Cluster** → Agent `ha-integration-deployer` / `ha-integration-verifier`
- **HA-spezifischer CI-Workflow** (hassfest / hacs-validate / pytest-Matrix) → eigener Skill `ha-integration-ci-scaffold` (geplant); das generische `nolte-shared:project-structure-apply` emittiert keine HA-spezifische CI

## Akzeptanzkriterien

- [ ] Der Skill scaffolded `custom_components/<domain>/` mit allen Pflicht-Dateien aus dem Generator-Choreographie-Block
- [ ] Der Skill scaffolded `tests/` mit den vier Pflicht-Tests (`test_config_flow`, `test_coordinator`, `test_init`, `test_diagnostics`)
- [ ] `manifest.json:domain` matched den Ordnernamen unter `custom_components/`
- [ ] `pytest tests/` läuft fehlerfrei direkt nach Scaffold (Tests gegen Mock-API)
- [ ] `ruff check custom_components/<domain>/` läuft fehlerfrei direkt nach Scaffold
- [ ] hassfest (via `hacs/action@main`) validiert die scaffoldete Integration ohne Errors
- [ ] Der Skill bricht ab, wenn `target_dir/custom_components/<domain>/` bereits existiert
- [ ] Der Skill schreibt eine `plan.md` mit Spec-Abdeckungs-Mapping, Quality-Scale-Stand, Nächste-Schritte und Open Questions
- [ ] `runtime_data` ist typisiert via `@dataclass`, kein Vorkommen von `hass.data[DOMAIN]` im Code
- [ ] `_attr_has_entity_name = True` auf der Base-Entity-Klasse, kein Vorkommen von `_attr_name = "<hardcoded>"` in den Plattform-Modulen
- [ ] Translation-Keys konsistent zwischen `strings.json`, `translations/<lang>.json`, `icons.json` und Plattform-Code
- [ ] Jedes generierte Plattform-Modul deklariert eine modul-weite `PARALLEL_UPDATES`-Konstante (Silver `parallel-updates`)

## Offene Fragen

- **Service-Definition-Schwelle**: Wann scaffolded der Skill `services.yaml`? Aktuell als „wenn der User Services explizit anfordert" formuliert — eine Heuristik (z. B. „immer, wenn `integration_type=hub`") wäre konkreter.
- **Multi-Coordinator-Default**: Der Skill scaffolded heute einen einzelnen Coordinator. Soll er bei `iot_class=local_polling` und `integration_type=hub` automatisch einen zweiten Coordinator (Alerts mit kürzerem Intervall) anlegen, oder bleibt das Konsumenten-Aufgabe?
- **`requirements`-Skelett**: Soll der Skill `aiohttp` als Default-Requirement in `manifest.json` setzen, oder bleibt das User-Aufgabe? `kamerplanter-ha` hat ein leeres `requirements`-Array, weil der API-Client `aiohttp` aus HA bereitstellt.
- **`README.md`-Scaffold**: Soll der Skill eine `README.md` für das Konsumenten-Repo erzeugen oder ist die Konsumenten-README außerhalb? Aktuell nicht in der Pflicht-Liste.
- **CI-Workflow-Scaffold**: HA-spezifische CI (hassfest / hacs-validate / pytest-Matrix) gehört dem dedizierten Skill `ha-integration-ci-scaffold` (geplant), nicht dem generischen `nolte-shared:project-structure-apply` (das keine HA-spezifische CI emittiert). Die Akzeptanz dieses Skills verlangt nur, dass hassfest *besteht*, nicht dass er den Workflow erzeugt. Ob `ha-integration-scaffold` automatisch in `ha-integration-ci-scaffold` verketten soll, bleibt offen.
- **`plan.md`-Format-Schwelle**: Wie strukturiert ist `plan.md`? Aktuell als formloses Mapping formuliert; eine Pflicht-Vorlage wäre konkreter, aber starr.
