---
name: ha-service-definition-generator
description: Add an HA service to an existing Custom Integration — services.yaml entry with typed selectors, voluptuous schema, handler stub with multi-instance disambiguation and coordinator refresh, translations, icon, and tests. Activate on phrasings like "add a service `<name>`", "add a `refresh_data` service", "füge einen Service `<name>` hinzu". Do not activate for service removal, service-schema migration, or greenfield scaffolding.
tags: [home-assistant, custom-integration, services]
---

# HA Service Definition Generator

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-service-definition-generator/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-service-definition-generator/en.md).

## When this skill activates

Use this skill to add one HA service per call to an existing Custom Integration. Examples: a refresh button that re-polls all coordinators, a confirmation service that marks a notification as handled, a record-event service.

## When NOT to activate

- removing a service → manual code edit
- migrating a service schema → manual code edit with explicit user approval
- greenfield scaffold → `ha-integration-scaffold`

## Hard rules

1. **Never overwrite existing services.** Conflict on `service` key aborts with the conflicting key quoted.
2. **Always use typed selectors.** `entity` with `integration: <DOMAIN>`, `select` with `options` list, `number` with `min`/`max`/`step`. Never free string fields.
3. **Always raise `ServiceValidationError` on user error and `HomeAssistantError` on internal.** Generic `except Exception:` is forbidden in the handler.
4. **Always include `_resolve_entry` for multi-instance safety.** The handler must abort with a clear error when multiple config entries match.
5. **Always refresh coordinator after mutation.** `mutating=true` services call `await entry.runtime_data.coordinators[<role>].async_request_refresh()` before returning.
6. **Name services per `ha/naming-conventions`.** The `service` key is `snake_case` under the integration `domain`, with matching `services.yaml`/translation keys and English field labels (see [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)).
7. **Verify HA internals against the official docs.** Don't reproduce HA API signatures, lifecycle hooks, conventions, or schemas from memory — when uncertain, consult the official docs before generating or relying on it: Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant), architecture/blueprint/YAML docs [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root |
| `service_name` | yes | — | lowercase snake_case ASCII |
| `description` | yes | — | 1–2 sentences |
| `mutating` | yes | — | bool; affects idempotency + refresh stub |
| `fields` | yes | — | list of `{name, selector_type, required, default?, options?, min?, max?, step?}` |
| `coordinator_role` | when `mutating=true` | — | key in `RuntimeData.coordinators` to refresh |
| `api_method` | yes | — | backend method on `api.py` the handler calls |

## Pre-flight

1. `git -C <target_dir> rev-parse --is-inside-work-tree` and clean working tree
2. Read `domain` from `manifest.json`
3. `<target_dir>/custom_components/<domain>/services.yaml` exists or will be created
4. Service key `<service_name>` is not in `services.yaml`
5. `api.py` contains `api_method` (or surface a user todo)

## Workflow

### 1) Resolve and confirm

Print the resolved service definition, the field selectors, the icon choice. Wait for user confirmation.

### 2) Apply edits

- `services.yaml` — append the service entry
- `__init__.py` (or `services.py` when ≥5 services exist) — `<SERVICE>_SCHEMA` (voluptuous), `_async_handle_<service_name>(call)` stub, `hass.services.async_register(...)` in `async_setup_entry`
- `_resolve_entry` helper — create when absent
- `strings.json` and every `translations/<lang>.json` — service + field labels
- `icons.json` — `services.<service>.service`
- `tests/test_services.py` (create when absent) — happy path, missing disambiguation, auth error

### 3) Verify

```bash
ruff check custom_components/<domain>/
pytest tests/test_services.py -v
```

### 4) Report

- files touched
- placeholder backend method call (if `api_method` was missing — user must implement it)
- icon used (and let the user override if needed)

## Boundaries

- Greenfield scaffold → `ha-integration-scaffold`
- Backend method implementation → user task
- Service removal → manual code edit
- Service-response (`return_response=True`) pattern → separate spec planned
