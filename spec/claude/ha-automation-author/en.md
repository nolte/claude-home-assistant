# Skill: `ha-automation-author`

Status: draft

## Context

The `ha-automation/` spec corpus describes how Home Assistant's YAML-based automation building blocks are *used* — `automation`, `script`, `scene`, the `template` integration (generic Jinja entities), the command escape hatches `rest_command` / `shell_command` / `python_script`, and the anti-pattern guide `legacy-trigger-helpers`. So far there is no skill that operationalizes these specs: users hand-write automations and trip over the same recurring mistakes — wrong `mode`, missing stable `id`/`unique_id`, unguarded templates against `unavailable` sources, shell injection in `shell_command`, `import` in the sandboxed `python_script`, or they reach for legacy helpers that are neither UI-editable nor shareable.

This skill authors **one** automation artifact from a described intent as spec-conformant YAML (or `.py` for `python_script`), validates it offline, and delivers a conformance report. It is the non-blueprint sibling of the `ha-blueprint-author` agent: blueprints parameterize an automation for sharing; this skill writes the concrete, instantiated automation for one's own HA instance.

## Scope

Generation of exactly one artifact per run from the logic/command part of `ha-automation/`: an `automation`, a `script`, a `scene`, a `template` integration entity (Jinja `sensor`/`binary_sensor`/actor), or a `rest_command` / `shell_command` / `python_script`. The skill determines the artifact type (or asks), reads the responsible `ha-automation/<topic>` spec, writes the artifact to the right place (`automations.yaml`, `scripts.yaml`, `scenes.yaml`, a `packages/` file, `configuration.yaml`, or `python_scripts/<name>.py`), and validates.

## Goals

- Produce a single, spec-conformant automation artifact from a prose intent that satisfies every MUST rule of the responsible `ha-automation/<topic>` spec
- Deliberately choose the artifact type (automation vs. script vs. scene vs. template entity vs. command) and justify the choice in the output — the specs draw sharp boundaries between these types
- Actively prevent the typical anti-patterns: blind `mode: single`, missing `id`/`unique_id`, unguarded templates, shell injection, `import` in `python_script`, legacy trigger helpers
- Guard templates against `unavailable`/`unknown` (`has_value()`, `is_number()`, `float(default)`, `availability`)
- Validate the artifact offline and deliver a CONFORMANT / NEEDS-WORK report against the spec's acceptance criteria

## Non-Goals

- Parameterized, shareable blueprints — that is `ha-blueprint-scaffold` / `ha-blueprint-author`
- State helpers (`input_*`, `counter`, `timer`, `schedule`) — that is `ha-helper-scaffold`
- Derived/statistical helper sensors (`bayesian`, `derivative`, `filter`, `min_max`, `statistics`, `threshold`, `trend`, `history_stats`, `integration`, `utility_meter`, `group`) — that is `ha-template-sensor-author`
- Python custom integrations — that is `ha-integration-scaffold`
- Deployment into a running HA instance — generation only; deploy is `ha-integration-deploy` / manual
- Migrating an existing automation into a blueprint — `ha-blueprint-scaffold`

## Requirements

### Activation triggers

- **MUST** activate on the following phrases:
  - "write an automation that …", "create a script for …", "add a scene for …"
  - "make a template sensor that …" (generic Jinja entity, not a statistics helper)
  - "add a rest_command / shell_command / python_script for …"
  - "schreibe eine Automation, die …", "erstelle ein Script für …", "lege eine Szene für … an"

### Inputs

- **MUST** capture: `intent` (prose, what the artifact should do) — no intent, no run
- **MAY** capture: `artifact_type` (`automation` / `script` / `scene` / `template` / `rest_command` / `shell_command` / `python_script`); when absent, the skill derives it from the intent and confirms it
- **MAY** capture: `target_dir` (repo/config root; default working directory) and `target_file` (default per type: `automations.yaml` / `scripts.yaml` / `scenes.yaml` / `configuration.yaml` / `python_scripts/<name>.py`)

### Pre-flight (in order, abort on first failure)

