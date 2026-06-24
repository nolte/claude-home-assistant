# HA Integration: Entity Platform Types

Status: draft

## Context

A Custom Integration declares its entities through typed platform base classes: `SensorEntity`, `BinarySensorEntity`, `ClimateEntity`, `LightEntity`, `CoverEntity`, and the rest of the HA platform list. The generic entity architecture — base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, the `EntityDescription` pattern, entity categories, and coordinator binding — is already fixed in `ha/entity-architecture` and is **not repeated here**. This spec addresses platform-specific typing only: which platform correctly models a capability, and which fields that platform expects from a **closed enum**, so that UI, voice control, unit conversion, and long-term statistics work.

Three mechanisms carry this typing. **`device_class`** classifies an entity from a platform-owned enum (`SensorDeviceClass`, `BinarySensorDeviceClass`, `CoverDeviceClass`, …); HA derives default names, icons, allowed units, and the voice/cloud integration from it. **`state_class`** plus `native_unit_of_measurement`, `native_value`, and `suggested_display_precision` turn a numeric sensor into a long-term-statistics source. **`supported_features`** is a bitmask from a platform-owned feature enum (`ClimateEntityFeature`, `LightEntityFeature`, `CoverEntityFeature`); every set flag promises an implemented method. Light color modes (`supported_color_modes` / `color_mode`) are the canonical example of a set of **mutually exclusive** capability options.

`developers.home-assistant` makes this typing a quality-scale obligation: the `entity-device-class` rule (Gold) requires entities to set device classes wherever possible, because they drive unit switching, voice control, cloud export (Google Assistant, Alexa), and UI representation. This spec lifts the platform docs into a generic obligation for skill output.

Quality scale markers:
- **Gold**: correctly set `device_class` per platform wherever a matching enum member exists (`entity-device-class`).

## Goals

- Bind platform choice to the capability being modeled — measurement/read-only value → `sensor`, two-state value → `binary_sensor`, switchable actuator → `switch`/`light`, opening → `cover`, etc.
- Set `device_class` as a mandatory field per platform from the closed enum, so UI, units, and voice work correctly (`entity-device-class`, Gold)
- Make numeric sensors long-term-statistics capable with `state_class` + `native_unit_of_measurement` + `native_value` (+ `suggested_display_precision`)
- Set `supported_features` bitmasks so that only actually implemented features are advertised — every flag has its `async_` method
- Correctly declare light color modes (`supported_color_modes` / `color_mode`) as a mutually exclusive capability set
- Have generated code start Gold conformant with respect to device-class coverage straight from skill output

## Non-Goals

- Generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, forbidden `entity_id`, `EntityDescription` pattern, entity categories, coordinator binding) — fully in `ha/entity-architecture`; this spec only references it
- HA translation format itself (`strings.json` shape, `entity.<platform>.<key>.name`, state translations) — separate `ha/translations` spec
- Icon selection and icon translations (`icons.json`, `default`/`state`) — separate `ha/icons` spec; this spec only sets the `device_class` from which HA derives default icons
- `RestoreSensor`/`RestoreEntity` persistence of `native_value` across restart — separate follow-up spec when concretely needed
- Platforms beyond the examples covered here (`fan`, `number`, `select`, `valve`, `humidifier`, …) in detail — the generic rules apply by analogy; an exhaustive per-platform table is not a goal

## Requirements

### Platform choice

- **MUST** choose exactly one platform from the HA platform catalog for each capability being modeled, whose semantics carry the capability — a read-only measurement is `sensor`, a two-state value is `binary_sensor`
- **MUST** use `binary_sensor` (with `is_on`) instead of a `sensor` with a text state for a value that has exactly two states — `binary_sensor` is defined for two states
- **MUST** use `light` (with `color_mode`/`supported_color_modes`) and not `switch` for a controllable light as soon as brightness or color is controllable — `switch` can only do on/off
- **SHOULD** use `cover` for an opening or cover (garage door, roller shutter, awning); the `cover` docs explicitly direct other device types (for example a pure setpoint actuator) to be modeled as `number` instead
- **SHOULD** use `number` instead of `cover` for a numeric setpoint without opening semantics — the `cover` docs delimit this explicitly
- **MUST NOT** combine several changing values into the `extra_state_attributes` of a single sensor where separate entities would be correct — the sensor docs require a dedicated `sensor` entity for additional changing values

