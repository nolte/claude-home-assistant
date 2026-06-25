---
name: ha-derived-sensor-author
description: Author one Home Assistant derived or statistical helper sensor as a spec-conformant YAML block from a described intent — bayesian, derivative, filter, min_max, statistics, threshold, trend, history_stats, integration, utility_meter, or group — conforming to the matching spec/ha-automation/<topic>. Picks the right integration, sets the math-bearing parameter (observations/prob_given_*, unit_time, window_size, state_characteristic, lower/upper/hysteresis, min_gradient, method, cycle), types the produced sensor and guards source unavailability, and reports runtime dependencies (recorder retention, integration→utility_meter). Activate on "add a sensor for the rate of change / energy from power / moving average / threshold / trend of…", "make a utility_meter / statistics / bayesian sensor for…". Do not activate for the generic template integration (ha-automation-author), stateful helpers (ha-helper-scaffold), real integration sensors (ha-integration-scaffold), blueprints, or deploying to a live HA instance.
tags: [home-assistant, sensor, statistics, yaml]
---

# HA Derived Sensor Author

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-derived-sensor-author/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-derived-sensor-author/en.md).

## Why this is a skill, not an agent

- **Human-visible authoring surface** — the user describes the derived value they need and reads back the YAML and the conformance report; a skill keeps this on the visible command surface, like the sibling author/scaffold skills.
- **Mid-flow interactivity** — integration selection and the delimitation redirect (rate vs. smoothing vs. integral; threshold vs. trend) are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — a single sensor block is small enough to generate inline.
- Counter-dimension considered: the draft→validate loop could be an agent, but the integration choice and the runtime-dependency notes belong in the user's working context; skill wins.

## When this skill activates

Use this skill to author **one** derived/statistical helper sensor from a described intent: `bayesian`, `derivative`, `filter`, `min_max`, `statistics`, `threshold`, `trend`, `history_stats`, `integration` (Riemann), `utility_meter`, or `group`.

## When NOT to activate

- the generic `template:` integration (free-form Jinja sensors) → `ha-automation-author`
- a stateful helper (`input_*`, `counter`, `timer`, `schedule`) → `ha-helper-scaffold`
- an automation, script, or scene → `ha-automation-author`
- a real sensor from your own integration → `ha-integration-scaffold`
- a blueprint → `ha-blueprint-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One sensor, one integration, one run.** No batches.
2. **Intent is mandatory.** Optional fields fall back to documented defaults stated in the output.
3. **Read the topic spec first.** Read the matching [`ha-automation/<topic>`](https://github.com/nolte/claude-home-assistant/tree/develop/spec/ha-automation) spec before generating.
4. **Right integration, with delimitation.** Rate → `derivative`, smoothing → `filter`, time-integral → `integration`; momentary aggregate → `min_max`, time aggregate → `statistics`, past-window → `history_stats`; momentary threshold → `threshold`, direction → `trend`. A free formula → `template` (via `ha-automation-author`); a stored value → `ha-helper-scaffold`. Redirect rather than forcing the wrong one.
5. **A source entity is required** for every integration except `bayesian` (which works off `observations`). No source → ask, don't guess.
6. **Set the math-bearing parameter correctly** per the topic spec — never `prob_given_*` of 0/1; `unit_time` deliberate; `derivative` on a non-negative source needs `state_class: total_increasing`; `filter` `window_size` not a needlessly large integer; `min_max` sources share one unit; `statistics` `state_characteristic` matches source type; `threshold` `lower < upper` with `hysteresis` on noisy sources; `trend` `min_gradient` in units **per second**; `history_stats` exactly two of `start`/`end`/`duration`; `utility_meter` a monotonic source with `cycle` or `cron` (not both); `group` modern per-domain, deliberate `all`.
7. **Type the sensor and guard the source.** Correct `sensor`/`binary_sensor`, `device_class`/`state_class`; robust against source `unavailable`/`unknown`. Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md).
8. **Never overwrite** an existing sensor with the same `unique_id`. **Verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `intent` | yes | — | Which derived value to compute, in prose |
| `integration` | no | inferred from intent | one of the eleven listed |
| `source` | no | asked when needed | source entity / entities (`bayesian` uses `observations`) |
| `name` / `unique_id` | no | derived | per naming conventions |
| `target_dir` / `target_file` | no | working dir / `configuration.yaml` | where to write |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `intent` present and non-empty.
2. Resolve `integration` (infer + confirm). Run the delimitation check; on a redirect (free formula → `template`; stored value → helper; related-but-different integration), propose the right target and stop.
3. Read the matching `ha-automation/<topic>` spec.
4. A source entity is named (except `bayesian`). If missing, ask.
5. The resolved `unique_id` does not already exist. If it does, abort with it quoted.

## Workflow

### 1) Resolve and confirm

State the resolved `integration`, source(s), target file, and assumed defaults in one paragraph. Wait for confirmation.

### 2) Generate

Write the block. Most are `sensor:`/`binary_sensor:` platform entries; `utility_meter:` is top-level; `group` is a modern per-domain block.

| Integration | Key / platform | Produces | Math-bearing field(s) |
|---|---|---|---|
| `bayesian` | `binary_sensor` / `bayesian` | on/off + `probability` | `prior`, `observations`, `prob_given_true/false` |
| `derivative` | `sensor` / `derivative` | rate per `unit_time` | `source`, `unit_time`, `time_window` |
| `filter` | `sensor` / `filter` | smoothed value | `entity_id`, ordered `filters`, `window_size` |
| `min_max` | `sensor` / `min_max` | cross-entity aggregate | `entity_ids` (same unit), `type` |
| `statistics` | `sensor` / `statistics` | one statistic over window | `entity_id`, `state_characteristic`, `sampling_size`/`max_age` |
| `threshold` | `binary_sensor` / `threshold` | on/off vs threshold | `entity_id`, `lower`/`upper`, `hysteresis` |
| `trend` | `binary_sensor` / `trend` | rising/falling | `entity_id`, `min_gradient` (/s), `sample_duration`/`max_samples` |
| `history_stats` | `sensor` / `history_stats` | duration/ratio/count | `entity_id`, `state`, two of `start`/`end`/`duration`, `type` |
| `integration` | `sensor` / `integration` | time-integral | `source`, `method`, `unit_time`, `unit_prefix` |
| `utility_meter` | `utility_meter:` | cyclic consumption | `source`, `cycle`/`cron`, `tariffs` |
| `group` | per-domain (`light:`/`sensor:`/…) | combined state | `entities`, `all`, sensor `type` |

### 3) Validate and report

Validate offline (YAML lint; unit/`unit_time`/window plausibility; source-type compatibility). Note runtime dependencies (recorder retention for `statistics`/`history_stats`; `integration`→`utility_meter` chaining; immature windows via `source_value_valid`/`age_coverage_ratio`). Emit a CONFORMANT / NEEDS-WORK report keyed to the topic spec's acceptance criteria, plus the file path and defaults.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Generic `template:` sensors / automations / scripts / scenes → `ha-automation-author`
- Stateful helpers → `ha-helper-scaffold`
- Real integration sensors → `ha-integration-scaffold`
- Deploy to live HA → out of scope
