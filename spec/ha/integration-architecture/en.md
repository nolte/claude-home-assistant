# HA Integration: Architecture Foundation

Status: draft

## Context

A Home Assistant Custom Integration is a reproducible on-disk shape: a `custom_components/<domain>/` folder with `manifest.json` as the contract, lifecycle entry points in `__init__.py`, optional `config_flow.py`, `coordinator.py`, `entity.py`, platform-specific modules (`sensor.py`, `binary_sensor.py`, …), `services.yaml`, `strings.json` plus `translations/`, and `icons.json`. Skills that scaffold this shape or generate individual parts need an authoritative frame of reference — otherwise either generic HA boilerplate emerges that violates nolte conventions, or skill-specific quirks drift away from the consumer repo `nolte/kamerplanter-ha`, which has already validated these patterns with ~5,400 LOC of implementation and ~11,000 LOC of its own specs.

This spec is the **foundation spec** for every other HA spec in this plugin: it defines the mandatory files, the manifest schema, the choice of `integration_type` and `iot_class`, the lifecycle entry points, and the convention for marking quality scale per pattern. Detail specs for `runtime_data`, config flow, coordinator, entity architecture, services, translations, icons, and zeroconf discovery cross-reference back to here.

## Goals

- Specify a predictable on-disk layout for every HA Custom Integration that humans and skills can navigate
- Name the mandatory `manifest.json` fields and their allowed values exactly, so skill output passes the hassfest validator
- Make the choice of `integration_type` and `iot_class` decidable rather than vibes-based
- Pin the lifecycle entry points (`async_setup_entry`, `async_unload_entry`) so detail specs can build on them
- Establish a convention for explicitly marking the HA quality scale (Bronze / Silver / Gold / Platinum) per pattern, so skill consumers know which tier their generated code lands at
- Cleanly model the jump from the `nolte/kamerplanter-ha` implementation to generic, domain-agnostic skills, without inheriting kamerplanter-specific terms

## Non-Goals

- Detailed prescriptions for `config_flow.py`, `coordinator.py`, `entity.py`, `services.yaml`, `strings.json`/`translations/`, `icons.json`, zeroconf/DHCP/SSDP/MQTT discovery, diagnostics, or Lovelace cards — these live in dedicated follow-up specs
- Test harness shape (pytest, `pytest-homeassistant-custom-component`, fixtures) — owned by `ha/test-harness`
- Local dev workflow (Kind cluster, `kubectl cp`, `kill 1` instead of `delete pod`) — owned by `ha/dev-environment`
- HA add-on specification (Supervisor, s6 init, `config.yaml`) — different skill axis, different spec
- ESPHome custom components — different skill axis, different spec
- HA Core acceptance process (PR lifecycle in `home-assistant/core`) — Custom Integration scope, not Core scope

## Requirements

### Repository layout

- **MUST** place integration code under `custom_components/<domain>/`, where `<domain>` carries the value of `manifest.json:domain`
- **MUST** include at least these two files in the domain folder: `manifest.json` and `__init__.py`
- **SHOULD** additionally include the following once the corresponding functionality exists:
  - `const.py` (domain constants — `DOMAIN`, `CONF_*`, `DEFAULT_*`, `MIN_*`, `EVENT_*`, `SERVICE_*`)
  - `config_flow.py` (see `ha/config-flow-patterns`)
  - `coordinator.py` (see `ha/coordinator-patterns`)
  - `entity.py` (see `ha/entity-architecture`)
  - `services.yaml` plus service handlers in `__init__.py` or `services.py` (see `ha/services`), as soon as the integration exposes HA services
  - `strings.json` plus `translations/<lang>.json` for every shipped language (see `ha/translations`)
  - `icons.json` (see `ha/icons`)
- **MAY** additionally include:
  - Platform modules such as `sensor.py`, `binary_sensor.py`, `button.py`, `switch.py`, `number.py`, `select.py`, `calendar.py`, `todo.py` — one per HA platform used
  - `diagnostics.py` (see `ha/diagnostics`)
  - `repairs.py`
  - `system_health.py`
  - `api.py` or an API-client subpackage
  - `www/` with custom Lovelace cards (auto-registered in `__init__.py`; see `ha/lovelace-card-patterns`)
- **MUST NOT** place primary integration code outside `custom_components/<domain>/`; loose modules at the repository root are reserved for tooling, tests, and docs

### HACS integration (optional)

- **MAY** include an `hacs.json` at the repository root if the integration ships through HACS
- **MUST** set at least `name` in `hacs.json` when the file is present
- **SHOULD** set `render_readme: true` in `hacs.json`, so HACS renders the repo's `README.md` as description
- **SHOULD** set a `homeassistant` minimum-version pin in `hacs.json` (see Open Questions for the portfolio-wide pin strategy)
- **MUST NOT** set `content_in_root: true` for a classic `custom_components/<domain>/` layout — that breaks HACS detection

