# HA Automation: Using Threshold

Status: draft

## Context

The `threshold` integration creates a **`binary_sensor`** that compares an analog sensor value against one or two thresholds and emits the result as `on`/`off`. It turns a continuous measurement (temperature, humidity, power, brightness …) into a boolean state that can be reused across automations, conditions, and dashboards. An optional **hysteresis** prevents flapping (rapid back-and-forth switching) around the threshold.

Its real HA classification is **Helper** (also "Binary sensor" and "Utility" per the integration card) — not a connectable device and not its own automation domain. It is set up via the UI helper (Settings → Devices & Services → Helpers → "Create helper") or as YAML under the `binary_sensor` platform `threshold`.

Three modes result from the keys set: only `lower` (lower bound), only `upper` (upper bound), or both (`lower` **and** `upper` → range / "in_range" mode). Besides its `on`/`off` state, the resulting sensor exposes the `position` attribute (`above`, `below`, `in_range`, `unknown`) plus `type`, `lower`, `upper`, `hysteresis`, and `sensor_value`.

Verified sources: `/integrations/threshold/` (configuration variables, the "Rising/Falling sensor values" mode table, hysteresis semantics) and the core component `homeassistant/components/threshold/binary_sensor.py` for the exact attribute names and `position` values.

## When to Use

Use `threshold` when you want to turn an **analog sensor value into a reusable boolean `binary_sensor`** that emits `on`/`off` as soon as it crosses one or two thresholds. Typical use cases:

- **Upper/lower bound alarm** — model a bound as a boolean via only `upper` (e.g. temperature above 28 °C → `on`) or only `lower` (e.g. humidity below 30 %)
- **Range / "in_range" monitoring** — model a comfort/setpoint band with `lower` **and** `upper` (inside → `on`, outside → `off`), e.g. temperature 20–24 °C
- **Flap-free switch point** — switch a noisy value or one hovering near the threshold (power, brightness) stably via `hysteresis`
- **Reused threshold boolean** — define a threshold centrally as one entity instead of duplicating the same `numeric_state` check across several automations, conditions, and dashboard cards
- **Three-way position via `position`** — read the `position` attribute (`above`/`below`/`in_range`/`unknown`) for a three-way branch instead of re-computing the raw value against the threshold

