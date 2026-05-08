# HA-Integration: Test-Harness

Status: draft

## Kontext

Eine Custom Integration ohne Test-Harness ist ein Kandidat für stille Regressionen — Config-Flow, Coordinator-Update-Logik, Error-Mapping und Service-Handler haben jeweils einen verzweigten Code-Pfad mit nicht-trivialer Async-Choreographie, die ad-hoc-getestet schwer zu fangen ist. HA stellt mit `pytest-homeassistant-custom-component` einen offiziellen Test-Helper bereit, der eine HA-`HomeAssistant`-Instanz pro Test aufsetzt, das Config-Entries-System bereitstellt, das `hass`-Fixture liefert und kompatible Helper für `MockConfigEntry`, `ZeroconfServiceInfo`, `aioresponses` und Frame-mocking exponiert.

`nolte/kamerplanter-ha` validiert dieses Pattern mit einem `tests/`-Baum, der `conftest.py` (Fixtures: `mock_config_entry_data`, `mock_api` mit `load_fixture(...)`-basierten JSON-Antworten), Modul-Tests pro Schlüssel-Datei (`test_config_flow.py`, `test_coordinator.py`, `test_api.py`, `test_init.py`, `test_helpers.py`, `test_lovelace_cleanup.py`, `test_diagnostics.py`) und einen `fixtures/`-Ordner mit JSON-Antworten enthält. `pytest.ini` setzt `asyncio_mode = auto`, sodass Tests den `async def`-Stil nutzen können, ohne pro Test einen Decorator zu setzen.

Diese Spec überführt das Pattern in eine generische Verpflichtung. Sie definiert Test-Layout, Pflicht-Fixtures, Coverage-Erwartungen und konkrete Test-Patterns (Config-Flow-Test mit `MockConfigEntry`, Coordinator-Test mit Error-Mapping, Zeroconf-Test mit `ZeroconfServiceInfo`-Helper).

Quality-Scale-Marker: **Silver** (HA-Quality-Scale verlangt Test-Coverage über Config-Flow auf Bronze, und über Coordinator + Entities auf Silver; konkrete Coverage-Schwellen ergeben sich aus der Quality-Scale-Spec).

## Ziele

- `pytest-homeassistant-custom-component` als alleinigen Test-Stack festschreiben
- Test-Layout (Verzeichnisstruktur, Fixture-Dateien) standardisieren, sodass Skills die Form ohne Variation produzieren
- Pflicht-Fixtures (`hass`, `mock_config_entry_data`, `load_fixture`-basierte API-Mocks) definieren, sodass Test-Module sie ohne Setup-Boilerplate konsumieren
- Konkrete Test-Patterns für die kritischen Code-Pfade (Config-Flow, Coordinator-Error-Mapping, Zeroconf-Discovery) als Referenz vorgeben
- Coverage-Disziplin etablieren — keine Acceptance ohne Tests für die in den Folge-Specs als MUSS markierten Patterns

## Nicht-Ziele

- Backend-seitige Test-Harness — der Backend-Mock-Server / die Backend-Test-Suite ist außerhalb dieses Plugins
- End-to-End-Tests mit echter HA-Installation — eigene Folge-Spec, sobald die erste Integration sie konkret braucht
- Performance-Benchmarks — kein HA-Quality-Scale-Kriterium für Custom Integrations
- Mutation-Testing — kein etabliertes Pattern in HA-Custom-Integrationen
- HACS-Validation-Test — wird über CI-Job (`hacs/action@main`) abgedeckt, kein Pytest-Test

## Anforderungen

### Test-Stack

- **MUSS [MUST]** `pytest-homeassistant-custom-component` als Test-Stack verwenden — Pin in `requirements-dev.txt` (oder Äquivalent)
- **MUSS [MUST]** `pytest` und `pytest-asyncio` als transitives Requirements voraussetzen (werden von `pytest-homeassistant-custom-component` mit­geliefert)
- **SOLLTE [SHOULD]** `pytest-cov` für Coverage-Reports verwenden — Coverage ist Pflicht-Eingabe für Quality-Scale-Validierung
- **MUSS NICHT [MUST NOT]** das HA-Test-Setup ohne `pytest-homeassistant-custom-component` selbst rebuilden — der Helper kapselt jahrelange HA-interne Test-Konventionen

### `pytest.ini` / `pyproject.toml`

- **MUSS [MUST]** `asyncio_mode = auto` in `pytest.ini` (oder `[tool.pytest.ini_options]` in `pyproject.toml`) setzen — sonst muss jeder Async-Test mit `@pytest.mark.asyncio` dekoriert werden
- **SOLLTE [SHOULD]** den Test-Discovery-Pfad explizit setzen (`testpaths = tests` oder Ähnliches)
- **KANN [MAY]** Pytest-Plugins für QoL-Verbesserungen aktivieren (`-p no:warnings` für stillere Output, `--strict-markers` für saubere Marker-Disziplin)

