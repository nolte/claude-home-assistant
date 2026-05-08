# Skill: `ha-lovelace-card-scaffold`

Status: draft

## Context

Custom Lovelace cards (see `ha/lovelace-card-patterns`) live under `custom_components/<domain>/www/<card-name>.js`, are auto-registered in `__init__.py` via `StaticPathConfig`, use vanilla JS plus shadow DOM, perform entity-change detection in the `set hass` setter, and build their styling on HA CSS custom properties. Manual card code regularly forgets mandatory lifecycle methods (`getCardSize`, `getGridOptions`, `setConfig` validation, `getStubConfig`), produces hard-coded colours instead of HA custom properties, or forgets the auto-registration in `__init__.py`.

This skill scaffolds a vanilla-JS card with every mandatory method, correct shadow-DOM init, entity-change-detection skeleton, and the auto-registration block in `__init__.py`. The actual card logic (what data is rendered, which layout, which interactions) stays a consumer task; the skill ships the spec-conformant skeleton.

## Scope

The skill scaffolds **one** card per call. It does not delete cards, does not merge them, does not modify existing auto-registrations. On conflict (card with the same name exists) it aborts.

## Goals

- Card skeleton with every `ha/lovelace-card-patterns` MUST method
- Auto-registration in `__init__.py` so the user does not have to configure Lovelace resources by hand
- Shadow DOM plus HA CSS custom-property skeleton — no hard-coded styling
- Entity-change detection in the `set hass` setter as the default pattern
- `getStubConfig` plus optional `getConfigElement` stub, so drag-and-drop in the Lovelace UI works

## Non-Goals

- TypeScript or Lit-based cards — separate follow-up spec when build stack becomes relevant
- Card-editor UI — the skill scaffolds a `getConfigElement` stub; the actual editor interface remains a consumer task
- Multi-card scaffolding per call
- HACS plugin distribution for standalone cards (outside the integration)

## Requirements

### Activation triggers

- **MUST** activate on:
  - "scaffold a Lovelace card for the integration"
  - "add a custom Lovelace card called `<name>`"
  - "erstelle eine Custom-Card für `<Resource>`"
- **MUST NOT** activate on greenfield setup (`ha-integration-scaffold`) or card removal

### Inputs

- **MUST** collect:
  - `target_dir`
  - `card_type` — lowercase kebab-case, prefixed with `<domain>` (for example `<domain>-resource-card`)
  - `display_name` — Lovelace card-picker name
  - `description` — description in the card picker
  - `entity_types` — list of entity platforms the card consumes (`sensor`, `binary_sensor`, …)
- **SHOULD** collect:
  - `preview` (default `false`) — whether the card renders a preview in the picker
  - `grid_options` (default `{columns: 6, rows: 3, min_columns: 3, min_rows: 2}`) — sections-layout defaults

### Pre-flight

- **MUST** check:
  1. `target_dir` is a git repo, clean
  2. `<target_dir>/custom_components/<domain>/www/<card-name>.js` does not exist
  3. `__init__.py` does not yet contain a `StaticPathConfig` entry for this card name

### Generator choreography

- **MUST** create `custom_components/<domain>/www/<card-name>.js` with the following building blocks:
  - `class <PascalCardName> extends HTMLElement` — top-level class
  - `setConfig(config)` — throws `Error` on missing required fields
  - `set hass(hass)` with entity-change-detection skeleton
  - `getCardSize()` — default `3`
  - `getGridOptions()` — from the `grid_options` input
  - `static getStubConfig()` — default card config on drag-and-drop
  - `static getConfigElement()` — optional stub returning a `<custom-card-name>-editor` element (the editor itself is a user task)
  - `connectedCallback()` with `attachShadow({mode: "open"})` and an initial render call
  - `_render()` — skeleton with HA CSS custom properties (`var(--primary-text-color)`, `var(--secondary-text-color)`, `var(--state-icon-color)`, `var(--ha-card-background)`, `var(--divider-color)`)
  - `customElements.define(card_type, <PascalCardName>)` and `window.customCards` push at the file end
- **MUST** add an auto-registration block in `__init__.py` that calls `await hass.http.async_register_static_paths([StaticPathConfig(url_path=..., path=..., cache_headers=False)])` for the card file
- **MUST** set `cache_headers=False` — without it, updated cards stay stale for browsers with cached resources
- **MUST NOT** write hard-coded hex colours or pixel values without CSS-custom-property wrap into the skeleton

### Test extension

- **MUST** extend the `tests/test_lovelace_cleanup.py` test (when present, from `ha-test-harness-augment`) with an assertion for the newly auto-registered card — the `StaticPathConfig` URL map must contain the new card path

### Forbidden

- **MUST NOT** set `cache_headers=True` — see above
- **MUST NOT** reference external CDN URLs as asset sources — cards run offline-capable
- **MUST NOT** ask the user to add Lovelace resources by hand

## Acceptance Criteria

- [ ] `custom_components/<domain>/www/<card-name>.js` exists with every mandatory method
- [ ] `__init__.py` carries the auto-registration block with `cache_headers=False`
- [ ] `customElements.define(...)` and `window.customCards` push exist at the file end
- [ ] Shadow DOM is set up in `connectedCallback` via `attachShadow({mode: "open"})`
- [ ] CSS uses HA custom properties — no hard-coded hex colours
- [ ] `tests/test_lovelace_cleanup.py` (when present) carries an assertion for the new card
- [ ] `ruff check custom_components/<domain>/__init__.py` runs cleanly

## Open Questions

- **Editor-element completeness depth**: `getConfigElement` as stub vs. full editor — threshold?
- **TypeScript migration**: When does a follow-up spec require TS / Lit?
- **Multi-card repos**: When the integration ships multiple cards, does the layout change? Currently each card lives as its own file.
- **Card-test pattern**: Vanilla-JS card tests are rare in HA — is there a convention?
