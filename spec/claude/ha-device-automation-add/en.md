# Skill: `ha-device-automation-add`

Status: draft

## Context

`ha/device-automations` defines the device-centric automation layer: an integration participates by providing the platform modules `device_trigger.py`, `device_condition.py`, and/or `device_action.py` — each with an `async_get_*` function returning a list of schema-conformant dictionaries per `device_id`, a module-constant `*_SCHEMA` (applied by the core, never manually), and the attach/check/call function (`async_attach_trigger`, `async_condition_from_config`, `async_call_action_from_config`). No skill augments this so far. Importantly: the quality-scale marker is **none**, and HA accepts **no new device automations** (it actively explores alternatives) — new implementations are a deliberate trade-off, not a standard scaffold. They mostly pay off for device-native events not bound to an entity (e.g. a button press on a remote).

This skill augments **one** device-automation kind (trigger, condition, or action) into an **existing** integration: the matching platform module, the `async_get_*` list, the module-constant `*_SCHEMA`, the attach/check/call function, optional capabilities, and the `device_automation:` strings — conformant to `ha/device-automations`. Before generating it checks whether an entity automation would not cover the need better.

## Scope

Augmenting exactly one device-automation kind per run (`trigger`, `condition`, or `action`) into an existing `custom_components/<domain>/` integration: the platform module (`device_trigger.py` / `device_condition.py` / `device_action.py`), the `async_get_*` function, the module-constant `*_SCHEMA`, the attach/check/call function, optional `async_get_*_capabilities`, and the `strings.json` `device_automation:` entries. The skill reads `ha/device-automations` and validates.

## Goals

- Pick the right kind (trigger/condition/action) from a described device interaction and augment it spec-conformantly
- Enforce the `async_get_*` contract: a list of dictionaries per `device_id` with the base-schema mandatory fields (`CONF_PLATFORM: "device"`, `CONF_DOMAIN`, `CONF_DEVICE_ID`, `CONF_TYPE`)
- Enforce static validation via the module-constant `*_SCHEMA` — never manual schema application
- Keep the modules thin adapters that build on event/state/service-action helpers — no duplicated business logic
- Save the user from unnecessary device automations: confirm the device-centric layer offers real value over entity automations, and point at HA's trade-off stance

## Non-Goals

- Entity automations (the state/event model without device indirection) — `ha/entity-architecture`
- Registered services with their own schema — `ha-service-definition-generator` / `ha/services` (device actions delegate internally but are not a service replacement)
- The frontend UI-editor logic — only the backend contract is defined here
- Greenfield scaffolding of an integration — `ha-integration-scaffold`
- Migration to HA's explored device-automation alternatives — a separate follow-up spec

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a device trigger / condition / action for …", "expose a remote button press as a device trigger"
  - "let the user pick this device in the automation editor"
  - "füge einen Device-Trigger / eine Device-Condition / Device-Action für … hinzu"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the device interaction (prose), from which the skill derives the kind and `CONF_TYPE`
- **MAY** capture: `kind` (`trigger`/`condition`/`action`), the `CONF_TYPE` values (and an optional `subtype`), and whether capability extra fields are needed

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** run the value check: if an entity automation (state/event trigger) covers the need, the skill **SHOULD** point that out; only a genuine device-centric need (a device-native event with no entity binding) justifies the device automation. The skill **MUST** point at HA's stance (no new device automations; a deliberate trade-off)
- **MUST** read the `ha/device-automations` spec
- **MUST NOT** overwrite an existing module/`CONF_TYPE`; on collision abort

### Generation rules (per kind, from `ha/device-automations`)

- **MUST** create the matching platform module: `device_trigger.py`, `device_condition.py`, or `device_action.py`
- **MUST** for triggers implement `async_get_triggers(hass, device_id)`; every dictionary carries `CONF_PLATFORM: "device"`, `CONF_DOMAIN`, `CONF_DEVICE_ID`, and at least `CONF_TYPE`; `TRIGGER_SCHEMA` extends `TRIGGER_BASE_SCHEMA` (module constant); `async_attach_trigger(hass, config, action, trigger_info)` calls the `action` on fire and returns a detach function
- **MUST** for conditions implement `async_get_conditions(hass, device_id)`; `CONDITION_SCHEMA` derives from `DEVICE_CONDITION_BASE_SCHEMA` (module constant); `async_condition_from_config(config, config_validation)` is a `@callback`, returns a `bool` checker function, and respects `config_validation`
- **MUST** for actions implement `async_get_actions(hass, device_id)`; `ACTION_SCHEMA` derives from `DEVICE_ACTION_BASE_SCHEMA` (module constant); `async_call_action_from_config(hass, config, variables, context)` executes the action
- **MUST NOT** apply the respective `*_SCHEMA` to the config manually — the core applies it when it is a module constant
- **MAY** implement `async_get_*_capabilities` to declare extra input fields (e.g. a `for` duration, a target value) for the UI editor, kept as narrow as possible; and mark an entry secondary via `"metadata": {"secondary": True}`
- **MAY** add `async_validate_*_config(hass, config)` when dynamic validation beyond the static schema is needed
- **MUST** maintain a human-readable string in `strings.json` under `device_automation:` for every used `CONF_TYPE` (and an optional subtype) — missing strings show the user a raw key
- **MUST** keep the modules thin adapters (build on event/state/service-action helpers, no duplicated business logic), name identifiers per `ha/naming-conventions`, and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: the matching module exists; the `async_get_*` function returns a list of dictionaries with the mandatory fields; `*_SCHEMA` is a module constant and is not applied manually; the attach/check/call function is implemented; every `CONF_TYPE` is resolved in `strings.json` under `device_automation:`
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/device-automations`, plus the changed file paths and the quality-scale marker (**none**) with the trade-off note

### Prohibitions

- **MUST NOT** augment more than one kind per run
- **MUST NOT** duplicate business logic that already exists as a service or in the entity platform
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill derives the kind (or asks) and runs the entity-vs-device value check incl. the HA trade-off note
- [ ] The matching module (`device_trigger.py`/`device_condition.py`/`device_action.py`) exists
- [ ] The `async_get_*` function returns a list of dictionaries per `device_id` with `CONF_PLATFORM`/`CONF_DOMAIN`/`CONF_DEVICE_ID`/`CONF_TYPE`
- [ ] `*_SCHEMA` is a module constant (extending the respective base schema) and is not applied manually
- [ ] The attach/check/call function is correctly implemented (detach function / `bool` checker / action execution)
- [ ] Every `CONF_TYPE` is resolved in `strings.json` under `device_automation:`
- [ ] Report names the file paths and the quality-scale marker **none** plus the trade-off note

## Open questions

- **New vs. existing**: HA accepts no new device automations. Should the skill generally discourage them and offer only a maintenance/legacy path once the HA alternative is named? Currently it augments with an explicit trade-off note.
- **Capabilities return shape**: which concrete form (`extra_fields` as a voluptuous schema) does the skill mandate? `ha/device-automations` leaves it open; the skill follows the doc pattern and asks when in doubt.
- **Subtype convention**: when a `subtype` in addition to `CONF_TYPE` (e.g. per button of a remote), and how structured in `strings.json`? Currently case-by-case.
