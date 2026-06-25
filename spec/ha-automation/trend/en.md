# HA Automation: Using Trend

Status: draft

## Context

The `trend` integration creates a **`binary_sensor`** that detects whether an observed value is **rising or falling** over a time window and emits the result as `on`/`off`. It collects samples of the source, fits a line through those samples, and compares its **gradient** (measured in "sensor units per second") against `min_gradient`. When the gradient exceeds the threshold in the expected direction, the sensor turns `on`.

Its real HA classification is **Helper** (also "Binary sensor" and "Utility" per the integration card) — not a connectable device and not its own automation domain. It is set up via the UI helper (Settings → Devices & Services → Helpers → "Create helper") or as YAML under the `binary_sensor` platform `trend`.

By default the sensor detects **rising** trends (`on` for a positive gradient ≥ `min_gradient`); `invert: true` flips this to **falling** trends. Per the docs the sensor needs "at least two updates of the tracked entity to establish a trend". Its behavior depends sensitively on `sample_duration`, `max_samples`, and `min_gradient` — poor tuning either produces noise or swallows real trends. The sensor exposes, among others, the attributes `gradient`, `min_gradient`, `invert`, `sample_count`, and `sample_duration`.

Verified sources: `/integrations/trend/` (configuration variables, the `min_gradient` example "-2 °C/h = -0.00055", gradient "in sensor units per second", the `max_samples` rule of thumb "7200/120 = 60") and the core component `homeassistant/components/trend/binary_sensor.py` for the exact attribute names and the `is_on` logic (absolute gradient above `min_gradient` **and** matching sign, then optionally inverted).

## When to Use

Use `trend` whenever the **direction** (rising or falling) of a numeric value is needed as a reusable boolean `binary_sensor` — not the exact value, but the statement "moving up/down". Typical use cases:

- **Detect a rising trend** — notify when room temperature or humidity climbs over the sample window (default `invert: false`)
- **Detect a falling trend** — warn on a dropping battery/tank/charge level via `invert: true`
- **Slope instead of instantaneous value** — trigger ventilation/heating already as a rise begins, before a fixed bound is reached (`min_gradient`)
- **Reusable direction signal** — define the same "rising/falling" statement once and reference it as `binary_sensor.<name>` across several automations, conditions, and dashboard cards
- **Diagnostics via `gradient`** — surface the currently measured slope (units/second) on a dashboard via the attribute

