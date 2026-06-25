# Skill: `ha-automation-solution`

Status: draft

## Context

The three authoring skills `ha-automation-author`, `ha-helper-scaffold`, and `ha-derived-sensor-author` (plus `ha-blueprint-scaffold`) each produce **one** artifact from a narrowly scoped intent. Real-world requirements are rarely a single artifact: "daily heat-pump energy on the dashboard, plus an alert above 10 kWh" is a chain of `integration` (Riemann) → `utility_meter` → `threshold` sensor → `automation`. A user who doesn't know the skills would have to do that decomposition themselves — which integration, which helper, which order, which `entity_id` references which. That mapping burden is exactly what the user should not have to carry.

This skill is the **upstream planning and dispatch layer**: it takes a fuzzy requirement, decomposes it into the minimal combination of artifacts, fixes the dependency order, confirms the plan with the user, and then dispatches the owning authoring skills one after another, threading the `entity_id`s of earlier steps into the inputs of later ones. It generates **no** artifact itself — generation and spec conformance stay with the individual skills.

## Scope

Planning and orchestration across the `ha-automation/` skill family plus `ha-blueprint-scaffold`. One requirement per run → one artifact plan → N dispatched authoring calls → one aggregate report. The skill decides the *combination* (which artifacts, which type per artifact, which order, which wiring), not the content of any single artifact.

## Goals

- Derive the right *combination* of artifacts from a prose requirement, without the user knowing the skill landscape
- Produce a processable artifact plan in dependency order (per entry: artifact, type, owning skill, dependency, purpose) and get it confirmed before any generation
- Dispatch the individual skills in correct order and thread the `entity_id`s/identifiers of earlier artifacts into the inputs of later ones
- Recognize requirements that need a Python custom integration (own device/cloud protocol, polling, config flow) and point at `ha-integration-scaffold` instead of forcing them into helpers/templates
- Deliver an aggregate report naming every produced file and its wiring

## Non-Goals

- Generating a single artifact and its spec conformance — that stays with `ha-automation-author`, `ha-helper-scaffold`, `ha-derived-sensor-author`, `ha-blueprint-scaffold`
- Scaffolding a Python custom integration — that is `ha-integration-scaffold` (the skill only recognizes the need and points)
- Deploying to a running HA instance — generation only
- Its own validation or conformance logic — each dispatched skill validates its own artifact; this skill only aggregates the reports

## Requirements

### Activation triggers

- **MUST** activate on composite, solution-oriented requests where the user describes the result, not the artifact:
  - "I want my heat pump's daily energy on the dashboard and an alert when it's high"
  - "set up presence-based lighting that only runs in the evening"
  - "baue mir eine Lösung, die …", "ich möchte, dass … (mehrteilig)", "richte … ein"
- **SHOULD** not activate when the requirement is clearly a single artifact (the owning individual skill applies directly); when in doubt, this skill plans and proposes a single-artifact plan

### Inputs

- **MUST** capture: `requirement` (prose, the desired result)
- **MAY** capture: `target_dir` / `target_file` hints and existing `entity_id`s to use as sources

### Pre-flight

- **MUST** check `requirement` is non-empty; on underspecification ask 1–3 targeted questions (which source entity, which threshold, which time windows) before planning
- **MUST** check whether the requirement needs a custom integration; if so, mark it in the plan and point at `ha-integration-scaffold` instead of forcing it

### Decomposition heuristic (requirement → artifact type → skill)

- **MUST** map a measured or derived value (rate, smoothing, integral, aggregate, threshold, trend, consumption cycle, probability) to `ha-derived-sensor-author`
- **MUST** map a manually/automation-held state, mode switch, countdown, or weekly plan to `ha-helper-scaffold`
- **MUST** map event→action logic to `ha-automation-author` (`automation`) and a reusable manually-callable action sequence to `script`; an HTTP/shell/python escape-hatch to the matching command artifact of `ha-automation-author`
- **SHOULD** map a reusable, parameterized, shareable pattern to `ha-blueprint-scaffold` rather than a hard-wired `automation`
- **MUST** keep artifacts minimal — never create a helper/sensor a single artifact already covers

### Plan & dispatch

- **MUST** present an artifact plan as a table in dependency order before any generation: per entry `#`, artifact name/`entity_id`, type, owning skill, dependency (`depends-on`), purpose — and wait for explicit confirmation
- **MUST NOT** generate an artifact inline itself; every generation runs through the owning individual skill
- **MUST** dispatch the skills in dependency order and thread the `entity_id`s/identifiers produced in one step into the inputs of dependent steps
- **MUST** stop and report when a dispatched skill returns a NEEDS-WORK report, rather than building on an unfinished predecessor artifact
- **MUST** keep all identifiers consistent across artifacts per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Aggregate report

- **MUST** list, at the end, every produced file path, its artifact, and the wiring (which `entity_id` references which)
- **MUST** relay the aggregated CONFORMANT / NEEDS-WORK reports of the individual skills without re-judging them

### Prohibitions

- **MUST NOT** orchestrate more than one requirement per run
- **MUST NOT** execute a plan without user confirmation
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill asks for missing essentials (source, threshold, time windows) before planning
- [ ] Skill presents an artifact plan in dependency order and waits for confirmation
- [ ] Skill dispatches the owning individual skills instead of generating itself
- [ ] `entity_id`s of earlier artifacts are threaded into the inputs of dependent steps
- [ ] A custom-integration requirement is recognized and pointed at `ha-integration-scaffold`
- [ ] Stops on a NEEDS-WORK predecessor instead of building further
- [ ] Aggregate report lists every file and the wiring and relays the individual reports

## Open questions

- **Agent vs. skill dispatch**: should the individual steps run as skills (visible, sequential) or via a generation agent (isolated, parallel)? Currently skill dispatch, because the plan confirmation and the `entity_id` wiring should stay visible in the user context.
- **Plan persistence**: should the artifact plan be persisted as a file (e.g. under `.plans/`) so an interrupted run is resumable? Currently in-conversation.
- **Existing-config awareness**: should the skill read the existing HA config to suggest source `entity_id`s and catch collisions early? Currently named by the user.
- **Boundary to blueprints**: when is a reusable pattern a blueprint and when an instantiated combination? A heuristic exists (shareable/parameterized → blueprint), but the "once, but generic" edge case stays a judgment call.
