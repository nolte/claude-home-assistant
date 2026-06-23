# HA Integration: Services

Status: draft

## Context

A Custom Integration can offer user-driven actions through **HA services** — the user clicks a button in the frontend, an automation triggers an action call, or a script invokes the service directly. Services are declared through two artefacts: `services.yaml` (the UI schema with selectors that HA renders) and an async handler registered via `hass.services.async_register(DOMAIN, "<service>", handler, schema=...)` (or the more modern `hass.services.async_register` with voluptuous schema validation).

`nolte/kamerplanter-ha` validates this pattern with five services (`refresh_data`, `clear_cache`, `fill_tank`, `water_channel`, `confirm_care`) and codifies three non-obvious refinements: (1) **multi-instance disambiguation** — when multiple config entries are running and the user calls the service without `entity_id`, the handler must figure out which entry was meant or abort with a clear error; (2) **selector discipline** — `entity:` with `integration:` filter instead of free entity strings, `select:` with `options:` list instead of free strings, `number:` with `min`/`max`/`step`; (3) **idempotency guards** — the same service call must not produce two identical backend mutations when HA repeats the call.

This spec lifts that convention into a generic obligation. Service security (path whitelisting, token gating) belongs in `ha/security-hardening`; translations for service names and field labels belong in `ha/translations`; icons for services belong in `ha/icons`.

Quality scale marker: **Silver** (services with schema validation and selectors are a Silver requirement; idempotency and multi-instance safety are refinements beyond Silver but expected portfolio-wide).

## Goals

- Make `services.yaml` the only source of UI rendering — no service definition without YAML schema
- Consolidate handler implementation in a clearly marked location (`__init__.py` or `services.py`), rather than scattering it across platform modules
- Use selectors instead of free string fields as the default — the HA UI gets typesafe pickers; the handler gets validated input
- Solve multi-instance disambiguation explicitly, so users with multiple config entries of the same integration don't run into silent misresolutions
- Make idempotency guards the default for mutating services, so duplicate HA calls don't lead to duplicate backend mutations
- Keep clear separation between `ServiceValidationError` (user error, render in frontend) and `HomeAssistantError` (internal error, log)

## Non-Goals

- Security hardening of service inputs (path validation, API key gating, bearer token whitelist) — separate `ha/security-hardening` spec
- Service translations (`services.<name>.name`, `services.<name>.fields.<field>.name`) — owned by `ha/translations`
- Service icons (`icons.json:services.<name>.service`) — owned by `ha/icons`
- Asynchronous background jobs / long-running tasks — services should feel short and synchronous; background work is the coordinator's job, not the service's
- HA action triggers (`event:<service>_<event>`) for reverse notification — separate follow-up spec once the first integration needs it

## Requirements

### `services.yaml`

- **MUST** carry an entry in `services.yaml` for every registered service — without an entry the HA UI does not render the service form
- **MUST** declare at least a `target:` block or a `fields:` map per service entry; a service without input is syntactically allowed, but most services have at least one field
- **MUST** declare fields via typed selectors (`selector: { entity: { ... } }`, `selector: { select: { ... } }`, `selector: { number: { ... } }`, `selector: { text: ... }`, `selector: { boolean: ... }`)
- **MUST NOT** declare free string fields without `selector:` when a matching selector exists — the HA UI then renders a generic text field, lowering input quality

### Selectors

- **MUST** use the `entity:` selector for `entity_id` fields, with `integration: <DOMAIN>` as a filter — the user only sees entities from the same integration
- **MUST** use the `select:` selector with an `options:` list for selection fields with a fixed option set, where each option element carries `label`/`value`; free enum strings without a list are not allowed
- **MUST** use the `number:` selector with `min`, `max`, and `step` for numeric fields — protection against typos and inputs outside the sensible range
- **SHOULD** also set `unit_of_measurement` for volume, time, and energy fields, so the UI shows the unit
- **MAY** use the `target:` block instead of an `entity:` field when the service supports multiple targets (entities, devices, areas) — that is HA-conformant and allows bulk calls

### Handler placement

- **MUST** keep all service handlers at exactly one place in the code — either in `__init__.py` (small, up to ~5 services) or in a dedicated `services.py` module
- **MUST** register service handlers inside `async_setup_entry` (or a dedicated setup hook): `hass.services.async_register(DOMAIN, "<service>", handler, schema=<SCHEMA>)`
- **SHOULD** declare service schemas with `voluptuous` and pass the `schema=` option to `async_register` — HA then validates the input before the handler call
- **MUST NOT** register service handlers in platform modules (`sensor.py`, `binary_sensor.py`) — service registry is global, platforms are per-platform setup

