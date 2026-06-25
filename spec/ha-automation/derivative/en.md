# HA Automation: Using Derivative

Status: draft

## Context

The `derivative` integration creates a sensor that estimates the **derivative** (rate of change) of another numeric sensor — the docs put it as: it "estimates the derivative of the values provided by another sensor (the **source sensor**)." Typical applications are power from energy, speed from position, or generally "how fast does this reading change per unit of time." The resulting sensor carries a unit of the form `x/y`, where `x` is the unit of the source sensor and `y` is the value of `unit_time`.

Its real HA classification is **Helper / Utility** (doc categories: *Helper, Sensor, Utility, Energy*) — **not** an automation. There is an integration card under [`/integrations/derivative/`](https://www.home-assistant.io/integrations/derivative/). The helper is created either through the UI (Settings → Devices & Services → Helpers → Create Helper → *Derivative*) or as YAML under the `sensor:` platform with `platform: derivative`. This spec deliberately lives in the `ha-automation` corpus because a derivative sensor's value is almost always consumed in automations, templates, and dashboards; it governs **usage**, not the development of a custom integration.

Verified source: [`/integrations/derivative/`](https://www.home-assistant.io/integrations/derivative/) (configuration options, `time_window` behaviour, the `total_increasing` note for non-negative derivatives).

## When to Use

Use `derivative` when you need a numeric sensor's **rate of change per unit of time** as its own sensor. The helper produces the derivative `source-unit/unit_time` and is the right tool as soon as "how fast does this reading change" is the question. Typical use cases:

- **Power from energy** — derive instantaneous power (`Wh/h ≈ W`) from an energy counter (`Wh`/`kWh`) with `unit_time: h`
- **Speed from position/distance** — obtain speed (distance per time) from a distance or position sensor
- **Consumption/flow rate** — derive the rate from a non-negative counter (router bandwidth, rain gauge), with `state_class: total_increasing` for correct reset handling
- **Temperature/fill-level gradient** — compute the rise/fall rate (e.g. °C per hour, tank fill per minute) as a numeric value for triggers and display
- **Smoothed rate for triggers** — produce a debounced rate of change for `numeric_state` triggers via `time_window` > 0 (time-weighted SMA) instead of chattering on the raw point-to-point derivative

A derivative sensor is right as soon as the **time derivative** of a continuous value is needed. For the time integral (energy from power), plain smoothing, statistical figures, or arbitrary computed values, other helpers apply (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the derivative helper's configuration options (`source`, `unit_time`, `unit_prefix`, `round`, `time_window`, `max_sub_interval`) as a binding usage convention
- Enforce a deliberate choice of `unit_time`/`unit_prefix` so the resulting unit is physically meaningful and legible
- Anchor the correct use of `time_window` as a time-weighted Simple Moving Average for discrete/noisy sources
- Fix the `total_increasing` contract for non-negative derivatives (counters, rain gauges) as a checkable rule
- Clearly delimit when a derivative sensor is **not** the right tool (smoothing, generic templates, integration instead of derivation)

## Non-Goals

- The inverse — the time integral (energy from power) — belongs in `ha-automation/integration-riemann`
- General smoothing/filtering of noisy signals as an end in itself — `ha-automation/filter`
- Statistical aggregation over a time window (min/max/mean) — `ha-automation/statistics`
- Arbitrary computed values unrelated to rate of change — `ha-automation/template`
- The naming dimension (`name`/`unique_id`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- The consumption contract of automations/triggers in general — `ha-automation/automation`

## Requirements

### Configuration

- **MUST** set a `source` that is the `entity_id` of a sensor providing **numeric** readings ("The entity ID of the sensor providing numeric readings")
- **MUST** choose `unit_time` deliberately from the documented SI set (`s`, `min`, `h`, `d`; default `h`) — the resulting unit is `source-unit/unit_time`, so this choice determines the physical meaning (e.g. energy `Wh` → `unit_time: h` yields power `Wh/h ≈ W`)
- **SHOULD** set `unit_prefix` only when the numeric range warrants it (documented prefixes `n`, `µ`, `m`, `k`, `M`, `G`, `T`; default `None`), aligning the choice to a sensible order of magnitude of the result
- **MAY** set `unit` explicitly to override the auto-generated unit — only when the auto unit would be physically misleading
- **SHOULD** align `round` (default `3`) to a sensible display precision so the sensor does not imply false precision
- **MUST** choose `time_window` (default `0`) **deliberately**: `0` produces the raw point-to-point derivative, a value > 0 averages over the window via a "Simple Moving Average algorithm weighted by time" — a window > 0 is indicated for discrete or briefly noisy sources
- **MAY** set `max_sub_interval` to recalculate the derivative even when the `source` provides no update for that duration (default `0` = only on a source update)
- **MUST** for non-negative derivatives (counters that reset to 0 after a power interruption — router bandwidth, rain gauges) ensure the `source` carries `state_class: total_increasing`, "as this is necessary for the integration to handle resets correctly without registering significant changes in the derivative sensor"
- **MUST** assign `name`/`unique_id` per `ha/naming-conventions` (snake_case id, English display name ≤50 chars) — mechanics there, not repeated here

### Use in Automations & Templates

- **MAY** use the derivative sensor like any sensor in `numeric_state` triggers/conditions (e.g. "power exceeds 2000 W"), read it in templates via `states('sensor.…')`, and surface it on dashboards (e.g. as a history graph of the rate of change)
- **SHOULD** guard against `unavailable`/`unknown` before comparing the value numerically in templates — a freshly created or just-restarted derivative sensor briefly provides no numeric value
- **SHOULD** trigger `numeric_state` rules on the smoothed sensor (`time_window` > 0) rather than the raw derivative when the source value is noisy, to avoid chatter (frequent firing around a threshold)
- **SHOULD NOT** use the raw sensor (`time_window: 0`) as the sole trigger for expensive/visible actions without further debouncing when the source is spiky

### Delimitation: When NOT to Use

- **MUST NOT** repurpose a derivative sensor as a generic **smoothing/de-noising filter** — it computes a derivative, not a filtered original value; for pure noise reduction of a signal the **`filter`** integration (`ha-automation/filter`) is the right tool, because it preserves the original value (optionally low-pass/outlier-filtered) instead of differentiating it
- **MUST NOT** use a derivative sensor where the **time integral** is needed (energy `kWh` from power `W`) — that is the inverse operation; the **`integration`** integration (Riemann sum, `ha-automation/integration-riemann`) is responsible there, because it accumulates over time instead of differentiating
- **SHOULD NOT** use a derivative sensor for an **arbitrary computed value** unrelated to rate of change (e.g. the sum/difference of two sensors) — a **template sensor** (`ha-automation/template`) is the fitting, more expressive construct
- **SHOULD NOT** choose `time_window` large blindly to get "smoother numbers" — too large a window lags real, fast changes (the averaged result trails reality); the window must be aligned to the expected dynamics of the signal
- **SHOULD NOT** derive statistical figures over a window (mean, min/max, trend) from a derivative sensor — the **`statistics`** integration (`ha-automation/statistics`) is meant for that; the derivative sensor provides only the rate of change

## Acceptance Criteria

- [ ] `source` points to a numeric sensor; for non-negative derivatives the source carries `state_class: total_increasing`
- [ ] `unit_time` is chosen deliberately and the resulting unit (`source-unit/unit_time`) is physically meaningful
- [ ] `unit_prefix`/`unit`/`round` are set only when they improve legibility or correctness
- [ ] `time_window` is set deliberately (0 = raw; > 0 = time-weighted SMA for discrete/noisy sources) and not oversized
- [ ] Triggers/templates guard `unavailable`/`unknown` and trigger on the smoothed sensor for a noisy source
- [ ] No derivative sensor is misused as a pure smoothing filter (use `filter`), as a time integral (use `integration`), as a generic template sensor, or as a statistics source (use `statistics`)
- [ ] `name`/`unique_id` follow `ha/naming-conventions` (mechanics not repeated)

## Open Questions

- **`state_class` of the result**: The docs do not explicitly specify the derivative sensor's `state_class` and state no Energy-dashboard suitability. Should this spec point at a cross-cutting sensor spec instead of asserting a value?