### `manifest.json` — required fields

- **MUST** include `domain` as a lowercase ASCII slug (`a–z`, `0–9`, `_`); hyphens and uppercase letters are not allowed
- **MUST** include `name` as a human-readable display name
- **MUST** include `codeowners` as a non-empty list of `@`-prefixed GitHub handles (at least one codeowner)
- **MUST** include `documentation` as an HTTPS URL pointing to a reachable documentation page (typically the repo or the MkDocs site)
- **MUST** include `issue_tracker` as an HTTPS URL pointing to the bug tracker (typically `https://github.com/<owner>/<repo>/issues`)
- **MUST** include `iot_class` — see _`iot_class` choice_ below
- **MUST** include `integration_type` — see _`integration_type` choice_ below
- **MUST** include `version` as a SemVer-compliant version (`MAJOR.MINOR.PATCH`); HA mandates this key for every Custom Integration
- **MUST** include `loggers` as the list of logger names the code uses — typically `["custom_components.<domain>"]` plus every external library that logs
- **MUST** include `requirements` as a list (even if empty), pinned to explicit versions when external PyPI packages are used (e.g. `["aiohttp==3.9.5"]`)
- **SHOULD** set `config_flow: true` once the integration is UI-configurable; pure YAML configuration is heavily deprecated for Custom Integrations and should be avoided
- **MAY** add discovery hints as top-level keys (`zeroconf`, `dhcp`, `ssdp`, `mqtt`, `bluetooth`, `usb`) — see `ha/zeroconf-discovery` and follow-up specs for the respective shape
- **MAY** add `dependencies` if the integration relies on other HA components (e.g. `["frontend"]` for Lovelace card auto-registration)
- **MAY** set `preload_platforms: false` to disable preloading

### `manifest.json` — required interpretations

- **MUST NOT** reference untagged git URLs in `requirements` (`git+https://...`); the list must consist of PyPI-installable, version-pinned entries
- **MUST NOT** change `domain` over the lifetime of the integration — `domain` is simultaneously the folder name, the translation-key prefix, the service namespace, and the config-entry lookup key; changing it breaks every existing installation
- **MUST NOT** list personal email addresses or real names in `codeowners` — only GitHub handles
- **SHOULD** keep `documentation` and `issue_tracker` pointing at the same repository root, so hassfest can verify consistency

### `integration_type` choice

- **MUST** set exactly one of the following values, based on the relationship between the integration and its world:
  - `hub` — the integration manages **multiple devices or entities** that hang off a central server / bridge / API endpoint (typical for most server-backed Custom Integrations)
  - `device` — the integration represents **exactly one physical or logical device** (typical for directly addressed IoT devices without a bridge)
  - `service` — the integration talks to an **online service without a physical device** (typical for purely cloud-based APIs)
  - `system` — internal system components; almost never applicable in Custom Integrations
  - `helper` — UI-only helper without a data source; almost never applicable in Custom Integrations
- **SHOULD** choose `hub` as soon as the integration creates more than one sub-device (even when the top-level device is just a server) — otherwise the device registry loses the hierarchy

### `iot_class` choice

- **MUST** set exactly one of the following values:
  - `local_polling` — the integration polls an endpoint on the local network (most common case for server-backed Custom Integrations)
  - `local_push` — the device / local endpoint pushes updates actively (mDNS broadcast, MQTT, HTTP webhook into HA)
  - `cloud_polling` — the integration polls a cloud service over the internet
  - `cloud_push` — the cloud service pushes updates over a webhook or a WebSocket connection
  - `assumed_state` — the integration sets state without read-back from the device
  - `calculated` — the integration derives its state from other entities (typical for helper integrations)
- **SHOULD** prefer `local_*` over `cloud_*` when both paths are technically possible — `local_*` is offline-resilient and more privacy-friendly

### Lifecycle entry points

- **MUST** export `async_setup_entry(hass, entry) -> bool` from `__init__.py` — HA calls this once per config entry
- **MUST** export `async_unload_entry(hass, entry) -> bool` from `__init__.py` — called when a config entry is removed
- **SHOULD** perform all platform setup via `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)` inside `async_setup_entry` rather than per-platform forwards
- **SHOULD** return `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` from `async_unload_entry` — every platform-specific cleanup hook then runs automatically
- **MAY** export `async_migrate_entry(hass, entry) -> bool` once the schema of `entry.data` or `entry.options` changes across versions — `manifest.json:version` is then simultaneously the source of `entry.version`
- **MUST NOT** use `hass.data[DOMAIN][entry.entry_id]` as the storage location for coordinators / API clients / listeners; see `ha/runtime-data-pattern` for the mandatory alternative (`entry.runtime_data`)

### Quality scale marker

