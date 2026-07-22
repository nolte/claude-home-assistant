# Skill: `ha-panel-author`

Status: draft

## Context

The Lovelace/frontend skill family has a minimal panel scaffolder — `ha-panel-add` — that emits one custom panel (the custom element plus the `panel_custom` registration) in conformance with `ha/lovelace-views-panels` (custom-panel part). That is the right tool for a bare scaffold, but a real panel need is rarely just the skeleton: it decides *which* surface to build (a full-page sidebar panel, a panel-mode view, or a custom-view layout container), reads its data through the right channel, may call a WebSocket backend, and must honour layout, responsive, performance, and theming discipline across several specs at once.

This skill is the **senior panel developer** of the family. It takes a described full-page or dashboard-surface need and develops it end-to-end to production grade, holding the result to the full relevant spec set: `ha/lovelace-views-panels` (delivery shapes), `ha/lovelace-layout-antipatterns` (layout/arrangement guardrails), `ha/frontend-data-api` (the `hass` data channel), `ha/frontend-websocket-commands` (a backend endpoint the panel calls), and `ha/lovelace-card-patterns` (shadow-DOM/theme/entity-change discipline). It does not reinvent the base scaffold — it dispatches `ha-panel-add` for that — and it does not generate the Python backend — it dispatches `ha-websocket-command-add` and surfaces `ha-integration-scaffold` as a prerequisite. Quality-scale marker: custom panels and views are **not part of the HA quality scale**; the pattern lives outside the scale.

## Scope

Developing exactly one panel solution per run, end-to-end, into an existing repo. The skill decides the delivery shape (custom sidebar panel / panel-mode view / custom view), presents a senior build plan, and then builds it: for a custom panel it dispatches `ha-panel-add` for the base scaffold and develops it (data access, responsive `narrow`, layout discipline, entity-change detection, shadow-DOM theming, and — when needed — a dispatched WebSocket command); for a panel-mode view or custom view it produces the corresponding config/element per the governing specs. It reads the binding spec set and validates offline, returning a multi-spec conformance report. It decides the *shape and development* of one panel solution, not the content of unrelated artifacts.

## Goals

- Develop a production-grade panel from a described need, delimited from the bare scaffold (`ha-panel-add`) and from the multi-artifact orchestrator (`ha-lovelace-solution`)
- Make the delivery-shape decision explicit and justified — custom sidebar panel vs. panel-mode view vs. custom view — per `ha/lovelace-views-panels` and `ha/lovelace-layout-antipatterns`
- Reuse `ha-panel-add` for the base custom-panel scaffold instead of hand-writing the element and `panel_custom` registration
- Wire data through the documented channel (`hass` / `hass.callWS`) per `ha/frontend-data-api`, and keep any backend endpoint in a Python integration as a WebSocket command (dispatched, not folded in)
- Enforce layout, responsive (`narrow`), performance (entity-change detection), and shadow-DOM theming discipline across the applied specs
- Return a CONFORMANT / NEEDS-WORK report keyed to every spec the build touched

## Non-Goals

