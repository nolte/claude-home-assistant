---
name: ha-card-editor-add
description: Add an ha-form-based visual configuration editor to an existing custom Home Assistant Lovelace card, conforming to spec/ha/lovelace-card-editor. Generates the editor custom element (a LitElement implementing setConfig + a hass setter + a render() over <ha-form> with a schema, .data, and computeLabel, plus a _valueChanged handler that dispatches config-changed with bubbles/composed and detail.config), the card's static getConfigElement() returning that element, static getStubConfig() for a default config without the type parameter, and the customElements.define registration. Activate on "add a config editor to my card", "wire up the ha-form editor", "make my card configurable in the UI", "füge meiner Card einen Editor hinzu". Do not activate for scaffolding the card itself (ha-lovelace-card-scaffold), base card-level patterns (ha/lovelace-card-patterns), entity-selector filtering (ha/lovelace-card-entity-selector), or deploying to a live HA instance.
tags: [home-assistant, lovelace-card, frontend]
---

# HA Card Editor Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-card-editor-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-card-editor-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user names an existing card and reads back the editor element, the `ha-form` schema, and the conformance report; a skill keeps this on the visible command surface, like the sibling frontend skill (`ha-lovelace-card-scaffold`).
- **Mid-flow interactivity** — the editor field set, the selector choices, and the `computeHelper`/`assertConfig` decisions are a per-run dialogue the user approves before generation.
- **Bounded, inline generation** — one editor element plus the two card hooks (`getConfigElement`, `getStubConfig`) and the `customElements.define` registration fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the field/selector decisions belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** `ha-form`-based visual configuration editor to an **existing** custom Lovelace card — the editor `LitElement`, the card's `static getConfigElement()` and `static getStubConfig()`, and the `customElements.define` registration.

## When NOT to activate

- scaffolding the card itself (file layout, `set hass`, render, registration) → `ha-lovelace-card-scaffold`
- base card-level patterns and portfolio house style → `ha/lovelace-card-patterns`
- entity-selector filtering (domain / device-class / supported-features) → `ha/lovelace-card-entity-selector`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One editor, one run.** No multi-editor batches.
2. **Read [`ha/lovelace-card-editor`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-card-editor/de.md) first.** Do not generate from memory.
3. **Existing card required.** The card must already exist and be registered via `customElements.define`. If it does not exist, point at `ha-lovelace-card-scaffold` and abort. If it already carries an editor hook (`getConfigElement` or `getConfigForm`), abort rather than add a second.
4. **`getConfigElement` contract.** `static getConfigElement()` on the card returns `document.createElement("<domain>-<card>-editor")`; that element is registered beforehand via `customElements.define`, in lowercase kebab-case with an integration-domain prefix.
5. **Editor is a `LitElement`.** It implements `setConfig(config)` and accepts the `hass` property as a setter. This skill's chosen surface is `ha-form`-driven: a `render()` over `<ha-form>` with `.hass`, `.data` (the current config), `.schema` (a list, one entry per field with `name` and preferably `selector`), and `.computeLabel`. Note that `<ha-form>` inside a `getConfigElement` custom element is this skill's implementation choice, not mandated by `ha/lovelace-card-editor` for the `getConfigElement` path (where the spec binds `ha-form` to the built-in `getConfigForm`); verify against the official HA docs.
6. **`config-changed` is the sole return channel.** The `_valueChanged` handler dispatches a `config-changed` event with `bubbles: true`, `composed: true`, and `detail: { config: newConfig }` — **never** on an unchanged config, and **never** by mutating the config passed to `setConfig`.
7. **`getStubConfig` without `type:`.** `static getStubConfig()` returns a default config **without** the `type:` parameter; the card picker adds it itself.
8. **Selectors preferred.** Prefer selectors (`{ selector: { entity: {} } }`, `{ selector: { text: {} } }`, …) over native form types; add `computeLabel`, and `computeHelper`/`assertConfig` where the form needs them; verify selector options beyond the named ones against `ha-form/types.ts`.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; an existing card file under the declared card path |
| `card` | yes | — | the existing card (file / class name) the editor is augmented onto |
| `fields` / `selectors` | no | inferred + confirmed | the config fields and their `ha-form` selectors |
| `editor_tag` | no | `<domain>-<card>-editor` | the editor element tag name |
| `computeHelper` / `assertConfig` | no | asked when needed | helper text / config assertion |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. The target card exists under the declared card path and is registered via `customElements.define`. If not, point at `ha-lovelace-card-scaffold` and abort.
2. The card carries no editor hook yet (`getConfigElement` or `getConfigForm`). On collision, abort.
3. Read `ha/lovelace-card-editor`.
4. The editor element / tag name is not already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State the target card, the editor tag name, the field set and their selectors, and whether `computeHelper`/`assertConfig` are needed, in one paragraph. Flag that a `LitElement` editor introduces a Lit dependency if the card is vanilla JS. Wait for confirmation.

### 2) Generate

| Artifact | What |
|---|---|
| editor element | `LitElement` with `setConfig(config)`, `hass` setter, `render()` over `<ha-form>` (`.hass`/`.data`/`.schema`/`.computeLabel`) + `_valueChanged` dispatching `config-changed` |
| registration | `customElements.define("<domain>-<card>-editor", <EditorClass>)` |
| card hook | `static getConfigElement()` returning the editor element |
| stub | `static getStubConfig()` returning a default config without `type:` |

Add `computeLabel`, and `computeHelper`/`assertConfig` only where the form needs them. Carry the editor in a separate `<card-name>-editor.js` file once it grows non-trivial.

### 3) Validate and report

Validate offline (editor is a `LitElement` with `setConfig` + `hass` setter, registered via `customElements.define`; `getConfigElement()` returns it; `render()` uses `<ha-form>` with `schema`/`.data`/`.computeLabel`; the handler dispatches `config-changed` with `bubbles`/`composed` and `detail.config`, not on an unchanged config; `getStubConfig()` returns a config without `type:`; the card carries exactly one editor hook). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/lovelace-card-editor` acceptance criteria, plus the changed file paths and the quality-scale marker (outside the HA quality scale, frontend delivery shape).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Scaffolding the card itself → `ha-lovelace-card-scaffold`
- Base card-level patterns → `ha/lovelace-card-patterns`
- Entity-selector filtering → `ha/lovelace-card-entity-selector`
- Deploy to live HA → out of scope
