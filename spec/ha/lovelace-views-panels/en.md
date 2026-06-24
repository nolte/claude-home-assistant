# HA Integration: Lovelace Views and Custom Panels

Status: draft

## Context

Beyond the single card, HA extends two larger frontend surfaces: the **custom view** and the **custom panel**. Both are registered — like the card — as a custom element; the render framework is free (Lit Element, Preact, or another; only React is explicitly excluded).

A **custom view** overrides the default masonry layout (Pinterest-like) and defines its own layout mechanism (for example a grid). Cards and badges are created and maintained by the core code and handed to the view; the view loads them and displays them in a custom layout. The view element receives `hass`, `lovelace`, `index`, `cards`, and `badges` as properties and implements `setConfig`. Through the `lovelace` object the view reaches the dashboard state including edit mode and can trigger the core dialogs to edit, delete, and add a card. The view is referenced via `type: custom:my-view`.

A **custom panel** is a full-page page, linked from the sidebar, with real-time access to the Home Assistant object (core examples: dashboards, Map, Logbook, History). Users register their own panels through the `panel_custom` component in `configuration.yaml`; the panel element receives `hass`, `narrow`, `route`, and `panel` as properties.

This spec covers both related surfaces. It delimits against the sibling specs: `ha/lovelace-card-patterns` covers the single card, `ha/lovelace-strategies` covers programmatic dashboard generation; the `hass` data channels are described in `ha/frontend-data-api`.

Quality scale marker: custom views and custom panels are **not part of the HA quality scale** — the pattern lives outside the scale.

## Goals

- Establish the custom view as a layout container that replaces the default masonry layout with its own mechanism (for example a grid)
- Establish the view element as a custom element with the property set HA supplies (`hass`, `lovelace`, `index`, `cards`, `badges`)
- Run card interaction (edit, delete, add) exclusively through the core events of the `lovelace` object instead of re-implementing the card lifecycle
- Establish custom-panel registration through `panel_custom` in `configuration.yaml` as the canonical entry point
- Establish the panel element with the property set HA supplies (`hass`, `narrow`, `route`, `panel`)
- Make the JavaScript-version choice (ES5 vs. latest) and the `embed_iframe` hint explicit instead of leaving them to chance

## Non-Goals

- Single-card patterns (`HTMLElement` subclass, `setConfig` validation, entity-change detection) — covered in `ha/lovelace-card-patterns`
- Programmatic dashboard generation (strategies that compute whole views/dashboards) — covered in `ha/lovelace-strategies`
- Detailed schema of the `hass`-object data channels (WebSocket, states, services) — covered in `ha/frontend-data-api`
- Build stacks (Vite, esbuild, Rollup) and TypeScript migration — separate follow-up spec
- Theming by the view or panel itself — both consume the HA theme, they do not define one

## Requirements

### Custom view: element & properties (`hass`/`lovelace`/`cards`)

- **MUST** define the view as a custom element — the render framework is free (Lit, Preact, etc.), but it **MUST NOT** use React, since React is explicitly excluded
- **MUST** accept the properties HA sets: `hass` (`HomeAssistant`), `lovelace` (`Lovelace`), `index` (`number`), `cards` (`Array<LovelaceCard | HuiErrorCard>`) and `badges` (`LovelaceBadge[]`)
- **MUST NOT** create cards or badges itself — these are created and maintained by the core code and handed to the view; the view loads them and displays them in a custom layout
- **SHOULD** provide a non-trivial layout (for example a grid) that goes beyond the default masonry layout — otherwise the custom view does not justify its effort

### Custom view: `setConfig` & custom data

- **MUST** implement `setConfig(config)` with the signature `setConfig(config: LovelaceViewConfig): void`
- **SHOULD** store card-level persistence data through the `view_layout` block in the card configuration (for example `key`, X/Y coordinates, `width`, `height`) when the view needs to store a card's location or dimensions
- **MUST NOT** place view-specific persistence data anywhere other than the `view_layout` block of the respective card — `view_layout` is the intended storage location

### Custom view: card interaction (`lovelace`)

