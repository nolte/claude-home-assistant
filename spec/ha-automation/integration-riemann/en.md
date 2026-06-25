# HA Automation: Using Integration (Riemann Sum)

Status: draft

## Context

The `integration` integration creates a sensor that estimates the **time integral** of another numeric sensor via a Riemann sum — the classic application is energy (`kWh`) from power (`W`). It is the inverse operation of `derivative`: instead of differentiating, it accumulates over time. When the source provides power in Watts with `device_class: power`, the sensor automatically sets `device_class: energy` and yields e.g. `sensor.energy_spent` "which will have your energy in kWh, as a `device_class` of `energy`." The resulting unit combines source unit, prefix, and time unit (e.g. `W` + prefix `k` + time `h` = `kWh`).

Note the ambiguity: the **real domain key is `integration`** (not `integration-riemann`) — this slug is chosen only to avoid confusion with the general notion of an "integration" (add-on/custom component). In the UI the helper is called **Integral** (Settings → Devices & Services → Helpers → Create Helper → *Integral*). In YAML it lives under the `sensor:` platform with `platform: integration`.

Its real HA classification is **Helper / Utility** (doc categories: *Helper, Sensor, Energy, Utility*) — **not** an automation. There is an integration card under [`/integrations/integration/`](https://www.home-assistant.io/integrations/integration/). This spec lives in the `ha-automation` corpus because the sensor is consumed in automations, dashboards, and above all the **Energy dashboard**; it governs **usage**, not the development of a custom integration. The sensor "keeps its value across Home Assistant restarts."

Verified source: [`/integrations/integration/`](https://www.home-assistant.io/integrations/integration/) (configuration options, `method` values, `device_class` derivation, `max_sub_interval`, restart persistence, update triggers).

## When to Use

Use `integration` (Integral/Riemann sum) when you want to **sum an instantaneous quantity over time into an accumulated quantity**. The helper is the inverse of `derivative`: it integrates instead of differentiating and keeps its value across restarts. Typical use cases:

- **Energy from power** — automatically form `device_class: energy` (`kWh`) from a `device_class: power` source (Watts), e.g. for a smart plug without its own energy counter
- **Energy-dashboard source** — feed the accumulated, restart-persistent energy sensor into the Energy dashboard as a consumption source
- **Volume from flow** — integrate cumulative volume (litres) over time from a flow rate (e.g. l/min)
- **Match the method to the source** — `trapezoidal` for frequently updating sources, `left`/`right` for rectangular, long-stable step profiles (control accuracy via `method`)
- **Accumulate a rarely reporting source** — keep integrating time-based via `max_sub_interval` when the source stays constant for long and sends updates only rarely

An integral sensor is right as soon as the **time integral** of a continuous reading is needed. For event counters, resettable consumption cycles, or plain derivation, other helpers apply (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the integral helper's configuration options (`source`, `method`, `round`, `unit_prefix`, `unit_time`, `max_sub_interval`) as a binding usage convention
- Enforce a **deliberate choice of `method`** (`left`/`right`/`trapezoidal`) against the source's characteristics, because it determines accuracy
- Anchor the automatic `device_class: energy` derivation (source `power` in Watts) and Energy-dashboard suitability
- Anchor the value of `max_sub_interval` for rarely updating sources (time-based integration)
- Clearly delimit when an integral sensor is **not** the right tool (event counting, resettable consumption cycles, plain derivation)

## Non-Goals

- The inverse — derivation/rate of change (power from energy) — belongs in `ha-automation/derivative`
- Resettable consumption cycles (daily/monthly, tariff cycles) — `ha-automation/utility-meter`
- Counting discrete events — `ha-automation/counter`
- The Energy-dashboard configuration itself (devices, tariffs, grid/production) — `ha/energy-dashboard`
- The naming dimension (`name`/`unique_id`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- The consumption contract of automations/triggers in general — `ha-automation/automation`

## Requirements

### Configuration

- **MUST** set a `source` that is the `entity_id` of a sensor providing **numeric** readings ("The entity ID of the sensor providing numeric readings") — typically an instantaneous quantity (power, flow)
- **MUST** choose `method` (default `trapezoidal`) deliberately against the source's characteristics:
  - `trapezoidal` — "the most accurate of the currently implemented methods, **if** the source updates often"
  - `left` — "**underestimates** the intrinsic source, but is extremely accurate at estimating rectangular functions which are very stable for long periods"
  - `right` — like `left`, but "**overestimates** the intrinsic source"
- **MUST** choose `unit_time` deliberately from the documented SI set (`s`, `min`, `h`, `d`; default `h`) — it sets the time axis of the integration and thus the result unit (Watts integrated over `h` ⇒ Watt-hours)
- **SHOULD** set `unit_prefix` where the order of magnitude warrants it (documented prefixes `k`, `M`, `G`, `T`; default `None`) — e.g. `k` so `Wh` becomes a readable `kWh`
- **SHOULD** align `round` (default `3`) to a sensible display precision
- **MAY** set `max_sub_interval`, which "applies time-based integration if the source did not change for this duration" — indicated for sources that stay constant for long stretches and send updates rarely, so the accumulated value does not freeze
- **MUST** accept that the sensor "is updated whenever the source changes and, optionally, based on a predefined time interval" (via `max_sub_interval`) — the update frequency follows the source, not a fixed cadence
- **MUST** assign `name`/`unique_id` per `ha/naming-conventions` (snake_case id, English display name ≤50 chars) — mechanics there, not repeated here

### Use in Automations, Templates & Energy Dashboard

- **SHOULD** use the integral sensor for the **Energy dashboard** when the source carries `device_class: power` (Watts) — it then automatically gets `device_class: energy` and yields e.g. energy in `kWh`; the accumulated value survives "across Home Assistant restarts," which is what makes energy tracking viable at all
- **MAY** use the sensor in `numeric_state` triggers/conditions (e.g. "energy consumed today exceeds X"), in templates via `states('sensor.…')`, and on dashboards (consumption/history graph)
- **SHOULD** guard against `unavailable`/`unknown` before comparing numerically in templates — a freshly created integral sensor briefly provides no numeric value
- **SHOULD NOT** display the monotonically rising integral sensor directly as "daily/monthly consumption" without layering a resettable cycle over it (see Delimitation) — the raw integral keeps accumulating without a reset

### Delimitation: When NOT to Use

- **MUST NOT** use an integral sensor as an **event counter** (e.g. "how many times was the door opened") — it integrates a continuous reading over time and does not count discrete events; a **`counter`** (`ha-automation/counter`) is the right construct for that
- **MUST NOT** use an integral sensor for **resettable consumption cycles** (daily, monthly, tariff cycle) — the integral accumulates monotonically and knows no periodic reset; the **`utility_meter`** (`ha-automation/utility-meter`) is responsible there, resetting the counter cyclically and modelling tariff periods (one typically feeds the integral sensor *into* a utility meter)
- **MUST NOT** use an integral sensor where a **derivative/rate of change** is needed (power `W` from energy `Wh`) — that is the inverse operation; the **`derivative`** integration (`ha-automation/derivative`) is responsible there
- **SHOULD NOT** leave `method` blindly on the `trapezoidal` default when the source has a **step/hold profile** with rare updates (e.g. a device that reports only on load change) — here `left`/`right` are more accurate for rectangular, long-stable functions; the default trapezoidal rule is only "accurate … if the source updates often"
- **SHOULD NOT** omit `max_sub_interval` when the source stays constant for long and sends rarely yet should still accumulate continuously — without `max_sub_interval` the integral does not advance between source updates

## Acceptance Criteria

- [ ] `source` points to a numeric (typically instantaneous) sensor
- [ ] `method` is chosen deliberately against the source characteristics (frequent updates → `trapezoidal`; rectangular/rare → `left`/`right`)
- [ ] `unit_time`/`unit_prefix`/`round` are set deliberately; the result unit is legible (e.g. `kWh`)
- [ ] `max_sub_interval` is set when the source is long-constant and reports rarely
- [ ] For a `power` source the automatic `device_class: energy` derivation is used for the Energy dashboard; restart persistence is accounted for
- [ ] Triggers/templates guard `unavailable`/`unknown`
- [ ] No integral sensor is misused as an event counter (use `counter`), as a resettable consumption cycle (use `utility_meter`), or as a derivative (use `derivative`)
- [ ] `name`/`unique_id` follow `ha/naming-conventions` (mechanics not repeated)

## Open Questions

- **`state_class` of the result**: The docs do not explicitly state whether the integral sensor carries `state_class: total` or `total_increasing` (relevant for long-term statistics/Energy dashboard). Should this spec point at a cross-cutting sensor spec instead of asserting a value?
