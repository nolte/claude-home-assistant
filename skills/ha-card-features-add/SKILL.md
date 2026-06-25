---
name: ha-card-features-add
description: Augment an existing Home Assistant frontend module with one custom tile/card feature — the interactive control row rendered inside the tile card and other host cards — conforming to spec/ha/lovelace-card-features. Creates the feature custom element implementing the card-feature contract (setConfig with an invalid-config reject path, the hass setter, a shared isSupported(hass, context) predicate that resolves stateObj from context.entity_id as the single source of truth, the render() of the control row calling this.hass.callService(domain, service, {entity_id})), optional static getStubConfig / getConfigElement, and registration via window.customCardFeatures.push({type, name, ...}) plus customElements.define. Activate on "add a tile feature", "create a custom card feature", "add a control row to the tile card", "füge ein Tile-Feature hinzu", "erstelle ein Custom-Card-Feature". Do not activate for a full card (ha-lovelace-card-scaffold), a card config editor (ha/lovelace-card-editor), badges (separate spec), or deploying to a live HA instance.
tags: [home-assistant, frontend, lovelace, card-feature]
---

# HA Card Features Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-card-features-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-card-features-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes a quick control and reads back the feature element, its registration, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-lovelace-card-scaffold`, `ha-config-flow-augment`).
- **Mid-flow interactivity** — the applicability-predicate decision (which domain/entity, entity- vs. area-bound) and whether the feature is configurable are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — one feature custom element plus its registration fits inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the predicate decision and the host-card context binding belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** custom card feature — an interactive control row rendered inside the tile card (or another host card) — to an existing frontend module, acting on the parent card's bound entity.

## When NOT to activate

- a full custom card (card file layout, `set hass` lifecycle, `getCardSize`/`getGridOptions`) → `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- the feature's graphical config editor mechanics → `ha/lovelace-card-editor`
- badges as a separate dashboard delivery shape → separate follow-up spec
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One feature, one run.** No multi-feature batches.
2. **Read [`ha/lovelace-card-features`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-card-features/de.md) first.** Do not generate from memory.
3. **Register both ways.** Register the feature via `window.customCardFeatures = window.customCardFeatures || []; window.customCardFeatures.push({ type, name, ... })` with mandatory `type` and `name`, **and** register the element via `customElements.define("<feature-type>", <FeatureClass>)` so the `type` resolves. The element extends `HTMLElement` or `LitElement`.
4. **`setConfig` lifecycle.** Implement `setConfig(config)` (`this.config = config`) and reject a missing/invalid config with `throw new Error("Invalid configuration")`.
5. **Context contract.** Carry `hass`, `config`, `context` as properties (the host card sets them); resolve the target `stateObj` from `this.hass.states[this.context.entity_id]`, handling a missing `context`/`entity_id`; return `null` from `render()` while `config`/`hass`/`context` are unset or the entity is unsupported.
6. **Service on interaction.** Render controls and on interaction call `this.hass.callService(domain, service, { entity_id })` on the target entity; call `ev.stopPropagation()` so the click does not bubble up to the host card.
7. **One predicate, two uses.** Provide an `isSupported(hass, context)` predicate that resolves the `stateObj` from `context.entity_id`, returns `false` when none exists, and checks applicability by domain (not a single entity ID) — and use the **same** function in `render()` and in the `customCardFeatures` `isSupported` entry.
8. **Configurable only when configured.** For a configurable feature add `static getStubConfig()` (returning a default config incl. `type: "custom:<feature-type>"`), set `configurable: true`, and add `static getConfigElement()` for a graphical editor (see [`ha/lovelace-card-editor`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-card-editor/de.md)); never require `getConfigElement`/`getStubConfig` for a feature with no extra config — `configurable` stays `false`.
9. **HA default styling.** Use the CSS custom properties `--feature-height`, `--feature-border-radius`, `--feature-button-spacing`.
10. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; an existing frontend module the feature is added into |
| `control` | yes | — | the quick control the feature expresses, in prose |
| `feature_type` | no | derived | the `customElements` type and `customCardFeatures` `type` |
| `name` | no | derived | editor label |
| domain / predicate | no | inferred + confirmed | which domain/entity the feature binds to; entity- vs. area-bound |
| configurable | no | `false` | whether the feature offers extra config (e.g. a `label`) |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir` contains an existing frontend module the feature can be augmented into.
2. Read `ha/lovelace-card-features`.
3. Confirm the applicability predicate: which domain/entity the feature binds to, and whether it is entity- or area-bound.
4. The feature / `feature_type` is not already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `feature_type`, `name`, the target domain/predicate, entity- vs. area-bound, and whether the feature is configurable in one paragraph. Wait for confirmation.

### 2) Generate

Create the feature custom element extending `HTMLElement`/`LitElement` with: `setConfig(config)` (reject invalid config), the `hass`/`config`/`context` properties, the shared `isSupported(hass, context)` predicate, and `render()` (returns `null` until ready / when unsupported; calls `this.hass.callService(...)` on interaction with `ev.stopPropagation()`; styled with `--feature-*`). Register via `window.customCardFeatures.push({ type, name, ... })` and `customElements.define`. Add `static getStubConfig`/`static getConfigElement` and `configurable: true` only when the feature is configurable.

### 3) Validate and report

Validate offline (registered both ways with `type`/`name`; extends `HTMLElement`/`LitElement`; `setConfig` throws on invalid config; `stateObj` resolved from `this.hass.states[this.context.entity_id]` with missing `context`/`entity_id` handled; `render()` returns `null` when not ready; interaction calls `this.hass.callService(...)`; the same predicate is used in `render()` and `isSupported`; configurable features set `configurable: true` plus `getStubConfig`/`getConfigElement`). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/lovelace-card-features` acceptance criteria, plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**, portfolio-specific).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- A full custom card → `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- The feature's graphical config editor → `ha/lovelace-card-editor`
- Badges → separate follow-up spec
- Feature JS delivery / frontend loading (`StaticPathConfig`) → `ha/lovelace-card-patterns`
- Deploy to live HA → out of scope
