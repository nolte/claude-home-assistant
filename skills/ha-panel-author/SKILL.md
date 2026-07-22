---
name: ha-panel-author
description: Act as a senior Home Assistant panel developer — take a described full-page or dashboard-surface need and develop it end-to-end to production grade, conforming to the full relevant spec set. First decides the delivery shape (custom sidebar panel vs. panel-mode view with one full-width card vs. custom view as a layout container) per spec/ha/lovelace-views-panels and spec/ha/lovelace-layout-antipatterns, then builds it — dispatching ha-panel-add for the base custom-panel scaffold, wiring hass data access (spec/ha/frontend-data-api) and any WebSocket backend (spec/ha/frontend-websocket-commands via ha-websocket-command-add + ha-integration-scaffold), and enforcing layout/responsive (narrow), performance (entity-change detection), shadow-DOM theming, and naming discipline. Activate on "build a proper custom panel for…", "develop a full-page HA panel that shows…", "I need a senior-grade dashboard panel", "entwickle ein vollwertiges Custom-Panel für…", "baue mir ein produktionsreifes HA-Panel". Do not activate for the minimal one-panel scaffold only (ha-panel-add), a single card (ha-lovelace-card-scaffold), a multi-artifact frontend solution across the whole Lovelace family (ha-lovelace-solution), a dashboard strategy (ha-strategy-add), the Python integration backend (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, frontend, lovelace, custom-panel]
---

# HA Panel Author

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-panel-author/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-panel-author/en.md).

This skill is the **senior panel-developer** of the Lovelace/frontend family. Where `ha-panel-add` mechanically scaffolds one custom panel against a single spec, this skill develops a panel **end-to-end to production grade**: it picks the right delivery shape, wires the data channel, honours layout/responsive/performance/theming discipline, and holds the result to the whole relevant spec set — then reuses `ha-panel-add` for the base scaffold rather than reinventing it.

## Why this is a skill, not an agent

- **Human-visible senior surface** — the user describes a need and reads back the delivery-shape decision, the build plan, the generated code, and a multi-spec conformance report; a skill keeps that judgement on the visible command surface, like the sibling `ha-lovelace-solution`.
- **Mid-flow interactivity** — the delivery-shape decision (custom panel vs. panel-mode view vs. custom view), the data-source/backend decision, and plan approval are per-run dialogues the user must see and approve before generation.
- **Orchestrator-leaning** — it dispatches `ha-panel-add` (base scaffold) and, when a backend endpoint is needed, `ha-websocket-command-add`; the skill-orchestrates-skill default keeps the entry point in skill form.
- Counter-dimension considered: the develop→validate→iterate loop could be an agent, but the shape decision, the backend call-out, and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill when the user wants a **complete, production-grade panel** built with senior judgement — not just a bare scaffold: a full-page sidebar page, a single-card panel-mode view, or a custom-view layout container, developed with correct data access, layout/responsive discipline, and a spec-conformance report.

## When NOT to activate

