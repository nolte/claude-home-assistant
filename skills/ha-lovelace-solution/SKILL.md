---
name: ha-lovelace-solution
description: Plan and orchestrate a complete Home Assistant Lovelace/frontend solution from a result-oriented requirement, so the user never has to pick which frontend skill to use. Decomposes the requirement into the minimal combination of artifacts across the Lovelace skill family, presents a dependency-ordered artifact plan for approval, then dispatches ha-lovelace-card-scaffold, ha-card-editor-add, ha-card-features-add, ha-badge-add, ha-strategy-add, ha-panel-add, and ha-websocket-command-add in order — threading the card tag, file path, module resource, and domain between steps — and surfaces a WebSocket backend's Python-integration dependency in the plan instead of folding it into a frontend skill. Activate on "build a custom card with an editor and a feature", "create a dashboard strategy plus a badge", "set up a custom panel with a WebSocket backend", "baue mir eine Lovelace-Card mit Editor", "richte ein Custom-Panel mit WebSocket-Backend ein". Do not activate for a single clear frontend artifact (let the owning skill handle it), the Python integration backend (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, lovelace, frontend, orchestration]
---

# HA Lovelace Solution

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-lovelace-solution/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-lovelace-solution/en.md).

This skill is the **front door** to the Lovelace/frontend skill family. It does not generate any artifact itself — it decomposes the requirement, plans the combination, and dispatches the owning skills, each of which owns its generation and spec conformance.

## Why this is a skill, not an agent

- **Plan-before-generate gate** — the artifact plan must be presented and explicitly approved before any generation; that human-visible gate is core to the contract and an agent's fire-and-forget shape would lose it.
- **Mid-flow interactivity** — clarifying questions (JS vs. Lit/TS, tag name, target entity, backend need), plan confirmation, and the "this needs a Python integration backend" decision are per-run dialogues.
- **Orchestrator that dispatches other skills** — the skill-orchestrates-skill default (see `skill-vs-agent`) keeps the entry point in skill form, like `ha-automation-solution` dispatching the automation authoring skills.
- Counter-dimension considered: the per-artifact generation could run as parallel agents, but the plan approval and the identity threading (card tag → editor/feature, card → command) must stay visible in the user's context; skill wins.

## When this skill activates

Use this skill when the user describes a **frontend result** that likely needs more than one artifact, and should not have to know which frontend skill produces what — e.g. "a custom card for my pump with a visual config editor and a tile feature", "a dashboard strategy plus a badge", "a custom panel backed by a WebSocket command".

## When NOT to activate

- a single clear frontend artifact (one card, one editor, one feature, one badge, one strategy, one panel) → let the owning skill activate directly
- the Python custom-integration backend (own device/cloud protocol, config flow, the WebSocket-command host) → `ha-integration-scaffold`
- deploying/importing into a running HA instance or writing dashboard/resource config → out of scope (generation only)

## Hard rules

1. **Never generate inline.** Every artifact is produced by its owning skill — `ha-lovelace-card-scaffold`, `ha-card-editor-add`, `ha-card-features-add`, `ha-badge-add`, `ha-strategy-add`, `ha-panel-add`, or `ha-websocket-command-add`. This skill plans and dispatches; it does not write artifacts.
2. **Plan before generate.** Always present the dependency-ordered artifact plan and wait for explicit approval before dispatching anything.
3. **One requirement, one run.** No multi-requirement batches.
4. **Minimal artifacts.** Decompose to the fewest artifacts that satisfy the requirement; never add an add-on a single artifact already covers.
5. **Thread identities.** Dispatch in dependency order and pass the identities produced in earlier steps — card tag / `custom:<type>`, file path, module resource, `<domain>`, command `type` — as inputs to dependent steps. Keep all names consistent per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md).
6. **Stop on NEEDS-WORK.** If a dispatched skill returns NEEDS-WORK, stop and report — do not build a dependent artifact on an unfinished predecessor.
7. **Backend lives in a Python integration.** A WebSocket command's backend belongs to a custom integration — dispatch the command via `ha-websocket-command-add`, surface a missing integration as a prerequisite (`ha-integration-scaffold`), and never fold backend work into a frontend skill.
8. **Verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `requirement` | yes | — | The desired frontend result, in prose |
| `target_dir` | no | working dir | repo root, passed through to dispatched skills |
| `domain` | no | asked when needed | the existing integration's domain (for `www/` placement and the WS command) |
| `known_sources` | no | asked when needed | existing card tag / module resource to build on |

## Decomposition heuristic (requirement → artifact type → skill)

| The requirement needs… | Artifact | Owning skill |
|---|---|---|
| a standalone custom card (the visible card element) | custom card (`www/<card>.js`) | `ha-lovelace-card-scaffold` (step 1 when a card is needed) |
| a visual config editor for a card (`ha-form` via `getConfigElement`) | card editor element | `ha-card-editor-add` (depends on the card) |
| a tile/card feature (interactive control row in the tile card and other host cards) | card-feature element | `ha-card-features-add` (depends on a frontend module) |
| a custom badge in the dashboard badge picker | badge element | `ha-badge-add` (independent top-level) |
| auto-generated views/cards (dashboard or view strategy) | strategy class | `ha-strategy-add` (independent top-level) |
| a full-page custom panel in the sidebar | custom panel | `ha-panel-add` (independent top-level) |
| a backend endpoint a card/panel calls | WebSocket command (Python) | `ha-websocket-command-add` (backend; needs an integration → `ha-integration-scaffold` if absent) |
| an own device/cloud protocol, config flow, the integration that hosts the command | custom integration | **out of scope** → `ha-integration-scaffold` |

## Workflow

### 1) Clarify

If the requirement is underspecified, ask 1–3 targeted questions (which device/entity target, JS or Lit/TS, which tag name, whether a backend endpoint is needed) before planning. Do not plan on guesses.

### 2) Plan

Decompose into a dependency-ordered artifact plan and present it as a table:

```markdown
| # | Artifact / tag | Type | Skill | Depends on | Purpose |
|---|---|---|---|---|---|
| 1 | custom:pump-card | custom card | ha-lovelace-card-scaffold | — | the pump card |
| 2 | pump-card editor | card editor | ha-card-editor-add | #1 | ha-form config UI |
| 3 | pump-card tile feature | card feature | ha-card-features-add | #1 | control row |
| 4 | <domain>/pump_status | websocket command | ha-websocket-command-add | integration (ha-integration-scaffold) | backend the card calls |
```

Surface any backend / custom-integration prerequisite here. Wait for explicit approval.

### 3) Dispatch

Invoke each owning skill in plan order, passing the identities resolved in earlier steps (card tag, file path, module resource, `<domain>`, command `type`) as inputs to the dependent steps. After each, check the returned report; stop on NEEDS-WORK.

### 4) Aggregate report

List every produced file, its artifact, and the wiring (which element references which tag; which card calls which command). Relay each dispatched skill's CONFORMANT / NEEDS-WORK report verbatim — do not re-judge them. Do not deploy and do not write dashboard/resource config.

## Boundaries

- Single-artifact generation + spec conformance → the owning frontend skill
- The WebSocket-command backend → `ha-websocket-command-add`; the hosting custom integration → `ha-integration-scaffold` (this skill only recognizes and points)
- Deploy to live HA / write dashboard/resource config → out of scope
