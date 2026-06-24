# HA Integration: Frontend Data API (`hass` object)

Status: draft

## Context

The HA frontend passes a single `hass` object around all frontend extensions. This object carries the latest state of all entities, lets you send commands back to the server, and provides helpers to format entity state in a localized, unit-correct way. Custom cards, custom panels, dialogs, and selectors all consume the same data surface — this spec codifies exactly that surface.

Whenever a state changes, HA creates a new version of the changed objects. A strict equality check (`const changed = newVal !== oldVal;`) is therefore enough to detect changes — the reason frontend entity-change detection works at all. The recommended way to get data is to consume the available contexts; `hass.states` and direct access remain the pragmatic option for simple cards.

Direct `hass` access via the browser devtools (`$0.hass` on the `<home-assistant>` element) is reference inspection only — production code must have `hass` passed to the extension correctly. This spec is delimited from the card lifecycle: `ha/lovelace-card-patterns` covers the `set hass` setter and re-render behaviour; here it is about the data and method surface of the `hass` object itself, which every frontend extension consumes.

Quality scale marker: **Not** part of the HA quality scale — the frontend data surface is a frontend delivery axis and lives outside the integration scale.

## Goals

- Establish context consumption as the recommended standard way to get frontend data (`states`, `entities`, `extendedEntities`, `connection`, `user`)
- Establish the `@consume({ context, subscribe: true })` pattern as the Lit default for initial data plus subscribed updates
- Establish `hass.callService(domain, service, data)` as the standard way for backend service calls
- Establish `hass.callWS(message)` as the recommended modern path for WebSocket commands — away from `callApi`
- Mandate entity-state formatting via the `formatEntity*` helpers instead of displaying raw state strings
- Keep the delimitation from the card lifecycle (`ha/lovelace-card-patterns`) clean

## Non-Goals

- The card lifecycle and the `set hass` setter — covered in `ha/lovelace-card-patterns`
- The visual card-editor UI and the selector shape — covered in `ha/lovelace-card-editor`
- The backend side of custom WebSocket commands — covered in `ha/frontend-websocket-commands`
- The integration side of `callService` (service registration, schema) — covered in `ha/services`
- Defining your own local contexts and acting as a provider — only a MAY mention here, not a detailed pattern

## Requirements

### Consuming contexts (`states`/`entities`/`connection`/`user`)

- **MUST** consume frontend data primarily through the available contexts — the `states` context (states of all entities) is the most common
- **SHOULD** consume `entities` or `extendedEntities` when the extension needs entity-registry data, instead of reconstructing it from `states`
- **SHOULD** consume `connection` to get the HA connection object, and `user` for the logged-in user
- **MAY** create your own local contexts to pass data around inside your own component hierarchy

### `@consume` pattern & subscriptions

- **MUST** consume a context in Lit components via `@consume({ context: <ctx>, subscribe: true })` when the extension has to react to data updates
- **MUST** fire a custom event with a callback to register at the context provider — the provider then sends initial data
- **SHOULD** set `subscribe: true` so the provider also sends updates on every data change — without a subscription you only get the initial data
- **MUST NOT** treat context data as a static snapshot while `subscribe: true` is active — the component keeps receiving new values

### Service calls (`callService`)

- **MUST** call backend service actions via `hass.callService(domain, service, data)` (for example `hass.callService('light', 'turn_on', { entity_id: 'light.kitchen' })`)
- **MUST** handle the `Promise` returned by `callService` — all methods starting with `call` are async and resolve with the result
- **MUST NOT** mutate state server-side through raw API paths when a registered service exists — `callService` is the canonical mutation path

### WebSocket (`callWS`) & legacy (`callApi`)

- **SHOULD** call WebSocket commands via `hass.callWS(message)` (for example `hass.callWS({ type: 'config/auth/create', name: 'Paulus' })`) — the recommended modern path
- **MUST NOT** use `hass.callApi(method, path, data)` as the default for new extensions — HA is migrating away from API calls towards `callWS(message)`
- **MAY** use `hass.callApi('get', 'hassio/backups')` only when no WebSocket equivalent exists yet (legacy fallback)
- **MUST** handle the `Promise` from `callWS` or `callApi` — both are async

### Entity-state formatting (`formatEntity*`)

- **MUST** format the displayed entity state via `hass.formatEntityState(stateObj, state)` instead of rendering the raw `state` string — the value is localized using user-profile settings (language, number/date format, timezone) and the unit of measurement
- **MUST** format attribute values via `hass.formatEntityAttributeValue(stateObj, attribute, value)` (for example `"20.5 °C"`) instead of displaying raw attribute values
- **SHOULD** localize attribute names via `hass.formatEntityAttributeName(stateObj, attribute)` (for example `"Current temperature"`)
- **SHOULD** build display names via `hass.formatEntityName(stateObj, name, options)` from the registry context (entity, device, area, floor) — the same helper the built-in cards use; `undefined` falls back to the friendly name, a string is taken as a user override as-is

## Acceptance Criteria

- [ ] Data is consumed primarily through contexts (`states`/`entities`/`extendedEntities`/`connection`/`user`)
- [ ] Lit components consume contexts via `@consume({ context, subscribe: true })`
- [ ] When updates are needed, `subscribe: true` is set; a custom event registers at the provider
- [ ] Backend service actions go through `hass.callService(domain, service, data)`
- [ ] WebSocket commands go through `hass.callWS(message)`; `callApi` only as a legacy fallback
- [ ] Every `call*` invocation handles the returned `Promise`
- [ ] Entity state is formatted via `hass.formatEntityState`, not rendered raw
- [ ] Attribute values and names are formatted via `formatEntityAttributeValue` / `formatEntityAttributeName`
- [ ] Display names are built via `hass.formatEntityName` from the registry context
- [ ] Quality scale marker: **Not** part of the HA quality scale (frontend surface)

## Open Questions

- **Context vs. direct access**: When is `hass.states[id]` direct access still fine for a simple card, and at what point must it switch to context consumption? Currently pragmatically mixed.
- **`formatEntityName` availability**: The helper is only available since HA 2026.4. How is a minimum HA version declared per extension and guarded against a missing helper?
- **Custom WebSocket commands**: The backend side of custom WS commands lives in `ha/frontend-websocket-commands` — how cleanly is the boundary drawn between `callWS` consumption (here) and command registration (there)?
- **`callApi` leftovers**: HA is migrating away from `callApi`. When does a WebSocket equivalent exist for every API path still needed today, so `callApi` can be dropped entirely?
- **Local context providers**: Defining your own contexts is only a MAY here. Is a follow-up spec needed for the provider pattern once an extension passes data across multiple component levels?
