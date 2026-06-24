# HA Integration: Entity Platforms (Climate Family)

Status: draft

## Context

The generic typing mechanics — `device_class`, `supported_features` as a bitmask from a platform-owned feature enum, and the one-to-one coupling between a set flag and an implemented method — are fixed in `ha/entity-platform-types`; the generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`, coordinator binding) in `ha/entity-architecture`. Both are **only referenced here, not repeated**. The `climate` platform itself is already covered as an example in `ha/entity-platform-types` and is **not** the subject of this spec.

This spec is the **concrete platform catalog for the climate-adjacent comfort platforms**: `fan`, `humidifier`, and `water-heater`. These devices cluster with `climate` around indoor climate and comfort, but each has its own base class (`FanEntity`, `HumidifierEntity`, `WaterHeaterEntity`), its own feature enum, and its own set of required properties and methods. For each of these three platforms, this spec fixes when to choose it, which `device_class` (where one exists), which `supported_features` flags, and which properties/methods the skill output must provide, so that only actually implemented capabilities are advertised.

Cross-cutting references: the HA translation format (`strings.json`, state translations for modes/operation states) is governed by `ha/translations`; icon selection by `ha/icons`.

## Goals

- Bind platform choice within the climate family to the capability being modeled — air movement → `fan`, humidity control → `humidifier`, water heating → `water-heater`
- Set the correct base class (`FanEntity`, `HumidifierEntity`, `WaterHeaterEntity`) and — where one exists — the `device_class` from the closed enum for each of the three platforms
- Set `supported_features` bitmasks from the platform-owned feature enum (`FanEntityFeature`, `HumidifierEntityFeature`, `WaterHeaterEntityFeature`) so that only flags with an implemented method are advertised
- Provide in full the properties and methods marked "Required" by a flag or by the platform
- Keep generated code consistent between feature flag and implementation per platform

## Non-Goals

- Generic typing mechanics (`device_class` enum closure, `supported_features` bitmask rule, feature-↔-implementation coupling) — fully in `ha/entity-platform-types`; this spec only applies them concretely
- The `climate` platform itself — already covered as an example in `ha/entity-platform-types`
- Generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`, coordinator binding) — fully in `ha/entity-architecture`
- HA translation format for mode/operation-state strings (`strings.json`, state translations) — separate `ha/translations` spec
- Icon selection and icon translations (`icons.json`) — separate `ha/icons` spec

## Requirements

### `fan`

- **MUST** derive a fan entity from `FanEntity` when the device controls vectors of a fan (speed, direction, oscillation) — as the fan docs state
- **MUST** set `supported_features` as a bitwise `|` combination from `FanEntityFeature` (`SET_SPEED`, `PRESET_MODE`, `OSCILLATE`, `DIRECTION`, `TURN_ON`, `TURN_OFF`) and never as a raw integer
- **MUST** implement `async_set_percentage` (or `set_percentage`) if and only if `FanEntityFeature.SET_SPEED` is set, and return `percentage` as a value between 0 (off) and 100
- **MUST** implement `async_set_preset_mode` (or `set_preset_mode`) and provide `preset_modes` if and only if `FanEntityFeature.PRESET_MODE` is set; `preset_mode` is a value from `preset_modes` or `None` when no preset is active
- **MUST** implement `async_oscillate` (or `oscillate`) if and only if `FanEntityFeature.OSCILLATE` is set, and return `oscillating`
- **MUST** implement `async_set_direction` (or `set_direction`) if and only if `FanEntityFeature.DIRECTION` is set, and return `current_direction`
- **MUST** implement `async_turn_on`/`async_turn_off` if and only if `FanEntityFeature.TURN_ON` resp. `FanEntityFeature.TURN_OFF` is set
- **MUST NOT** include named (manual) speed settings in `preset_modes` — the fan docs require that `preset_modes` contains no speeds and that named speeds be modeled as percentages
- **SHOULD** use the HA utilities (`ordered_list_item_to_percentage`, `ranged_value_to_percentage`) for percentage conversion on a device with a named or numeric speed list, and return `speed_count` accordingly
- **SHOULD** not implement the deprecated `speed` argument in new integrations and use only `percentage` and `preset_mode` — as the fan docs state

### `humidifier`

