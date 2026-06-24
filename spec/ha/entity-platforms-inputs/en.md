# HA Integration: Entity Platforms (Input Helpers)

Status: draft

## Context

Beyond the read-only and actuator-oriented platforms (`sensor`, `binary_sensor`, `light`, `cover`, `climate`, …), Home Assistant provides a family of **input-oriented** platforms through which an integration offers the user a freely settable value: `number`, `select`, `text`, `date`, `time`, and `datetime`. These platforms mirror the well-known `input_*` helpers (`input_number`, `input_select`, `input_text`, `input_datetime`), but are **integration-backed** — the value is held by the device or service and written back to the integration through a set method, instead of being managed locally by Home Assistant.

This spec is the **concrete catalog** of these input platforms: per platform the capability, the right choice heuristic, the base class, the value attributes, and the mandatory set method, derived exclusively from the respective platform docs on `developers.home-assistant`. The generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`, entity categories, coordinator binding) is fixed in `ha/entity-architecture`; the cross-platform typing concepts (`device_class`, units, `state_class`, `supported_features`) in `ha/entity-platform-types`. Both are **only referenced here by slug, not repeated**.

Unlike sensor platforms, these platforms are **bidirectional**: each declares exactly one set method (`async_set_native_value`, `async_select_option`, `async_set_value`) that the user or an automation triggers. The skill output must implement this method, otherwise the entity is not operable.

## Goals

- Bind platform choice to the value type the user inputs — numeric → `number`, fixed option list → `select`, free text → `text`, date → `date`, time → `time`, timestamp → `datetime`
- Set the correct base class per platform (`NumberEntity`, `SelectEntity`, `TextEntity`, `DateEntity`, `TimeEntity`, `DateTimeEntity`) and the documented value attributes
- Provide for every input entity the property the platform docs mark as **Required** (`native_value`, `options`) and the associated set method
- Type `number` entities via `device_class` from `NumberDeviceClass` and return the matching `native_unit_of_measurement` wherever a member exists
- Make the integration-backed nature visible — the value is written to the device/service through the set method, not managed locally by HA

## Non-Goals

- Generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription` pattern, entity categories, coordinator binding) — fully in `ha/entity-architecture`; this spec only references it
- Cross-platform typing concepts (`device_class` mechanics in general, unit conversion, `state_class`, `supported_features` bitmasks) — fully in `ha/entity-platform-types`; this spec only references them
- HA translation format itself (`strings.json` shape, `entity.<platform>.<key>.name`, option/state translations) — separate `ha/translations` spec
- `RestoreNumber`/`RestoreEntity` persistence of `native_value` across restart — the `number` docs point to `RestoreNumber`; a separate follow-up spec when concretely needed
- The YAML `input_*` helpers themselves (user-configurable helpers without an integration) — this spec addresses only the integration-backed platform entities

## Requirements

### `number`

- **MUST** model a numeric quantity freely settable by the user as a `number` with base class `NumberEntity` — the docs define `number` as an "entity that allows the user to input an arbitrary value"
- **MUST** return the current value via `native_value` (float, **Required**) in the `native_unit_of_measurement`
- **MUST** declare the value range via `native_min_value` and `native_max_value` (inclusive bounds) and the resolution via `native_step` — if `native_step` is not set, HA derives the default dynamically from the range
- **SHOULD** set the `device_class` from the closed `NumberDeviceClass` enum for a physical quantity and then return the unit allowed for that class as `native_unit_of_measurement` (for example `TEMPERATURE` → °C/°F/K, `POWER` → mW/W/kW/…) — the mechanics themselves are described by `ha/entity-platform-types`
- **SHOULD** leave `mode` on the default `auto` and force `box` or `slider` only on justified need — as the docs recommend
- **MUST** implement exactly one set method — `async_set_native_value(value: float)` (or the synchronous `set_native_value`) — otherwise the `number` is not settable

### `select`

