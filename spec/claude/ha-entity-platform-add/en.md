# Skill: `ha-entity-platform-add`

Status: draft

## Context

`ha/entity-platform-types` classifies the HA platform catalog into **declarative read-type platforms** (`sensor`, `binary_sensor`, `button` via `EntityDescription` tables) and **active, command-driven platforms** whose entity exposes async **command/set methods**: `climate`, `cover`, `light`, `fan`, `lock`, `media_player`, `vacuum`, `valve`, `humidifier`, `water_heater`, `siren`, `lawn_mower`, and others. Bidirectional platforms such as `switch`, `number`, `select`, `calendar`, `todo` are active too — their family spec mandates a set method (`async_set_native_value`/`async_select_option`/…) — but may be authored **either** purely declaratively as an `EntityDescription` table (then `ha-entity-description-mapper`) **or** as a full active entity class with a hand-written set method (then this skill); the boundary is the **authoring form**, not the domain. The active platforms spread across family specs: `ha/entity-platforms-controls` (`switch`/`button`/`scene`/`siren`/`valve`/`lock`/`remote`), `ha/entity-platforms-climate` (`fan`/`humidifier`/`water-heater`; `climate` itself in `ha/entity-platform-types`), `ha/entity-platforms-devices` (`alarm_control_panel`/`vacuum`/`lawn_mower`/`calendar`/`todo`/infrared/radio-frequency), `ha/entity-platforms-media` (`media_player`/`camera`/`image`), `ha/entity-platforms-voice` (`stt`/`tts`/`wake_word`/`assist_satellite`/`ai_task`/`notify`), `ha/entity-platforms-inputs` (`number`/`select`/`text`/`date`/`time`/`datetime`), and `ha/entity-platforms-sensors` (`weather`/`device_tracker`/`event`/`update`). No skill scaffolds an active platform entity so far.

This skill scaffolds **one** active platform entity into an **existing** integration: the platform module `<platform>.py` with the entity subclass (`ClimateEntity` / `CoverEntity` / `LightEntity` / …), the `EntityDescription` (where the family uses one), the `_attr_supported_features` / `supported_features` bitmask from the platform-native `*EntityFeature` enum, the async command methods the domain mandates (`async_turn_on`/`async_set_temperature`/`async_open_cover`/`async_set_hvac_mode` …), the `async_setup_entry` platform setup that adds the entities to the coordinator, and the state/attribute properties — conformant to `ha/entity-platform-types` plus the chosen family spec. The skill **MUST** have the operator name the target domain and confirm the family before generating.

## Scope

Scaffolding exactly one active platform entity per run into an existing `custom_components/<domain>/` integration: the `<platform>.py` module with the entity subclass, an optional `EntityDescription`, the `supported_features` bitmask from the `*EntityFeature` enum, the mandated async command methods, the `async_setup_entry` platform setup, and the state/attribute properties. The skill reads `ha/entity-platform-types` (the active-vs-declarative catalog) and the family spec matching the chosen domain, and validates.

## Goals

- Pick the correct active platform (domain) and its family spec from a described device capability and scaffold it spec-conformantly
- Derive the entity from the documented platform base class (`ClimateEntity`/`CoverEntity`/`LightEntity`/`FanEntity`/`LockEntity`/`MediaPlayerEntity`/`StateVacuumEntity`/`ValveEntity`/`HumidifierEntity`/`WaterHeaterEntity`/`SirenEntity`/`LawnMowerEntity` …)
- Set `supported_features` as a bitwise `|` combination of the platform-native `*EntityFeature` enum, never as a raw integer
- Implement the corresponding async command method for every set feature flag — a one-to-one flag ↔ method coupling, no flag set "on spec"
- Provide the state/attribute properties the domain marks as **Required** and have the `async_setup_entry` setup attach the entities to the coordinator

## Non-Goals