- just the minimal one-panel scaffold (bare custom element + `panel_custom` entry, no senior development) → `ha-panel-add`
- a single custom card → `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- a multi-artifact frontend solution across the whole Lovelace family (card + editor + feature + badge + …) → `ha-lovelace-solution` (which MAY dispatch this skill for the panel part)
- a programmatic dashboard/view strategy → `ha-strategy-add` / `ha/lovelace-strategies`
- the Python custom-integration backend (the WebSocket-command host, own protocol, config flow) → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **Delivery-shape first.** Before building, decide the shape — a custom **sidebar panel** (full-page), a **panel-mode view** (one full-width card), or a **custom view** (layout container rendering core cards) — per [`ha/lovelace-views-panels`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-views-panels/de.md) and [`ha/lovelace-layout-antipatterns`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-layout-antipatterns/de.md); surface the choice with its rationale and only build a custom panel for a genuine full-page-sidebar need.
2. **Read the relevant specs first, never generate from memory.** The binding set: [`ha/lovelace-views-panels`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-views-panels/de.md), [`ha/lovelace-layout-antipatterns`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-layout-antipatterns/de.md), [`ha/frontend-data-api`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/frontend-data-api/de.md), [`ha/frontend-websocket-commands`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/frontend-websocket-commands/de.md), and [`ha/lovelace-card-patterns`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-card-patterns/de.md) (shadow-DOM/theme/entity-change discipline).
3. **Reuse, don't reinvent.** Dispatch `ha-panel-add` for the base custom-panel scaffold (panel element + `panel_custom` registration) instead of hand-writing it; build senior-grade development on top. Stop and report if it returns NEEDS-WORK.
4. **Custom element, never React; `hass` is the only state channel.** Define every panel/view element as a custom element (Lit or another non-React framework — React is excluded; B5) and read the HA state exclusively through the `hass` property.
5. **Layout & responsive discipline.** Conform to `ha/lovelace-layout-antipatterns`: a panel-mode view holds exactly one card and no badges (A1/A2); honour `narrow` and order content for the mobile single-column collapse (E1); never depend on third-party layout tooling (D1); avoid fixed-outer-pixel widths (B1/B2/B4). The panel's and any embedded card's size declarations (`getGridOptions()`/`getCardSize()`) are **determined by dispatching `ha-card-sizing-determine`** per [`ha/card-panel-sizing`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/card-panel-sizing/en.md) — never hand-waved inline — so edit-mode overlays sit at the cell boundary and the panel is correct across view/masonry/panel and devices.
6. **Data through the documented channel; backend stays in the integration.** Read state via `hass` and registry/extra data via `hass.callWS(...)` per `ha/frontend-data-api`; when the panel needs a backend endpoint, it is a WebSocket command in a Python integration (`ha/frontend-websocket-commands`) — dispatch `ha-websocket-command-add` and surface a missing integration as an `ha-integration-scaffold` prerequisite; never fold backend logic into the panel.
7. **Performance & theming.** Perform entity-change detection before re-rendering (no blanket re-render on every `hass` tick, per `ha/lovelace-card-patterns`); render into shadow DOM with HA CSS custom properties, no hard-coded colours and no pixel-forced outer widths.
8. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).
9. **One panel solution per run; generation only.** No multi-panel batches; never deploy to or import into a live HA instance.

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `need` | yes | — | the desired panel/page result, in prose |
| `target_dir` | no | working dir | repo root; passed through to `ha-panel-add` and used to resolve `module_url` |
| `domain` | no | asked when needed | existing integration domain (for `www/` placement and any WS command) |
| `data_sources` | no | asked when needed | entities / registries / WebSocket data the panel renders |
| `backend_needed` | no | inferred + confirmed | whether the panel calls a backend endpoint (→ WebSocket command) |
| `config_view_needed` | no | inferred + confirmed | whether the panel needs a user-configurable, persisted settings/options view (→ `ha-panel-config-view-add`) |
| `delivery_shape` | no | decided + confirmed | override for the custom-panel / panel-mode-view / custom-view decision |
| `ux_audit_report` | no | none | a `ha-panel-ux-audit` report to consume as a prioritized improvement work-list |

If the need is underspecified, ask 1–3 targeted questions (which data/entities, what interactivity, whether a backend endpoint is needed, target repo/domain) before deciding the shape. Do not plan on guesses.

When a `ux_audit_report` (from `ha-panel-ux-audit`) is provided, treat its work-list as the prioritized set of improvements to fold into the build plan — address findings in severity order and confirm the mobile-usability items are resolved. When none is provided and the panel is non-trivial, you **MAY** dispatch `ha-panel-ux-audit` after the build to obtain one and fold its findings back in — closing the build → audit → fix loop rather than relying on a hand-pasted report.

## Pre-flight (in order — abort on first failure)

1. `need` is non-empty; `target_dir` is an existing repo and the `module_url` target location is resolvable.
2. Read the binding spec set (hard rule 2).
3. Run the delivery-shape decision (hard rule 1) and confirm it with the user.
4. Determine whether a backend endpoint is required; if so, note the WebSocket-command dependency and, if no integration exists, the `ha-integration-scaffold` prerequisite.

## Workflow

### 1) Understand & scope

Restate the need, the data it renders, and the interactivity. Ask up to three targeted questions when underspecified.

### 2) Delivery-shape decision

Choose custom panel vs. panel-mode view vs. custom view against `ha/lovelace-views-panels` + `ha/lovelace-layout-antipatterns`, and present the choice with its rationale for confirmation.

### 3) Build plan

Present a short senior build plan for approval: the chosen shape, the specs that apply, the data channel (`hass` / `callWS` / WebSocket command), any backend dependency, the layout/responsive approach, and the files to be produced. Wait for approval.

### 4) Develop

- **Custom panel** — dispatch `ha-panel-add` for the base scaffold, then develop it to production grade: wire `hass`/`callWS` data access, apply `narrow`/responsive and layout-antipattern discipline, add entity-change detection and shadow-DOM/theme styling, dispatch `ha-card-sizing-determine` to determine the panel's/embedded cards' size declarations (hard rule 5), dispatch `ha-panel-config-view-add` when a persisted settings/options view is needed (`config_view_needed`), and — if needed — dispatch `ha-websocket-command-add` (flagging `ha-integration-scaffold` when absent).
- **Panel-mode view** — produce the `type: panel` view holding exactly one container card (stack/grid) and no badges (A1/A2), referencing `ha/lovelace-card-patterns` for the single card.
- **Custom view** — produce the custom-view layout container per `ha/lovelace-views-panels` (view part; `ll-*` events, `view_layout`), applying `ha/lovelace-layout-antipatterns`.

### 5) Validate & report

Validate offline against the applied specs and emit a CONFORMANT / NEEDS-WORK report keyed to their acceptance criteria, plus the changed file paths, any dispatched-skill results, and the quality-scale marker (**not part of the HA quality scale**).

## Delegation

- Base custom-panel scaffold → `ha-panel-add`
- Panel / embedded-card size declaration (`getGridOptions`/`getCardSize`, edit-mode overlay fix) → `ha-card-sizing-determine` (per `ha/card-panel-sizing`)
- A persisted settings/options view for the panel → `ha-panel-config-view-add`
- Mobile-first UX / a11y audit of the built panel → `ha-panel-ux-audit` (build → audit → fix loop)
- A backend endpoint the panel calls → `ha-websocket-command-add` (needs an integration → `ha-integration-scaffold` if absent)
- A single custom card the view embeds → `ha-lovelace-card-scaffold`
- A multi-artifact frontend solution across the family → `ha-lovelace-solution` (the front door; it may dispatch this skill for the panel part)
