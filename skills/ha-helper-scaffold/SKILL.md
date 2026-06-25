---
name: ha-helper-scaffold
description: Scaffold one Home Assistant stateful helper entity as a spec-conformant YAML block from a described intent — input_boolean, input_button, input_datetime, input_number, input_select, input_text, counter, timer, or schedule — conforming to the matching spec/ha-automation/<topic>. Picks the right helper type, sets every mandatory field (min/max, options, has_date/has_time, duration, weekly windows, restore), redirects measured/derived values to a sensor, names per ha/naming-conventions, and reports the helper's state, trigger events, and mutating services. Activate on "add an input_number/input_select helper for…", "create a timer/counter/schedule for…", "lege einen Helfer für… an". Do not activate for automations/scripts/scenes (ha-automation-author), derived/statistical sensors (ha-derived-sensor-author), real integration sensors, blueprints (ha-blueprint-scaffold), or deploying to a live HA instance.
tags: [home-assistant, helper, input, yaml, scaffolding]
---

# HA Helper Scaffold

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-helper-scaffold/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-helper-scaffold/en.md).

## Why this is a skill, not an agent

- **Human-visible scaffolding surface** — the user describes what state they need held and reads back the YAML block plus the helper's read/mutate surface; a skill keeps this on the visible command surface, like the sibling scaffold skills.
- **Mid-flow interactivity** — helper-type confirmation and the measured-value redirect are per-run dialogues the user approves before scaffolding.
- **Bounded, inline generation** — a single helper block is small enough to generate inline; no isolated agent context is needed.
- Counter-dimension considered: a one-shot generator could be an agent, but the type decision and the reported surface belong in the user's working context; skill wins.

## When this skill activates

Use this skill to scaffold **one** stateful helper entity from a described intent: `input_boolean`, `input_button`, `input_datetime`, `input_number`, `input_select`, `input_text`, `counter`, `timer`, or `schedule`.

## When NOT to activate

- an automation, script, scene, template entity, or command integration → `ha-automation-author`
- a derived/statistical helper sensor (`bayesian`, `derivative`, … `utility_meter`, `group`) → `ha-derived-sensor-author`
- a measured value from real hardware → belongs in an integration, not an input helper
- a blueprint → `ha-blueprint-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One helper, one type, one run.** No multi-helper batches.
2. **Intent is mandatory.** Without it there is no scaffold; optional fields fall back to documented defaults stated in the output.
3. **Read the topic spec first.** Read the matching [`ha-automation/<topic>`](https://github.com/nolte/claude-home-assistant/tree/develop/spec/ha-automation) spec before scaffolding.
4. **Right helper, not the convenient one.** If the intent targets a measured value (→ sensor/integration), a derived value (→ `ha-derived-sensor-author`), or behavior another helper carries better (one-shot press → `input_button`, not `input_boolean`), redirect instead of scaffolding the wrong helper.
5. **Never overwrite an existing helper** with the same `object_id`. Abort with the id quoted.
6. **Mandatory fields are mandatory.** `input_number` → `min`+`max`; `input_select` → non-empty `options`; `input_datetime` → at least one of `has_date`/`has_time`; `input_text` → `max` ≤ 255; `timer` → `restore: true` when it must survive a restart; `schedule` → per-weekday `from`/`to` windows. Set `initial` only for a fixed start value, else document restore semantics.
7. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md).** `object_id` snake_case; English display names ≤ 50 chars.
8. **Verify HA internals against the official docs** — don't reproduce schemas from memory (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `intent` | yes | — | What state the helper should hold / do, in prose |
| `helper_type` | no | inferred from intent | one of the nine helper domains |
| `object_id` | no | derived (`snake_case`) | the entity slug |
| `target_dir` / `target_file` | no | working dir / `configuration.yaml` | where to write |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `intent` present and non-empty.
2. Resolve `helper_type` (infer + confirm). Run the delimitation check (measured → sensor, derived → template/statistics, wrong-helper → redirect); on a redirect, propose the right target and stop.
3. Read the matching `ha-automation/<topic>` spec.
4. The resolved `object_id` does not already exist. If it does, abort with it quoted.

## Workflow

### 1) Resolve and confirm

State the resolved `helper_type`, `object_id`, target file, and assumed defaults in one paragraph. Wait for confirmation.

### 2) Scaffold

Write the block under the top-level key, with mandatory + deliberate-default fields:

| Helper | Key | Mandatory / load-bearing fields |
|---|---|---|
| `input_boolean` | `input_boolean:` | `object_id`; optional `name`/`icon`/`initial` |
| `input_button` | `input_button:` | `object_id` (stateless; state = last-press timestamp) |
| `input_datetime` | `input_datetime:` | ≥1 of `has_date`/`has_time` |
| `input_number` | `input_number:` | `min`, `max`; deliberate `mode`/`step`/`unit_of_measurement` |
| `input_select` | `input_select:` | non-empty `options` |
| `input_text` | `input_text:` | `max` ≤ 255; `mode: password` for masked, never for secrets |
| `counter` | `counter:` | integer-only; `initial`/`step`/`minimum`/`maximum`/`restore` |
| `timer` | `timer:` | `duration`; `restore: true` for restart survival |
| `schedule` | `schedule:` | per-weekday `from`/`to` window lists |

### 3) Report

State the written block, file path, and defaults. Always report the helper's **read/mutate surface**: relevant state/attributes, trigger events (e.g. `timer.finished`, `counter.maximum_reached`, `schedule.turned_on`), and mutating services (e.g. `input_number.set_value`, `counter.increment`). Emit a CONFORMANT / NEEDS-WORK report keyed to the topic spec's acceptance criteria.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Gotchas

- **`timer` defaults to `restore: false`** — a timer that must survive a restart needs `restore: true`; and a timer that expires while HA is down does **not** fire `timer.finished` retroactively, so critical logic needs an extra state check on startup.
- **`input_text` is not secret storage** — its value is cleartext in state, history, and the API; `mode: password` only masks the UI field.
- **A set `initial` overrides state restoration on every start** — omit it to let the last user-set value persist.

## Boundaries

- Automations / scripts / scenes / templates / commands → `ha-automation-author`
- Derived / statistical sensors → `ha-derived-sensor-author`
- Real sensors/actuators → an integration (`ha-integration-scaffold`)
- Deploy to live HA → out of scope
