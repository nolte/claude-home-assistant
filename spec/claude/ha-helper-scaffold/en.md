# Skill: `ha-helper-scaffold`

Status: draft

## Context

Home Assistant knows a family of stateful helper entities that are configured purely in YAML (or via the UI): `input_boolean`, `input_button`, `input_datetime`, `input_number`, `input_select`, `input_text`, `counter`, `timer`, and `schedule`. They hold state set manually or by automation and are the building blocks with which automations express mode switches, thresholds, time windows, countdowns, and counters. The `ha-automation/` corpus describes the correct use per helper, but so far there is no skill that scaffolds them. In practice users reach for the wrong helper (an `input_boolean` for a one-shot press instead of `input_button`, an `input_number` for a measured quantity instead of a sensor), omit mandatory fields (`min`/`max` for `input_number`, `options` for `input_select`, `has_date`/`has_time` for `input_datetime`), or forget `restore: true` on the `timer`.

This skill scaffolds **one** state helper from a described intent as a spec-conformant YAML block, chooses the right helper type (and redirects to the right one when the intent demands another), and delivers a conformance report.

## Scope

Generation of exactly one helper block per run from the state-helper family: `input_boolean`, `input_button`, `input_datetime`, `input_number`, `input_select`, `input_text`, `counter`, `timer`, `schedule`. The skill determines the helper type (or asks), reads the responsible `ha-automation/<topic>` spec, and writes the block under the matching top-level key in `configuration.yaml` (or a `packages/` file).

## Goals

- Choose the right state helper from a prose intent and scaffold it as a spec-conformant YAML block
- Set all mandatory fields per helper (`min`/`max`, `options`, `has_date`/`has_time`, `duration`, weekly windows) and sensible defaults for optional fields
- Sharply delimit the helpers against each other: measured vs. set values, one-shot press vs. persistent state, countdown vs. weekly schedule
- Name `object_id`/alias per `ha/naming-conventions` (snake_case, English display names ≤ 50 characters)
- Name each helper's state/event/service surface in the output so automations know how to read and mutate it

## Non-Goals

- Automations, scripts, scenes, template entities, or command integrations — that is `ha-automation-author`
- Derived/statistical helper sensors (`bayesian`, `derivative`, … `utility_meter`, `group`) — that is `ha-derived-sensor-author`
- Real sensors/actors from an integration — measured values belong in an integration, not an input helper
- Blueprints — `ha-blueprint-scaffold`
- Deployment into a running HA instance — generation only

## Requirements

### Activation triggers

- **MUST** activate on the following phrases:
  - "add an input_number / input_select / input_boolean helper for …"
  - "create a timer / counter / schedule for …"
  - "I need a helper to hold / toggle / count / schedule …"
  - "lege einen Helfer für … an", "erstelle einen Timer / Zähler / Wochenplan für …"

### Inputs

- **MUST** capture: `intent` (prose, what the helper should hold/do)
- **MAY** capture: `helper_type` (`input_boolean` / `input_button` / `input_datetime` / `input_number` / `input_select` / `input_text` / `counter` / `timer` / `schedule`); when absent, the skill derives it from the intent and confirms it
- **MAY** capture: `object_id`, `target_dir`, `target_file` (default `configuration.yaml`)

### Pre-flight (in order, abort on first failure)

- **MUST** check `intent` is non-empty
- **MUST** resolve the helper type and check it against the delimitation rules: if the intent targets a measured value (→ sensor/integration), a derived value (→ template/statistics sensor), or a behavior that another helper carries better, the skill **MUST** redirect instead of scaffolding the wrong helper
- **MUST** read the responsible `ha-automation/<topic>` spec
- **MUST NOT** overwrite an existing helper with the same `object_id`

### Scaffold rules (per helper, from the respective spec)

- **MUST** for `input_number` set `min` and `max`, choose `mode` (`slider`/`box`) and `step` deliberately
- **MUST** for `input_select` set a non-empty `options` list
- **MUST** for `input_datetime` set at least one of `has_date`/`has_time`
- **MUST** for `input_text` keep `max` ≤ 255 (HA state limit) and not misuse it for secrets (cleartext in state/history/API)
- **MUST** for `timer` set `restore: true` when the timer should survive a restart, and note in the report the behavior of timers that expired during downtime
- **MUST** for `schedule` set a `from`/`to` window list per used weekday
- **MUST** for `counter` deliberately assign `initial`/`step`/`minimum`/`maximum`/`restore` (integer-only)
- **MUST** set `initial` only when a fixed start value is wanted; otherwise document the restore semantics (a set `initial` overrides restoration on every start)
- **MUST** name all identifiers per `ha/naming-conventions`
- **MUST** verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Report

- **MUST** name the written block, the file path, and every default
- **MUST** state the helper's read/mutation surface: relevant state/attributes, trigger events (e.g. `timer.finished`, `counter.maximum_reached`, `schedule.turned_on`) and mutating services (e.g. `input_number.set_value`, `counter.increment`)
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the responsible spec's acceptance criteria

### Prohibitions

- **MUST NOT** scaffold more than one helper per run
- **MUST NOT** propose an input helper for a measured or derived value
- **MUST NOT** deploy into a running HA instance

## Acceptance criteria

- [ ] Skill derives the helper type (or asks for it) and confirms it
- [ ] Skill reads the responsible `ha-automation/<topic>` spec before the scaffold
- [ ] Every helper carries its mandatory fields (`min`/`max`, `options`, `has_date`/`has_time`, `duration`/windows)
- [ ] A `timer` with a restart requirement carries `restore: true`
- [ ] An intent targeting a measured/derived value is redirected to sensor/template/statistics
- [ ] The report names the helper's state, trigger events, and mutating services
- [ ] Skill delivers a CONFORMANT / NEEDS-WORK report with file path and defaults

## Open questions

- **UI vs. YAML helpers**: HA also allows the same helpers via UI (Settings → Devices & Services → Helpers). Should the skill scaffold YAML only or also document the UI path? Currently YAML-only.
- **Bundling with consumer**: Should the skill optionally write the helper together with the automation that uses it into a `packages/<name>.yaml`? Currently one helper per run, bundling via `ha-automation-author`.
- **`restore` default**: `timer` defaults to `restore: false`, `counter` to `true`. Should the skill actively propose `timer.restore: true` when the intent suggests persistence? Currently yes (MUST on restart requirement).
