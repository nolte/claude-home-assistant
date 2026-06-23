# HA Integration: Test Harness

Status: draft

## Context

A Custom Integration without a test harness is a candidate for silent regressions — config flow, coordinator update logic, error mapping, and service handlers all carry branched code paths with non-trivial async choreography that is hard to catch through ad-hoc testing. HA provides `pytest-homeassistant-custom-component` as the official test helper that spins up an HA `HomeAssistant` instance per test, supplies the config-entries system, exposes the `hass` fixture, and offers compatible helpers for `MockConfigEntry`, `ZeroconfServiceInfo`, `aioresponses`, and frame mocking.

`nolte/kamerplanter-ha` validates this pattern with a `tests/` tree that contains `conftest.py` (fixtures: `mock_config_entry_data`, `mock_api` with `load_fixture(...)`-based JSON responses), per-key-module tests (`test_config_flow.py`, `test_coordinator.py`, `test_api.py`, `test_init.py`, `test_helpers.py`, `test_lovelace_cleanup.py`, `test_diagnostics.py`), and a `fixtures/` folder with JSON responses. `pytest.ini` sets `asyncio_mode = auto`, so tests can use the `async def` style without setting a decorator per test.

This spec lifts the pattern into a generic obligation. It defines test layout, mandatory fixtures, coverage expectations, and concrete test patterns (config-flow test with `MockConfigEntry`, coordinator test with error mapping, zeroconf test with the `ZeroconfServiceInfo` helper).

Quality scale marker: **Silver** (the HA quality scale requires test coverage over config flow at Bronze, and over coordinator + entities at Silver; concrete coverage thresholds emerge from the quality-scale spec).

## Goals

- Establish `pytest-homeassistant-custom-component` as the only test stack
- Standardise the test layout (directory structure, fixture files), so skills produce the shape without variation
- Define mandatory fixtures (`hass`, `mock_config_entry_data`, `load_fixture`-based API mocks), so test modules consume them without setup boilerplate
- Provide concrete test patterns for the critical code paths (config flow, coordinator error mapping, zeroconf discovery) as reference
- Establish coverage discipline — no acceptance without tests for the patterns that follow-up specs mark as MUST

## Non-Goals

- Backend-side test harness — the backend mock server / backend test suite is outside this plugin
- End-to-end tests against a real HA installation — separate follow-up spec once the first integration concretely needs them
- Performance benchmarks — not an HA quality-scale criterion for Custom Integrations
- Mutation testing — no established pattern in HA Custom Integrations
- HACS validation test — covered by the CI job (`hacs/action@main`), not a pytest test

## Requirements

### Test stack

- **MUST** use `pytest-homeassistant-custom-component` as the test stack — pin in `requirements-dev.txt` (or equivalent)
- **MUST** require `pytest` and `pytest-asyncio` as transitive dependencies (shipped with `pytest-homeassistant-custom-component`)
- **SHOULD** use `pytest-cov` for coverage reports — coverage is a mandatory input for quality-scale validation
- **MUST NOT** rebuild the HA test setup without `pytest-homeassistant-custom-component` — the helper encapsulates years of HA-internal test conventions

### `pytest.ini` / `pyproject.toml`

- **MUST** set `asyncio_mode = auto` in `pytest.ini` (or `[tool.pytest.ini_options]` in `pyproject.toml`) — otherwise every async test must be decorated with `@pytest.mark.asyncio`
- **SHOULD** set the test-discovery path explicitly (`testpaths = tests` or similar)
- **MAY** enable pytest plugins for QoL improvements (`-p no:warnings` for quieter output, `--strict-markers` for clean marker discipline)

### Directory layout

- **MUST** place the test tree under `tests/` at the repository root (see `nolte-shared:project-structure`)
- **MUST** include `tests/conftest.py` with shared fixtures
- **MUST** create per-key-module tests for each integration module — convention: `test_<module>.py` with the same name as the tested module (`test_config_flow.py`, `test_coordinator.py`, `test_api.py`, `test_init.py`, …)
- **SHOULD** keep a `tests/fixtures/` folder with JSON files for API-response mocks
- **MAY** place end-to-end tests in a separate `tests/e2e/` subfolder when they concretely exist

### Mandatory fixtures in `conftest.py`

- **MUST** define a `mock_config_entry_data` fixture that supplies default input values for a setup test (URL, API key, tenant slug, other `entry.data` fields) — with harmless test values (`http://localhost:8000`, `<test-prefix>_test_key_123`, `test-tenant`)
- **MUST** define an API-client mock fixture — typically `mock_api` — that replaces the real API class with `unittest.mock.AsyncMock` and returns `load_fixture(...)`-based JSON responses
- **MUST** use `load_fixture` from `pytest_homeassistant_custom_component.common` — the helper reads from `tests/fixtures/<name>.json`
- **SHOULD** offer a `mock_config_entry` fixture that produces a fully configured `MockConfigEntry` and registers it on `hass.config_entries`
- **MAY** carry additional fixtures for specific setup stages (for example `mock_loaded_config_entry` with `async_setup_entry` already executed)

### Test patterns: config flow

