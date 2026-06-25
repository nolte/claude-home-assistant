# Skill: `ha-derived-sensor-author`

Status: draft

## Context

Home Assistant ships a number of prefabricated integrations that compute a derived or statistical sensor from existing entities — `bayesian`, `derivative`, `filter`, `min_max`, `statistics`, `threshold`, `trend`, `history_stats`, `integration` (Riemann sum), `utility_meter`, and `group`. They are the right answer when a user needs a rate, a smoothing, an aggregation, a threshold, a trend, a consumption period, or a probability — instead of hand-writing this math into a `template` (which knows nothing of the temporal history) or pouring it into an automation (which caches in `input_*`). The `ha-automation/` corpus describes each of these integrations, but so far no skill operationalizes them. Typical mistakes: setting `prob_given_true`/`prob_given_false` to 0/1 (breaks Bayes), forgetting `state_class: total_increasing` on the source of a `derivative`, an overly large integer `window_size` on the `filter` (DB load at start), putting a fluctuating source into a `utility_meter`, or `min_max` sources with differing units (→ `ERR`).

This skill authors **one** derived/statistical sensor from a described intent as spec-conformant YAML, chooses the right integration (and delimits it against the related ones), and delivers a conformance report.

## Scope

Generation of exactly one derived sensor per run from: `bayesian`, `derivative`, `filter`, `min_max`, `statistics`, `threshold`, `trend`, `history_stats`, `integration`, `utility_meter`, `group`. The skill determines the integration (or asks), reads the responsible `ha-automation/<topic>` spec, and writes the block as a `sensor:`/`binary_sensor:` platform entry, as a top-level `utility_meter:`, or as a modern domain-specific `group` in `configuration.yaml` (or a `packages/` file).

## Goals

- Choose the right derived/statistical integration from a prose intent and write it as a spec-conformant YAML block
- Set the math-bearing parameter per integration correctly (`observations`/`prob_given_*`, `unit_time`/`time_window`, `filters`/`window_size`, `state_characteristic`, `lower`/`upper`/`hysteresis`, `min_gradient`/`sample_duration`, `start`/`end`/`duration`, `method`, `cycle`/`tariffs`, `type`)
- Sharply delimit the integrations against each other (rate vs. smoothing vs. integral; instantaneous aggregate vs. time aggregate vs. history; threshold vs. trend)
- Type the produced sensor correctly (`sensor` vs. `binary_sensor`, `device_class`/`state_class`) and make it robust against source `unavailable`/`unknown`
- Point out dependencies (recorder retention for `statistics`/`history_stats`; `integration` as the typical source of a `utility_meter`)

## Non-Goals

- The generic `template:` integration (free-form Jinja sensors) — that is `ha-automation-author`
- State helpers (`input_*`, `counter`, `timer`, `schedule`) — that is `ha-helper-scaffold`
- Automations/scripts/scenes — `ha-automation-author`
- Real sensors from an own integration — `ha-integration-scaffold`
- Blueprints — `ha-blueprint-scaffold`
- Deployment into a running HA instance — generation only

## Requirements

### Activation triggers

- **MUST** activate on the following phrases:
  - "add a sensor for the rate of change / energy from power / moving average / threshold / trend of …"
  - "make a utility_meter / statistics sensor / bayesian binary_sensor / min_max sensor for …"
  - "erstelle einen Sensor für die Änderungsrate / den Verbrauch / den gleitenden Mittelwert / die Schwelle von …"

### Inputs

- **MUST** capture: `intent` (prose, which derived value should be computed)
- **MAY** capture: `integration` (`bayesian` / `derivative` / `filter` / `min_max` / `statistics` / `threshold` / `trend` / `history_stats` / `integration` / `utility_meter` / `group`); when absent, the skill derives it from the intent and confirms it
- **MAY** capture: `source` (source entity/entities), `name`/`unique_id`, `target_dir`, `target_file` (default `configuration.yaml`)

### Pre-flight (in order, abort on first failure)

