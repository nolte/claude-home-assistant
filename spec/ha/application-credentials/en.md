# HA Integration: Application Credentials (OAuth2)

Status: draft

## Context

Integrations that offer [configuration via OAuth2](https://developers.home-assistant.io/docs/core/integration/config_flow#configuration-via-oauth2) let users link their accounts. OAuth2 requires credentials (client ID / client secret) shared between an application and a provider. Home Assistant provides these integration-specific OAuth2 credentials through the **Application Credentials platform**: the user creates their own credentials with the cloud provider — often acting as an application developer — and registers them with Home Assistant via the Application Credentials UI. This path (*Local OAuth with Application Credentials Component*) is, per the HA docs, **required** for all OAuth2 integrations; the alternative *Cloud Account Linking* via Nabu Casa is recommended but out of scope for this spec.

The integration enables this path by declaring `application_credentials` as a manifest dependency and shipping an `application_credentials.py` platform module. That module provides at least an `AuthorizationServer` (authorize URL + token URL); optionally custom OAuth2 implementations, PKCE support, and description placeholders for the UI. The actual config flow then runs through `config_entry_oauth2_flow.AbstractOAuth2FlowHandler`, and token refresh through the `OAuth2Session` helpers.

Delimitation: this spec covers **only** the OAuth2 application-credentials path. Generic user/password or API-key config flows stay in `ha/config-flow-patterns`; the OAuth2 flow is a variant of those and is described here only where it differs from the generic quartet.

## Goals

- Make the Application Credentials platform the standard path for OAuth2 integrations, so users can enter their own client credentials
- Establish the manifest dependency `application_credentials` as mandatory for every OAuth2 integration
- Define the contract for `application_credentials.py` — at minimum `async_get_authorization_server`, optionally a custom implementation and description placeholders
- Pin down the coupling to the OAuth2 config flow (`AbstractOAuth2FlowHandler`) and token refresh (`OAuth2Session`) without duplicating the generic flow mechanics from `ha/config-flow-patterns`
- Anchor secure handling of the user-entered credentials (`client_id` / `client_secret`) as a contract (see `ha/security-hardening`)
- Ensure translatable instruction text for the credentials dialog via `strings.json` and optional placeholders (see `ha/translations`)

## Non-Goals

- Generic user/password or API-key config flows — those stay in `ha/config-flow-patterns`
- Cloud Account Linking via Nabu Casa (centrally managed client ID/secret) — separate path, not covered here
- Building an OAuth2-capable API library (token-refresh structure in the client) — separate follow-up spec / API library guide
- Importing YAML credentials for legacy integrations (`async_import_client_credential`) — relevant only as a migration path; no new integration may accept YAML credentials
- Frontend rendering of the application-credentials dialog — HA owns the frontend

## Requirements

### Prerequisites (manifest dependency)

- **MUST** list `application_credentials` in the `dependencies` array of `manifest.json` — see `ha/integration-manifest`
- **MUST** additionally have `manifest.json:config_flow: true` set — the Application Credentials platform is consumed through a config flow (see `ha/config-flow-patterns`)

### `application_credentials.py` platform

- **MUST** add a file `application_credentials.py` in the integration folder that implements the platform functions
- **MUST** implement `async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer` and return a valid `AuthorizationServer`
- **MAY** instead implement `async def async_get_auth_implementation(hass, auth_domain, credential) -> config_entry_oauth2_flow.AbstractOAuth2Implementation` when a custom OAuth2 implementation (for example differing token handling) is needed
- **MAY** return a `LocalOAuth2ImplementationWithPkce` from `async_get_auth_implementation` for PKCE support (RFC 7636), passing `credential.client_id` and optionally `credential.client_secret`
- **MUST NOT** accept OAuth2 client credentials in `configuration.yaml` — new integrations let the user enter credentials via the Application Credentials UI

### Authorization Server

- **MUST** import `AuthorizationServer` from `homeassistant.components.application_credentials`
- **MUST** set `authorize_url` — the OAuth authorize URL the user is redirected to during the config flow (required field)
- **MUST** set `token_url` — the URL for obtaining an access token (required field)
- **SHOULD** specify `authorize_url` and `token_url` as the provider's HTTPS endpoints, not as hard-coded plaintext HTTP URLs (see `ha/security-hardening`)

### Config flow integration (OAuth2)

- **MUST** define the config flow as a subclass of `config_entry_oauth2_flow.AbstractOAuth2FlowHandler` with `domain=DOMAIN` — the generic flow mechanics (schema validation, `unique_id`, `entry.data` vs. `entry.options`) are pinned down in `ha/config-flow-patterns`
- **MUST** use the HA-invoked `async_oauth_create_entry(self, data)` to create or (in the reauth case) update the config entry with the OAuth token data
- **SHOULD** set `async_set_unique_id` in `async_oauth_create_entry` and call `self._abort_if_unique_id_configured()` on first creation to prevent duplicate setups of the same account

### Token refresh & reauth

- **MUST** run token refresh through the HA-provided `OAuth2Session` helpers from `config_entry_oauth2_flow` rather than refreshing tokens itself — the API library must be structured so HA owns the refresh
- **MUST** run a token validation/refresh call on setup and raise `ConfigEntryAuthFailed` on auth failure, so HA starts the reauth flow (see `ha/config-flow-patterns` and the reauth quality-scale rule)
- **SHOULD** implement `async_step_reauth` / `async_step_reauth_confirm` that show the reauth dialog and then route back into the OAuth2 flow via `async_step_user`
- **MUST** call `self._abort_if_unique_id_mismatch()` in the reauth case (`self.source == SOURCE_REAUTH`) and finish with `async_update_reload_and_abort(self._get_reauth_entry(), data_updates=data)` — this enforces the same account and reloads the entry with new tokens

### Description placeholders/translations

- **MUST** define texts for the application-credentials dialog under the `application_credentials` key in `strings.json` (see `ha/translations`)
- **MAY** implement `async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]` in `application_credentials.py` to inject placeholders (for example `console_url`) into the dialog text
- **SHOULD** give the user a hint in the `description` text about where (for example which developer console) to create the credentials, ideally as a linked placeholder

## Acceptance Criteria

- [ ] `manifest.json:dependencies` contains `application_credentials` and `manifest.json:config_flow` is `true`
- [ ] `application_credentials.py` exists and implements `async_get_authorization_server` with a valid `AuthorizationServer(authorize_url=..., token_url=...)`
- [ ] When a custom implementation is needed: `async_get_auth_implementation` is implemented (optionally with `LocalOAuth2ImplementationWithPkce` for PKCE)
- [ ] `config_flow.py` contains an `AbstractOAuth2FlowHandler` subclass with `domain = DOMAIN` that uses `async_oauth_create_entry` and sets `unique_id`
- [ ] Token refresh runs through `OAuth2Session`; setup raises `ConfigEntryAuthFailed` on auth failure
- [ ] Reauth is implemented: `async_step_reauth` / `async_step_reauth_confirm` plus `_abort_if_unique_id_mismatch` and `async_update_reload_and_abort` in the reauth path
- [ ] The credentials dialog is translated via the `application_credentials` key in `strings.json`; optional placeholders come from `async_get_description_placeholders`
- [ ] No OAuth2 client credentials are accepted via `configuration.yaml`

## Open Questions

- **PKCE as default vs. opt-in**: Should the spec recommend `LocalOAuth2ImplementationWithPkce` for new integrations (SHOULD) where the provider supports PKCE, or does PKCE stay a pure MAY option per provider capability?
- **Cloud Account Linking as follow-up spec**: *Cloud Account Linking* via Nabu Casa is recommended by HA but set as a non-goal here. Should a separate spec (`ha/cloud-account-linking`) be created once a portfolio integration takes the partner path?
- **YAML credential import**: `async_import_client_credential` exists for legacy migrations. Should the spec get an explicit migration section, or does the import stay out of scope since new integrations do not need it?
- **`unique_id` source for OAuth2**: In the OAuth2 flow the `unique_id` typically comes from a user ID that is only available after successful auth. Are there providers without a stable user ID where an alternative `unique_id` strategy becomes necessary?
