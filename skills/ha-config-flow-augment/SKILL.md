---
name: ha-config-flow-augment
description: Augment an existing Home Assistant Custom Integration config flow with an additional pattern — multi-step tenant / account selection, zeroconf discovery, reauth flow, reconfigure flow, or OAuth as alternative to API key — non-destructively. Activate on phrasings like "add a multi-step tenant selection to the config flow", "add zeroconf discovery to the existing config flow", "add a reauth flow", "add reconfigure flow", "add OAuth login as alternative to API key", "erweitere den Config-Flow um Tenant-Auswahl". Do not activate for greenfield scaffolding (use ha-integration-scaffold), pure schema edits, or destructive refactors.
tags: [home-assistant, custom-integration, config-flow]
---

# HA Config Flow Augment

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-config-flow-augment/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-config-flow-augment/en.md).

## When this skill activates

Use this skill when the user wants to:

- retrofit a tenant / account selection step after the auth step
- retrofit zeroconf discovery into a config flow that did not initially carry it
- retrofit a reauth flow
- retrofit a reconfigure flow
- add OAuth as a parallel auth path next to the existing API-key path

## When NOT to activate

- greenfield integration scaffolding → `ha-integration-scaffold`
- pure schema edits (rename a field, change a default) → manual code edit
- destructive refactors (remove a step, rewrite a step) → manual code edit with explicit user approval
- schema migration of `entry.data` across versions → `ha-schema-migration` (planned)

## Hard rules

1. **Never overwrite existing flow steps.** Augment is additive. If the requested pattern already exists in `config_flow.py`, abort with "pattern already present".
2. **Never touch unrelated modules.** Allowed targets: `config_flow.py`, `strings.json`, `translations/<lang>.json`, `tests/test_config_flow.py`, and (for zeroconf) `manifest.json`. The only exception is `oauth`, which also writes a registration block in `__init__.py`.
3. **Never split the augment.** Code, strings, translations, manifest entry (where applicable), and tests land together in a single commit-ready state. Half augments where code exists but strings are missing are forbidden.
4. **Never invent backend specifics.** For `oauth`, the skill scaffolds the flow skeleton — token endpoint, authorize endpoint, scopes, client ID/secret stay user-fed. Surface them in the output as an explicit checklist.
5. **Always state the quality-scale impact.** The output names which Quality Scale tier the augment unlocks (Bronze → Silver for reauth, Silver → Gold for reconfigure, …).
6. **Verify HA internals against the official docs.** Don't reproduce HA API signatures, lifecycle hooks, conventions, or schemas from memory — when uncertain, consult the official docs before generating or relying on it: Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant), architecture/blueprint/YAML docs [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root of the existing integration |
| `pattern` | yes | — | one of `tenant-step`, `zeroconf`, `reauth`, `reconfigure`, `oauth` |
| `service_type` | only for `zeroconf` | `_<domain>._tcp.local.` | mDNS service-type string |
| `tenant_list_method` | only for `tenant-step` | — | API method on `api.py` that returns the tenant list (e.g. `async_get_tenants`) |
| `oauth_token_endpoint` | only for `oauth` | — | OAuth provider token endpoint URL |
| `oauth_authorize_endpoint` | only for `oauth` | — | OAuth provider authorize endpoint URL |
| `oauth_scopes` | only for `oauth` | `[]` | space-separated scope list |

## Pre-flight (every run, in order — abort on first failure)

1. `git -C <target_dir> rev-parse --is-inside-work-tree` returns true.
2. `git -C <target_dir> status --porcelain` is empty.
3. `<target_dir>/custom_components/<domain>/config_flow.py` exists. Read `domain` from `manifest.json`; do not ask the user.
4. The pattern is not already present:
   - `tenant-step`: `async_step_tenant` does not exist in the file
   - `zeroconf`: `async_step_zeroconf` does not exist in the file and `manifest.json:zeroconf` is not set
   - `reauth`: `async_step_reauth` does not exist
   - `reconfigure`: `async_step_reconfigure` does not exist
   - `oauth`: `AbstractOAuth2FlowHandler` is not in the imports / base classes

## Workflow

### 1) Resolve

Read `domain` from `manifest.json`. Resolve the pattern, and pattern-specific inputs. Print a one-paragraph summary of what will change. Wait for user confirmation.

### 2) Apply pattern

Append the relevant code, strings, manifest changes, and tests for the chosen pattern. Each pattern is documented in the spec — keep operations idempotent and additive.

| Pattern | Files touched |
|---|---|
| `tenant-step` | `config_flow.py`, `const.py` (new `CONF_TENANT_SLUG`), `strings.json`, `translations/*.json`, `tests/test_config_flow.py` |
| `zeroconf` | `config_flow.py`, `manifest.json`, `tests/test_config_flow.py`, `tests/conftest.py` (or `tests/helpers.py`) for `_make_zeroconf_info` helper |
| `reauth` | `config_flow.py`, `strings.json`, `translations/*.json`, `tests/test_config_flow.py` |
| `reconfigure` | `config_flow.py`, `strings.json`, `translations/*.json`, `tests/test_config_flow.py` |
| `oauth` | `config_flow.py`, `__init__.py` (provider registration), `strings.json`, `translations/*.json`, `tests/test_config_flow.py` |

### 3) Verify

```bash
ruff check custom_components/<domain>/
pytest tests/test_config_flow.py -v
```

Both must run cleanly. If they fail, surface the failing tool output and abort. Do not commit on the user's behalf — they own the commit.

### 4) Report

Output to the user:

1. files touched
2. defaults assumed (and which inputs are still pending the user, especially for `oauth`)
3. **quality-scale tier transition** — name it explicitly:
   - `reauth` → Bronze → Silver
   - `reconfigure` → Silver → Gold
   - `zeroconf` (for `iot_class: local_*`) → Bronze → Silver
   - `tenant-step` and `oauth` → no tier transition (refinements within the same tier)

## Boundaries to neighbouring skills

- Greenfield scaffold → `ha-integration-scaffold`
- Add a coordinator → `ha-coordinator-add` (planned)
- Test coverage augmentation → `ha-test-harness-augment` (planned)
- Schema migration of `entry.data` across versions → `ha-schema-migration` (planned)
- Provider-specific OAuth setup beyond the skeleton → consumer task; no dedicated skill planned