- Datapoints authored purely as an `EntityDescription` table (read-type `sensor`/`binary_sensor`/`button`, plus the table form of `number`/`select`/`switch`/`calendar`/`todo` with no hand-written command/set method) — `ha-entity-description-mapper`
- The coordinator itself (`DataUpdateCoordinator` setup and update mechanics) — `ha-coordinator-add`
- Greenfield scaffolding of an integration — `ha-integration-scaffold`
- Device-centric device-automation triggers/conditions/actions — `ha-device-automation-add`
- The generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`) and the typing mechanics in detail — `ha/entity-architecture` and `ha/entity-platform-types`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a climate / cover / light / fan / lock entity", "scaffold an active platform entity"
  - "implement async command methods for my <domain> entity"
  - "scaffolde eine aktive <Domain>-Entity", "füge eine Cover-/Light-/Fan-Entity hinzu"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the device capability (prose), from which the skill derives the platform/domain and the family
- **MUST** have the operator name the target domain and confirm the family before generating
- **MAY** capture: `platform`/`domain` directly, the `*EntityFeature` flags to set, and whether the family uses an `EntityDescription`

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** check the entity is authored as an **active** platform class with a hand-written async command/set method; if it is a read-type datapoint or a purely declarative `EntityDescription`-table mapping with no hand-written command/set method, the skill **MUST** point at `ha-entity-description-mapper` and abort
- **MUST** read `ha/entity-platform-types`, determine active-vs-declarative and the family from it, and read the matching family spec (`ha/entity-platforms-controls` / `-climate` / `-devices` / `-media` / `-voice` / `-inputs` / `-sensors`) in full
- **MUST** check a coordinator exists or a `runtime_data`/`config_entry` binding is reachable for `async_setup_entry` to attach the entities to; if absent, the skill **SHOULD** point at `ha-coordinator-add`
- **MUST NOT** overwrite an existing `<platform>.py` module; on collision abort

### Generation rules (from `ha/entity-platform-types` + the family spec)

- **MUST** create the platform module `<platform>.py` with the entity base class documented by the family spec
- **MUST** implement `async_setup_entry(hass, entry, async_add_entities)` that builds the entities and registers them via `async_add_entities(...)`, attaching to the coordinator or `config_entry.runtime_data` (coordinator mechanics referenced in `ha/entity-architecture`)
- **MUST** set `supported_features` as a bitwise `|` combination of the platform-native `*EntityFeature` enum (`ClimateEntityFeature`/`CoverEntityFeature`/`LightEntityFeature`/`FanEntityFeature`/`LockEntityFeature`/`MediaPlayerEntityFeature`/`VacuumEntityFeature`/`ValveEntityFeature`/`HumidifierEntityFeature`/`WaterHeaterEntityFeature`/`SirenEntityFeature`/`LawnMowerEntityFeature`/…), never as a raw integer
- **MUST** implement, for every set feature flag, exactly the async command method documented by the family spec (e.g. `CoverEntityFeature.OPEN` → `async_open_cover`, `ClimateEntityFeature.TARGET_TEMPERATURE` → `async_set_temperature`, `LockEntityFeature.OPEN` → `async_open`, `FanEntityFeature.SET_SPEED` → `async_set_percentage`, `MediaPlayerEntityFeature.PLAY` → `async_media_play`)
- **MUST NOT** set a feature flag "on spec" whose command method is not (yet) implemented — an advertised but non-operable feature breaks the UI and voice binding
- **MUST** provide the state/attribute properties the domain marks as **Required** (e.g. `hvac_mode`/`hvac_modes` for `climate`, `is_closed` for `cover`, `color_mode`/`supported_color_modes` for `light`, `activity` for `vacuum`/`lawn_mower`, `alarm_state` for `alarm_control_panel`) and use only the built-in state/mode enums (e.g. only built-in `HVACMode` members; `VacuumActivity`/`LawnMowerActivity`)
- **MUST** set the `device_class` from the closed platform-native enum where a matching member exists (`CoverDeviceClass`, `ValveDeviceClass`, `HumidifierDeviceClass`, `MediaPlayerDeviceClass`, …) — never a free-chosen string
- **MAY** create an `EntityDescription` when the family uses the `EntityDescription` pattern for the platform, and set `supported_features`/`device_class` there instead of via `_attr_*` (setting mechanics see `ha/entity-architecture`)
- **MUST** name identifiers per `ha/naming-conventions`, not duplicate the generic entity pattern (delegate to `ha/entity-architecture`), and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: `<platform>.py` exists; the entity derives from the documented base class; `async_setup_entry` registers entities via `async_add_entities`; `supported_features` is a `*EntityFeature` bitmask (not a raw integer); every set flag has its async command method; all **Required** properties are implemented; state/mode enums are built-in; a set `device_class` comes from the platform-native enum
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria of `ha/entity-platform-types` and the chosen family spec, plus the changed file paths and the quality-scale marker (**Gold** for correct per-platform device-class coverage, `entity-device-class`)

### Prohibitions

- **MUST NOT** scaffold more than one platform entity per run
- **MUST NOT** scaffold a purely declarative `EntityDescription`-table entity with no hand-written command/set method through this skill — use `ha-entity-description-mapper`
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill derives the platform/domain and family (or asks) and has the target domain + family confirmed before generation
- [ ] `<platform>.py` exists; the entity derives from the documented platform base class
- [ ] `async_setup_entry` builds the entities and registers them via `async_add_entities`, attaching to the coordinator/`runtime_data`
- [ ] `supported_features` is a bitwise `|` combination of the platform-native `*EntityFeature` enum, never a raw integer
- [ ] Every set feature flag has its corresponding async command method; no flag set "on spec"
- [ ] All state/attribute properties the domain marks as **Required** are implemented; state/mode enums are built-in
- [ ] A set `device_class` comes from the closed platform-native enum; purely declarative `EntityDescription`-table entities are referred to `ha-entity-description-mapper`
- [ ] Report names the file paths and the quality-scale marker **Gold** (`entity-device-class`)

## Open questions

- **Family-spec selection automation**: Should the skill derive the family strictly from the domain name, or always ask on ambiguity (e.g. `valve` vs. `cover`)? Currently: derive and confirm.
- **`EntityDescription` on active platforms**: Some active platforms use the `EntityDescription` pattern, others don't. Should the skill fix per family whether a description is generated, or decide per run?
- **Coordinator requirement**: Must a coordinator exist, or may the skill also scaffold a direct `config_entry.runtime_data` binding without a coordinator? Currently: coordinator preferred, point at `ha-coordinator-add` when absent.
- **Infrared/RF special case**: `ha/entity-platforms-devices` treats IR/RF as an abstraction layer without a `supported_features` enum. Should this skill cover these special cases or point at a follow-up spec?
