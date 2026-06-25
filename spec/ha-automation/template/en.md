# HA Automation: Using the Template Integration

Status: draft

## Context

The `template` integration creates **template entities**: entities whose state, availability, attributes, and (for actuator domains) actions are derived from Jinja2 templates over other entities. It is the declarative tool for computing a new, clean value out of existing states — such as a combined sensor, a derived `binary_sensor`, or a virtual switch that bundles several devices.

Its real HA classification is **Helper** plus the respective entity domains — not "Automation". In the integration catalog `template` appears as a helper; each generated entity lands in its target domain (`sensor.*`, `binary_sensor.*`, `switch.*`, etc.). The integration has two fundamentally different operating modes: **state-based** (re-renders automatically whenever a referenced entity changes) and **trigger-based** (re-renders only when a declared trigger fires). This distinction is the heart of high-quality template use and the core of the delimitation below.

This spec turns the official usage docs into a binding convention for plugin-generated template entities. It defers to `ha-automation/automation` for the automation base model (trigger/condition/action) and to `ha/naming-conventions` for the naming mechanics.

Verified sources: `/integrations/template/` (modern `template:` block, state-based vs. trigger-based, domain catalog, per-entity keys) and `/docs/configuration/templating/` and `/template-functions/` (`has_value`, `is_number`, `float`/`int` with default, `default` filter, `states`/`is_state`/`state_attr`).

## When to Use

Use the `template` integration whenever a **new value, state, or entity should be derived declaratively** from existing entities — as a single source of truth that updates itself, instead of writing a value into a helper via an automation. Typical use cases:

- **Derived sensor** — compute a clean `sensor`/`binary_sensor` from several source entities (combination, formatting, threshold logic) that re-renders on its own whenever a source changes (state-based)
- **Virtual actuator** — build a `switch`/`light`/`cover`/`fan` with a `state` template plus action keys (`turn_on`/`turn_off`, `set_value`, `select_option`) that bundles several devices under one entity
- **Frozen snapshot / event value** — advance a value only at a specific moment (on an `event`, at a time, on `homeassistant` start) via a trigger-based entity with `triggers`/`conditions`/`actions`
- **Avoiding a re-render storm** — with many or frequently changing dependencies, choose a trigger-based entity that recomputes only at the desired moment instead of on every source change
- **Robust availability** — report `unavailable` deliberately via an `availability` template and the guard idioms (`has_value`, `is_number`, `float(default)`) instead of delivering a wrong value from `unavailable`/`unknown` sources

