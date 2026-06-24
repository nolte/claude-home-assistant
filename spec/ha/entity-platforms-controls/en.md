# HA Integration: Entity Platforms (Controls)

Status: draft

## Context

A Custom Integration models controllable actuators through the control platforms of Home Assistant: `switch`, `button`, `scene`, `siren`, `valve`, `lock`, and `remote`. Each of these platforms represents a concrete control capability — turn something on/off, trigger a stateless action, reproduce a target state, sound a siren, move a valve, lock/unlock a lock, or send commands to a device. This spec is the **concrete catalog** of these control/actuator platforms: for each platform the modeled capability, the base entity class, the platform-owned `device_class` enum (if any), the `supported_features` flags, and the methods to implement.

The **generic entity pattern** — base class, `_attr_has_entity_name`, `unique_id`, the `EntityDescription` pattern, entity categories, and coordinator binding — is fixed in `ha/entity-architecture` and is **not repeated here**. The **cross-cutting typing concept** — `device_class`/`state_class`/`supported_features` as a pattern, the rule "advertise only actually implemented features", the bitmask combination via `|` — lives in `ha/entity-platform-types`. This spec references both by slug and concretizes them for the seven control platforms.

The pervasive coupling reads: a `supported_features` flag **may only be set when its associated method is implemented** — the platform docs couple flag and method one-to-one (for example `LockEntityFeature.OPEN` ↔ `async_open`, `ValveEntityFeature.SET_POSITION` ↔ `async_set_valve_position`).

## Goals

- Choose the semantically appropriate control platform from `switch`/`button`/`scene`/`siren`/`valve`/`lock`/`remote` for each controllable actuator capability
- Derive the correct base entity class per platform (`SwitchEntity`, `ButtonEntity`, `Scene`, `SirenEntity`, `ValveEntity`, `LockEntity`, `RemoteEntity`)
- Set the platform-owned `device_class` from the closed enum wherever an enum exists (`SwitchDeviceClass`, `ButtonDeviceClass`, `ValveDeviceClass`)
- Set `supported_features` from the platform-owned feature enum (`SirenEntityFeature`, `ValveEntityFeature`, `LockEntityFeature`, `RemoteEntityFeature`) so that every flag has its implemented method
- Provide the methods required per platform (`async_turn_on/off`, `async_press`, `async_activate`, `async_lock/unlock/open`, `async_open_valve/close_valve/set_valve_position`, `async_send_command`)

## Non-Goals

- Generic entity pattern (base class, `_attr_has_entity_name`, `unique_id`, `EntityDescription` pattern, entity categories, coordinator binding) — fully in `ha/entity-architecture`; this spec only references it
- The cross-cutting typing concept (`device_class`/`state_class`/`supported_features` as a pattern, bitmask mechanics, feature-↔-method rule) — fully in `ha/entity-platform-types`; this spec only concretizes it for the control platforms
- HA translation format (`strings.json`, `entity.<platform>.<key>.name`, tone/activity names) — separate `ha/translations` spec
- Icon selection and icon translations (`icons.json`, `default`/`state`) — separate `ha/icons` spec
- Read-only/measurement platforms (`sensor`, `binary_sensor`) and the remaining actuator platforms beyond the seven covered here (`light`, `cover`, `climate`, `fan`, `number`, `select`, `humidifier`, …) — the generic rules apply by analogy but are not the subject of this catalog

## Requirements

### `switch`

- **MUST** derive an entity that turns something on or off (for example a relay) from `SwitchEntity` — as the switch docs state
- **MUST** implement `async_turn_on` and `async_turn_off` (or their synchronous variants `turn_on`/`turn_off`) and report state via `is_on`
- **SHOULD** override `async_toggle`/`toggle` only when a device-specific toggle is needed; without an implementation HA derives `toggle` from `is_on` — as the switch docs state
- **SHOULD** set the `device_class` from `SwitchDeviceClass` (`SwitchDeviceClass.OUTLET` for an outlet, `SwitchDeviceClass.SWITCH` for a generic switch) where applicable — it may map to Google device types
- **MUST NOT** use `switch` for a state that is only reported but cannot be switched from HA — `binary_sensor` is correct there; and not for a stateless action — `button` or a custom event is correct there (as the switch docs delimit)

