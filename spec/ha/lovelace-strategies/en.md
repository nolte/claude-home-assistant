# HA Integration: Lovelace Strategies

Status: draft

## Context

Custom strategies are custom elements that **generate dashboards and/or views programmatically** instead of declaring them statically (introduced in Home Assistant 2021.5). A strategy typically starts from a small strategy config and returns the full dashboard or view structure — comparable to a JSON/YAML config that is rendered into a dashboard at runtime. The built-in HA dashboards (for example the home-overview and energy dashboards) are themselves built with dashboard strategies.

There are two strategy kinds: a **dashboard strategy** generates a full dashboard configuration (`generate(config, hass)` returns `{ views: [...] }`); a **view strategy** generates the configuration of a single view (`generate(config, hass)` returns `{ cards: [...] }`). Both are loaded — like custom cards — as dashboard resources and have access to the Home Assistant API. Generation runs client-side in the frontend and, through `hass`, has access to states, entities, areas, and devices.

This spec covers only strategies that **generate** dashboards/views. Static custom cards are governed by `ha/lovelace-card-patterns`; custom view-layout elements are governed by `ha/lovelace-views-panels`. This spec references both by slug and does not duplicate them. The `hass` data-access pattern (`callWS` against the registries) is detailed in `ha/frontend-data-api`.

Quality scale marker: **not part of the HA quality scale** (custom strategies are a frontend delivery shape and live outside the scale; the pattern here is nolte-portfolio-specific).

## Goals

- Cleanly separate the two strategy kinds: dashboard strategy (`generate → views`) versus view strategy (`generate → cards`)
- Establish registration via the custom element `ll-strategy-dashboard-<id>` / `ll-strategy-view-<id>` with a static `async generate(config, hass)` as the binding pattern
- Establish referencing in the dashboard/view config via `strategy.type: custom:<id>` as the canonical entry point
- Make community dashboards discoverable in the new-dashboard dialog via `window.customStrategies`
- Make `getCreateSuggestions(hass)` usable for suggested values in the create dialog
- Provide for graphical strategy configuration via `getConfigElement` as an option
- Keep `hass` access (areas/devices/entities) deterministic and fast — generation blocks the initial dashboard rendering

## Non-Goals

- Static custom cards — governed by `ha/lovelace-card-patterns`, not duplicated here
- Custom view-layout elements (a custom view layout instead of generated cards) — governed by `ha/lovelace-views-panels`
- The frontend data-API pattern (`callWS`, registry queries) in detail — detailed in `ha/frontend-data-api`
- Build stacks (TypeScript, Lit, Vite) for strategy modules — separate follow-up spec once a strategy justifies a build step
- Contributions to the HA frontend repo itself (built-in strategies) — this spec only addresses custom strategies loaded as resources

## Requirements

### Dashboard strategy (`generate → views`)

- **MUST** define a static async method `static async generate(config, hass)` that returns an object with a `views` array
- **MUST** derive the full dashboard structure from the passed strategy `config` — the `config` is the small starting point that expands to the full structure
- **SHOULD** guard values from `config` with defaults (for example `const title = config.title || "My demo dashboard"`), so the strategy renders even without a complete config
- **MAY** set a `strategy` reference instead of a finished `cards` array per generated view, so a view strategy generates the cards only when the view is opened

### View strategy (`generate → cards`)

- **MUST** define a static async method `static async generate(config, hass)` that returns an object with a `cards` array
- **SHOULD** use the view strategy to generate the cards of a single view while a dashboard strategy produces the view list — this keeps the first dashboard load small and builds each view only when it is opened
- **MAY** pass data the dashboard strategy already queried to the view strategy via strategy options, instead of re-querying it per view
- **MUST NOT** return a `views` array from a view strategy — view strategies return only `cards`

### Registration and referencing