A `trend` is the right tool as soon as only the **direction** matters. For the exact rate value, an instantaneous threshold comparison, or unsmoothed noise it is not (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the `trend` helper as the canonical way to express a **direction** (rising/falling) of a value as a reusable boolean `binary_sensor`
- Make the roles of `sample_duration`, `max_samples`, `min_samples`, and `min_gradient` binding for reliable trend detection
- Enforce deliberate use of `invert` (falling instead of rising)
- Fix the need for smoothing/sample tuning on noisy signals
- Clearly delimit when a `trend` is **not** the right tool (exact rate value, instantaneous threshold, unsmoothed noise)

## Non-Goals

- General automation anatomy (trigger/condition/action, modes) — `ha-automation/automation`
- The **exact numeric value** of a rate of change (e.g. °C per hour) — `ha-automation/derivative`
- Comparing an **instantaneous value** against a fixed bound as a boolean — `ha-automation/threshold`
- Statistical aggregates/smoothing (mean, min/max over a window) as input smoothing — `ha-automation/statistics`
- The naming dimension (`friendly_name`/`unique_id`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here

## Requirements

### Configuration

- **MUST** name exactly one source to observe via `entity_id`; without `attribute` the **state** is tracked, with `attribute` the named attribute value
- **MUST** set `min_gradient` deliberately (default `0.0`) and think in the unit "sensor units **per second**" — the docs convert their example "-2 °C per hour" as `-2 / 3600 = -0.00055`; too small a value makes the sensor oversensitive, too large swallows real trends
- **MUST** tune `sample_duration` (default `0`, seconds) and `max_samples` (default `2`) to the source's update frequency; the docs give the rule of thumb: to trend over two hours with a 120 s update, `max_samples` must be ≥ `7200/120 = 60`
- **MAY** raise `min_samples` (default `2`) so the gradient is computed only after enough samples are collected and short outliers do not feign a trend
- **MUST** set `invert: true` when a **falling** rather than a rising trend should be detected (default `false` = rising)
- **MAY** set `device_class` to pick a fitting icon and `on`/`off` label in the frontend
- **SHOULD** give a `friendly_name` and — in YAML — a `unique_id` so the sensor is stably referenceable and UI-adjustable; mechanics in `ha/naming-conventions`

### Use in Automations & Templates

- **MUST** treat the resulting `binary_sensor.<name>` as an ordinary boolean entity: as a `state` trigger (`to: "on"`/`"off"`), as a `state` condition, and in templates via `is_state(...)`; `on` means "trend detected in the configured direction"
- **MAY** read the `gradient` attribute (currently measured slope in units/second) plus `min_gradient`, `invert`, `sample_count`, and `sample_duration` for diagnostics or dashboard display
- **SHOULD** prefer the `binary_sensor` as soon as the same direction statement is needed in **multiple** places (several automations, conditions, dashboard cards) — one trend definition instead of n duplicated templates
- **MUST** account for `unavailable`/`unknown` of the source entity: if the source yields no numeric samples, the trend sensor can become indeterminate — downstream automations must handle this case
- **SHOULD** note that once the trend ends, `on` returns to `off` only when the gradient falls below `min_gradient` — for hold logic with a fixed minimum duration use the automation `for` option (`ha-automation/automation`), not the trend itself

### Delimitation: When NOT to Use

- **MUST NOT** use `trend` to obtain or display an **exact rate value** (e.g. "currently +1.4 °C/h") — `trend` yields only the boolean "trend yes/no"; for the rate as a usable numeric value/sensor use `ha-automation/derivative`
- **MUST NOT** use `trend` to check an **instantaneous value** against a fixed bound (e.g. "temperature > 25 °C") — that is a threshold comparison, not a direction signal; use `ha-automation/threshold` (or a `numeric_state` trigger) instead
- **SHOULD NOT** apply `trend` to a heavily **noisy** signal without sufficient `sample_duration`/`max_samples` and without pre-smoothing — noise produces spurious trends and false `on`/`off` switches; first smooth and feed the smoothed value as `entity_id` — for pure noise smoothing use `ha-automation/filter` as the dedicated smoother, for a statistical characteristic over the samples use `ha-automation/statistics` (e.g. moving average) — or choose `min_gradient` and the sample window more conservatively
- **SHOULD NOT** use `trend` with the default `max_samples: 2` for a **long-term** trend window — two samples only measure the last change, not the trend over time; `sample_duration`/`max_samples` must cover the desired window (the docs' rule of thumb)
- **MUST NOT** express **boolean combination logic** of several entities (AND/OR) with `trend` — use a **template binary sensor** (`ha-automation/template`) that expresses the composite condition declaratively

## Acceptance Criteria

- [ ] Exactly one `entity_id` is set; `attribute` is set only when the state should not be tracked
- [ ] `min_gradient` is set deliberately in units **per second** (hour/minute rates are converted)
- [ ] `sample_duration` and `max_samples` cover the desired trend window (the docs' rule of thumb applied); the default `max_samples: 2` is not kept for long-term trends
- [ ] `invert: true` is set when a falling trend should be detected
- [ ] The `binary_sensor` is used as a boolean entity in triggers/conditions/templates; `on` = "trend in the configured direction"
- [ ] `unavailable`/`unknown` of the source is handled downstream
- [ ] The "when NOT to use" delimitation holds: no `trend` for exact rates (→ `derivative`), no `trend` for instantaneous thresholds (→ `threshold`), no unsmoothed noise, no long-term trend with `max_samples: 2`, no combination logic (→ `template`)
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Attribute stability**: The exact attribute names (`gradient`, `min_gradient`, `invert`, `sample_count`, `sample_duration`) and the `is_on` logic (magnitude + sign) come from the core component, not from the integration doc page itself. Should the spec treat them as binding or only mark them "observable but not documentation-guaranteed" until they appear on `/integrations/trend/`?