### Multi-instance disambiguation

- **MUST** resolve the config entry via the entity registry for services that take `entity_id` (or `target:` entities), rather than guessing through global `hass.data` / `runtime_data` lookups
- **MUST** derive the config entry from an **explicit** parameter (`entry_id` as an additional field) for services that allow a backend resource key instead of `entity_id` (for example `tank_key="xy"`), **or** resolve the service successfully only when exactly one config entry exists
- **MUST** raise a `ServiceValidationError` with a clear message (`"Multiple config entries — please specify entry_id"`) for non-disambiguated calls when multiple config entries exist — never silently fall back to the first entry
- **SHOULD** bundle disambiguation logic in a helper (`_resolve_entry(hass, call) -> ConfigEntry`), so every service handler uses the same resolver
- **MUST NOT** rely on globals or module-level caches that span `async_setup_entry` invocations to guess the entry

### Idempotency guards

- **MUST** for services that trigger **mutating** backend calls (for example `fill_tank`, `water_channel`, `confirm_care`) cache the mutation result locally after the call or hold a backend acknowledgement ID
- **SHOULD** detect duplicate calls when the backend accepts an idempotency key or request ID — derive the key deterministically from the inputs (for example a hash over `entity_id + payload + timestamp_within_window`)
- **MUST NOT** silently execute duplicate calls twice when the backend offers no idempotency protection — in that case warn the user with a clear error message or de-duplicate the call within a short window

### Error handling

- **MUST** raise user errors (invalid input, validation failure, missing disambiguation) as `homeassistant.exceptions.ServiceValidationError` — HA renders them in the frontend as a red error message
- **MUST** raise internal errors (dead backend connection, handler bug, unexpected exception) as `homeassistant.exceptions.HomeAssistantError` — these land in the HA log with stack trace
- **MUST** not dump API auth errors inside a service handler into the HA service-error log; convert them into `ServiceValidationError("invalid_auth")` — the user sees a meaningful message; the coordinator triggers the reauth flow on the next regular tick
- **MUST NOT** use generic `Exception` catches in the handler — only catch specifically known errors; everything else propagates

### Coordinator refresh after mutation

- **SHOULD** kick off `await coordinator.async_request_refresh()` for the corresponding coordinator after every mutating service call, so the entities reflect the new backend state
- **MUST NOT** call `coordinator.async_refresh()` (synchronous-blocking) from a service handler — `async_request_refresh()` is the correct variant; it debounces and does not block the handler

## Acceptance Criteria

- [ ] `services.yaml` carries an entry with `description`, `fields:` (or `target:`) for every registered service
- [ ] Every `fields:` entry uses typed selectors (`entity`, `select`, `number`, `text`, `boolean`)
- [ ] `entity:` selectors filter on `integration: <DOMAIN>`
- [ ] Service handlers are registered at exactly one place (`__init__.py` or `services.py`)
- [ ] Service schemas are declared with `voluptuous` and passed to `async_register(..., schema=...)`
- [ ] When multiple config entries exist: a central `_resolve_entry(hass, call)` helper aborts with `ServiceValidationError` when the entry cannot be uniquely resolved
- [ ] Mutating services call `await coordinator.async_request_refresh()` at the end
- [ ] User errors are raised as `ServiceValidationError`; internal errors as `HomeAssistantError`
- [ ] Auth errors inside the handler are translated into `ServiceValidationError("invalid_auth")`, not raw-propagated
- [ ] Quality scale marker: **Silver**

## Open Questions

- **`hass.services.async_register` vs. modern decorator API**: HA has experimental decorator-based service registration. Should the spec stick with the classic call or allow the modern decorator once stable?
- **Default idempotency window**: Which window applies for de-duplication (5 s, 30 s, none)? Currently formulated as "short" — a concrete value would make skill output deterministic.
- **Multi-target services**: The `target:` block allows entity, device, and area targets. Should the spec require the resolver helper for all three target types, or does it stay entity-centric?
- **`response` field**: HA supports service responses since 2024.x (`return_response`). Should the spec explicitly address response-capable services — when SHOULD a service return a response?
- **Service security threshold**: At which service class does `ha/security-hardening` become mandatory? Currently a cross-reference to a follow-up spec; a concrete threshold (for example "services that mutate backend state") is missing here.
