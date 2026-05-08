---
name: ha-coordinator-add
description: Append a new DataUpdateCoordinator to an existing Home Assistant Custom Integration — separate role, separate update interval, full integration with RuntimeData mapping, options-flow entry, translations, and tests. Activate on phrasings like "add a new coordinator for alerts", "split the existing coordinator", "add a faster polling coordinator", "füge einen Coordinator für X hinzu". Do not activate for greenfield scaffolding (use ha-integration-scaffold), coordinator removal, or push-based coordinators.
tags: [home-assistant, custom-integration, coordinator]
---

# HA Coordinator Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-coordinator-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-coordinator-add/en.md).

## When this skill activates

Use this skill when the user wants to add a new `DataUpdateCoordinator` to an existing integration — typically because a subset of data needs a faster (alerts) or slower (master data) update interval than the existing coordinator.

## When NOT to activate

- greenfield scaffold → `ha-integration-scaffold`
- removing or merging coordinators → manual code edit
- push-based coordinator (webhook / MQTT / WebSocket) → separate spec planned

## Hard rules

1. **Never modify the existing coordinator.** Add only; never touch the existing class signature, name, or update interval.
2. **Never rewire platform modules.** The new coordinator key lands in `RuntimeData.coordinators`; which platforms read from it is a follow-up user decision.
3. **Never set min cap below 30 s without warning.** Sub-30s polling risks rate-limiting / DDoS. Warn the user explicitly when they request it.
4. **Always update the options flow.** A new coordinator without a configurable interval defeats the user's ability to tune polling. The new `CONF_POLL_<ROLE>` lands in `OPTIONS_SCHEMA` plus `strings.json` plus translations.
5. **Always ship tests.** Three tests for the new coordinator (auth error, connection error, happy path) are mandatory.

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root of the integration |
| `role` | yes | — | lowercase ASCII slug (`alerts`, `tenants`, …) |
| `default_interval` | yes | — | seconds |
| `min_interval` | yes | — | seconds; warn if < 30 |
| `update_method` | yes | — | API method name (e.g. `async_get_alerts`) |
| `setup_method` | no | none | optional `_async_setup` master-data loader |
| `data_type` | no | `list[dict[str, Any]]` | generic for `DataUpdateCoordinator[<T>]` |

## Pre-flight

1. `git -C <target_dir> rev-parse --is-inside-work-tree` and clean working tree
2. `<target_dir>/custom_components/<domain>/coordinator.py` exists; read `domain` from `manifest.json`
3. Class `<Domain><Role>Coordinator` does not yet exist; mapping key `role` not in `RuntimeData.coordinators`
4. API method `update_method` exists in `api.py` (else: surface as a user todo, do not auto-add)

## Workflow

### 1) Resolve and confirm

Print one paragraph stating: role, intervals (default + min), API method, generic type, list of files to be touched. Wait for user confirmation.

### 2) Apply edits

Touch these files in order:

- `coordinator.py` — append the new class
- `const.py` — append `CONF_POLL_<ROLE>`, `DEFAULT_POLL_<ROLE>`, `MIN_POLL_<ROLE>`
- `__init__.py` — instantiate, first-refresh, extend mapping
- `config_flow.py` — extend `OPTIONS_SCHEMA`
- `strings.json` and every `translations/<lang>.json` — `options.step.init.data.poll_interval_<role>`
- `tests/test_coordinator.py` — three new tests

### 3) Verify

```bash
ruff check custom_components/<domain>/
pytest tests/test_coordinator.py -v
```

Both must run cleanly. On failure, surface the tool output and abort.

### 4) Report

- files touched (counted)
- min cap warning (if `min_interval` < 30 s)
- next-step hint: which platforms could benefit from binding to the new coordinator (reading the platform code is the user's job)

## Boundaries

- Greenfield scaffold → `ha-integration-scaffold`
- Config flow extension → `ha-config-flow-augment`
- Test coverage extension → `ha-test-harness-augment` (planned)
- Push-based coordinator → separate spec planned