- **MUST** register the strategy class via `customElements.define("ll-strategy-dashboard-<id>", <Class>)` (dashboard) or `customElements.define("ll-strategy-view-<id>", <Class>)` (view)
- **MUST** reference the strategy in the dashboard or view config through the `strategy` key with `type: custom:<id>` — `<id>` without the `ll-strategy-dashboard-`/`ll-strategy-view-` prefix
- **MUST** load the strategy as a dashboard resource (module resource), like a custom card — without a loaded resource the strategy is not resolvable
- **SHOULD** import custom cards a strategy includes in its generated output as their own resources — strategies and custom cards work alongside each other

### Accessing `hass` (areas/devices/entities)

- **MUST** query registry data via `hass.callWS(...)` when generation needs areas, devices, or entities (`config/area_registry/list`, `config/device_registry/list`, `config/entity_registry/list`)
- **SHOULD** parallelise independent registry queries via `Promise.all([...])` instead of serialising them
- **SHOULD** keep generation deterministic and fast — the same `config` plus the same `hass` state produce the same structure; generation blocks the initial dashboard rendering
- **MAY** read `hass.config` (for example `hass.config.location_name`) to personalise generated content

### Graphical configuration

- **SHOULD** define `static getConfigElement()` that returns a custom element for editing the strategy config — HA displays it in the dashboard-settings dialog
- **MUST** have the config element implement a `setConfig(config)` — HA calls it on setup
- **MUST** communicate changes back through a `config-changed` custom event (`bubbles: true, composed: true, detail: { config: newConfig }`)
- **SHOULD** set `configRequired = true` when the strategy does not work without configuration — HA then enforces the config editor before dashboard creation
- **MAY** set `noEditor = true` when the strategy does not support graphical configuration

### Community-dashboard dialog

- **SHOULD** register a dashboard strategy via `window.customStrategies = window.customStrategies || []; window.customStrategies.push({...})` so it appears in the new-dashboard dialog under "Community dashboards" (introduced in HA 2026.5)
- **MUST** set `type` (the strategy type without the `custom:` prefix) and `strategyType: "dashboard"` on the push — both are required
- **MAY** set `name`, `description`, and `documentationURL` — friendly name, short text, and documentation link for the picker
- **SHOULD** define `static getCreateSuggestions(hass)` that suggests `title` and/or `icon` as default values for the create dialog — these values are only defaults and users can change them

## Acceptance Criteria

- [ ] Dashboard strategy has `static async generate(config, hass)` and returns `{ views: [...] }`
- [ ] View strategy has `static async generate(config, hass)` and returns `{ cards: [...] }`
- [ ] Strategy is registered via `customElements.define("ll-strategy-dashboard-<id>", ...)` or `ll-strategy-view-<id>`
- [ ] Dashboard/view config references the strategy via `strategy.type: custom:<id>`
- [ ] Strategy is loaded as a dashboard resource (module)
- [ ] Registry access (areas/devices/entities) runs via `hass.callWS(...)`, with independent queries parallelised via `Promise.all`
- [ ] Graphical configuration (if present) supplies a `getConfigElement` with `setConfig` and a `config-changed` event
- [ ] Community dashboard is registered via a `window.customStrategies` push with `type` and `strategyType: "dashboard"`
- [ ] `getCreateSuggestions(hass)` (if present) supplies `title`/`icon` as default suggestions
- [ ] Quality scale marker: **not part of the HA quality scale** (portfolio-specific)

## Open Questions

- **Strategy options vs. re-query**: The docs pass registry data from the dashboard to the view strategy through strategy options. When is passing it through worth it versus a fresh `callWS` query per view? A heuristic for the threshold is missing.
- **Determinism boundary**: Generation is meant to be deterministic, but `hass.states` ticks. How far may a strategy react to live states without re-generation noticeably delaying the initial rendering?
- **TypeScript/Lit migration**: The docs recommend Lit `ReactiveElement` over `HTMLElement` and typing via TypeScript/JSDoc. When does a follow-up spec require a build step for strategy modules?
- **`frontend-data-api` overlap**: The `callWS` registry pattern is formulated here only at minimum-bar level. What delimitation against `ha/frontend-data-api` applies once that spec exists?
- **`configRequired` vs. `getCreateSuggestions`**: Both drive the create flow. How do an enforced config editor and suggested default values interact when both are set?