- **MUST** trigger the core frontend dialogs through the three `ll-*` events — `ll-edit-card` (detail `{ path }`), `ll-delete-card` (detail `{ path }`), and `ll-create-card` (detail: none) — to edit, delete, or add a card, instead of re-implementing the card lifecycle itself
- **MUST** dispatch the event from the affected card element via `this.dispatchEvent(new CustomEvent("ll-edit-card", { detail: { path: [...] } }))`, with `path` as `[number]` or `[number, number]`
- **SHOULD** read the edit-mode state from the `lovelace` object (`editMode`) before offering edit affordances (edit/delete/add)

### Custom panel: registration (`panel_custom`)

- **MUST** register the panel through the `panel_custom` component in `configuration.yaml`
- **MUST** set a unique `url_path` per `panel_custom` entry — `url_path` must be unique for each `panel_custom` config
- **MUST** reference the panel module through `module_url` (ES module), for example `module_url: /local/example-panel.js`
- **MAY** pass arbitrary data to the panel through the `config` block — it becomes available at runtime as `panel.config`
- **SHOULD** set `sidebar_title` and `sidebar_icon` so the panel is sensibly linked from the sidebar

### Custom panel: element properties (`hass`/`narrow`/`route`/`panel`)

- **MUST** define the panel as a custom element and register it through `customElements.define(...)`
- **MUST** accept the properties HA sets: `hass` (object, current HA state), `narrow` (boolean, whether the panel should render in narrow mode) and `panel` (object, panel information; config available as `panel.config`)
- **SHOULD** additionally accept `route` (object), which HA sets on the panel element
- **MUST NOT** access the HA state outside the `hass` property — `hass` is the real-time channel to the Home Assistant object

### JS versions & `embed_iframe`

- **SHOULD** ship without ES5 support as long as no wider browser support is required — the ES5 variant has wider browser reach but at a cost of size and performance
- **MUST** load the ES5 custom-elements adapter before defining the element when ES5 support is required, via `window.loadES5Adapter().then(function() { customElements.define('my-panel', MyCustomPanel) })`
- **MAY** set `embed_iframe` in the `panel_custom` config when the panel should be served embedded in an iframe instead of loaded directly into the frontend

## Acceptance Criteria

- [ ] Custom view is a custom element (not React) and accepts `hass`, `lovelace`, `index`, `cards`, `badges`
- [ ] Custom view does not create cards/badges itself but renders the core-supplied ones in a custom layout
- [ ] Custom view implements `setConfig(config)` with the `LovelaceViewConfig` signature
- [ ] Card-level persistence runs through the `view_layout` block of the card configuration
- [ ] Card interaction runs through `ll-edit-card` / `ll-delete-card` / `ll-create-card` with the correct `path` detail
- [ ] Custom panel is registered in `configuration.yaml` through `panel_custom` with a unique `url_path`
- [ ] Panel module is referenced through `module_url`
- [ ] Panel element accepts `hass`, `narrow`, `route`, and `panel` (config via `panel.config`)
- [ ] ES5 support, if needed, loads the ES5 adapter via `window.loadES5Adapter()` before `customElements.define`
- [ ] Quality scale marker: not part of the HA quality scale

## Open Questions

- **View vs. panel as delivery shape**: When is a custom view sufficient (layout inside the dashboard) and when does it take a full-page custom panel (its own sidebar page)? A heuristic for the choice is missing.
- **`route` property depth**: The `panel` API table lists `hass`, `narrow`, and `panel`, but the example element additionally renders `route`. Is `route` guaranteed to be set or optional? Currently formulated as a SHOULD.
- **`embed_iframe` trade-offs**: The docs name `embed_iframe` as an option without deepening the consequences (isolation vs. direct `hass` access). When is iframe embedding worth it?
- **ES5 requirement threshold**: From which browser matrix does the ES5 adapter justify the size and performance overhead? Currently formulated as "only when needed".
- **`js_url` vs. `module_url`**: Registration supports both classic scripts (`js_url`) and ES modules (`module_url`). When is `js_url` still sensible instead of requiring `module_url` throughout?
