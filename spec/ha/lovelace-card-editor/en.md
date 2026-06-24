# HA Integration: Lovelace Card Editor (`ha-form`)

Status: draft

## Context

A custom Lovelace card can ship more than a YAML-configurable render target: it can bring its own graphical configuration surface into the dashboard card editor. HA queries static hooks on the card type for this — `getConfigElement` for a custom editor element, `getConfigForm` for the built-in form editor (`ha-form`), and `getStubConfig` for a default config on drag-and-drop from the card picker. The editor element and the card communicate configuration changes back to the dashboard through a `config-changed` CustomEvent.

This spec covers **only** the graphical configuration editor surface. The base card lifecycle — file layout under `www/`, auto-registration in `__init__.py`, `setConfig`, `set hass`, shadow-DOM CSS, `getCardSize`/`getGridOptions` — is codified in the sibling spec `ha/lovelace-card-patterns` (portfolio house style, vanilla JS) and is **not duplicated** here, only referenced.

Note on the base class: the official editor examples in the HA documentation use `LitElement`; the portfolio standard in `ha/lovelace-card-patterns` is vanilla JS. Both are valid — a custom element is a custom element. This spec stays base-class-agnostic and prescribes neither Lit nor vanilla JS for the editor element.

Quality scale marker: custom cards are **not part of the HA quality scale**; the card editor is a frontend delivery shape and, like the sibling spec, lives outside the scale.

## Goals

- Establish the graphical card editor as a deliberate, separate delivery shape of the custom card — not as an afterthought of the render code
- Clearly delimit `getConfigElement` for non-trivial editors from `getConfigForm` (`ha-form`) for simple configuration requirements
- Fix the `config-changed` CustomEvent (`bubbles`, `composed`, `detail.config`) as the sole return channel from editor to dashboard
- Make `getStubConfig` mandatory for sensible default configs on drag-and-drop from the card picker
- Anchor the `ha-form` form editor with a schema (selectors), `computeLabel`, and `assertConfig` as the preferred path for simple editors
- Document the per-entity card suggestion (`getEntitySuggestion`) as an opt-in mechanism without making the card picker noisy

## Non-Goals

- Base card lifecycle (`setConfig`, `set hass`, shadow DOM, CSS, `getCardSize`, `getGridOptions`, auto-registration) — covered in `ha/lovelace-card-patterns`
- The full selector option list — canonical in the frontend repo under `ha-form/types.ts`, only referenced here, not copied
- Translations of editor labels — a separate axis, addressed in `ha/translations`
- Data fetching in the editor (`hass` states, service calls) beyond the editor lifecycle properties — addressed in `ha/frontend-data-api`
- `tap_action`, `more-info`, or other card interaction patterns — not part of the graphical editor surface

## Requirements

### `getConfigElement` & editor element

- **MUST** define `static getConfigElement()` on the card class for a custom editor, returning a registered custom element (`return document.createElement("<card-editor>")`) — HA displays this element in the dashboard card editor
- **MUST** register the element returned by the editor beforehand via `customElements.define("<card-editor>", <EditorClass>)`, with `<card-editor>` in lowercase kebab-case and an integration-domain prefix
- **SHOULD** carry the editor element in a separate `<card-name>-editor.js` file once it grows non-trivial — consistent with `ha/lovelace-card-patterns`
- **MUST NOT** define `getConfigElement` and `getConfigForm` on the same card at the same time — either a custom editor element or the built-in form editor, not both

### `config-changed` event

- **MUST** communicate configuration changes from the editor element back to the dashboard through a `config-changed` event — the dashboard listens for it and adopts the new config
- **MUST** construct the event with `bubbles: true` and `composed: true` so it crosses the editor's shadow-DOM boundary and reaches the dashboard
- **MUST** carry the new configuration in `event.detail.config` (`event.detail = { config: newConfig }`)
- **MUST NOT** blindly fire the `config-changed` event on every keystroke when the config is unchanged — dispatch only on an actual configuration change

### Built-in form editor (`ha-form` + selectors)

