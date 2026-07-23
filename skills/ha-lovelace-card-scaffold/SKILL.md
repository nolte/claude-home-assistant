---
name: ha-lovelace-card-scaffold
description: Scaffolds a vanilla-JS Lovelace card under custom_components/<domain>/www/<card-name>.js with every mandatory lifecycle method, shadow DOM, entity-change detection, HA CSS custom properties, and auto-registration in __init__.py. Activate on phrasings like "scaffold a Lovelace card for the integration", "add a custom Lovelace card called `<name>`", "erstelle eine Custom-Card für `<Resource>`". Do not activate for greenfield setup (use ha-integration-scaffold), TypeScript / Lit cards, or card removal.
tags: [home-assistant, custom-integration, lovelace]
phase: design
summary: "Scaffolds a vanilla-JS Lovelace card under www/ with every mandatory lifecycle method, shadow DOM, entity-change detection, HA CSS properties, and auto-registration."
summary_de: "Scaffolded eine Vanilla-JS-Lovelace-Card unter www/ mit allen Pflicht-Lifecycle-Methoden, Shadow DOM, Entity-Change-Erkennung, HA-CSS-Properties und Auto-Registrierung."
use_when:
  - "you want to add a custom Lovelace card to an existing integration"
  - "you want a vanilla-JS card auto-registered through __init__.py"
dont_use_when:
  - situation: "You are setting up a greenfield integration"
    alternative: ha-integration-scaffold
see_also:
  - ha-integration-scaffold
  - ha-badge-add
  - ha-card-editor-add
  - ha-card-features-add
  - ha-card-preview-add
  - ha-lovelace-solution
---

# HA Lovelace Card Scaffold

Spec: `spec/claude/ha-lovelace-card-scaffold/en.md` (EN canonical) / `spec/claude/ha-lovelace-card-scaffold/de.md` (DE translation).

## Why this is a skill, not an agent

- **Mid-flow interactivity (decisive):** card name, target entities, and registration path are confirmed with the operator before scaffolding; corrections iterate in the same thread.
- **Quick, targeted change:** one new file under `www/` plus registration — main-conversation territory per the change-scope dimension.
- **Counter-dimension considered:** the lifecycle boilerplate is template-like and self-contained (agent bias), but the scaffold is the first step of card development the conversation continues, so a report boundary would only add friction.

## When this skill activates

Use this skill when the user wants to add a custom Lovelace card to an existing HA Custom Integration — a vanilla-JS card living under `custom_components/<domain>/www/`, auto-registered through `__init__.py`.

## When NOT to activate

- greenfield integration setup → `ha-integration-scaffold`
- TypeScript or Lit cards → separate spec planned
- card removal → manual code edit
- multi-card scaffold in one call → call once per card

## Hard rules

1. **Never set hard-coded hex colours.** Use HA CSS custom properties (`var(--primary-text-color)` etc.) so the card respects the active theme.
2. **Always set `cache_headers=False` in the StaticPathConfig.** Otherwise updated cards stay stale for cached browsers.
3. **Always include `getCardSize`, `getGridOptions`, `setConfig`, and `getStubConfig`.** Sections-layout and the card picker depend on them.
4. **Always perform entity-change detection in `set hass`.** Re-rendering on every HA state tick burns CPU for nothing.
5. **Never reference external CDN assets.** Cards run offline-capable.
6. **Never ask the user to add Lovelace resources by hand.** Auto-registration is the contract.
7. **Name the element, class, and file per `ha/naming-conventions`.** The custom-element tag is `kebab-case` with at least one hyphen, namespaced by the integration `domain` (`<domain>-card`); if a config editor element is provided, its tag is `<tag>-editor`; the class is `PascalCase` ending in `Card`/`CardEditor`; the source file is `kebab-case`; the card `name`/`description` are English (see `spec/ha/naming-conventions/en.md`).
8. **Verify HA internals against the official docs.** Don't reproduce HA API signatures, lifecycle hooks, conventions, or schemas from memory — when uncertain, consult the official docs before generating or relying on it: Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant), architecture/blueprint/YAML docs [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see `spec/ha/upstream-docs-verification/en.md`).
9. **Honour the layout-antipattern catalogue.** Conform to `spec/ha/lovelace-layout-antipatterns/en.md`: default `grid_options.columns` to a multiple of 3 (`3`/`6`/`9`/`12`; B3); never hardcode a fixed **outer** pixel width or absolutely position the card to force its grid footprint (fixed inner-content heights are fine — `rows: "auto"` measures them; B4); set `columns: "full"` only when the card truly spans the section (B4); never use React as the render layer (B5).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root |
| `card_type` | yes | — | lowercase kebab-case, prefixed with `<domain>` |
| `display_name` | yes | — | card-picker name |
| `description` | yes | — | description in the picker |
| `entity_types` | yes | — | list of platforms the card consumes |
| `preview` | no | `false` | preview in picker |
| `grid_options` | no | `{columns: 6, rows: 3, min_columns: 3, min_rows: 2}` | sections-layout defaults |

## Pre-flight

1. `git -C <target_dir> rev-parse --is-inside-work-tree` and clean working tree
2. Read `domain` from `manifest.json`
3. `<target_dir>/custom_components/<domain>/www/<card-name>.js` does not exist
4. No existing `StaticPathConfig` entry for this card name in `__init__.py`

## Workflow

### 1) Resolve and confirm

Print the card name, type, picker label, grid options. Wait for user confirmation.

### 2) Generate

- `custom_components/<domain>/www/<card-name>.js` — the full skeleton (class, lifecycle methods, shadow DOM, render method with CSS custom properties, `customElements.define`, `window.customCards` push)
- `__init__.py` — append `StaticPathConfig` block (or extend the existing block list) with `cache_headers=False`
- `tests/test_lovelace_cleanup.py` (when present) — append assertion for the new card

### 3) Verify

```bash
ruff check custom_components/<domain>/__init__.py
pytest tests/ -v
```

### 4) Report

- file path of the new card
- auto-registration URL the card will be served from
- next-step hint to fill in the actual `_render` body

## Boundaries

- TypeScript / Lit cards → planned follow-up spec
- Card editor element → `ha-card-editor-add`
- HACS plugin distribution → out of scope
