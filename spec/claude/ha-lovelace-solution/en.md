# Skill: `ha-lovelace-solution`

Status: draft

## Context

The Lovelace/frontend skill family each produces **one** artifact from a narrowly scoped intent: `ha-lovelace-card-scaffold` builds the custom card itself, `ha-card-editor-add` adds an `ha-form` config editor via `getConfigElement`, `ha-card-features-add` adds a tile/card feature, `ha-badge-add` a custom badge, `ha-strategy-add` a dashboard/view strategy, and `ha-panel-add` a full-page custom panel. Real-world frontend requirements are rarely a single artifact: "a custom card for my pump with a visual config editor and a tile feature" is a chain of `card-scaffold` → `card-editor` + `card-features`, where the add-ons build on the previously generated card. A user who doesn't know the skills would have to do that decomposition themselves — which frontend element, which add-on, which order, which file/custom-element references which. That mapping burden is exactly what the user should not have to carry.

This skill is the **upstream planning and dispatch layer** of the frontend cluster: it takes a fuzzy frontend requirement, decomposes it into the minimal combination of artifacts, fixes the dependency order, confirms the plan with the user, and then dispatches the owning skills one after another, threading the identities (card tag name, file path, module resource, `<domain>`) of earlier steps into the inputs of later ones. It generates **no** artifact itself — generation and spec conformance stay with the individual skills. A frontend-cluster specialty: when a card or panel calls a backend endpoint (a WebSocket command), that backend lives in a Python custom integration — the skill surfaces that dependency in the plan but does not fold backend work into a frontend skill.

## Scope

Planning and orchestration across the Lovelace/frontend skill family: `ha-lovelace-card-scaffold`, `ha-card-editor-add`, `ha-card-features-add`, `ha-badge-add`, `ha-strategy-add`, `ha-panel-add`, and — as the backend endpoint a card/panel consumes — `ha-websocket-command-add`. One requirement per run → one artifact plan → N dispatched owning calls → one aggregate report. The skill decides the *combination* (which artifacts, which type per artifact, which order, which wiring), not the content of any single artifact.

## Goals

- Derive the right *combination* of artifacts from a prose frontend requirement, without the user knowing the frontend skill landscape
- Produce a processable artifact plan in dependency order (per entry: artifact, type, owning skill, dependency, purpose) and get it confirmed before any generation
- Dispatch the individual skills in correct order and thread the identities (card tag/`custom:<type>`, file path, module resource, `<domain>`) of earlier artifacts into the inputs of later ones
- Recognize and surface a backend dependency (a card/panel calls a WebSocket command); dispatch the command itself via `ha-websocket-command-add`, and when no custom integration exists (yet) point at `ha-integration-scaffold` as the backend prerequisite instead of folding backend work into a frontend skill
- Deliver an aggregate report naming every produced file and its wiring

## Non-Goals

- Generating a single artifact and its spec conformance — that stays with `ha-lovelace-card-scaffold`, `ha-card-editor-add`, `ha-card-features-add`, `ha-badge-add`, `ha-strategy-add`, `ha-panel-add`, `ha-websocket-command-add`
- Scaffolding the Python custom integration that hosts a WebSocket-command backend — that is `ha-integration-scaffold` (the skill only recognizes the need and points)
- Deploying to a running HA instance or writing dashboard/resource configuration into a real Lovelace config — generation only
- Its own validation or conformance logic — each dispatched skill validates its own artifact; this skill only aggregates the reports

## Requirements

### Activation triggers

- **MUST** activate on composite, solution-oriented frontend requests where the user describes the result, not the artifact:
  - "build a custom card with an editor and a feature"
  - "create a dashboard strategy plus a badge"
  - "set up a custom panel with a WebSocket backend"
  - "baue mir eine Lovelace-Card mit Editor (und Tile-Feature)", "richte ein Custom-Panel mit WebSocket-Backend ein"
- **SHOULD** not activate when the requirement is clearly a single frontend artifact (the owning individual skill applies directly); when in doubt, this skill plans and proposes a single-artifact plan

### Inputs

- **MUST** capture: `requirement` (prose, the desired frontend result)
- **MAY** capture: `target_dir` (repo root) and the `domain` of the existing integration, existing card/module identities (tag name, file path) to use as sources

### Pre-flight

