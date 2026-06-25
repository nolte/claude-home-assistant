# Skill: `ha-card-features-add`

Status: draft

## Context

`ha/lovelace-card-features` defines the card-feature layer: the small interactive control rows rendered **inside** a host card (for example the tile card) that inherit its context — not a standalone dashboard element. A feature is shipped like a custom card as a JavaScript module that defines a custom element (`HTMLElement` or `LitElement`), and is registered through `window.customCardFeatures.push({ type, name, ... })` so it becomes selectable in the card editor. It receives `hass`, a `config` set through `setConfig(config)`, and a `context` object carrying the parent card's `entity_id` (or `area_id`). An `isSupported(hass, context)` predicate decides whether the feature is applicable to the selected entity; configurable features additionally supply `static getConfigElement` and `static getStubConfig`. No skill augments this so far.

This skill augments **one** card feature into an **existing** frontend module: the feature custom element with `setConfig`, the `hass` setter, the `isSupported(hass, context)` predicate as the single source of truth, the `render()` of the control row, optional `static getStubConfig`/`static getConfigElement`, and registration via `window.customCardFeatures` plus `customElements.define` — conformant to `ha/lovelace-card-features`. Custom cards and card features are **not part of the HA quality scale**; the pattern is portfolio-specific.

## Scope

Augmenting exactly one card feature per run into an existing frontend module (alongside the Custom Integration and its custom cards in the same repo): the feature custom element, `setConfig(config)` with a reject path, the `hass` setter, the `isSupported(hass, context)` predicate (used in `render()` **and** the registration entry), the `render()` of the control row with `this.hass.callService(...)`, optional `static getStubConfig`/`static getConfigElement`, and registration via `window.customCardFeatures.push({ type, name, ... })` plus `customElements.define("<feature-type>", <FeatureClass>)`. The skill reads `ha/lovelace-card-features` and validates offline.

## Goals

- Derive the matching feature from a described quick control and augment it spec-conformantly
- Register the feature via `window.customCardFeatures.push({ type, name, ... })` (mandatory properties `type` and `name`) and register the element via `customElements.define("<feature-type>", <FeatureClass>)` so the `type` resolves
- Enforce the synchronous `setConfig` lifecycle: adopt `this.config = config`, reject an invalid config with `throw new Error("Invalid configuration")`
- Codify the context flow as a contract: `hass`, `config`, `context` as properties; resolve the target `stateObj` from `this.hass.states[this.context.entity_id]`; handle a missing `context`/`entity_id`; render `null` while `config`/`hass`/`context` are missing or the entity is unsupported
- Establish the `isSupported(hass, context)` predicate as **one** source of truth — the same function in `render()` and in the `customCardFeatures` entry
- On interaction call the appropriate service via `this.hass.callService(domain, service, { entity_id })` and set `ev.stopPropagation()` so the click does not bubble up to the host card
- Use HA CSS custom properties (`--feature-height`, `--feature-border-radius`, `--feature-button-spacing`) for HA default integration

## Non-Goals

- A full custom card (card file layout, auto-registration, `set hass` lifecycle, `getCardSize`/`getGridOptions`) — `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- The feature's graphical config editor (the detailed `getConfigElement` mechanics) — `ha/lovelace-card-editor`
- Badges as a separate dashboard delivery shape — a separate follow-up spec
- The detailed structure of the `hass` object and frontend data access — `ha/frontend-data-api`
- Build stacks (Vite/esbuild/Rollup) and a mandatory TypeScript/Lit stack — a separate follow-up spec
- Delivery / loading of the feature JS in the frontend (`StaticPathConfig`) — `ha/lovelace-card-patterns`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a tile feature", "create a custom card feature", "add a control row to the tile card"
  - "expose a quick control inside the tile card for this entity"
  - "füge ein Tile-Feature hinzu", "erstelle ein Custom-Card-Feature"

### Inputs

- **MUST** capture: `target_dir` (repo root with the existing frontend module) and the quick control (prose), from which the skill derives `type`, `name`, and the target domain
- **MAY** capture: `feature_type` (the `customElements` type and `customCardFeatures` `type`), `name` (editor label), the target domain or applicability predicate, whether the feature is configurable (for example a `label`), and whether it is entity- rather than area-bound

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` contains an existing frontend module the feature can be augmented into
- **MUST** read the `ha/lovelace-card-features` spec
- **MUST** confirm the applicability predicate: which domain/entity the feature binds to, and whether it is entity- or area-bound
- **MUST NOT** overwrite an existing feature / an existing `feature_type`; on collision abort

### Generation rules (from `ha/lovelace-card-features`)

