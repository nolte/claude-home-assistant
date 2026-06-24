# HA Integration: Lovelace Badges

Status: draft

## Context

Badges are small widgets that sit at the top of a Lovelace view, above all cards. HA ships a built-in badge (the entity badge), but integrations can define and use their own custom badges. A custom badge is shipped — very similarly to a custom card — as a JavaScript module that registers a custom element (`HTMLElement`/`LitElement` subclass), is recognised by HA as a badge type, and can be selected in the dashboard's badge picker.

This spec covers **custom badges** only — the small status elements at the head of a view. Custom cards (the larger content building blocks) are governed by `ha/lovelace-card-patterns`; the graphical editor UI is governed by `ha/lovelace-card-editor`; access to the `hass` object and the frontend data API is governed by `ha/frontend-data-api`. This spec does not duplicate those rules; it references them by slug.

The badge API is declaratively shaped: the badge receives the `hass` object as a property setter (HA sets it on every state tick) and the user configuration via `setConfig(config)` (HA calls it when the configuration changes — rarely). If `setConfig` throws an error, HA renders an error badge. Optional static methods (`getConfigElement`, `getStubConfig`) drive the graphical editor UI.

Quality scale marker: custom badges are **not part of the HA quality scale** — the pattern here lives outside the scale.

## Goals

- Establish custom badges as a custom element (`HTMLElement`/`LitElement` subclass), registered via `customElements.define`
- Make the badge visible in the dashboard's badge picker through a push into `window.customBadges`
- Establish the `setConfig(config)` lifecycle and the `hass` property-setter pattern as a mandatory contract
- Offer the graphical editor UI (`getConfigElement`/`getStubConfig`) as an optional but recommended layer — analogous to the card editor
- Document dashboard referencing via `type: custom:<badge-name>`

## Non-Goals

- Custom cards — governed by `ha/lovelace-card-patterns`, not duplicated here
- The detailed pattern of the graphical editor UI (event wiring, `config-changed` dispatch) — governed by `ha/lovelace-card-editor`, referenced here only at minimum-bar level
- The access pattern for the `hass` object and the frontend data API — governed by `ha/frontend-data-api`
- The built-in entity badge — HA-native, not a custom extension
- Build stacks (Vite, esbuild, Rollup) and TypeScript/Lit build pipelines — a separate follow-up spec

## Requirements

### Defining the badge (`HTMLElement`)

- **MUST** define the badge as a custom element — a subclass of `HTMLElement` (or `LitElement`)
- **MUST** leave it up to the element how it renders its DOM — Polymer, Angular, Preact, or another popular framework is allowed, **except** React
- **SHOULD** place the badge in its own file under `<config>/www/<badge-name>.js` and register it as a resource of type `module`
- **MUST NOT** use React as the rendering framework — custom elements and React are not compatible in HA badges

### Registration (`window.customBadges`)

- **MUST** call `customElements.define("<badge-type>", <BadgeClass>)` — the tag name determines the badge type `custom:<badge-type>`
- **SHOULD** push an object describing the badge into the `window.customBadges` array, so the badge appears in the dashboard's badge picker dialog (`window.customBadges = window.customBadges || []; window.customBadges.push({...})`)
- **MUST** set at least the required properties `type` and `name` in the push object
- **MAY** set the optional properties `description`, `documentationURL`, and `preview` — `documentationURL` adds a help link in the frontend badge editor; `preview` defaults to `false`

### `setConfig` & `hass`

- **MUST** implement `setConfig(config)` — HA calls it when the configuration changes (rare)
- **MUST** reject invalid configurations with `throw new Error("...")` — HA catches the error and renders an error badge
- **MUST** implement the `hass` property as a setter — HA sets it when the HA state changes (frequent); the badge must update itself to the latest state on every set
- **SHOULD** read the consumed entity's state from `hass.states[entityId]` and render a sensible fallback (for example `unavailable`) when the entity is missing

### Graphical configuration

- **SHOULD** define a static `getConfigElement()` method that returns a custom element for editing the user configuration — HA displays it in the dashboard's badge editor
- **SHOULD** define a static `getStubConfig()` method that returns a default badge configuration in JSON form (without the `type:` parameter) for the badge-type picker
- **MAY** define the config element in a separate file (for example `<badge-name>-editor.js`) and pull it in via `import`
- **MUST NOT** spell out the `config-changed` event pattern here — the graphical editor detail pattern is governed by `ha/lovelace-card-editor`

### Dashboard referencing

- **MUST** reference the badge in the dashboard via `type: "custom:<badge-type>"`, embedded in a view's `badges:` list
- **MUST** add a resource with the badge module's URL and type `module` to the dashboard configuration before the badge is usable
- **SHOULD** make the badge module reachable under `/local/<badge-name>.js` when the file lives in the `<config>/www` directory — after first creating the `www` folder, an HA restart is required for the files to be picked up

## Acceptance Criteria

- [ ] Badge is defined as a subclass of `HTMLElement` (or `LitElement`); React is not used as the rendering framework
- [ ] `customElements.define("<badge-type>", <BadgeClass>)` is called
- [ ] Badge appears in the badge picker via a `window.customBadges` push with at least `type` and `name`
- [ ] `setConfig(config)` is implemented; invalid configs throw `Error`
- [ ] `hass` property is implemented as a setter and updates the badge on every state tick
- [ ] `getConfigElement()` and `getStubConfig()` are implemented (or deliberately omitted)
- [ ] Badge is referenced in the dashboard via `type: "custom:<badge-type>"` in the `badges:` list
- [ ] A resource of type `module` with the badge module URL is added to the dashboard configuration
- [ ] Quality scale marker: **not part of the HA quality scale** (outside the scale)

## Open Questions

- **Editor requirement depth**: `getConfigElement` and `getStubConfig` as SHOULD or MUST? Currently SHOULD — a missing `getStubConfig` leads to empty default badges when added through the picker.
- **`LitElement` vs vanilla `HTMLElement`**: the HA docs allow both. Should the nolte portfolio mandate vanilla JS as the default, analogous to `ha/lovelace-card-patterns`, or is `LitElement` acceptable for badges?
- **Auto-registration**: should badge modules — analogous to the card auto-registration in `ha/lovelace-card-patterns` — be registered automatically from the integration `www/` folder instead of requiring a manual resource entry?
- **Delimitation against the editor slug**: how deeply may "graphical configuration" reference here without duplicating the `config-changed` pattern from `ha/lovelace-card-editor`?
