# Skill: `ha-integration-scaffold`

Status: draft

## Context

A greenfield setup of a Home Assistant Custom Integration consists of about twelve mandatory files (see `ha/integration-architecture`) whose contents depend on each other: `manifest.json:domain` matches the folder name, the translation key in `strings.json` matches `_attr_translation_key` in the platforms, the icon entry in `icons.json` matches the same translation key, the `runtime_data` type alias in `__init__.py` matches the imports in the platforms. Manual scaffolding systematically produces drift at exactly these interfaces — the translation key is spelled differently in code than in `strings.json`, the icon mapping forgets a platform, the coordinator lookup key diverges between `__init__.py` and `sensor.py`.

This skill distils the nolte conventions (codified in the `spec/ha/*` specs) into a deterministic generator that produces a complete Custom Integration skeleton in one go, without consumers having to verify cross-file consistency by hand afterwards.

## Scope

The skill scaffolds a **greenfield skeleton** for an HA Custom Integration. It does not modify an existing `custom_components/<domain>/`, does not refactor an existing integration, and does not migrate from an old layout to the nolte style. Pure edits on an existing integration go through the relevant detail spec (`ha/config-flow-patterns`, `ha/coordinator-patterns`, …) plus code-edit steps; they are not the job of this skill.

## Goals

- Produce a Custom Integration skeleton that satisfies every MUST pattern in `spec/ha/*` from the start — Bronze / Silver of the HA quality scale is reached out of the box
- Guarantee cross-file consistency: same `domain`, same `translation_key`, same coordinator key across manifest.json, `__init__.py`, `const.py`, `config_flow.py`, `coordinator.py`, `sensor.py`, `strings.json`, `translations/`, `icons.json`, `diagnostics.py`, tests
- Get the consumer into a runnable, lint-clean, test-passing state without having to read the detail specs first — the specs remain the canonical source; the skill is the tooling entry point
- Emit a `plan.md` annotation that shows the consumer which file embodies which spec — mapping between code and `spec/ha/*` patterns

## Non-Goals

- Backend API client logic — the skill ships an API client skeleton with path whitelist and bearer gating (see `ha/security-hardening`); the concrete API operation logic (which endpoints, which JSON schema) remains a consumer task
- HACS distribution setup — `hacs.json` is generated optionally, but the HACS submission process (repo listing at HACS) is out of scope
- ESPHome or add-on scaffolding — separate follow-up skills (`ha-esphome-component-scaffold`, `ha-addon-scaffold`)
- Lovelace card scaffolding — separate skill (`ha-lovelace-card-scaffold`); the cards land under `custom_components/<domain>/www/` but are produced by a dedicated skill
- Migration of an existing YAML-configured integration to config flow — separate follow-up skill if needed at all
- Multi-tenant-specific setup logic — the skill scaffolds the user step plus an optional tenant step as a generic multi-step flow; tenant-specific logic is filled in by the consumer

## Requirements

### Activation triggers

- **MUST** activate on the following phrases:
  - "scaffold a new HA Custom Integration"
  - "create a Home Assistant integration"
  - "neue HA-Integration scaffolden"
  - "skeleton einer HA Custom Integration anlegen"
  - "bootstrap a new HACS-compatible integration"
- **MUST NOT** activate on:
  - pure edits of an existing integration (domain already under `custom_components/`)
  - Lovelace card creation (different skill)
  - blueprint / automation creation (different skill)
  - ESPHome custom component (different skill)
  - migration of a YAML-config integration to config flow (different skill)

### Inputs

- **MUST** collect the following mandatory inputs before writing anything:
  - `domain` — lowercase ASCII slug (`[a-z0-9_]+`); identifies the integration uniquely in the HA frontend, the service namespace, and the translation-key prefix
  - `name` — human-readable display name (for example "Acme Plant Manager")
  - `description` — 1–2 sentence description for `manifest.json` and `README.md`
  - `codeowner` — GitHub handle with `@` prefix (at least one)
  - `integration_type` — one of `hub`, `device`, `service` (see `ha/integration-architecture`)
  - `iot_class` — one of `local_polling`, `local_push`, `cloud_polling`, `cloud_push`, `assumed_state`, `calculated`
  - `target_dir` — the repository-root path the skeleton is written into (typically an empty or freshly created consumer repo)
