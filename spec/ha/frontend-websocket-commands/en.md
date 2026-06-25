# HA Integration: Frontend WebSocket Commands

Status: draft

## Context

A Custom Integration may hold data it wants to make available to the frontend — the HA frontend communicates with the backend over the WebSocket API, and that API can be extended with **custom commands**. The standard example from the HA docs is the media player exposing album covers to the frontend; more generally: as soon as a card or panel needs integration-specific data that is not a state attribute, a custom WebSocket command is the right transport.

Per the HA docs a command consists of three parts: a message type, a message schema, and a message handler. The integration does **not** have to declare `websocket_api` as a manifest dependency — you register the command, and if the user is using the WebSocket API, the command becomes available. On the Python side the decorator `@websocket_api.websocket_command({...})` defines the type and data schema, the handler sends the result via `connection.send_result(msg["id"], result)` or an error via `connection.send_error(...)`, and `websocket_api.async_register_command(hass, ws_handler)` makes the command available. On the JavaScript side a card or panel calls the command through the `hass` object and awaits the result promise.

This spec lifts the HA-docs pattern into a generic obligation. The delimitation against services is owned by `ha/services` (services = user-driven actions/mutations; WebSocket commands = read/query transport into the frontend); the frontend consumer side (`callWS` call, response typing) is owned by `ha/frontend-data-api`; the card wiring is owned by `ha/lovelace-card-patterns`; the sync/async handler discipline (`@callback` vs. `async_response`) is owned by `ha/async-patterns`.

Quality scale marker: no direct quality-scale rule point — the HA docs do not place WebSocket commands in a quality-scale tier. The pattern does, however, border on `ha/diagnostics` (which integration data is exposed) and on data-exposure considerations: a command that delivers sensitive data **MUST** weigh the same access restriction as a diagnostics dump.

## Goals

- Transport integration-specific frontend data over a custom WebSocket command, rather than squeezing it into state attributes or services
- Define command type, schema, and handler per the HA-docs pattern at a clearly marked location and register it via `async_register_command`
- Choose sync vs. async handlers deliberately: `@callback` for pure in-memory responses, `@websocket_api.async_response` for I/O, device access, or computation
- Deliver results and errors via `connection.send_result` / `connection.send_error` with correct `msg["id"]` correlation
- Protect admin-only commands explicitly via `@websocket_api.require_admin`
- Call the command from the frontend through the `hass` object and await the result promise correctly

## Non-Goals

- User-driven actions / backend mutations — those are services; see `ha/services` (WebSocket commands are primarily read/query transport)
- The frontend consumer side in detail (TypeScript typing of the response, `callWS` error handling in the card) — owned by `ha/frontend-data-api`
- The card and panel wiring (rendering, editor, lifecycle) — owned by `ha/lovelace-card-patterns`
- The generic sync/async discipline in the event loop (blocking I/O, executor jobs) — owned by `ha/async-patterns`
- Access hardening beyond `require_admin` (token gating, path whitelist) — owned by `ha/security-hardening`

## Requirements

### Registering the command (Python, `async_register_command`)

- **MUST** register every custom command via `websocket_api.async_register_command(hass, ws_handler)` — without registration the command is not available to the WebSocket API
- **MUST** perform the registration inside the integration's setup method (for example `async_setup`), as in the HA-docs example — not scattered across platform modules
- **MUST** import `from homeassistant.components import websocket_api` and define the handler as a callback function that runs inside the event loop
- **MUST NOT** require `websocket_api` as a manifest dependency to register the command — per the HA docs this is not needed; the command becomes available if the user is using the WebSocket API

### Command schema & `type`

- **MUST** declare the type and data schema via the `@websocket_api.websocket_command({...})` decorator on the handler
- **MUST** namespace the message type as `vol.Required("type"): "<domain>/<name>"` — the docs-conformant shape is `"<domain>/<name>"` (for example `"camera/get_thumbnail"`)
- **MUST** declare input fields via `vol.Required(...)` and `vol.Optional(...)` with a type annotation in the schema (for example `vol.Optional("entity_id"): str`)
- **SHOULD** keep the schema minimal and include only the fields the handler actually reads