### `device_class` (closed enums)

- **MUST** set `device_class` from the **platform-owned closed enum** (`SensorDeviceClass`, `BinarySensorDeviceClass`, `CoverDeviceClass`, …) on every entity for which a matching enum member exists — quality rule `entity-device-class`, Gold
- **MUST** use only enum members, never a freely chosen string — `device_class` is closed to the documented enum per platform
- **MUST** return a `native_unit_of_measurement` matching the class when a sensor `device_class` is set — the sensor docs bind each class to allowed units (for example `TEMPERATURE` → °C/°F/K, `POWER` → mW/W/kW/…)
- **MUST** set the `options` list for `SensorDeviceClass.ENUM` and must not combine that class with `state_class` or `native_unit_of_measurement` — as the sensor docs document
- **SHOULD** set the `device_class` via the `EntityDescription` (`device_class=...`) rather than as `_attr_device_class` when the platform uses the `EntityDescription` pattern (setting mechanics see `ha/entity-architecture`)
- **MUST NOT** use `BinarySensorDeviceClass.UPDATE` where an `update` entity would be correct — the binary-sensor docs explicitly advise against it

### Sensor: `state_class`, units & precision

- **MUST** set `state_class` to exactly one of `SensorStateClass.MEASUREMENT`, `SensorStateClass.TOTAL`, or `SensorStateClass.TOTAL_INCREASING` for every numeric `sensor` intended to feed long-term statistics
- **MUST** choose `SensorStateClass.MEASUREMENT` for a present-time measurement (current temperature, power, remaining capacity) and not for accumulated values — as the sensor docs state
- **MUST** use `SensorStateClass.TOTAL_INCREASING` for a monotonically increasing counter that periodically resets to 0 (daily gas consumption, lifetime energy), and `SensorStateClass.TOTAL` for a value that can both increase and decrease
- **MUST** return the value via `native_value` in the `native_unit_of_measurement` (not via a generic `state`/`unit_of_measurement` override) — HA handles the user-side unit conversion
- **SHOULD** set `suggested_display_precision` when the raw `native_value` carries more decimal places than is sensible to display — the field controls only the display, not the stored value
- **SHOULD** not set `state_class = MEASUREMENT` with the device classes the sensor docs exclude from min/max/mean (`DATE`, `ENUM`, `ENERGY`, `GAS`, `MONETARY`, `TIMESTAMP`, `VOLUME`, `WATER`)
- **MUST NOT** set a custom unit spelling that deviates from the HA constants (for example `KWh` instead of `kWh`) — the sensor docs warn that HA interprets this as a unit change and suspends statistics

### `supported_features` bitmasks

- **MUST** set `supported_features` as a bitwise `|` combination from the **platform-owned feature enum** (`ClimateEntityFeature`, `LightEntityFeature`, `CoverEntityFeature`, …), never as a raw integer
- **MUST** set only flags whose associated method is actually implemented — the `cover` docs require `async_open_cover`, for example, if and only if `CoverEntityFeature.OPEN` is set (analogously `CLOSE`, `SET_POSITION`, `STOP`, tilt variants)
- **MUST** provide the properties the climate docs mark as "Required by …" when the corresponding `ClimateEntityFeature` flag is set (for example `FAN_MODE` → `fan_mode` + `fan_modes`, `TARGET_TEMPERATURE_RANGE` → `target_temperature_high`/`_low`)
- **MUST** use only the built-in `HVACMode` members in `hvac_modes` for `climate` entities — the docs forbid custom modes and direct additional needs to presets
- **MUST NOT** set a feature flag "on spec" whose method is not (yet) implemented — an advertised but unserviceable feature breaks UI and voice integration
- **SHOULD** set the feature mask via the `EntityDescription` or an `_attr_supported_features` class attribute, depending on whether the platform uses the `EntityDescription` pattern (see `ha/entity-architecture`)

### Color modes (light) as the example

