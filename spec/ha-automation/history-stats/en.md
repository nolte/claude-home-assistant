# HA Automation: Using history_stats

Status: draft

## Context

`history_stats` is a **helper/sensor integration** (HA categories per the docs: *Helper*, *Sensor*, *Utility*): it produces a derived sensor that evaluates **how long** or **how often** another entity was in a given state over a **past time window**. It thus yields a backward-looking metric (e.g. "how long was the light on today") — not a real-time state and not a numeric aggregation of measured values.

At config level, `history_stats` is set up as a sensor platform under the top-level key `sensor` with `platform: history_stats` (YAML); the integration also offers UI helper setup. `entity_id` and `state` are required; `type` selects the output form (`time`/`ratio`/`count`, default `time`). The time window is defined via `start`, `end`, and `duration`, of which **exactly two of the three** must be given — HA computes the third. Because the evaluation relies on history data, `history_stats` depends on the **`recorder`** and **`history`** integrations.

Verified source: [`/integrations/history_stats/`](https://www.home-assistant.io/integrations/history_stats/) (config keys `entity_id`/`state`/`type`/`start`/`end`/`duration`/`name`/`unique_id`/`state_class`/`min_state_duration`; `type` values `time`/`ratio`/`count`; the two-of-three rule for `start`/`end`/`duration`; templating in `start`/`end` with `now()`/`today_at()`/`timedelta()`; dependency on `history`/`recorder` and `purge_keep_days`). Naming mechanics referenced via `ha/naming-conventions`.

## When to Use

Use `history_stats` when you need **how long** or **how often** an entity was in a given state over a **past time window** as a backward-looking metric. Typical use cases:

- **Duration "on today"** — how many hours the light, pump, or heating ran today (`type: time`, window via `today_at()`)
- **Share/utilization** — the percentage share of a state over the window, e.g. "Wi-Fi device online today" (`type: ratio`)
- **Frequency** — how often the door was opened or a device switched on (`type: count`)
- **Threshold automation on the past** — fire when the pump ran > 2 h today (`numeric_state` on the `history_stats` sensor)
- **Several states as one match** — bundle related states as a string list under `state` and count them as one event

A `history_stats` sensor is the right tool as soon as the metric is formed **backward-looking over a window**. For the current real-time state, multi-sensor aggregation, or long-term value statistics it is not (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration of a `history_stats` sensor (required `entity_id`/`state`, `type`, two-of-three window) as binding
- Fix its correct use as a backward-looking duration/frequency metric over a defined window
- Enforce the two-of-three rule for `start`/`end`/`duration` and DST-safe templating (`today_at()`)
- Turn the documented dependency on `recorder`/`history` and the `purge_keep_days` boundary into checkable rules
- Clearly delimit when a `history_stats` sensor is **not** the right tool and which building block applies instead

## Non-Goals

- The trigger/condition/action model of the automation itself — `ha-automation/automation`
- Numeric aggregation of several sensors at one instant — `ha-automation/min-max`
- Long-term statistics (mean/min/max) of a single numeric sensor over time — `ha-automation/statistics`
- Template syntax in general — `/docs/configuration/templating/`, only the window-forming patterns here (`now()`/`today_at()`/`timedelta()`)
- The naming dimension (`name`, snake_case `object_id`, English, ≤50 chars) — `ha/naming-conventions`, only referenced here

## Requirements

### Configuration

- **MUST** set up a `history_stats` sensor as a sensor platform (`platform: history_stats` under the top-level key `sensor`) or via UI helper setup, and set the **required keys** `entity_id` and `state`
- **MUST** give under `state` the state value(s) to count as a string or a **list of strings** (the docs allow a single value or several); the values must match the real states of the referenced entity
- **MUST** give **exactly two** of the three keys `start`, `end`, `duration` — HA computes the third; giving all three or only one is invalid per the docs
- **MUST** choose `type` deliberately: `time` (duration in hours, default), `ratio` (percentage share), `count` (number of matches) — the output unit follows directly from `type`
- **SHOULD** work DST-safely in `start`/`end` templates with `today_at()` (instead of manual date/time arithmetic) and `timedelta()`, as the docs explicitly recommend, to avoid daylight-saving-time errors
- **SHOULD** set a `unique_id` so the sensor becomes UI-customizable, and keep the `object_id` a snake_case slug and the `name` English and ≤50 characters (mechanics: `ha/naming-conventions`)
- **MAY** set `min_state_duration` to filter out state changes below a minimum duration, and adjust `state_class` (default `measurement`) when the sensor should appear in long-term statistics

### Use in Automations & Templates

- **MUST** read the sensor value numerically: in `numeric_state` triggers/conditions via `above`/`below`, in templates via `states('sensor.x') | float` — the value is hours, percent, or a count depending on `type`
- **MUST** account for the fact that `history_stats` evaluates only the **current** window and updates continuously (per the docs: when the source entity changes and once per minute) — the value is not a frozen end-of-day total but a running state of the window
- **SHOULD** use the sensor as an input for threshold automations (e.g. "pump ran > 2 h today → notify") instead of reconstructing the history evaluation in a template via `states.*` history
- **MAY** combine several `state` values to treat related states as one match (per the docs, a transition between listed states counts as one continuous event for `count`)

### Delimitation: When NOT to Use

- **MUST NOT** use `history_stats` to query or react to the **current real-time state** of an entity — a direct `state`/`numeric_state` trigger or a **template sensor** (`ha-automation/template`) is the right tool — or `ha-automation/threshold` only when a reusable numeric threshold bool is needed — because `history_stats` is a backward-looking aggregation over a window and does not yield the instantaneous value
- **MUST NOT** misuse `history_stats` for **numeric aggregation of the measured values of several sensors at one instant** (min/max/mean/sum) — that is what `min_max` (`ha-automation/min-max`) is for, because `history_stats` measures state **durations/frequencies** of a single entity, not the combination of values from several sources
- **SHOULD NOT** use `history_stats` for **long-term statistics** (mean/min/max/median of a numeric sensor over time) — that is what `statistics` (`ha-automation/statistics`) is for, because `history_stats` is bound to **states** (on/off/"home") and does not form a continuous value statistic
- **SHOULD NOT** choose a `duration`/`start`/`end` window that **reaches beyond the recorder retention** (`purge_keep_days`) — per the docs the history data then does not cover the full window and the statistics become incomplete; the window must lie within the stored history
- **SHOULD NOT** give **all three** time keys or only **one** — the docs require exactly two of three; any other combination is invalid or ambiguous

## Acceptance Criteria

- [ ] Every `history_stats` sensor sets the required keys `entity_id` and `state`
- [ ] `state` matches real state values of the entity (string or list)
- [ ] Exactly two of the three keys `start`/`end`/`duration` are given
- [ ] `type` is set deliberately (`time`/`ratio`/`count`) and the read logic matches the resulting unit
- [ ] `start`/`end` templates use `today_at()`/`timedelta()` (DST-safe) instead of manual date arithmetic
- [ ] The time window lies within the recorder retention (`purge_keep_days`)
- [ ] The sensor is used as a backward-looking duration/frequency metric, not as a real-time state
- [ ] The "when NOT to use" delimitation holds: no `history_stats` where template/threshold (real-time), `min_max` (multi-sensor aggregation), or `statistics` (long-term value statistics) is the right tool
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