- The bare one-panel scaffold with no senior development (element + `panel_custom` only) — `ha-panel-add` (dispatched by this skill for the base scaffold)
- A single custom card — `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- A multi-artifact frontend solution across the whole family (card + editor + feature + badge + strategy + panel) — `ha-lovelace-solution` (which may dispatch this skill for the panel part)
- Programmatic dashboard/view generation (strategies) — `ha-strategy-add` / `ha/lovelace-strategies`
- The Python custom integration in which a WebSocket-command backend lives — `ha-integration-scaffold` (the skill only detects the need and dispatches/flags it)
- Build stacks (Vite, esbuild, Rollup), TypeScript migration, and theme definition by the panel itself — separate follow-up specs
- Deploying/importing into a running HA instance — generation only

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "build a proper custom panel for…", "develop a full-page HA panel that shows…", "I need a senior-grade dashboard panel"
  - "entwickle ein vollwertiges Custom-Panel für…", "baue mir ein produktionsreifes HA-Panel"
- **SHOULD NOT** activate when the user wants only the bare scaffold (`ha-panel-add`) or a multi-artifact frontend solution (`ha-lovelace-solution`); in doubt this skill decides the delivery shape and proposes a plan

### Inputs

- **MUST** capture: `need` (prose, the desired panel/page result)
- **MAY** capture: `target_dir` (repo root), `domain` of the existing integration, `data_sources` (entities/registries/WebSocket data), `backend_needed`, and a `delivery_shape` override

### Pre-flight (in order — abort on first failure)

- **MUST** check that `need` is non-empty, `target_dir` is an existing repo, and the `module_url` target location is resolvable
- **MUST** read the binding spec set: `ha/lovelace-views-panels`, `ha/lovelace-layout-antipatterns`, `ha/frontend-data-api`, `ha/frontend-websocket-commands`, `ha/lovelace-card-patterns`
- **MUST** run the delivery-shape decision and confirm it with the user before building
- **MUST** determine whether a backend endpoint is required; if so, note the WebSocket-command dependency and, when no integration exists, the `ha-integration-scaffold` prerequisite

### Delivery-shape decision

- **MUST** choose between a custom sidebar panel (full-page), a panel-mode view (one full-width card), and a custom view (layout container) per `ha/lovelace-views-panels`, and present the choice with its rationale
- **MUST** apply `ha/lovelace-layout-antipatterns` to the choice — a panel-mode view holds exactly one card and no badges (A1/A2); only a genuine full-page-sidebar need justifies a custom panel
- **SHOULD** point the user at the lighter tool when a bare scaffold (`ha-panel-add`) or a strategy (`ha-strategy-add`) covers the need

### Development rules

- **MUST** dispatch `ha-panel-add` for the base custom-panel scaffold instead of hand-writing the panel element and `panel_custom` registration; **MUST** stop and report if it returns NEEDS-WORK
- **MUST** define every panel/view element as a custom element and **MUST NOT** use React (B5); **MUST NOT** access the HA state outside the `hass` property
- **MUST** conform to `ha/lovelace-layout-antipatterns`: honour `narrow` and the mobile single-column collapse (E1); never depend on third-party layout tooling (D1); an embedded custom card declares `getGridOptions()`/`getCardSize()` and avoids fixed-outer-pixel widths (B1/B2/B4)
- **MUST** read state via `hass` and registry/extra data via `hass.callWS(...)` per `ha/frontend-data-api`; **MUST** implement a backend endpoint the panel calls as a WebSocket command in a Python integration (`ha/frontend-websocket-commands`), dispatched via `ha-websocket-command-add`, and **MUST NOT** fold backend logic into the panel
- **MUST** perform entity-change detection before re-rendering (no blanket re-render on every `hass` tick) and render into shadow DOM with HA CSS custom properties per `ha/lovelace-card-patterns`; **MUST NOT** hard-code colours or pixel-forced outer widths
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline against the applied specs: correct delivery shape; custom element (not React) with `hass`-only state access; `panel_custom` registration (for a custom panel) with a unique `url_path` and `module_url`; layout-antipattern conformance (A1/A2/E1/D1 and embedded-card B-rules); data via `hass`/`callWS`; a backend endpoint dispatched as a WebSocket command, not folded in; entity-change detection and shadow-DOM theming present
- **MUST** deliver a CONFORMANT / NEEDS-WORK report keyed to every spec the build touched, plus the changed file paths, any dispatched-skill results, and the quality-scale marker (**not part of the HA quality scale**)

### Prohibitions

- **MUST NOT** develop more than one panel solution per run
- **MUST NOT** hand-write the base custom-panel scaffold when `ha-panel-add` can produce it
- **MUST NOT** fold a WebSocket backend into the panel or scaffold the Python integration itself
- **MUST NOT** deploy to or import into a running HA instance

## Acceptance criteria

- [ ] The delivery shape (custom panel / panel-mode view / custom view) is decided, justified, and confirmed before building
- [ ] The binding spec set is read before generation
- [ ] The base custom-panel scaffold is produced by dispatching `ha-panel-add`, not hand-written
- [ ] Every element is a custom element (not React) and accesses the HA state only through `hass`
- [ ] Layout-antipattern conformance holds — panel-mode view has one card and no badges (A1/A2), `narrow`/single-column collapse honoured (E1), no third-party layout tooling (D1), embedded cards follow B1/B2/B4
- [ ] Data flows through `hass`/`hass.callWS`; a backend endpoint is a dispatched WebSocket command, not folded into the panel
- [ ] Entity-change detection and shadow-DOM theming (HA CSS custom properties) are present; no hard-coded colours or pixel-forced outer widths
- [ ] The report names the applied specs, the changed file paths, dispatched-skill results, and the quality-scale marker **not part of the HA quality scale**

## Open questions

- **Overlap with `ha-lovelace-solution`**: the orchestrator may dispatch this skill for the panel part of a multi-artifact solution. The exact hand-off (does the solution own the plan and this skill own only the panel build?) is left to the orchestrator; a firm contract is a follow-up.
- **Delivery-shape heuristic**: `ha/lovelace-views-panels` leaves the view-vs-panel choice to case-by-case judgement. This skill decides per run; a codified heuristic is open.
- **Embedded-card generation depth**: when a panel embeds bespoke cards, does this skill dispatch `ha-lovelace-card-scaffold` per card or render inline? Currently it dispatches for a reusable card and renders inline for panel-only content; the threshold is open.
- **`ha-panel-add` re-dispatch on iteration**: when senior development changes the base panel shape, is `ha-panel-add` re-run or is the scaffold edited in place? Currently edited in place after the initial scaffold; a re-dispatch contract is open.