### `button`

- **MUST** derive an entity that triggers an action towards a device or service but remains **stateless** from the HA perspective from `ButtonEntity` — as the button docs state (for example firmware upgrade, restart, resetting a counter)
- **MUST** implement `async_press` (or the synchronous variant `press`) — it is the only platform-specific method; the platform provides no state properties of its own
- **SHOULD** set the `device_class` from `ButtonDeviceClass` (`IDENTIFY`, `RESTART`) where applicable — it may map to Google device types
- **MUST NOT** use `ButtonDeviceClass.UPDATE` where an `update` entity would be correct — the button docs explicitly advise against it
- **MUST NOT** use `button` for something with an actual on/off state (use `switch`) or to integrate a real, physical button device (use custom events) — as the button docs delimit

### `scene`

- **MUST** derive an entity that reproduces a wanted state for a group of entities and remains **stateless** from the HA perspective from `Scene` — as the scene docs state
- **MUST** implement `async_activate` (or the synchronous variant `activate`) — it is called when the `activate` button is pressed or `scene.turn_on` is called
- **SHOULD** derive from `BaseScene` instead, override `_async_activate()`, and call `_async_record_activation()` on external activation for scenes that can also be activated **outside** of HA (for example by a physical button) — as the scene docs state
- **MUST NOT** set a `device_class` on a scene entity — the scene docs state there are none and the attribute is not set
- **MUST NOT** use `scene` for something with an actual on/off state — `switch` is correct there (as the scene docs delimit)

### `siren`

- **MUST** derive an entity whose main purpose is to control siren devices (for example a doorbell or chime) from `SirenEntity` — as the siren docs state
- **MUST** implement `async_turn_on` and set `SirenEntityFeature.TURN_ON`; implement `async_turn_off` and set `SirenEntityFeature.TURN_OFF` where the device can be turned off — the siren docs couple each service call to its feature flag
- **MUST** set `supported_features` as a bitwise `|` combination from `SirenEntityFeature` — the permitted flags are `TURN_ON`, `TURN_OFF`, `TONES`, `DURATION`, `VOLUME_SET`
- **MUST** provide `available_tones` (list or dict) when `SirenEntityFeature.TONES` is set — the siren docs require this property exactly for that feature
- **MUST NOT** set `SirenEntityFeature.DURATION` or `SirenEntityFeature.VOLUME_SET` when the device does not service the corresponding `turn_on` parameter (`duration`, `volume_level`) — the base platform filters non-advertised parameters out of the call

### `valve`

- **MUST** derive an entity that controls a valve (for example a water or gas valve) from `ValveEntity` — as the valve docs state
- **MUST** set `reports_position` (required property); for `reports_position = True` additionally provide `current_valve_position` (0 = closed, 100 = fully open), otherwise report state via `is_closed`/`is_closing`/`is_opening`
- **MUST** set `supported_features` as a bitwise `|` combination from `ValveEntityFeature` (`OPEN`, `CLOSE`, `SET_POSITION`, `STOP`) and implement exactly the method whose flag is set — `OPEN` ↔ `async_open_valve`, `CLOSE` ↔ `async_close_valve`, `SET_POSITION` ↔ `async_set_valve_position`, `STOP` ↔ `async_stop_valve`
- **MUST** leave `async_open_valve`/`async_close_valve` **unimplemented** for positionable valves and provide only `async_set_valve_position` — as the valve docs explicitly state
- **SHOULD** set the `device_class` from `ValveDeviceClass` (`ValveDeviceClass.WATER`, `ValveDeviceClass.GAS`) where applicable

### `lock`

