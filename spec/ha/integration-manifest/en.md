# HA Integration: `manifest.json`

Status: draft

## Context

Every Home Assistant integration has a manifest file describing its basic information. This file lives as `manifest.json` in the integration directory (`custom_components/<domain>/manifest.json`) and is required — without it HA does not load the integration. The manifest declares identity (`domain`, `name`), dependencies, classification (`integration_type`, `iot_class`), feature flags (`config_flow`, `quality_scale`) and optional discovery matchers (`zeroconf`, `ssdp`, `dhcp`, `bluetooth`, `usb`, `homekit`, `mqtt`).

This spec covers the manifest from the perspective of a **Custom Integration** (distribution typically via HACS), not a Core integration. The most important difference: the `version` key is **required** for Custom Integrations, while it must be omitted for Core integrations. Several manifest fields behave differently for Custom Integrations than for Core (`dependencies`/`after_dependencies` may reference custom integrations; `requirements` should only list packages Core does not already ship; virtual integrations are Core-only).

Quality scale relevance: several manifest fields are directly tied to quality-scale rules — `codeowners` satisfies the "integration-owner" rule (every integration needs an owner), and `requirements` must satisfy the "dependency-transparency" rule (dependencies must be OSI-licensed, available on PyPI, and exactly pinned). Cross-references: `ha/config-flow-patterns` (for `config_flow`), `ha/zeroconf-discovery` (for the discovery keys), `ha/quality-scale` (for `quality_scale`), `ha/integration-architecture` (for the overall integration layout).

## Goals

- Bindingly establish the required keys (`domain`, `name`) and their naming rules
- Secure the `version` key that is mandatory for Custom Integrations and delimit it from Core behaviour
- Enforce correct and transparent dependency declaration (`dependencies`, `after_dependencies`, `requirements`)
- Set classification (`integration_type`, `iot_class`) explicitly instead of relying on defaults
- Keep feature flags (`config_flow`, `quality_scale`) consistent with the code artifacts that are present
- Set discovery keys only when the integration actually supports the respective discovery
- Maintain identity metadata (`codeowners`, `documentation`, `issue_tracker`, `loggers`) so the associated quality-scale rules are satisfied

## Non-Goals

- Virtual integrations (`integration_type: virtual`, `supported_by`, `iot_standards`) — per the HA docs provided by Home Assistant Core only, not by Custom Integrations
- Brand images and the `brands` repository — separate follow-up spec once a concrete need lands
- The actual config-flow implementation behind `config_flow: true` — belongs to `ha/config-flow-patterns`
- The concrete requirements per quality-scale tier behind `quality_scale` — belongs to `ha/quality-scale`
- The detailed matcher semantics of the discovery keys (wildcard syntax, UUID conversion) — belongs to `ha/zeroconf-discovery`

## Requirements

### Required keys

- **MUST** set a `domain` key consisting only of lowercase characters and underscores, unique project-wide, matching exactly the name of the directory the `manifest.json` lives in
- **MUST NOT** change the `domain` after the first release — it is documented as immutable
- **MUST** set a `name` key with the human-readable integration name
- **SHOULD** follow the naming rules: for pure cloud integrations append the "Cloud" suffix (for example "LIFX Cloud"), for local or hybrid variants use the plain product name with no suffix (no "Local"), for inherently cloud-based products leave the name as-is (for example "iCloud", not "iCloud Cloud")

### Identity & metadata (codeowners, documentation, issue_tracker, version)

