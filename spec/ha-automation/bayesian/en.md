# HA Automation: Using the Bayesian Sensor

Status: draft

## Context

The `bayesian` integration is a **binary-sensor helper** that combines several uncertain signals via Bayesian inference into a single probability and derives an `on`/`off` state from it. Typical use case: "Is the room occupied?" — estimated from motion, the TV's power draw, door state, and time of day, none of which is conclusive on its own. The sensor maintains a baseline probability (`prior`) and updates it for each configured observation using two conditional probabilities, `prob_given_true` and `prob_given_false`.

Unlike the rule engine, the Bayesian integration has an **integration card** in the catalog. Its real classification per the docs is **Binary Sensor / Utility** (helper category) — not a connectable device, but a declarative sensor definition. It is configured as a `binary_sensor` platform in YAML or through the UI helper; the UI path expresses probabilities as percentages (0–100), YAML as fractions (0–1).

This spec turns the official integration docs into a binding convention for plugin-generated Bayesian sensors. It refers to the root spec `ha-automation/automation` (consuming the generated `binary_sensor` entity in triggers/conditions) and to `ha-automation/template` as the deterministic alternative.

Verified source: [`/integrations/bayesian/`](https://www.home-assistant.io/integrations/bayesian/).

## When to Use

Use `bayesian` whenever an `on`/`off` state should be estimated from **several uncertain, mutually independent signals**, none of which is conclusive on its own. Typical use cases:

- **Probable presence/occupancy** — combine "room occupied?" from motion, TV power draw, door state, and time of day (`state`/`numeric_state` observations)
- **Sleep/away inference** — derive a sleep state or "house empty" from several weak cues (lights off, no motion, time of day)
- **Incorporate numeric cues** — feed power draw or brightness via `above`/`below` as a `numeric_state` observation into the probability
- **Template observation** — feed a composite condition as a `value_template` observation (`True`/`False`)
- **Graded logic via `probability`** — read the `probability` attribute (posterior) to react in a graded way below the hard `probability_threshold`

A Bayesian sensor is the right tool as soon as **several weak, uncertain signals** are combined into a probability. For deterministic logic, smoothing, or a single strong signal it is not (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the anatomy of a Bayesian sensor (`prior`, `probability_threshold`, `observations`) as binding
- Fix the three observation types (`state`, `numeric_state`, `template`) and the multi-state pattern with their mandatory probabilities
- Enforce honest, documented probability estimates instead of values tuned backwards to a desired outcome
- Turn the documented pitfalls (avoid `0`/`1` values, multi-state sums, threshold vs. prior) into checkable rules
- Clearly delimit when a Bayesian sensor is **not** the right tool and which building block applies instead

## Non-Goals

- The trigger/condition/action syntax that consumes the generated `binary_sensor` entity — `ha-automation/automation`
- General template syntax in `value_template` — `/docs/configuration/templating/`, only the Bayesian-specific observation contract here
- The naming dimension (`name`, `unique_id`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Smoothing/denoising a noisy sensor stream — `ha-automation/filter`
- Quality-Scale marker — not applicable (usage spec, not an integration-development concept)

## Requirements

### Configuration

- **MUST** define the sensor as a `binary_sensor` platform with `platform: bayesian` and provide a `prior` (float 0–1, required) plus a non-empty `observations` list (required)
- **MUST** give every generated entity a `name` (English, ≤50 chars) and a stable `unique_id` as a snake_case slug so the entity stays UI-customizable (mechanics: `ha/naming-conventions`)
- **SHOULD** set `probability_threshold` (default `0.5`) deliberately; if the threshold is higher than the `prior`, the default state is `off` (documented behavior)
- **MUST** give every observation a `prob_given_true` and `prob_given_false` (both float 0–1, required) — the probability that the observation holds when the event is true vs. false
- **MUST NOT** use `0` or `1` for `prob_given_true`/`prob_given_false` — the docs warn these distort the odds and are rarely true because sensors fail; for extreme estimates use `0.99`/`0.001`, where the number of `9`s/`0`s determines the weight
- **MUST** for `platform: state` provide `entity_id` and `to_state` (target state value)
- **MUST** for `platform: numeric_state` provide `entity_id` and at least one of `above`/`below` (range bounds)
- **MUST** for `platform: template` provide a `value_template` that evaluates to `True`/`False`
- **MUST** for an entity with more than two relevant states/ranges cover **all possible values** as separate observations; the `prob_given_true` of all values must sum to `1`, as must the `prob_given_false` (documented multi-state rule)
- **MAY** set `device_class` to influence the icon/display of the `binary_sensor` entity

### Use in Automations & Templates

- **MUST** trigger/gate on the generated `binary_sensor` entity in automations only via its `on`/`off` state (`state`/`numeric_state` triggers and conditions) — detailed contract in `ha-automation/automation`
- **MAY** read the entity's `probability` attribute (the computed posterior probability) in templates/conditions, e.g. to build graded logic below the hard threshold
- **MAY** use the `observations` attribute for debugging, to trace which observations currently contribute to the probability
- **SHOULD** raise the `probability_threshold` rather than bending observation probabilities when the sensor triggers too easily (documented recommendation)

### Delimitation: When NOT to Use

- **MUST NOT** use a Bayesian sensor for a **deterministic AND/OR combination** of several conclusive signals (e.g. "door open AND alarm armed") — a **template binary sensor** (`ha-automation/template`) is the right construct, because the logic is exact, traceable, and free of probability tuning; Bayes is justified only when the individual signals are **uncertain**
- **MUST NOT** choose `prob_given_true`/`prob_given_false` backwards to force a desired outcome — the docs warn against this explicitly; the values must be **honest** estimates of the conditional probabilities, otherwise the model is worthless
- **SHOULD NOT** use a Bayesian sensor when **a single** reliable signal suffices — the Bayes machinery only adds value when several weak, mutually independent signals are combined; for one strong signal a direct `state` trigger or template sensor is enough
- **SHOULD NOT** try to **smooth a noisy numeric stream** by pressing it into Bayes observations — smoothing/denoising is what the `filter` integration (`ha-automation/filter`) is for; Bayes yields a binary inference, not a smoothed measurement series
- **SHOULD NOT** feed strongly **correlated** signals as independent observations (e.g. two motion sensors that almost always fire together) — Bayes treats observations as conditionally independent, and double-counted correlation overestimates the probability

## Acceptance Criteria

- [ ] The sensor is defined as a `binary_sensor` platform `bayesian` with `prior` (0–1) and a non-empty `observations` list
- [ ] Every entity carries an English `name` ≤50 chars and a stable snake_case `unique_id`
- [ ] `probability_threshold` is set deliberately (default `0.5` only where intended)
- [ ] Every observation has `prob_given_true` and `prob_given_false`; none of the values is `0` or `1`
- [ ] Observation-type-specific required fields are set (`state`: `entity_id`+`to_state`; `numeric_state`: `entity_id`+`above`/`below`; `template`: `value_template`)
- [ ] For multi-state entities all values are covered and the `prob_given_true`/`prob_given_false` each sum to `1`
- [ ] The probabilities are honest estimates, not tuned backwards to a desired outcome
- [ ] The "when NOT to use" delimitation holds: no Bayes for deterministic logic (template), smoothing (filter), or a single strong signal
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Independence assumption**: Bayes presupposes conditional independence of the observations, and the docs anchor no dedicated warning on this. Should this spec carry a hard rule against obviously correlated observations, or stay with the SHOULD NOT recommendation?
