# Skill: `ha-card-editor-add`

Status: draft

## Context

`ha/lovelace-card-editor` defines the graphical configuration editor surface of a custom Lovelace card: HA queries static hooks on the card type — `getConfigElement` for a custom editor element, `getConfigForm` for the built-in form editor, `getStubConfig` for a default config on drag-and-drop. The editor element and the card communicate configuration changes back to the dashboard through a `config-changed` CustomEvent (`bubbles`, `composed`, `detail.config`). No skill augments this surface so far; the base card lifecycle (file layout, `setConfig`, `set hass`, registration) belongs to `ha/lovelace-card-patterns` and is produced by `ha-lovelace-card-scaffold`.

This skill augments an `ha-form`-based visual configuration editor into an **existing** custom card: the editor custom element (a `LitElement` with `setConfig` and a `render()` over `<ha-form>` with a schema and `computeLabel`), the card hook `static getConfigElement()`, `static getStubConfig()` for the default config, and the `customElements.define` registration — conformant to `ha/lovelace-card-editor`. Generation is offline; the skill never deploys to a running HA instance.

## Scope

Augmenting **one** visual `ha-form` editor per run into an existing custom card under `www/` (or the declared card path): the editor element (a `LitElement` with `setConfig`, a `hass` setter, a `render()` over `<ha-form>` with `schema`/`.data`/`.computeLabel` and a `_valueChanged` handler that dispatches `config-changed`), `static getConfigElement()` on the card class, `static getStubConfig()` without the `type:` parameter, and the `customElements.define` registration. The skill reads `ha/lovelace-card-editor` and validates.

## Goals

- Derive a registered editor element from an existing card and its configuration shape, and augment it spec-conformantly
- Enforce the `getConfigElement` contract: `static getConfigElement()` returns an element registered via `customElements.define`
- Fix the `config-changed` event as the sole return channel: `bubbles: true`, `composed: true`, the new config in `event.detail.config`, dispatched only on an actual change
- Anchor the `ha-form` editor with a `schema` (selectors preferred), `computeLabel`, and — where the form needs it — `computeHelper`/`assertConfig`
- Ensure `getStubConfig()` returns a default config **without** the `type:` parameter for drag-and-drop
- Preserve the editor lifecycle: `setConfig(config)` does not mutate the config; changes flow solely through `config-changed`

## Non-Goals

- Greenfield scaffolding of the card itself (file layout, `set hass`, render, registration) — `ha-lovelace-card-scaffold`
- Base card lifecycle and portfolio house style — `ha/lovelace-card-patterns`
- Entity-selector filtering (domain, device-class, supported-features filters in the selector) — `ha/lovelace-card-entity-selector`
- The built-in form editor `getConfigForm` as an alternative to the custom element — referenced, but not the path this skill generates
- Translations of editor labels — a separate axis, `ha/translations`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a config editor to my card", "wire up the ha-form editor", "make my card configurable in the UI"
  - "give my card a visual editor", "add getConfigElement to my card"
  - "füge meiner Card einen Editor hinzu"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the existing card (file/class name) the editor is augmented onto
- **MAY** capture: the configuration fields and their selectors (`entity`, `text`, `boolean`, …), the editor-element tag name, and whether `computeHelper`/`assertConfig` are needed

### Pre-flight (in order — abort on first failure)

- **MUST** check that the target card exists (a card file under the declared card path, registered via `customElements.define`); if no card exists, point at `ha-lovelace-card-scaffold` and abort
- **MUST** check that the card carries no editor hook yet (`getConfigElement` or `getConfigForm`); on collision abort instead of adding a second hook
- **MUST** read the `ha/lovelace-card-editor` spec
- **MUST NOT** overwrite an existing editor element or an existing tag name

### Generation rules (from `ha/lovelace-card-editor`)

