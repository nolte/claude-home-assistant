# Skill: `ha-test-harness-augment`

Status: draft

## Kontext

Der initiale Scaffold-Skill liefert vier Pflicht-Tests aus (`test_config_flow`, `test_coordinator`, `test_init`, `test_diagnostics`). Eine reife Integration wächst über diesen Stand hinaus: Plattform-Tests pro `<platform>.py`, Service-Tests pro Service, Helper-Tests, Lovelace-Cleanup-Tests, ggf. End-to-End-Tests gegen einen Mock-Backend-Server. Dieser Skill ergänzt die Test-Suite um genau diese zusätzlichen Test-Klassen, ohne den vorhandenen Bestand zu zerstören.

## Scope

Der Skill ergänzt **eine** Test-Klasse (Plattform-Tests, Service-Tests, Helper-Tests, Lovelace-Cleanup-Tests) pro Aufruf. Er löscht keine Tests, mergt keine, ändert keine Fixtures, die andere Tests konsumieren. Er erweitert `tests/conftest.py` um zusätzliche Fixtures, falls die neuen Tests sie brauchen — bestehende Fixtures bleiben unverändert.

## Ziele

- Test-Coverage für sekundäre Code-Pfade (Plattformen, Services, Helpers) ohne dass der User die Test-Konventionen aus `ha/test-harness` neu durchlesen muss
- Cross-File-Konsistenz mit den Quell-Modulen — die Tests referenzieren existierende Fixtures, JSON-Snapshots, Mock-API-Methoden, statt eigene Setup-Boilerplate zu wiederholen
- Coverage-Ausweis im Skill-Output: welche Code-Pfade sind durch den Augment frisch abgedeckt
- HA-Quality-Scale-Bewusstsein: Plattform- und Service-Tests sind Silver-Pflicht; ein klarer Coverage-Bericht zeigt, wann Silver erreicht ist

## Nicht-Ziele

- End-to-End-Tests gegen eine echte HA-Instanz oder einen Live-Backend — eigene Folge-Spec (E2E-Stack), sobald konkret nötig
- Test-Refactoring (Bestand umordnen, Fixtures konsolidieren) — manuelle Aufgabe
- Coverage-Schwelle-Forcing (CI-Fail unter X%) — Tooling-Frage, gehört in die CI-Konfig der Konsumenten
- Mutation-Testing oder Property-Based-Testing — keine etablierten Patterns in HA-Custom-Integrationen

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add tests for the sensor platform"
  - „add tests for the `<service_name>` service"
  - „add tests for the helpers module"
  - „erweitere die Test-Suite um Plattform-Tests"

### Eingaben

- **MUSS [MUST]** erfassen:
  - `target_dir`
  - `kind` — `platform`, `service`, `helpers`, `lovelace_cleanup`
  - Bei `kind=platform`: `platform_name` (sensor, binary_sensor, …)
  - Bei `kind=service`: `service_name`
  - Bei `kind=helpers`: keine zusätzliche Eingabe
  - Bei `kind=lovelace_cleanup`: keine zusätzliche Eingabe (testet die Lovelace-Resource-Lifecycle)

### Pre-Flight

- **MUSS [MUST]** prüfen:
  1. `target_dir` ist git-Repo, sauber
  2. Das Quell-Modul existiert (z. B. `<platform>.py` für `kind=platform`)
  3. Die zu generierende Test-Datei existiert noch nicht oder kann angehängt werden, ohne bestehenden Test-Code zu überschreiben

### Generator-Choreographie

- **MUSS [MUST]** je nach `kind` die passende Test-Datei anlegen oder erweitern:
  - `kind=platform` → `tests/test_<platform>.py`: Plattform-Setup-Test (asserts dass async_setup_entry für die Plattform die erwartete Anzahl Entitäten registriert), `_handle_coordinator_update`-Test (asserts dass `native_value` korrekt aus den Coordinator-Daten extrahiert wird), pro `EntityDescription` aus der Tupel-Liste mindestens einen Happy-Path-Test
  - `kind=service` → `tests/test_services.py`: Service-Test mit Happy-Path, fehlender Disambiguation, Auth-Fehler (siehe `ha-service-definition-generator`-Test-Pattern)
  - `kind=helpers` → `tests/test_helpers.py`: pro Helper-Funktion in `helpers.py` mindestens einen Test
  - `kind=lovelace_cleanup` → `tests/test_lovelace_cleanup.py`: testet die Lovelace-Card-Auto-Registrierung in `__init__.py` (StaticPathConfig-Aufruf, korrekte URLs, korrekte Pfade)
- **MUSS [MUST]** in `tests/conftest.py` zusätzliche Fixtures ergänzen, falls die neuen Tests sie brauchen — typisch: ein erweitertes `mock_api`-Fixture mit zusätzlichen Mock-Methoden
- **MUSS [MUST]** in `tests/fixtures/` JSON-Snapshots für Plattform-Tests anlegen, falls die Tests Coordinator-Daten als Input benötigen
- **SOLLTE [SHOULD]** in der Skill-Ausgabe den Coverage-Bericht-Befehl ausführen (`pytest --cov=custom_components.<domain>`) und das Delta zum Vor-Augment-Stand benennen
- **MUSS NICHT [MUST NOT]** existierenden Test-Code überschreiben oder löschen

### Verbote

- **MUSS NICHT [MUST NOT]** generische `Exception`-Catches in den Test-Helpern einbauen
- **MUSS NICHT [MUST NOT]** in den Tests blocking I/O ausführen — Tests laufen unter `asyncio_mode = auto`
- **MUSS NICHT [MUST NOT]** echte HA-Instanzen oder echte Backends ansprechen — nur Mocks und Fixtures

## Akzeptanzkriterien

- [ ] Die passende Test-Datei existiert und enthält die Tests gemäß `kind`
- [ ] `tests/conftest.py` ist um die nötigen Fixtures erweitert (sofern erforderlich)
- [ ] `tests/fixtures/` enthält die nötigen JSON-Snapshots
- [ ] `pytest tests/<test-file> -v` läuft fehlerfrei
- [ ] Skill-Output enthält Coverage-Delta gegenüber Vor-Augment-Stand
- [ ] Existierende Tests bleiben unverändert

## Offene Fragen

- **Coverage-Schwelle**: Sollen Skill-Output-Empfehlungen (z. B. „Silver erreicht ab 80%") angezeigt werden, oder bleibt das User-Aufgabe?
- **End-to-End-Tests**: Wann verlangt eine Folge-Spec E2E-Tests?
- **Snapshot-Tests** (z. B. mit `syrupy`): Sollen sie als Pattern unterstützt werden, oder bleibt es bei klassischen Asserts?
- **Test-Daten-Generation**: Soll der Skill Faker-/Hypothesis-basierte Test-Daten generieren, oder bleibt es bei statischen Fixtures?
