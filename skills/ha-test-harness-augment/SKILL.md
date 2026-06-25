---
name: ha-test-harness-augment
description: Add tests for one secondary code path (platform, service, helpers, Lovelace cleanup) to an existing HA Custom Integration test suite, including fixtures and JSON snapshots, without disturbing existing tests. Activate on phrasings like "add tests for the sensor platform", "add tests for the `<service>` service", "add tests for the helpers module", "erweitere die Test-Suite um Plattform-Tests". Do not activate for E2E tests, test refactoring, or coverage-threshold tooling.
tags: [home-assistant, custom-integration, testing]
---

# HA Test Harness Augment

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-test-harness-augment/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-test-harness-augment/en.md).

## When this skill activates

Use this skill to augment the test suite of an existing HA Custom Integration with one secondary test class per call.

## When NOT to activate

- end-to-end tests against a real HA instance → separate spec (planned)
- refactoring existing tests → manual code edit
- coverage-threshold enforcement → CI configuration

## Hard rules

1. **Never overwrite or delete existing tests.** Augment is additive only.
2. **Never address real backends or real HA instances.** Mocks (`mock_api`) and fixtures (`load_fixture`) only.
3. **Never include generic `except Exception:`.** Catch only specific known errors.
4. **Always extend conftest.py rather than create parallel fixtures.** Reuse existing fixture names; add new ones only when none fits.
5. **Always run the coverage-report command after augment.** Skill output names the new coverage delta.
6. **Verify HA internals against the official docs.** Don't reproduce HA API signatures, lifecycle hooks, conventions, or schemas from memory — when uncertain, consult the official docs before generating or relying on it: Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant), architecture/blueprint/YAML docs [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root |
| `kind` | yes | — | `platform`, `service`, `helpers`, `lovelace_cleanup` |
| `platform_name` | when `kind=platform` | — | `sensor`, `binary_sensor`, … |
| `service_name` | when `kind=service` | — | service key from `services.yaml` |

## Pre-flight

1. `git -C <target_dir> rev-parse --is-inside-work-tree` and clean working tree
2. Source module exists (`<platform>.py`, `services.yaml` carries `service_name`, `helpers.py`, or `__init__.py` carries Lovelace registration)
3. Target test file does not collide with existing test code (will be created or appended)

## Workflow

### 1) Resolve

Read `domain` from `manifest.json`. Identify the source module to test against. Print the test list that will be added. Wait for user confirmation.

### 2) Apply edits

| `kind` | Files |
|---|---|
| `platform` | `tests/test_<platform>.py`; possibly `tests/conftest.py` (additional fixtures); possibly `tests/fixtures/<platform>.json` |
| `service` | `tests/test_services.py` (create or extend) |
| `helpers` | `tests/test_helpers.py` (create or extend) |
| `lovelace_cleanup` | `tests/test_lovelace_cleanup.py` (create) |

### 3) Verify

```bash
ruff check tests/
pytest tests/<test-file> -v
pytest --cov=custom_components.<domain> --cov-report=term-missing
```

### 4) Report

- list of tests added
- coverage delta (lines covered before vs. after)
- explicit note when Silver test-coverage tier is reached for the augmented module

## Boundaries

- E2E tests against real HA → separate spec planned
- Test refactoring → manual code edit
- Coverage threshold enforcement → CI configuration
- Snapshot testing (`syrupy`) → not in scope
