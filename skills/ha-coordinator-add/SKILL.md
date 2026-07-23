---
name: ha-coordinator-add
description: Appends a new DataUpdateCoordinator to an existing Home Assistant Custom Integration — separate role, separate update interval, full integration with RuntimeData mapping, options-flow entry, translations, and tests. Activate on phrasings like "add a new coordinator for alerts", "split the existing coordinator", "add a faster polling coordinator", "füge einen Coordinator für X hinzu". Do not activate for greenfield scaffolding (use ha-integration-scaffold) or coordinator removal; a push-style coordinator variant (async_set_updated_data) is supported for local_push / cloud_push integrations.
tags: [home-assistant, custom-integration, coordinator]
phase: design
summary: "Appends a new DataUpdateCoordinator with its own role and update interval to an existing integration — RuntimeData mapping, options-flow entry, translations, and tests."
summary_de: "Fügt einer bestehenden Integration einen neuen DataUpdateCoordinator mit eigener Rolle und eigenem Update-Intervall hinzu — RuntimeData-Mapping, Options-Flow-Eintrag, Übersetzungen und Tests."
use_when:
  - "you want to add a coordinator with a faster or slower update interval"
  - "you want to split polling of an integration's data into a new coordinator"
dont_use_when:
  - situation: "You are scaffolding a brand-new integration"
    alternative: ha-integration-scaffold
  - situation: "You want to add the entity platforms backed by the coordinator"
    alternative: ha-entity-platform-add
see_also:
  - ha-integration-scaffold
  - ha-entity-platform-add
  - ha-entity-description-map
---

# HA Coordinator Add

Spec: `spec/claude/ha-coordinator-add/en.md` (EN canonical) / `spec/claude/ha-coordinator-add/de.md` (DE translation).

## Why this is a skill, not an agent

- **Quick, targeted change in the current context (decisive):** appending one coordinator touches a handful of known files in the integration the conversation is already working on; per the `skill-vs-agent` change-scope dimension that routes to the main thread.
- **Mid-flow approval:** role, update interval, and RuntimeData wiring are confirmed with the operator before writing.
- **Counter-dimension considered:** the addition has a well-defined input/output shape (agent bias), but the spin-up and report boundary of a subagent buys nothing for a change this local — latency and interactivity win.

## When this skill activates

Use this skill when the user wants to add a new `DataUpdateCoordinator` to an existing integration — typically because a subset of data needs a faster (alerts) or slower (master data) update interval than the existing coordinator.

## When NOT to activate

- greenfield scaffold → `ha-integration-scaffold`
- removing or merging coordinators → manual code edit
- bespoke push transport wiring (webhook server, MQTT broker setup) → out of scope; the push-style *coordinator* variant itself is supported (see Hard rules)

## Hard rules

1. **Never modify the existing coordinator.** Add only; never touch the existing class signature, name, or update interval.
2. **Never rewire platform modules.** The new coordinator key lands in `RuntimeData.coordinators`; which platforms read from it is a follow-up user decision.
3. **Never set min cap below 30 s without warning.** Sub-30s polling risks rate-limiting / DDoS. Warn the user explicitly when they request it.
4. **Always update the options flow.** A new coordinator without a configurable interval defeats the user's ability to tune polling. The new `CONF_POLL_<ROLE>` lands in `OPTIONS_SCHEMA` plus `strings.json` plus translations.
5. **Always ship tests.** Three tests for the new coordinator (auth error, connection error, happy path) are mandatory.
6. **Store the new coordinator on a typed `runtime_data`.** The coordinator lands in the `RuntimeData.coordinators` mapping on a **typed** config entry (a typed alias such as `type <Domain>ConfigEntry = ConfigEntry[RuntimeData]`, used throughout); re-verify the `RuntimeData` dataclass field type when the mapping key is added so the typed entry stays sound (`ha/runtime-data-pattern`).
7. **Surface `PARALLEL_UPDATES` for the backed platforms.** This skill adds the coordinator, not the entity-platform modules — but every platform that reads the new coordinator needs a module-level `PARALLEL_UPDATES` (Silver `parallel-updates` rule). Surface this in the report and point the user at `ha-entity-platform-add` / `ha-entity-description-map` to emit it.
8. **Push-style variant for `local_push` / `cloud_push`.** For a push iot_class a poll-based coordinator is the wrong shape — a push-style coordinator (`async_set_updated_data`, no `update_interval`) MAY be produced instead; the bespoke transport wiring (webhook server, MQTT broker) stays out of scope.
9. **Verify HA internals against the official docs.** Don't reproduce HA API signatures, lifecycle hooks, conventions, or schemas from memory — when uncertain, consult the official docs before generating or relying on it: Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant), architecture/blueprint/YAML docs [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see `spec/ha/upstream-docs-verification/en.md`).

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
- reminder: each platform bound to the new coordinator needs a module-level `PARALLEL_UPDATES` — point at `ha-entity-platform-add` / `ha-entity-description-map`

## Boundaries

- Greenfield scaffold → `ha-integration-scaffold`
- Config flow extension → `ha-config-flow-augment`
- Test coverage extension → `ha-test-harness-augment`
- Push-style coordinator variant (`async_set_updated_data`) → supported as a MAY for `local_push` / `cloud_push`; bespoke transport wiring stays out of scope
