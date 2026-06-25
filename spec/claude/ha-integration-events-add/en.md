# Skill: `ha-integration-events-add`

Status: draft

## Context

`ha/integration-events` defines how a Custom Integration participates through the HA event bus (`hass.bus`): **fire** its own events (`hass.bus.async_fire("<domain>_event", event_data)`) and **listen** for events (`hass.bus.async_listen` until canceled / `hass.bus.async_listen_once` exactly once). The spec carries two non-obvious guardrails: (1) **event naming** — custom events must carry the integration domain as a prefix (`<domain>_event`), so the global bus stays collision-free; (2) **event vs. state** — event code does not belong in entity logic, and entity state must not represent transient events. When listening, the bus and the event helpers return an unsubscribe callable that **must** be registered via `entry.async_on_unload(...)`, otherwise the listener leaks beyond the config entry reload. The quality-scale marker is **Bronze**. No skill augments this so far.

This skill augments event firing and/or listening into an **existing** integration: bus firing with a documented event type (`<domain>_event`) and data shape, listener registration via `async_listen` / `async_listen_once`, holding and tearing down the unsubscribe callable via `entry.async_on_unload`, and the `@callback` decoration of non-blocking listeners — conformant to `ha/integration-events`. Before generating it decides **fire vs. listen vs. both** explicitly with the user.

## Scope

Augmenting event firing and/or listening into an existing `custom_components/<domain>/` integration: the `async_fire` firing with a domain-prefixed event type and a documented `event_data` shape (in `__init__.py` setup, not in entity logic), listener registration via `async_listen` / `async_listen_once`, holding the unsubscribe callable and registering it via `entry.async_on_unload(...)` (or teardown in `async_unload_entry`), and the `@callback` decoration. The skill reads `ha/integration-events` and validates.

## Goals

- Choose the direction explicitly with the user — **fire**, **listen**, or **both** — before anything is generated
- When firing, prefix the event type with the integration domain (`<domain>_event`) and document a JSON-serializable `event_data` shape and keep it stable
- Place the firing in `async_setup_entry` (`__init__.py`) and never couple it into a platform's entity logic
- When listening, use exclusively `async_listen` / `async_listen_once` (or an event helper) and register the returned unsubscribe callable via `entry.async_on_unload(...)`
- Decorate non-blocking listeners with `@callback` and offload blocking follow-up work as a task
- Hold the separation between event (transient occurrence) and state (durable condition) consistently

## Non-Goals

- User-driven actions (service calls from frontend, automation, script) — `ha-service-definition-generator` / `ha/services`
- Device triggers built on top of a fired event — `ha-device-automation-add` / `ha/device-automations`
- `@callback` mechanics and loop-vs-executor rules in detail — `ha/async-patterns`
- The `async_on_unload` teardown pattern and the setup lifecycle as a whole — `ha/setup-lifecycle`
- Entity modeling and the question of when an event is exposed as an `event` entity — `ha/entity-architecture`
- Greenfield scaffolding of an integration — `ha-integration-scaffold`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "fire a custom event", "listen for an event", "emit an event when … happens"
  - "subscribe to the HA stop event", "react to a state change via the bus"
  - "feuere/lausche ein Integration-Event", "feuere ein eigenes Event", "lausche auf ein Event"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the direction (`fire` / `listen` / `both`) plus the occurrence (prose), from which the skill derives the event type and data shape
- **MAY** capture: the `event_data` shape (keys + types), whether a `device_id` attribute is needed, and for listeners the event type plus whether `async_listen_once` (one-shot lifecycle events) fits

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** clarify the direction explicitly with the user — **fire vs. listen vs. both**; do not generate without this decision
- **MUST** run the event-vs-state check: fire transient occurrences as an event, do not model them as durable entity state; **SHOULD** point at an `event` entity when it models the occurrence more cleanly (`ha/entity-architecture`)
- **MUST** read the `ha/integration-events` spec
- **MUST NOT** overwrite an existing event type or listener; on collision abort

