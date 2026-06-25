# HA Automation: Using the Statistics Sensor

Status: draft

## Context

The `statistics` integration provides a **statistics sensor**: it observes a source entity (`entity_id` — only sensors and binary sensors) and computes **a single statistical characteristic** (`state_characteristic`) from its most recent measurements — such as mean, median, minimum, maximum, change, or standard deviation — over a sliding window of the latest samples. The sensor is thus a **sliding aggregate over recent values**, not a long-term history.

`statistics` is **not** an automation domain. Its real HA category is **Helper/Utility** (integration card under `/integrations/statistics/`); the sensor is created via YAML (platform sensor) or as a UI helper. This spec turns the official usage docs into a binding convention for how the plugin configures statistics sensors and reads them from automations.

The sample window is bounded along two axes: `sampling_size` (maximum number of stored measurements) and/or `max_age` (maximum age of stored measurements). Used together, they cut down to the newest `sampling_size` samples within the `max_age` window.

Verified source: `/integrations/statistics/` (configuration variables `entity_id`, `name`, `state_characteristic`, `sampling_size`, `max_age`, `keep_last_sample`, `percentile`, `precision`, `unique_id`; the full characteristic catalog for numeric and binary sources; the sensor attributes `age_coverage_ratio`, `buffer_usage_ratio`, `source_value_valid`).

## When to Use

Use `statistics` when you need **a single statistical characteristic over a sliding window of the most recent measurements** from a sensor or binary sensor — a distribution over several samples, not a single derived value. Typical use cases:

- **Smooth a sliding mean** — smooth a noisy signal (temperature, power) via `state_characteristic: mean`/`average_linear`, e.g. as a clean `entity_id` source for a `threshold` helper
- **Min/max/spread in the window** — obtain the extremes or fluctuation range of the latest samples via `value_min`/`value_max`/`distance_absolute` for display and triggers
- **Dispersion/noise measure** — judge how strongly a reading fluctuates via `standard_deviation`/`variance`/`noisiness`
- **Change over the window** — quantify the change or increase/decrease over the most recent samples via `change`/`change_second`/`sum_differences`
- **Aggregate a binary sensor** — count how often a binary sensor was `on` or toggled within the window via `count_on`/`count`/`mean`
- **Span the window axes deliberately** — define the sample window by count and/or age via `sampling_size` and/or `max_age` (plus optional `keep_last_sample`)