- **MUST** carry at least one happy-path test and one sad-path test (validation error, backend error) for every step marked MUST in `ha/config-flow-patterns` (`async_step_user`, `async_step_reauth`, `async_step_reconfigure`, options flow)
- **MUST** start the user-flow test through `await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})` and progress the form result via `await hass.config_entries.flow.async_configure(result["flow_id"], user_input={...})`
- **MUST** check the end result for `FlowResultType.CREATE_ENTRY` (happy path) or `FlowResultType.FORM` with the `errors` dict (sad path)
- **SHOULD** cover the `unique_id` abort path with a second init call (against the same endpoint) — `_abort_if_unique_id_configured` must fire

### Test patterns: coordinator

- **MUST** test error mapping for every coordinator — auth errors raise `ConfigEntryAuthFailed`, connection errors raise `UpdateFailed`
- **MUST** set the test up via a `MagicMock(spec=<Api>)` with `AsyncMock(side_effect=<AuthError>)` and wrap the coordinator update with `pytest.raises(ConfigEntryAuthFailed)`
- **SHOULD** carry happy-path tests with real JSON fixtures as coordinator responses
- **MUST** test the `_async_setup` path (master-data load) when present — a mocking gap there leads to false asserts in the downstream update tests

### Test patterns: zeroconf discovery

- **MUST** create a test for `async_step_zeroconf` with a `_make_zeroconf_info(...)` helper that builds a `ZeroconfServiceInfo` carrying the TXT records the backend would deliver
- **MUST** run the test for both greenfield discovery (no existing entry) and re-discovery (existing entry with old IP) — the latter checks the `_abort_if_unique_id_configured(updates={...})` logic
- **SHOULD** centralise the `_make_zeroconf_info` helper in `conftest.py` or a test-helper module (`tests/helpers.py`)

### Test patterns: lifecycle

- **MUST** test `async_setup_entry` and `async_unload_entry` via `hass.config_entries.async_setup(entry.entry_id)` and `hass.config_entries.async_unload(entry.entry_id)`
- **MUST** verify that `entry.runtime_data` is set after `async_setup_entry` (see `ha/runtime-data-pattern`)
- **MUST** verify that `entry.runtime_data` is no longer readable after `async_unload_entry` (HA cleans up automatically)

### Test patterns: diagnostics

- **MUST** carry a test for `async_get_config_entry_diagnostics` that checks the output against the `TO_REDACT` set — credentials in `entry.data` must appear as `**REDACTED**`
- **SHOULD** run the test through `from pytest_homeassistant_custom_component.common import async_get_config_entry_diagnostics` — the helper encapsulates the HA-internal diagnostics call

### Coverage discipline

- **SHOULD** maintain at least **80 % statement coverage** across `custom_components/<domain>/` — measured via `pytest --cov=custom_components.<domain> --cov-report=term-missing`
- **SHOULD** additionally measure **branch coverage** to validate if / else paths in error mapping
- **MUST NOT** use `# pragma: no cover` without an explanatory comment next to it — every branch skip must be justified

### CI integration

- **MUST** run tests in the CI job (`task test` from `Taskfile.yml` plus `pytest tests/`) — already at PR check time, not only at release
- **SHOULD** run the `hacs/action@main` validator and the `hassfest` integration validator in parallel

## Acceptance Criteria

- [ ] `requirements-dev.txt` (or equivalent) pins `pytest-homeassistant-custom-component` to a concrete version
- [ ] `pytest.ini` or `[tool.pytest.ini_options]` sets `asyncio_mode = auto`
- [ ] `tests/conftest.py` exists and contains at least `mock_config_entry_data`, an API-client mock fixture, and uses `load_fixture` from `pytest_homeassistant_custom_component.common`
- [ ] `tests/test_config_flow.py` covers user-flow happy path, user-flow sad path, and (when present) reauth / reconfigure / options flow
- [ ] `tests/test_coordinator.py` covers error mapping (auth → `ConfigEntryAuthFailed`, connection → `UpdateFailed`)
- [ ] When `manifest.json:zeroconf` is set: `tests/test_config_flow.py` carries zeroconf discovery tests including re-discovery with IP change
- [ ] `tests/test_init.py` tests `async_setup_entry` and `async_unload_entry` lifecycle
- [ ] `tests/test_diagnostics.py` (when diagnostics exists) checks redaction via `TO_REDACT`
- [ ] CI runs `pytest tests/ -v --cov=custom_components.<domain>`
- [ ] Quality scale marker: **Silver**

## Open Questions

- **Coverage threshold as MUST**: Currently formulated as "at least 80 %" SHOULD. Should this become a hard requirement with CI fail below the threshold?
- **Branch-coverage requirement**: Statement coverage alone lets if / else gaps in error mapping slip through. Should branch coverage become MUST once tooling stabilises?
- **End-to-end test threshold**: When does a follow-up spec require E2E tests against a real HA instance? Currently excluded as a non-goal.
- **`MockConfigEntry` vs. `async_init` style**: HA-internal test conventions oscillate between both. Should the spec prescribe one style as default?
- **Fixture sharing across repos**: Should the `_make_zeroconf_info` and `mock_api` helpers be published portfolio-wide as a library, or stay duplicated per repo?