- **MUST** check `requirement` is non-empty; on underspecification ask 1–3 targeted questions (which device/entity target, JS or Lit/TS, which tag name, whether a backend endpoint is needed) before planning
- **MUST** check whether the requirement needs a backend endpoint (WebSocket command); if so, mark it in the plan — and when no custom integration exists (yet), name `ha-integration-scaffold` as the prerequisite instead of forcing the backend work into a frontend skill

### Decomposition heuristic (requirement → artifact type → skill)

- **MUST** map a standalone custom card (the visible card element) to `ha-lovelace-card-scaffold` — step 1 whenever a card is needed
- **MUST** map a visual config editor for a card (`ha-form` via `getConfigElement`) to `ha-card-editor-add`, depending on the card
- **MUST** map a tile/card feature (interactive control row inside the tile card and other host cards) to `ha-card-features-add`, depending on a frontend module
- **MUST** map a custom badge to `ha-badge-add`, a dashboard/view strategy (auto-generation of views/cards) to `ha-strategy-add`, and a full-page custom panel to `ha-panel-add` — each an independent top-level frontend element
- **MUST** map a backend endpoint a card or panel calls to `ha-websocket-command-add` (Python side); the command lives in a custom integration and is its prerequisite (`ha-integration-scaffold` when absent)
- **MUST** keep artifacts minimal — never create an add-on a single artifact already covers

### Plan & dispatch

- **MUST** present an artifact plan as a table in dependency order before any generation: per entry `#`, artifact name/tag, type, owning skill, dependency (`depends-on`), purpose — and wait for explicit confirmation
- **MUST NOT** generate an artifact inline itself; every generation runs through the owning individual skill
- **MUST** dispatch the skills in dependency order (card before its add-ons; badges/strategies/panels independent; a WebSocket command as the backend the card/panel consumes) and thread the identities (card tag/`custom:<type>`, file path, module resource, `<domain>`, command `type`) into the inputs of dependent steps
- **MUST** stop and report when a dispatched skill returns a NEEDS-WORK report, rather than building on an unfinished predecessor artifact
- **MUST** keep all identifiers consistent across artifacts per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Aggregate report

- **MUST** list, at the end, every produced file path, its artifact, and the wiring (which element/tag references which; which card calls which command)
- **MUST** relay the aggregated CONFORMANT / NEEDS-WORK reports of the individual skills without re-judging them

### Prohibitions

- **MUST NOT** orchestrate more than one requirement per run
- **MUST NOT** execute a plan without user confirmation
- **MUST NOT** fold backend work (the WebSocket-command backend or the custom integration) into a frontend skill
- **MUST NOT** deploy to a running HA instance or write dashboard/resource configuration into a real Lovelace config

## Acceptance criteria

- [ ] Skill asks for missing essentials (target entity, JS vs. Lit/TS, tag name, backend need) before planning
- [ ] Skill presents an artifact plan in dependency order and waits for confirmation
- [ ] Skill dispatches the owning individual skills instead of generating itself
- [ ] Identities (card tag, file path, module resource, `<domain>`, command `type`) of earlier artifacts are threaded into the inputs of dependent steps
- [ ] A backend dependency (WebSocket command) is recognized, pointed at `ha-websocket-command-add`, and — when no integration exists — pointed at `ha-integration-scaffold` as the prerequisite
- [ ] Stops on a NEEDS-WORK predecessor instead of building further
- [ ] Aggregate report lists every file and the wiring and relays the individual reports

## Open questions

- **Agent vs. skill dispatch**: should the individual steps run as skills (visible, sequential) or via a generation agent (isolated, parallel)? Currently skill dispatch, because the plan confirmation and the identity wiring (card tag → editor/feature, card → command) should stay visible in the user context.
- **Backend boundary**: how far should the skill follow the backend prerequisite — only dispatch the WebSocket command, or also pre-scaffold a missing integration? Currently: dispatch the command, only name a missing integration as the prerequisite.
- **TS/Lit vs. vanilla JS**: `ha-lovelace-card-scaffold` produces vanilla JS, some add-ons are LitElement-centric. Should the skill enforce a consistent framework choice on mixed requirements or leave it per artifact to the owning skill? Currently per owning skill.
- **Existing-config awareness**: should the skill read the `www/` directory and existing module resources to catch collisions early? Currently named by the user.
