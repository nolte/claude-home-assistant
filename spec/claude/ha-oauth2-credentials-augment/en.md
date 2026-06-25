# Skill: `ha-oauth2-credentials-augment`

Status: draft

## Context

`ha/application-credentials` defines the mandatory OAuth2 path for integrations: users create their own client credentials with the provider and enter them via the **Application Credentials UI**. An integration enables this path by declaring `application_credentials` as a manifest dependency (with `config_flow: true` set) and shipping an `application_credentials.py` platform module that provides at least `async_get_authorization_server(hass) -> AuthorizationServer` (authorize URL + token URL) — optionally a custom implementation (`async_get_auth_implementation`, possibly `LocalOAuth2ImplementationWithPkce`) and `async_get_description_placeholders`. The config flow runs through `config_entry_oauth2_flow.AbstractOAuth2FlowHandler` with `domain=DOMAIN`, and token refresh through the `OAuth2Session` helpers. No skill augments this so far.

This skill augments the OAuth2 / application-credentials flow into an **existing** integration: the `application_credentials.py` module, the `AbstractOAuth2FlowHandler` config flow incl. reauth, the manifest dependency, the `OAuth2Session` token usage, and the `application_credentials:` strings — conformant to `ha/application-credentials`. Generic user/password or API-key flows are explicitly out of scope.

## Scope

Augmenting the OAuth2 application-credentials path into an existing `custom_components/<domain>/` integration: `application_credentials.py` (`async_get_authorization_server`, optional `async_get_auth_implementation` / `async_get_description_placeholders`), the `AbstractOAuth2FlowHandler` config flow with `DOMAIN` and logger, the manifest dependency `application_credentials` (plus `config_flow: true`), token refresh through `OAuth2Session`, the reauth path, and the `application_credentials:` entries in `strings.json`. The skill reads `ha/application-credentials` and validates.

## Goals

- Wire up the Application Credentials path as the standard for OAuth2 spec-conformantly, so users can enter their own client credentials
- Set the manifest dependency `application_credentials` and enforce `config_flow: true`
- Create `application_credentials.py` with `async_get_authorization_server` (a valid `AuthorizationServer(authorize_url=..., token_url=...)`); when needed `async_get_auth_implementation` (optionally with PKCE) and `async_get_description_placeholders`
- Wire the config flow as an `AbstractOAuth2FlowHandler` subclass (`domain = DOMAIN`, logger) that uses `async_oauth_create_entry` and sets `unique_id` — without duplicating the generic flow mechanics
- Run token refresh through `OAuth2Session`, make a refresh call on setup and raise `ConfigEntryAuthFailed` on auth failure; implement the reauth path
- Keep the credentials dialog translatable via `application_credentials:` in `strings.json` and anchor secure credential handling

## Non-Goals

- Generic user/password or API-key config flows — `ha-config-flow-augment` / `ha/config-flow-patterns`
- Cloud Account Linking via Nabu Casa (centrally managed client ID/secret) — separate path, not covered here
- Building an OAuth2-capable API library (token-refresh structure in the client) — separate follow-up spec
- Importing YAML credentials for legacy integrations (`async_import_client_credential`) — new integrations do not accept YAML credentials
- Greenfield scaffolding of an integration — `ha-integration-scaffold`; coordinator wiring — `ha-coordinator-add`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add OAuth2 to my integration", "wire up application credentials", "set up the OAuth2 config flow"
  - "let the user enter their own client id and secret"
  - "füge OAuth2 / Application Credentials hinzu"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the provider OAuth2 endpoints (`authorize_url`, `token_url`)
- **MAY** capture: whether a custom implementation (`async_get_auth_implementation`) or PKCE (`LocalOAuth2ImplementationWithPkce`) is needed, the `unique_id` source after auth, and description placeholders (e.g. `console_url`) for the dialog

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** check that the integration requires an OAuth2 provider; if a user/password or API-key flow covers the need, the skill **SHOULD** point at `ha-config-flow-augment` instead of forcing OAuth2
- **MUST** read the `ha/application-credentials` spec
- **MUST NOT** overwrite an existing non-OAuth2 `ConfigFlow` or an existing `application_credentials.py`; on collision abort

### Generation rules (from `ha/application-credentials`)

