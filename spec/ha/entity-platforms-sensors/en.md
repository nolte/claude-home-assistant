# HA Integration: Entity Platforms (Sensors)

Status: draft

## Context

Beyond the generic measurement and two-state platforms `sensor` and `binary_sensor`, Home Assistant knows a set of further read-only and status platforms, each typing its own capability: air quality, weather, presence (device tracker), physical events, and update availability. Each of these platforms derives from its own base class and expects a fixed set of properties, forecast methods, feature flags, or device classes, so that UI, forecast API, DHCP discovery, automation triggers, and update management work.

The **generic entity architecture** — base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, the `EntityDescription` pattern, entity categories, and coordinator binding — is fixed in `ha/entity-architecture` and is **not repeated here**. The **platform-specific typing** of the generic measurement platforms — `sensor`/`binary_sensor` with the `device_class`/`state_class`/`supported_features` pattern — is fully fixed in `ha/entity-platform-types`; it too is **not repeated here**. This spec is the **concrete catalog** for the remaining read-only and status surfaces and references both sibling specs by slug.

Platforms covered: `air-quality` (deprecated, migration note), `weather`, `device-tracker`, `event`, `update`. For each: bind platform choice to the capability, derive the documented base class, use only the properties/features/device classes named in the platform docs, and back every advertised feature flag with its method.

## Goals

- Bind platform choice to the capability being modeled — air-quality measurement → separate `sensor` (air quality is deprecated), weather condition+forecast → `weather`, presence → `device_tracker`, physical event → `event`, update availability → `update`
- Derive the documented base class per platform (`WeatherEntity`, `TrackerEntity`/`ScannerEntity`/`BaseScannerEntity`, `EventEntity`, `UpdateEntity`)
- Set forecast and feature flags (`WeatherEntityFeature`, `UpdateEntityFeature`) only when the corresponding method is actually implemented
- Set `device_class` from the platform-owned closed enum wherever a matching member exists (`EventDeviceClass`, `UpdateDeviceClass`)
- Have generated code start such that UI, forecast API, DHCP discovery, and update management work without rework

## Non-Goals

- Generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription` pattern, entity categories, coordinator binding) — fully in `ha/entity-architecture`; this spec only references it
- `sensor`/`binary_sensor` and the `device_class`/`state_class`/`supported_features` typing pattern — fully in `ha/entity-platform-types`; this spec only references it
- HA translation format itself (`strings.json` shape, `entity.<platform>.<key>.name`, state translations) — separate `ha/translations` spec
- Actuator platforms (`climate`, `light`, `cover`, `switch`, `fan`, …) — read-only/status surfaces are the focus here; controllable platforms are not a goal
- Exhaustive lists of all weather conditions, unit variants, or AwesomeVersion strategies — this spec points to the respective platform docs instead of duplicating them

## Requirements

### Air quality

- **MUST NOT** use the `air_quality` platform for new integrations — the air-quality docs explicitly mark the entity as deprecated and require separate `sensor` entities for the individual measurements instead
- **MUST** model air-quality measurements (PM2.5, PM10, PM0.1, AQI, ozone, CO, CO₂, SO₂, NO₂, …) as a dedicated `sensor` entity each per `ha/entity-platform-types` rather than bundling them into an air-quality entity
- **SHOULD** migrate an existing integration that still uses the air-quality entity to separate sensors — as the air-quality docs require
- **MUST**, should an air-quality entity unavoidably stay in operation, provide `particulate_matter_2_5` as the only required property and use only the documented units (`ppb`, `ppm`, `µg/m³`) for `nitrogen_dioxide`
- **MUST NOT** use the attribute shorthand (`_attr_` property implementation) for the air-quality entity — the air-quality docs explicitly exclude it

### Weather

- **MUST** derive a weather platform from `homeassistant.components.weather.WeatherEntity`
- **MUST** provide `condition`, `native_temperature`, and `native_temperature_unit` as required properties — the weather docs mark exactly these three as **Required**
- **MUST** return measurements in the native `native_*` properties (`native_temperature`, `native_pressure`, `native_wind_speed`, `native_visibility`, …) and set the corresponding `native_*_unit` property when the value is set (for example `native_pressure_unit` is required once `native_pressure` is set) — HA handles the user-side unit conversion
- **SHOULD** use only the recommended condition strings listed in the weather docs (`sunny`, `cloudy`, `rainy`, `clear-night`, …) for `condition` — these are baked into the HA translation and icon files, so `weather` platforms do not need to support languages
- **MUST** set `supported_features` as a bitwise `|` combination from `WeatherEntityFeature` (`FORECAST_DAILY`, `FORECAST_HOURLY`, `FORECAST_TWICE_DAILY`) and implement exactly the corresponding async method (`async_forecast_daily`, `async_forecast_hourly`, `async_forecast_twice_daily`) per set flag — the weather docs couple flag and method one-to-one
- **MUST NOT** put forecast data into the entity state — forecasts are, per the weather docs, not part of the state but made available through a separate API that consumers subscribe to
- **SHOULD** cache fetched forecasts and, on update, invalidate the cache and await `WeatherEntity.async_update_listeners` to notify active subscribers — as the weather docs recommend
- **MUST** set `is_daytime` on each entry in `async_forecast_twice_daily` data — the weather docs mark it as mandatory there (day/night distinction)

### Device tracker

- **MUST** derive a presence platform from exactly one of the three documented base classes — `BaseScannerEntity` (pure connection state), `ScannerEntity` (IP network, identifiable by MAC), or `TrackerEntity` (position tracking)
- **MUST** provide `is_connected` and `source_type` as required properties for `ScannerEntity`/`BaseScannerEntity` — the device-tracker docs mark both as **Required**
- **MUST** set either `in_zones` or `latitude` **and** `longitude` to report a state for `TrackerEntity`; if both are present, `in_zones` takes priority — as the device-tracker docs state
- **MUST** set `source_type` from the `SourceType` enum (for example `SourceType.ROUTER` for `ScannerEntity`, `SourceType.GPS` for `TrackerEntity`) and never as a freely chosen string
- **SHOULD** additionally set `ip_address`, `mac_address`, and `hostname` for a `ScannerEntity` with `source_type` `router` — the docs name this as an accelerator for DHCP discovery
- **MUST NOT** treat the `device_tracker` platform as a controllable entity — a device tracker is, per the docs, a read-only entity that only provides presence information

### Event

- **MUST** derive an event platform from `homeassistant.components.event.EventEntity`
- **MUST** provide `event_types` as the list of possible event types — the event docs mark it as **Required**
- **MUST** trigger an event via `_trigger_event(event_type, extra_data=None)` and call `async_write_ha_state()` afterwards — the entity is, per the docs, stateless; HA manages the state, the integration fires the events
- **MUST NOT** fire an event type not declared in `event_types` — the event docs require `_trigger_event` to raise a `ValueError` otherwise
- **SHOULD** set the `device_class` from `EventDeviceClass` (`BUTTON`, `DOORBELL`, `MOTION`) wherever a matching member exists
- **MUST** carry the standard event type `DoorbellEventType.RING` in `event_types` for `EventDeviceClass.DOORBELL` — the event docs mark this standard type as mandatory
- **SHOULD** deregister registered device callbacks when the entity is removed — as the event docs recommend

### Update

- **MUST** derive an update platform from `homeassistant.components.update.UpdateEntity`
- **MUST** provide `installed_version` and `latest_version` so HA can derive availability and difference — the update docs base the availability indicator on this
- **MUST** set `supported_features` from `UpdateEntityFeature` (`INSTALL`, `SPECIFIC_VERSION`, `BACKUP`, `PROGRESS`, `RELEASE_NOTES`) and provide exactly the required method per flag — `INSTALL` requires `install`/`async_install`, `RELEASE_NOTES` requires `release_notes`/`async_release_notes`
- **MUST** implement `async_install(version, backup, **kwargs)` such that `version=None` installs the latest version and the `backup` parameter triggers a backup before installation — as the update docs state
- **MUST NOT** set `UpdateEntityFeature.SPECIFIC_VERSION` or `UpdateEntityFeature.BACKUP` without `install`/`async_install` actually servicing the respective capability — both flags presuppose `INSTALL`
- **SHOULD** set `device_class` to `UpdateDeviceClass.FIRMWARE` when the update concerns a device firmware — the only documented member of this enum
- **MUST NOT** present an update as skippable when `auto_update=True` is set — the update docs state that with auto update enabled no updates can be skipped

## Acceptance Criteria

- [ ] No new integration uses the deprecated `air_quality` platform; air-quality measurements are separate `sensor` entities
- [ ] Every `weather` entity derives from `WeatherEntity` and provides `condition`, `native_temperature`, `native_temperature_unit`
- [ ] Every set `WeatherEntityFeature` forecast flag has its `async_forecast_*` method; forecasts are not in the entity state
- [ ] `async_forecast_twice_daily` entries set `is_daytime`
- [ ] Every `device_tracker` entity derives from `BaseScannerEntity`/`ScannerEntity`/`TrackerEntity` and sets `source_type` from the `SourceType` enum
- [ ] `ScannerEntity`/`BaseScannerEntity` provide `is_connected`; `TrackerEntity` sets `in_zones` or `latitude`+`longitude`
- [ ] `router` `ScannerEntity` entities set `ip_address`, `mac_address`, `hostname` to accelerate DHCP
- [ ] Every `event` entity derives from `EventEntity`, provides `event_types`, and fires only declared types via `_trigger_event`
- [ ] `EventDeviceClass.DOORBELL` entities carry `DoorbellEventType.RING` in `event_types`
- [ ] Every `update` entity derives from `UpdateEntity`, provides `installed_version`/`latest_version`, and has the required method for each `UpdateEntityFeature` flag
- [ ] `device_class` is set from the platform-owned enum wherever a member exists (`EventDeviceClass`, `UpdateDeviceClass.FIRMWARE`)

## Open Questions

- **Air-quality migration path**: Should this spec prescribe a concrete mapping table air-quality property → sensor `device_class`, or does the pointer to `ha/entity-platform-types` suffice?
- **Forecast cache convention**: The weather docs recommend caching but prescribe no concrete strategy. Does a cache-invalidation convention belong in this spec or in `ha/entity-architecture` (coordinator)?
- **Device-tracker base-class choice**: Should the skill derive the choice between `ScannerEntity` and `TrackerEntity` automatically from the available data (MAC vs. GPS) or always ask back?
- **Event translation keys**: Non-standard event types need translations. Should the spec prescribe a convention for their translation keys (interface to `ha/translations`)?
- **Version comparison strategy**: The update docs allow a `version_is_newer` override via AwesomeVersion. Should the skill generate this override by default or only on request?
