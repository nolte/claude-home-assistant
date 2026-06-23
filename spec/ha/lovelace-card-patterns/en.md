# HA Integration: Lovelace Card Patterns

Status: draft

## Context

Custom Lovelace cards are the frontend extension of an HA Custom Integration: a JavaScript module that registers an `HTMLElement`, is recognised by HA as a card type, and can be selected in the dashboard. HA's card API is declaratively shaped — the card receives the `hass` object as a property setter, renders its state via shadow DOM, and supplies lifecycle callbacks (`setConfig`, `getCardSize`, `getGridOptions`, `getConfigElement`, `getStubConfig`) that drive the card-picker UI and resize behaviour.

`nolte/kamerplanter-ha` ships custom cards as vanilla JS under `custom_components/<domain>/www/`, **auto-registered** in `__init__.py` through `StaticPathConfig`, so users do not have to add the cards to Lovelace resources by hand. The repo additionally codifies three non-obvious rules in `spec/ha-integration/LOVELACE-CARD-PATTERNS.md`: (1) **entity-change detection** in the `set hass` callback prevents unnecessary re-rendering on every HA state tick; (2) **HA CSS custom properties** (`var(--primary-text-color)`, …) instead of hard-coded colours; (3) **`getGridOptions`** for responsive card layouts.

This spec lifts the pattern into a generic obligation. The Lovelace card lives in the same repo as the Custom Integration but is a separate delivery shape — card development can happen independently of integration development.

Quality scale marker: **Bronze** (custom cards are not part of the HA quality scale; the pattern here is nolte-portfolio-specific and lives outside the scale).

## Goals

- Establish vanilla JS as the standard stack for custom cards — no Lit, no React, no build step (at least for the initial generation; build stack is a separate follow-up spec)
- Make auto-registration of cards from the `www/` folder in `__init__.py` mandatory — users do not have to add anything to Lovelace resources by hand
- Establish entity-change detection as the default pattern inside the `set hass` callback
- Shadow DOM as the default render target — no style leaks into the HA frontend
- HA CSS custom properties instead of hard-coded colours — the card respects the active HA theme automatically
- `getGridOptions` for responsive card sizes, so cards scale sensibly inside HA sections (HA 2024.3+)

## Non-Goals

- Build stacks (Vite, esbuild, Rollup, Webpack) — separate follow-up spec once the first card justifies a build step
- TypeScript / Lit-based cards — separate follow-up spec
- Custom-card editor UIs (beyond `getConfigElement`) — only addressed here at minimum-bar level, not as a detailed pattern
- HACS distribution for standalone cards (outside an integration) — different delivery axis
- Frontend theming by the card itself — cards consume the HA theme, they do not define one

## Requirements

### Card file layout

- **MUST** place custom cards under `custom_components/<domain>/www/<card-name>.js`
- **SHOULD** carry one JS module per card type — no mega-file with multiple cards
- **MAY** place additional assets (SVG icons, locally hosted fonts) in the same `www/` folder as long as they remain reachable through auto-registration
- **MUST NOT** place cards in a second, parallel `www/` folder at the repository root — the HA-integration `www/` is the canonical source

### Auto-registration in `__init__.py`

- **MUST** register every card file from `custom_components/<domain>/www/` in `async_setup_entry` (or a dedicated setup hook) via `await hass.http.async_register_static_paths([StaticPathConfig(url_path=..., path=..., cache_headers=False)])`
- **MUST** set `cache_headers=False` — otherwise updated card JS files end up stale for users with cached browser resources
- **SHOULD** additionally register the card type through `frontend.add_extra_js_url(hass, url_path)` once HA supports it natively per integration — currently a workaround through `frontend.async_register_built_in_panel` or dynamic Lovelace-resource extension
- **MUST NOT** require the user to add the card to Lovelace resources by hand — auto-registration is mandatory

### `HTMLElement` subclass

- **MUST** define the card as a subclass of `HTMLElement` — no Lit / React / Vue wrappers
- **MUST** call `customElements.define("<card-type>", <CardClass>)`, with `<card-type>` in lowercase kebab-case, prefixed by the integration domain (for example `domain-resource-card`)
- **MUST** call `window.customCards = window.customCards || []; window.customCards.push({type: "<card-type>", name: "...", description: "...", preview: false})`, so the card appears in the Lovelace card picker
- **MUST** implement `connectedCallback()` that calls `attachShadow({mode: "open"})` and triggers initial rendering — no direct manipulation of the light DOM

### `setConfig(config)` lifecycle

