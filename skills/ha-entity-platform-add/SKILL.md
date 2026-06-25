---
name: ha-entity-platform-add
description: Scaffold one active platform entity into an existing Home Assistant Custom Integration — a command-driven domain (climate, cover, light, fan, lock, media_player, vacuum, valve, humidifier, water_heater, siren, lawn_mower, …) whose entity exposes async command methods — conforming to spec/ha/entity-platform-types plus the matching ha/entity-platforms-* family spec. Creates the platform module <platform>.py with the entity subclass (ClimateEntity / CoverEntity / LightEntity / …), its EntityDescription where the family uses one, the supported_features bitmask from the domain's *EntityFeature enum, the mandated async command methods (async_turn_on, async_set_temperature, async_open_cover, async_set_hvac_mode), the async_setup_entry platform setup adding entities to the coordinator, and the state/attribute properties. Requires the operator to name the target domain and confirm the family first. Activate on "add a climate/cover/light/fan/lock entity", "scaffold an active platform entity", "implement async command methods for my <domain> entity", "scaffolde eine aktive <Domain>-Entity", "füge eine Cover-Entity hinzu". Do not activate for declarative read-type entities via EntityDescription tables (ha-entity-description-mapper), the coordinator itself (ha-coordinator-add), greenfield integration scaffolding (ha-integration-scaffold), device-automation triggers (ha-device-automation-add), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, entity-platform]
---

# HA Entity Platform Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-entity-platform-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-entity-platform-add/en.md).

## Why this is a skill, not an agent

