---
name: ha-oauth2-credentials-augment
description: Augment an existing Home Assistant Custom Integration with the OAuth2 / Application Credentials flow, conforming to spec/ha/application-credentials. Creates application_credentials.py (async_get_authorization_server returning an AuthorizationServer with authorize_url + token_url, optional async_get_auth_implementation / LocalOAuth2ImplementationWithPkce and async_get_description_placeholders), wires the config_flow as a config_entry_oauth2_flow.AbstractOAuth2FlowHandler subclass with DOMAIN + logger that uses async_oauth_create_entry and sets unique_id, adds "application_credentials" to manifest dependencies (with config_flow true), runs token refresh through config_entry_oauth2_flow.OAuth2Session, implements the reauth path, and adds the application_credentials strings.json entries. Activate on "add OAuth2 to my integration", "wire up application credentials", "set up the OAuth2 config flow", "füge OAuth2 / Application Credentials hinzu". Do not activate for generic user/password or API-key config flows (ha-config-flow-augment), greenfield scaffolding (ha-integration-scaffold), coordinator wiring (ha-coordinator-add), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, oauth2]
---

# HA OAuth2 Credentials Augment

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-oauth2-credentials-augment/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-oauth2-credentials-augment/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user names the OAuth2 provider endpoints and reads back `application_credentials.py`, the OAuth2 config flow, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-repairs-add`).
- **Mid-flow interactivity** — the OAuth2-vs-non-OAuth2 check, the PKCE decision, and the `unique_id` source are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — one platform module plus the config-flow handler, the manifest edit, and the strings fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the provider-endpoint capture and the OAuth2-fit advice belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add the OAuth2 / Application Credentials flow to an existing integration whose provider requires OAuth2 — the user enters their own client id and secret via the Application Credentials UI.

## When NOT to activate

- a generic user/password or API-key config flow → `ha-config-flow-augment` / `ha/config-flow-patterns`
- greenfield integration scaffolding → `ha-integration-scaffold`
- coordinator wiring → `ha-coordinator-add`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One flow, one run.** Augment the OAuth2 application-credentials path; do not also rebuild a generic config flow.
2. **Read [`ha/application-credentials`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/application-credentials/de.md) first.** Do not generate from memory.
3. **Manifest prerequisites.** Add `application_credentials` to `manifest.json:dependencies` and ensure `config_flow: true` (see [`ha/integration-manifest`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/integration-manifest/de.md)).
4. **Authorization server contract.** `application_credentials.py` implements `async def async_get_authorization_server(hass) -> AuthorizationServer`, importing `AuthorizationServer` from `homeassistant.components.application_credentials`; `authorize_url` and `token_url` are required and **SHOULD** be HTTPS, never hard-coded plaintext HTTP (see [`ha/security-hardening`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/security-hardening/de.md)). Add `async_get_auth_implementation` (optionally `LocalOAuth2ImplementationWithPkce` for PKCE) only when custom token handling is needed.
5. **OAuth2 config-flow handler.** Define the flow as a `config_entry_oauth2_flow.AbstractOAuth2FlowHandler` subclass with `domain = DOMAIN` and a `logger` property; use `async_oauth_create_entry(self, data)` and set `unique_id` (`async_set_unique_id` + `_abort_if_unique_id_configured` on first creation). Do not duplicate the generic mechanics from `ha/config-flow-patterns`.
6. **HA owns the refresh.** Run token refresh through the `config_entry_oauth2_flow.OAuth2Session` helpers — **never** refresh tokens manually. On setup, make a refresh call and raise `ConfigEntryAuthFailed` on auth failure so HA starts reauth.
7. **Reauth path.** Implement `async_step_reauth` / `async_step_reauth_confirm`; in the reauth case (`self.source == SOURCE_REAUTH`) call `self._abort_if_unique_id_mismatch()` and finish with `async_update_reload_and_abort(self._get_reauth_entry(), data_updates=data)`.
8. **No YAML credentials.** Never accept OAuth2 client credentials via `configuration.yaml`.
9. **Translate the dialog.** Define the credentials dialog under the `application_credentials` key in `strings.json` (see [`ha/translations`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/translations/de.md)); optional placeholders come from `async_get_description_placeholders`.
10. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `authorize_url` / `token_url` | yes | — | the provider OAuth2 endpoints (HTTPS) |
| custom implementation / PKCE | no | asked when needed | `async_get_auth_implementation` / `LocalOAuth2ImplementationWithPkce` |
| `unique_id` source | no | asked | the post-auth user identity for `unique_id` |
| description placeholders | no | asked when needed | e.g. `console_url` for the dialog text |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Confirm the provider requires OAuth2; if a user/password or API-key flow suffices, surface `ha-config-flow-augment` instead of forcing OAuth2.
3. Read `ha/application-credentials`.
4. No existing non-OAuth2 `ConfigFlow` or existing `application_credentials.py` would be overwritten. If there is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the `authorize_url` / `token_url`, whether a custom implementation / PKCE is needed, the `unique_id` source, and any description placeholders in one paragraph. Wait for confirmation.

### 2) Generate

- `manifest.json`: add `application_credentials` to `dependencies`; ensure `config_flow: true`.
- `application_credentials.py`: `async_get_authorization_server` returning `AuthorizationServer(authorize_url=..., token_url=...)`; add `async_get_auth_implementation` (optionally `LocalOAuth2ImplementationWithPkce`) and `async_get_description_placeholders` only when needed.
- `config_flow.py`: an `AbstractOAuth2FlowHandler` subclass with `domain = DOMAIN` and a `logger` property; `async_oauth_create_entry` setting `unique_id`; `async_step_reauth` / `async_step_reauth_confirm` with `_abort_if_unique_id_mismatch` and `async_update_reload_and_abort`.
- Setup: token refresh through `OAuth2Session`, raising `ConfigEntryAuthFailed` on auth failure.
- `strings.json`: the `application_credentials:` dialog entries.

### 3) Validate and report

Validate offline (manifest dependency + `config_flow: true`; `async_get_authorization_server` with a valid `AuthorizationServer`; `AbstractOAuth2FlowHandler` with `domain = DOMAIN` using `async_oauth_create_entry` and setting `unique_id`; refresh through `OAuth2Session`; setup raises `ConfigEntryAuthFailed`; reauth path present; dialog translated under `application_credentials`; no YAML credentials). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/application-credentials` acceptance criteria, plus the changed file paths.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Generic user/password or API-key config flow → `ha-config-flow-augment`
- Greenfield scaffold → `ha-integration-scaffold`
- Coordinator wiring → `ha-coordinator-add`
- Deploy to live HA → out of scope
