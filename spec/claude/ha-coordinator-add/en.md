# Skill: `ha-coordinator-add`

Status: draft

## Context

A mature Custom Integration rarely starts with its final coordinator topology. Typical course: the initial scaffold ships a `<Domain>Coordinator` that works fine for plant / resource data; over time it becomes clear that alert / notification data needs a markedly shorter update interval (`60 s` instead of `300 s`), or that master data (tenants, locations) tolerates a longer interval because it changes rarely. At that point a mega-coordinator becomes friction — it polls either too often or too slowly for individual data sets.

This skill adds another coordinator to an existing integration without destroying the existing one. It bundles the cross-file edits (coordinator class, RuntimeData extension, `__init__.py` setup, `const.py` constants, `config_flow.py` options schema, tests) into an additive pattern.

## Scope

The skill adds **one** additional coordinator per call. It does not remove one, merge one, or change the update interval of an existing one. Existing platform modules stay unchanged; the new coordinator binding only affects platform modules the user explicitly names — the rest stay on the old coordinator.

## Goals

- Make the multi-coordinator topology from `ha/coordinator-patterns` introducible after the fact
- Ensure `RuntimeData.coordinators` mapping as the only lookup path — the new coordinator is not a separate `RuntimeData` field but an additional key in the mapping
- Configurable update intervals for the new coordinator from the start, with options-flow entry plus min cap
- Test coverage for the new coordinator (error mapping, happy path) as a mandatory part of delivery

## Non-Goals

- Coordinator removal or coordinator consolidation — manual task
- Splitting a mega-coordinator into multiple pieces in one call — step-by-step with the `add` skill
- Cross-coordinator data aggregation (platform reads from two coordinators) — separate follow-up spec if needed at all
- Push-based coordinators (webhook, MQTT, WebSocket) — separate follow-up spec

## Requirements

### Activation triggers

- **MUST** activate on:
  - "add a new coordinator for <role>"
  - "split the existing coordinator into <role> and <role>"
  - "add a faster polling coordinator for alerts"
  - "füge einen Coordinator für <Rolle> hinzu"
- **MUST NOT** activate on:
  - greenfield setup (`ha-integration-scaffold`)
  - coordinator removal (manual edit)
  - push-coordinator setup (separate spec planned)

### Inputs

- **MUST** collect:
  - `target_dir` — repo root of the integration
  - `role` — coordinator role name in lowercase ASCII (`alerts`, `tenants`, `metrics`, …) — used as the key in `RuntimeData.coordinators` mapping and the suffix in the coordinator class (`<Domain><Role>Coordinator`)
  - `default_interval` — default update interval in seconds
  - `min_interval` — minimum cap in seconds
  - `update_method` — name of the API method in `api.py` that `_async_update_data` calls (for example `async_get_alerts`)
- **SHOULD** collect:
  - `setup_method` — name of an optional `_async_setup` method for master-data load (default: none)
  - `data_type` — generic type for `DataUpdateCoordinator[<Type>]` (default: `list[dict[str, Any]]`)

### Pre-flight

- **MUST** check, aborting on failure:
  1. `target_dir` is a git repo with a clean working tree
  2. `target_dir/custom_components/<domain>/coordinator.py` exists
  3. A coordinator class named `<Domain><Role>Coordinator` does not yet exist
  4. The mapping key `role` does not yet exist in `RuntimeData.coordinators`
  5. `target_dir/custom_components/<domain>/api.py` contains the API method named in `update_method` (or the user is hinted to add it manually)

### Generator choreography

- **MUST** append a new `<Domain><Role>Coordinator(DataUpdateCoordinator[<DataType>])` class in `coordinator.py` that satisfies `ha/coordinator-patterns`: `config_entry`, `name=f"{DOMAIN}_<role>"`, `update_interval` from `entry.options` with min cap, `always_update=False`, error mapping (`ConfigEntryAuthFailed` / `UpdateFailed`), `async_timeout.timeout(...)` wrap
- **MUST** add constants in `const.py`: `CONF_POLL_<ROLE>`, `DEFAULT_POLL_<ROLE>`, `MIN_POLL_<ROLE>`
- **MUST** instantiate the new coordinator in `__init__.py` (`async_setup_entry`), call `async_config_entry_first_refresh()`, and extend the `runtime_data.coordinators` mapping (`{"<existing_role>": existing, "<role>": new}`) — the `RuntimeData` dataclass itself stays unchanged because the mapping already exists
- **MUST** add the new `CONF_POLL_<ROLE>` entry in `config_flow.py` (options flow) inside `OPTIONS_SCHEMA` with `vol.All(int, vol.Range(min=MIN_POLL_<ROLE>))`, default `DEFAULT_POLL_<ROLE>`
- **MUST** add the `options.step.init.data.poll_interval_<role>` string in `strings.json` and every `translations/<lang>.json`
- **MUST** add tests in `tests/test_coordinator.py`: auth error → `ConfigEntryAuthFailed`, connection error → `UpdateFailed`, happy path with a JSON fixture
- **MAY** create a new fixture file `tests/fixtures/<role>.json` when the API method returns structured responses

### Forbidden

- **MUST NOT** rename or modify the existing coordinator
- **MUST NOT** rewire platform modules — coordinator binding in the platforms remains a user task (two platforms could share the new coordinator role, that is the user's call)
- **MUST NOT** set the minimum cap below `30 s` without an explicit user warning — the skill warns when the user wants to set it below `30 s`

## Acceptance Criteria

- [ ] A new coordinator class appears in `coordinator.py`
- [ ] `const.py` carries `CONF_POLL_<ROLE>`, `DEFAULT_POLL_<ROLE>`, `MIN_POLL_<ROLE>`
- [ ] `__init__.py` instantiates the new coordinator, calls `async_config_entry_first_refresh()`, and extends the `runtime_data.coordinators` mapping
- [ ] `config_flow.py:OPTIONS_SCHEMA` carries the new `CONF_POLL_<ROLE>` entry
- [ ] `strings.json` and `translations/<lang>.json` carry the new options string
- [ ] `tests/test_coordinator.py` carries the three new tests (auth error, connection error, happy path)
- [ ] `pytest tests/test_coordinator.py` runs cleanly
- [ ] `ruff check custom_components/<domain>/` runs cleanly

## Open Questions

- **API method lookup**: Should the skill read `api.py` and suggest methods, or must the user name the method?
- **Push coordinator variant**: When does a follow-up spec require the webhook / MQTT coordinator path?
- **Cross-coordinator platforms**: How does the skill handle the case of a platform combining data from two coordinators? Currently excluded as a non-goal.
