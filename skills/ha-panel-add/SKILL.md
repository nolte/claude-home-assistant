---
name: ha-panel-add
description: Augment an existing Home Assistant integration or frontend repo with one custom panel — a full-page custom element registered in the sidebar that takes over the whole content area — conforming to spec/ha/lovelace-views-panels (custom-panel part). Creates the panel custom element (Lit or another non-React framework receiving hass / narrow / route / panel, registered via customElements.define), the JS-module wiring, and the panel_custom registration in configuration.yaml (unique url_path, module_url, optional sidebar_title/sidebar_icon/config/embed_iframe). Distinguishes a custom panel from a panel-mode view (single-card layout) and a custom view (layout container). Activate on "add a custom panel", "register a sidebar panel", "create a full-page custom panel", "füge ein Custom-Panel hinzu", "registriere ein Sidebar-Panel". Do not activate for a single card or panel-mode view (ha-lovelace-card-scaffold), a dashboard strategy (ha/lovelace-strategies), a websocket command the panel calls (ha/frontend-websocket-commands), greenfield scaffolding (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, frontend, lovelace, custom-panel]
---

# HA Panel Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-panel-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-panel-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes a full-page sidebar page and reads back the panel element, the `panel_custom` registration, and the conformance report; a skill keeps this on the visible command surface, like the sibling frontend skill `ha-lovelace-card-scaffold`.
- **Mid-flow interactivity** — the delivery-shape decision (custom panel vs. custom view vs. panel-mode view) is a per-run dialogue the user approves before generation.
- **Bounded, inline generation** — one panel element plus its ES-module wiring and the `panel_custom` config fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the delivery-shape advice and the `url_path`/registration decisions belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** custom panel — a full-page custom element registered in the sidebar that takes over the whole content area — to an existing integration or frontend repo, when the need is a genuine full-page page (not a layout inside a dashboard).

## When NOT to activate

- a single card, or a panel-mode view (single-card layout in a dashboard) → `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- a custom view as a layout container (renders core cards/badges via `ll-*` events) → `ha/lovelace-views-panels` (view part), not this skill
- a programmatic dashboard strategy → `ha/lovelace-strategies`
- a WebSocket command the panel calls → `ha/frontend-websocket-commands`
- greenfield integration scaffolding → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One panel, one run.** No multi-panel batches; never generate a custom view, a card, or a strategy.
2. **Read [`ha/lovelace-views-panels`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-views-panels/de.md) first.** Do not generate from memory.
3. **Delivery-shape check.** Run it before generating: if a custom view (layout inside the dashboard) or a panel-mode view (single card) covers the need, surface it; only a genuine full-page page linked from the sidebar justifies a custom panel.
4. **Custom element, not React.** Define the panel as a custom element — the render framework is free (Lit, Preact, etc.) but **never** React (explicitly excluded) — and register it through `customElements.define(...)`.
5. **HA-supplied property set.** Accept `hass` (object, current HA state), `narrow` (boolean), and `panel` (object; config via `panel.config`); accept `route` (object) too.
6. **`hass` is the only state channel.** Never access the HA state outside the `hass` property.
7. **Register through `panel_custom`.** Add the entry in `configuration.yaml` with a unique `url_path` per entry and the panel module through `module_url` (ES module, e.g. `/local/example-panel.js`); set `sidebar_title`/`sidebar_icon` where sensible; `config`/`embed_iframe` only on request.
8. **ES5 only when needed.** Ship without ES5 by default; when ES5 support is required, load the adapter before defining via `window.loadES5Adapter().then(function() { customElements.define('my-panel', MyCustomPanel) })`.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; target for `module_url` must be resolvable (e.g. `www/` → `/local/`) |
| `page` | yes | — | the full-page sidebar page in prose; the skill derives `url_path` and panel name |
| `url_path` | no | derived + confirmed | unique per `panel_custom` entry |
| `sidebar_title` / `sidebar_icon` | no | asked | sidebar link affordances |
| `config` | no | none | arbitrary data, available at runtime as `panel.config` |
| ES5 / `embed_iframe` | no | off | ES5 adapter / iframe embedding only when needed |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir` is an existing repo and the `module_url` target location is resolvable.
2. Run the delivery-shape check; if a custom view or panel-mode view suffices, surface it before proceeding.
3. Read `ha/lovelace-views-panels`.
4. The panel element / `url_path` / `panel_custom` entry is not already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State the resolved `url_path`, the panel name, the `sidebar_title`/`sidebar_icon`, whether a `config` block / ES5 support / `embed_iframe` is needed, and the delivery-shape conclusion in one paragraph. Wait for confirmation.

### 2) Generate

- The panel custom element (non-React; Lit by default) accepting `hass`, `narrow`, `route`, `panel`, registered via `customElements.define(...)`, reading state only from `hass`.
- The ES-module file at the path that backs `module_url`.
- The `panel_custom` entry in `configuration.yaml` (unique `url_path`, `module_url`; `sidebar_title`/`sidebar_icon` where sensible; `config`/`embed_iframe` only on request).
- ES5-adapter wiring only when ES5 support is required.

### 3) Validate and report

Validate offline (panel is a custom element, not React, accepting `hass`/`narrow`/`route`/`panel`; registered via `customElements.define(...)`; no state access outside `hass`; `panel_custom` entry has a unique `url_path` and `module_url`; ES5 adapter loaded before `customElements.define` when needed). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/lovelace-views-panels` (panel part) acceptance criteria, plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- A single card or panel-mode view → `ha-lovelace-card-scaffold`
- A custom view as a layout container → `ha/lovelace-views-panels` (view part)
- A dashboard strategy → `ha/lovelace-strategies`
- A WebSocket command the panel calls → `ha/frontend-websocket-commands`
- Greenfield scaffold → `ha-integration-scaffold`
- Deploy to live HA → out of scope
