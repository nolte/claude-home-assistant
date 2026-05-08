# Skill: `ha-config-flow-augment`

Status: draft

## Context

The initial scaffold (`ha-integration-scaffold`) ships a config flow with user / reauth / reconfigure / options steps and optionally zeroconf discovery. Real integrations regularly need follow-up extensions that the initial scaffold cannot cover generically: a second auth step for tenant or account selection, a second discovery source (DHCP, SSDP, MQTT, Bluetooth, USB), an OAuth flow as an alternative to API key, or migrating from API key to OAuth in a running setup.

This skill augments an existing `config_flow.py` with exactly these patterns, **additively** and **non-destructively** — existing steps are not overwritten, only new steps that hook into the existing flow are appended.

## Scope

The skill augments an **existing** `config_flow.py` of a Custom Integration. It does not scaffold a greenfield flow (`ha-integration-scaffold` does that) and does not strip existing steps from the code (that would be destructive refactoring requiring manual user approval). The skill identifies the desired augmentation pattern from the user's request and appends the required steps plus schema constants plus string entries plus tests.

## Goals

- Retrofit single config-flow patterns without forcing the user back through the initial-scaffold path
- Non-destructive extension: existing steps stay unchanged; only new steps and new schema constants land in the code
- Cross-file consistency for every added step: `config_flow.py` code, `strings.json` step strings, `translations/<lang>.json` mirrors, possibly `manifest.json` discovery keys, tests in `tests/test_config_flow.py`
- Make quality-scale transitions visible: a user → reauth augment lifts Bronze to Silver; a user → reconfigure augment lifts Silver to Gold

## Non-Goals

- Greenfield scaffold — `ha-integration-scaffold`
- Destructive refactors (step rewrites, step removal, schema reduction) — manual task
- Backend-specific OAuth provider configuration (token endpoint, scopes, client-ID auth) — the skill scaffolds the OAuth **flow** skeleton; concrete provider values are filled by the user
- Multi-account architecture beyond multi-step selection (for example one account with sub-accounts per service region) — separate follow-up spec when concretely needed

## Requirements

### Activation triggers

- **MUST** activate on the following phrases:
  - "add a multi-step tenant selection to the config flow"
  - "add zeroconf discovery to the existing config flow"
  - "add a reauth flow" (when not initially scaffolded)
  - "add reconfigure flow" (when not initially scaffolded)
  - "add OAuth login as alternative to API key"
  - "erweitere den Config-Flow um <Pattern>"
- **MUST NOT** activate on:
  - greenfield setup (`ha-integration-scaffold` owns that)
  - pure schema changes (rename a field, change a default) — code edit, not skill task
  - schema migration (`async_migrate_entry` logic) — separate skill (`ha-schema-migration`, planned) when needed

### Inputs