- **MUST** create an editor custom element as a `LitElement` that implements `setConfig(config)` and accepts the `hass` property as a setter
- **MUST** register the element via `customElements.define("<domain>-<card>-editor", <EditorClass>)`, in lowercase kebab-case with an integration-domain prefix
- **MUST** define `static getConfigElement()` on the card class, returning `document.createElement("<domain>-<card>-editor")`
- **SHOULD** realise the editor as an `ha-form`-driven surface: render `<ha-form>` in the editor `render()` with `.hass`, `.data` (the current config), `.schema` (a list, one entry per field with `name` and preferably `selector`), and `.computeLabel`, and bind the `value-changed` event of `<ha-form>` to a `_valueChanged` handler — `<ha-form>` inside the custom element is this skill's chosen implementation path, not prescribed by `ha/lovelace-card-editor` for the `getConfigElement` path (where `ha-form` is bound to the built-in `getConfigForm` path); verify against the official HA docs
- **MUST** dispatch in the `_valueChanged` handler a `config-changed` event with `bubbles: true`, `composed: true`, and `detail: { config: <newConfig> }`
- **MUST NOT** fire `config-changed` when the config is unchanged, and **MUST NOT** mutate the config passed to `setConfig` (only read / locally copy)
- **MUST** define `static getStubConfig()` on the card, returning a default config **without** the `type:` parameter
- **SHOULD** provide `computeLabel(schema)` for field-specific labels; returning `undefined` lets HA apply the known translation for generic field names like `entity`
- **SHOULD** add `computeHelper(schema)` for longer helper text and `assertConfig(config)` (throws an `Error` on incompatible input) where the form needs them
- **SHOULD** prefer selectors (`{ selector: { entity: {} } }`, `{ selector: { text: {} } }`, …) over native form types; verify selector options beyond those named here against `ha-form/types.ts`
- **SHOULD** carry the editor element in a separate `<card-name>-editor.js` file once it grows non-trivial — consistent with `ha/lovelace-card-patterns`
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: the editor element is a `LitElement` with `setConfig` and a `hass` setter, registered via `customElements.define`; `static getConfigElement()` returns this element; `render()` uses `<ha-form>` with `schema`/`.data`/`.computeLabel`; the handler dispatches `config-changed` with `bubbles`/`composed` and `detail.config`, without firing on an unchanged config; `static getStubConfig()` returns a config without `type:`; the card carries exactly one editor hook
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/lovelace-card-editor`, plus the changed file paths and the quality-scale marker (outside the HA quality scale, frontend delivery shape)

### Prohibitions

- **MUST NOT** augment more than one editor per run
- **MUST NOT** (re)scaffold the base card lifecycle or the card itself — that is `ha-lovelace-card-scaffold`
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill checks that a target card exists and carries no editor hook yet, and reads `ha/lovelace-card-editor`
- [ ] Editor element is a `LitElement` with `setConfig(config)` and accepts the `hass` property
- [ ] Editor element is registered via `customElements.define`, lowercase kebab-case with an integration-domain prefix
- [ ] `static getConfigElement()` on the card returns the registered editor element
- [ ] `render()` uses `<ha-form>` with `.data`, `.schema` (one entry per field with `name`/`selector`), and `.computeLabel`
- [ ] The handler dispatches `config-changed` with `bubbles: true`, `composed: true`, and `detail.config`, and does not fire on an unchanged config
- [ ] `static getStubConfig()` returns a default config **without** the `type:` parameter
- [ ] Report names the file paths and the quality-scale marker (outside the scale, frontend delivery shape)

## Open questions

- **Lit availability**: the HA-doc editor examples use `LitElement` (typically pulled in via CDN/bundle). If the target card is vanilla JS (the portfolio standard in `ha/lovelace-card-patterns`), the skill introduces a Lit dependency — should it instead generate a vanilla-JS editor or explicitly ask for the Lit source? Currently it follows the brief (`LitElement`) and flags the dependency.
- **`getConfigForm` alternative**: `ha/lovelace-card-editor` prefers the built-in `getConfigForm` path for simple cards. When does the skill advise `getConfigForm` over a custom element — and is that a separate generation path? Currently it generates the `getConfigElement` path and names `getConfigForm` as the alternative.
- **Selector drift**: `ha-form/types.ts` is the canonical selector source but drifts across HA releases. Which HA frontend version does the skill pin as the reference for available selectors?
