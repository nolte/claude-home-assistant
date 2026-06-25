# HA Integration: Device Automations

Status: draft

## Context

Device automations give users a device-centric layer on top of Home Assistant's core concepts: instead of dealing with states and events, they pick a device and then choose from a list of pre-defined triggers, conditions, and actions. Integrations hook into this system by exposing functions that generate these pre-defined triggers, conditions, and actions, and by providing functions that attach a trigger, check a condition, and execute an action. Device automations expose no extra functionality — they are a translation layer that builds on the event, state, and service-action helpers under the hood so users do not have to learn new concepts.

An integration participates in device automations by providing the three platform modules `device_trigger.py`, `device_condition.py`, and/or `device_action.py`. Triggers, conditions, and actions can come from the integration that provides the device (for example ZHA, deCONZ — typical for events not tied to an entity, such as a key press on a remote control) or from the entity integrations whose entities the device has (for example `light`, `switch` — such as "light turned on"). This spec lifts the convention from the HA developer docs into a generic obligation for every Custom Integration that skills in this plugin scaffold.

Quality scale marker: **none** (device automations are not a quality-scale criterion; HA is actively exploring alternatives and no longer accepts new device automations — existing ones keep working, so a new implementation is a deliberate trade-off, not a default scaffold).

## Goals

- Establish the three platform modules (`device_trigger.py`, `device_condition.py`, `device_action.py`) as the canonical structure for device automations
- Enforce the contract of the `async_get_*` functions: per `device_id`, a list of dictionaries that satisfy the respective base schema
- Use static validation via module-constant schemas (`TRIGGER_SCHEMA` / `CONDITION_SCHEMA` / `ACTION_SCHEMA`) applied by the core, instead of manual schema application
- Attach, check, and execute correctly via `async_attach_trigger`, `async_condition_from_config`, `async_call_action_from_config`
- Expose extra fields through the `async_get_*_capabilities` functions so the UI editor renders additional inputs
- Maintain human-readable strings for every trigger, condition, and action type in `strings.json` under `device_automation:`

## Non-Goals

- Entity automations (the state-/event-based default model without device indirection) — the device-centric layer is defined here, the underlying model in `ha/entity-architecture`
- Service actions in the classic sense (registered services with their own schema) — device actions delegate to service-action helpers internally but are not a replacement for `ha/services`
- The frontend's UI-editor logic — this spec defines only the integration's backend contract
- Migration of existing device automations or bridging to the alternatives HA is exploring — a separate follow-up spec once the alternative is concrete

## Requirements

### Device triggers

- **MUST** provide a `device_trigger.py` module when the integration offers device triggers
- **MUST** implement `async_get_triggers(hass, device_id)` and return a list of trigger dictionaries supported by the device or its associated entities
- **MUST** populate every trigger dictionary with the required fields of `TRIGGER_BASE_SCHEMA` (`CONF_PLATFORM: "device"`, `CONF_DOMAIN`, `CONF_DEVICE_ID`) plus the required fields of its own `TRIGGER_SCHEMA` (at least `CONF_TYPE`)
- **MUST** define `TRIGGER_SCHEMA` as a module constant that extends `TRIGGER_BASE_SCHEMA` from `device_automation/__init__.py`; the core applies this schema
- **MUST** implement `async_attach_trigger(hass, config, action, trigger_info)` that calls the `action` when the trigger fires (for example via `event_trigger.async_attach_trigger(..., platform_type="device")`) and returns a detach function
- **MUST NOT** apply the `TRIGGER_SCHEMA` to the config manually — the core applies it as long as it is defined as a module constant
- **MAY** implement `async_validate_trigger_config(hass, config)` when the trigger needs dynamic validation that the static `TRIGGER_SCHEMA` cannot provide

### Device conditions

- **MUST** provide a `device_condition.py` module when the integration offers device conditions
- **MUST** implement `async_get_conditions(hass, device_id)` and return a list of the conditions the device supports
- **MUST** derive `CONDITION_SCHEMA` from `homeassistant.helpers.config_validation.DEVICE_CONDITION_BASE_SCHEMA`
- **MUST** implement `async_condition_from_config(config, config_validation)` as a `@callback` that returns an async-friendly checker function which evaluates the condition and returns a `bool`
- **MUST** honour the `config_validation` parameter — the core uses it to apply config validation against `CONDITION_SCHEMA` conditionally
- **MAY** implement `async_validate_condition_config(hass, config)` when the condition needs dynamic validation that the static `CONDITION_SCHEMA` cannot provide