### Generation rules (from `ha/integration-events`)

- **MUST** when firing use `hass.bus.async_fire("<domain>_event", event_data)` — the event type must carry the domain prefix (canonical `<domain>_event`)
- **MUST** pass `event_data` as a JSON-serializable dictionary (numbers, strings, lists, nested dicts) — no non-serializable objects
- **MUST** place the firing code in `async_setup_entry` (`__init__.py`), not in a platform's entity logic
- **MUST** for device-/service-related events add a `device_id` attribute carrying the device registry identifier to the event data
- **SHOULD** document the `event_data` shape (keys with types) and keep it stable, so device triggers and automations can reliably build on it
- **MUST** when listening use `hass.bus.async_listen(event_type, callback)` (until canceled) or `hass.bus.async_listen_once(event_type, callback)` (exactly once); for one-shot lifecycle events (`EVENT_HOMEASSISTANT_START` / `_STARTED` / `_STOP`) `async_listen_once` **SHOULD** be used
- **SHOULD** prefer an existing helper from `homeassistant.helpers.event` when it covers the needed event type; **MUST NOT** listen directly to core events such as `EVENT_STATE_CHANGED` when a dedicated helper exists
- **MUST** hold the unsubscribe callable returned by `async_listen` / `async_listen_once` (or the helper) and register it via `entry.async_on_unload(unsub)` — or tear it down in `async_unload_entry`; a discarded callable leaks beyond the reload and fires twice
- **MUST** decorate non-blocking, loop-running listeners with `@callback` (`homeassistant.core.callback`) and avoid any blocking or I/O-bound work inside them; **SHOULD** offload blocking follow-up work as a task (`hass.async_create_task(...)`) — details in `ha/async-patterns`
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: fired events use `async_fire` with the domain prefix; device-related events carry `device_id`; the `event_data` shape is documented; firing code lives in `async_setup_entry`; listeners use `async_listen` / `async_listen_once` (or a helper); every unsubscribe callable is registered via `entry.async_on_unload(...)`; loop listeners are `@callback` with no blocking I/O; no entity state represents a transient event
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/integration-events`, plus the changed file paths and the quality-scale marker (**Bronze**)

### Prohibitions

- **MUST NOT** use unprefixed or generic event names that may collide with core or third-party integration events
- **MUST NOT** discard or leave an unsubscribe callable unused
- **MUST NOT** let entity state represent a transient event (no "30-second-on" binary sensor)
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill clarifies the direction explicitly (fire / listen / both) and runs the event-vs-state check
- [ ] Fired events use `hass.bus.async_fire("<domain>_event", event_data)` with the domain prefix
- [ ] Device-related events carry a `device_id` attribute from the device registry; the `event_data` shape is documented
- [ ] Firing code lives in `async_setup_entry` (`__init__.py`), not in a platform's entity logic
- [ ] Listeners are registered via `async_listen` / `async_listen_once` (or an event helper)
- [ ] Every returned unsubscribe callable is registered via `entry.async_on_unload(...)` / torn down in `async_unload_entry`
- [ ] Loop listeners are decorated with `@callback` and contain no blocking I/O
- [ ] No entity state represents a transient event
- [ ] Report names the file paths and the quality-scale marker **Bronze**

## Open questions

- **`event` entity instead of bus fire**: The docs recommend `event` entities as the preferred representation over raw bus firing. Should the skill allow bus firing only as an exception and point at `event` entities? Currently it points and fires on the user's decision.
- **`device_id` mandatory threshold**: From when is the `device_id` attribute mandatory — for every device-related event or only when a device trigger exists? Currently case-by-case.
- **Unsubscribe without config entry**: `async_on_unload` presupposes a config entry. How does the skill handle listener cleanup for YAML-only or setup-phase listeners with no entry? Currently outside the standard path.