- **MUST** check `intent` is non-empty; otherwise ask back instead of generating
- **MUST** resolve the artifact type and check it against the `legacy-trigger-helpers` spec: if the intent targets a legacy helper (`flux`, `device_sun_light_trigger`, hand-built `platform:` trigger helpers), the skill **MUST** propose the modern alternative instead of generating the legacy path
- **MUST** read the responsible `ha-automation/<topic>` spec before generating
- **MUST NOT** overwrite an existing target entity; on a collision of `id`/`unique_id`/`object_id`, abort with the quoted identifier

### Generation rules (per type, from the respective spec)

- **MUST** for `automation` and `script` choose the `mode` deliberately (not blindly `single`), set an appropriate `max` for `parallel`/`queued`, and justify a `max_exceeded: silent`; use the modern plural syntax (`triggers`/`conditions`/`actions`); give every automation a stable `id` and an English `alias` (≤ 50 characters)
- **MUST** for `script` express public parameters via `fields` with selectors and separate internal values via `variables`
- **MUST** for `scene` set attributes only in the nested `state:` form, never attach them to a scalar state value
- **MUST** for `template` use the modern `template:` block form (never `platform: template`), give every entity a stable `unique_id`, and guard every template against `unavailable`/`unknown` (`has_value()`, `is_number()`, `float(default)`, `availability`)
- **MUST** for `rest_command` set `verify_ssl: false` only with a documented justification and carry credentials via `username`/`password`/`authentication` instead of in the URL
- **MUST** for `shell_command` never interpolate untrusted input unquoted (shell injection runs as root), use no pipes/redirects in the template, and check the `returncode` via `response_variable`
- **MUST** for `python_script` work without `import`, use only the provided objects (`hass`, `data`, `logger`, `output`), and log via `logger` instead of `print`
- **MUST** name all identifiers (`id`, `object_id`, `unique_id`, `alias`, service names) per `ha/naming-conventions` (snake_case IDs, English display names)
- **MUST** verify HA internals against the official docs instead of from memory (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate the artifact offline (YAML lint; where possible `ha core check`; mentally walk through template rendering with `unavailable`/`unknown` sources) and name violations
- **MUST** deliver a CONFORMANT / NEEDS-WORK report that traces each point back to an acceptance criterion of the responsible `ha-automation/<topic>` spec
- **MUST** name the written file path and every assumed default in the output

### Prohibitions

- **MUST NOT** produce multiple artifacts per run (one artifact, one type, one run)
- **MUST NOT** generate a legacy trigger helper when a modern alternative exists
- **MUST NOT** deploy into a running HA instance

## Acceptance criteria

- [ ] Skill derives the artifact type (or asks for it) and confirms it before generation
- [ ] Skill reads the responsible `ha-automation/<topic>` spec before generation
- [ ] `automation`/`script` carry a deliberately chosen `mode` (with `max` for `parallel`/`queued`), a stable `id`, and an English `alias`
- [ ] `template` entities carry a `unique_id` and templates guarded against `unavailable`/`unknown`
- [ ] `shell_command`/`python_script` violate no sandbox/injection rule (no unquoted input, no `import`)
- [ ] An intent targeting a legacy helper is redirected to the modern alternative
- [ ] Skill delivers a CONFORMANT / NEEDS-WORK report with file path and assumed defaults

## Open questions

- **Packages layout**: Should the skill write into `automations.yaml`/`scripts.yaml` by default or prefer a `packages/<name>.yaml` that bundles automation + associated helpers? Currently default per type, `packages/` on request.
- **Validation depth**: When is a real `ha core check` against a temporary config worthwhile instead of static YAML/template checking?
- **Agent offload**: Should the draft-validate-iterate loop be offloaded into a `ha-automation-author` agent like for blueprints, or does generation stay inline in the skill?
- **`template` delimitation**: The generic `template:` integration also produces sensors — the boundary to `ha-template-sensor-author` (prefabricated statistics helpers) is conceptual, not syntactic. Is the description sufficient for a clean separation?
