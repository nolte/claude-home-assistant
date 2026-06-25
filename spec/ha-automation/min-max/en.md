# HA Automation: Using min_max

Status: draft

## Context

`min_max` is a **helper/sensor integration** (HA categories per the docs: *Helper*, *Sensor*, *Utility*): it combines the **current values of several source sensors at one instant** into a single derived sensor — as the minimum, maximum, latest value, mean, median, range, or sum across the monitored entities. It is a **cross**-aggregation over several sources in the moment, not a **time** statistic of a single sensor over the past.

At config level, `min_max` is set up via the UI (Settings → Devices & Services → Helpers → Create helper) or as YAML under the sensor platform key `min_max`. `entity_ids` (at least two entities) is required. `type` selects the calculation method (default `max`); `round_digits` rounds the mean/median/sum output. **All source entities must use the same unit of measurement** — the unit of the first entry becomes the sensor's unit; with differing units the sensor enters an error state per the docs (`UNKNOWN`/`ERR`).

Verified source: [`/integrations/min_max/`](https://www.home-assistant.io/integrations/min_max/) (config keys `entity_ids`/`type`/`round_digits`/`name`/`unique_id`; `type` values `min`/`max`/`last`/`mean`/`median`/`range`/`sum`; at least two entities; shared unit of measurement; handling of `unknown` states — ignored except for `sum`; UI and YAML setup). Naming mechanics referenced via `ha/naming-conventions`.

## When to Use

Use `min_max` when you want to combine the **current values of several like-kind sensors at one instant** into a single value — all sources sharing the same unit of measurement. Typical use cases:

- **Extreme across rooms** — warmest/coldest room as `max`/`min` over several temperature sensors
- **Mean of several sources** — average temperature or humidity across all room sensors (`mean`/`median`, `round_digits`)
- **Sum of like-kind meters** — total power of several outlets or total rainfall (`sum`)
- **Latest reading** — surface the most recently reported value across a sensor group (`last`)
- **Threshold automation on the aggregate** — trigger on the combined value (e.g. "warmest room > 26 °C → ventilate") instead of repeating the calculation per automation

A `min_max` sensor is the right tool as soon as **several numeric sources in the moment** are combined. For a time statistic of a single source, state duration/frequency, or non-numeric group logic it is not (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration of a `min_max` sensor (required `entity_ids`, `type`, `round_digits`) as binding
- Fix its correct use as an instantaneous cross-aggregation of several like-kind sensors
- Enforce the documented unit consistency (same unit of measurement, unit of the first entry)
- Precisely fix the `type` choice (`min`/`max`/`last`/`mean`/`median`/`range`/`sum`) and the effect of `round_digits`
- Clearly delimit when a `min_max` sensor is **not** the right tool and which building block applies instead

## Non-Goals

- The trigger/condition/action model of the automation itself — `ha-automation/automation`
- State duration/frequency of a single entity over a window — `ha-automation/history-stats`
- Long-term statistics (mean/min/max over time) of a single numeric sensor — `ha-automation/statistics`
- Non-numeric group state aggregation (e.g. "one is on") — `ha-automation/group`
- The naming dimension (`name`, snake_case `object_id`, English, ≤50 chars) — `ha/naming-conventions`, only referenced here

## Requirements

### Configuration

- **MUST** set up a `min_max` sensor via UI helper setup or as the YAML sensor platform `min_max`, and set the **required key** `entity_ids` with **at least two** entities
- **MUST** ensure that **all** sources referenced under `entity_ids` provide the **same unit of measurement** — the unit of the first entry becomes the sensor's unit; with differing units the sensor enters an error state per the docs (value `UNKNOWN`, unit `ERR`)
- **MUST** choose `type` deliberately from the documented catalog: `min`, `max` (default), `last`, `mean`, `median`, `range`, `sum` — each value computes a different aggregation across the sources
- **SHOULD** set `round_digits` (default `2`) appropriately to the magnitude, as it rounds the `mean`, `median`, and `sum` output and avoids excessive false precision
- **SHOULD** set a `unique_id` so the sensor becomes UI-customizable, and keep the `object_id` a snake_case slug and the `name` English and ≤50 characters (mechanics: `ha/naming-conventions`)

### Use in Automations & Templates

- **MUST** read the sensor value numerically: in `numeric_state` triggers/conditions via `above`/`below`, in templates via `states('sensor.x') | float` — the value is the chosen aggregation of the sources at the current instant
- **MUST** account for the fact that `unknown` source states are ignored per the docs — **except for `type: sum`**, where the sensor itself becomes `unknown`; automations must guard this case (and the unit error state) instead of computing blindly
- **SHOULD** use the sensor as an input for threshold automations (e.g. "warmest room > 26 °C → ventilate") instead of repeating the min/max/mean calculation via template in every automation
- **MAY** use `type: last` to surface the most recently reported value across the sources, when the latest reading rather than a true aggregation is wanted

### Delimitation: When NOT to Use

- **MUST NOT** misuse `min_max` as a **time statistic of a single sensor** (mean/min/max over the past) — that is what `statistics` (`ha-automation/statistics`) is for, which consumes a **single** `entity_id`, so this redirect holds for the single-source case, because `min_max` combines several sources **at one instant** and does not form a time series of a single source
- **MUST NOT** use `min_max` for **state duration/frequency** (how long/how often an entity was in a state) — that is what `history_stats` (`ha-automation/history-stats`) is for, because `min_max` aggregates numeric instantaneous values and has no notion of history/state evaluation
- **MUST NOT** use `min_max` for **non-numeric group state aggregation** (e.g. "one of several doors open", "at least one light on") — a **group** (`ha-automation/group`) is the right tool, because `min_max` computes solely on numeric values with a shared unit. Where a sensor `group` also offers momentary numeric multi-source aggregation (mean/median/range/sum), the tie-breaker is: prefer `min_max` (`ha-automation/min-max`) for a standalone aggregate sensor, and a sensor `group` (`ha-automation/group`) when the aggregate should double as a group entity or live alongside group control
- **MUST NOT** combine sources with **inconsistent units of measurement** (e.g. °C and °F, or W and kWh) — the sensor falls into `UNKNOWN`/`ERR` per the docs; the sources must be normalized to a shared unit before aggregation (e.g. via template sensors)
- **SHOULD NOT** set `round_digits` so coarse that threshold-relevant decimals are lost when the sensor feeds `above`/`below` comparisons — the rounding affects the emitted value and can distort threshold logic

## Acceptance Criteria

- [ ] Every `min_max` sensor sets `entity_ids` with at least two entities
- [ ] All source entities provide the same unit of measurement (no `UNKNOWN`/`ERR` error state)
- [ ] `type` is chosen deliberately from `min`/`max`/`last`/`mean`/`median`/`range`/`sum`
- [ ] `round_digits` is set appropriately and does not distort threshold-relevant decimals
- [ ] The read logic guards `unknown` (especially for `sum`) and the unit error state
- [ ] The sensor is used as an instantaneous cross-aggregation of several sources, not as a time statistic
- [ ] The "when NOT to use" delimitation holds: no `min_max` where `statistics` (time statistic), `history_stats` (state duration/frequency), or a `group` (non-numeric aggregation) is the right tool
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
