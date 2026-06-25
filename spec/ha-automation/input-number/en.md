# HA Automation: Using input_number

Status: draft

## Context

`input_number` is a **helper integration** (HA category *Helper*): it provides a **user-settable numeric value** that appears as a slider or input box in the frontend. The state is the current number; it is a setpoint (e.g. target temperature, brightness threshold, delay duration) that a human chooses and automations read — not a measurement.

At the configuration level, an `input_number` is created through the UI (Settings → Devices & Services → Helpers) or as YAML under the top-level key `input_number`. The keys `min` and `max` are required; `name`, `initial`, `step`, `icon`, `unit_of_measurement`, and `mode` (values `box` or `slider`, default `slider`) are optional. The integration has a real integration card; its real classification is **Helper**, not sensor.

Verified source: [`/integrations/input_number/`](https://www.home-assistant.io/integrations/input_number/) (config keys `name`/`min`/`max`/`initial`/`step`/`icon`/`unit_of_measurement`/`mode`; `mode` values `box`/`slider`; services `set_value`/`increment`/`decrement`/`reload`; attributes `min`/`max`/`step`/`mode`/`unit_of_measurement`; restore behavior). Naming mechanics referenced via `ha/naming-conventions`.

## When to Use

Use `input_number` for a **user-settable numeric value** with fixed `min`/`max` bounds that a human chooses and automations read — not a measured or derived quantity. Typical use cases:

- **Settable setpoint** — a resident-chosen target temperature an automation passes to `climate`/`light` as a setpoint
- **Adjustable threshold** — a brightness or threshold bound that fires an automation via `numeric_state` (`above`/`below`)
- **Delay/duration parameter** — a settable value fed into an automation as a `delay` or action parameter
- **Programmatic setting/stepping** — change the value via `input_number.set_value` or stepwise via `increment`/`decrement` (by exactly `step`)
- **Dashboard slider** — make it operable as a slider (`mode: slider`) or input box (`mode: box`) via an `entities` row or an `input_number` card

An `input_number` is the right tool as soon as a **user-settable, bounded numeric value** is needed. For a measured/derived value or a selection from fixed options, another building block applies (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration of an `input_number` (mandatory `min`/`max`, `step`, `mode`, restore semantics) as binding
- Fix the correct use as a user-settable setpoint
- Define the exposed services (`set_value`/`increment`/`decrement`) and how state and attributes are read from trigger/condition/template
- Clearly delimit when an `input_number` is **not** the right tool and which building block applies instead

## Non-Goals

- The trigger/condition/action model of automation itself — `ha-automation/automation`
- Template syntax in general — `/docs/configuration/templating/`, only the read patterns here
- The naming dimension (`name`, snake_case `object_id`, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Measured or derived numeric values — `sensor`/template/derivative/statistics sensor (`ha-automation/template`, `ha-automation/derivative`, `ha-automation/statistics`)

## Requirements

### Configuration

- **MUST** structure an `input_number` through the top-level key `input_number` and set the **required** keys `min` and `max` per entry; `name`, `initial`, `step`, `icon`, `unit_of_measurement`, `mode` are optional
- **MUST** keep the `object_id` a snake_case slug and the `name` English and ≤50 characters (mechanics: `ha/naming-conventions`)
- **SHOULD** choose `step` to fit the magnitude (default `1`, minimum `0.001` per the docs) and set `unit_of_measurement` when the value represents a physical quantity, so the frontend and templates know the unit
- **SHOULD** choose `mode` deliberately — `slider` (default) for convenient coarse setting, `box` for precise direct entry
- **SHOULD** treat the `initial` key deliberately: if `initial` is set, HA starts with that value; otherwise the state before the stop is restored (per the docs)
- **SHOULD NOT** set `initial` when the user's last chosen value should survive a restart — a hard-set `initial` overrides the restore behavior on every start

### Use in Automations & Templates

- **MUST** read the value numerically: in conditions/triggers via `numeric_state` (with `above`/`below`), in templates via `states('input_number.x') | float` — the `states(...)` return value is a string and must be cast to a number
- **MAY** read the documented attributes `min`, `max`, `step`, `mode`, and `unit_of_measurement` via `state_attr('input_number.x', 'min')` etc., e.g. to mirror limits in the logic
- **MUST** use the documented service `input_number.set_value` (with `value`) to set it programmatically, and `input_number.increment`/`input_number.decrement` to change it stepwise (shift by exactly `step`); `input_number.reload` reloads the YAML helpers
- **MAY** use the value as a parameter in actions (e.g. `delay`, `target` data, setpoint for `climate`/`light`) — as a user-settable lever
- **MAY** embed the element on a dashboard via an `entities` row or an `input_number` card

### Delimitation: When NOT to Use

- **MUST NOT** use an `input_number` as a **measurement sensor** (e.g. to "display" a temperature or a consumption) — it is user-editable and has no measurement source; measured values belong in a **`sensor`**, derived values in a **template sensor** (`ha-automation/template`)
- **SHOULD NOT** use an `input_number` to "store" a **computed/derived** numeric value that an automation keeps in sync via `set_value` so it looks "like a sensor" — this is fragile (race conditions, no history, drift after restart) and loses the source; instead define a **template/derivative/statistics sensor** (`ha-automation/template`, `ha-automation/derivative`, `ha-automation/statistics`) that derives the value declaratively
- **SHOULD NOT** repurpose an `input_number` as a selection from a few fixed options (e.g. 1/2/3 for three modes) — an **`input_select`** is the right helper, because it enforces named options instead of a numeric range
- **SHOULD NOT** use an `input_number` without meaningful `min`/`max` bounds to store "arbitrary" numbers — the mandatory bounds are part of the semantics; an unbounded computed value belongs in a template sensor, not in a settable slider

## Acceptance Criteria

- [ ] Every helper is created through the top-level key `input_number` with required `min`/`max`, a snake_case `object_id`, and an English `name` ≤50 characters
- [ ] `step`, `mode`, and `unit_of_measurement` are set deliberately; `initial` only when a fixed start value is wanted
- [ ] The value is read numerically (`numeric_state` or `| float`); attributes `min`/`max`/`step`/`mode`/`unit_of_measurement` are read via `state_attr(...)`
- [ ] Setting uses `input_number.set_value`/`increment`/`decrement` with `target.entity_id`
- [ ] No `input_number` carries a measured or derived value (use `sensor`/template/derivative/statistics sensor)
- [ ] No `input_number` replaces an `input_select` option selection
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
