# Skill: `ha-blueprint-scaffold`

Status: draft

## Context

A Home Assistant blueprint is a pure YAML artifact (automation, script, or template entity) with `!input` placeholders that users fill in without code ([`ha/blueprint-patterns`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/blueprint-patterns/en.md)). Unlike a custom integration there is no Python code, no coordinator lifecycle, and no test harness here — all of its quality is decided by schema correctness, selector UX, and template robustness. That makes producing a blueprint a tightly scoped draft-validate-iterate task.

This skill is the **entry point** for exactly that task. It does not generate the blueprint itself; it gathers the intent and path parameters, runs a lightweight pre-flight, and **dispatches the [`ha-blueprint-author`](https://github.com/nolte/claude-home-assistant/blob/develop/agents/ha-blueprint-author.md) agent**, which encapsulates the generative loop (draft → offline validation → repair → conformance report) in its own tool session. The skill then relays the agent's report back to the user.

This split follows the established pattern "skill = activation + input gathering + pre-flight + dispatch + report relay; agent = heavyweight generation loop". It keeps the main conversation free of validation churn (repeated YAML renders, lint output) and gives the user a single, discoverable slash-command entry.

## Scope

The skill produces **one** blueprint per invocation for **one** domain (`automation`, `script`, or `template`). It dispatches the `ha-blueprint-author` agent for the actual generation and does not reimplement its loop inline. It writes no Python code, imports nothing into a running HA instance, and bundles no multi-blueprint batches.

## Goals

- Provide a single, discoverable entry point (`/claude-home-assistant:ha-blueprint-scaffold`) for blueprint creation
- Interactively gather the parameters the agent needs (intent, domain, target path, author, optional `source_url`) before dispatching
- Run a pre-flight that catches collisions (existing blueprint) and path problems **before** the dispatch
- Use the `ha-blueprint-author` agent as the sole generation path — the skill does not produce the YAML itself
- Transparently relay the agent's CONFORMANT/NEEDS-WORK report plus the written file path back to the user

## Non-Goals

- The generative logic itself — that lives entirely in the `ha-blueprint-author` agent and in `ha/blueprint-patterns`
- Custom-integration scaffolding (`ha-integration-scaffold`), Lovelace cards (`ha-lovelace-card-scaffold`), integration services (`ha-service-definition-generator`)
- Importing, deploying, or pushing a blueprint to a running HA instance
- Editing/versioning an already-published blueprint beyond a fresh draft — backward-compatible updates are governed by `ha/blueprint-patterns`; a dedicated augment skill may follow later
- Multiple blueprints in one invocation

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "scaffold a blueprint for <intent>"
  - "create an automation blueprint"
  - "turn this automation into a blueprint"
  - "draft a motion-light blueprint"
  - "schreibe ein Blueprint für <Intent>"
  - "erstelle ein Automations-Blueprint"
  - "mach aus dieser Automation ein Blueprint"
- **MUST NOT** activate for:
  - custom-integration scaffolding (`ha-integration-scaffold`)
  - Lovelace card scaffolding (`ha-lovelace-card-scaffold`)
  - integration service definition (`ha-service-definition-generator`)
  - import/deployment into a running HA instance

### Input gathering

- **MUST** capture the `intent` (what the blueprint should do, in prose) before dispatching — no intent, no dispatch
- **MUST** determine the `domain` (`automation`, `script`, `template`); if absent, `automation` is the default, named explicitly in the report
- **SHOULD** capture target path (`target_dir`), `author`, and — if the blueprint is to be shared — `source_url`; missing values fall back to documented defaults
- **MUST** surface every chosen default in the dispatch and in the relayed report — no silent defaulting

### Pre-flight

- **MUST** verify the target path exists or sits under a writable directory **before** dispatching
- **MUST** catch a collision with an existing blueprint at the same path and abort with the path quoted instead of overwriting
- **SHOULD** derive the canonical target path `blueprints/<domain>/<author>/<file>.yaml` when writing into an HA config tree and show it to the user for confirmation before the dispatch

### Dispatch and report relay

- **MUST** delegate the actual generation to the `ha-blueprint-author` agent and not rebuild its loop inline
- **MUST** pass all gathered parameters (intent, domain, path, author, `source_url`, `min_version`) through to the agent
- **MUST** relay the agent's CONFORMANT/NEEDS-WORK report plus the relative file path back to the user
- **MUST NOT** echo the full blueprint YAML inline unless the user asks — the written file is the artifact
- **SHOULD** forward the agent's named caller follow-ups to the user as the next decisions when the report is NEEDS-WORK

## Acceptance Criteria

- [ ] The skill activates on the listed EN and DE trigger phrasings and not on the delimited neighbor cases
- [ ] `intent` is captured before the dispatch; without intent there is no dispatch
- [ ] `domain` is determined (the `automation` default, if chosen, is named explicitly)
- [ ] Pre-flight aborts on a path collision with the path quoted, without overwriting
- [ ] Generation runs through the `ha-blueprint-author` agent; the skill does not rebuild the loop inline
- [ ] All gathered parameters are passed through to the agent
- [ ] The agent report (CONFORMANT/NEEDS-WORK) plus file path is relayed to the user
- [ ] Every chosen default is surfaced in the report

## Open Questions

- **Interactivity vs. one-shot**: Should the skill ask targeted follow-ups on an incomplete intent (more rounds) or dispatch immediately with documented defaults? Currently "intent is mandatory, the rest defaults" is chosen.
- **Augment sibling**: Is there a need for an `ha-blueprint-augment` skill (analogous to `ha-coordinator-add`) for additive, backward-compatible edits to an existing blueprint? Only on concrete demand.
- **Validation gate**: The pre-flight checks path/collision, not schema. Should the skill run an optional post-dispatch gate that checks the agent report for CONFORMANT before it counts as "done"? This hinges on the validation toolchain left open in `ha/blueprint-patterns`.
