---
name: ha-device-automation-add
description: Augment an existing Home Assistant Custom Integration with one device-automation kind — a device trigger, condition, or action — conforming to spec/ha/device-automations. Creates the matching platform module (device_trigger.py / device_condition.py / device_action.py) with its async_get_* list (CONF_PLATFORM/CONF_DOMAIN/CONF_DEVICE_ID/CONF_TYPE fields), a module-constant *_SCHEMA the core applies (never manually), the attach/check/call function, optional capabilities, and the device_automation strings.json entries. Runs an entity-vs-device value check and flags HA's stance that no new device automations are accepted. Activate on "add a device trigger for…", "expose a remote button press as a device trigger", "füge eine Device-Action hinzu". Do not activate for entity automations (ha/entity-architecture), registered services (ha-service-definition-generator), greenfield scaffolding (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, device-automation]
---

# HA Device Automation Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-device-automation-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-device-automation-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes a device interaction and reads back the platform module, the schema, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-repairs-add`).
- **Mid-flow interactivity** — the kind decision and the entity-vs-device value check (with HA's "no new device automations" caveat) are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — one platform module plus its schema and strings fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the kind decision and the trade-off advice belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** device-automation kind — a device trigger, condition, or action — to an existing integration, typically for a device-native event with no entity binding (e.g. a remote button press).

## When NOT to activate

- entity automations (state/event model without device indirection) → `ha/entity-architecture`
- a registered service with its own schema → `ha-service-definition-generator` / `ha/services`
- greenfield integration scaffolding → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One kind, one run.** No multi-kind batches.
2. **Read [`ha/device-automations`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/device-automations/de.md) first.** Do not generate from memory.
3. **Deliberate trade-off.** The quality-scale marker is **none** and HA accepts no new device automations. Run an entity-vs-device value check first: if a state/event entity automation covers the need, point that out; only a genuine device-native event justifies this. State the caveat in the report.
4. **`async_get_*` contract.** `async_get_triggers`/`async_get_conditions`/`async_get_actions(hass, device_id)` returns a list of dicts; every entry carries `CONF_PLATFORM` (`"device"`), `CONF_DOMAIN`, `CONF_DEVICE_ID`, and at least `CONF_TYPE`.
5. **Module-constant schema, core-applied.** Define `TRIGGER_SCHEMA` (extends `TRIGGER_BASE_SCHEMA`) / `CONDITION_SCHEMA` (from `DEVICE_CONDITION_BASE_SCHEMA`) / `ACTION_SCHEMA` (from `DEVICE_ACTION_BASE_SCHEMA`) as a module constant — **never** apply it to the config manually; the core does.
6. **Attach / check / call.** `async_attach_trigger(...)` calls the `action` on fire and returns a detach function; `async_condition_from_config(...)` is a `@callback` returning a `bool` checker and respecting `config_validation`; `async_call_action_from_config(...)` executes the action.
7. **Thin adapters.** Build on event/state/service-action helpers; never duplicate business logic that already lives in a service or the entity platform.
8. **Translate every type.** Each used `CONF_TYPE` (and optional subtype) has a string in `strings.json` under `device_automation:` (see [`ha/translations`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/translations/de.md)); a missing string shows the user a raw key.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `interaction` | yes | — | the device interaction the automation expresses, in prose |
| `kind` | no | inferred + confirmed | `trigger` / `condition` / `action` |
| `conf_type` / `subtype` | no | derived | the `CONF_TYPE` value(s) |
| capabilities | no | asked when needed | extra UI-editor input fields |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Resolve `kind` (infer + confirm). Run the entity-vs-device value check; if an entity automation suffices, surface it and state HA's "no new device automations" caveat before proceeding.
3. Read `ha/device-automations`.
4. The module / `CONF_TYPE` is not already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the resolved `kind`, the `CONF_TYPE`(s), whether capabilities are needed, and the trade-off caveat in one paragraph. Wait for confirmation.

### 2) Generate

| Kind | Module | Functions | Schema base |
|---|---|---|---|
| trigger | `device_trigger.py` | `async_get_triggers` + `async_attach_trigger` | `TRIGGER_BASE_SCHEMA` |
| condition | `device_condition.py` | `async_get_conditions` + `async_condition_from_config` (`@callback`) | `DEVICE_CONDITION_BASE_SCHEMA` |
| action | `device_action.py` | `async_get_actions` + `async_call_action_from_config` | `DEVICE_ACTION_BASE_SCHEMA` |

Add `async_get_*_capabilities` only when extra fields are needed; add the `device_automation:` `strings.json` entries for every `CONF_TYPE`.

### 3) Validate and report

Validate offline (module present; `async_get_*` returns dicts with the mandatory fields; `*_SCHEMA` is a module constant, not applied manually; the attach/check/call function is implemented; every `CONF_TYPE` resolved in `strings.json`). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/device-automations` acceptance criteria, plus the changed file paths and the quality-scale marker (**none**) with the trade-off note.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Entity automations → `ha/entity-architecture`
- Registered services → `ha-service-definition-generator`
- Greenfield scaffold → `ha-integration-scaffold`
- Deploy to live HA → out of scope