- **MUST** register the feature via `window.customCardFeatures = window.customCardFeatures || []; window.customCardFeatures.push({ type, name, ... })` and set the mandatory properties `type` and `name`
- **MUST** register the element via `customElements.define("<feature-type>", <FeatureClass>)` and let it extend `HTMLElement` or `LitElement`
- **MUST** implement `setConfig(config)` (`this.config = config`) and reject a missing/invalid config with `throw new Error("Invalid configuration")`
- **MUST** carry `hass`, `config`, and `context` as properties (the host card sets them) and resolve the target `stateObj` from `this.hass.states[this.context.entity_id]`, handling a missing `context`/`entity_id`
- **MUST** return `null` (no rendering) while `config`/`hass`/`context` are not set or the feature does not support the entity
- **MUST** render controls and on interaction call `this.hass.callService(domain, service, { entity_id })` on the target entity
- **SHOULD** call `ev.stopPropagation()` in the interaction handler so the click does not bubble up to the host card
- **SHOULD** provide an `isSupported(hass, context)` function that returns `boolean`, resolves the `stateObj` from `context.entity_id` through `hass.states`, returns `false` when no `stateObj` exists, and checks applicability by domain (not by a single entity ID)
- **MUST** use the same predicate function in `render()` (before rendering the controls) **and** in the `isSupported` entry of `window.customCardFeatures` — one source of truth
- **SHOULD** for configurable features implement `static getStubConfig()` returning a default config including `type: "custom:<feature-type>"`, and set `configurable: true` in the `customCardFeatures` entry; for a graphical configuration add `static getConfigElement()` (detailed in `ha/lovelace-card-editor`)
- **MUST NOT** require `getConfigElement`/`getStubConfig` for a feature without additional configuration — `configurable` then stays at the default `false`
- **MAY** read `context.area_id` when the feature is bound to the parent card's area rather than a single entity
- **SHOULD** use the HA CSS custom properties `--feature-height`, `--feature-border-radius`, and `--feature-button-spacing` for HA default integration
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: the feature is registered via `window.customCardFeatures.push({ type, name, ... })` (`type`/`name` set); the element is registered via `customElements.define` and extends `HTMLElement`/`LitElement`; `setConfig` is implemented and throws on an invalid config; the target `stateObj` is resolved from `this.hass.states[this.context.entity_id]` (a missing `context`/`entity_id` handled); `render()` returns `null` without `config`/`hass`/`context`; interaction calls `this.hass.callService(...)`; the same predicate function is used in `render()` and `isSupported`; configurable features set `configurable: true` plus `getStubConfig`/`getConfigElement`
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/lovelace-card-features`, plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**, portfolio-specific)

### Prohibitions

- **MUST NOT** augment more than one feature per run
- **MUST NOT** implement a full custom card or a graphical config editor
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Feature is registered via `window.customCardFeatures.push({ type, name, ... })`; `type` and `name` are set
- [ ] The element is registered via `customElements.define("<feature-type>", <FeatureClass>)` and extends `HTMLElement`/`LitElement`
- [ ] `setConfig(config)` is implemented; an invalid config throws `Error`
- [ ] On interaction a service is called via `this.hass.callService(domain, service, { entity_id })` on the target entity
- [ ] The target `stateObj` is resolved from `this.hass.states[this.context.entity_id]`; a missing `context`/`entity_id` is handled
- [ ] `render()` returns `null` while `config`/`hass`/`context` are missing or the feature does not support the entity
- [ ] `isSupported(hass, context)` is set and returns `false` when no `stateObj` exists
- [ ] The same predicate function is used in `render()` and in the `isSupported` entry
- [ ] Configurable features set `configurable: true` and supply `getStubConfig`/`getConfigElement`
- [ ] Report names the file paths and the quality-scale marker (not part of the HA quality scale, portfolio-specific)

## Open questions

- **`isSupported` SHOULD or MUST**: `ha/lovelace-card-features` carries the predicate as SHOULD; a missing predicate lets the editor propose the feature for any entity. Should the skill effectively enforce it for a device-/domain-specific control?
- **Vanilla vs. Lit**: The HA doc uses `LitElement`, `ha/lovelace-card-patterns` mandates vanilla `HTMLElement` for cards. Does the skill follow the existing cards' vanilla mandate or allow Lit for features? Currently it follows the style found in the target module.
- **Editor depth**: `getStubConfig`/`getConfigElement` are carried only as SHOULD, with a pointer to `ha/lovelace-card-editor`. When is a configurable feature without a graphical editor still acceptable?
- **Delivery**: How is the feature JS shipped within the integration and loaded in the frontend — through the same `StaticPathConfig` mechanism as custom cards? Open in `ha/lovelace-card-features`; the skill augments only the module, not the delivery path.
