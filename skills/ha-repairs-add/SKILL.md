---
name: ha-repairs-add
description: Augment an existing Home Assistant Custom Integration with one Repairs issue (fixable or informative) conforming to spec/ha/repairs — the async_create_issue call site, a repairs.py with async_create_fix_flow + RepairsFlow/ConfirmRepairFlow for fixable issues, the strings.json issues entry (title/description), and the async_delete_issue lifecycle path. Decides fixable vs. informative and severity, redirects transient connection errors to the coordinator's UpdateFailed handling, and forbids hard-coded user strings. Activate on "add a repair issue for…", "create a fixable repair flow for…", "warn the user about a deprecation", "füge ein Repair-Issue für… hinzu". Do not activate for greenfield scaffolding (ha-integration-scaffold), system_health, whole-integration quality grading (ha-quality-scale-audit), transient error handling (ha-coordinator-add), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, repairs]
---

# HA Repairs Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-repairs-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-repairs-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes a problem situation and reads back the generated call site, flow, and translations; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-coordinator-add`, `ha-config-flow-augment`).
- **Mid-flow interactivity** — the fixable-vs-informative decision and the transient-error redirect are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — one issue plus its flow and strings fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the type decision and the conformance report belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** Repairs issue (fixable or informative) to an existing integration — a deprecation warning, an outdated-backend notice, a misconfiguration the user must fix.

## When NOT to activate

- greenfield integration scaffolding → `ha-integration-scaffold`
- system health (`system_health.py`) → separate HA mechanism
- grading the whole integration against the quality scale → `ha-quality-scale-audit`
- transient connection/API error handling (`UpdateFailed`, `entity-unavailable`) → `ha-coordinator-add` / `ha/coordinator-patterns`
- a multi-step repair flow with complex user input, or an issue raised on behalf of another integration (`issue_domain`) → out of scope (standard `ConfirmRepairFlow`/single-issue case only)
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One issue, one run.** No multi-issue batches.
2. **Read [`ha/repairs`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/repairs/de.md) first.** Do not generate from memory.
3. **Not for transient errors.** If the situation is a transient connection/API error or a pure "something is broken" with no user action, redirect to the coordinator's `UpdateFailed` handling instead of raising an issue.
4. **`async_create_issue` carries the mandatory fields** — `domain`, `issue_id` (unique in domain), `is_fixable`, `severity` (`IssueSeverity`: `ERROR` now-broken / `WARNING` future-break), `translation_key`. Set `breaks_in_ha_version` for deprecations.
5. **`is_fixable=True` ⇒ a real flow.** Generate `repairs.py` with `async_create_fix_flow(hass, issue_id, data) -> RepairsFlow` routing by `issue_id`; the flow derives from `RepairsFlow` (or `ConfirmRepairFlow`), implements `async_step_init`, and closes with `self.async_create_entry(title="", data={})` (which removes the issue). `is_fixable=False` ⇒ a `learn_more_url`, no flow.
6. **No hard-coded user strings.** Every `translation_key` lives in `strings.json` under `issues:` with `title`/`description`, all `translation_placeholders` resolved (see [`ha/translations`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/translations/de.md)).
7. **Own the lifecycle.** Produce or name an `async_delete_issue(hass, domain, issue_id)` path that clears the issue once resolved; HA does not auto-clear it.
8. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `situation` | yes | — | the problem the issue points at, in prose |
| `issue_id` | no | derived (`snake_case`) | unique within the domain |
| `fixable` | no | inferred + confirmed | true ⇒ a RepairsFlow is generated |
| `severity` | no | inferred | `error` (now broken) / `warning` (future break) |
| `breaks_in_ha_version` / `learn_more_url` / `is_persistent` | no | per situation | deprecation version / docs link / restart-survival |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Classify the situation: transient connection/API error → redirect to coordinator `UpdateFailed` and stop. Only a recurring/persistent, user-actionable state becomes an issue.
3. Read `ha/repairs`.
4. The resolved `issue_id` does not already exist. If it does, abort with it quoted.

## Workflow

### 1) Resolve and confirm

State `domain`, `issue_id`, fixable-vs-informative, `severity`, and every assumed default in one paragraph. Wait for confirmation.

### 2) Generate

| Artifact | When | Content |
|---|---|---|
| `async_create_issue(...)` call site | always | mandatory fields + optional `breaks_in_ha_version`/`learn_more_url`/`data`/`is_persistent`, placed at the state-detection location |
| `async_delete_issue(...)` path | always | clears the issue once the state is resolved |
| `strings.json` `issues:` entry | always | `title` + `description`, placeholders resolved |
| `repairs.py` | fixable only | `async_create_fix_flow` + `RepairsFlow`/`ConfirmRepairFlow` with `async_step_init` → `async_create_entry(title="", data={})` |

### 3) Validate and report

Validate offline (mandatory fields present; no `is_fixable=True` without a flow; `translation_key` resolved in `strings.json`; an `async_delete_issue` path exists; no hard-coded strings). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/repairs` acceptance criteria, plus the changed file paths and the quality-scale marker (**Gold**).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Whole-integration quality grading → `ha-quality-scale-audit`
- Transient error handling → `ha-coordinator-add` / `ha/coordinator-patterns`
- Greenfield scaffold → `ha-integration-scaffold`
- Deploy to live HA → out of scope