- **MUST** set `codeowners` as an array of GitHub usernames or team names and include at least your own GitHub username — this satisfies the quality-scale "integration-owner" rule, which requires every integration to have an owner
- **MUST** set `documentation` as a URL to the integration's usage documentation
- **SHOULD** set `issue_tracker` as a URL to the issue tracker so users report bugs in the right place — for a submission into Core this key is omitted, because Core generates the link automatically
- **MUST** set the `version` key for a Custom Integration; the value must be a version accepted by [AwesomeVersion](https://github.com/ludeeus/awesomeversion) (CalVer or SemVer) — this deliberately differs from Core behaviour, where `version` must be omitted
- **MAY** set `loggers` as an array of the logger names the integration's requirements use in their `getLogger` calls

### Dependencies (dependencies, after_dependencies, requirements)

- **MUST** list only integrations in `dependencies` that must be **set up successfully** before this integration (hard dependency); a Custom Integration may reference both built-in and custom integrations
- **SHOULD** use `after_dependencies` instead of `dependencies` when a dependency is optional but not critical — HA then waits for the listed integrations if they are configured, and installs their requirements, without forcing setup when they are not configured
- **MUST** set `requirements` as an array of `pip`-compatible strings in which every Python library is exactly pinned with `==` (for example `"aiohue==1.9.1"`) — this satisfies the quality-scale "dependency-transparency" rule (OSI license, PyPI availability, tagged release)
- **MUST NOT** list packages in `requirements` already provided by Core's [requirements.txt](https://github.com/home-assistant/core/blob/dev/requirements.txt) — a Custom Integration lists only its additional requirements

### Classification (integration_type, iot_class)

- **MUST** set `integration_type` explicitly instead of relying on the `hub` default — valid values are `device`, `entity`, `hardware`, `helper`, `hub`, `service`, `system`, `virtual`; `hub` is a gateway to multiple devices/services, `device`/`service` provide exactly one device or service per config entry
- **MUST** set `iot_class` to exactly one of the accepted values: `assumed_state`, `cloud_polling`, `cloud_push`, `local_polling`, `local_push` or `calculated`
- **MUST NOT** set `integration_type: virtual` for a Custom Integration — virtual integrations are, per the HA docs, reserved for Core only

### Feature flags (config_flow, quality_scale)

- **MUST** set `config_flow: true` as soon as the integration provides a config flow; in that case the file `config_flow.py` **must** exist (see `ha/config-flow-patterns`)
- **MAY** set `single_config_entry: true` when the integration supports exactly one config entry — HA then prevents creating further entries
- **SHOULD** set `quality_scale` to the achieved tier (`bronze`, `silver`, `gold`, `platinum`); new integrations must reach at least bronze (see `ha/quality-scale`)

### Discovery keys

- **MUST** set a discovery key (`zeroconf`, `ssdp`, `dhcp`, `bluetooth`, `usb`, `homekit`, `mqtt`) only when the integration actually supports that discovery and the associated config-flow step exists — the detailed matcher semantics are governed by `ha/zeroconf-discovery`
- **SHOULD** constrain generic `zeroconf` types (`_http._tcp.local.`, `_printer._tcp.local.` etc.) with a `name` or `properties` filter so foreign devices do not falsely trigger this integration
- **MAY** set `registered_devices: true` in a `dhcp` matcher to receive IP-address updates for devices already registered by MAC when a `hostname` or `oui` match would be too broad
- **MUST** add `mqtt` to `dependencies` as well for an integration that uses `mqtt` discovery or requires MQTT, and wait for the client with `await mqtt.async_wait_for_mqtt_client(hass)` before subscribing

### Custom-integration specifics

- **MUST** have the `version` key set — for a Custom Integration (and therefore any HACS-distributed integration) it is mandatory, otherwise HA refuses to load; when overriding a Core integration in the `custom_components` directory, `version` is mandatory as well
- **SHOULD** have a HACS-distributed integration bump the `version` value on every release so HACS detects and rolls out updates
- **MUST** keep the manifest such that `domain` and directory name match under `custom_components/<domain>/` — this is the only location where HA finds the integration (`<config>/custom_components/<domain>`)

## Acceptance Criteria

- [ ] `domain` is set, lowercase/underscores only, unique, and equal to the directory name
- [ ] `name` is set and follows the cloud/local naming rules
- [ ] `codeowners` contains at least one GitHub username (integration-owner rule satisfied)
- [ ] `documentation` is set as a URL
- [ ] `version` is set and a valid AwesomeVersion (CalVer/SemVer)
- [ ] `requirements` pins every library exactly with `==` and contains no packages already shipped by Core (dependency-transparency rule satisfied)
- [ ] `dependencies` / `after_dependencies` are correctly split by hard/optional
- [ ] `integration_type` is set explicitly and is not `virtual`
- [ ] `iot_class` is set to exactly one of the six accepted values
- [ ] `config_flow: true` is set exactly when `config_flow.py` exists
- [ ] Every set discovery key corresponds to a genuinely supported discovery path with an associated config-flow step
- [ ] For MQTT discovery, `mqtt` is additionally listed in `dependencies`
- [ ] `manifest.json` is valid JSON and lives under `custom_components/<domain>/`

## Open Questions

- **`quality_scale` mandatoriness**: Does this spec require at least `bronze` for every scaffolded Custom Integration, or does setting `quality_scale` stay optional as long as the integration is not submitted to Core? The HA docs require bronze only for new Core integrations.
- **`loggers` obligation**: Should `loggers` become mandatory as soon as the integration pulls in external libraries with their own logging, or stay `MAY`? The docs describe only the purpose, not the obligation.
- **Discovery-matcher validation**: Should this spec enforce validation of discovery matchers (for example lowercase properties for `zeroconf`, byte range for `bluetooth.manufacturer_data_start`), or delegate it entirely to `ha/zeroconf-discovery`?
- **`single_config_entry` heuristic**: When does the spec require `single_config_entry: true`? Currently it is `MAY` — a heuristic (exactly one account/gateway per installation) is missing.
- **Version-bump automation**: Should the skill scaffold automate the `version` bump on HACS releases or leave it to the release workflow?
