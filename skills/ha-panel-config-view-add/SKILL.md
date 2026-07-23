---
name: ha-panel-config-view-add
description: "Adds or completes the configuration/options view of an existing Home Assistant custom panel, conforming to spec/ha/lovelace-panel-config-view — separating deploy-time panel.config from runtime-editable options, composing the options form from ha-form plus ha-selector selectors, persisting domain/shared state through a custom WebSocket command and per-user UI preferences through the frontend user-data store, and gating admin-only options in the UI while enforcing them server-side. Completes the missing config-view pieces on an existing panel and validates them, producing a CONFORMANT / NEEDS-WORK report. Activate on \"add a settings view to my panel\", \"let users configure my panel\", \"persist my panel options\", or equivalent German requests. Do not activate for scaffolding a new panel (ha-panel-add), defining the WebSocket command itself (ha-websocket-command-add), the card config editor (ha-card-editor-add), the backend integration options flow (ha-options-flow-augment), or deploying to a live HA instance."
tags: [home-assistant, custom-integration, lovelace, panel]
phase: design
summary: "Adds or completes the configuration/options view of an existing Home Assistant custom panel, with correct persistence and admin gating."
summary_de: "Fügt einer bestehenden Home-Assistant-Custom-Panel die Konfigurations-/Optionsansicht hinzu oder vervollständigt sie — mit korrekter Persistenz und Admin-Gating."
use_when:
  - "you want to add a settings view to your panel"
  - "you want to let users configure your panel"
  - "you want to persist your panel's options"
  - "you want to add an options page to the custom panel"
dont_use_when:
  - situation: "You are scaffolding a brand-new panel"
    alternative: ha-panel-add
  - situation: "You need to define the backend WebSocket command itself"
    alternative: ha-websocket-command-add
  - situation: "You need the card graphical config editor"
    alternative: ha-card-editor-add
  - situation: "You need the backend integration config/options flow"
    alternative: ha-options-flow-augment
see_also:
  - ha-panel-add
  - ha-websocket-command-add
  - ha-card-editor-add
  - ha-options-flow-augment
  - ha-panel-author
---

# HA Panel Config View Add

Spec: `spec/claude/ha-panel-config-view-add/en.md` (EN canonical) / `spec/claude/ha-panel-config-view-add/de.md` (DE translation).

This skill makes an existing custom panel's **configuration/options view** complete and correct, per `spec/ha/lovelace-panel-config-view/en.md`. It completes the missing config-view pieces (deploy-time-vs-runtime classification, the `ha-form` options form, a persistence path, admin gating) and validates them — it does not scaffold the panel (`ha-panel-add`) or define the WebSocket command (`ha-websocket-command-add`).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the panel and reads back the options-form composition, the chosen persistence path, and a conformance report; a skill keeps this on the visible command surface, like the sibling `ha-card-editor-add`.
- **Mid-flow interactivity** — which values are deploy-time config vs. runtime options, whether options are shared (WebSocket command) or per-user (user-data store), and which controls are admin-only are per-run dialogues the user confirms.
- **Bounded, inline generation** — the options view, the form schema, the `hass.callWS` calls, and the admin guards fit inline; no isolated agent context is needed.
- Counter-dimension considered: the audit-then-complete loop could be an agent, but the ownership/persistence choice and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill to give an **existing** custom panel a complete, correct configuration/options view — the user can review and change how the panel behaves, and those choices persist through the right channel and are gated correctly.

## When NOT to activate

