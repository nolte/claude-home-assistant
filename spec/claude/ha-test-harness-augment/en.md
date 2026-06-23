# Skill: `ha-test-harness-augment`

Status: draft

## Context

The initial scaffold ships four mandatory tests (`test_config_flow`, `test_coordinator`, `test_init`, `test_diagnostics`). A mature integration grows beyond that baseline: platform tests per `<platform>.py`, service tests per service, helper tests, Lovelace cleanup tests, possibly end-to-end tests against a mock backend server. This skill augments the test suite with exactly these additional test classes, without destroying the existing baseline.

## Scope

The skill augments **one** test class (platform tests, service tests, helper tests, Lovelace cleanup tests) per call. It does not delete tests, does not merge them, does not modify fixtures consumed by other tests. It extends `tests/conftest.py` with additional fixtures when the new tests need them — existing fixtures stay unchanged.

## Goals

- Test coverage for secondary code paths (platforms, services, helpers) without requiring the user to re-read the test conventions from `ha/test-harness`
- Cross-file consistency with the source modules — tests reference existing fixtures, JSON snapshots, mock API methods rather than repeating their own setup boilerplate
- Coverage reporting in the skill output: which code paths are now freshly covered by the augment
- HA quality-scale awareness: platform and service tests are a Silver requirement; a clear coverage report shows when Silver is reached

## Non-Goals

- End-to-end tests against a real HA instance or a live backend — separate follow-up spec (E2E stack) when concretely needed
- Test refactoring (rearrange the baseline, consolidate fixtures) — manual task
- Coverage-threshold enforcement (CI fail below X%) — tooling concern, lives in the consumer's CI config
- Mutation testing or property-based testing — no established patterns in HA Custom Integrations

## Requirements

### Activation triggers

- **MUST** activate on:
  - "add tests for the sensor platform"
  - "add tests for the `<service_name>` service"
  - "add tests for the helpers module"
  - "erweitere die Test-Suite um Plattform-Tests"

### Inputs

- **MUST** collect:
  - `target_dir`
  - `kind` — `platform`, `service`, `helpers`, `lovelace_cleanup`
  - On `kind=platform`: `platform_name` (sensor, binary_sensor, …)
  - On `kind=service`: `service_name`
  - On `kind=helpers`: no additional input
  - On `kind=lovelace_cleanup`: no additional input (tests the Lovelace resource lifecycle)

### Pre-flight

- **MUST** check:
  1. `target_dir` is a git repo, clean
  2. The source module exists (for example `<platform>.py` for `kind=platform`)
  3. The target test file does not yet exist or can be appended without overwriting existing test code

### Generator choreography

- **MUST** create or extend the relevant test file based on `kind`:
  - `kind=platform` → `tests/test_<platform>.py`: platform setup test (asserts that `async_setup_entry` for the platform registers the expected number of entities), `_handle_coordinator_update` test (asserts that `native_value` is extracted correctly from coordinator data), at least one happy-path test per `EntityDescription` in the tuple list
  - `kind=service` → `tests/test_services.py`: service test with happy path, missing disambiguation, auth error (see `ha-service-definition-generator` test pattern)
  - `kind=helpers` → `tests/test_helpers.py`: at least one test per helper function in `helpers.py`
  - `kind=lovelace_cleanup` → `tests/test_lovelace_cleanup.py`: tests the Lovelace card auto-registration in `__init__.py` (StaticPathConfig call, correct URLs, correct paths)
- **MUST** add additional fixtures in `tests/conftest.py` when the new tests need them — typically: an extended `mock_api` fixture with additional mock methods
- **MUST** add JSON snapshots in `tests/fixtures/` when platform tests need coordinator data as input
- **SHOULD** run the coverage-report command (`pytest --cov=custom_components.<domain>`) in the skill output and name the delta against the pre-augment state
- **MUST NOT** overwrite or delete existing test code

### Forbidden

- **MUST NOT** include generic `Exception` catches in the test helpers
- **MUST NOT** run blocking I/O in the tests — tests run under `asyncio_mode = auto`
- **MUST NOT** address real HA instances or real backends — mocks and fixtures only

## Acceptance Criteria

- [ ] The relevant test file exists and contains the tests per `kind`
- [ ] `tests/conftest.py` is extended with the necessary fixtures (when required)
- [ ] `tests/fixtures/` contains the necessary JSON snapshots
- [ ] `pytest tests/<test-file> -v` runs cleanly
- [ ] Skill output contains coverage delta against the pre-augment state
- [ ] Existing tests stay unchanged

## Open Questions

- **Coverage threshold**: Should skill output recommendations (for example "Silver reached at 80%") show, or does that stay a user task?
- **End-to-end tests**: When does a follow-up spec require E2E tests?
- **Snapshot tests** (for example with `syrupy`): Should they be supported as a pattern, or stay with classic asserts?
- **Test-data generation**: Should the skill generate Faker / Hypothesis-based test data, or stay with static fixtures?