- **SHOULD** use the built-in form editor instead of a custom editor element for cards with relatively simple configuration requirements — via `static getConfigForm()` returning a form schema
- **MUST** return an object from `getConfigForm()` with the required key `schema` — a list of schema objects, one per form field, each with `name` and (preferably) `selector`
- **SHOULD** provide `computeLabel(schema)` for field-specific labels and `computeHelper(schema)` for longer helper text below the field; returning `undefined` lets HA apply the known translation for generic field names like `entity`
- **SHOULD** define `assertConfig(config)` that throws an `Error` on incompatible input — that disables the visual editor until a subsequent call passes without throwing
- **SHOULD** prefer selectors (`{ selector: { entity: {} } }`, `{ selector: { text: {} } }`, …) over native form types like `float` or `boolean`; `grid` and `expandable` containers structure more complex forms
- **MAY** look up the full selector and schema option list in the frontend repo under `ha-form/types.ts` — the options named here are not exhaustive

### `getStubConfig` & card suggestion

- **SHOULD** define `static getStubConfig()` returning a default card configuration **without** the `type:` parameter (in JSON form) — the card picker uses it on drag-and-drop
- **MUST NOT** include the `type:` parameter in the `getStubConfig` return object — the card picker adds it itself
- **MAY** suggest the card via `getEntitySuggestion(hass, entityId)` on the `window.customCards` entry for a selected entity — suggested custom cards appear in the card picker under a **Community** section (available since HA 2026.6)
- **MUST** return `null` from `getEntitySuggestion` when the entity is not sensibly supported by the card — the `hass`-object check on domain, device class, or supported features decides this
- **MUST** include the required field `config`, with the `type:` including the `custom:` prefix, in every returned suggestion object; set the optional `label` only when returning several variants
- **MUST NOT** suggest the card for every entity — that makes the picker noisy and leads users to the wrong card

### Editor lifecycle (`setConfig`/`hass`)

- **MUST** implement `setConfig(config)` on the editor element — HA calls it on setup of the config element to hand over the current configuration
- **MUST** accept the `hass` property as a setter on the editor element — HA updates it on state changes, along with the `lovelace` element carrying dashboard configuration information
- **MUST NOT** mutate the card configuration inside the editor `setConfig` — only read or locally copy the passed config, and report changes solely through `config-changed`

## Acceptance Criteria

- [ ] `static getConfigElement()` returns an editor element registered via `customElements.define`
- [ ] Editor element is named in lowercase kebab-case with an integration-domain prefix
- [ ] Card defines either `getConfigElement` or `getConfigForm` — not both
- [ ] Editor dispatches `config-changed` with `bubbles: true`, `composed: true`, and the new config in `event.detail.config`
- [ ] For `getConfigForm`: the return carries the required key `schema` (a list, one entry per field with `name` and `selector`)
- [ ] `computeLabel`/`computeHelper`/`assertConfig` are present where the form needs them
- [ ] `static getStubConfig()` returns a default config **without** the `type:` parameter
- [ ] `getEntitySuggestion` (if present) returns `null` for unsupported entities and sets `config` including the `custom:` prefix
- [ ] Editor element implements `setConfig(config)` and accepts the `hass` property
- [ ] Selector options beyond those named here are verified against `ha-form/types.ts`
- [ ] Quality scale marker: outside the HA quality scale (frontend delivery shape, portfolio-specific)

## Open Questions

- **`getConfigForm` vs. `getConfigElement` threshold**: At what configuration complexity does a custom editor element justify itself over the built-in form editor? Currently qualitative ("relatively simple requirements") — a hard heuristic (field count, nested containers) is missing.
- **`getEntitySuggestion` minimum version**: The mechanism is available only since HA 2026.6. How does the portfolio handle cards that must run on older HA versions — feature detection, hard floor at 2026.6?
- **Selector drift**: `ha-form/types.ts` is the canonical source but drifts across HA releases. When does the portfolio pin an HA frontend version as the reference for available selectors?
- **Editor translations**: `computeLabel` can supply its own translations or use HA's known field-name translations. How does this interlock with `ha/translations` — a dedicated label-translation table per card?
- **Editor data context**: The editor element receives `hass` and `lovelace`. How far may the editor read `hass` states (entity pre-fill, validation) before that belongs in `ha/frontend-data-api`?