- **MUST** collect `target_dir` (the integration's repo root)
- **MUST** read `domain` from `manifest.json` without asking — the domain value is part of the existing code and reused in the augment
- **MUST** collect the desired augment pattern from this list:
  - `tenant-step` — second step after successful user auth that renders a selectable list of tenants / accounts
  - `zeroconf` — zeroconf discovery pre-fill for the existing user step
  - `reauth` — retrofit the reauth flow (reauth step + confirm step)
  - `reconfigure` — retrofit the reconfigure flow
  - `oauth` — OAuth flow as an additional auth path (parallel to the API-key path)
- **SHOULD** collect pattern-specific options:
  - For `zeroconf`: service-type string (default `_<domain>._tcp.local.`), required TXT records (default: `instance_id`, `version`, `api_path`, `scheme`)
  - For `tenant-step`: backend API method for tenant listing (for example `async_get_tenants`)
  - For `oauth`: backend token endpoint, default scopes (user fills the values)

### Pre-flight

- **MUST** check in this order, aborting on failure:
  1. `target_dir` is a git repo with a clean working tree
  2. `target_dir/custom_components/<domain>/config_flow.py` exists
  3. The desired augment pattern is not already present in the existing code (for example no existing `async_step_zeroconf` when the user wants to retrofit zeroconf) — on hit, abort with the hint "pattern already present"
- **MUST NOT** overwrite existing step code — append new methods only

### Augment patterns

#### `tenant-step`

- **MUST** insert a second flow step `async_step_tenant(self, user_input=None)` invoked after successful user auth
- **MUST** adjust the user step so that on success it returns `return await self.async_step_tenant()` instead of calling `async_create_entry` directly
- **MUST** fetch the backend tenant list (`api.<list-method>()`) inside the tenant step, render it as a `vol.In(tenant_choices)` schema, and after user selection feed it into `async_create_entry(title=..., data={..., CONF_TENANT_SLUG: tenant_slug})`
- **MUST** derive the `unique_id` from user input plus tenant slug (typically `f"{base_url}_{tenant_slug}"`)
- **MUST** extend `strings.json` with `config.step.tenant.{title,data,description}` and possibly `config.error.no_tenants`
- **MUST** add tests for single-tenant selection and multi-tenant selection in `tests/test_config_flow.py`

#### `zeroconf`

- **MUST** insert `async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo)`
- **MUST** set `manifest.json:zeroconf` to `[<service_type>]`
- **MUST** store discovery data as instance attributes (`self._discovered_url`, `self._discovered_instance_id`, `self._discovered_api_path`) between steps
- **MUST** insert a pre-fill path into the user step that uses `add_suggested_values_to_schema(SCHEMA, self._discovered_payload)` when the instance attributes are set
- **MUST** implement the re-discovery-with-IP-change path: `_abort_if_unique_id_configured(updates={CONF_HOST: ..., CONF_PORT: ..., CONF_API_PATH: ...})`
- **MUST** add tests for greenfield discovery and re-discovery-with-IP-change, plus a `_make_zeroconf_info(...)` helper in `tests/conftest.py` or `tests/helpers.py`

#### `reauth`

- **MUST** insert `async_step_reauth(self, entry_data: Mapping[str, Any])` and `async_step_reauth_confirm(self, user_input=None)`
- **MUST** check the coordinator path (`ha/coordinator-patterns`) — the coordinators must raise `ConfigEntryAuthFailed`, otherwise the reauth flow does not fire; if not yet present, surface a hint to the user (no auto-edit)
- **MUST** extend `strings.json` with `config.step.reauth_confirm.{title,data,description}` and `config.abort.reauth_successful`
- **MUST** add tests for the happy-path reauth and sad-path reauth (invalid_auth)

#### `reconfigure`

- **MUST** insert `async_step_reconfigure(self, user_input=None)`
- **MUST** load existing `entry.data` as suggested values (`self.add_suggested_values_to_schema(SCHEMA, self._get_reconfigure_entry().data)`)
- **MUST** use the same real validation as the user step — typically through a shared `_validate_input(hass, data)` helper
- **MUST** end with `async_update_reload_and_abort(self._get_reconfigure_entry(), data_updates={...})`
- **MUST** extend `strings.json` with `config.step.reconfigure.{title,data,description}`

#### `oauth`

- **MUST** introduce the OAuth flow as a parallel path next to the existing API-key path — the user step gains a choice between "API key" and "OAuth"
- **MUST** integrate `homeassistant.helpers.config_entry_oauth2_flow.AbstractOAuth2FlowHandler` as a second base class (or extend the ConfigFlow class via multiple inheritance, depending on the OAuth provider)
- **MUST** add the OAuth setup block in `__init__.py` (`hass.helpers.config_entry_oauth2_flow.async_register_implementation(...)`)
- **MUST** emit a list of values the user has to fill in manually in the skill-output docs (token endpoint, authorize endpoint, scopes, client ID, client secret)
- **SHOULD** end the skill output with a clear "provider-specific values are your job" hint

### Cross-file consistency

- **MUST** carry every added step simultaneously: code in `config_flow.py`, strings in `strings.json` and every `translations/<lang>.json`, possibly keys in `manifest.json`, tests in `tests/test_config_flow.py`
- **MUST** leave the augment in a single commit-ready state — no half augments where code is present but strings are missing

### Quality-scale marker in output

- **SHOULD** explicitly call out which quality-scale tier the augment reached in the skill output summary (`tenant-step` alone lifts nothing; `reauth` lifts Bronze to Silver; `reconfigure` lifts Silver to Gold; `zeroconf` lifts Bronze to Silver for local integrations — assuming `ha/coordinator-patterns` conformance is in place)

## Acceptance Criteria

- [ ] The skill modifies only `config_flow.py`, `strings.json`, `translations/<lang>.json`, possibly `manifest.json` and `tests/test_config_flow.py` — no changes to `coordinator.py`, `entity.py`, platform modules, or `__init__.py` except for `oauth`
- [ ] Existing steps in `config_flow.py` stay unchanged
- [ ] The added step satisfies the relevant `ha/config-flow-patterns` (or `ha/zeroconf-discovery`) requirement
- [ ] Translation strings stay in sync between `strings.json` and every `translations/<lang>.json`
- [ ] Tests for the new step run cleanly directly after the augment
- [ ] For `oauth`: the skill output contains an explicit list of provider-specific values the user must fill in manually
- [ ] The quality-scale tier transition is named in the output

## Open Questions

- **OAuth provider catalogue**: Should the skill ship a small catalogue of common OAuth providers (Google, GitHub, generic OAuth2) as templates, or does each provider stay a user task?
- **Reauth-trigger verification**: Currently the skill only hints that coordinators must raise `ConfigEntryAuthFailed`. Should it also read `coordinator.py` and verify, or does that stay a user task?
- **Tenant-listing API method**: Currently the user must name the method (`async_get_tenants`). Should the skill read `api.py` and generate method suggestions, or does that stay user input?
- **Multi-augment in one call**: Should the skill be able to apply multiple augment patterns sequentially (for example `tenant-step` + `zeroconf`) in one run, or does each augment stay a separate call?
- **API key → OAuth migration**: When the user wants to migrate an existing API-key flow to OAuth, that is a destructive change to `entry.data`. Should this skill cover it or open a dedicated `ha-auth-migration` spec?
