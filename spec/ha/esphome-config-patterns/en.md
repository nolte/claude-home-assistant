# ESPHome Device-Config Patterns

Status: draft

## Context

An ESPHome device config is a single YAML file that fully describes one microcontroller device — board, connectivity, and its sensor/actuator platforms — compiled and flashed by the ESPHome toolchain and surfaced in Home Assistant through the native API. Unlike a Custom Integration there is no Python lifecycle here: all of the quality is decided by YAML structure, secret handling, naming discipline, and how much shared configuration is reused instead of copied.

This spec canonizes the device-YAML patterns for the portfolio, distilled from the round-trip fixture [`nolte/esphome-configs`](https://github.com/nolte/esphome-configs) (per-device files under `src/`, shared include snippets, substitution-driven naming) and verified against the official ESPHome documentation. It grounds the first slice of the ESPHome skill axis (`ha-esphome-config-scaffold`, `ha-esphome-config-augment`); ESPHome custom components (C++/Python) and HA add-ons are deliberately separate, later axes.

## Goals

- One canonical shape for a device config: file location, required core blocks, secret handling, naming
- Shared configuration is reused through `packages:` (preferred) or legacy include snippets — never copied between device files
- Every generated config is HA-ready out of the box: encrypted native API, OTA, sane logging
- Facts about ESPHome internals are verified against the official docs per `spec/ha/upstream-docs-verification`, never generated from memory

## Non-Goals

- ESPHome **custom components** (`external_components` authoring, C++/Python) — a later axis; consuming an existing local component in a device YAML is in scope
- HA **add-ons** (Supervisor, s6) — a separate distribution concern
- The compile/flash toolchain itself (`esphome run`, CI builds) and fleet/OTA rollout orchestration
- Dashboard/UI concerns in Home Assistant (owned by the Lovelace family)

## Requirements

### File layout and naming

- One device **MUST** live in exactly one YAML file named after the device (`<device-name>.yaml`, kebab-case), under the repository's device-config root (fixture: `src/`)
- The device name **MUST** be declared once via `substitutions:` (`name`, `friendly_name`) and referenced as `${name}` / `${friendly_name}` everywhere else — entity names derive as `${friendly_name}_<platform>_<n>_<measurement>` so renames stay one-line changes
- Retired devices **SHOULD** move to an `archive/` sibling folder instead of being deleted, preserving the config as pattern history

### Shared configuration

- Common blocks (wifi, logger, api, ota, board/platform families, i2c buses) **MUST** be factored into shared files and pulled into device files — never duplicated per device
- New configs **SHOULD** use ESPHome `packages:` for that reuse; the fixture's legacy `<<: !include ./include-*.yaml.snipped` merge-key form **MAY** be kept in existing files but **MUST NOT** be introduced in new ones (merge keys don't deep-merge lists and the pattern predates packages)
- A shared file **MUST** stay board- or concern-scoped (`esp32`, `esp8266-i2c`, `base`) so a device composes exactly the concerns it has

### Connectivity and security

- `wifi:` credentials **MUST** come from environment variables (`!env_var WIFI_SSID` / `!env_var WIFI_PASSWORD`), never from a file in the repository: remote packages provably cannot resolve `!secret`, and environment variables reach a local build and a CI build alike. Every variable a config reads **MUST** be documented so a fresh checkout is buildable
- `wifi:` **SHOULD** declare an `ap:` fallback plus `captive_portal:` so an unreachable device stays recoverable
- `api:` **MUST** declare `encryption:` with a **per-device** key, supplied as a substitution the device file sets (`substitutions: {api_key: !env_var <DEVICE>_API_KEY}`) and consumed as `key: ${api_key}` — an unencrypted native API is a finding, not a variant, and one fleet-wide key would let a single compromised device expose every other device's API session
- `ota:` **MUST** be present and password-protected via `!env_var OTA_PASSWORD`
- No literal credential, token, or key **MUST** ever appear in a device or shared file, and a populated `secrets.yaml` **MUST NOT** be committed

### Platforms and components

- Sensor/actuator blocks **MUST** carry explicit `name:` (substitution-derived), and **SHOULD** pin `update_interval` via a substitution (fixture: `intervall`) so polling cadence is tunable per device
- A locally consumed custom component **MUST** be declared via `external_components:` with a repository-relative `source:` and an explicit `components:` list
- Multiplexed I²C topologies (fixture: `tca9548a`) **MUST** name every channel bus (`bus_id`) so sensor blocks bind to an explicit bus, never an implicit default
- Every component/platform key used **MUST** exist in the official ESPHome docs for a current release; deprecated keys are findings

### Verification

- Facts about schema keys, defaults, and deprecations **MUST** be verified against the official ESPHome documentation (<https://esphome.io>) per `spec/ha/upstream-docs-verification` — never asserted from memory
- A generated or augmented config **SHOULD** be validated with `esphome config <file>` when the toolchain is available; when it isn't, the skill reports the validation as an open caller step

## Acceptance Criteria

- [ ] A scaffolded device config compiles the required core blocks (substitutions, esphome, shared package/include, wifi+ap, api+encryption, ota, logger) with zero literal secrets
- [ ] Entity names in generated platform blocks derive from `${friendly_name}` per the naming rule
- [ ] New configs use `packages:` for shared blocks; no new `<<: !include` merge keys are introduced
- [ ] Every schema key in generated output resolves against the official ESPHome docs
- [ ] Credentials resolve from documented environment variables; no credential file is committed

## Open Questions

- Minimum pinned ESPHome version for the generated patterns (fixture pins none explicitly) — align with the portfolio-wide HA-version question in `AUDIENCES.md`
- Whether the archive/ convention should become a MUST once a second consumer repo adopts the axis