### Responses (`send_result`/`send_error`)

- **MUST** deliver a success result via `connection.send_result(msg["id"], result)` using the `msg["id"]` from the incoming message — the `msg["id"]` correlates request and response
- **MUST** report errors via `connection.send_error(msg["id"], "<error_code>", "<message>")` instead of letting an exception propagate out of the handler (docs example: `"entity_not_found"`, `"thumbnail_fetch_failed"`)
- **MUST** leave the handler (`return`) after every `send_error` path, so that no additional `send_result` is sent for the same `msg["id"]`
- **MUST NOT** substitute the `msg["id"]` with another value — without the correct ID the frontend cannot match the response to the call

### Sync vs. async (`@callback`/`async_response`)

- **MUST** declare a handler that only returns in-memory data (no network, device, or computation work) as a synchronous function with `@callback` — like the `ws_get_panels` example in the HA docs
- **MUST** write a handler that interacts with the network or a device or needs to compute information as `async def` and decorate it with `@websocket_api.async_response` — per the HA docs this is the way to queue work and send a delayed response
- **MUST NOT** run blocking I/O in a `@callback` handler — such work belongs in a `@websocket_api.async_response` handler

### Admin restriction (`require_admin`)

- **MUST** decorate commands that only administrators may run with `@websocket_api.require_admin`
- **SHOULD** consider `require_admin` for every command that delivers sensitive or integration-internal data — the default is "do not expose unless necessary"
- **MUST NOT** hand-roll admin checks in the handler body when `@websocket_api.require_admin` serves the purpose

### Calling from the frontend (`hass.callWS`)

- **MUST** call the command from the frontend through the `hass` object that holds the WebSocket connection to the backend — `await hass.callWS({ type: "<domain>/<name>", ... })`
- **MUST** use the same `type` string and field names in the `callWS` call that the Python schema declares
- **MUST** await the promise returned by `callWS` and process the result — a card or panel consumes the command to load integration-specific data
- **SHOULD** choose a custom WebSocket command (instead of a service) when the goal is to fetch integration-specific data into a card; a service is the choice for user-driven actions/mutations

## Acceptance Criteria

- [ ] Every command is registered via `websocket_api.async_register_command(hass, ws_handler)` in the setup method
- [ ] Type and schema are declared via `@websocket_api.websocket_command({...})`; `type` is namespaced as `"<domain>/<name>"`
- [ ] Input fields use `vol.Required`/`vol.Optional` with type annotation
- [ ] Success is delivered via `connection.send_result(msg["id"], result)` with the correct `msg["id"]`
- [ ] Errors are reported via `connection.send_error(msg["id"], code, message)`, followed by `return`
- [ ] In-memory handlers use `@callback`; I/O / device / computation handlers use `@websocket_api.async_response` with `async def`
- [ ] Admin-only commands are decorated with `@websocket_api.require_admin`
- [ ] The frontend call uses `hass.callWS({ type: "<domain>/<name>", ... })` with the same `type` and field names as the Python schema and awaits the result
- [ ] The command-vs-service choice is justified: data fetch into the frontend → command, action/mutation → service (`ha/services`)

## Open Questions

- **Schema validation errors**: The HA docs show domain errors via `send_error` but say nothing about schema validation errors (invalid payload). Should the spec prescribe a standard error code for schema violations?
- **Subscription commands**: Some WebSocket commands are long-lived subscriptions (a stream of events), not one-shot requests. The docs examples are request/response. Should the spec address subscription commands as a separate subclass?
- **`callWS` vs. `sendMessagePromise`**: The HA docs show the frontend call via `hass.connection.sendMessagePromise`; the more common high-level API is `hass.callWS`. Should the spec mandate `callWS` exclusively and name `sendMessagePromise` only as a low-level fallback?
- **Data-exposure threshold**: At which point does `@require_admin` become mandatory rather than SHOULD? Currently formulated as a consideration — a concrete threshold (for example "delivers personal or backend-internal data") would make skill output deterministic.
- **Versioning of the `type`**: When a command's response schema changes, there is no versioning mechanism in the `type` string. Should the spec prescribe a convention (`"<domain>/<name>/v2"`)?
