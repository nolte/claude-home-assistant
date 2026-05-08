# Skill: `ha-entity-description-mapper`

Status: draft

## Context

A platform file (`sensor.py`, `binary_sensor.py`, …) typically grows with the count of its datapoints — new backend fields, new status values, new metrics. Without a declarative form, every new datapoint adds about ten lines of code (own class, own `unique_id`, own `native_value` property). The `EntityDescription` pattern from `ha/entity-architecture` cuts that cost down to one tuple entry per datapoint.

This skill takes a datapoint description (for example a CSV with `name`, `device_class`, `state_class`, `unit`, `icon`) or an API-response schema JSON and produces the `EntityDescription` tuple list plus the generic entity class plus the corresponding `strings.json` / `icons.json` entries.

## Scope

The skill augments an **existing** platform file (typically `sensor.py`) with datapoints. It does not create a new platform file (greenfield is `ha-integration-scaffold`'s job, or a dedicated `ha-platform-add` if planned). It does not delete existing datapoints and does not overwrite existing `EntityDescription` entries — on conflict it aborts and reports the datapoint key as the hit.

## Goals

- Make datapoint-to-code generation deterministic and consistent between platform code, `strings.json`, `translations/<lang>.json`, and `icons.json`
- Enforce cross-file consistency: same `translation_key` across all four locations
- Make the HA quality-scale tier visible per datapoint (Bronze / Silver / Gold) — the skill writes it as a code comment next to each `EntityDescription` entry when the convention is defined
- Sanity validation: check `device_class` plus `unit` against HA-known classes, `state_class` against `MEASUREMENT` / `TOTAL_INCREASING` / `TOTAL`

## Non-Goals

- API response parser generation — the skill produces the `EntityDescription`s and the skeleton `_handle_coordinator_update` logic, but not the concrete path lookup in the coordinator data dict (that is consumer territory)
- Multi-platform generation in one call — one platform file per call
- Migration from the per-datapoint-class style to `EntityDescription` — separate follow-up spec if needed at all
- Lovelace card adjustments — different skill axis (`ha-lovelace-card-scaffold`)

## Requirements

### Activation triggers

- **MUST** activate on:
  - "add sensors from this datapoint list to the integration"
  - "generate EntityDescriptions from this CSV"
  - "add binary_sensors for the alert types"
  - "erweitere die Sensor-Plattform um folgende Datapoints"
- **MUST NOT** activate on:
  - greenfield scaffold (`ha-integration-scaffold`)
  - missing platform file (user should run scaffold first)
  - custom state-class definition (user edit)

### Inputs

- **MUST** collect:
  - `target_dir` — repo root
  - `platform` — `sensor`, `binary_sensor`, `button`, `number`, `select`, `switch`, `calendar`, `todo`
  - `datapoints` — list of datapoint dicts with fields `key`, `translation_key`, `device_class` (optional), `state_class` (optional), `native_unit_of_measurement` (optional), `entity_category` (optional), `default_icon` (`mdi:...`), `state_icons` (dict, optional; sensors with enum state only)
- **SHOULD** offer datapoint-format hints: CSV input is interpreted as a table; JSON input as a list-of-dicts; free text is rejected with "please submit as a table"

### Validation

- **MUST** check per datapoint dict:
  - `key` is lowercase snake_case ASCII
  - `translation_key` is lowercase snake_case ASCII (may equal `key`)
  - `device_class` (when set) is an HA-known class for the platform — for example `SensorDeviceClass.TEMPERATURE` for `sensor`
  - `state_class` (when set) is `MEASUREMENT`, `TOTAL_INCREASING`, or `TOTAL`
  - `native_unit_of_measurement` (when set) is consistent with `device_class` (for example `°C` / `K` for `TEMPERATURE`)
- **MUST** report validation violations as a verbose list and abort the run instead of writing half-generated datapoints

### Generator choreography

- **MUST** append the `EntityDescription` tuple list in `<platform>.py` — constant name typically `<DOMAIN>_<PLATFORM>_DESCRIPTIONS` (uppercase with `_DESCRIPTIONS` suffix)
- **MUST** ensure a generic entity class consuming the tuple list exists; if missing, append it
- **MUST** add `entity.<platform>.<translation_key>.name` per datapoint to `strings.json` and every `translations/<lang>.json` — English in `strings.json`, translations as TODO markers in non-EN languages unless the user supplies them
- **MUST** add `entity.<platform>.<translation_key>.default` to `icons.json` (plus `state.<value>` if the datapoint spec carries state icons)
- **SHOULD** set a code comment with the HA quality-scale tier per datapoint when the spec defines it (typically Bronze for datapoints without `device_class`, Silver for datapoints with correct `device_class`+`state_class`)

### Forbidden

- **MUST NOT** overwrite existing `EntityDescription` entries with the same `key` — conflict aborts with hint
- **MUST NOT** invent translations for non-EN languages — non-EN translations are marked `<TODO: translate '<EN value>'>` unless the user supplies them
- **MUST NOT** concretise the `_handle_coordinator_update` path (which backend field maps to which datapoint) — that is a consumer task; the skill ships only the generic class with the `entity_description.key` lookup skeleton

## Acceptance Criteria

- [ ] The `EntityDescription` tuple list in `<platform>.py` carries every requested datapoint
- [ ] `strings.json` carries every datapoint under `entity.<platform>.<translation_key>.name`
- [ ] Every `translations/<lang>.json` carries every datapoint with a translation or `<TODO: …>` marker
- [ ] `icons.json` carries every datapoint under `entity.<platform>.<translation_key>.default`; for state icons, the `state:` block as well
- [ ] `ruff check custom_components/<domain>/<platform>.py` runs cleanly
- [ ] Validation violations are reported as a list and block the run
- [ ] Existing datapoints stay unchanged

## Open Questions

- **`_handle_coordinator_update` concretisation**: Should the skill ship the datapoint-to-backend-field lookup as a skeleton (for example `data.get(<key>)`), or does it stay user territory?
- **Auto-translation**: Should the skill ship machine translations (for example via DeepL API), or stick with `<TODO>` markers?
- **State-class heuristic**: For numeric datapoints — should the skill suggest `MEASUREMENT` as the default, or does the user always have to specify it?
- **HA quality-scale tier format**: How exactly is the tier marked in the code comment? Style question; currently open.
