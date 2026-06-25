---
name: ha-badge-add
description: Add a custom Lovelace badge to an existing Home Assistant frontend module, conforming to spec/ha/lovelace-badges. Generates the badge custom element (an HTMLElement or LitElement subclass with setConfig, the hass property setter, and render), the customElements.define call (the tag name becomes custom:<badge-type>), optionally getConfigElement / getStubConfig for the graphical editor, and the window.customBadges registration entry (type, name, description) so the badge appears in the dashboard badge picker. Documents dashboard referencing via type "custom:<badge-type>" and the module resource. Activate on "add a custom badge", "create a Lovelace badge", "register a custom badge", "füge ein Custom-Badge hinzu", "erstelle ein Lovelace-Badge". Do not activate for a custom card (ha-lovelace-card-scaffold), a tile card feature (ha/lovelace-card-features), a dashboard strategy (ha/lovelace-strategies), or deploying to a live HA instance.
tags: [home-assistant, lovelace, frontend, badge]
---

# HA Badge Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-badge-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-badge-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes a status display and reads back the badge element, the registration entry, and the conformance report; a skill keeps this on the visible command surface, like the sibling frontend skill `ha-lovelace-card-scaffold`.
- **Mid-flow interactivity** — the `badge_type` tag-name decision and the "graphical editor yes/no" choice are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — one custom-element module plus its `window.customBadges` push and optional editor fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the tag-name and editor-depth decisions belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** custom badge — the small status widget at the head of a Lovelace view — to an existing frontend module (an integration's `www/` folder or a standalone Lovelace module).

## When NOT to activate

- a custom card (the larger content building block) → `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- a tile card feature → `ha/lovelace-card-features`
- a dashboard strategy → `ha/lovelace-strategies`
- the `config-changed` graphical-editor detail pattern → `ha/lovelace-card-editor`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One badge, one run.** No multi-badge batches.
2. **Read [`ha/lovelace-badges`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-badges/de.md) first.** Do not generate from memory.
3. **Custom element, no React.** Define the badge as a subclass of `HTMLElement` (or `LitElement`) and register it via `customElements.define("<badge-type>", <BadgeClass>)`; the tag name becomes the badge type `custom:<badge-type>`. **Never** use React as the rendering framework — custom elements and React are not compatible in HA badges.
4. **`setConfig` contract.** Implement `setConfig(config)`; reject an invalid configuration with `throw new Error("...")` — HA catches it and renders an error badge.
5. **`hass` setter.** Implement the `hass` property as a setter; the badge updates itself to the latest state on every set. Read the consumed entity from `hass.states[entityId]` and render a sensible fallback (e.g. `unavailable`) when it is missing (see [`ha/frontend-data-api`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/frontend-data-api/de.md)).
6. **Picker registration.** Push an entry into `window.customBadges` (`window.customBadges = window.customBadges || []; window.customBadges.push({...})`) with at least the required `type` and `name`; `description` / `documentationURL` / `preview` are optional (`preview` defaults to `false`).
7. **Graphical editor is optional.** Add the static `getConfigElement()` / `getStubConfig()` only when an editor is wanted; do **not** spell out the `config-changed` event pattern here — that is governed by [`ha/lovelace-card-editor`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/lovelace-card-editor/de.md).
8. **Document the wiring.** Reference the badge via `type: "custom:<badge-type>"` in a view's `badges:` list and add a `module` resource with the badge module URL (typically `/local/<badge-name>.js`); note the HA restart needed after first creating the `www` folder.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; an existing frontend module / `www/` directory must exist |
| `display` | yes | — | the status display the badge expresses, in prose (incl. the consumed entity) |
| `badge_type` | no | inferred + confirmed | the `customElements.define` tag name → `custom:<badge-type>` |
| `name` / `description` | no | derived | the badge-picker display name and optional description |
| `framework` | no | per project default | `HTMLElement` vs `LitElement` |
| `editor` | no | asked | generate `getConfigElement` / `getStubConfig` |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir` is an existing frontend module (a `www/` directory or an existing Lovelace module). If not, point at `ha-lovelace-card-scaffold` for greenfield and stop.
2. Resolve `badge_type` (infer + confirm) and check it against `ha/naming-conventions`.
3. Read `ha/lovelace-badges`.
4. The badge module / `badge_type` is not already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `target_dir`, the resolved `badge_type` (→ `custom:<badge-type>`), the display `name`, the chosen framework, and whether a graphical editor is generated, in one paragraph. Wait for confirmation.

### 2) Generate

- The badge custom element (subclass of `HTMLElement`/`LitElement`) with `setConfig(config)` (throwing on invalid config), the `hass` property setter (updating on every set, with an `unavailable` fallback), and the render.
- The `customElements.define("<badge-type>", <BadgeClass>)` call and the `window.customBadges` push (`type` + `name` mandatory; `description` optional).
- When `editor` is wanted, the static `getConfigElement()` / `getStubConfig()` (and an optional `<badge-name>-editor.js`).
- The dashboard wiring note: `type: "custom:<badge-type>"` in the `badges:` list and the `module` resource URL.

### 3) Validate and report

Validate offline (subclass of `HTMLElement`/`LitElement`, no React; `customElements.define` called; `setConfig` implemented and throwing on invalid config; `hass` is a setter; `window.customBadges` push carries `type` + `name`; `getConfigElement`/`getStubConfig` implemented or deliberately omitted; dashboard referencing + `module` resource documented). Emit a CONFORMANT / NEEDS-WORK report keyed to the `ha/lovelace-badges` acceptance criteria, plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**).

### 4) No deploy

The skill never deploys to a live HA instance and never writes a live dashboard/resource configuration. Surface the report and stop.

## Boundaries

- Custom card → `ha-lovelace-card-scaffold` / `ha/lovelace-card-patterns`
- Tile card feature → `ha/lovelace-card-features`
- Dashboard strategy → `ha/lovelace-strategies`
- Graphical-editor `config-changed` detail → `ha/lovelace-card-editor`
- Deploy to live HA → out of scope
