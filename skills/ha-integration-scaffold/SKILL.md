---
name: ha-integration-scaffold
description: Scaffold a complete Home Assistant Custom Integration skeleton — manifest, lifecycle, config flow, coordinator, entity, platforms, translations, icons, diagnostics, plus pytest harness — in one go, conformant to every MUST pattern in spec/ha/*. Activate on phrasings like "scaffold a new HA Custom Integration", "create a Home Assistant integration", "neue HA-Integration scaffolden", "skeleton einer HA Custom Integration anlegen", "bootstrap a new HACS-compatible integration". Do not activate when the user only edits an existing integration, scaffolds a Lovelace card, scaffolds an ESPHome component, scaffolds a blueprint, or asks for a YAML-to-config-flow migration — those have their own skills.
tags: [home-assistant, custom-integration, scaffolding]
---

# HA Integration Scaffold

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-integration-scaffold/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-integration-scaffold/en.md).

## When this skill activates

Use this skill when the user wants to:

- bootstrap a brand-new HA Custom Integration in an empty consumer repo
- get a runnable, lint-clean, test-passing skeleton without having to read every `spec/ha/*` spec first
- start an integration that targets HACS distribution

## When NOT to activate

- editing an existing `custom_components/<domain>/` → there is no scaffold to do; consult the relevant detail spec under `spec/ha/*`
- scaffolding a Lovelace card → separate skill `ha-lovelace-card-scaffold` (planned)
- scaffolding an ESPHome custom component → separate skill `ha-esphome-component-scaffold` (planned)
- scaffolding a blueprint / automation → separate skill (planned)
- migrating a YAML-configured integration to config flow → separate skill (planned, only on demand)

## Hard rules

1. **Never overwrite an existing `custom_components/<domain>/`.** If the directory exists, abort with the path quoted. Collision is a user-disambiguation problem, not a generator problem.
2. **Never use `hass.data[DOMAIN]`.** Every setup artefact lives in typed `entry.runtime_data` (see [`ha/runtime-data-pattern`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/runtime-data-pattern/de.md)). The generated `__init__.py` is the single source of this contract.
3. **Never set `_attr_name = "<string>"` on a generated entity.** All entity names live in `strings.json` under `entity.<platform>.<translation_key>.name` (see [`ha/translations`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/translations/de.md)). Hard-coded names break translation and stable `entity_id` slugs.
4. **Never set `self.entity_id = "..."`.** HA derives the `entity_id` from the system-language display name at first registration. The skeleton stays English-source so the slug remains language-independent (see [`ha/entity-architecture`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-architecture/de.md)).
5. **Never bypass the API path whitelist.** Generated `api.py` carries `_API_PATH_RE` and a `_with_auth(headers)` helper; bearer tokens go on the wire only after the path has passed the whitelist (see [`ha/security-hardening`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/security-hardening/de.md)).
6. **Never silently default.** When the user did not specify `hacs` / `zeroconf` / `auth` / `platforms`, fall back to documented defaults — but state every default in the output summary so the user sees what was assumed.
7. **Name every artefact per `ha/naming-conventions`.** The integration `domain`, `unique_id`, `translation_key`, device `identifiers`, service names, config-entry title, and all generated file paths follow the consolidated naming authority — `snake_case` identifiers, English display names (≤ 50 chars), no volatile data (IP, hostname, token, timestamp) in any ID (see [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)). Rules 3–4 are the entity-name instances of this authority.
8. **Verify HA internals against the official docs.** Don't reproduce HA API signatures, lifecycle hooks, conventions, or schemas from memory — when uncertain, consult the official docs before generating or relying on it: Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant), architecture/blueprint/YAML docs [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `domain` | yes | — | lowercase ASCII slug (`[a-z0-9_]+`); folder name, `manifest.json:domain`, `DOMAIN` constant |
| `name` | yes | — | human-readable display name |
| `description` | yes | — | 1–2 sentences for `manifest.json` and `plan.md` |
| `codeowner` | yes | — | GitHub handle with `@` prefix |
| `integration_type` | yes | — | one of `hub`, `device`, `service` |
| `iot_class` | yes | — | one of `local_polling`, `local_push`, `cloud_polling`, `cloud_push`, `assumed_state`, `calculated` |
| `target_dir` | yes | — | repo-root path; the consumer must have a clean git repo here |
| `hacs` | no | `true` | generate `hacs.json` |
| `zeroconf` | no | `false` | generate `async_step_zeroconf` plus `manifest.json:zeroconf` |
| `auth` | no | `true` | generate reauth flow |
| `platforms` | no | `["sensor"]` | list of HA platforms to scaffold |

If the user is silent on `hacs`, `zeroconf`, `auth`, or `platforms`, use the defaults but state them explicitly in the output.

## Pre-flight (every run, in order — abort on first failure)

1. `git -C <target_dir> rev-parse --is-inside-work-tree` returns true. If not, instruct the user to `git init` first.
2. `git -C <target_dir> status --porcelain` returns empty. If the working tree is dirty, abort and tell the user to commit or stash first.
3. `<target_dir>/custom_components/<domain>/` does not exist. If it does, abort with the path quoted.
4. `<target_dir>/manifest.json` (at repo root) does not exist. A root-level `manifest.json` indicates an HA add-on layout, not a Custom Integration — abort and explain.

## Workflow

### 1) Resolve and confirm

Resolve every input including defaults. Print a one-paragraph summary listing exactly what will be scaffolded:

- which platforms (`sensor`, `binary_sensor`, …)
- whether HACS / zeroconf / reauth are on
- the resulting `manifest.json:domain`, `integration_type`, `iot_class`

Wait for user confirmation. This is the only approval gate — the rest of the workflow is bulk-write.

### 2) Generate `custom_components/<domain>/`

Write these files (every file is mandatory unless marked optional):

- `manifest.json` — every required field per [`ha/integration-architecture`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/integration-architecture/de.md)
- `__init__.py` — `async_setup_entry` + `async_unload_entry` with `runtime_data` ([`ha/runtime-data-pattern`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/runtime-data-pattern/de.md))
- `const.py` — `DOMAIN`, `PLATFORMS`, `CONF_*`, `DEFAULT_POLL_*` / `MIN_POLL_*`
- `api.py` — API client skeleton with path whitelist + bearer gating ([`ha/security-hardening`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/security-hardening/de.md))
- `config_flow.py` — user flow + (when `auth=true`) reauth + reconfigure + options flow ([`ha/config-flow-patterns`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/config-flow-patterns/de.md)); when `zeroconf=true`, additionally `async_step_zeroconf` ([`ha/zeroconf-discovery`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/zeroconf-discovery/de.md))
- `coordinator.py` — `<Domain>Coordinator` with error mapping ([`ha/coordinator-patterns`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/coordinator-patterns/de.md))
- `entity.py` — base entity + DeviceInfo factories ([`ha/entity-architecture`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-architecture/de.md), [`ha/device-registry`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/device-registry/de.md))
- one platform module per entry in `platforms` (default: `sensor.py`)
- `strings.json` — English source ([`ha/translations`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/translations/de.md))
- `translations/en.json` and `translations/de.json` — mirrors of `strings.json`
- `icons.json` — icon mappings ([`ha/icons`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/icons/de.md))
- `diagnostics.py` — redaction hook with `TO_REDACT` ([`ha/diagnostics`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/diagnostics/de.md))
- `services.yaml` (optional, only when services are explicitly requested)
- `hacs.json` at the repo root (when `hacs=true`)

Cross-file consistency invariants — verify before writing:

- the same `<domain>` everywhere it appears
- the same coordinator key in `__init__.py` and every platform module
- the same `translation_key` in `strings.json`, `translations/<lang>.json`, `icons.json`, and the `EntityDescription` instances
- the same `unique_id` format string across every platform module

### 3) Generate `tests/`

Write:

- `tests/conftest.py` — `mock_config_entry_data` + API mock fixture using `load_fixture` ([`ha/test-harness`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/test-harness/de.md))
- `tests/test_config_flow.py` — user-flow happy path, user-flow sad path; reauth tests when `auth=true`
- `tests/test_coordinator.py` — `ConfigEntryAuthFailed` and `UpdateFailed` mappings
- `tests/test_init.py` — `async_setup_entry` / `async_unload_entry` lifecycle
- `tests/test_diagnostics.py` — `TO_REDACT` redaction check
- `tests/fixtures/health.json` — sample API response
- `pytest.ini` (or `[tool.pytest.ini_options]` if `pyproject.toml` exists) with `asyncio_mode = auto`
- pin `pytest-homeassistant-custom-component` in `requirements-dev.txt` (if missing)

### 4) Verify

Run, in this order, surface failures back to the user:

```bash
ruff check custom_components/<domain>/
pytest tests/ -v
```

Both must run without errors. If they fail, the generator produced inconsistent output — abort and quote the failing tool output.

### 5) Write `plan.md`

At `target_dir/plan.md`, with these sections:

- **Spec coverage** — table mapping every generated file to the relevant `spec/ha/*` requirement
- **Quality scale state** — Bronze / Silver markers reached out of the box; what the consumer still has to fill in for Gold / Platinum
- **Next steps** — concrete edit list (fill API endpoints in `api.py`, populate `EntityDescription` tuples with real datapoints, augment `tests/fixtures/`)
- **Open questions** — inherited from the relevant `spec/ha/*` Open Questions sections

## Output to the user

Return a brief summary listing:

1. files written (counted)
2. defaults that were assumed (when the user did not specify them)
3. the path to `plan.md`
4. one-line note that hassfest validation should run as part of CI (`hacs/action@main` is configured in the project-structure scaffold)

## Boundaries to neighbouring skills

- API endpoint logic → consumer task; no dedicated skill planned
- Config flow extension beyond the defaults → `ha-config-flow-augment` (planned)
- Add a second coordinator → `ha-coordinator-add` (planned)
- Lovelace card scaffold → `ha-lovelace-card-scaffold` (planned)
- Test coverage augmentation → `ha-test-harness-augment` (planned)
- Deploy and verify against a Kind cluster → agents `ha-integration-deploy` / `ha-integration-verify` (planned)
- Repo project structure (Taskfile, pre-commit, .github/workflows, mkdocs) → `nolte-shared:project-structure-apply`
