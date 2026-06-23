# HA Integration: Config Flow Patterns

Status: draft

## Context

A modern Custom Integration in Home Assistant is configured exclusively through the UI-driven **config flow**; YAML-based configuration is deprecated for new integrations as of HA 2024. A complete Custom Integration covers four flows: the **user flow** for initial setup, the **reauth flow** triggered when a coordinator raises `ConfigEntryAuthFailed` (see `ha/coordinator-patterns`), the **reconfigure flow** for after-the-fact URL or endpoint changes, and the **options flow** for runtime-configurable behaviour switches (typically polling intervals).

`nolte/kamerplanter-ha` validates this quartet with an additional multi-step pattern (tenant selection after successful auth) and zeroconf discovery that pre-fills the user flow. This spec lifts the quartet into a generic obligation and pins down how `entry.data` (immutable setup data) is cleanly separated from `entry.options` (behaviour switches).

Quality scale markers:
- **Bronze**: basic config flow (`async_step_user` + `manifest.json:config_flow: true`).
- **Silver**: reauth flow for auth-based integrations.
- **Gold**: reconfigure flow.

## Goals

- Make config flow the only configuration path — no YAML config block, no imperative imports
- Define the four flows (user / reauth / reconfigure / options) as the standard suite, so skill output ships reauth-capable and reconfigure-capable without retrofitting
- Make `unique_id` setting on the config entry mandatory, so duplicate setups against the same endpoint are rejected automatically
- Establish the contract that `entry.data` (immutable setup state) is separate from `entry.options` (runtime-mutable)
- Plan discovery integration (zeroconf, DHCP, SSDP, …) as a pre-fill source for `async_step_user`, without discovery bypassing the user-confirmation step
- Require schema validation **and** API test validation per user input, so bad data does not surface only inside the coordinator loop

## Non-Goals

- YAML-based configuration (classic `async_setup`) — forbidden for new Custom Integrations
- Discovery mechanics themselves (zeroconf TXT format, DHCP MAC match, SSDP service type) — separate follow-up specs (`ha/zeroconf-discovery`, `ha/dhcp-discovery`, …)
- Reauth trigger inside the coordinator — that belongs in `ha/coordinator-patterns` (mapping `AuthError → ConfigEntryAuthFailed`)
- Multi-account / multi-tenant sharing strategies (one account token across multiple entries) — separate spec once concretely needed
- Frontend customization of config-flow rendering — HA owns the frontend; skills do not interfere with rendering

## Requirements

### Manifest precondition

- **MUST** set `manifest.json:config_flow: true` — see `ha/integration-architecture`
- **MUST NOT** offer `async_setup`-based YAML configuration as an alternative path; YAML config is rejected by HA 2024 for new integrations and trips the hassfest audit

### `ConfigFlow` class

- **MUST** define a subclass of `homeassistant.config_entries.ConfigFlow` in `config_flow.py`
- **MUST** annotate the class with `domain=DOMAIN` (class attribute)
- **MUST** set `VERSION` as a class attribute — starting at `1`; every schema change to `entry.data` (for example a new mandatory field) bumps `VERSION` and triggers `async_migrate_entry`
- **SHOULD** store discovery payloads (for example zeroconf properties) as instance attributes between steps rather than class attributes, so parallel flow instances do not interfere

### User flow (mandatory)

- **MUST** implement `async_step_user(self, user_input=None) -> ConfigFlowResult` — the primary entry point for manual setup
- **MUST** render a form with the input schema when `user_input is None` (`return self.async_show_form(step_id="user", data_schema=USER_SCHEMA, errors=errors)`)
- **MUST** run two validation stages when `user_input` is present, in this order:
  1. Schema validation via `vol.Schema(...)` (implicit on rendering, but verify explicitly for safety)
  2. **Real validation** against the API: run a test call (for example a health endpoint, token validation) and catch API-specific exceptions
- **MUST** call `await self.async_set_unique_id(<unique_id>)` on successful validation, where `<unique_id>` uniquely identifies the configuration target (typically `f"{base_url}_{tenant_slug}"` or `f"{instance_id}"` from discovery)
- **MUST** call `self._abort_if_unique_id_configured()` immediately after `async_set_unique_id` — prevents duplicate setups
- **MUST** return `return self.async_create_entry(title=<title>, data=<entry_data>)` on success; `<title>` is human-readable and translated in `strings.json`
- **MAY** be structured as a multi-step flow — typical: step 1 collects auth credentials, step 2 lets the user pick from authenticated tenants/accounts
- **MUST NOT** write credentials or API keys to `entry.data` without explicit user confirmation

### Reauth flow

- **SHOULD** implement `async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult` when the integration is auth-based (API key, OAuth token, username/password)
- **SHOULD** route the reauth entry into an `async_step_reauth_confirm` step that renders a schema with the credential to be renewed
- **MUST** show error messages on failed re-validation without destroying the entry or aborting the reauth flow
- **MUST** return `self.async_update_reload_and_abort(self._get_reauth_entry(), data_updates={CONF_<KEY>: user_input[CONF_<KEY>]})` on successful re-validation — that updates `entry.data` with the new credential and reloads the entry
- **MUST NOT** store reauth-specific credentials in `entry.options` — credentials belong in `entry.data`

### Reconfigure flow

- **SHOULD** implement `async_step_reconfigure(self, user_input=None) -> ConfigFlowResult` when the API endpoint should be changeable after the fact (for example a server move to a new IP / hostname)
- **MUST** pre-fill existing `entry.data` values as suggested values in the schema, so the user only confirms what actually changed: `self.add_suggested_values_to_schema(SCHEMA, self._get_reconfigure_entry().data)`
- **MUST** run the same real validation as the user flow before writing the data
- **MUST** return `self.async_update_reload_and_abort(self._get_reconfigure_entry(), data_updates={...})` on success