- **SHOULD** collect the following options before writing — defaults when the user does not answer:
  - `hacs` (default `true`) — generate `hacs.json` alongside
  - `zeroconf` (default `false`) — generate the zeroconf discovery step in `config_flow.py`; also sets `manifest.json:zeroconf`
  - `auth` (default `true`) — generate the reauth flow; on `false`, no reauth step is generated
  - `platforms` (default `["sensor"]`) — list of HA platforms to scaffold
- **MUST NOT** use defaults without explicitly mentioning them in the output summary

### Pre-flight (every run)

- **MUST** check in this order, aborting on any failed step:
  1. `target_dir` is a git repository (`git rev-parse --is-inside-work-tree`)
  2. The working tree in `target_dir` is clean (no uncommitted changes)
  3. `target_dir/custom_components/<domain>/` does not yet exist — collision avoidance; on hit, abort with a path quote
  4. `target_dir/manifest.json` (at repo root) does not exist — a root-level `manifest.json` is a different layout (typically an add-on) and would conflict
- **MUST NOT** initialise the repository or commit for the user — the consumer owns git init and the initial commit

### Generator choreography

The skill writes these files in one go (no per-file user approval — bulk approval is implicit through the skill invocation):

- **Mandatory (always)**:
  - `custom_components/<domain>/manifest.json` — every required field per `ha/integration-architecture`
  - `custom_components/<domain>/__init__.py` — `async_setup_entry` + `async_unload_entry` with `runtime_data` (see `ha/runtime-data-pattern`)
  - `custom_components/<domain>/const.py` — `DOMAIN`, `PLATFORMS`, `CONF_*` keys, `DEFAULT_POLL_*` / `MIN_POLL_*` defaults
  - `custom_components/<domain>/api.py` — API client skeleton with `_API_PATH_RE` whitelist and `_with_auth` helper (see `ha/security-hardening`)
  - `custom_components/<domain>/config_flow.py` — user flow plus reauth (when `auth=true`) plus reconfigure plus options flow (see `ha/config-flow-patterns`)
  - `custom_components/<domain>/coordinator.py` — a `<Domain>Coordinator` class with error mapping (see `ha/coordinator-patterns`)
  - `custom_components/<domain>/entity.py` — base entity class plus DeviceInfo factory functions (see `ha/entity-architecture` and `ha/device-registry`)
  - `custom_components/<domain>/<platform>.py` for each platform in `platforms` — `EntityDescription` tuple list plus generic entity class (see `ha/entity-architecture`)
  - `custom_components/<domain>/strings.json` — English source strings for config flow, entities, services where applicable (see `ha/translations`)
  - `custom_components/<domain>/translations/en.json` — mirror of `strings.json`
  - `custom_components/<domain>/translations/de.json` — German translation
  - `custom_components/<domain>/icons.json` — icon mappings for entities (see `ha/icons`)
  - `custom_components/<domain>/diagnostics.py` — redaction hook with `TO_REDACT` set (see `ha/diagnostics`)
  - `tests/conftest.py` — shared fixtures (`mock_config_entry_data`, `mock_api`) (see `ha/test-harness`)
  - `tests/test_config_flow.py` — happy / sad path tests for the user flow
  - `tests/test_coordinator.py` — error-mapping tests
  - `tests/test_init.py` — lifecycle test for setup / unload
  - `tests/test_diagnostics.py` — redaction test
  - `tests/fixtures/health.json` — sample API response as a test fixture
  - `pytest.ini` (or appended to `pyproject.toml`) — `asyncio_mode = auto`
- **Optional based on inputs**:
  - `hacs.json` (when `hacs=true`) — `name`, `render_readme: true`, `homeassistant: <version>`
  - `services.yaml` plus service handler stub in `__init__.py` (when `platforms` includes a service-emitting platform type or the user explicitly asks for services)
  - `__init__.py` auto-registration block for Lovelace cards (when `lovelace=true` — default `false`)

### Cross-file consistency

- **MUST** use the same `<domain>` value across every generated file:
  - folder name under `custom_components/`
  - `manifest.json:domain`
  - `DOMAIN` constant in `const.py`
  - `domain` class attribute in `ConfigFlow`
  - logger name (`custom_components.<domain>`)