A template entity is the right tool as soon as a value is **computed from other states**. For time derivatives or statistics use the purpose-built integrations, for side effects use an automation (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the **modern `template:` config block** as the standard and exclude the legacy `platform: template` form
- Enforce **state-based vs. trigger-based** as a deliberate design decision instead of blindly adopting default behavior
- Make the documented domain catalog (sensor, binary_sensor, number, select, switch, light, cover, fan, image, button, weather, alarm_control_panel, vacuum, etc.) the binding set of valid targets
- Set the per-entity required and short-form keys (`state`, `availability`, `unique_id`, `device_class`, `state_class`, `attributes`, `name`) consistently
- Anchor the **unavailable/unknown guard idioms** (`has_value`, `is_number`, `float(default)`/`int(default)`, `availability`) as checkable rules
- Clearly delimit when a template entity is **not** the right tool and which building block applies instead

## Non-Goals

- The full trigger/condition/action model for trigger-based entities — detailed contract in `ha-automation/automation` (trigger catalog) and `ha-automation/script` (action syntax); only the template-specific keys here
- General Jinja2/template syntax and the full function catalog — `/docs/configuration/templating/` and `/template-functions/`; only the guard-relevant functions here
- Purpose-built math (time derivative, statistics, min/max) — `ha-automation/derivative`, `ha-automation/statistics`, `ha-automation/min-max`
- The naming dimension (`name`, `unique_id`, snake_case, English, ≤50 chars, ASCII) — `ha/naming-conventions`, only referenced here
- Quality Scale — not applicable (usage spec)

## Requirements

### Configuration

- **MUST** define template entities in the **modern `template:` block** — a list of configuration blocks, each holding one domain (`sensor:`, `binary_sensor:`, `switch:`, …) with a list of entities:

  ```yaml
  template:
    - sensor:
        - name: "Example"
          state: "{{ ... }}"
  ```

- **MUST NOT** use the legacy `platform: template` form under the respective domain; it is superseded and does not mix with the modern block

- **MUST** choose as the target domain only one of the documented template-entity domains: `alarm_control_panel`, `binary_sensor`, `button`, `cover`, `device_tracker`, `event`, `fan`, `image`, `light`, `lock`, `number`, `select`, `sensor`, `switch`, `update`, `vacuum`, `weather`

- **MUST** give every entity a stable `unique_id` so it is UI-customizable (rename, area, customize); without `unique_id` the entity cannot be managed through the UI. `name` and `unique_id` follow the mechanics in `ha/naming-conventions`

- **MUST** set a `state` template for most domains (the required key for the entity state); for actuator domains additionally the domain-specific action keys (e.g. `turn_on`/`turn_off` for `switch`/`light`, `set_value` for `number`, `select_option` for `select`, `open_cover`/`close_cover`/`set_cover_position` for `cover`)

- **SHOULD** set an `availability` template returning `true`/`false` whenever the state is derived from unreliable sources — so the entity becomes deliberately `unavailable` instead of delivering a wrong value

- **SHOULD** set the appropriate classification keys on sensors: `device_class`, `unit_of_measurement` and — for long-term statistics — `state_class` (`measurement`, `total`, `total_increasing`); on `binary_sensor` `device_class` plus optional `delay_on`/`delay_off`/`auto_off`

- **MAY** add dynamic presentation via `icon` and `picture` templates and extra `attributes` (a map of attribute templates)

### State-Based vs. Trigger-Based

- **MUST** decide deliberately between **state-based** and **trigger-based** and justify the choice when it is not obvious:
  - *state-based*: no `triggers`; the entity **re-renders automatically** whenever an entity referenced in the template changes
  - *trigger-based*: with `triggers`; the entity **re-renders only when a trigger fires** — per the docs: "Trigger-based entities do not automatically update when states referenced in the templates change."

- **MUST** choose state-based when the target value is a pure, cheap function of the current states (derivation, combination, formatting) — this is the normal case

- **MUST** choose trigger-based when **event semantics** are needed: the value should advance only at a specific moment (e.g. on an `event`, at a time, on `homeassistant` start), a snapshot should be frozen, or a **re-render storm** from many changing dependencies should be avoided

- **MAY** use, in trigger-based entities, the keys `triggers` (trigger catalog as in `ha-automation/automation`), `conditions` (gate after the trigger), `actions` (script syntax whose result variables are visible to the template), and `variables`/`trigger_variables` (key-value pairs available in the template)

- **MUST** account for the fact that only **trigger-based** sensors/binary sensors **restore** their state across a restart; state-based entities are recomputed after start

### Use in Automations & Templates

- **MUST** reference the generated entity like any native entity: as a trigger (`state`/`numeric_state` on `sensor.*`/`binary_sensor.*`), as a condition, as an action target (`switch.*`, `light.*`, `number.*`, …), and in dashboards — the domain determines the available triggers/services

- **SHOULD** guard against `unavailable`/`unknown` of the source entities in every value-producing template instead of forwarding a raw `states('…')` value directly:
  - `has_value('sensor.x')` tests whether an entity exists and has a valid state (not `unavailable`/`unknown`)
  - `is_number(value)` tests whether a value can be converted to a finite number before computing
  - `states('sensor.x') | float(0)` / `| int(0)` yields a defined default when conversion fails; the `default` filter covers undefined/none

- **SHOULD** phrase the `availability` template so the entity reports `unavailable` when its data basis is missing (e.g. `availability: "{{ has_value('sensor.source') }}"`), so downstream automations do not react to a guessed default

- **MAY** use, in the templates, the `this` variable (the entity's own state object, e.g. for self-referencing attributes) and — in trigger-based entities — `trigger` and `trigger_variables`

### Delimitation: When NOT to Use

- **SHOULD NOT** use an automation that writes a derived value into an `input_number`/`input_text` where a **state-based template entity** delivers the same value declaratively — the template entity is the declarative single source of truth, re-renders on its own, is not accidentally user-editable, and has no write race conditions (background: `ha-automation/automation`, `ha-automation/input-number`)

- **SHOULD NOT** build a **state-based** template entity with heavy or slow logic that depends on many or frequently changing entities — it re-renders on **every** dependency change and creates a re-render storm; instead use a **trigger-based** entity that recomputes only at the desired moment

- **MUST NOT** choose a **trigger-based** entity where pure derivation from current states suffices — it does **not** update automatically on source state changes and then delivers stale values; for ongoing derivation, state-based is correct

- **SHOULD NOT** rebuild time derivatives or statistics in a template (rate of change, moving average, min/max over time) — the purpose-built integrations `ha-automation/derivative`, `ha-automation/statistics`, and `ha-automation/min-max` handle history, time windows, and resampling correctly

- **SHOULD NOT** trigger side effects (service calls, notifications, writing to other entities) from the `state` template of a state-based entity — state templates must stay side-effect-free; side effects belong in the `actions` block of a **trigger-based** entity or in an **automation** (`ha-automation/automation`)

- **SHOULD NOT** forward a raw `states('sensor.x')` value into a computation, condition, or `state` without a `has_value`/`is_number`/`float(default)` guard — at startup or with `unavailable`/`unknown` sources this yields faulty or empty states; the guard idioms are mandatory, not stylistic

## Acceptance Criteria

- [ ] Every template entity is defined in the modern `template:` block; no `platform: template` legacy form
- [ ] The target domain comes from the documented domain catalog
- [ ] Every entity carries a stable `unique_id`; `name`/`unique_id` follow `ha/naming-conventions`
- [ ] state-based vs. trigger-based is chosen deliberately and justified when not obvious
- [ ] Actuator domains define their action keys (e.g. `turn_on`/`turn_off`, `set_value`, `select_option`)
- [ ] Sensors set `device_class`, `unit_of_measurement`, and `state_class` where meaningful
- [ ] Value-producing templates are guarded against `unavailable`/`unknown` (`has_value` / `is_number` / `float(default)` / `int(default)` / `availability`)
- [ ] No heavy/frequently re-rendering logic in a state-based entity; such cases are trigger-based
- [ ] No trigger-based entity where ongoing state-based derivation is needed
- [ ] Time/statistical computations use the purpose-built integrations, not a template
- [ ] No side effects from a state template; side effects run in the trigger-based `actions` block or in an automation
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
