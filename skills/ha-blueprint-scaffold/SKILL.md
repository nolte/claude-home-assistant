---
name: ha-blueprint-scaffold
description: Scaffold a single Home Assistant blueprint (automation, script, or template domain) as a self-contained, spec-conformant YAML file — by gathering the intent, running a pre-flight, and dispatching the ha-blueprint-author agent for the draft-validate-iterate loop, then relaying its conformance report. Activate on phrasings like "scaffold a blueprint for X", "create an automation blueprint", "turn this automation into a blueprint", "draft a motion-light blueprint", "schreibe ein Blueprint für X", "erstelle ein Automations-Blueprint", "mach aus dieser Automation ein Blueprint". Do not activate for custom-integration scaffolding (ha-integration-scaffold), Lovelace cards (ha-lovelace-card-scaffold), integration services (ha-service-definition-generator), or importing/deploying into a running HA instance.
tags: [home-assistant, blueprint, automation, yaml, scaffolding]
---

# HA Blueprint Scaffold

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-blueprint-scaffold/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-blueprint-scaffold/en.md).

This skill is the **entry point** for creating a blueprint. It does not generate the YAML itself — it gathers parameters, runs a pre-flight, and dispatches the [`ha-blueprint-author`](https://github.com/nolte/claude-home-assistant/blob/develop/agents/ha-blueprint-author.md) agent, which owns the draft → validate → iterate loop and the conformance report against [`ha/blueprint-patterns`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/blueprint-patterns/de.md).

## When this skill activates

Use this skill when the user wants to create one Home Assistant blueprint (automation, script, or template) from a described intent — typically to package a reusable automation for sharing or for their own home.

## When NOT to activate

- scaffolding a Python custom integration → `ha-integration-scaffold`
- scaffolding a Lovelace card → `ha-lovelace-card-scaffold`
- defining an integration service → `ha-service-definition-generator`
- importing, deploying, or pushing a blueprint into a running HA instance → out of scope (generation only)

## Hard rules

1. **Never generate the blueprint inline.** The `ha-blueprint-author` agent is the sole generation path; this skill gathers inputs, pre-flights, dispatches, and relays. Do not rebuild the agent's loop here.
2. **Intent is mandatory.** Without a described intent there is no dispatch. Everything else may fall back to a documented default.
3. **Never overwrite an existing blueprint.** If the resolved path already exists, abort with the path quoted. Collision is a user-disambiguation problem.
4. **Never silently default.** When the user is silent on `domain`, `target_dir`, `author`, or `source_url`, use the documented defaults — but state every default in the dispatch and in the relayed report.
5. **One blueprint, one domain, one run.** No multi-blueprint batches, no Python, no live-HA import.

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `intent` | yes | — | What the blueprint should do, in prose |
| `domain` | no | `automation` | One of `automation`, `script`, `template` |
| `target_dir` | no | repo root | Where to write; an HA config tree triggers the `blueprints/<domain>/<author>/` path derivation |
| `author` | no | git user or `local` | Namespace folder + `author` key |
| `file_name` | no | derived from name (kebab-case) | The `.yaml` filename |
| `source_url` | no | — | Canonical origin; set only when the blueprint is meant to be shared |

If the user is silent on any optional field, use the default but state it explicitly in the output.

## Pre-flight (every run, in order — abort on first failure)

1. `intent` is present and non-empty. If not, ask for it; do not dispatch.
2. `target_dir` exists (or its parent is writable). If the path is unusable, abort and say why.
3. Resolve the target path. When `target_dir` is an HA config tree, derive `blueprints/<domain>/<author>/<file_name>.yaml`; otherwise honor the caller's path.
4. The resolved blueprint file does not already exist. If it does, abort with the path quoted.

## Workflow

### 1) Resolve and confirm

Print one paragraph stating: domain, resolved file path, author, whether `source_url` is set, and every default that was assumed. Wait for user confirmation.

### 2) Dispatch the agent

Dispatch the `ha-blueprint-author` agent, passing every gathered parameter (`intent`, `domain`, `target_dir`, `author`, `file_name`, `source_url`). The agent reads `ha/blueprint-patterns`, drafts the inputs/selectors/body, wires the `!input` → `variables`/`trigger_variables` bridge, validates offline, repairs, and returns a CONFORMANT / NEEDS-WORK report.

### 3) Relay the report

Surface the agent's report verbatim plus the relative path to the written file. Do not echo the full blueprint YAML unless the user asks. When the report is NEEDS-WORK, forward the agent's named caller follow-ups as the user's next decisions.

## Boundaries

- The generative loop and all spec conformance → `ha-blueprint-author` agent
- Blueprint authoring rules (schema, selectors, templating, modes, versioning) → `ha/blueprint-patterns`
- Custom-integration scaffold → `ha-integration-scaffold`
- Backward-compatible edits to an existing blueprint → `ha-blueprint-augment` (planned, on demand)
