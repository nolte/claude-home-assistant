# HA Integration: Custom Panel Configuration and Options View

Status: draft

## Context

A custom panel (`panel_custom`) is a full-page frontend surface. Beyond rendering data, many panels need to expose their **own configuration or options view** — a settings surface where the user (or admin) reviews and changes how the panel behaves, and where those choices are **persisted** so they survive a reload. This is the panel analogue of an integration's config-vs-options flow: some values are fixed at deploy time, others are meant to be edited at runtime.

HA offers no single "panel options" API. Instead a panel composes the options view from existing frontend building blocks and chooses a persistence path deliberately. This spec covers **that surface**: what a panel's configuration/options view can look like, which inputs it may read, and — the load-bearing decision — **where the changed values are stored**. It delimits against the sibling specs and references them by slug rather than duplicating:

- Panel **registration and the element contract** (`panel_custom` YAML keys, `module_url`, `customElements.define`, the `hass` / `narrow` / `route` / `panel` properties) — `ha/lovelace-views-panels`. This spec assumes that contract and builds on it.
- The **WebSocket command definition** mechanics (`@websocket_api.websocket_command`, `async_register_command`) — `ha/frontend-websocket-commands`. This spec calls such a command as a persistence path; it does not re-document how to define one.
- The **`hass` object and `hass.callWS`** data channel — `ha/frontend-data-api`.
- The **`ha-form` / `ha-selector`** form-schema pattern — `ha/lovelace-card-editor` (reused here for a panel's options form).
- The backend **config-vs-options** conceptual parallel — `ha/config-flow-patterns`.
- Server-side **authorization enforcement** — `ha/security-hardening`.

**Evidence tiers.** HA-internal facts must be verified against the official docs, not asserted from memory (`ha/upstream-docs-verification`). The panel-options surface is thin in the official docs — the docs describe registration and `panel.config`, but not persistence, not the `route` shape, and not the per-user data store. Each rule below is tagged:

- `[doc]` — stated in the official docs (`developers.home-assistant.io/docs/frontend/custom-ui/creating-custom-panels/`, `.../custom-card/`, `.../frontend/data/`, `.../extending/websocket-api/`; `home-assistant.io` `panel_custom` integration page); quoted or paraphrased.
- `[src]` — verified against HA frontend/backend source (`github.com/home-assistant/frontend`, `github.com/home-assistant/core`) because the docs are silent; the source is the authority for the exact identifier/behaviour.
- `[unsupported]` — not stated in either docs or as a stable public API; an inference from source or absence. **Must** be presented as an inference, never as a documented guarantee.
- `[policy]` — a nolte-portfolio rule; **not** an HA-documented requirement, marked as such.

Quality scale marker: custom panels are **not part of the HA quality scale**; a panel's configuration/options view is a frontend delivery-shape concern and lives outside the scale.

## Goals

- Separate **deploy-time config** (`panel.config`, set at registration) from **runtime-editable options** (persisted through a WebSocket command or the per-user data store) so a panel does not try to persist through the wrong channel
- Establish the two documented/verified persistence paths — a **custom WebSocket command** for domain/shared state and the **`frontend/*_user_data`** store for per-user UI preferences — and when each applies
- Compose the options view from reused frontend building blocks (`ha-form` + `ha-selector`) instead of hand-rolling form widgets
- Gate admin-only options both in the UI (`require_admin` / `hass.user.is_admin`) and, decisively, on the **server side** in the command handler
- Keep HA-doc facts, frontend/backend-source facts, inferences, and portfolio policy cleanly separated so no rule rests on an undocumented assumption presented as documented

## Non-Goals

- Panel registration and the element property contract (`panel_custom` YAML, `module_url`, `hass`/`narrow`/`route`/`panel`, ES5 adapter, `embed_iframe`) — `ha/lovelace-views-panels`
- Defining a WebSocket command on the backend (decorator, schema, `async_register_command`, subscription lifecycle) — `ha/frontend-websocket-commands`
- The detailed schema of the `hass` object data channels — `ha/frontend-data-api`
- The card config editor (`getConfigElement` / `getConfigForm` / `config-changed`) — `ha/lovelace-card-editor` (this spec reuses the `ha-form` pattern for a panel, not the card-editor contract)
- The backend integration config/options flow (`config_flow.py`, `OptionsFlow`) — `ha/config-flow-patterns`
- Theming and translations of the options view — separate axes

## Requirements

### Static registration config (`panel.config`)

- **MUST** treat the `config` block passed at registration as **deploy-time, set-once** data: it is passed into the web component at instantiation and read at runtime as `panel.config` `[doc]` (the `panel_custom` page: "Config is available as `panel.config`"; the `config:` YAML key is "Configuration to be passed into your web component when being instantiated")
- **MUST NOT** mutate `panel.config` at runtime and expect the change to persist — there is **no documented write-back path** from the element to the registration config `[unsupported]` (the read-only nature is inferred from source: `config` is a registration-time object with no persistence hook; it is not documented as read-only, so present it as an inference, not a guarantee)
- **MAY** register the panel programmatically via `async_register_built_in_panel(..., config=...)` from an integration instead of `panel_custom` YAML `[src]` (the Python registration API is not in the docs; only the resulting `panel.config` property is `[doc]`)
- **SHOULD** use `panel.config` for values that are legitimately fixed per deployment (an API base URL, a feature flag, a mode) and route everything the **user edits** to a persistence path below

### The options view surface (routing & form composition)

- **SHOULD** render the options/settings view as a distinct region or sub-route of the panel rather than a separate registration — a panel is one full-page element, and the options view is part of it
- **MAY** drive an in-panel sub-route from the `route` property (`{ prefix, path }`) HA sets on the element `[src]` (the `route` property and its `{ prefix, path }` shape appear in the panel example but are **not** in the documented property table; treat `route` as source-verified, consistent with `ha/lovelace-views-panels`)
- **SHOULD** compose the options form from `ha-form` bound to a schema of `ha-selector` selector configs — the documented public path is a form schema of selectors `[doc]` (the `getConfigForm` selector approach links to the `/docs/blueprint/selectors/` selector catalogue), while the `ha-form` / `ha-selector` **elements used directly** in a panel are frontend-internal `[src]` (there is no documented `getConfigForm` equivalent for a standalone panel, so a panel binds `ha-form` directly)
- **SHOULD** reuse HA selectors (entity, area, boolean, number, select) rather than raw inputs so the options view inherits HA's validation, theming, and mobile behaviour `[policy]`

### Persistence path A — custom WebSocket command (domain/shared state)

- **MUST** use a **custom WebSocket command** as the persistence path when the options are **domain or shared state** (configuration that applies to the installation, not just the current user) — define it per `ha/frontend-websocket-commands` and call it from the panel with `hass.callWS({ type: "<domain>/options/set", ... })` `[doc]` (`hass.callWS` is documented as "Call a WebSocket command on the backend"; `@websocket_api.websocket_command` + `async_register_command` are documented under Extending the WebSocket API)
- **SHOULD** provide a matching read command (`hass.callWS({ type: "<domain>/options/get" })`) the options view calls on load, and — where the options can change elsewhere — a subscription command so the view updates live `[doc]`
- **MUST NOT** invent an ad-hoc HTTP endpoint or write to a file from the frontend to persist options when a WebSocket command is the documented mechanism `[policy]`

### Persistence path B — per-user data store (`frontend/*_user_data`)

- **MAY** persist **per-user UI preferences** (a chosen tab, a collapsed section, a sort order — state that belongs to the current user, not the installation) through the frontend user-data store: `frontend/get_user_data`, `frontend/set_user_data`, `frontend/subscribe_user_data` `[src]` (these commands are **not** documented in either official docs repo; they are verified only in frontend source `src/data/frontend.ts` and the backend `frontend` component — treat as source-verified and flag as undocumented)
- **MUST NOT** use the per-user data store for **installation-wide** configuration — it is keyed per user, so admin-set shared options stored there would not be visible to other users `[src]`
- **SHOULD** choose path A vs path B by **ownership**: shared/domain state → WebSocket command (path A); per-user preference → user-data store (path B) `[policy]`

### Admin gating & server-side enforcement

- **MAY** set `require_admin: true` on the `panel_custom` registration so the panel is hidden from non-admin users in the sidebar `[doc]` (the `panel_custom` page: "If admin access is required to see this panel")
- **SHOULD** additionally gate admin-only controls **inside** the options view on `hass.user.is_admin` so a non-admin who reaches the view does not see admin-only options `[doc]` (`hass.user` exposes `is_admin`)
- **MUST** enforce admin-only writes on the **server side** in the WebSocket command handler — `require_admin` only hides the panel in the frontend and `hass.user.is_admin` is a frontend check; neither prevents a crafted WebSocket call `[src]`/`[policy]` (server-side enforcement of `require_admin` is not documented; the command handler is the real trust boundary, per `ha/security-hardening`)

### Config vs. options separation

- **MUST** classify every configurable value as **deploy-time config** (fixed per deployment → `panel.config`) or **runtime option** (user- or admin-editable → persistence path A or B), mirroring the integration config-vs-options split in `ha/config-flow-patterns` `[policy]`
- **MUST NOT** require a `configuration.yaml` edit and HA restart for a value the user is expected to change at runtime — that value is a runtime option and belongs in a persistence path, not in `panel.config` `[policy]`

## Acceptance Criteria

- [ ] Every configurable value is classified as deploy-time `panel.config` or a runtime option; runtime options do not require a YAML edit + restart
- [ ] `panel.config` is read at runtime as `panel.config` and is never mutated in the element to persist state
- [ ] Domain/shared options persist through a custom WebSocket command (`hass.callWS`), with a matching read (and, where relevant, subscription) command
- [ ] Per-user UI preferences persist through the `frontend/*_user_data` store and are not used for installation-wide config
- [ ] The options form is composed from `ha-form` + `ha-selector` selectors, not raw inputs
- [ ] Admin-only options are gated in the UI (`require_admin` / `hass.user.is_admin`) **and** enforced server-side in the command handler
- [ ] Every rule is tagged `[doc]` / `[src]` / `[unsupported]` / `[policy]`; source-verified, inferred, and policy facts are not presented as documented HA facts
- [ ] Quality scale marker: not part of the HA quality scale (frontend delivery shape)

## Open Questions

- **`route`-driven sub-routing depth**: the `route` `{ prefix, path }` shape is source-verified, not documented. Is in-panel sub-routing for a settings view a stable pattern, or should the options view stay a same-page region to avoid depending on undocumented `route` internals?
- **`ha-form` as a panel API**: `getConfigForm` (schema of selectors) is documented for cards, but no equivalent exists for panels, so a panel binds `ha-form` / `ha-selector` directly (`[src]`). Is there a supported panel-level form API, or is direct `ha-form` binding the only path?
- **`frontend/*_user_data` stability**: the per-user data commands are undocumented (`[src]`). Is there a documented per-user preference store for panels, or is this the de-facto one despite the documentation gap?
- **Server-side `require_admin` semantics**: the docs state `require_admin` controls panel visibility but do not state it enforces anything server-side. Does registration-time `require_admin` gate any backend access, or is the WebSocket command handler the only enforcement point (current assumption)?
- **Config write-back**: is there any supported way to persist back into the registration `config`, or is `panel.config` strictly read-only in practice (`[unsupported]`)? If a write-back path exists, the deploy-time-vs-runtime split would need revisiting.
