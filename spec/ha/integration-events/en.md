# HA Integration: Events (Firing and Listening)

Status: draft

## Context

The core of Home Assistant is driven by events — whoever wants to react to something reacts to events. A Custom Integration can do two things through the **HA event bus** (`hass.bus`): **fire** its own events (for example "motion detected", "button pushed") and **listen** for events (for example HA's lifecycle stop, an entity state change). The event bus accepts any event type as a string and any JSON-serializable event data as a dictionary.

This spec lifts the HA developer docs (`integration_events`, `integration_listen_events`, `dev_101_events`) into a generic obligation for portfolio integrations. The docs carry two non-obvious guardrails that become central here: (1) **event naming** — custom events must carry the integration domain as a prefix (`<domain>_event`), so the global bus stays collision-free; (2) **event vs. state** — event code does not belong in entity logic, and entity state must not represent events (no binary sensor that is `on` for 30 seconds when an event happens).

When listening, both the event helpers (`homeassistant.helpers.event`) and direct bus access (`async_listen`, `async_listen_once`) return a callable that cancels the listener. This unsubscribe callable must be registered via `entry.async_on_unload(...)` for clean teardown — otherwise the listener leaks beyond the config entry reload. `@callback` semantics (non-blocking, runs in the event loop) belong to `ha/async-patterns`; the `async_on_unload` cleanup pattern to `ha/setup-lifecycle`; the delimitation against user-driven actions to `ha/services`; entity modeling to `ha/entity-architecture`.

Quality scale marker: **Bronze** (correct event naming, clean listener teardown, and the event-vs-state separation are fundamental correctness requirements).

## Goals

- Fire the integration's own events via `hass.bus.async_fire(event_type, event_data)`, rather than coupling events to entity logic
- Prefix event types with the integration domain (`<domain>_event`), so the global bus stays collision-free
- Document and keep the `event_data` shape stable, so device triggers and automations can reliably build on it
- Listen for events exclusively via `async_listen` / `async_listen_once` (or the preferred event helpers) and register the returned unsubscribe callable via `entry.async_on_unload(...)`
- Implement listeners as `@callback`, so they do not block and run in the event loop
- Hold the separation between event (transient occurrence) and state (durable condition) consistently

## Non-Goals

- User-driven actions (service calls from frontend, automation, script) — separate `ha/services` spec
- `@callback` mechanics and loop-vs-executor rules in detail — owned by `ha/async-patterns`
- The `async_on_unload` teardown pattern and the setup lifecycle as a whole — owned by `ha/setup-lifecycle`
- Entity modeling and the question of when an event is exposed as an `event` entity — owned by `ha/entity-architecture`
- Database persistence of events (recorder schema, `data.home-assistant.io`) — outside the integration scope

## Requirements

### Firing events

- **MUST** fire the integration's own events through the event bus: `hass.bus.async_fire("<domain>_event", event_data)` — the bus is reachable via `hass.bus` on the HA instance
- **MUST** pass event data as a JSON-serializable dictionary (numbers, strings, lists, nested dicts) — non-serializable objects are not allowed
- **SHOULD** fire the bus directly only when no matching helper or `event` entity already models the occurrence more cleanly — the docs recommend `event` entities as the preferred representation
- **MUST NOT** put event code into the entity logic of a platform — translating integration events into HA events belongs in `async_setup_entry` inside `__init__.py`

### Event naming & data shape

- **MUST** prefix event types with the integration domain — the canonical format is `<domain>_event` (example: ZHA fires `zha_event`)
- **MUST** correctly attribute device-/service-related events by adding a `device_id` attribute carrying the device registry identifier to the event data
- **SHOULD** document the `event_data` shape (which keys with which types) and keep it stable, so device triggers and automations can reliably build on it
- **MAY** attach a device trigger to the event (based on the payload), so users can see all available events of the device and use them in automations
- **MUST NOT** use unprefixed or generic event names that may collide with core or third-party integration events

### Listening for events (`async_listen`)

- **MUST** listen for events via `hass.bus.async_listen(event_type, callback)` (until canceled) or `hass.bus.async_listen_once(event_type, callback)` (exactly once)
- **SHOULD** prefer an existing event helper from `homeassistant.helpers.event` when it already covers the needed event type (for example state-change tracking, time tracking) — the helpers are highly optimized and minimize the number of callbacks
- **SHOULD** use `async_listen_once` for lifecycle events that fire only once per run (`EVENT_HOMEASSISTANT_START`, `EVENT_HOMEASSISTANT_STARTED`, `EVENT_HOMEASSISTANT_STOP`)
- **MUST NOT** listen directly to core events such as `EVENT_STATE_CHANGED` or `EVENT_ENTITY_REGISTRY_UPDATED` when a dedicated helper exists — the helper is the preferred variant

### Unsubscribe & cleanup

- **MUST** hold the unsubscribe callable returned by `async_listen` / `async_listen_once` (and by the event helpers) — both return a callable that cancels the listener
- **MUST** register that unsubscribe callable via `entry.async_on_unload(unsub)`, so HA automatically cancels the listener on config entry unload/reload (see `ha/setup-lifecycle`)
- **MUST NOT** discard or leave an unsubscribe callable unused — an uncanceled listener leaks beyond the reload and fires twice

### Callback semantics

- **MUST** decorate listener functions with `@callback` (`homeassistant.core.callback`) when they are non-blocking and run entirely in the event loop — see `ha/async-patterns`
- **MUST** avoid any blocking or I/O-bound work inside a `@callback` listener — the callback runs directly in the loop and must not stall it
- **SHOULD** offload blocking follow-up work out of the callback as a task (`hass.async_create_task(...)`), rather than running it in the callback itself — details in `ha/async-patterns`

### Event vs. state

- **MUST** fire transient occurrences (motion detected, button pushed) as an event and not model them as durable entity state
- **MUST NOT** let entity state represent events — for example, no binary sensor that is `on` for 30 seconds just because an event happened
- **SHOULD** manually register a device/service that only fires events in the device registry, so the events are correctly attributed to a device

## Acceptance Criteria

- [ ] The integration's own events are fired via `hass.bus.async_fire("<domain>_event", event_data)`, with domain prefix
- [ ] Device-related events carry a `device_id` attribute from the device registry
- [ ] The `event_data` shape is documented (keys + types)
- [ ] Event-firing code lives in `async_setup_entry` (`__init__.py`), not in a platform's entity logic
- [ ] Listeners are registered via `async_listen` / `async_listen_once` (or an event helper)
- [ ] Every returned unsubscribe callable is registered via `entry.async_on_unload(...)`
- [ ] Listener functions that run in the loop are decorated with `@callback` and contain no blocking I/O
- [ ] No entity state represents a transient event (no "30-second-on" binary sensor)
- [ ] Quality scale marker: **Bronze**

## Open Questions

- **`event` entity instead of bus fire**: The docs recommend `event` entities as the preferred representation over raw bus firing. Should the spec allow bus firing only as an exception and make `event` entities the default requirement — and where is the line drawn?
- **`device_id` mandatory threshold**: From when is the `device_id` attribute mandatory — for every device-related event or only when a device trigger exists?
- **Sync vs. async listen**: The docs list `listen`/`listen_once` (sync) alongside `async_listen`/`async_listen_once`. Should the spec forbid sync variants generally, or are there sync contexts (`setup`) where they stay allowed?
- **Event helper catalog**: The docs carry a large helper catalog (state, template, time, sun tracking). Should the spec prescribe individual helpers by name as preferred, or stay generic at "use the helper when available"?
- **Unsubscribe without config entry**: `async_on_unload` presupposes a config entry. How is listener cleanup handled for YAML-only or setup-phase listeners that have no entry?