- **MUST** add `application_credentials` to the `dependencies` array of `manifest.json` and ensure `config_flow: true` (see `ha/integration-manifest`)
- **MUST** create `application_credentials.py` implementing `async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer` and importing `AuthorizationServer` from `homeassistant.components.application_credentials`; `authorize_url` and `token_url` are required fields
- **SHOULD** specify `authorize_url` and `token_url` as HTTPS endpoints, not as hard-coded plaintext HTTP URLs (see `ha/security-hardening`)
- **MAY** instead implement `async def async_get_auth_implementation(hass, auth_domain, credential) -> config_entry_oauth2_flow.AbstractOAuth2Implementation` when differing token handling is needed; for PKCE (RFC 7636) return a `LocalOAuth2ImplementationWithPkce` passing `credential.client_id` and optionally `credential.client_secret`
- **MUST** define the config flow as a subclass of `config_entry_oauth2_flow.AbstractOAuth2FlowHandler` with `domain = DOMAIN` and a `logger` property; do not duplicate the generic flow mechanics from `ha/config-flow-patterns`
- **MUST** use `async_oauth_create_entry(self, data)` to create or (reauth) update the config entry with the OAuth token data; **SHOULD** set `async_set_unique_id` and call `self._abort_if_unique_id_configured()` on first creation
- **MUST** run token refresh through the `OAuth2Session` helpers from `config_entry_oauth2_flow` rather than refreshing tokens itself; make a refresh call on setup and raise `ConfigEntryAuthFailed` on auth failure so HA starts reauth
- **SHOULD** implement `async_step_reauth` / `async_step_reauth_confirm`; in the reauth case (`self.source == SOURCE_REAUTH`) call `self._abort_if_unique_id_mismatch()` and finish with `async_update_reload_and_abort(self._get_reauth_entry(), data_updates=data)`
- **MUST** define texts for the credentials dialog under the `application_credentials` key in `strings.json` (see `ha/translations`); **MAY** add `async_get_description_placeholders(hass) -> dict[str, str]` to inject e.g. `console_url`
- **MUST NOT** accept OAuth2 client credentials in `configuration.yaml`
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: `manifest.json:dependencies` contains `application_credentials` and `config_flow` is `true`; `application_credentials.py` exists and implements `async_get_authorization_server` with a valid `AuthorizationServer`; the `AbstractOAuth2FlowHandler` config flow carries `domain = DOMAIN`, uses `async_oauth_create_entry` and sets `unique_id`; token refresh runs through `OAuth2Session`; setup raises `ConfigEntryAuthFailed`; the reauth path is implemented; the dialog is translated via `application_credentials:`; no YAML credentials are accepted
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/application-credentials`, plus the changed file paths

### Prohibitions

- **MUST NOT** create or replace a generic non-OAuth2 config flow
- **MUST NOT** refresh tokens itself instead of through `OAuth2Session`
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] `manifest.json:dependencies` contains `application_credentials` and `manifest.json:config_flow` is `true`
- [ ] `application_credentials.py` exists and implements `async_get_authorization_server` with a valid `AuthorizationServer(authorize_url=..., token_url=...)`
- [ ] When needed: `async_get_auth_implementation` is implemented (optionally with `LocalOAuth2ImplementationWithPkce` for PKCE)
- [ ] `config_flow.py` contains an `AbstractOAuth2FlowHandler` subclass with `domain = DOMAIN` and a logger that uses `async_oauth_create_entry` and sets `unique_id`
- [ ] Token refresh runs through `OAuth2Session`; setup raises `ConfigEntryAuthFailed` on auth failure
- [ ] Reauth is implemented: `async_step_reauth` / `async_step_reauth_confirm` plus `_abort_if_unique_id_mismatch` and `async_update_reload_and_abort` in the reauth path
- [ ] The credentials dialog is translated via the `application_credentials` key in `strings.json`; optional placeholders come from `async_get_description_placeholders`
- [ ] No OAuth2 client credentials are accepted via `configuration.yaml`; report names the changed file paths

## Open questions

- **PKCE as default vs. opt-in**: Should the skill actively recommend `LocalOAuth2ImplementationWithPkce` for providers with PKCE support, or leave it a pure MAY option per provider capability? Currently the skill asks.
- **`unique_id` source for OAuth2**: The `unique_id` typically comes from a user ID only available after auth. How does the skill handle providers without a stable user ID? Currently case-by-case with a query.
- **Reauth SHOULD vs. MUST**: `ha/application-credentials` lists the reauth path as SHOULD; the reauth quality-scale rule makes it effectively mandatory. Should the skill always generate it by default?