- **MUST** derive a humidifier entity from `HumidifierEntity` when the device's main purpose is humidity control (humidifier or dehumidifier) — as the humidifier docs state
- **MUST** set `device_class` from the closed enum `HumidifierDeviceClass` (`HUMIDIFIER` or `DEHUMIDIFIER`) where the device type allows
- **MUST** implement `async_set_humidity` (or `set_humidity`) and return `target_humidity`; if the current mode does not allow adjusting the setpoint, the device automatically switches on this call to a mode that does — as the humidifier docs state
- **MUST** implement `async_turn_on`/`async_turn_off` (or the synchronous variants) and provide `is_on`
- **MUST** set `supported_features` as a bitwise `|` combination from `HumidifierEntityFeature` — currently `MODES` is the only flag
- **MUST** implement `async_set_mode` (or `set_mode`) and provide `mode` and `available_modes` if and only if `HumidifierEntityFeature.MODES` is set
- **SHOULD** prefer the built-in mode constants for `available_modes` (`MODE_NORMAL`, `MODE_ECO`, `MODE_AWAY`, `MODE_BOOST`, `MODE_COMFORT`, `MODE_HOME`, `MODE_SLEEP`, `MODE_AUTO`, `MODE_BABY`), since these carry translations; custom modes are allowed when they better represent the device
- **SHOULD** return `action` as an informational property from `HumidifierAction` (`HUMIDIFYING`, `DRYING`, `IDLE`, `OFF`) when the operating state is known
- **MUST NOT** treat `action = OFF` as a replacement for the `is_on` property — the humidifier docs clarify that `action` does not replace `is_on`

### `water-heater`

- **MUST** derive a water-heater entity from `WaterHeaterEntity` when the device controls water heating
- **MUST** set `supported_features` as a bitwise `|` combination from `WaterHeaterEntityFeature` (`TARGET_TEMPERATURE`, `OPERATION_MODE`, `AWAY_MODE`, `ON_OFF`) and never as a raw integer
- **MUST** implement `async_set_temperature` (or `set_temperature`) if and only if `WaterHeaterEntityFeature.TARGET_TEMPERATURE` is set, and return the temperature properties in the unit declared via `temperature_unit`
- **MUST** implement `async_set_operation_mode` (or `set_operation_mode`) and provide `current_operation` and `operation_list` if and only if `WaterHeaterEntityFeature.OPERATION_MODE` is set; `current_operation` must be contained in `operation_list`
- **MUST** set `temperature_unit` to a value from `UnitOfTemperature` (`CELSIUS`, `FAHRENHEIT`, or `KELVIN`) — the docs otherwise mark the field as `NotImplementedError`
- **MUST** implement `async_turn_on`/`async_turn_off` if and only if `WaterHeaterEntityFeature.ON_OFF` is set, and `async_turn_away_mode_on`/`async_turn_away_mode_off` plus `is_away_mode_on` if and only if `WaterHeaterEntityFeature.AWAY_MODE` is set
- **MUST NOT** use custom operation modes beyond the states specified by the base component (`STATE_ECO`, `STATE_ELECTRIC`, `STATE_PERFORMANCE`, `STATE_HIGH_DEMAND`, `STATE_HEAT_PUMP`, `STATE_GAS`, `STATE_OFF`) — the docs require that implementations cannot differ from these
- **SHOULD** keep all temperature properties (`current_temperature`, `target_temperature`, `target_temperature_high`/`_low`, `min_temp`, `max_temp`) consistently in the unit declared via `temperature_unit` — as the docs state

## Acceptance Criteria

- [ ] Every climate-family capability is modeled on the semantically appropriate platform (air movement → `fan`, humidity → `humidifier`, water heating → `water-heater`)
- [ ] Each of the three platforms derives from its correct base class (`FanEntity`, `HumidifierEntity`, `WaterHeaterEntity`)
- [ ] `humidifier` entities set `device_class` from `HumidifierDeviceClass` where the device type allows
- [ ] `supported_features` is set per platform as a bitwise `|` combination from the platform-owned feature enum, never as a raw integer
- [ ] For every set `fan` flag the corresponding method exists (`SET_SPEED` → `async_set_percentage` + `percentage`; `PRESET_MODE` → `async_set_preset_mode` + `preset_modes`; `OSCILLATE` → `async_oscillate`; `DIRECTION` → `async_set_direction`)
- [ ] `fan` `preset_modes` contains no named speeds; named speeds are modeled as percentages
- [ ] `humidifier` with `HumidifierEntityFeature.MODES` provides `async_set_mode`, `mode`, and `available_modes`; `action` does not replace `is_on`
- [ ] `water-heater` with `OPERATION_MODE` provides `async_set_operation_mode`, `current_operation` (within `operation_list`); with `TARGET_TEMPERATURE` it provides `async_set_temperature`
- [ ] `water-heater` operation modes use only the states specified by the base component; `temperature_unit` is set from `UnitOfTemperature`
- [ ] No platform flag is set "on spec" whose method is missing

## Open Questions

- **`fan` speed representation**: Should the skill auto-generate the HA utility conversion (`ordered_list_item_to_percentage`) for a device with named steps, or does this remain a manual author decision?
- **`humidifier` custom modes**: The docs allow custom mode strings alongside the built-in ones. Should this spec prescribe a translation-key convention for custom modes (interface to `ha/translations`)?
- **`water-heater` state translations**: The operation states (`STATE_ECO`, …) are closed but user-visible. Does fixing their translation belong in this spec or fully in `ha/translations`?
- **Further climate-family platforms**: Should adjacent platforms (for example `climate` presets in detail) be added here, or does the climate family stay limited to `fan`, `humidifier`, `water-heater` plus the `climate` reference in `ha/entity-platform-types`?
