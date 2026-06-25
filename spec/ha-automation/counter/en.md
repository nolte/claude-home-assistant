# HA Automation: Using Counter

Status: draft

## Context

The `counter` integration is a helper that exposes an **integer counter** as an entity. Its state is a whole number that is incremented, decremented, reset, or set directly via an action — which makes it the natural tool for counting **discrete events** (door openings, cups of coffee, triggered alarms) over time.

Its real HA classification is **Helper** — an auxiliary object created via UI or YAML, not a connectable device and not a measurement source. The state is the current counter value; the attributes (`initial`, `step`, `minimum`, `maximum`, `editable`) describe the counting behavior. It is driven by `counter.*` actions and fires its own events that automations can trigger on.

Verified source: [`/integrations/counter/`](https://www.home-assistant.io/integrations/counter/) (configuration variables, actions, triggers, condition, attributes). The trigger/condition/action base model comes from `ha-automation/automation`.

## When to Use

Use `counter` for **counting discrete events as an integer state** that is incremented, decremented, reset, or set via an action. A counter pays off as soon as an event count must be held persistently and observed. Typical use cases:

- **Event counting** — count door openings, cups of coffee, or triggered alarms up over time (`counter.increment` on each occurrence)
- **Threshold action** — act when an upper bound is reached by triggering on `counter.maximum_reached` (or `counter.minimum_reached`)
- **Periodically reset daily counter** — carry a value per day/shift and reset it to `initial` via `counter.reset`
- **Directly setting a value** — bring a known value to a concrete number via `counter.set_value` (e.g. from an external source)
- **Bounded step counter** — carry a bounded, step-wise changed value with `minimum`/`maximum` and `step` and check it as a gate via `counter.is_value`

A counter is the right tool as soon as a **discrete, integer count** must be counted and held. For measured/continuous values, arithmetic on sensor data, elapsing time, or fractions, another building block is right (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration of a counter (`name`, `initial`, `step`, `minimum`, `maximum`, `restore`, `icon`) as binding
- Fix the control contract over the actions `counter.increment`/`decrement`/`reset`/`set_value`
- Fix the read contract over the integer state and the attributes (`step`, `minimum`, `maximum`, `initial`)
- Anchor the event triggers (`counter.incremented`, `counter.decremented`, `counter.reset`, `counter.maximum_reached`, `counter.minimum_reached`) as the preferred reaction path
- Clearly delimit when a counter is **not** the right tool (vs. a sensor, vs. template/utility_meter)

## Non-Goals

- The trigger/condition/action base model of automations — `ha-automation/automation`
- The naming dimension (`name`/entity id, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Measurement/consumption counting from sensor data — `ha-automation/utility-meter`
- Derived/computed values from sensors — `ha-automation/template`
- Elapsing time / countdowns — `ha-automation/timer`

## Requirements

### Configuration

- **MUST** create a YAML counter under the `counter:` domain with a snake_case key (the alias that determines the entity id); mechanics of id/`name` assignment: `ha/naming-conventions`
- **SHOULD** set `initial` (start value, default `0`, 0 or positive integer) and `step` (step size, default `1`) explicitly when they differ from the defaults
- **MAY** set `minimum` and/or `maximum` to bound the value range — reaching them fires `counter.minimum_reached`/`counter.maximum_reached`
- **SHOULD** handle `restore` deliberately: the default is `true` (the last value is restored across a restart); set it to `false` when the counter should start at `initial` on every start
- **SHOULD** assign a `name` (friendly name) and optionally `icon` for the UI; the `name` stays English and ≤50 characters (`ha/naming-conventions`)

### Use in Automations & Templates

- **MUST** control the counter through the documented actions: `counter.increment` (increase by `step`), `counter.decrement` (decrease by `step`), `counter.reset` (reset to `initial`), `counter.set_value` (set to a concrete `value`)
- **SHOULD** trigger on the event triggers `counter.incremented`/`counter.decremented`/`counter.reset`/`counter.maximum_reached`/`counter.minimum_reached` instead of polling the state
- **MAY** read the counter state and the attributes `step`/`minimum`/`maximum`/`initial` in templates and conditions; the condition `counter.is_value` tests the value as a gate
- **MUST** treat the state as a number in numeric evaluation (e.g. via a `numeric_state` trigger or the `int` filter in a template), not compare it as a raw string

### Delimitation: When NOT to Use

- **SHOULD NOT** use a counter for **measured or continuous values** (temperature, power, level) — a counter only holds integer steps changed manually or by automation and has no measurement source; for measured/derived values a **sensor** (`ha-automation/template` for derived, a native sensor entity for measured) is the right construct
- **SHOULD NOT** misuse counter actions for **arithmetic on sensor data** (e.g. writing sums/differences of sensor values into a counter) — that loses the source and is error-prone; instead define a **template sensor** (`ha-automation/template`) or, for consumption/cycle counting over time, a **utility meter** (`ha-automation/utility-meter`) declaratively
- **MUST NOT** use a counter as a **time meter/countdown** (e.g. counting seconds up) — elapsing time is modeled by `ha-automation/timer`, not by an event counter
- **SHOULD NOT** represent non-integer quantities (fractions, decimals) in a counter — the counter is integer-only; for floating-point quantities an `input_number` or a template sensor is appropriate

## Acceptance Criteria

- [ ] Every counter is created under `counter:` with a snake_case alias; `name` stays English and ≤50 characters (`ha/naming-conventions` referenced)
- [ ] `initial`/`step` are set where they differ from the defaults; `minimum`/`maximum` bound the range where needed
- [ ] `restore` is handled deliberately (default `true`)
- [ ] Control happens exclusively through `counter.increment`/`decrement`/`reset`/`set_value`
- [ ] Reactions use the event triggers (`counter.incremented` etc.), not state polling
- [ ] Numeric evaluation treats the state as a number
- [ ] No counter is used for measured/continuous values, arithmetic on sensor data, time measurement, or fractions where a sensor, template/utility meter, or timer is the right tool
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
