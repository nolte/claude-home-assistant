# HA Integration: `icons.json`

Status: draft

## Context

Home Assistant has allowed declaring **icons per translation key** through an `icons.json` next to `strings.json` since 2024.1 — for entities (default icon and state-specific icons) and for services. Before that, icons were set through `_attr_icon` properties or dynamic `icon` methods on every entity class, which led to drift between similar entities and hard-to-maintain in-code logic.

`nolte/kamerplanter-ha` uses `icons.json` consistently: default icons per `translation_key`, state-specific icons for enum sensors (for example different phase symbols), and service icons. Material Design Icons (`mdi:...`) are the default icon set; HA additionally supports SVG path icons, but skill output sticks with `mdi:`. This spec lifts the pattern into a generic obligation.

Quality scale marker: **Bronze** (icons via `icons.json` instead of in code are a Bronze convention; without icons HA renders generic default symbols, which is technically correct but UX-poor).

## Goals

- Make `icons.json` the only place for icon declarations — no `_attr_icon` hard-codes, no `icon` properties on entity classes
- Establish default icons per `translation_key` and state-specific icons for enum sensors as the standard pattern
- Carry service icons centrally, so the HA service UI renders consistent symbols
- Specify Material Design Icons (`mdi:...`) as the default icon set

## Non-Goals

- Custom SVG icons (own vector paths) — HA technically supports them, but skill output stays with `mdi:`; a follow-up spec covers SVG icons once the first integration needs them
- Branding icons (integration logo) — live in the `brand/` folder and follow a different convention; separate follow-up spec
- Lovelace card icons (card-specific icon) — card property, owned by `ha/lovelace-card-patterns`
- Per-language icon translation — icons are language-independent

## Requirements

### `icons.json` existence

- **MUST** include an `icons.json` in `custom_components/<domain>/` once the integration defines at least one entity or one service
- **SHOULD** cover every translation key from `strings.json` with a default icon — missing keys cause HA defaults to render, which usually do not fit

### Schema

`icons.json` is hierarchically structured by platform and translation key:

```text
{
  "entity": {
    "<platform>": {
      "<translation_key>": {
        "default": "mdi:<icon-name>",
        "state": {
          "<value>": "mdi:<icon-name>",
          ...
        }
      }
    }
  },
  "services": {
    "<service>": {
      "service": "mdi:<icon-name>"
    }
  }
}
```

- **MUST** carry platform names under `entity` as top-level keys (`sensor`, `binary_sensor`, `button`, `calendar`, `todo`, `switch`, `number`, `select`, …)
- **MUST** use the entity's `translation_key` as the key under each platform — same key as in `strings.json`
- **MUST** set at least `default` under `entity.<platform>.<translation_key>`
- **MAY** additionally carry a `state:` block with `<value> → mdi:<icon>` mappings under `entity.<platform>.<translation_key>` — the state-specific icon takes precedence over `default` when it matches the current state value
- **MUST** keep services under the top-level key `services` with `services.<service>.service` as the icon path
- **MUST NOT** carry platform names in PascalCase or mixed casing — HA convention is lowercase

### Icon set

- **SHOULD** use Material Design Icons (`mdi:<name>`) as the default icon set — HA bundles the `mdi:` library out of the box
- **MAY** use alternative icon sets where HA supports them (for example `hass:<name>` for HA's own icons); the spec does not require unification beyond the `mdi:` default
- **MUST NOT** use absolute URLs as icon paths — HA bundles icons; external URLs break offline setups

### Consistency with `strings.json`

- **MUST** match `translation_key` values in `icons.json` exactly with keys in `strings.json` — drift (icon entry without translation or vice versa) classifies as a bug
- **SHOULD** maintain `strings.json` and `icons.json` together when adding a new entity — the typical skill flow scaffolds both jointly
- **MUST NOT** embed icons inside `strings.json` — `strings.json` is for strings, not visuals

### Forbidden patterns

- **MUST NOT** set `_attr_icon = "mdi:..."` as a hard-coded property on entity classes — icons belong in `icons.json`, not in code
- **MUST NOT** write dynamic `icon` methods on entity classes — state-specific icons belong in the `state:` block of `icons.json`
- **MUST NOT** use `EntityDescription.icon` as the default when `icons.json` can carry the same entry — `icons.json` is the canonical source; `EntityDescription.icon` remains allowed as a fallback when the entity has no `translation_key` (rare)

## Acceptance Criteria

- [ ] `custom_components/<domain>/icons.json` exists
- [ ] Top-level sections are limited to `entity` and `services`
- [ ] Platform names under `entity` are lowercase and match HA platform names
- [ ] Every `translation_key` with an associated entity has at least `default` in `icons.json`
- [ ] Sensors with enum state have a `state:` block with icons per backend value
- [ ] Services have `services.<service>.service` as an icon entry
- [ ] A `grep` for `_attr_icon = "mdi:` in the platform modules returns no hits
- [ ] A `grep` for `def icon` in the platform modules returns no dynamic `icon` property methods
- [ ] Quality scale marker: **Bronze**

## Open Questions

- **State-block completeness requirement**: Should the `state:` block cover every possible value (mandatory) or is a selection of the most common ones enough (SHOULD)? `kamerplanter-ha` covers the most common ones, not all.
- **`hass:` vs. `mdi:` mix**: Should the spec require `mdi:` exclusively or allow a mix with HA's own icons (`hass:`)? Currently formulated as MAY.
- **`EntityDescription.icon` ban**: Currently formulated as "do not use when `icons.json` is possible"; a full ban would force consistency. Are there legitimate use cases for `EntityDescription.icon`?
- **Custom icons (SVG paths)**: When does a follow-up spec require custom SVG icons? Currently excluded as a non-goal.
