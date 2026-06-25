---
name: ha-automation-solution
description: Plan and orchestrate a complete Home Assistant YAML solution from a result-oriented requirement, so the user never has to pick which authoring skill to use. Decomposes the requirement into the minimal combination of artifacts across the ha-automation skill family, presents a dependency-ordered artifact plan for approval, then dispatches ha-automation-author, ha-helper-scaffold, ha-derived-sensor-author, and ha-blueprint-scaffold in order — threading entity_ids between steps — and flags requirements that actually need a custom integration. Activate on "I want my heat pump's daily energy on the dashboard and an alert when it's high", "set up presence-based lighting that only runs in the evening", "baue mir eine Lösung, die…", "richte… ein". Do not activate for a single clear artifact (let the owning skill handle it), Python custom integrations (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, automation, orchestration, planning]
---

# HA Automation Solution

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-automation-solution/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-automation-solution/en.md).

This skill is the **front door** to the `ha-automation` skill family. It does not generate any artifact itself — it decomposes the requirement, plans the combination, and dispatches the owning authoring skills, each of which owns its generation and spec conformance.

## Why this is a skill, not an agent

- **Plan-before-generate gate** — the artifact plan must be presented and explicitly approved before any generation; that human-visible gate is core to the contract and an agent's fire-and-forget shape would lose it.
- **Mid-flow interactivity** — clarifying questions, plan confirmation, and the "this actually needs a custom integration" decision are per-run dialogues.
- **Orchestrator that dispatches other skills** — the skill-orchestrates-skill default (see `skill-vs-agent`) keeps the entry point in skill form, like `ha-blueprint-scaffold` dispatching `ha-blueprint-author`.
- Counter-dimension considered: the per-artifact generation could run as parallel agents, but the plan approval and the entity_id threading must stay visible in the user's context; skill wins.

## When this skill activates

Use this skill when the user describes a **result** that likely needs more than one artifact, and should not have to know which authoring skill produces what.

## When NOT to activate

- a single clear artifact (one automation, one helper, one sensor, one blueprint) → let the owning skill activate directly
- a Python custom integration (own device/cloud protocol, polling, config flow) → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **Never generate inline.** Every artifact is produced by its owning skill — `ha-automation-author`, `ha-helper-scaffold`, `ha-derived-sensor-author`, or `ha-blueprint-scaffold`. This skill plans and dispatches; it does not write artifacts.
2. **Plan before generate.** Always present the dependency-ordered artifact plan and wait for explicit approval before dispatching anything.
3. **One requirement, one run.** No multi-requirement batches.
4. **Minimal artifacts.** Decompose to the fewest artifacts that satisfy the requirement; never add a helper or sensor a single artifact already covers.
5. **Thread identities.** Dispatch in dependency order and pass the `entity_id`s/identifiers produced in earlier steps as inputs to dependent steps. Keep all names consistent per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md).
6. **Stop on NEEDS-WORK.** If a dispatched skill returns NEEDS-WORK, stop and report — do not build a dependent artifact on an unfinished predecessor.
7. **Recognize integration-shaped work.** When the requirement needs a custom integration rather than YAML, say so in the plan and point at `ha-integration-scaffold` instead of forcing it into helpers/templates.
8. **Verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `requirement` | yes | — | The desired result, in prose |
| `target_dir` / `target_file` | no | working dir | passed through to dispatched skills |
| `known_sources` | no | asked when needed | existing `entity_id`s to use as sources |

## Decomposition heuristic (requirement → artifact type → skill)

| The requirement needs… | Artifact | Owning skill |
|---|---|---|
| a measured/derived value (rate, smoothing, integral, aggregate, threshold, trend, consumption cycle, probability) | derived/statistical sensor | `ha-derived-sensor-author` |
| a manually/automation-held state, mode switch, countdown, weekly plan | `input_*` / `counter` / `timer` / `schedule` | `ha-helper-scaffold` |
| event→action logic | `automation` | `ha-automation-author` |
| a reusable manually-callable action sequence | `script` | `ha-automation-author` |
| an HTTP / shell / python escape-hatch | `rest_command` / `shell_command` / `python_script` | `ha-automation-author` |
| a reusable, parameterized, shareable pattern | blueprint | `ha-blueprint-scaffold` |
| an own device/cloud protocol, polling, config flow | custom integration | **out of scope** → `ha-integration-scaffold` |

## Workflow

### 1) Clarify

If the requirement is underspecified, ask 1–3 targeted questions (which source entity, which threshold, which time windows) before planning. Do not plan on guesses.

### 2) Plan

Decompose into a dependency-ordered artifact plan and present it as a table:

```markdown
| # | Artifact / entity_id | Type | Skill | Depends on | Purpose |
|---|---|---|---|---|---|
| 1 | sensor.heat_pump_energy | integration | ha-derived-sensor-author | — | Riemann power→energy |
| 2 | sensor.heat_pump_energy_daily | utility_meter | ha-derived-sensor-author | #1 | daily cycle |
| 3 | binary_sensor.heat_pump_energy_high | threshold | ha-derived-sensor-author | #2 | > 10 kWh |
| 4 | automation.heat_pump_energy_alert | automation | ha-automation-author | #3 | notify |
```

State any custom-integration finding here. Wait for explicit approval.

### 3) Dispatch

Invoke each owning skill in plan order, passing the `entity_id`s resolved in earlier steps as inputs to the dependent steps. After each, check the returned report; stop on NEEDS-WORK.

### 4) Aggregate report

List every produced file, its artifact, and the wiring (which `entity_id` references which). Relay each dispatched skill's CONFORMANT / NEEDS-WORK report verbatim — do not re-judge them. Do not deploy.

## Boundaries

- Single-artifact generation + spec conformance → the owning authoring skill
- Custom integration → `ha-integration-scaffold` (this skill only recognizes and points)
- Deploy to live HA → out of scope