- **MUST** implement `setConfig(config)` — HA invokes it once the user saves the card configuration
- **MUST** reject invalid configurations with `throw new Error("...")` — HA catches the error and renders an error card
- **SHOULD** check schema mandatory fields in `setConfig` (`if (!config.entity) throw new Error("entity is required")`)
- **MUST NOT** run I/O or async calls inside `setConfig` — the lifecycle is synchronous

### `set hass(hass)` with entity-change detection

- **MUST** implement `set hass(hass)` as a setter property — HA sets it on every state tick
- **MUST** perform entity-change detection **before** triggering a re-render — compare `this._hass?.states[id] !== hass.states[id]` across every entity the card consumes
- **MUST NOT** render on every `hass` setter call — HA ticks multiple times per second; a blanket re-render every tick burns CPU cycles for nothing
- **SHOULD** force the initial render when `this._rendered` is still `false` (`if (changed || !this._rendered) this._render(); this._rendered = true`)

### `getCardSize` and `getGridOptions`

- **MUST** implement `getCardSize()` and return a value >= 1 (one unit equals ~50 px in the pre-sections Lovelace world)
- **SHOULD** implement `getGridOptions()` — HA 2024.3+ sections layout uses it to scale the card responsively; default shape: `return { columns: 6, rows: 3, min_columns: 3, min_rows: 2 }`
- **MAY** carry a dynamic `getGridOptions()` when the card needs different sizes depending on configuration — the return object is evaluated per render

### `getConfigElement` and `getStubConfig`

- **SHOULD** implement `static getConfigElement()` and `static getStubConfig()` — the HA UI then renders the custom editor and supplies a default config on drag-and-drop
- **MUST NOT** define the editor in the same file as the card when it grows non-trivial — a separate `<card-name>-editor.js` file is cleaner

### Shadow DOM and CSS

- **MUST** render card content inside the shadow DOM, opened via `attachShadow({mode: "open"})` in `connectedCallback`
- **MUST** use HA CSS custom properties instead of hard-coded colours:
  - `var(--primary-text-color)` for primary text
  - `var(--secondary-text-color)` for secondary text
  - `var(--state-icon-color)` for icon colours
  - `var(--error-color)` for error messages
  - `var(--divider-color)` for divider lines
  - `var(--ha-card-background)` and `var(--card-background-color)` for card backgrounds
- **MUST NOT** use hexadecimal or named colours as defaults — the card then does not follow the active HA theme
- **SHOULD** use `var(--ha-font-weight-bold)` and similar font properties instead of hard-coding font weights numerically

### Performance discipline

- **MUST NOT** block synchronously in `set hass` (no `JSON.parse` over huge states, no `forEach` over thousands of entities) — the heavy lifting is entity-change detection, not the setter
- **SHOULD** bundle heavy DOM manipulations in `requestAnimationFrame` callbacks when re-renders touch more than a few nodes

## Acceptance Criteria

- [ ] Card file lives under `custom_components/<domain>/www/<card-name>.js`
- [ ] `__init__.py` registers the card JS file via `StaticPathConfig` with `cache_headers=False`
- [ ] Card type is registered via `customElements.define`; name is lowercase kebab-case with an integration prefix
- [ ] Card appears in the Lovelace card picker via `window.customCards` push
- [ ] `setConfig(config)` is implemented; invalid configs throw `Error`
- [ ] `set hass(hass)` performs entity-change detection before re-render
- [ ] `getCardSize()` and `getGridOptions()` are implemented
- [ ] Shadow DOM is set up in `connectedCallback` via `attachShadow({mode: "open"})`
- [ ] CSS uses HA custom properties (`var(--primary-text-color)`, …); no hard-coded hex colours
- [ ] A `grep` for `#[0-9A-Fa-f]{3,6}` in the card stylesheet returns no hits (except inside custom-property definitions)
- [ ] Quality scale marker: **Bronze** (portfolio-specific, not HA quality scale)

## Open Questions

- **TypeScript migration**: When does a follow-up spec require TypeScript / Lit-based cards? `kamerplanter-ha` is vanilla JS; a build step for multi-file cards becomes inevitable eventually.
- **Card-editor requirement depth**: `getConfigElement` and `getStubConfig` as SHOULD or MUST? Currently SHOULD — a missing `getStubConfig` leads to empty default cards on drag-and-drop.
- **Auto-registration mechanism**: HA has no official "register one card per integration" API. Currently via `StaticPathConfig` plus a user hint to Lovelace resources. When does that land natively?
- **Multi-card repos**: When the integration ships multiple cards, what is the layout? `www/<card-1>.js`, `www/<card-2>.js`, …? Currently formulated; a heuristic for "one card per concept" is missing.
- **HACS frontend distribution for standalone cards**: Distributed outside an integration (HACS plugin category instead of integration category) — separate follow-up spec?