- **SHOULD** explicitly mark each pattern in every detail spec of this plugin (`ha/runtime-data-pattern`, `ha/config-flow-patterns`, `ha/coordinator-patterns`, `ha/entity-architecture`, …) with an HA quality scale tier (`bronze` / `silver` / `gold` / `platinum`), so skill consumers know which tier the generated code lands at
- **MAY** mark patterns without a clear quality scale mapping as `unscaled` rather than inventing a tier
- **MUST** reference the prevailing HA quality scale definition (link to `home-assistant/developers.home-assistant.io`) when marking, so the marker remains verifiable later

### Cross-references to follow-up specs

- `runtime_data` pattern, `KamerplanterRuntimeData` analogue, typed `ConfigEntry` → `ha/runtime-data-pattern`
- Config flow (user / reauth / reconfigure / options) → `ha/config-flow-patterns`
- Discovery mechanisms (zeroconf, DHCP, SSDP, MQTT, Bluetooth, USB) → `ha/zeroconf-discovery` plus follow-up specs per mechanism
- `DataUpdateCoordinator` topology, error mapping, update intervals → `ha/coordinator-patterns`
- Base entity, `has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`, `DeviceInfo`, `via_device` → `ha/entity-architecture` and `ha/device-registry`
- `services.yaml`, selectors, multi-instance disambiguation → `ha/services`
- `strings.json`, `translations/<lang>.json`, sync strategy → `ha/translations`
- `icons.json` → `ha/icons`
- Diagnostics + `async_redact_data` → `ha/diagnostics`
- Lovelace card auto-registration in `__init__.py` → `ha/lovelace-card-patterns`
- Local dev loop (`kubectl cp`, `kill 1`) → `ha/dev-environment`
- Test harness → `ha/test-harness`
- Security hardening (path whitelist, bearer gating) → `ha/security-hardening`

## Acceptance Criteria

- [ ] `custom_components/<domain>/` exists and contains `manifest.json` plus `__init__.py`
- [ ] `manifest.json` contains every required field: `domain`, `name`, `codeowners`, `documentation`, `issue_tracker`, `iot_class`, `integration_type`, `version`, `loggers`, `requirements`
- [ ] `manifest.json:domain` matches the folder name under `custom_components/`
- [ ] `manifest.json:domain` is lowercase ASCII (`[a-z0-9_]+`), no hyphens, no uppercase
- [ ] `manifest.json:codeowners` is a non-empty list of `@`-prefixed GitHub handles
- [ ] `manifest.json:version` is SemVer-compliant
- [ ] `manifest.json:integration_type` is exactly one of `hub`, `device`, `service`, `system`, `helper`
- [ ] `manifest.json:iot_class` is exactly one of `local_polling`, `local_push`, `cloud_polling`, `cloud_push`, `assumed_state`, `calculated`
- [ ] `manifest.json:requirements` contains no untagged git URLs; every entry is PyPI-installable and version-pinned
- [ ] `__init__.py` exports `async_setup_entry` and `async_unload_entry`
- [ ] No primary integration code lives outside `custom_components/<domain>/`
- [ ] When `hacs.json` is present: `name` is set; `content_in_root: true` is not set
- [ ] Follow-up specs under `spec/ha/` mark their patterns with an HA quality scale tier or explicitly as `unscaled`
- [ ] hassfest (`hacs/action@main` with category `Integration`) runs cleanly in the consumer repo's CI

## Open Questions

- **HA minimum version**: Which version do we pin portfolio-wide in `hacs.json:homeassistant`? `nolte/kamerplanter-ha` uses `2024.1.0` — is that the portfolio-wide anchor or do we pin more aggressively? This question already appears in `AUDIENCES.md` and is referenced from here.
- **`requirements` pinning style**: `==1.2.3` (strict) or `~=1.2.3` (compatible) — is there a convention or does this remain decidable per integration?
- **First quality scale application**: Which follow-up spec is the first to actually apply this marker? Do we build a quality scale appendix into every follow-up spec or do we consolidate every marker in a dedicated `ha/quality-scale-mapping` spec?
- **Discovery spec ordering**: Is `ha/zeroconf-discovery` enough as the first discovery spec (kamerplanter-ha uses zeroconf) or do we pull DHCP / SSDP / MQTT / Bluetooth / USB along immediately?
- **`dependencies` vs. `after_dependencies`**: HA offers both keys — when does the spec require which? Currently undifferentiated; clarifies once the first integration with a real HA-component dependency lands.
- **Source-code language convention for Custom Integrations**: `nolte/kamerplanter-ha` mandates English source code (variables, classes, functions, strings); doc comments may be German. Should this rule live in the foundation spec or in `ha/translations`?
- **HACS mandatory vs. optional**: Should skills produce HACS-conformant layout by default, or is HACS optional? `AUDIENCES.md` flags this as an open question against the HACS steward.
