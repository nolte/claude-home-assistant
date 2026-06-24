# HA Integration: Lovelace Card Features (Tile Features)

Status: draft

## Context

Some dashboard cards support [features](https://www.home-assistant.io/dashboards/features/) — small interactive widgets that add quick controls for the bound entity inside a card (for example the tile card). HA ships a range of built-in features, but a repo is not limited to that selection: custom features are defined the same way as custom cards — as a JavaScript module that registers a custom element.

What sets a feature apart from a card: a card feature is not a standalone dashboard element but is rendered **inside** a host card and inherits its context. It receives `hass`, a `config` set through `setConfig`, and a `context` object carrying the parent card's entity (`entity_id`) or area (`area_id`) — the entity the feature acts on. An `isSupported(hass, context)` predicate decides whether the feature is applicable to the selected entity at all; configurable features additionally supply `static getConfigElement` and `static getStubConfig`.

This spec lifts the custom-card-feature pattern into a generic obligation for nolte-portfolio repos. Card features live in the same repo as the Custom Integration and its custom cards but are a separate delivery shape — the interactive controls inside a tile / other card, not the card itself.

Delimitation: `ha/lovelace-card-patterns` covers the custom cards (card file layout, auto-registration, `set hass` lifecycle, shadow DOM); this spec covers card features only. Editor UI mechanics (`getConfigElement`) are detailed in `ha/lovelace-card-editor`; the data flow out of `hass` is described in `ha/frontend-data-api`. Overlaps are referenced by slug, not repeated.

Quality scale marker: custom cards and custom card features are **not part of the HA quality scale**; the pattern here is nolte-portfolio-specific and lives outside the scale.

## Goals

- Establish registration of custom card features through `window.customCardFeatures` as the mandatory path, so features become selectable in the card editor
- Establish the feature element as a custom element (vanilla `HTMLElement` or `LitElement`) with a synchronous `setConfig` lifecycle
- Codify the context flow (`hass`, `config`, `context` with `entity_id` / `area_id`) as the standard contract between host card and feature
- Make the `isSupported(hass, context)` predicate mandatory, so the editor only proposes features for compatible entities
- Enable configurable features through `configurable: true` plus `static getConfigElement` / `static getStubConfig`
- Use HA CSS custom properties (`--feature-height`, `--feature-border-radius`, `--feature-button-spacing`) to integrate with the HA default design

## Non-Goals

- Custom cards themselves (card file layout, auto-registration, `set hass` lifecycle, `getCardSize` / `getGridOptions`) — covered by `ha/lovelace-card-patterns`
- Detailed editor UI mechanics beyond the minimum — covered by `ha/lovelace-card-editor`
- Detailed structure of the `hass` object and frontend data access — covered by `ha/frontend-data-api`
- Build stacks (Vite, esbuild, Rollup, Webpack) and TypeScript / Lit as a mandatory stack — separate follow-up spec
- HACS distribution for standalone features outside an integration — different delivery axis

## Requirements

### Register the feature (`window.customCardFeatures`)

- **MUST** register the feature via `window.customCardFeatures = window.customCardFeatures || []; window.customCardFeatures.push({ type, name, ... })`, so it appears in the card editor
- **MUST** set the mandatory properties `type` and `name` in the push object
- **SHOULD** set `isSupported` as `(hass, context) => boolean`, so the editor only proposes the feature for a compatible entity
- **MAY** set `configurable` — `true` when the feature has additional configuration (for example a `label`); the default is `false`
- **MUST** additionally register the element via `customElements.define("<feature-type>", <FeatureClass>)`, so the `type` can be resolved

### Feature element & `setConfig`

- **MUST** define the feature as a custom element extending `HTMLElement` or `LitElement` — analogous to defining a custom card
- **MUST** implement `setConfig(config)` and adopt the passed config (`this.config = config`)
- **MUST** reject a missing or invalid config with `throw new Error("Invalid configuration")`
- **MUST** render controls and, on interaction, call the appropriate service through `this.hass.callService(domain, service, { entity_id })` (for example `button.press` on the target entity)
- **SHOULD** call `ev.stopPropagation()` in the interaction handler, so the click does not bubble up to the host card

### Context (`hass`, `stateObj`)

- **MUST** carry `hass`, `config`, and `context` as properties of the feature element — the host card sets them
- **MUST** resolve the target `stateObj` from `this.hass.states[this.context.entity_id]` and handle that `context` or `context.entity_id` may be absent
- **MUST** return `null` (i.e. no rendering) while `config`, `hass`, or `context` are not yet set or the feature does not support the entity
- **MAY** read `context.area_id` when the feature is bound to the parent card's area rather than a single entity
- **SHOULD** use the HA CSS custom properties `--feature-height` (42px), `--feature-border-radius` (12px), and `--feature-button-spacing` (12px) to fit the HA default design

### `supported(stateObj)` predicate

- **SHOULD** provide an `isSupported(hass, context)` function that returns `boolean` and decides whether the feature is applicable to the selected entity
- **MUST** resolve the `stateObj` from `context.entity_id` through `hass.states` inside the predicate and return `false` when no `stateObj` exists
- **SHOULD** check applicability by domain (for example `stateObj.entity_id.split(".")[0] === "button"`), not by a single entity ID
- **MUST** use the same predicate function both in `render()` (before rendering the controls) and in the `isSupported` entry of `window.customCardFeatures` — one source of truth

### Configurable features (`getConfigElement` / `getStubConfig`)

- **SHOULD** implement `static getStubConfig()` for configurable features, returning a default config including `type: "custom:<feature-type>"`
- **SHOULD** implement `static getConfigElement()` for a graphical configuration — it works the same as with normal custom cards
- **MUST** set `configurable: true` in the `window.customCardFeatures` entry once the feature offers additional config options
- **MUST NOT** require `getConfigElement` / `getStubConfig` for a feature without additional configuration — `configurable` then stays at the default `false`

## Acceptance Criteria

- [ ] Feature is registered via `window.customCardFeatures.push({ type, name, ... })`; `type` and `name` are set
- [ ] The element is registered via `customElements.define("<feature-type>", <FeatureClass>)` and extends `HTMLElement` or `LitElement`
- [ ] `setConfig(config)` is implemented; an invalid config throws `Error`
- [ ] On interaction a service is called via `this.hass.callService(domain, service, { entity_id })` on the target entity
- [ ] The target `stateObj` is resolved from `this.hass.states[this.context.entity_id]`; a missing `context` / `entity_id` is handled
- [ ] `render()` returns `null` while `config` / `hass` / `context` are missing or the feature does not support the entity
- [ ] `isSupported(hass, context)` is set and returns `false` when no `stateObj` exists
- [ ] The same predicate function is used in `render()` and in the `isSupported` entry
- [ ] Configurable features set `configurable: true` and supply `getStubConfig` / `getConfigElement`
- [ ] Styling uses `--feature-height` / `--feature-border-radius` / `--feature-button-spacing` for HA default integration
- [ ] Quality scale marker: not part of the HA quality scale (portfolio-specific)

## Open Questions

- **`isSupported` SHOULD or MUST**: The HA doc recommends `isSupported` but keeps it optional. A missing predicate lets the editor propose the feature for any entity. Should the portfolio make it mandatory?
- **Editor depth**: `getConfigElement` / `getStubConfig` are carried here only as SHOULD, with a pointer to `ha/lovelace-card-editor`. When is a configurable feature without a graphical editor still acceptable?
- **Vanilla vs. Lit**: The HA doc example code uses `LitElement`; `ha/lovelace-card-patterns` mandates vanilla `HTMLElement` for cards. Should the same vanilla mandate apply to features, or is Lit allowed here?
- **`area_id` features**: Besides `entity_id`, the context also exposes `area_id`. What does an area-bound feature look like, and when is that sensible over an entity-bound feature? Currently carried only as MAY.
- **Registration / delivery**: How is the feature JS shipped within the integration and loaded in the frontend — through the same `StaticPathConfig` mechanism as custom cards (see `ha/lovelace-card-patterns`) or separately?