- **MUST** set both `supported_color_modes` (a `set[ColorMode]`) and `color_mode` on every `light` entity — the light docs otherwise raise an error on state write
- **MUST** set `color_mode` to a value from `supported_color_modes` (exception: an active effect, which may set a more restrictive mode)
- **MUST** carry `ColorMode.ONOFF` and `ColorMode.BRIGHTNESS` each as the **only** mode when supported — the light docs require that these two modes are not combined with others
- **MUST NOT** set `ColorMode.WHITE` without at least one color mode (`HS`, `RGB`, `RGBW`, `RGBWW`, or `XY`) and not together with `ColorMode.COLOR_TEMP` — as the light docs state
- **SHOULD** set `LightEntityFeature.EFFECT`/`FLASH`/`TRANSITION` only when the device actually services the respective capability — the same feature-↔-implementation rule as above

### Feature-flag ↔ implementation consistency

- **MUST** ensure for every set `supported_features` flag that the corresponding `async_` method (or its synchronous variant) exists on the entity class — the platform docs couple flag and method one-to-one
- **MUST** provide an implementation for every property a flag or a `device_class` marks as "Required" (for example `native_value` for `sensor`, `is_closed` for `cover`, `hvac_mode`/`hvac_modes` for `climate`)
- **SHOULD** change `device_class`, `supported_features`, and other capability attributes at runtime only when absolutely required, and then at a modest interval — the entity docs warn that such changes force, for example, voice-assistant integrations to resynchronize
- **MUST NOT** declare a platform capability inconsistently (flag set, property/method missing; `device_class` set, unit mismatched) — such inconsistencies cause runtime errors or silent UI misrepresentation

## Acceptance Criteria

- [ ] Every capability is modeled on the semantically appropriate platform (measurement → `sensor`, two-state → `binary_sensor`, dimmable/color-capable light → `light`, opening → `cover`)
- [ ] Every entity with a matching enum member sets `device_class` from the closed platform enum (Gold rule `entity-device-class`)
- [ ] No `device_class` is set as a freely chosen string; every set sensor `device_class` has a matching `native_unit_of_measurement`
- [ ] Every statistics-relevant numeric `sensor` sets `state_class` to `MEASUREMENT`, `TOTAL`, or `TOTAL_INCREASING` and returns `native_value` in `native_unit_of_measurement`
- [ ] `suggested_display_precision` is set where the raw `native_value` carries too many decimal places
- [ ] No unit deviates in spelling from the HA constant (for example no `KWh` instead of `kWh`)
- [ ] `supported_features` is set as a bitwise `|` combination from the platform-owned feature enum, never as a raw integer
- [ ] For every set feature flag the corresponding `async_` method exists; no flags set "on spec"
- [ ] Every `light` entity sets `supported_color_modes` and `color_mode`; `ONOFF`/`BRIGHTNESS` each stand alone, `WHITE` never without a color mode and never with `COLOR_TEMP`
- [ ] `climate` entities use only built-in `HVACMode` members; all "Required by feature" properties are implemented
- [ ] Quality scale markers: **Gold** for correct device-class coverage per platform

## Open Questions

- **Per-platform table depth**: This spec covers `sensor`, `binary_sensor`, `climate`, `light`, `cover` as examples. Should `fan`, `number`, `select`, `valve`, `humidifier` each get their own follow-up specs, or does the generic rule plus a pointer to the HA docs suffice?
- **Device-class coverage threshold**: The Gold rule says "wherever possible". Should the skill explicitly document why no `device_class` is set on an entity without a matching enum member, or does omission suffice?
- **Auto-checking `state_class`-vs-device-class conflicts**: The sensor docs exclude certain device classes from `MEASUREMENT` statistics. Should the skill actively forbid this combination or only warn?
- **Color-mode migration**: When a device later adds color, `supported_color_modes` changes. Does a migration/versioning convention for this belong in this spec or in `ha/entity-architecture`?
- **Custom presets/fan modes**: Climate allows custom preset and fan-mode strings (but not custom `HVACMode`). Should the spec prescribe a convention for their translation keys (interface to `ha/translations`)?