### Verzeichnis-Layout

- **MUSS [MUST]** den Test-Baum unter `tests/` im Repository-Wurzelverzeichnis ablegen (siehe `nolte-shared:project-structure`)
- **MUSS [MUST]** `tests/conftest.py` mit den geteilten Fixtures enthalten
- **MUSS [MUST]** Modul-Tests pro Schlüssel-Datei der Integration anlegen — Konvention: `test_<module>.py` mit demselben Namen wie das geprüfte Modul (`test_config_flow.py`, `test_coordinator.py`, `test_api.py`, `test_init.py`, …)
- **SOLLTE [SHOULD]** einen `tests/fixtures/`-Ordner mit JSON-Dateien für API-Antwort-Mocks führen
- **KANN [MAY]** End-to-End-Tests in einem eigenen `tests/e2e/`-Unterordner ablegen, wenn sie konkret existieren

### Pflicht-Fixtures in `conftest.py`

- **MUSS [MUST]** ein `mock_config_entry_data`-Fixture definieren, das die Default-Eingabewerte für einen Setup-Test liefert (URL, API-Key, Tenant-Slug, andere `entry.data`-Felder) — mit unschädlichen Test-Werten (`http://localhost:8000`, `<test-prefix>_test_key_123`, `test-tenant`)
- **MUSS [MUST]** ein API-Client-Mock-Fixture definieren — typisch `mock_api` —, das die echte API-Klasse mit `unittest.mock.AsyncMock` ersetzt und `load_fixture(...)`-basierte JSON-Antworten zurückgibt
- **MUSS [MUST]** `load_fixture` aus `pytest_homeassistant_custom_component.common` verwenden — der Helper liest aus `tests/fixtures/<name>.json`
- **SOLLTE [SHOULD]** ein `mock_config_entry`-Fixture anbieten, das einen vollständig konfigurierten `MockConfigEntry` produziert und an `hass.config_entries` registriert
- **KANN [MAY]** weitere Fixtures für spezifische Setup-Stadien führen (z. B. `mock_loaded_config_entry` mit bereits durchgelaufenem `async_setup_entry`)

### Test-Patterns: Config-Flow

- **MUSS [MUST]** für jeden in `ha/config-flow-patterns` als MUSS markierten Step (`async_step_user`, `async_step_reauth`, `async_step_reconfigure`, Options-Flow) mindestens einen Happy-Path-Test und einen Sad-Path-Test (Validierungs-Fehler, Backend-Fehler) führen
- **MUSS [MUST]** den User-Flow-Test über `await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})` starten und das Form-Result über `await hass.config_entries.flow.async_configure(result["flow_id"], user_input={...})` weiterführen
- **MUSS [MUST]** das End-Result auf `FlowResultType.CREATE_ENTRY` (Happy-Path) oder `FlowResultType.FORM` mit `errors`-Dict (Sad-Path) prüfen
- **SOLLTE [SHOULD]** den `unique_id`-Abort-Pfad mit einem zweiten Init-Call (gegen denselben Endpoint) abdecken — `_abort_if_unique_id_configured` muss feuern

### Test-Patterns: Coordinator

- **MUSS [MUST]** für jeden Coordinator das Error-Mapping testen — Auth-Fehler raised `ConfigEntryAuthFailed`, Connection-Fehler raised `UpdateFailed`
- **MUSS [MUST]** den Test über einen `MagicMock(spec=<Api>)` mit `AsyncMock(side_effect=<AuthError>)` aufsetzen und den Coordinator-Update mit `pytest.raises(ConfigEntryAuthFailed)` umschließen
- **SOLLTE [SHOULD]** Happy-Path-Tests mit echten JSON-Fixtures als Coordinator-Antworten führen
- **MUSS [MUST]** den `_async_setup`-Pfad (Stammdaten-Ladung) testen, sofern er existiert — eine Mocking-Lücke an der Stelle führt zu falschen Asserts in den nachgelagerten Update-Tests

### Test-Patterns: Zeroconf-Discovery

- **MUSS [MUST]** für `async_step_zeroconf` einen Test mit einem `_make_zeroconf_info(...)`-Helper anlegen, der einen `ZeroconfServiceInfo` mit den TXT-Records aufsetzt, die das Backend liefern würde
- **MUSS [MUST]** den Test sowohl für Greenfield-Discovery (kein existierender Entry) als auch für Re-Discovery (bestehender Entry mit alter IP) führen — letzteres prüft die `_abort_if_unique_id_configured(updates={...})`-Logik
- **SOLLTE [SHOULD]** den `_make_zeroconf_info`-Helper in `conftest.py` oder in einem Test-Helper-Modul (`tests/helpers.py`) zentralisieren