- **MUST** derive an entity that can be locked and unlocked from `LockEntity` — as the lock docs state
- **MUST** implement `async_lock` and `async_unlock` (or the synchronous variants `lock`/`unlock`) and report state via `is_locked`/`is_locking`/`is_unlocking` (and optionally `is_jammed`, `is_opening`, `is_open`)
- **MUST** implement `async_open` (unlatch/open the latch) **only** when `LockEntityFeature.OPEN` is set — it is the only flag of the `LockEntityFeature` enum
- **SHOULD** set `code_format` (regex) when the lock requires a user code to lock/unlock, and report `changed_by` when the source of the last change is known
- **MUST NOT** set `LockEntityFeature.OPEN` when the device cannot open the latch or `async_open` is not implemented — otherwise the entity advertises an unserviceable feature

### `remote`

- **MUST** derive an entity that sends commands (a physical sending device or a virtual HA device that controls another device) from `RemoteEntity` — as the remote docs state
- **MUST** implement `async_turn_on` and `async_turn_off` (or the synchronous variants) and report state via `is_on`
- **MUST** set `supported_features` as a bitwise `|` combination from `RemoteEntityFeature` (`LEARN_COMMAND`, `DELETE_COMMAND`, `ACTIVITY`)
- **MUST** implement `async_learn_command` **only** when `RemoteEntityFeature.LEARN_COMMAND` is set and `async_delete_command` **only** when `RemoteEntityFeature.DELETE_COMMAND` is set — as the remote docs state
- **SHOULD** report `current_activity` and `activity_list` when `RemoteEntityFeature.ACTIVITY` is set and provide `async_send_command` for sending commands

## Acceptance Criteria

- [ ] Every actuator capability is modeled on the semantically appropriate control platform and derives from the correct base class (`SwitchEntity`/`ButtonEntity`/`Scene`/`SirenEntity`/`ValveEntity`/`LockEntity`/`RemoteEntity`)
- [ ] `switch` entities implement `async_turn_on`/`async_turn_off`, report `is_on`, and set `SwitchDeviceClass` where applicable
- [ ] `button` entities implement `async_press`, remain stateless, and do not use `ButtonDeviceClass.UPDATE` where an `update` entity would be correct
- [ ] `scene` entities implement `async_activate` (or `BaseScene`/`_async_activate` for external activation) and set no `device_class`
- [ ] `siren` entities set `supported_features` from `SirenEntityFeature` and provide `available_tones` when `TONES` is set
- [ ] `valve` entities set `reports_position`, combine `ValveEntityFeature` flags only with the respectively implemented method, and leave `open_valve`/`close_valve` unimplemented for positionable valves
- [ ] `lock` entities implement `async_lock`/`async_unlock` and set `LockEntityFeature.OPEN` only when `async_open` is implemented
- [ ] `remote` entities set `RemoteEntityFeature` flags only with the respectively implemented method (`LEARN_COMMAND` ↔ `async_learn_command`, `DELETE_COMMAND` ↔ `async_delete_command`)
- [ ] No `supported_features` flag is set without its corresponding method being implemented
- [ ] Every set `device_class` comes from the platform-owned closed enum, never from a freely chosen string

## Open Questions

- **Quality-scale coverage**: This spec carries no dedicated quality-scale marker set for the control platforms, since `entity-device-class` is already anchored in `ha/entity-platform-types`. Should the catalog additionally point per platform to Bronze/Silver rules (for example `has-entity-name`) or does that stay in `ha/entity-architecture`?
- **`siren` tone-dictionary translation**: `available_tones` can be a dict (display value → device key). Does a translation-key convention for the display values belong in this spec or fully in `ha/translations`?
- **`remote` activity model**: The remote docs describe `current_activity`/`activity_list` tersely. Should the spec prescribe a convention for translating the activity names (interface to `ha/translations`)?
- **`valve`-vs-`cover` delimitation**: Valve and cover share the position/open-close model. Should an explicit decision rule (valve = flow, cover = opening/cover) live in this spec or in `ha/entity-platform-types`?