- scaffolding a brand-new panel → `ha-panel-add`
- defining the backend WebSocket command (decorator, schema, `async_register_command`) → `ha-websocket-command-add`
- the card graphical config editor (`getConfigElement` / `getConfigForm`) → `ha-card-editor-add`
- the backend integration config/options flow (`config_flow.py`, `OptionsFlow`) → `ha/config-flow-patterns`
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **Read `spec/ha/lovelace-panel-config-view/en.md` first.** Do not generate from memory. Honour its evidence tiers — `[doc]` / `[src]` / `[unsupported]` / `[policy]` — and never present a source-verified, inferred, or policy rule as a documented HA fact.
2. **Classify every value.** Split each configurable value into deploy-time config (fixed per deployment → `panel.config`) or runtime option (user/admin-editable → a persistence path). `[policy]` A value the user changes at runtime **MUST NOT** require a `configuration.yaml` edit + restart.
3. **`panel.config` is read-only in practice.** Read it at runtime as `panel.config`; `[unsupported]` never mutate it in the element to persist state — there is no documented write-back path.
4. **Pick the persistence path by ownership.** Domain/shared state → a custom WebSocket command (`hass.callWS`, with a matching read and, where relevant, subscribe command; define it via `ha-websocket-command-add`) `[doc]`. Per-user UI preference → the `frontend/*_user_data` store `[src]` (undocumented). Never store installation-wide config in the per-user store.
5. **Compose the form from `ha-form` + `ha-selector`.** `[doc]` selectors are the documented approach; `[src]` binding `ha-form`/`ha-selector` directly in a panel is source-verified (no `getConfigForm` equivalent for panels). Reuse HA selectors over raw inputs so validation, theming, and mobile behaviour come for free.
6. **Gate admin, and enforce it server-side.** `require_admin` / `hass.user.is_admin` gate the UI `[doc]`, but `[src]`/`[policy]` the WebSocket command handler is the real trust boundary — every admin-only write **MUST** be enforced server-side; frontend gating alone is not enough.
7. **Name per `spec/ha/naming-conventions/en.md`** and **verify HA internals against the official docs** (see `spec/ha/upstream-docs-verification/en.md`).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; the panel lives under `custom_components/<domain>/www/<panel>.js` (or a frontend build) |
| `panel_file` | no | discovered | the panel JS module to add/complete the config view for |
| `options` | no | asked | the option fields to expose, each classified deploy-time vs runtime |
| `persistence` | no | asked | per option group — shared (WebSocket command) or per-user (user-data store) |
| `admin_only` | no | asked | which options are admin-only (UI gate + server-side enforcement) |

## Pre-flight (in order — abort on first failure)

1. `git -C <target_dir> rev-parse --is-inside-work-tree`.
2. Locate the panel JS module and read its element, `panel`/`panel.config` reads, `route` handling, and any existing options UI or `hass.callWS` usage.
3. Read `ha/lovelace-panel-config-view`.

## Workflow

### 1) Audit the current config view

Report, per `ha/lovelace-panel-config-view`: which values are deploy-time `panel.config` vs runtime options? Is there an options view at all? Where do changed options persist today (a real path, or nowhere/lost on reload)? Is the form built from `ha-form`/selectors or raw inputs? Are admin-only writes enforced server-side, or only hidden in the UI?

### 2) Complete the missing pieces

- classify each value; keep deploy-time config in `panel.config` and route runtime options to a persistence path
- build/repair the options view — an `ha-form` bound to a selector schema, as a same-page region or a `route`-driven sub-route
- wire the persistence path — `hass.callWS` set/get (+ subscribe) for shared state (command defined via `ha-websocket-command-add`), or `frontend/*_user_data` for per-user preferences
- gate admin-only controls on `hass.user.is_admin` in the UI and confirm the command handler enforces admin server-side

### 3) Validate & report

Validate offline (every value classified; `panel.config` not mutated to persist; shared options go through a WebSocket command with a read path; per-user prefs go through the user-data store; the form uses `ha-form`/selectors; admin-only writes are enforced server-side) and emit a CONFORMANT / NEEDS-WORK report keyed to the `ha/lovelace-panel-config-view` acceptance criteria, plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**).

## Boundaries

- Scaffolding a new panel → `ha-panel-add`
- Defining the WebSocket command → `ha-websocket-command-add` / `ha/frontend-websocket-commands`
- The card config editor → `ha-card-editor-add` / `ha/lovelace-card-editor`
- The backend integration options flow → `ha/config-flow-patterns`
