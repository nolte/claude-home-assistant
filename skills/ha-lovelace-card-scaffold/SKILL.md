---
name: ha-lovelace-card-scaffold
description: Scaffold a vanilla-JS Lovelace card under custom_components/<domain>/www/<card-name>.js with every mandatory lifecycle method, shadow DOM, entity-change detection, HA CSS custom properties, and auto-registration in __init__.py. Activate on phrasings like "scaffold a Lovelace card for the integration", "add a custom Lovelace card called `<name>`", "erstelle eine Custom-Card für `<Resource>`". Do not activate for greenfield setup (use ha-integration-scaffold), TypeScript / Lit cards, or card removal.
tags: [home-assistant, custom-integration, lovelace]
---

# HA Lovelace Card Scaffold

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-lovelace-card-scaffold/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-lovelace-card-scaffold/en.md).

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
7. **Name the element, class, and file per `ha/naming-conventions`.** The custom-element tag is `kebab-case` with at least one hyphen, namespaced by the integration `domain` (`<domain>-card`); if a config editor element is provided, its tag is `<tag>-editor`; the class is `PascalCase` ending in `Card`/`CardEditor`; the source file is `kebab-case`; the card `name`/`description` are English (see [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)).

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
- Card editor element → consumer task
- HACS plugin distribution → out of scope
