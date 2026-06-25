# HA Automation: Using Utility Meter

Status: draft

## Context

The `utility_meter` integration is a **consumption meter with billing cycles**: it takes a continuously increasing total counter (e.g. an energy, water, or gas sensor) as its `source` and derives a sensor that reports consumption **within a cycle** and is automatically reset to zero at the end of that cycle. This turns a steadily growing meter reading into billable quantities such as "energy used this week" or "water used this month".

`utility_meter` is **not** an automation domain. Its real HA category is **Helper/Utility** (integration card under `/integrations/utility_meter/`); it is created via YAML under the top-level `utility_meter:` key or as a UI helper. This spec turns the official usage docs into a binding convention for how the plugin configures utility-meter helpers and references them from automations.

Optionally the integration supports **tariffs** (`tariffs`): instead of a single sensor, it then creates one sensor per tariff plus a **select entity** that switches the currently active tariff — only the active tariff keeps counting, the others pause.

Verified source: `/integrations/utility_meter/` (configuration variables `source`, `name`, `unique_id`, `cycle`, `offset`, `cron`, `delta_values`, `net_consumption`, `tariffs`, `periodically_resetting`, `always_available`; actions `utility_meter.calibrate`, `utility_meter.reset`; tariff switching via `select.select_option` on the generated select entity).

## When to Use

Use `utility_meter` when you want to derive a per-billing-cycle consumption from a **continuously increasing total counter** that automatically resets to zero at the end of each cycle. The helper slices a steadily growing meter reading into billable periods. Typical use cases:

- **Daily/monthly/yearly consumption** — turn a total energy/water/gas counter into a per-`cycle` (`daily`, `monthly`, `yearly` …) consumption sensor that resets at the period end
- **Tariff/time-of-use billing** — create one sensor per tariff (e.g. peak/off-peak) plus a select entity via `tariffs`, switching the active tariff time-based via `select.select_option`
- **Feed-in/net meter** — keep a counter that may run both positive (import) and negative (feed-in) via `net_consumption: true`
- **Offset billing periods** — align the reset not to the period start but e.g. to the utility's billing date via `offset` (or `cron`)
- **Source with delta values or self-reset** — handle sources correctly that provide deltas rather than absolute values or reset to 0 by themselves (e.g. a smart plug on boot) via `delta_values`/`periodically_resetting`
- **Energy-dashboard source** — feed the cyclically reset consumption sensor into the Energy dashboard as a consumption source

