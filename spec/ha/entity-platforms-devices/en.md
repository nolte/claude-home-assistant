# HA Integration: Entity Platforms (Device Domains)

Status: draft

## Context

Beyond the simple measurement and switching platforms, Home Assistant has a set of **complex device domains** that model a whole device with a state machine, action commands, and in some cases CRUD records: alarm system, vacuum, lawn mower, calendar, to-do list, and the infrared and radio-frequency abstractions. Each of these domains derives from its own platform base class and expects a characteristic combination of state enum, `supported_features` bitmask, and feature-coupled `async_` methods.

The generic entity pattern — base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, the `EntityDescription` pattern, entity categories, and coordinator binding — is fixed in `ha/entity-architecture` and is **not repeated here**. The generic typing mechanics — `device_class` from closed enums, `supported_features` as a bitmask, the one-to-one coupling of flag and method — are fixed in `ha/entity-platform-types` and are **only referenced here**. This spec is the **concrete catalog** for the named device domains: per platform the correct base class, the state enum, the allowed feature flags, and the mandatory methods, each grounded in the platform docs of `developers.home-assistant`.

These domains are uniformly actuator- and command-driven: their state is an activity enum (`VacuumActivity`, `LawnMowerActivity`, `AlarmControlPanelState`) or a derived state (calendar: active event; to-do: count of open items), and every advertised feature promises an implemented `async_` method. Infrared and radio frequency are a special case: they define emitter/receiver/transmitter entities as an **abstraction layer** between hardware integrations and consumer integrations.

## Goals

- Name the correct platform base class for each of the seven device domains (`AlarmControlPanelEntity`, `StateVacuumEntity`, `LawnMowerEntity`, `CalendarEntity`, `TodoListEntity`, infrared emitter/receiver, `RadioFrequencyTransmitterEntity`)
- Return each domain's state from the documented state enum or documented state derivation
- Set `supported_features` per domain exclusively from the domain-owned feature enum and couple every flag to its implemented `async_` method
- Provide the properties marked **Required** per domain (`alarm_state`, `activity`, `event`, `todo_items`)
- Create infrared and radio-frequency entities correctly as a hardware abstraction layer and respect their consumer/helper separation
- Have generated code start with flag, method, and state consistent per device domain

## Non-Goals

- Generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription` pattern, entity categories, coordinator binding) — fully in `ha/entity-architecture`; this spec only references it
- Generic typing mechanics (`device_class` enums, `supported_features` bitmasks, feature-↔-method coupling in general) — fully in `ha/entity-platform-types`; this spec only applies them per domain
- Simple measurement/switching platforms (`sensor`, `binary_sensor`, `switch`, `light`, `cover`, …) — covered as examples in `ha/entity-platform-types`
- HA translation format (`strings.json`, state and feature translations) — separate `ha/translations` spec
- Icon selection and icon translations (`icons.json`) — separate `ha/icons` spec
- Device domains beyond the seven covered here (for example `media_player`, `climate`, `water_heater`) — the generic rules apply by analogy

## Requirements

### Alarm control panel

- **MUST** derive an alarm-panel entity from `AlarmControlPanelEntity` — this platform models the control of an alarm
- **MUST** return the state via the property `alarm_state` marked **Required**, as a member of `AlarmControlPanelState` (`DISARMED`, `ARMED_HOME`, `ARMED_AWAY`, `ARMED_NIGHT`, `ARMED_VACATION`, `ARMED_CUSTOM_BYPASS`, `PENDING`, `ARMING`, `DISARMING`, `TRIGGERED`)
- **MUST** set `supported_features` from `AlarmControlPanelEntityFeature` (`ARM_HOME`, `ARM_AWAY`, `ARM_NIGHT`, `ARM_VACATION`, `ARM_CUSTOM_BYPASS`, `TRIGGER`) as a bitwise `|` combination and implement the associated method for every flag (`ARM_HOME` → `async_alarm_arm_home`, `ARM_AWAY` → `async_alarm_arm_away`, `ARM_NIGHT` → `async_alarm_arm_night`, `ARM_VACATION` → `async_alarm_arm_vacation`, `ARM_CUSTOM_BYPASS` → `async_alarm_arm_custom_bypass`, `TRIGGER` → `async_alarm_trigger`)
- **MUST** provide `async_alarm_disarm` (or the synchronous variant) to model disarming — the docs list disarm as its own method independent of a feature flag
- **SHOULD** set `code_format` from `CodeFormat` (`None`, `NUMBER`, `TEXT`) when the panel requires a code, and carry `code_arm_required` to match device reality — both properties drive the code entry in the frontend
- **MUST NOT** use `ARMED_CUSTOM_BYPASS` to signal a disconnected, malfunctioning, or low-battery sensor — the docs require dedicated sensor entities for that

### Vacuum

- **MUST** derive a vacuum entity from `StateVacuumEntity`
- **MUST** return the state via the property `activity` marked **Required**, as a member of `VacuumActivity` (`CLEANING`, `DOCKED`, `IDLE`, `PAUSED`, `RETURNING`, `ERROR`)
- **MUST** set the `VacuumEntityFeature.STATE` flag on every entity derived from `StateVacuumEntity` — the docs explicitly require it for all derived platforms
- **MUST** set `supported_features` from `VacuumEntityFeature` as a bitwise `|` combination and couple every set flag to its method (`START` → `async_start`, `PAUSE` → `async_pause`, `STOP` → `async_stop`, `RETURN_HOME` → `async_return_to_base`, `FAN_SPEED` → `async_set_fan_speed`, `CLEAN_SPOT` → `async_clean_spot`, `LOCATE` → `async_locate`, `SEND_COMMAND` → `async_send_command`)
- **MUST** provide the `fan_speed_list` property (available speeds) and `fan_speed` (current speed) when `VacuumEntityFeature.FAN_SPEED` is set — otherwise `fan_speed_list` raises `NotImplementedError`
- **MUST** implement the methods `async_get_segments` and `clean_segments`/`async_clean_segments` when `VacuumEntityFeature.CLEAN_AREA` is set — the docs mark both as required for `CLEAN_AREA`

### Lawn mower

- **MUST** derive a lawn-mower entity from `LawnMowerEntity`
- **MUST** return the state via the property `activity` as a member of `LawnMowerActivity` (`MOWING`, `DOCKED`, `PAUSED`, `RETURNING`, `ERROR`)
- **MUST** set `supported_features` from `LawnMowerEntityFeature` (`START_MOWING`, `PAUSE`, `DOCK`) as a bitwise `|` combination and couple every flag to its method (`START_MOWING` → `async_start_mowing`, `PAUSE` → `async_pause`, `DOCK` → `async_dock`)
- **MUST NOT** set a lawn-mower feature flag whose `async_` method is not implemented — the docs couple each of the three flags to exactly one method

### Calendar

- **MUST** derive a calendar entity from `CalendarEntity` — this platform models a set of events with start/end times
- **MUST** provide the property `event` marked **Required** with the current or next upcoming `CalendarEvent` (or `None`); from it HA derives the binary-sensor-like state (active event yes/no)
- **MUST** implement `async_get_events(hass, start_date, end_date)` and return the events ordered and with resolved (flattened) recurring events in the HA timezone context
- **MUST** interpret times in the HA timezone (for example via `homeassistant.util.dt.now`) and carry all-day events as a `datetime.date` (not a date with a time)
- **MUST** implement the associated mutation method for every set `CalendarEntityFeature` flag (`CREATE_EVENT` → `async_create_event`, `DELETE_EVENT` → `async_delete_event`, `UPDATE_EVENT` → `async_update_event`)
- **MUST** handle rfc5545 fields and recurring events when supporting mutations (series via `uid`; single instance via `uid` + `recurrence_id`; range additionally via `recurrence_range = THISANDFUTURE`)
- **SHOULD** call `CalendarEntity.async_update_event_listeners` after CRUD operations outside a state change to notify subscribers — the state is not automatically updated on create/update/delete

### To-do list

- **MUST** derive a to-do-list entity from `TodoListEntity`
- **MUST** provide the property `todo_items` marked **Required** (ordered `list[TodoItem]`); the state is the count of incomplete items
- **MUST** carry each `TodoItem` with the fields required for state and updates (`uid`, `summary`, `status` from `TodoItemStatus` `NEEDS_ACTION`/`COMPLETE`)
- **MUST** implement the associated method for every set `TodoListEntityFeature` flag (`CREATE_TODO_ITEM` → `async_create_todo_item`, `DELETE_TODO_ITEM` → `async_delete_todo_items`, `UPDATE_TODO_ITEM` → `async_update_todo_item`, `MOVE_TODO_ITEM` → `async_move_todo_item`)
- **MUST** support deleting multiple items when `DELETE_TODO_ITEM` is set — `async_delete_todo_items` takes a `list[str]` of `uids`
- **SHOULD** set the `due` feature flags (`SET_DUE_DATE_ON_ITEM` for `datetime.date`, `SET_DUE_DATETIME_ON_ITEM` for `datetime.datetime`) and `SET_DESCRIPTION_ON_ITEM` only when the respective field can actually be set on create/update
- **MUST** insert the item with the given `uid` after the item denoted by `previous_uid` when moving (`MOVE_TODO_ITEM`) (`previous_uid = None` means the first position)

### Infrared (emitter / receiver)

- **MUST** derive an IR emitter entity from `InfraredEmitterEntity` and an IR receiver entity from `InfraredReceiverEntity` — the infrared domain separates transmit and receive hardware into two entity kinds
- **MUST** implement `async_send_command(self, command)` in an emitter integration that performs the actual IR transmission and raises `HomeAssistantError` on failure
- **MUST** report received signals in a receiver integration via the base-class method `_handle_received_signal` (with `InfraredReceivedSignal`) and leave the state update to the base mechanism
- **MUST NOT** set the `device_class` of the infrared entity itself — the base classes assign `InfraredDeviceClass.emitter` or `InfraredDeviceClass.receiver` automatically
- **MUST NOT** change the state of the infrared entity in the integration — it represents the timestamp of the last sent/received signal and is maintained by the base class
- **MUST NOT** call `InfraredEmitterEntity.async_send_command` directly from a consumer integration — instead use the helper `infrared.async_send_command` (or the consumer base class `InfraredEmitterConsumerEntity`), which propagates state and context
- **SHOULD** use the provided base classes (`InfraredEmitterConsumerEntity`, `InfraredReceiverConsumerEntity`) or the helpers (`async_get_emitters`, `async_get_receivers`, `async_subscribe_receiver`) in a consumer integration instead of holding direct references to entity instances

### Radio frequency (transmitter)

- **MUST** derive an RF transmitter entity from `RadioFrequencyTransmitterEntity` — the radio-frequency domain models a virtual RF transmitter as an abstraction layer over the hardware
- **MUST** declare the property `supported_frequency_ranges` as a list of `(min_hz, max_hz)` tuples in a transmitter integration, so consumers can pick a compatible transmitter
- **MUST** implement `async_send_command(self, command)` that performs the actual RF transmission and raises `HomeAssistantError` on failure
- **MUST NOT** change the state of the radio-frequency entity in the integration — it represents the timestamp of the last sent RF command and is maintained by the base class
- **MUST NOT** call `RadioFrequencyTransmitterEntity.async_send_command` directly from a consumer integration — instead use the helper `radio_frequency.async_send_command`, which manages state and context
- **SHOULD** resolve a matching transmitter via `radio_frequency.async_get_transmitters(hass, frequency, modulation)` in a consumer integration; the docs currently support `ModulationType.OOK` only

## Acceptance Criteria

- [ ] Every device domain derives from its documented base class (`AlarmControlPanelEntity`, `StateVacuumEntity`, `LawnMowerEntity`, `CalendarEntity`, `TodoListEntity`, `InfraredEmitterEntity`/`InfraredReceiverEntity`, `RadioFrequencyTransmitterEntity`)
- [ ] Alarm entity returns `alarm_state` from `AlarmControlPanelState`; every set `AlarmControlPanelEntityFeature` flag has its arm/trigger method; `async_alarm_disarm` is implemented
- [ ] Vacuum entity returns `activity` from `VacuumActivity`, sets `VacuumEntityFeature.STATE`, and every further flag (`START`/`PAUSE`/`STOP`/`RETURN_HOME`/`FAN_SPEED`/…) has its method
- [ ] Lawn-mower entity returns `activity` from `LawnMowerActivity`; `START_MOWING`/`PAUSE`/`DOCK` are set exactly when `async_start_mowing`/`async_pause`/`async_dock` are implemented
- [ ] Calendar entity returns `event`, implements `async_get_events` with ordered, flattened events in the HA timezone; every `CalendarEntityFeature` flag (`CREATE`/`DELETE`/`UPDATE_EVENT`) has its mutation method with rfc5545 recurrence handling
- [ ] To-do entity returns `todo_items`; every `TodoListEntityFeature` flag has its method; `async_delete_todo_items` deletes multiple items; `MOVE_TODO_ITEM` respects `previous_uid`
- [ ] Infrared emitter/receiver implement `async_send_command` or `_handle_received_signal`, do not set the `device_class` themselves, do not change the base state, and consumers use helpers/consumer base classes instead of direct calls
- [ ] RF transmitter declares `supported_frequency_ranges`, implements `async_send_command`, does not change the base state; consumers use `radio_frequency.async_send_command` and `async_get_transmitters`
- [ ] For every set feature flag across all seven domains the corresponding `async_` method exists; no flags set "on spec"

## Open Questions

- **Infrared detail depth**: The infrared docs show base classes, helpers, and consumer base classes, but no `supported_features` enum and no quality-scale markers for this domain. Should IR consumer entities (button/event) additionally be referenced in `ha/entity-platforms-controls`, or does the IR abstraction stay fully here?
- **Radio-frequency modulation extension**: The docs currently support only `ModulationType.OOK` and announce further types. Should the spec prescribe a convention for how transmitters later declare additional modulations, or follow up once the docs show them?
- **Custom fan speeds (vacuum)**: `fan_speed_list` contains free strings. Should the spec prescribe a translation-key convention for fan-speed names (interface to `ha/translations`)?
- **Custom alarm codes**: `code_format` covers `NUMBER`/`TEXT`. Is that enough for all real panels, or is a convention needed for device-specific validation rules beyond the enum?
- **Calendar/to-do statistics**: Both domains derive their state from records (active event, count of open items). Should the spec clarify whether/how these states feed long-term statistics, or does that remain reserved for `ha/entity-platform-types`?