- **MUST** check `intent` is non-empty
- **MUST** resolve the integration and check it against the delimitation rules: if the intent demands a free formula (→ `template` via `ha-automation-author`), a stored state (→ `ha-helper-scaffold`), or a related but different integration (rate instead of smoothing etc.), the skill **MUST** redirect
- **MUST** read the responsible `ha-automation/<topic>` spec
- **MUST** check that a source entity is named (except `bayesian`, which works via `observations`); without a source, abort and ask back
- **MUST NOT** overwrite an existing sensor with the same `unique_id`

### Generation rules (per integration, from the respective spec)

- **MUST** for `bayesian` set `prior` and a complete `observations` list, `prob_given_true`/`prob_given_false` never to 0 or 1, and for multi-state observations sum the probabilities each to 1.0
- **MUST** for `derivative` and `integration` choose `unit_time` deliberately; for `derivative` on non-negative sources require `state_class: total_increasing` on the source; for `integration` choose `method` to match the source characteristic
- **MUST** for `filter` set the `filters` stages in a deliberate order and choose `window_size` deliberately (time format vs. integer; no unnecessarily large integer value → startup DB load)
- **MUST** for `min_max` ensure the same unit across all sources and choose `type` from the catalog
- **MUST** for `statistics` choose a `state_characteristic` matching the source type (numeric vs. binary) and define a window via `sampling_size` and/or `max_age`
- **MUST** for `threshold` set at least `lower` or `upper` (with both, `lower < upper`) and set `hysteresis` for noisy sources
- **MUST** for `trend` express `min_gradient` in unit **per second** and adapt `sample_duration`/`max_samples` to the update frequency
- **MUST** for `history_stats` set exactly two of `start`/`end`/`duration`, a `state` matching the source, and DST-safe templates (`today_at()`, `timedelta()`); keep the window within the recorder retention
- **MUST** for `utility_meter` require a monotonically increasing source, choose `cycle` (or `cron`, not both), and set `delta_values`/`periodically_resetting`/`net_consumption` to the source reality; tariff switch via `select.select_option`
- **MUST** for `group` use modern domain-specific groups instead of the old `group:` YAML, set members of one domain, `all` (OR vs. AND) deliberately, and for sensor groups assign `type`/`ignore_non_numeric`
- **MUST** type the produced sensor correctly and make it robust against source `unavailable`/`unknown`
- **MUST** name all identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate the artifact offline (YAML lint; plausibility of unit/`unit_time`/window; source-type compatibility) and name violations
- **MUST** point out runtime dependencies (recorder retention, `integration`→`utility_meter` chaining, immature windows via `source_value_valid`/`age_coverage_ratio`)
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the responsible spec's acceptance criteria, plus file path and defaults

### Prohibitions

- **MUST NOT** produce more than one sensor per run
- **MUST NOT** output a free Jinja formula as a derived sensor when a dedicated integration fits (or conversely a dedicated integration where only `template` fits)
- **MUST NOT** deploy into a running HA instance

## Acceptance criteria

- [ ] Skill derives the integration (or asks for it) and confirms it
- [ ] Skill reads the responsible `ha-automation/<topic>` spec before generation
- [ ] The math-bearing parameter is set correctly per integration (see generation rules)
- [ ] The produced sensor is typed correctly (`sensor`/`binary_sensor`, `device_class`/`state_class`) and robust against source `unavailable`/`unknown`
- [ ] An intent targeting a free formula or a stored state is redirected
- [ ] The report names runtime dependencies (recorder retention, `integration`→`utility_meter`)
- [ ] Skill delivers a CONFORMANT / NEEDS-WORK report with file path and defaults

## Open questions

- **Chaining `integration` → `utility_meter`**: Should the skill, for "daily electricity consumption from power", produce both sensors in one run (Riemann integral + utility-meter cycle) or strictly one per run? Currently one per run, with a note on the chaining.
- **`group` special case**: `group` is less a "sensor" than a domain aggregate. Does it stay in this skill or rather belong to an entity-group skill? Currently here, because sensor groups share the derived-aggregate semantics.
- **Validation depth**: When is a real `ha core check` against a temporary config worthwhile instead of static plausibility checking?