A utility meter is right as soon as an increasing total counter should be sliced into **resettable consumption cycles**. To form the raw integral from a power quantity, for freely incrementable counters, or for statistical figures, other building blocks apply (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the required and optional keys of a utility-meter helper (`source`, `cycle`, `offset`, `tariffs`, `net_consumption`, `delta_values`, `periodically_resetting`) as binding
- Enforce the correct nature of the `source` (a continuously increasing total counter) as a precondition
- Fix the tariff mechanics (tariff sensors + select entity, switching via `select.select_option`) as the documented path
- Guard deliberate use of `delta_values`/`periodically_resetting`/`net_consumption` against their respective measurement situations
- Clearly delimit when a utility meter is **not** the right tool and which building block applies instead

## Non-Goals

- Producing the raw integral from a power quantity (W → kWh) — that is the Riemann integration's job (`ha-automation/integration-riemann`)
- The automation engine itself (trigger/condition/action, modes) — `ha-automation/automation`
- Energy-dashboard configuration in the UI (setting up consumption sources) — out of scope here; only the sensor's suitability as a source
- The naming dimension (key/`name`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- The detailed cron syntax for `cron:` — HA's extended crontab format, named here only as an alternative to `cycle`/`offset`

## Requirements

### Configuration

- **MUST** specify a `source` whose state is a **continuously increasing total counter** (energy, water, gas, heating); the docs describe the source as "the entity ID of the sensor providing utility readings"
- **MUST** choose the reset cycle via `cycle` from the documented value range: `quarter-hourly`, `hourly`, `daily`, `weekly`, `monthly`, `bimonthly`, `quarterly`, `yearly` (`bimonthly` resets once in two months)
- **MUST** give every generated helper a stable snake_case key and an English `name` ≤50 characters, and set a `unique_id` for UI customization (mechanics: `ha/naming-conventions`)
- **SHOULD** set `offset` only when the cycle should not begin at the period start (the docs: "Cycle reset occur at the beginning of the period"); formats `'HH:MM:SS'`, `'HH:MM'`, or a time-period dictionary
- **MAY** use a `cron` instead of `cycle`/`offset` when an advanced reset schedule is needed — `cron` is per the docs "mutually exclusive of `cycle` and `offset`" and must not be set together with them
- **MUST** set `delta_values: true` **if and only if** the source provides delta values since the last reading rather than absolute values ("Set this to True if the source values are delta values since the last reading instead of absolute values") — the wrong choice corrupts every reading
- **MUST** keep or disable `periodically_resetting` deliberately: the default `true` expects a source that can itself drop back to 0 (e.g. a smart plug that resets on boot); for a source that never does, review this, since it governs the consumption calculation across source resets
- **MAY** set `net_consumption: true` when the source is a net meter and the counter may run both positive and negative ("This will allow your counter to go both positive and negative") — e.g. with feed-in
- **MAY** set `always_available: true` so the sensor stays available with its last value even when the source becomes `unavailable`/`unknown`
- **MAY** specify a `tariffs` list; the integration then creates **one sensor per tariff** plus a **select entity** that holds the current tariff

### Use in Automations & Templates

- **MUST** treat the consumption sensor the helper produces (`sensor.<key>` or `sensor.<key>_<tariff>`) as a read quantity; do not "maintain" the meter reading from automations, but let it be derived from the `source`
- **MUST** perform the tariff switch via `select.select_option` on the generated select entity (e.g. `select.daily_energy`) — this is the path the docs show, e.g. via a time-based automation (`trigger: time` … `action: select.select_option`)
- **SHOULD NOT** rely on undocumented tariff action names: the integration card lists as actions only `utility_meter.calibrate` (sets the meter to a value) and `utility_meter.reset` (resets all counters to zero) — the documented tariff switch goes through the select entity
- **MAY** use `utility_meter.calibrate` to set a known reading after a meter swap or data gap, and `utility_meter.reset` to start a cycle off-schedule
- **MAY** use the consumption sensor as a source for the **Energy dashboard**; suitability follows from the sensor's monotonic, cyclically reset nature

### Delimitation: When NOT to Use

- **MUST NOT** use `utility_meter` to turn a **power quantity** (e.g. `W`) into an energy quantity (`kWh`) — `utility_meter` does not sum an integral, it slices an already increasing total into cycles; the raw integral is produced by the Riemann integration (`ha-automation/integration-riemann`), whose output can then be the `source`
- **MUST NOT** use `utility_meter` as a generic, manually incremented/decremented counter — that is what `counter` (`ha-automation/counter`) is for; `utility_meter` is bound to an external, continuously increasing measurement source and is not freely incrementable
- **SHOULD NOT** attach a **non-monotonically-increasing** source (a fluctuating instantaneous value such as temperature, power, fill level) as the `source` — consumption derives from the growth of a total; a fluctuating source produces meaningless or negative consumption. For statistical characteristics over such values, `ha-automation/statistics` is responsible
- **SHOULD NOT** set `delta_values` and `periodically_resetting` "on suspicion" — both encode a concrete assumption about the source (delta vs. absolute values; source drops to 0 by itself). Set wrongly, they corrupt consumption across every reset; the choice must match the real source
- **SHOULD NOT** hand-duplicate several near-identical utility-meter helpers for different cycles of the same source when a tariff or cycle set expresses the same declaratively — multiple `cycle` helpers on the same `source` are legitimate, but logic does not belong in accompanying automations that set the reading manually

## Acceptance Criteria

- [ ] Every helper has a `source` that is a continuously increasing total counter (not an instantaneous/fluctuating value)
- [ ] `cycle` is from the documented value range; `cron` is not set together with `cycle`/`offset`
- [ ] Every helper carries a stable snake_case key, an English `name` ≤50 chars, and a `unique_id`
- [ ] `delta_values`, `periodically_resetting`, and `net_consumption` are set only when the real source requires it, not blanket
- [ ] Tariff helpers switch the tariff exclusively via `select.select_option` on the generated select entity
- [ ] Only the documented actions `utility_meter.calibrate`/`utility_meter.reset` are called
- [ ] The "when NOT to use" delimitation holds: no utility meter where the Riemann integration, `counter`, or `statistics` is the right tool
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Tariff-switch actions**: Earlier HA versions exposed `utility_meter.next_tariff` and `utility_meter.select_tariff`. The currently verified integration card (`/integrations/utility_meter/`) shows tariff switching exclusively via `select.select_option` and lists only `calibrate`/`reset` under actions. This spec follows the documented form. Should a note on the legacy actions be added once their status (removed vs. merely undocumented) is confirmed against the source?
