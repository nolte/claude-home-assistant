# Skill: `ha-badge-add`

Status: draft

## Context

`ha/lovelace-badges` defines the frontend's custom-badge layer: the small status widgets that sit at the top of a Lovelace view, above all cards. A custom badge is shipped — very similarly to a custom card — as a JavaScript module that registers a custom element (`HTMLElement` or `LitElement` subclass) via `customElements.define("<badge-type>", <BadgeClass>)`, is recognised by HA as a badge type, and is selectable in the dashboard's badge picker. The API is declarative: the badge receives `hass` as a property setter (HA sets it on every state tick) and the user configuration via `setConfig(config)` (HA calls it rarely); if `setConfig` throws an error, HA renders an error badge. Optional static methods (`getConfigElement`, `getStubConfig`) drive the graphical editor UI. No skill augments this so far.

This skill augments **one** custom badge into an **existing** frontend module: the badge custom element (with `setConfig`, the `hass` setter, and render), optional `getConfigElement` / `getStubConfig`, and the `window.customBadges` registration entry (`type`, `name`, `description`) — conformant to `ha/lovelace-badges`. The quality-scale marker is **not part of the HA quality scale** (outside the scale).

## Scope

Augmenting exactly one custom badge per run into an existing frontend module (an integration's `www/` folder or a standalone Lovelace module): the badge custom element (subclass of `HTMLElement` or `LitElement`), the `setConfig(config)` lifecycle, the `hass` property-setter pattern, the `customElements.define` call, the `window.customBadges` push (at least `type` and `name`), optional `getConfigElement` / `getStubConfig`, and dashboard referencing via `type: "custom:<badge-type>"` plus the `module` resource note. The skill reads `ha/lovelace-badges` and validates offline.

## Goals

- Produce a custom badge from a described status display as a custom element (`HTMLElement`/`LitElement` subclass), registered via `customElements.define`
- Enforce the `setConfig(config)` lifecycle and the `hass` property-setter pattern as a mandatory contract — update on every state tick, `throw new Error` on invalid config
- Make the badge visible in the badge picker through a push into `window.customBadges` with at least `type` and `name`
- Offer the graphical editor UI (`getConfigElement` / `getStubConfig`) as an optional but recommended layer — analogous to the card editor
- Document dashboard referencing (`type: "custom:<badge-type>"` in the `badges:` list) and the `module` resource

## Non-Goals

- Custom cards (the larger content building blocks) — `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- Tile card features — `ha/lovelace-card-features`
- Dashboard strategies — `ha/lovelace-strategies`
- The `config-changed` detail pattern of the graphical editor — `ha/lovelace-card-editor`, referenced here only at minimum-bar level
- The `hass` access pattern and the frontend data API — `ha/frontend-data-api`
- The built-in entity badge (HA-native) and build stacks (Vite/esbuild/Rollup, TS/Lit pipelines)

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a custom badge", "create a Lovelace badge", "register a custom badge"
  - "füge ein Custom-Badge hinzu", "erstelle ein Lovelace-Badge"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the status display (prose), from which the skill derives the badge content and the consumed entity
- **MAY** capture: `badge_type` (the `customElements.define` tag name → `custom:<badge-type>`), the display `name`, a `description`, the render framework (`HTMLElement` vs `LitElement`), and whether a graphical editor (`getConfigElement` / `getStubConfig`) should be generated

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` is an existing frontend module (a `www/` directory or an existing Lovelace module); otherwise point at `ha-lovelace-card-scaffold` for greenfield
- **MUST** resolve the `badge_type` tag name (infer + confirm) and check it against `ha/naming-conventions`
- **MUST** read the `ha/lovelace-badges` spec
- **MUST NOT** overwrite an existing badge module or an existing `badge_type`; on collision abort

### Generation rules (from `ha/lovelace-badges`)

- **MUST** define the badge as a custom element — a subclass of `HTMLElement` (or `LitElement`) — and register it via `customElements.define("<badge-type>", <BadgeClass>)`; the tag name determines the badge type `custom:<badge-type>`
- **MUST NOT** use React as the rendering framework — custom elements and React are not compatible in HA badges
- **MUST** implement `setConfig(config)` and reject invalid configurations with `throw new Error("...")` — HA catches the error and renders an error badge
- **MUST** implement the `hass` property as a setter — the badge updates itself to the latest state on every set
- **SHOULD** read the consumed entity's state from `hass.states[entityId]` and render a sensible fallback (for example `unavailable`) when the entity is missing
- **SHOULD** produce a push into `window.customBadges` (`window.customBadges = window.customBadges || []; window.customBadges.push({...})`) so the badge appears in the badge picker, with at least the required properties `type` and `name`
- **MAY** set the optional push properties `description`, `documentationURL`, and `preview` (`preview` defaults to `false`)
- **SHOULD** define the static methods `getConfigElement()` (returns an editor custom element) and `getStubConfig()` (returns a default config without the `type:` parameter) — or deliberately omit them
- **MUST NOT** spell out the `config-changed` event pattern here — that is governed by `ha/lovelace-card-editor`
- **SHOULD** place the badge in its own file under `<config>/www/<badge-name>.js` and name identifiers per `ha/naming-conventions`; verify HA internals against the official docs (`ha/upstream-docs-verification`)
- **MUST** document dashboard referencing: `type: "custom:<badge-type>"` in a view's `badges:` list, plus a `module` resource with the badge module URL (typically `/local/<badge-name>.js`), noting that an HA restart is required after first creating the `www` folder

### Validation & report

- **MUST** validate offline: the badge subclasses `HTMLElement`/`LitElement` (no React); `customElements.define` is called; `setConfig` is implemented and throws on invalid config; the `hass` property is a setter; the `window.customBadges` push carries at least `type` and `name`; `getConfigElement`/`getStubConfig` are implemented or deliberately omitted; dashboard referencing and the `module` resource are documented
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/lovelace-badges`, plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**)

### Prohibitions

- **MUST NOT** augment more than one badge per run
- **MUST NOT** use React as the rendering framework
- **MUST NOT** deploy to a running HA instance or write the dashboard/resource configuration of a live instance

## Acceptance criteria

- [ ] Badge is defined as a subclass of `HTMLElement` (or `LitElement`); React is not used as the rendering framework
- [ ] `customElements.define("<badge-type>", <BadgeClass>)` is called
- [ ] Badge appears in the badge picker via a `window.customBadges` push with at least `type` and `name`
- [ ] `setConfig(config)` is implemented; invalid configs throw `Error`
- [ ] `hass` property is implemented as a setter and updates the badge on every state tick
- [ ] `getConfigElement()` and `getStubConfig()` are implemented (or deliberately omitted)
- [ ] Dashboard referencing (`type: "custom:<badge-type>"` in the `badges:` list) and the `module` resource are documented
- [ ] Report names the file paths and the quality-scale marker **not part of the HA quality scale**

## Open questions

- **Editor requirement depth**: `getConfigElement` and `getStubConfig` as SHOULD or MUST? Currently SHOULD (mirroring `ha/lovelace-badges`) — a missing `getStubConfig` leads to empty default badges when added through the picker.
- **`LitElement` vs vanilla `HTMLElement`**: `ha/lovelace-badges` leaves both open. Should the skill mandate vanilla JS as the default, analogous to `ha/lovelace-card-patterns`, or is `LitElement` acceptable for badges?
- **Auto-registration**: should the skill — analogous to the card auto-registration — automate the `window.customBadges` push from the integration `www/` folder instead of requiring a manual resource entry?