A statistics sensor is right as soon as a **real distribution over several recent samples** is evaluated. For long-term/historical analysis, a single formula value, or a resettable consumption meter, other building blocks apply (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the required contract (`entity_id` + `state_characteristic`) and the window axes (`sampling_size`, `max_age`, `keep_last_sample`) as binding
- Enforce a deliberate choice of `state_characteristic` from the documented catalog against the intended purpose
- Anchor the separation "sliding statistic over recent samples" vs. "long-term history" as a delimitation rule
- Fix the handling of numeric vs. binary sources (different admissible characteristics)
- Clearly delimit when a statistics sensor is **not** the right tool and which building block applies instead

## Non-Goals

- Long-term/historical analysis over long timespans (hours/days "on" etc.) — `history_stats` or the recorder long-term statistics, out of scope here
- The automation engine itself (trigger/condition/action, modes) — `ha-automation/automation`
- General derived single values via template — `ha-automation/template`
- The naming dimension (`name`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- The exact mathematical definition of each individual characteristic — the integration card is the source; only selection rules here

## Requirements

### Configuration

- **MUST** specify an `entity_id` that is a **sensor or binary sensor** ("Only sensors and binary sensors are supported")
- **MUST** set a `state_characteristic` from the documented catalog — the key is required ("The characteristic that should be used as the state of the statistics sensor")
- **MUST** choose, for a **numeric source**, a characteristic from the numeric catalog: `average_linear`, `average_step`, `average_timeless`, `change`, `change_sample`, `change_second`, `count`, `datetime_newest`, `datetime_oldest`, `datetime_value_max`, `datetime_value_min`, `distance_95_percent_of_values`, `distance_99_percent_of_values`, `distance_absolute`, `mean`, `mean_circular`, `median`, `noisiness`, `percentile`, `standard_deviation`, `sum`, `sum_differences`, `sum_differences_nonnegative`, `total`, `value_max`, `value_min`, `variance`
- **MUST** choose, for a **binary source**, a characteristic from the binary catalog: `average_step`, `average_timeless`, `count`, `count_on`, `count_off`, `datetime_newest`, `datetime_oldest`, `mean`
- **MUST** define the sample window via `sampling_size` and/or `max_age`; at least one of the two axes should reasonably be set, since `sampling_size` without `max_age` has no time limit and `max_age` without `sampling_size` has no count limit
- **SHOULD** choose `sampling_size` "reasonably high" or omit it when samples should be driven by `max_age` (doc recommendation)
- **MAY** set `keep_last_sample: true` so the most recent sampled value is preserved regardless of `max_age` (default `false`) — relevant when the source does not update for longer than `max_age`
- **MUST** set `percentile` (1–99, default `50`) only in conjunction with the `percentile` characteristic; it is "only relevant with the percentile characteristic"
- **SHOULD** adapt `precision` (default `2`) deliberately to the meaningful number of decimal places of the characteristic
- **MUST** give every sensor an English `name` ≤50 characters and a `unique_id` for UI customization (mechanics: `ha/naming-conventions`)

### Use in Automations & Templates

- **MUST** treat the statistics sensor (`sensor.<name>`) as a read quantity; its state carries the computed characteristic, not the source value
- **MAY** read the documented attributes: `age_coverage_ratio` (0.0–1.0, how well the `max_age` window is covered by measurements), `buffer_usage_ratio` (0.0–1.0, how full the `sampling_size` buffer is), `source_value_valid` (whether the source provides valid values)
- **SHOULD** account for `source_value_valid`/`age_coverage_ratio` in triggers/conditions before deciding on the characteristic, when a not-yet-filled window could lead to wrong conclusions
- **MAY** use the characteristic as a `numeric_state` trigger/condition (e.g. "mean over the last N values exceeds a threshold") — trigger mechanics in `ha-automation/automation`

### Delimitation: When NOT to Use

- **MUST NOT** use the statistics sensor for **long-term/historical analysis** over long timespans (e.g. "hours a device was on today") — that is what `history_stats` or the recorder long-term statistics are for; `statistics` works on a sliding window of the most recent samples, not on the full history
- **SHOULD NOT** create a statistics sensor where a **single derived value** via a formula suffices (e.g. sum/difference/conversion of two entities) — that is a template sensor's job (`ha-automation/template`); `statistics` is only meaningful when evaluating a real distribution over several samples
- **MUST NOT** use `statistics` when only **a single smoothed output stream** of the noisy signal is needed — pure smoothing is `ha-automation/filter`'s job; `statistics` is the right tool only once a statistical characteristic/distribution over the most recent samples (mean, dispersion, min/max, change) is to be evaluated
- **SHOULD NOT** choose `state_characteristic` and window size "by feel" — the characteristic (e.g. `mean` vs. `median` vs. `change`) and `sampling_size`/`max_age` fully determine what the sensor says; an unsuitable combination yields a technically valid but semantically wrong number
- **SHOULD NOT** pair a **binary source** with a purely numeric characteristic (e.g. `median`, `standard_deviation`) or vice versa — the docs list separate characteristic catalogs for sensor and binary-sensor sources; only their intersection is valid across both source types
- **MUST NOT** misuse `statistics` as a substitute for a cyclically reset **consumption meter** (e.g. "consumption this week") — that is what `utility_meter` (`ha-automation/utility-meter`) is for, slicing an increasing total counter into billable cycles

## Acceptance Criteria

- [ ] Every sensor has an `entity_id` (sensor or binary sensor) and a set `state_characteristic`
- [ ] The chosen `state_characteristic` comes from the catalog matching the source type (numeric vs. binary)
- [ ] The window is deliberately defined via `sampling_size` and/or `max_age`; `keep_last_sample` only when needed
- [ ] `percentile` is set only together with the `percentile` characteristic; `precision` is chosen deliberately
- [ ] Every sensor carries an English `name` ≤50 chars and a `unique_id`
- [ ] Automations read the characteristic and account for `source_value_valid`/`age_coverage_ratio` where relevant
- [ ] The "when NOT to use" delimitation holds: no statistics sensor where `history_stats`, `template`, `filter`, or `utility_meter` is the right tool
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