### Device actions

- **MUST** provide a `device_action.py` module when the integration offers device actions
- **MUST** implement `async_get_actions(hass, device_id)` and return a list of the actions the device supports
- **MUST** derive `ACTION_SCHEMA` from `homeassistant.helpers.config_validation.DEVICE_ACTION_BASE_SCHEMA` and define it as a module constant; the core applies it
- **MUST** implement `async_call_action_from_config(hass, config, variables, context)` that executes the passed-in action
- **MUST NOT** apply the `ACTION_SCHEMA` to the config manually — the core applies it as long as it is defined as a module constant
- **MAY** implement `async_validate_action_config(hass, config)` when the action needs dynamic validation that the static `ACTION_SCHEMA` cannot provide

### Capabilities (extra fields)

- **MAY** implement `async_get_trigger_capabilities`, `async_get_condition_capabilities`, or `async_get_action_capabilities` to declare additional input fields per entry (for example a `for` duration or a target value) that the UI editor renders
- **SHOULD** keep the capability fields as close as possible to the input set actually needed, so the UI editor is not overloaded with irrelevant fields
- **MAY** mark a device automation as secondary via `"metadata": {"secondary": True}` so that devices with many automations do not overwhelm the user; secondary entries are shown later or behind a "show more" option
- **MUST** accept, for an `entity_id`-referencing entry, that the core sets the `secondary` flag to `True` automatically when the referenced entity is hidden or has an entity category other than `None` (see `ha/device-registry` for the entity-to-device mapping)

### Translations

- **MUST** maintain a human-readable string for every trigger, condition, and action type in `strings.json` under the `device_automation:` key (for example `trigger_type`, `condition_type`, `action_type`)
- **MUST** cover every `CONF_TYPE` value (and any subtype) used in the `async_get_*` lists in `strings.json` — a missing string shows the user a raw key instead of a name
- **SHOULD** verify the translations locally with `python3 -m script.translations develop` and otherwise follow the translation workflow in `ha/translations`

### Delimitation from entity automations

- **MUST** offer device automations only when they provide real value to the user over the underlying state-/event model — they expose no new functionality but build on event, state, and service-action helpers
- **SHOULD** separate device actions clearly from registered services (`ha/services`): a device action delegates to a service-action helper internally but is not a standalone, externally callable service definition
- **MUST NOT** duplicate business logic in the device-automation modules that already exists as a service or in the entity platform — the modules stay thin adapters

## Acceptance Criteria

- [ ] For every offered automation kind, the matching module exists (`device_trigger.py`, `device_condition.py`, `device_action.py`)
- [ ] `async_get_triggers` / `async_get_conditions` / `async_get_actions` return a list of dictionaries per `device_id`
- [ ] Every trigger dictionary contains `CONF_PLATFORM: "device"`, `CONF_DOMAIN`, `CONF_DEVICE_ID`, and `CONF_TYPE`
- [ ] `TRIGGER_SCHEMA` extends `TRIGGER_BASE_SCHEMA`; `CONDITION_SCHEMA` / `ACTION_SCHEMA` derive from the respective `DEVICE_*_BASE_SCHEMA` — all as module constants
- [ ] No module applies its schema to the config manually
- [ ] `async_attach_trigger` calls the `action` on firing and returns a detach function
- [ ] `async_condition_from_config` returns a `bool` checker function and honours `config_validation`
- [ ] `async_call_action_from_config` executes the passed-in action
- [ ] Where extra fields are needed, the matching `async_get_*_capabilities` function is implemented
- [ ] `strings.json` contains an entry under `device_automation:` for every used type
- [ ] Quality scale marker for this pattern is set: **none**

## Open Questions

- **Alternatives migration**: HA is actively exploring alternatives to device automations and no longer accepts new ones. Should this spec generally discourage scaffolding new device automations and define only a maintenance/legacy path once the alternative is named?
- **Capabilities schema shape**: The docs describe the `async_get_*_capabilities` functions only conceptually. Which concrete return shape (`extra_fields` as a voluptuous schema?) should the spec fix as binding?
- **Subtype convention**: When does the spec require a `subtype` in addition to `CONF_TYPE` (for example per channel/button of a remote control), and how is it structured in `strings.json`?
- **Entity vs. device source**: Should the spec fix a heuristic for when a trigger/condition/action comes from the device integration versus the entity integration, or does that stay a case-by-case decision?