### Options flow

- **SHOULD** use `OptionsFlowWithReload` as the base class for HA 2024.2+ — the class invokes `entry.async_reload()` automatically on save, so coordinators restart with the new intervals
- **MAY** use the classic `OptionsFlow` with manual `await self.hass.config_entries.async_reload(entry.entry_id)` for HA minimum versions before 2024.2
- **MUST** export an `@staticmethod async_get_options_flow(config_entry)` (or the `@callback def async_get_options_flow(config_entry)` equivalent) on the `ConfigFlow` class that returns an options-flow instance
- **MUST** end the options flow with `async_create_entry(data=user_input)` — `title` is not allowed here
- **SHOULD** use `add_suggested_values_to_schema(OPTIONS_SCHEMA, self.config_entry.options)`, so current values are pre-selected
- **MUST** give every behaviour option declared in `OPTIONS_SCHEMA` a default — the coordinator reads with `entry.options.get(CONF_<KEY>, DEFAULT_<KEY>)` (see `ha/coordinator-patterns`)

### Discovery integration

- **MAY** implement discovery steps (`async_step_zeroconf`, `async_step_dhcp`, `async_step_ssdp`, `async_step_mqtt`, `async_step_bluetooth`, `async_step_usb`); each step has its own follow-up spec
- **MUST** set `unique_id` from the discovery payload such that it uniquely identifies the device discovered by the mechanism (typically: `instance_id` from zeroconf TXT records)
- **SHOULD** pass discovery data into `async_step_user` (or a discovery-specific confirmation step) as pre-fill rather than bypassing the user-confirmation step — the user should know what is being added
- **MUST** abort the discovery flow with `_abort_if_unique_id_configured(updates={...})` when the `unique_id` is already configured — the `updates` map can be used to refresh changed discovery data (for example a new IP) into `entry.data` without a reauth

### Validation and error messages

- **MUST** validate every user input declaratively through `voluptuous` schemas (`vol.Schema`) — no ad-hoc string manipulation
- **MUST** run API test validation as a real validation step — schema validation alone is not enough
- **MUST** show validation errors to the user via the `errors` dict in `async_show_form(..., errors=errors)`
- **MUST** use error keys (`"cannot_connect"`, `"invalid_auth"`, `"unknown"`) that are translated in `strings.json` as `config.error.<key>` (see `ha/translations`)
- **SHOULD** share a common validation helper (for example `async def _validate_input(hass, data) -> dict`) between user, reauth, and reconfigure flows, so the API-test behaviour stays consistent

### `entry.data` vs. `entry.options`

- **MUST** store immutable setup configuration (URL, API key, tenant slug, instance_id, other identifying data) in `entry.data`
- **MUST** store runtime-mutable behaviour switches (polling intervals, feature toggles, language overrides) in `entry.options`
- **MUST NOT** mutate `entry.data` outside of reauth, reconfigure, or `async_migrate_entry` — those three are the only allowed paths to mutate `entry.data`
- **MUST NOT** store credentials or other auth material in `entry.options` — `entry.options` is intended as runtime-configurable, not as a credential store

## Acceptance Criteria

- [ ] `manifest.json:config_flow` is `true`
- [ ] `config_flow.py` contains a `ConfigFlow` subclass with `domain = DOMAIN` and `VERSION = N`
- [ ] `async_step_user` is implemented, validates the schema, runs an API test call, and calls `async_set_unique_id` + `_abort_if_unique_id_configured`
- [ ] When the integration is auth-based: `async_step_reauth` and `async_step_reauth_confirm` are implemented; on success `async_update_reload_and_abort` is called with `data_updates`
- [ ] When the endpoint should be changeable after setup: `async_step_reconfigure` is implemented and pre-fills existing `entry.data` as suggested values
- [ ] Options flow is implemented as an `OptionsFlowWithReload` subclass (or classic `OptionsFlow` with manual reload)
- [ ] `async_get_options_flow(config_entry)` is exported on the `ConfigFlow` class
- [ ] Validation errors are surfaced via the `errors` dict; error keys are translated in `strings.json` as `config.error.<key>`
- [ ] `entry.data` and `entry.options` are cleanly separated — no auth data in `entry.options`, no behaviour switches in `entry.data`
- [ ] Quality scale markers: **Bronze** for the user flow, additional **Silver** for the reauth flow, additional **Gold** for the reconfigure flow

## Open Questions

- **HA minimum version implication for `OptionsFlowWithReload`**: The class exists in HA 2024.2+. If the portfolio-wide HA minimum (see open question in `ha/integration-architecture`) pins to 2024.1, skills must scaffold the classic `OptionsFlow` plus manual `async_reload` — the spec requirement would then be conditioned on 2024.2+.
- **Multi-step user flow as obligation**: `kamerplanter-ha` uses two steps (auth → tenant selection) because multi-tenant setup demands it. Should the spec allow multi-step flows in general, or define a convention for multi-tenant selection?
- **Reauth trigger beyond `ConfigEntryAuthFailed`**: Is the coordinator-driven trigger (see `ha/coordinator-patterns`) sufficient, or are there cases where reauth is initiated manually by the user (for example after a voluntary token reset at the backend)?
- **Reconfigure without reload**: Are there reconfigure cases that should **not** reload the entry (for example a topic-hint change in an MQTT-based integration)? `async_update_reload_and_abort` always reloads; a no-reload variant would require `async_update_entry` + `async_abort`.
- **Validation helper style**: Shared free helper (`_validate_input`) vs. methods on the flow class vs. methods on a separate validator class — is there a convention, or does this remain per-integration?