- **Human-visible scaffolding surface** — the operator describes a device capability and reads back the platform module, the feature bitmask, the command methods, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-coordinator-add`, `ha-entity-description-mapper`, `ha-device-automation-add`).
- **Mid-flow interactivity** — the platform/domain decision and the family confirmation are per-run dialogues the operator approves before generation.
- **Bounded, inline generation** — one platform module plus its description and setup fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the domain decision and the active-vs-declarative gate belong in the operator's working context; skill wins.

## When this skill activates

Use this skill to scaffold **one** active platform entity — a command-driven domain (`climate`, `cover`, `light`, `fan`, `lock`, `media_player`, `vacuum`, `valve`, `humidifier`, `water_heater`, `siren`, `lawn_mower`, …) whose entity exposes async command methods — into an existing integration.

## When NOT to activate

- declarative read-type entities (`sensor`/`binary_sensor`/`button`/`number`/`select`/`switch`/`calendar`/`todo` via `EntityDescription` tables) → `ha-entity-description-mapper`
- the coordinator itself → `ha-coordinator-add`
- greenfield integration scaffolding → `ha-integration-scaffold`
- device-automation triggers/conditions/actions → `ha-device-automation-add`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One platform entity, one run.** No multi-platform batches.
2. **Read the operationalized spec first.** Read [`ha/entity-platform-types`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-platform-types/de.md) to pick active-vs-declarative and the family, **then** read the matching family spec ([`controls`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-platforms-controls/de.md) / [`climate`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-platforms-climate/de.md) / [`devices`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-platforms-devices/de.md) / [`media`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-platforms-media/de.md) / [`voice`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-platforms-voice/de.md) / [`inputs`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-platforms-inputs/de.md) / [`sensors`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-platforms-sensors/de.md)) in full. Do not generate from memory.
3. **Active platforms only.** This skill scaffolds command-driven entities. If the capability is a declarative read-type one (`sensor`/`binary_sensor`/`button`/`number`/`select`/`switch`/`calendar`/`todo` via `EntityDescription` tables), point at `ha-entity-description-mapper` and abort.
4. **Name the domain, confirm the family.** Require the operator to name the target domain and confirm the resolved family before generating.
5. **Base class from the family spec.** Derive the entity from the documented platform base class (`ClimateEntity`/`CoverEntity`/`LightEntity`/`FanEntity`/`LockEntity`/`MediaPlayerEntity`/`StateVacuumEntity`/`ValveEntity`/`HumidifierEntity`/`WaterHeaterEntity`/`SirenEntity`/`LawnMowerEntity` …).
6. **Feature bitmask from the enum.** Set `supported_features` as a bitwise `|` combination of the platform-native `*EntityFeature` enum — **never** a raw integer.
7. **Flag ↔ method, one-to-one.** Implement the documented async command method for every set flag (e.g. `CoverEntityFeature.OPEN` ↔ `async_open_cover`, `ClimateEntityFeature.TARGET_TEMPERATURE` ↔ `async_set_temperature`, `LockEntityFeature.OPEN` ↔ `async_open`, `FanEntityFeature.SET_SPEED` ↔ `async_set_percentage`). Never set a flag "on spec" whose method is missing.
8. **Required properties, built-in enums.** Provide every property the domain marks as **Required** (`hvac_mode`/`hvac_modes`, `is_closed`, `color_mode`/`supported_color_modes`, `activity`, `alarm_state`, …) and use only the built-in state/mode enums (only built-in `HVACMode`; `VacuumActivity`/`LawnMowerActivity`). Set `device_class` from the closed platform-native enum where a member exists, never a free string.
9. **Wire the setup.** Implement `async_setup_entry(hass, entry, async_add_entities)` that builds the entities and registers them via `async_add_entities`, attaching to the coordinator / `config_entry.runtime_data`; if no coordinator exists, point at `ha-coordinator-add`.
10. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)**, do not duplicate the generic entity pattern (delegate to [`ha/entity-architecture`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-architecture/de.md)), and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `capability` | yes | — | the device capability the entity expresses, in prose |
| `platform` / `domain` | no | inferred + confirmed | the active platform, e.g. `climate` / `cover` / `light` |
| `features` | no | derived | the `*EntityFeature` flags to set |
| `use_entity_description` | no | per family | whether the family uses the `EntityDescription` pattern |

If the operator is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. The capability is an **active** platform (exposes command methods). If it is a declarative read-type one, point at `ha-entity-description-mapper` and abort.
3. Read `ha/entity-platform-types`; resolve the platform + family (infer + confirm); read the matching family spec in full.
4. A coordinator or a `config_entry.runtime_data` binding is reachable for `async_setup_entry`; if absent, point at `ha-coordinator-add`.
5. `<platform>.py` is not already present. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the resolved platform + family, the `*EntityFeature` flags to set, the **Required** properties, and whether an `EntityDescription` is used, in one paragraph. Wait for confirmation.

### 2) Generate

| Family | Spec | Example base class | Example flag → method |
|---|---|---|---|
| controls | `ha/entity-platforms-controls` | `LockEntity` / `ValveEntity` / `SirenEntity` | `LockEntityFeature.OPEN` → `async_open` |
| climate | `ha/entity-platforms-climate` (+ `climate` in `ha/entity-platform-types`) | `FanEntity` / `WaterHeaterEntity` / `ClimateEntity` | `ClimateEntityFeature.TARGET_TEMPERATURE` → `async_set_temperature` |
| devices | `ha/entity-platforms-devices` | `StateVacuumEntity` / `LawnMowerEntity` | `VacuumEntityFeature.START` → `async_start` |
| media | `ha/entity-platforms-media` | `MediaPlayerEntity` | `MediaPlayerEntityFeature.PLAY` → `async_media_play` |
| voice | `ha/entity-platforms-voice` | `AssistSatelliteEntity` | `AssistSatelliteEntityFeature.ANNOUNCE` → `async_announce` |
| inputs | `ha/entity-platforms-inputs` | `NumberEntity` / `SelectEntity` | (one set method, e.g. `async_set_native_value`) |
| sensors | `ha/entity-platforms-sensors` | `WeatherEntity` / `UpdateEntity` | `WeatherEntityFeature.FORECAST_DAILY` → `async_forecast_daily` |

Generate `<platform>.py` with the entity subclass, its `supported_features` bitmask, the per-flag async command methods, the **Required** state/attribute properties, the `async_setup_entry` setup, and (where the family uses it) the `EntityDescription`. For `light`, also set `supported_color_modes` + `color_mode`.

### 3) Validate and report

Validate offline (`<platform>.py` present; correct base class; `async_setup_entry` registers via `async_add_entities`; `supported_features` is a `*EntityFeature` bitmask, not a raw integer; every set flag has its async command method; all **Required** properties implemented; built-in state/mode enums; `device_class` from the platform-native enum). Emit a CONFORMANT / NEEDS-WORK report keyed to the acceptance criteria of `ha/entity-platform-types` and the chosen family spec, plus the changed file paths and the quality-scale marker (**Gold**, `entity-device-class`).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Declarative read-type entities → `ha-entity-description-mapper`
- The coordinator itself → `ha-coordinator-add`
- Greenfield scaffold → `ha-integration-scaffold`
- Device-automation triggers/conditions/actions → `ha-device-automation-add`
- Deploy to live HA → out of scope
