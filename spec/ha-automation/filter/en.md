# HA Automation: Using the Filter Sensor

Status: draft

## Context

The `filter` integration is a **sensor helper** that takes a noisy numeric source sensor and produces a new, smoothed sensor. It attaches one or more filter stages to the stream of an existing `sensor` entity and emits the processed value as its own entity. Typical use case: denoise a jittery temperature, power, or brightness sensor before it triggers automations, or remove outlier spikes from a radio sensor.

Unlike the rule engine, the Filter integration has an **integration card** in the catalog. Its real classification per the docs is **Helper / Sensor / Utility** — not a connectable device, but a declarative sensor transformation. It is configured as a `sensor` platform in YAML; the UI path supports only **one** filter stage, multi-stage chains require YAML.

Filters are **stateful** and introduce **lag**: each stage looks at a window of past states, so the smoothed signal trails the raw signal. The window size is therefore a deliberate trade-off between smoothing and latency.

This spec turns the official integration docs into a binding convention for plugin-generated filter sensors. It refers to `ha-automation/automation` (consuming the generated `sensor` entity) and to `ha-automation/derivative` and `ha-automation/statistics` as delimitation alternatives.

Verified source: [`/integrations/filter/`](https://www.home-assistant.io/integrations/filter/).

## When to Use

Use `filter` when a **noisy numeric source sensor should be smoothed** and emitted as a new, calmer entity before it triggers automations. Typical use cases:

- **Denoise a jittery sensor** — smooth temperature, power, or brightness via `lowpass` or `time_simple_moving_average`
- **Remove outlier spikes** — discard short misreadings of a radio/battery sensor via an `outlier` stage (`radius`)
- **Clamp implausible values** — cut off values outside fixed bounds via `range` (`lower_bound`/`upper_bound`)
- **Reduce data volume** — pass only the first value per window via `throttle`/`time_throttle` (debouncing, not smoothing)
- **Multi-stage processing chain** — chain several stages in the `filters` list (e.g. `outlier` then `lowpass`), each stage's output being the next stage's input

A filter sensor is the right tool as soon as the **value itself should be smoothed/cleaned**. For rate of change, statistical characteristics, or categorical states it is not (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the anatomy of a filter sensor (`entity_id`, `filters` list) as binding
- Fix the six filter types (`lowpass`, `outlier`, `throttle`, `time_throttle`, `time_simple_moving_average`, `range`) with their type-specific keys
- Enforce deliberate use of `window_size` (smoothing vs. latency) and `precision`
- Turn the documented pitfalls (DB load with large `window_size`, ordering in chains, UI limit) into checkable rules
- Clearly delimit when a filter sensor is **not** the right tool and which building block applies instead

## Non-Goals

- The trigger/condition/action syntax that consumes the generated `sensor` entity — `ha-automation/automation`
- Rate of change/derivative of a sensor — `ha-automation/derivative`
- Statistical characteristics (mean, min/max, standard deviation over a time window) — `ha-automation/statistics`
- The naming dimension (`name`, `unique_id`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Quality-Scale marker — not applicable (usage spec, not an integration-development concept)

## Requirements

### Configuration

- **MUST** define the sensor as a `sensor` platform with `platform: filter` and provide an `entity_id` (required; a single `sensor` source entity) plus a non-empty `filters` list (required)
- **MUST** give every generated entity a `name` (English, ≤50 chars) and set a `unique_id` — the latter is the precondition for UI customization of the entity (documented; mechanics: `ha/naming-conventions`)
- **MUST** in each stage of the `filters` list provide the `filter` key with one of the six types: `lowpass`, `outlier`, `throttle`, `time_throttle`, `time_simple_moving_average`, `range`
- **SHOULD** choose `window_size` deliberately (default `1`): for `time_throttle`/`time_simple_moving_average` as a time (`"hh:mm"`), otherwise as an integer count of past states to examine — a larger window smooths more but increases latency
- **MAY** set `precision` (default `2`), which rounds the filtered output value via Python's `round()` to the given number of decimals
- **MUST** assign the type-specific keys correctly: `time_constant` (default `10`) only on `lowpass`; `radius` (default `2.0`) only on `outlier`; `type` (default `"last"`) only on `time_simple_moving_average`; `lower_bound`/`upper_bound` (default `-∞`/`+∞`) only on `range`
- **MUST** account for the fact that `throttle` passes only the first state per (integer) window and `time_throttle` only the first state per time window — both reduce data volume but do not smooth

### Use in Automations & Templates

- **MUST** consume the generated `sensor` entity (the smoothed value) in automations and templates instead of the raw sensor where smoothing was the purpose — detailed contract in `ha-automation/automation`
- **MUST** order filter stages in the desired processing order — the docs state clearly: "Filters are applied according to the order present in the configuration file"; each stage's output is the next stage's input
- **SHOULD** account for the latency introduced by the window in time-critical triggers — the smoothed sensor trails the raw signal

### Delimitation: When NOT to Use

- **MUST NOT** use a filter sensor to compute the **rate of change** of a value (e.g. consumption per hour from a meter reading) — that is what the **Derivative** integration (`ha-automation/derivative`) is for; a filter smooths the value itself, it does not differentiate it
- **MUST NOT** use a filter sensor to obtain **statistical characteristics** (mean, min/max, standard deviation, count) over a time window — the **Statistics** integration (`ha-automation/statistics`) is the right tool; the filter emits a single smoothed stream, not a set of characteristics
- **SHOULD NOT** set a large integer `window_size` (>1, non-time format) carelessly — the docs warn that on startup HA examines nearly every stored state of the source sensor via a DB query, which degrades responsiveness with a modified `purge_keep_days` or extensive history; prefer the time format or a small window
- **SHOULD NOT** use `throttle`/`time_throttle` when the goal is **smoothing** — these filters pass only the first value per window (data reduction/debouncing) but do not denoise the signal; for smoothing use `lowpass` or `time_simple_moving_average`
- **SHOULD NOT** apply a filter sensor to a non-numeric or categorical state — the filters operate on numeric `sensor` values; for state logic use a template sensor (`ha-automation/template`)

## Acceptance Criteria

- [ ] The sensor is defined as a `sensor` platform `filter` with `entity_id` (exactly one source) and a non-empty `filters` list
- [ ] Every entity carries an English `name` ≤50 chars and a `unique_id` (for UI customization)
- [ ] Every filter stage names one of the six valid `filter` types
- [ ] `window_size` is chosen deliberately (time format for `time_*`, otherwise integer); the latency is accounted for
- [ ] Type-specific keys are assigned correctly (`time_constant`/`lowpass`, `radius`/`outlier`, `type`/`time_simple_moving_average`, `lower_bound`/`upper_bound`/`range`)
- [ ] Filter stages are in the intended processing order
- [ ] No carelessly large integer `window_size` (DB-load warning accounted for)
- [ ] The "when NOT to use" delimitation holds: no filter for rate of change (derivative), statistics (statistics), or throttle-instead-of-smoothing
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Default filter choice**: Should this spec recommend a binding default filter type for "smooth a noisy sensor" (e.g. `outlier` followed by `lowpass`), or does the filter choice stay a case-by-case author decision?