A `threshold` helper is right as soon as an analog value is needed as a **reusable above/below boolean**. For exact equality/categorical logic, one-shot use without its own entity, or judging a rate of change, other building blocks apply (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the `threshold` helper as the canonical way to turn an analog value into a reusable boolean `binary_sensor`
- Make the three modes (`lower`, `upper`, both) and their `on`/`off` semantics binding
- Enforce deliberate use of `hysteresis` against flapping
- Prioritize reading the `position` attribute over re-computing the threshold in templates
- Clearly delimit when a `threshold` is **not** the right tool (exact equality, one-shot trigger without reuse, raw values without smoothing)

## Non-Goals

- General automation anatomy (trigger/condition/action, modes) — `ha-automation/automation`
- Purely computed or combined boolean logic (AND/OR over several entities, exact string equality) — `ha-automation/template`
- Rate/derivative values (e.g. °C per hour as a number) — `ha-automation/derivative`; trend direction as a boolean — `ha-automation/trend`
- Statistical aggregates (mean, min/max over a window) as a smoothing source — `ha-automation/statistics`
- The naming dimension (`name`/`unique_id`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here

## Requirements

### Configuration

- **MUST** name exactly one source to monitor via `entity_id`; per the docs only sensors are supported
- **MUST** set at least one threshold key: `lower`, `upper`, or both — without a threshold the sensor has no basis for comparison
- **MUST** choose the mode deliberately: only `lower` (sensor below the lower bound → `on`), only `upper` (sensor above the upper bound → `on`), or `lower` **and** `upper` (inside the range → `on`, outside → `off`; `position: in_range`)
- **SHOULD** set `hysteresis` (default `0.0`) explicitly when the source value is noisy or can hover near the threshold; hysteresis is "the distance the observed value must be from the threshold before the state is changed" and thus prevents flapping
- **MUST** keep `lower < upper` when both are set so that a valid range exists
- **MAY** set `device_class` to pick a fitting icon and `on`/`off` label in the frontend (e.g. `cold`, `heat`, `problem`)
- **SHOULD** give a `name` and — in YAML — a `unique_id` so the sensor is stably referenceable and UI-adjustable; mechanics in `ha/naming-conventions`

### Use in Automations & Templates

- **MUST** treat the resulting `binary_sensor.<name>` as an ordinary boolean entity: as a `state` trigger (`to: "on"`/`"off"`), as a `state` condition, and in templates via `is_state(...)`
- **SHOULD** read the `position` attribute (`above`, `below`, `in_range`, `unknown`) instead of re-computing the raw value against the same threshold when the three-way position is needed
- **MAY** read the attributes `lower`, `upper`, `hysteresis`, `type`, and `sensor_value` for diagnostics or dashboard display
- **SHOULD** prefer the `binary_sensor` as soon as the same threshold boolean is needed in **multiple** places (several automations, conditions, dashboard cards) — one threshold definition instead of n duplicated `numeric_state` checks
- **MUST** account for `unavailable`/`unknown` of the source entity: the threshold sensor itself can become `unknown`/`position: unknown` when the source yields no numeric value — downstream automations must handle this case

### Delimitation: When NOT to Use

- **MUST NOT** use `threshold` for **exact equality** or discrete states (e.g. "exactly 21 °C", "mode == eco", string comparison) — `threshold` only knows "above/below a bound"; for exact/categorical logic use a **template binary sensor** (`ha-automation/template`) that expresses the condition declaratively
- **SHOULD NOT** create a `threshold` helper when the threshold is needed in **only a single place** and no reusable entity is wanted — then a `numeric_state` trigger directly in the automation (`ha-automation/automation`) is leaner; the helper pays off once the boolean is **reused**
- **SHOULD NOT** apply `threshold` to a heavily **noisy** raw signal with neither smoothing **nor** `hysteresis` — the sensor then flaps; either set `hysteresis` or first smooth and feed the smoothed value as `entity_id` — for pure noise smoothing use `ha-automation/filter` as the dedicated smoother, for a statistical characteristic over the samples use `ha-automation/statistics` (e.g. moving average)
- **MUST NOT** use `threshold` to judge a **rate of change** ("rising faster than X") — that is not a threshold comparison of an instantaneous value; for direction use `ha-automation/trend`, for the numeric rate use `ha-automation/derivative`
- **SHOULD NOT** stack several `threshold` sensors to build an AND/OR combination of conditions when a single **template binary sensor** (`ha-automation/template`) expresses the composite logic more clearly and with one entity

## Acceptance Criteria

- [ ] Exactly one `entity_id` (a sensor) is set as the source
- [ ] At least one threshold (`lower`, `upper`, or both) is set; with both, `lower < upper` holds
- [ ] The mode (lower/upper/range) and the resulting `on`/`off` semantics are chosen deliberately
- [ ] `hysteresis` is set explicitly when the source signal is noisy or can hover near the threshold
- [ ] The `binary_sensor` is used as a boolean entity in triggers/conditions/templates; for the three-way position, `position` is read instead of re-computed
- [ ] `unavailable`/`unknown` of the source is handled downstream
- [ ] The "when NOT to use" delimitation holds: no `threshold` for exact equality (→ template), no helper without reuse (→ `numeric_state`), no unsmoothed noise without `hysteresis`, no rate judgement (→ `trend`/`derivative`)
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Attribute stability**: The exact `position` values (`above`/`below`/`in_range`/`unknown`) and the attribute names come from the core component, not from the integration doc page itself. Should the spec treat them as binding or only mark them "observable but not documentation-guaranteed" until they appear on `/integrations/threshold/`?
