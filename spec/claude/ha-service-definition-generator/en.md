# Skill: `ha-service-definition-generator`

Status: draft

## Context

`ha/services` defines the pattern: `services.yaml` as the UI schema with selectors, handler in `__init__.py` or `services.py`, multi-instance disambiguation, idempotency guards, clean error mapping (`ServiceValidationError` for user errors, `HomeAssistantError` for internal errors), coordinator refresh after mutation. The initial scaffold phase ships no services because they are integration-specific. This skill adds them: per call, one service with defined fields, selectors, translation strings, icon, handler stub, and test.

## Scope

The skill adds one or more services to `services.yaml` plus a handler in `__init__.py` (or `services.py` once the service count goes beyond ~5). It does not delete services, does not merge service definitions, and does not modify an existing service schema — on conflict on the same `service` key it aborts.

## Goals

- Generate service definitions deterministically from a fields description — no free YAML edit that forgets selector conventions
- Pull multi-instance disambiguation in as the default pattern — the handler stub calls the `_resolve_entry` helper, which raises `ServiceValidationError` on ambiguity
- Idempotency-guard skeleton for mutating services — the handler reserves a slot for backend acknowledgement lookup
- Coordinator refresh after mutation as a mandatory call — `await coordinator.async_request_refresh()` is part of the handler stub for mutating services
- Cross-file consistency: `services.yaml`, `strings.json` (`services.<name>.name/description/fields.<f>.name/description`), `translations/<lang>.json`, `icons.json` (`services.<name>.service`)

## Non-Goals

- Backend mutation logic itself (which API endpoint, which payload construction, which response validation) — consumer task; the handler stub calls a backend method from `api.py` whose existence the skill verifies
- Service removal — manual task
- Service-response pattern (`return_response=True`) — separate follow-up spec once the first integration concretely needs it
- Cross-service state sharing — explicitly not wanted; every service call is atomic

## Requirements

### Activation triggers

- **MUST** activate on:
  - "add a service `<name>` that does <X>"
  - "add a `refresh_data` service"
  - "add a service to confirm a notification"
  - "füge einen Service `<name>` hinzu"
- **MUST NOT** activate on:
  - service removal
  - service-schema migration
  - greenfield scaffold

### Inputs

- **MUST** collect:
  - `target_dir`
  - `service_name` — lowercase snake_case ASCII (`refresh_data`, `confirm_notification`, …)
  - `description` — 1–2 sentences describing what the service does
  - `mutating` — bool; mutating services receive an idempotency guard and coordinator refresh
  - `fields` — list of field dicts with `name`, `selector_type` (`entity` / `select` / `number` / `text` / `boolean` / `target`), `required` (bool), `default` (optional), selector-specific options (`options` for `select`, `min`/`max`/`step` for `number`, …)
  - `coordinator_role` — when `mutating=true`: which coordinator key from `RuntimeData.coordinators` is refreshed after mutation
  - `api_method` — name of the backend API method in `api.py` the handler calls

### Pre-flight

- **MUST** check:
  1. `target_dir` is a git repo, clean
  2. `<target_dir>/custom_components/<domain>/services.yaml` (create it when absent — generator logic)
  3. service key `<service_name>` is not already in `services.yaml`
  4. `api.py` contains `api_method` (or surface a user todo)

### Generator choreography

- **MUST** add a new service entry in `services.yaml` — when the file does not yet exist, create it with YAML header and initial service
- **MUST** append the service schema (field validation) as a `voluptuous` schema in `__init__.py` (or `services.py` when present) — typically `<SERVICE>_SCHEMA = vol.Schema({...})`
- **MUST** add the handler stub as `async def _async_handle_<service_name>(call: ServiceCall) -> None` in `__init__.py` (or `services.py`), which:
  1. calls the `_resolve_entry(hass, call)` helper (create when absent)
  2. validates inputs from `call.data` against the schema (HA does this before the handler call, but the stub documents the fields)
  3. calls the backend API method with try / except on API-specific auth / connection exceptions
  4. on `mutating=true`: `await entry.runtime_data.coordinators[<coordinator_role>].async_request_refresh()`
  5. converts auth errors into `ServiceValidationError("invalid_auth")`
- **MUST** call `hass.services.async_register(DOMAIN, "<service_name>", _async_handle_<service_name>, schema=<SERVICE>_SCHEMA)` in `async_setup_entry` (or a dedicated service-setup function)
- **MUST** add translation keys in `strings.json` and every `translations/<lang>.json` for `services.<service_name>.name`, `services.<service_name>.description`, `services.<service_name>.fields.<field>.name`, `services.<service_name>.fields.<field>.description`
- **MUST** add `services.<service_name>.service` with a fitting Material Design icon in `icons.json`
- **MUST** add a test block for the service in `tests/` — typically in `tests/test_services.py` (create when absent) — with tests for: successful call, missing disambiguation, auth error

### Forbidden

- **MUST NOT** overwrite existing services
- **MUST NOT** include generic `Exception` catches in the handler stub
- **MUST NOT** include background tasks or long-running logic in the handler — services are short and synchronous-feel; background work belongs in the coordinator

## Acceptance Criteria

- [ ] `services.yaml` carries the new service entry with every field and selector
- [ ] `__init__.py` (or `services.py`) carries `<SERVICE>_SCHEMA` and the handler stub
- [ ] `_resolve_entry` helper is available (create when absent)
- [ ] `hass.services.async_register(...)` is called
- [ ] Translation keys exist in `strings.json` and every `translations/<lang>.json`
- [ ] `services.<service>.service` icon is in `icons.json`
- [ ] Tests for the service run cleanly
- [ ] `ruff check custom_components/<domain>/` runs cleanly

## Open Questions

- **`services.py` vs. inline in `__init__.py` threshold**: Currently formulated as "up to ~5 services in `__init__.py`, after that `services.py`"; a concrete threshold is missing.
- **Default-icon selection**: Should the skill heuristically pick the icon from the service name, or must the user supply it? Currently formulated as "fitting mdi:" without clear logic.
- **Backend-method lookup**: Should the skill read `api.py` and produce method suggestions?
- **`return_response` variant**: When does a follow-up spec require the response pattern?
