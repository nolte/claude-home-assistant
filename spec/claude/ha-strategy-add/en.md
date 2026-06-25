# Skill: `ha-strategy-add`

Status: draft

## Context

`ha/lovelace-strategies` defines the frontend delivery shape that **generates dashboards and/or views programmatically** instead of declaring them statically: custom strategies are custom elements with a static `static async generate(config, hass)` method that returns the full structure from a small strategy `config`. There are two kinds — a **dashboard strategy** (`generate → { views: [...] }`) and a **view strategy** (`generate → { cards: [...] }`). Both are loaded — like custom cards — as a dashboard resource (module), registered via `customElements.define("ll-strategy-dashboard-<id>", …)` or `ll-strategy-view-<id>`, and referenced in the config via `strategy.type: custom:<id>`. No skill augments this so far.

This skill augments **one** strategy (dashboard or view) into an **existing** frontend module: the strategy class with the static `generate(config, hass)`, the `customElements.define` registration, the resource loading, optionally `getConfigElement`/`getCreateSuggestions`, and — for dashboard strategies — the `window.customStrategies` push for the community-dashboard dialog. Quality scale marker: **not part of the HA quality scale** (portfolio-specific). The skill works offline and never deploys to a running HA instance.

## Scope

Augmenting exactly one strategy per run (`dashboard` or `view`) into an existing frontend module (typically `custom_components/<domain>/www/`): the strategy class, the static `static async generate(config, hass)`, the `customElements.define("ll-strategy-dashboard-<id>"/"ll-strategy-view-<id>", …)` registration, the resource loading (for example `StaticPathConfig` in `__init__.py`), the optional graphical configuration (`getConfigElement` + `setConfig` + `config-changed`), and — for dashboard strategies — the `window.customStrategies` push with optional `getCreateSuggestions`. The skill reads `ha/lovelace-strategies` and validates.

## Goals

- Pick the right kind (dashboard vs. view) from the described generation intent and augment it spec-conformantly
- Enforce the `generate` contract: a dashboard strategy returns `{ views: [...] }`, a view strategy returns `{ cards: [...] }` — a view strategy **never** returns a `views` array
- Enforce registration (`customElements.define` with the correct `ll-strategy-…` prefix), referencing (`strategy.type: custom:<id>`), and resource loading as the binding pattern
- Keep `hass` access to areas/devices/entities via `hass.callWS(...)` with `Promise.all` parallelisation and config defaults deterministic and fast — generation blocks the initial dashboard rendering
- Optionally wire up the graphical configuration and the community-dashboard discoverability (`window.customStrategies`, `getCreateSuggestions`) correctly

## Non-Goals

- Static custom cards (one card, no generator) — `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- Custom view-layout elements and panels (a custom view layout instead of generated cards) — `ha/lovelace-views-panels`
- Custom badges — `ha/lovelace-badges`
- The frontend data-API pattern (`callWS`, registry queries) in detail — `ha/frontend-data-api`
- Build stacks (TypeScript, Lit, Vite) for strategy modules — a separate follow-up spec
- Contributions to the HA frontend repo itself (built-in strategies) — only custom strategies loaded as resources are addressed here

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a dashboard strategy", "auto-generate views with a strategy", "create a custom Lovelace strategy"
  - "generate this dashboard / view programmatically"
  - "füge eine Strategy hinzu", "generiere die Views automatisch über eine Strategy"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the generation intent (prose), from which the skill derives the kind and `<id>`
- **MAY** capture: `kind` (`dashboard`/`view`), the `<id>`, which registry data (areas/devices/entities) generation needs, whether a graphical configuration (`getConfigElement`) is needed, and — for dashboard strategies — whether the `window.customStrategies` push should happen

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` is an existing frontend module (for example `custom_components/<domain>/manifest.json` exists; read `domain` if present)
- **MUST** derive the kind (or ask) and confirm: a dashboard strategy generates the view list, a view strategy generates the cards of a single view
- **MUST** read the `ha/lovelace-strategies` spec
- **MUST NOT** overwrite an existing strategy / `<id>` / `customElements.define` registration; on collision abort

### Generation rules (per kind, from `ha/lovelace-strategies`)

