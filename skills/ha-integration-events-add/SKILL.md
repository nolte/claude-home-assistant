---
name: ha-integration-events-add
description: Augment an existing Home Assistant Custom Integration with event firing and/or listening on the HA event bus, conforming to spec/ha/integration-events. For firing it generates hass.bus.async_fire("<domain>_event", event_data) with a domain-prefixed event type and a documented JSON-serializable data shape, placed in async_setup_entry (__init__.py) and never in entity logic. For listening it generates hass.bus.async_listen / async_listen_once, holds the returned unsubscribe callable, registers it via entry.async_on_unload (or tears it down in async_unload_entry), and decorates non-blocking listeners with @callback. Decides fire vs. listen vs. both with the user first and runs an event-vs-state check. Activate on "fire a custom event", "listen for an event", "feuere/lausche ein Integration-Event". Do not activate for registered services (ha-service-definition-generator), device triggers off events (ha-device-automation-add), greenfield scaffolding (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, events]
---

# HA Integration Events Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-integration-events-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-integration-events-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes an occurrence and reads back the `async_fire` call, the documented data shape, the listener wiring, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-device-automation-add`).
- **Mid-flow interactivity** — the fire-vs-listen-vs-both decision and the event-vs-state check are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — a bus-fire call plus a documented data shape, or a listener with its `async_on_unload` teardown, fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the direction decision and the event-vs-state advice belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add event **firing** and/or **listening** to an existing integration — firing a domain-prefixed custom event when a transient occurrence happens, or subscribing to a bus event with clean unsubscribe teardown.

## When NOT to activate

- a user-driven action with its own schema → `ha-service-definition-generator` / `ha/services`
- a device trigger built on top of a fired event → `ha-device-automation-add` / `ha/device-automations`
- greenfield integration scaffolding → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **Decide the direction first.** Resolve **fire vs. listen vs. both** with the user before generating anything.
2. **Read [`ha/integration-events`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/integration-events/de.md) first.** Do not generate from memory.
3. **Domain-prefixed firing.** Fire via `hass.bus.async_fire("<domain>_event", event_data)`; the event type **must** carry the domain prefix; `event_data` is a JSON-serializable dict. Never use unprefixed or generic event names.
4. **Firing lives in setup.** Place firing code in `async_setup_entry` (`__init__.py`), never in a platform's entity logic. For device-/service-related events add a `device_id` attribute from the device registry, and document the `event_data` shape (keys + types).
5. **Listen via the bus or a helper.** Use `hass.bus.async_listen` (until canceled) or `hass.bus.async_listen_once` (exactly once); prefer `async_listen_once` for one-shot lifecycle events (`EVENT_HOMEASSISTANT_START` / `_STARTED` / `_STOP`). Prefer an `homeassistant.helpers.event` helper when it covers the type; do not listen to core events like `EVENT_STATE_CHANGED` when a dedicated helper exists.
6. **Never drop the unsubscribe.** Hold the callable returned by `async_listen` / `async_listen_once` (or the helper) and register it via `entry.async_on_unload(unsub)` — or tear it down in `async_unload_entry` (see [`ha/setup-lifecycle`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/setup-lifecycle/de.md)). A discarded callable leaks beyond the reload and fires twice.
7. **`@callback` listeners.** Decorate non-blocking, loop-running listeners with `@callback` (`homeassistant.core.callback`); avoid blocking or I/O work inside them and offload follow-up work as a task (see [`ha/async-patterns`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/async-patterns/de.md)).
8. **Event, not state.** Fire transient occurrences as events; never let entity state represent a transient event (no "30-second-on" binary sensor). Point at an `event` entity ([`ha/entity-architecture`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-architecture/de.md)) when it models the occurrence more cleanly.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `direction` | yes | asked | `fire` / `listen` / `both` |
| `occurrence` | yes | — | the occurrence the event expresses, in prose |
| `event_type` | no | derived (`<domain>_event`) | the event type to fire / listen for |
| `event_data` shape | no | derived | keys + types of the data dict |
| `device_id` | no | asked when device-related | device registry identifier in the data |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Resolve `direction` (`fire` / `listen` / `both`) explicitly with the user.
3. Run the event-vs-state check; surface an `event` entity when it models the occurrence more cleanly before proceeding.
4. Read `ha/integration-events`.
5. The event type / listener is not already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the resolved `direction`, the event type (`<domain>_event`), the `event_data` shape, whether `device_id` is needed, and the event-vs-state outcome in one paragraph. Wait for confirmation.

### 2) Generate

| Direction | Where | Calls |
|---|---|---|
| fire | `async_setup_entry` (`__init__.py`) | `hass.bus.async_fire("<domain>_event", event_data)` with documented shape (+ `device_id` when device-related) |
| listen | `async_setup_entry` (`__init__.py`) | `hass.bus.async_listen` / `async_listen_once` → `@callback` listener; `entry.async_on_unload(unsub)` (or teardown in `async_unload_entry`) |
| both | both | the union of the above |

Prefer an `homeassistant.helpers.event` helper over a raw core-event listen when one covers the type.

### 3) Validate and report

Validate offline (fired events use `async_fire` with the domain prefix; device-related events carry `device_id`; the data shape is documented; firing lives in `async_setup_entry`; listeners use `async_listen` / `async_listen_once` or a helper; every unsubscribe callable is registered via `entry.async_on_unload(...)`; loop listeners are `@callback` with no blocking I/O; no entity state represents a transient event). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/integration-events` acceptance criteria, plus the changed file paths and the quality-scale marker (**Bronze**).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Registered services / user-driven actions → `ha-service-definition-generator` / `ha/services`
- Device triggers off events → `ha-device-automation-add` / `ha/device-automations`
- `@callback` mechanics / setup lifecycle → `ha/async-patterns` / `ha/setup-lifecycle`
- Greenfield scaffold → `ha-integration-scaffold`
- Deploy to live HA → out of scope