### Test-Patterns: Lifecycle

- **MUSS [MUST]** `async_setup_entry` und `async_unload_entry` jeweils über `hass.config_entries.async_setup(entry.entry_id)` und `hass.config_entries.async_unload(entry.entry_id)` testen
- **MUSS [MUST]** prüfen, dass `entry.runtime_data` nach `async_setup_entry` gesetzt ist (siehe `ha/runtime-data-pattern`)
- **MUSS [MUST]** prüfen, dass `entry.runtime_data` nach `async_unload_entry` nicht mehr lesbar ist (HA bereinigt automatisch)

### Test-Patterns: Diagnostics

- **MUSS [MUST]** für `async_get_config_entry_diagnostics` einen Test führen, der den Output gegen das `TO_REDACT`-Set prüft — Credentials in `entry.data` müssen als `**REDACTED**` erscheinen
- **SOLLTE [SHOULD]** den Test über `from pytest_homeassistant_custom_component.common import async_get_config_entry_diagnostics` ausführen — der Helper kapselt den HA-internen Diagnostics-Aufruf

### Coverage-Disziplin

- **SOLLTE [SHOULD]** mindestens **80 % Statement-Coverage** über `custom_components/<domain>/` halten — gemessen via `pytest --cov=custom_components.<domain> --cov-report=term-missing`
- **SOLLTE [SHOULD]** **Branch-Coverage** zusätzlich messen, um if/else-Pfade in Error-Mapping zu validieren
- **MUSS NICHT [MUST NOT]** `# pragma: no cover` ohne Begründung als Code-Kommentar daneben verwenden — jeder Branch-Skip muss erklärt sein

### CI-Integration

- **MUSS [MUST]** Tests im CI-Job (`task test` aus `Taskfile.yml` plus `pytest tests/`) ausführen — schon im PR-Check, nicht erst beim Release
- **SOLLTE [SHOULD]** den `hacs/action@main`-Validator und `hassfest`-Integration-Validator parallel laufen lassen

## Akzeptanzkriterien

- [ ] `requirements-dev.txt` (oder Äquivalent) pinnt `pytest-homeassistant-custom-component` an eine konkrete Version
- [ ] `pytest.ini` oder `[tool.pytest.ini_options]` setzt `asyncio_mode = auto`
- [ ] `tests/conftest.py` existiert und enthält mindestens `mock_config_entry_data`, ein API-Client-Mock-Fixture, und nutzt `load_fixture` aus `pytest_homeassistant_custom_component.common`
- [ ] `tests/test_config_flow.py` deckt User-Flow-Happy-Path, User-Flow-Sad-Path, und (sofern vorhanden) Reauth/Reconfigure/Options-Flow ab
- [ ] `tests/test_coordinator.py` deckt Error-Mapping (Auth → `ConfigEntryAuthFailed`, Connection → `UpdateFailed`) ab
- [ ] Wenn `manifest.json:zeroconf` gesetzt: `tests/test_config_flow.py` enthält Zeroconf-Discovery-Tests inklusive Re-Discovery-mit-IP-Wechsel
- [ ] `tests/test_init.py` testet `async_setup_entry` und `async_unload_entry`-Lifecycle
- [ ] `tests/test_diagnostics.py` (sofern Diagnostics existiert) prüft Redaction über `TO_REDACT`
- [ ] CI führt `pytest tests/ -v --cov=custom_components.<domain>` aus
- [ ] Quality-Scale-Marker: **Silver**

## Offene Fragen

- **Coverage-Schwelle als MUSS**: Aktuell als „mindestens 80 %" SOLLTE formuliert. Soll daraus eine harte Pflicht werden, mit CI-Fail unterhalb der Schwelle?
- **Branch-Coverage-Pflicht**: Statement-Coverage allein lässt if/else-Lücken in Error-Mapping durchrutschen. Soll Branch-Coverage MUSS werden, sobald Tooling stabil ist?
- **End-to-End-Test-Schwelle**: Wann verlangt eine Folge-Spec E2E-Tests gegen eine echte HA-Instanz? Aktuell als Nicht-Ziel ausgeschlossen.
- **`MockConfigEntry`-vs.-`async_init`-Stil**: HA-interne Test-Stilkonventionen schwanken zwischen den beiden. Soll die Spec einen Stil als Default vorschreiben?
- **Fixture-Sharing über Repos**: Sollen die `_make_zeroconf_info`- und `mock_api`-Helper portfolio-weit als Library veröffentlicht werden, oder bleiben sie pro Repo dupliziert?
