---
name: ha-entity-description-mapper
description: Generate EntityDescription tuple lists for an HA Custom Integration platform module from a datapoint table or API-schema JSON, plus matching strings.json and icons.json entries. Activate on phrasings like "add sensors from this datapoint list", "generate EntityDescriptions from this CSV", "add binary_sensors for the alert types", "erweitere die Sensor-Plattform um folgende Datapoints". Do not activate for greenfield scaffolding (use ha-integration-scaffold) or when the platform file does not yet exist.
tags: [home-assistant, custom-integration, entity-description]
phase: design
summary: "Generates EntityDescription tuple lists for a platform module from a datapoint table or API-schema JSON, plus matching strings.json and icons.json entries."
summary_de: "Erzeugt EntityDescription-Listen für ein Plattform-Modul aus einer Datapoint-Tabelle oder API-Schema-JSON, samt passender strings.json- und icons.json-Einträge."
use_when:
  - "you want to add sensors from a datapoint list"
  - "you want to generate EntityDescriptions from a CSV"
  - "you want to add binary_sensors for alert types"
  - "you want to extend a platform with more datapoints"
dont_use_when:
  - situation: "You are scaffolding a brand-new integration from scratch"
    alternative: ha-integration-scaffold
  - situation: "The target platform file does not yet exist"
    alternative: ha-integration-scaffold
see_also:
  - ha-integration-scaffold
  - ha-entity-platform-add
  - ha-coordinator-add
  - ha-translation-sync
---

# HA EntityDescription Mapper

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-entity-description-mapper/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-entity-description-mapper/en.md).

## Why this is a skill, not an agent

- **Per-datapoint operator decisions (decisive):** mapping a datapoint table to EntityDescription tuples requires judgement calls (device class, unit, enabled-by-default) that are confirmed in the conversation, not fired off blind.
- **Output flows back naturally:** the generated tuple list and strings/icons entries are reviewed and iterated inline before they land.
- **Counter-dimension considered:** the generation step is mechanical and self-contained (agent bias), but a wrong device-class guess multiplied over a whole table is expensive — the confirm-as-you-go dialogue outweighs isolation.

## When this skill activates

Use this skill when the user wants to add datapoints (sensors, binary sensors, buttons, numbers, selects, switches, calendars, todos) to an existing platform file in declarative `EntityDescription` form.

## When NOT to activate

- greenfield scaffold → `ha-integration-scaffold`
- platform file missing → run scaffold first, then come back
- custom state-class definitions → manual code edit
- multi-platform generation in one call → call this skill once per platform

## Hard rules

1. **Never overwrite existing entries.** Conflict on `EntityDescription.key` aborts with the conflicting key quoted.
2. **Never invent translations.** Non-English translations land as `<TODO: translate '<EN value>'>` unless the user supplies them. Skill output mentions these placeholders explicitly.
3. **Never concretise the backend-field lookup.** The skill produces the generic entity class with `entity_description.key`-based access; mapping to actual coordinator data dict paths is the user's job.
4. **Always validate `device_class`/`state_class`/`unit` consistency.** Mismatches block the run with a verbose violation list.
5. **Always update strings.json AND translations AND icons.json together.** Half-augments where code is present but translations are missing are forbidden.
6. **Name keys and entities per `ha/naming-conventions`.** `EntityDescription.key` and `translation_key` are `snake_case`; entity names come from the `translation_key` path, never a hard-coded `_attr_name`; English display names only (see [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)).
7. **Emit `PARALLEL_UPDATES`.** The generated platform module declares a module-level `PARALLEL_UPDATES` constant (Silver `parallel-updates` quality-scale rule); verify the appropriate value against the HA `parallel-updates` rule page (`0` for coordinator-backed read-only platforms). A module without it is a quality-scale finding waiting to happen.
8. **Validate `entity_category`.** A provided `entity_category` MUST be a member of `EntityCategory` (`CONFIG` / `DIAGNOSTIC`); an invalid value aborts the run with the offending value quoted.
9. **Verify HA internals against the official docs.** Don't reproduce HA API signatures, lifecycle hooks, conventions, or schemas from memory — when uncertain, consult the official docs before generating or relying on it: Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant), architecture/blueprint/YAML docs [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root |
| `platform` | yes | — | `sensor`, `binary_sensor`, `button`, `number`, `select`, `switch`, `calendar`, `todo` |
| `datapoints` | yes | — | list of dicts with `key`, `translation_key`, `device_class?`, `state_class?`, `native_unit_of_measurement?`, `entity_category?`, `default_icon`, `state_icons?` |

Datapoint input format: CSV (parsed as table), JSON (list-of-dicts), or markdown table. Free text is rejected.

## Pre-flight

1. `git -C <target_dir> rev-parse --is-inside-work-tree` and clean working tree
2. `<target_dir>/custom_components/<domain>/<platform>.py` exists; read `domain` from `manifest.json`
3. Every datapoint passes validation:
   - `key` and `translation_key` are lowercase snake_case ASCII
   - `device_class` is HA-known for the platform
   - `state_class` ∈ `MEASUREMENT` / `TOTAL_INCREASING` / `TOTAL` when set
   - `native_unit_of_measurement` is consistent with `device_class`
   - `entity_category`, when set, is a member of `EntityCategory` (`CONFIG` / `DIAGNOSTIC`)
4. None of the datapoint `key`s collide with existing `EntityDescription.key`s in the platform file

## Workflow

### 1) Resolve and confirm

Print a table of the datapoints, the resolved `device_class`/`state_class`/`unit` per row, and the inferred quality-scale tier. Wait for user confirmation.

### 2) Apply edits

- `<platform>.py` — append the new descriptions to the tuple list (or create it if absent); add the generic entity class if absent; ensure a module-level `PARALLEL_UPDATES` constant is present (`parallel-updates` quality-scale rule)
- `strings.json` — append `entity.<platform>.<translation_key>.name` per datapoint
- every `translations/<lang>.json` — same keys, with translation or `<TODO>` marker
- `icons.json` — append `entity.<platform>.<translation_key>.default`; for state-icon datapoints, the `state:` block

### 3) Verify

```bash
ruff check custom_components/<domain>/<platform>.py
pytest tests/ -v
```

### 4) Report

- count of datapoints added
- list of `<TODO>` translation markers that need user attention
- list of inferred quality-scale tiers
- pointer to `ha-test-harness-augment` to add tests for the new descriptions (this skill generates descriptions, not tests)

## Boundaries

- Greenfield scaffold → `ha-integration-scaffold`
- Add a new coordinator → `ha-coordinator-add`
- Translation sync only → `ha-translation-sync`
- Test coverage extension → `ha-test-harness-augment`