- **MUST** model a choice from a **limited option list provided by the integration** as a `select` with base class `SelectEntity`
- **MUST** provide the available options via `options` (list of str, **Required**) and the currently selected option via `current_option` (str)
- **MUST** implement exactly one set method — `async_select_option(option: str)` (or the synchronous `select_option`)
- **MUST NOT** use `select` where a better fitting platform exists — the docs state: "This entity should only be used in cases there is no better fitting option available" (for example light effects belong on the `light` entity, not on a `select`)
- **SHOULD** not carry the option strings raw as UI text but make them localizable through the HA translation format — interface to `ha/translations`

### `text`

- **MUST** model a string freely entered by the user as a `text` with base class `TextEntity`
- **MUST** return the current value via `native_value` (str, **Required**)
- **SHOULD** bound the permitted length via `native_min` and `native_max` (inclusive character count) and, where the format is fixed, validate via `pattern` (regex)
- **SHOULD** set `mode` to `password` when the value is a secret, otherwise leave it on the default `text` — the docs know exactly these two modes
- **MUST** implement exactly one set method — `async_set_value(value: str)` (or the synchronous `set_value`)

### `date`

- **MUST** model a date entered by the user as a `date` with base class `DateEntity`
- **MUST** return the value via `native_value` as `datetime.date | None` (**Required**)
- **MUST** implement exactly one set method — `async_set_value(value: date)` (or the synchronous `set_value`)
- **MUST NOT** use `date` when a time is additionally part of the value — `datetime` is intended for that

### `time`

- **MUST** model a time entered by the user as a `time` with base class `TimeEntity`
- **MUST** return the value via `native_value` as `time` (**Required**)
- **MUST** implement exactly one set method — `async_set_value(value: time)` (or the synchronous `set_value`)
- **MUST NOT** use `time` when a date is additionally part of the value — `datetime` is intended for that

### `datetime`

- **MUST** model a timestamp entered by the user as a `datetime` with base class `DateTimeEntity`
- **MUST** return the value via `native_value` as `datetime.datetime | None` (**Required**) and **include timezone info** — the docs require: "Must include timezone info"
- **MUST** implement exactly one set method — `async_set_value(value: datetime)` (or the synchronous `set_value`); the input value passed by HA is **always in UTC**, as the docs explicitly state
- **MUST NOT** use `datetime` for a pure date or pure time value — `date` resp. `time` are intended for that

## Acceptance Criteria

- [ ] Every user input is modeled on the value-type-appropriate platform (numeric → `number`, fixed option list → `select`, free text → `text`, date → `date`, time → `time`, timestamp → `datetime`)
- [ ] Every input entity derives from the correct base class (`NumberEntity`, `SelectEntity`, `TextEntity`, `DateEntity`, `TimeEntity`, `DateTimeEntity`)
- [ ] Every input entity provides the property marked **Required** (`native_value` resp. `options`)
- [ ] Every input entity implements exactly one set method (`async_set_native_value`, `async_select_option`, `async_set_value`)
- [ ] Every `number` declares `native_min_value`/`native_max_value` and returns `native_value` in the `native_unit_of_measurement`; a set `NumberDeviceClass` has a unit matching the class
- [ ] Every `select` sets `options` and `current_option`; `select` is not used where a more fitting platform exists
- [ ] Every `text` with a secret value uses `mode = password`; where the format is fixed, `pattern` is set
- [ ] Every `datetime` entity returns a timezone-aware `native_value`; `date`/`time`/`datetime` are not swapped against each other

## Open Questions

- **Persistence across restart**: The `number` docs point to `RestoreNumber` instead of `RestoreEntity`. Does a restore convention for `number` (and by analogy for the other input platforms) belong in this spec or in a separate follow-up spec?
- **Option translation for `select`**: Should the `options` strings be mandatorily localized through `ha/translations`, or does this stay a recommendation?
- **`device_class` for non-`number` inputs**: Only `number` carries a `device_class` enum. Should the spec explicitly state this so the skill does not attempt to set a `device_class` for `select`/`text`/`date`/`time`/`datetime`?
- **`mode` heuristic for `text`**: When is a value "secret" enough for `mode = password`? Should the spec prescribe a heuristic or leave the decision to the author?