- **MUST** use the same coordinator key between `__init__.py` (`runtime_data.coordinators["<key>"]`) and the platform modules (`entry.runtime_data.coordinators["<key>"]`)
- **MUST** use the same translation key across `EntityDescription.translation_key` (in the platform modules), `strings.json` (`entity.<platform>.<key>.name`) and `icons.json` (`entity.<platform>.<key>.default`)
- **MUST** use the same `unique_id` format string across every platform module: `f"{entry.entry_id}_<resource>_<slug>_<descriptor>"`

### `plan.md` annotation

- **MUST** write a `plan.md` at the root of `target_dir` after scaffolding, containing the following sections:
  - **Spec coverage** — mapping "<file> satisfies <spec/ha/* slug> requirement X" for every generated file
  - **Quality scale state** — what is Bronze / Silver / Gold conformant from the skeleton and what the consumer still has to fill in
  - **Next steps** — the concrete edit list (fill API endpoints in `api.py`, fill platform `EntityDescription` tuples with real datapoints, augment backend tests in `tests/fixtures/`)
  - **Open questions** — the inherited open-question items from the involved `spec/ha/*` specs that demand consumer decision

### Boundaries to neighbouring skills

- **API client specifics** (real endpoints, real schemas, real validation logic) → no dedicated skill planned; consumer task
- **Config flow augmentations** beyond the default (multi-step tenants, custom discovery) → separate skill `ha-config-flow-augment` (planned)
- **Coordinator topology extension** beyond the single coordinator → separate skill `ha-coordinator-add` (planned)
- **Lovelace card scaffold** → separate skill `ha-lovelace-card-scaffold` (planned)
- **Test coverage beyond the default skeleton** → separate skill `ha-test-harness-augment` (planned)
- **Deploy / verify into the Kind cluster** → agents `ha-integration-deploy` / `ha-integration-verify` (planned)

## Acceptance Criteria

- [ ] The skill scaffolds `custom_components/<domain>/` with every mandatory file from the generator-choreography block
- [ ] The skill scaffolds `tests/` with the four mandatory tests (`test_config_flow`, `test_coordinator`, `test_init`, `test_diagnostics`)
- [ ] `manifest.json:domain` matches the folder name under `custom_components/`
- [ ] `pytest tests/` runs cleanly directly after scaffold (tests against the mock API)
- [ ] `ruff check custom_components/<domain>/` runs cleanly directly after scaffold
- [ ] hassfest (via `hacs/action@main`) validates the scaffolded integration without errors
- [ ] The skill aborts when `target_dir/custom_components/<domain>/` already exists
- [ ] The skill writes a `plan.md` with spec-coverage mapping, quality-scale state, next steps, and open questions
- [ ] `runtime_data` is typed via `@dataclass`; no occurrence of `hass.data[DOMAIN]` in the code
- [ ] `_attr_has_entity_name = True` on the base entity class; no occurrence of `_attr_name = "<hardcoded>"` in the platform modules
- [ ] Translation keys are consistent across `strings.json`, `translations/<lang>.json`, `icons.json`, and platform code

## Open Questions

- **Service-definition threshold**: When does the skill scaffold `services.yaml`? Currently formulated as "when the user explicitly asks for services" — a heuristic (for example "always when `integration_type=hub`") would be more concrete.
- **Multi-coordinator default**: Today the skill scaffolds a single coordinator. Should it automatically create a second coordinator (alerts at a shorter interval) on `iot_class=local_polling` and `integration_type=hub`, or does that stay a consumer task?
- **`requirements` skeleton**: Should the skill set `aiohttp` as a default requirement in `manifest.json`, or does that stay a user task? `kamerplanter-ha` has an empty `requirements` array because the API client uses the `aiohttp` shipped by HA.
- **`README.md` scaffold**: Should the skill produce a `README.md` for the consumer repo, or is the consumer README out of scope? Currently not on the mandatory list.
- **CI workflow scaffold**: Should the skill produce `.github/workflows/ci.yml`, or is that the job of `nolte-shared:project-structure-apply`? The latter is cleaner (separation of responsibility), but then the user has to call two skills in succession.
- **`plan.md` format threshold**: How structured is `plan.md`? Currently formulated as a formless mapping; a mandatory template would be more concrete but rigid.
