# Skill: `ha-websocket-command-add`

Status: draft

## Context

`ha/frontend-websocket-commands` defines how a Custom Integration extends the WebSocket API with a **custom command** — the backend endpoint a card or panel calls to load integration-specific data that is not a state attribute. Per the HA docs a command consists of three parts: a message type, a message schema, and a message handler. On the Python side `@websocket_api.websocket_command({...})` declares the type and data schema, the handler sends the result via `connection.send_result(msg["id"], result)` or an error via `connection.send_error(...)`, and `websocket_api.async_register_command(hass, ws_handler)` makes the command available. No skill augments this so far.

This skill augments **one** WebSocket command into an **existing** integration: the decorated handler, its voluptuous schema with a `"<domain>/<name>"` type, the correct sync/async choice (`@callback` vs. `@websocket_api.async_response`), the `send_result`/`send_error` delivery with correct `msg["id"]` correlation, optional `@websocket_api.require_admin`, and the `async_register_command` wiring in the setup method — conformant to `ha/frontend-websocket-commands`. Before generating it checks whether the data is read into the frontend (command) or an action/mutation is triggered (service).

## Scope

Augmenting exactly one WebSocket command per run into an existing `custom_components/<domain>/` integration: the handler decorated with `@websocket_api.websocket_command({...})`, the voluptuous schema with `vol.Required("type"): "<domain>/<name>"`, the sync/async shape with `@callback` or `@websocket_api.async_response`, the `connection.send_result` / `connection.send_error` paths, optional `@websocket_api.require_admin`, and the `async_register_command(hass, ws_handler)` call in the setup method (for example `async_setup`). The skill reads `ha/frontend-websocket-commands` and validates offline. The frontend consumer side is sketched at most as a `callWS` call example, not built out in detail.

## Goals

- Derive a spec-conformant WebSocket command from a described data need of a card/panel and augment it
- Enforce the three-part contract: message type as `"<domain>/<name>"`, voluptuous schema with `vol.Required`/`vol.Optional` and a type annotation, handler with signature `(hass, connection, msg)`
- Choose sync vs. async deliberately: `@callback` for pure in-memory responses, `@websocket_api.async_response` with `async def` for I/O, device access, or computation
- Deliver results and errors via `connection.send_result(msg["id"], result)` / `connection.send_error(msg["id"], code, message)` with correct `msg["id"]` correlation and return after every `send_error`
- Protect admin-only or sensitive commands via `@websocket_api.require_admin`
- Register the command via `async_register_command(hass, ws_handler)` in the setup method — not scattered across platform modules

## Non-Goals

- User-driven actions / backend mutations with their own schema — those are services; `ha-service-definition-generator` / `ha/services`
- The frontend consumer side in detail (TypeScript typing of the response, `callWS` error handling in the card) — `ha/frontend-data-api`
- A custom panel that consumes the command — `ha-panel-add`
- The generic sync/async discipline in the event loop (blocking I/O, executor jobs) — `ha/async-patterns`
- Access hardening beyond `require_admin` (token gating, path whitelist) — `ha/security-hardening`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a websocket command", "expose a backend endpoint to my card", "register a custom ws command"
  - "let my card fetch integration data from the backend"
  - "füge ein WebSocket-Command hinzu", "registriere einen eigenen WS-Command"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the data need (prose), from which the skill derives the type name, schema fields, and handler logic
- **MAY** capture: the `"<domain>/<name>"` type, the schema fields (`vol.Required`/`vol.Optional`), whether the handler does I/O (sync/async choice), and whether `require_admin` is needed

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** settle the command-vs-service choice: if the goal is a data fetch into the frontend, a command is correct; if it is a user-driven action/mutation, the skill **MUST** point at `ha-service-definition-generator` and abort
- **MUST** read the `ha/frontend-websocket-commands` spec
- **MUST NOT** overwrite an existing command type; on collision abort

### Generation rules (from `ha/frontend-websocket-commands`)

- **MUST** import `from homeassistant.components import websocket_api` and define the handler with signature `(hass, connection, msg)`
- **MUST** declare the type and data schema via `@websocket_api.websocket_command({...})` on the handler; the message type is namespaced as `vol.Required("type"): "<domain>/<name>"` (docs example: `"camera/get_thumbnail"`)
- **MUST** declare input fields via `vol.Required(...)` and `vol.Optional(...)` with a type annotation and keep the schema minimal (only fields the handler reads)
- **MUST** declare a pure in-memory handler synchronously with `@callback`; write a handler with network, device, or computation work as `async def` and decorate it with `@websocket_api.async_response`
- **MUST NOT** run blocking I/O in a `@callback` handler — such work belongs in a `@websocket_api.async_response` handler
- **MUST** deliver a success result via `connection.send_result(msg["id"], result)` using the incoming `msg["id"]` and report errors via `connection.send_error(msg["id"], "<error_code>", "<message>")` instead of letting an exception propagate; after every `send_error` path the handler **MUST** return (`return`)
- **MUST NOT** substitute the `msg["id"]` with another value — without the correct ID the frontend cannot match the response
- **MUST** decorate admin-only commands with `@websocket_api.require_admin` and **MUST NOT** hand-roll admin checks in the handler body; for sensitive or integration-internal data `require_admin` **SHOULD** be considered
- **MUST** register the command via `websocket_api.async_register_command(hass, ws_handler)` in the integration's setup method (for example `async_setup`) — not scattered across platform modules
- **MUST NOT** require `websocket_api` as a manifest dependency to register the command
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: the handler carries `@websocket_api.websocket_command({...})`; the `type` is namespaced as `"<domain>/<name>"`; input fields use `vol.Required`/`vol.Optional` with a type annotation; the sync/async choice matches the work (`@callback` vs. `@websocket_api.async_response`); success goes via `send_result(msg["id"], ...)`, errors via `send_error(msg["id"], ...)` followed by `return`; `require_admin` is set where needed; `async_register_command` lives in the setup method
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/frontend-websocket-commands`, plus the changed file paths and the justified command-vs-service choice

### Prohibitions

- **MUST NOT** augment more than one command per run
- **MUST NOT** generate a command for a user-driven action/mutation — that is a service
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill runs the command-vs-service choice and aborts on action/mutation in favour of `ha-service-definition-generator`
- [ ] The handler carries `@websocket_api.websocket_command({...})`; the `type` is namespaced as `"<domain>/<name>"`
- [ ] Input fields use `vol.Required`/`vol.Optional` with a type annotation and the schema is minimal
- [ ] The sync/async shape matches the work: `@callback` for in-memory, `@websocket_api.async_response` with `async def` for I/O/device/computation
- [ ] Success goes via `connection.send_result(msg["id"], result)`, errors via `connection.send_error(msg["id"], code, message)` followed by `return`; the `msg["id"]` stays unchanged
- [ ] Admin-only commands are decorated with `@websocket_api.require_admin`
- [ ] The command is registered via `websocket_api.async_register_command(hass, ws_handler)` in the setup method (no manifest dependency)
- [ ] Report names the file paths and justifies the command-vs-service choice

## Open questions

- **Schema validation errors**: `ha/frontend-websocket-commands` leaves open which error code applies to an invalid payload. Until that is settled the skill emits only domain `send_error` codes from the docs pattern and asks when in doubt.
- **Subscription commands**: The docs examples are request/response; long-lived subscriptions are an open question in the spec. The skill generates only one-shot requests for now.
- **Data-exposure threshold**: At which point `@require_admin` becomes mandatory rather than SHOULD is left open by the spec; the skill considers it for sensitive data and asks.
