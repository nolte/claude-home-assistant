---
name: ha-automation-author
description: Author one Home Assistant automation-logic or command artifact as spec-conformant YAML (or a sandboxed .py) from a described intent — an automation, script, scene, generic template entity, or a rest_command / shell_command / python_script — conforming to the matching spec/ha-automation/<topic>. Picks the artifact type, enforces a deliberate mode, stable id/unique_id, unavailable-guarded templates, shell-injection and python-sandbox safety, redirects legacy trigger helpers to modern equivalents, validates offline, and returns a conformance report. Activate on "write an automation that…", "create a script for…", "add a scene/template sensor/rest_command for…", "schreibe eine Automation, die…", "erstelle ein Script für…". Do not activate for blueprints (ha-blueprint-scaffold), stateful helpers (ha-helper-scaffold), derived/statistical sensors (ha-template-sensor-author), Python custom integrations (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, automation, script, scene, yaml]
---

# HA Automation Author

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-automation-author/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-automation-author/en.md).

## Why this is a skill, not an agent

- **Human-visible authoring surface** — the user describes an intent and reads back the generated YAML and the conformance report; a skill keeps that on the visible command surface, like the sibling `ha-blueprint-scaffold`.
- **Mid-flow interactivity** — artifact-type confirmation and the legacy-helper redirect are per-run dialogues the user must see and approve before generation.
- **Orchestrator-leaning** — it may later dispatch a generation agent (as `ha-blueprint-scaffold` dispatches `ha-blueprint-author`); the skill-orchestrates default keeps the entry point in skill form.
- Counter-dimension considered: the draft→validate→iterate loop could be an agent, but the type decision and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill to author **one** non-blueprint automation-logic or command artifact from a described intent: an `automation`, `script`, `scene`, generic `template` entity, or a `rest_command` / `shell_command` / `python_script`.

## When NOT to activate

- a parameterized, shareable blueprint → `ha-blueprint-scaffold` / `ha-blueprint-author`
- a stateful helper (`input_*`, `counter`, `timer`, `schedule`) → `ha-helper-scaffold`
- a derived/statistical helper sensor (`bayesian`, `derivative`, `filter`, `min_max`, `statistics`, `threshold`, `trend`, `history_stats`, `integration`, `utility_meter`, `group`) → `ha-template-sensor-author`
- a Python custom integration → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **One artifact, one type, one run.** No multi-artifact batches.
2. **Intent is mandatory.** Without a described intent there is no generation; everything else may fall back to a documented default, stated in the output.
3. **Read the topic spec first.** Before generating, read the matching [`ha-automation/<topic>`](https://github.com/nolte/claude-home-assistant/tree/develop/spec/ha-automation) spec; do not generate from memory.
4. **Never generate a legacy trigger helper.** If the intent targets `flux`, `device_sun_light_trigger`, or a hand-built `platform:` trigger helper, propose the modern equivalent per [`ha-automation/legacy-trigger-helpers`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha-automation/legacy-trigger-helpers/de.md) instead.
5. **Never overwrite an existing entity.** Collision on `id` / `unique_id` / `object_id` aborts with the identifier quoted.
6. **Deliberate mode, stable identity, guarded templates.** `automation`/`script` carry a consciously chosen `mode` (with `max` for `parallel`/`queued`); every entity gets a stable `id`/`unique_id` and an English `alias` (≤50 chars); every Jinja template guards `unavailable`/`unknown` (`has_value()`, `is_number()`, `float(default)`, `availability`). Names follow [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md).
7. **Command-artifact safety.** `shell_command` never interpolates untrusted input unquoted (runs as root), no pipes/redirects in templates; `python_script` uses no `import` and only `hass`/`data`/`logger`/`output`; `rest_command` keeps `verify_ssl: true` unless justified and credentials out of the URL.
8. **Verify HA internals against the official docs.** Don't reproduce HA schemas/conventions from memory — consult Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant) and [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `intent` | yes | — | What the artifact should do, in prose |
| `artifact_type` | no | inferred from intent | `automation` / `script` / `scene` / `template` / `rest_command` / `shell_command` / `python_script` |
| `target_dir` | no | working dir | Repo / HA config root |
| `target_file` | no | per type | `automations.yaml` / `scripts.yaml` / `scenes.yaml` / `configuration.yaml` / `python_scripts/<name>.py` |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `intent` present and non-empty. If not, ask; do not generate.
2. Resolve `artifact_type` (infer + confirm). Check it against the legacy-helper gate; on a legacy target, propose the modern alternative and stop.
3. Read the matching `ha-automation/<topic>` spec.
4. The resolved target entity does not already exist (`id`/`unique_id`/`object_id`). If it does, abort with the identifier quoted.

## Workflow

### 1) Resolve and confirm

State the resolved `artifact_type`, target file path, and every assumed default in one paragraph. Wait for confirmation.

### 2) Generate

Write the artifact per the topic spec's MUST rules:

| Type | Key / location | Load-bearing rules |
|---|---|---|
| `automation` | `automation:` in `automations.yaml`/`packages/` | plural `triggers`/`conditions`/`actions`; stable `id`; English `alias`; deliberate `mode`(+`max`); event-driven trigger over polling |
| `script` | `script:` in `scripts.yaml`/`packages/` | `sequence`; public `fields`(+selectors) vs internal `variables`; deliberate `mode` |
| `scene` | `scene:` in `scenes.yaml`/`packages/` | attributes only in nested `state:`; activate via `scene.turn_on` |
| `template` | `template:` block in `configuration.yaml` | modern block form; `unique_id`; state-based vs trigger-based chosen; unavailable-guarded |
| `rest_command` | `rest_command:` | `url` (template ok); deliberate `method`; `verify_ssl: true`; creds via `username`/`password` |
| `shell_command` | `shell_command:` | snake_case alias; literal command name; quote untrusted input; check `returncode` |
| `python_script` | `python_scripts/<name>.py` | no `import`; `hass`/`data`/`logger`/`output` only; `data.get(...)`; `output` dict |

### 3) Validate and report

Validate offline (YAML lint; `ha core check` where available; mentally render templates against `unavailable`/`unknown` sources). Emit a CONFORMANT / NEEDS-WORK report keyed to the topic spec's acceptance criteria, plus the written file path and assumed defaults. Do not echo the full artifact again unless asked.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Blueprints → `ha-blueprint-scaffold` / `ha-blueprint-author`
- Stateful helpers → `ha-helper-scaffold`
- Derived/statistical sensors → `ha-template-sensor-author`
- Custom integrations → `ha-integration-scaffold`
- Deploy to live HA → out of scope