- **MUST** for dashboard strategies define a `static async generate(config, hass)` that returns `{ views: [...] }`, and derive the full dashboard structure from the passed `config`
- **MUST** for view strategies define a `static async generate(config, hass)` that returns `{ cards: [...] }`
- **MUST NOT** return a `views` array from a view strategy — view strategies return only `cards`
- **SHOULD** guard values from `config` with defaults (for example `const title = config.title || "…"`), so the strategy renders even without a complete config
- **MAY** set a `strategy` reference instead of a finished `cards` array per generated view, so the view strategy generates the cards only when the view is opened; and pass data the dashboard strategy already queried to the view strategy via strategy options instead of re-querying it per view
- **MUST** register the strategy class via `customElements.define("ll-strategy-dashboard-<id>", …)` (dashboard) or `customElements.define("ll-strategy-view-<id>", …)` (view) and load it as a dashboard resource (module), like a custom card — without a loaded resource the strategy is not resolvable
- **MUST** document the referencing via `strategy.type: custom:<id>` — `<id>` without the `ll-strategy-dashboard-`/`ll-strategy-view-` prefix
- **MUST** query registry data via `hass.callWS(...)` when generation needs areas/devices/entities (`config/area_registry/list`, `config/device_registry/list`, `config/entity_registry/list`), and parallelise independent queries via `Promise.all([...])`
- **SHOULD** keep generation deterministic and fast — the same `config` plus the same `hass` state produce the same structure; generation blocks the initial dashboard rendering
- **SHOULD** for graphical configuration define a `static getConfigElement()` whose config element implements a `setConfig(config)` and communicates changes back through a `config-changed` custom event (`bubbles: true, composed: true, detail: { config: newConfig }`); set `configRequired = true` when the strategy does not work without config, otherwise `noEditor = true`
- **SHOULD** register a dashboard strategy via `window.customStrategies.push({...})` for the community-dashboard dialog; the push **MUST** set `type` (the strategy type without the `custom:` prefix) and `strategyType: "dashboard"` and **MAY** add `name`/`description`/`documentationURL` plus a `static getCreateSuggestions(hass)` (default `title`/`icon`)
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: the `generate` method is static + async and returns the kind-correct shape (`{ views }` or `{ cards }`, a view strategy without `views`); the `customElements.define` registration carries the correct `ll-strategy-…-<id>` prefix; the strategy is loaded as a dashboard resource (module); `strategy.type: custom:<id>` is documented; registry access (if present) runs via `hass.callWS` with `Promise.all`; a present graphical configuration supplies `getConfigElement` + `setConfig` + `config-changed`; a present `window.customStrategies` push carries `type` and `strategyType: "dashboard"`
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/lovelace-strategies`, plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**, portfolio-specific)

### Prohibitions

- **MUST NOT** augment more than one strategy per run
- **MUST NOT** emit a static custom card, a panel/view layout, or a badge as a strategy — these go to the respective sibling layer
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill derives the kind (or asks) and confirms dashboard-vs-view before generation
- [ ] Dashboard strategy has `static async generate(config, hass)` and returns `{ views: [...] }`; view strategy has `static async generate(config, hass)` and returns `{ cards: [...] }` (no `views` array)
- [ ] Strategy is registered via `customElements.define("ll-strategy-dashboard-<id>", …)` or `ll-strategy-view-<id>` and loaded as a dashboard resource (module)
- [ ] Referencing via `strategy.type: custom:<id>` is documented
- [ ] Registry access (areas/devices/entities) runs via `hass.callWS(...)`, with independent queries parallelised via `Promise.all`
- [ ] Graphical configuration (if present) supplies a `getConfigElement` with `setConfig` and a `config-changed` event
- [ ] Community dashboard (if a dashboard strategy) is registered via a `window.customStrategies` push with `type` and `strategyType: "dashboard"`; `getCreateSuggestions(hass)` (if present) supplies `title`/`icon` as default suggestions
- [ ] Report names the file paths and the quality-scale marker **not part of the HA quality scale** (portfolio-specific)

## Open questions

- **Module layout**: Do strategies always live under `custom_components/<domain>/www/` (like custom cards), or does a standalone frontend module without an integration justify a different resource layout? Currently the skill follows the card layout and asks when in doubt.
- **Dashboard + view strategy in one run**: A dashboard strategy often delegates to a view strategy. Should the skill be allowed to augment the pair together despite "one strategy per run", or strictly require two runs? Currently strictly one per run.
- **Determinism boundary**: `hass.states` ticks; how far may generation react to live states without noticeably delaying the initial rendering? `ha/lovelace-strategies` leaves it open.
- **`configRequired` vs. `getCreateSuggestions`**: How do an enforced config editor and suggested default values interact when both are set? Case-by-case.
