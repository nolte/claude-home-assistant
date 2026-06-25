---
name: ha-websocket-command-add
description: Augment an existing Home Assistant Custom Integration with one custom WebSocket API command — the backend endpoint a frontend card or panel calls — conforming to spec/ha/frontend-websocket-commands. Creates the handler with signature (hass, connection, msg) decorated with @websocket_api.websocket_command({...vol schema...}) and either @callback (in-memory) or @websocket_api.async_response (I/O/device/computation), a "<domain>/<name>" namespaced type, vol.Required/vol.Optional input fields, connection.send_result / send_error delivery with correct msg["id"] correlation, optional @websocket_api.require_admin, and the async_register_command wiring in async_setup. Runs a command-vs-service check first. Activate on "add a websocket command", "expose a backend endpoint to my card", "register a custom ws command", "füge ein WebSocket-Command hinzu". Do not activate for user-driven actions/mutations (ha-service-definition-generator), the frontend consumer side (ha/frontend-data-api), a custom panel (ha-panel-add), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, frontend, websocket]
---

# HA WebSocket Command Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-websocket-command-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-websocket-command-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the data a card needs and reads back the handler, the schema, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-repairs-add`).
- **Mid-flow interactivity** — the command-vs-service decision and the sync-vs-async choice are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — one decorated handler plus its schema and the `async_register_command` call fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the command-vs-service and admin-exposure decisions belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** custom WebSocket API command to an existing integration — the backend endpoint a card or panel calls via `hass.callWS(...)` to load integration-specific data that is not a state attribute.

## When NOT to activate

- a user-driven action / backend mutation with its own schema → `ha-service-definition-generator` / `ha/services`
- the frontend consumer side (TypeScript typing, `callWS` error handling in the card) → `ha/frontend-data-api`
- a custom panel that consumes the command → `ha-panel-add`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One command, one run.** No multi-command batches.
2. **Read [`ha/frontend-websocket-commands`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/frontend-websocket-commands/de.md) first.** Do not generate from memory.
3. **Command vs. service.** Run the choice first: a data fetch into the frontend is a command; a user-driven action/mutation is a service. On action/mutation, point at `ha-service-definition-generator` and abort.
4. **Three-part contract.** Declare type and schema via `@websocket_api.websocket_command({...})` on a handler with signature `(hass, connection, msg)`; namespace the type as `vol.Required("type"): "<domain>/<name>"` (docs example: `"camera/get_thumbnail"`); declare input fields via `vol.Required`/`vol.Optional` with a type annotation, kept minimal.
5. **Sync vs. async.** A pure in-memory handler is a synchronous function with `@callback`; a handler doing network/device/computation work is `async def` decorated with `@websocket_api.async_response`. **Never** run blocking I/O in a `@callback` handler.
6. **Results and errors.** Deliver success via `connection.send_result(msg["id"], result)` using the incoming `msg["id"]`; report errors via `connection.send_error(msg["id"], "<code>", "<message>")` instead of letting an exception propagate, and **return** after every `send_error`. Never substitute the `msg["id"]`.
7. **Admin restriction.** Decorate admin-only commands with `@websocket_api.require_admin`; consider it for sensitive or integration-internal data. Never hand-roll admin checks in the handler body.
8. **Register in setup.** Register via `websocket_api.async_register_command(hass, ws_handler)` inside the integration's setup method (e.g. `async_setup`), not scattered across platform modules; do **not** require `websocket_api` as a manifest dependency.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `data_need` | yes | — | the data the card/panel needs from the backend, in prose |
| `type` | no | derived + confirmed | `"<domain>/<name>"` message type |
| `schema_fields` | no | derived | `vol.Required`/`vol.Optional` input fields |
| `does_io` | no | inferred | drives the `@callback` vs. `@websocket_api.async_response` choice |
| `require_admin` | no | asked when sensitive | whether `@websocket_api.require_admin` is added |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Settle command vs. service: data fetch into the frontend → command; action/mutation → point at `ha-service-definition-generator` and abort.
3. Read `ha/frontend-websocket-commands`.
4. The command `type` is not already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the resolved `"<domain>/<name>"` type, the schema fields, the sync/async choice (and why), whether `require_admin` applies, and the command-vs-service justification in one paragraph. Wait for confirmation.

### 2) Generate

- The handler `(hass, connection, msg)` decorated with `@websocket_api.websocket_command({vol.Required("type"): "<domain>/<name>", ...})`.
- `@callback` for an in-memory handler, or `@websocket_api.async_response` + `async def` for I/O/device/computation; stack `@websocket_api.require_admin` when admin-only.
- `connection.send_result(msg["id"], result)` on success; `connection.send_error(msg["id"], code, message)` + `return` on each error path.
- The `websocket_api.async_register_command(hass, ws_handler)` call in the setup method (e.g. `async_setup`); add the `from homeassistant.components import websocket_api` import.

Optionally sketch the matching `await hass.callWS({ type: "<domain>/<name>", ... })` frontend call (same type and field names), but the consumer side is owned by `ha/frontend-data-api`.

### 3) Validate and report

Validate offline (handler carries `@websocket_api.websocket_command`; `type` is `"<domain>/<name>"`; fields use `vol.Required`/`vol.Optional` with annotations; sync/async matches the work; success via `send_result(msg["id"], ...)`, errors via `send_error(msg["id"], ...)` + `return`; `require_admin` where needed; `async_register_command` in the setup method; no manifest dependency). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/frontend-websocket-commands` acceptance criteria, plus the changed file paths and the justified command-vs-service choice.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- User-driven actions / mutations → `ha-service-definition-generator`
- Frontend consumer side (`callWS`, response typing) → `ha/frontend-data-api`
- A custom panel consuming the command → `ha-panel-add`
- Deploy to live HA → out of scope
