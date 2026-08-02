# ESPHome Device-Config Patterns

Status: draft

## Context

An ESPHome device config is a single YAML file that fully describes one microcontroller device — board, connectivity, and its sensor/actuator platforms — compiled and flashed by the ESPHome toolchain and surfaced in Home Assistant through the native API. Unlike a Custom Integration there is no Python lifecycle here: all of the quality is decided by YAML structure, secret handling, naming discipline, and how much shared configuration is reused instead of copied.

This spec canonizes the device-YAML patterns for the portfolio, drawing on the round-trip fixture [`nolte/esphome-configs`](https://github.com/nolte/esphome-configs) (per-device files under `src/`, shared configuration under `src/common/` consumed through `packages:`, substitution-driven naming) and verified against the official ESPHome documentation. Note that the fixture is a *source of patterns, not a compliance benchmark*: several requirements below — API encryption and the OTA password in particular — are portfolio decisions the fixture does **not** currently satisfy, and they are tiered accordingly. It is the **device-file** half of a pair: [`ha/esphome-project-structure`](../esphome-project-structure/en.md) owns the repository around these files — directory layout, package architecture, parameterisation, and onboarding — and is the deeper authority wherever the two touch. The *File layout* and *Shared configuration* sections below state only what a single device file must look like; take the tree-level rules from that spec. It grounds the first slice of the ESPHome skill axis (`ha-esphome-config-scaffold`, `ha-esphome-config-augment`); ESPHome custom components (C++/Python) and HA add-ons are deliberately separate, later axes.

### Source tiers

Evidence tiers are used as defined in [`ha/esp32-s3-box`](../esp32-s3-box/en.md) §"Source tiers": `[doc]` for the official ESPHome component documentation at <https://esphome.io>, `[src]` for behaviour that is real but undocumented and therefore established from the ESPHome source tree, `[fixture]` for a pattern observed in `nolte/esphome-configs`, and `[policy]` for a nolte-portfolio rule that is not an upstream fact. `[fixture]` is the weakest tier here: it records what the reference repository does, which is evidence of a workable pattern and nothing more.

Verified 2026-08.

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

- One device **MUST** live in exactly one YAML file named after the device (`<device-name>.yaml`, kebab-case), under the repository's device-config root (fixture: `src/`) `[fixture]` `[policy]`
- The device name **MUST** be declared once via `substitutions:` (`name`, `friendly_name`) and referenced as `${name}` / `${friendly_name}` everywhere else — entity names derive as `${friendly_name}_<platform>_<n>_<measurement>` so renames stay one-line changes `[doc]` `[fixture]` `[policy]`
- Retired devices **SHOULD** move to an `archive/` folder beside the device files instead of being deleted, preserving the config as pattern history. The fixture also keeps a third category, `src/poc/`, for experiments that were never deployed — a config in neither `src/` nor `archive/` carries no promise of being buildable `[fixture]` `[policy]`

### Shared configuration

- Common blocks (wifi, logger, api, ota, board/platform families, i2c buses) **MUST** be factored into shared files and pulled into device files — never duplicated per device. In the fixture these live under `src/common/` `[fixture]` `[policy]`
- New configs **MUST** use ESPHome `packages:` for that reuse, in the `!include` form that takes a `file:` and optional `vars:`, so a shared file can be parameterised per device rather than copied. The legacy `<<: !include ./include-*.yaml.snipped` merge-key form **MUST NOT** be introduced, and is no longer merely deprecated in the fixture: every `.snipped` file now sits under `src/archive/`, while `src/box-01.yaml` still references `./include-base.yaml.snipped` at a path where no such file exists — a config that cannot resolve, which the fixture's CI does not catch because it runs pre-commit and security scans but never `esphome config` `[doc]` `[fixture]` `[policy]`
- A shared file **MUST** stay board- or concern-scoped (`esp32`, `esp8266-i2c`, `base`) so a device composes exactly the concerns it has. Note that a `<<: !include` merge **into a list entry** (as `src/common/base.yaml` does for its status/uptime/wifi-signal blocks) is a different construct from a top-level document merge and remains idiomatic `[fixture]` `[policy]`

### Connectivity and security

- `wifi:` credentials **MUST** come from environment variables (`!env_var WIFI_SSID` / `!env_var WIFI_PASSWORD`), never from a file in the repository, because environment variables reach a local build and a CI build alike. Two things about `!env_var` must be understood before relying on it: it is **undocumented** — it exists only as a loader tag registered in `esphome/yaml_util.py`, on no page of esphome.io — and it accepts a **default** as trailing words (`!env_var NAME fallback value`), raising only when the variable is unset *and* no default is given. Every variable a config reads **MUST** be documented so a fresh checkout is buildable `[src]` `[fixture]` `[policy]`
- **MUST NOT** justify that rule with the remote-package limitation alone. It is true and documented that "remote packages cannot have secret lookups in them" — but upstream's own remedy is *not* environment variables: it prescribes "substitutions with an optional default in the packaged YAML, which the local device YAML can set using values from the local secrets". Local (non-remote) packages resolve `!secret` normally, as the documentation's own example shows. Choosing environment variables over `!secret` is therefore a portfolio decision taken for CI parity, not a constraint upstream imposes `[doc]` `[policy]`
- `wifi:` **SHOULD** declare an `ap:` fallback plus `captive_portal:` so an unreachable device stays recoverable `[doc]` `[fixture]`
- `api:` **MUST** declare `encryption:` with a **per-device** key, supplied as a substitution the device file sets (`substitutions: {api_key: !env_var <DEVICE>_API_KEY}`) and consumed as `key: ${api_key}` — an unencrypted native API is a finding, not a variant, and one fleet-wide key would let a single compromised device expose every other device's API session. The fixture does **not** meet this: `src/common/base.yaml` ships a bare `api:` with no `encryption:` block at all `[policy]`
- `ota:` **MUST** be present and password-protected via `!env_var OTA_PASSWORD`. The fixture does **not** meet this either — it declares `ota: - platform: esphome` with no password `[policy]`
- No literal credential, token, or key **MUST** ever appear in a device or shared file, and a populated `secrets.yaml` **MUST NOT** be committed `[policy]`

### Platforms and components

- Sensor/actuator blocks **MUST** carry explicit `name:` (substitution-derived), and **SHOULD** pin `update_interval` via a substitution (fixture: `intervall`) so polling cadence is tunable per device `[fixture]` `[policy]`
- A locally consumed custom component **MUST** be declared via `external_components:` with a repository-relative `source:` and an explicit `components:` list. Listing components explicitly is a portfolio rule, not a schema one — `components` is optional and defaults to using every component the source offers, which is exactly the implicit behaviour worth avoiding `[doc]` `[policy]`
- Multiplexed I²C topologies (fixture: `tca9548a`) **MUST** name every channel bus (`bus_id`) so sensor blocks bind to an explicit bus, never an implicit default `[doc]` `[fixture]`
- Every component/platform key used **MUST** exist in the official ESPHome docs for a current release; deprecated keys are findings `[policy]`

### Verification

- Facts about schema keys, defaults, and deprecations **MUST** be verified against the official ESPHome documentation (<https://esphome.io>) per `spec/ha/upstream-docs-verification` — never asserted from memory `[policy]`
- **MAY** fall back to the ESPHome source tree where a behaviour is real but undocumented — `!env_var` is the worked example — but **MUST** then tier the claim `[src]` rather than `[doc]`, because an undocumented tag can change without a documentation change `[policy]`
- A generated or augmented config **SHOULD** be validated with `esphome config <file>` when the toolchain is available; when it isn't, the skill reports the validation as an open caller step. Note that the fixture repository does **not** run this in CI — its pipeline covers pre-commit, Trivy and chain-bench only — so "it is in the fixture" is not evidence that a config resolves `[fixture]` `[policy]`

## Acceptance Criteria

- [ ] A scaffolded device config compiles the required core blocks (substitutions, esphome, shared package/include, wifi+ap, api+encryption, ota, logger) with zero literal secrets
- [ ] Entity names in generated platform blocks derive from `${friendly_name}` per the naming rule
- [ ] New configs use `packages:` for shared blocks; no new `<<: !include` merge keys are introduced
- [ ] Every schema key in generated output resolves against the official ESPHome docs
- [ ] Credentials resolve from documented environment variables; no credential file is committed
- [ ] Shared configuration is consumed through `packages:` with `file:`/`vars:`; no `<<: !include` document merge is introduced, and every include a config references actually resolves

## Open Questions

- Minimum pinned ESPHome version for the generated patterns (fixture pins none explicitly) — align with the portfolio-wide HA-version question in `AUDIENCES.md`. Note that [`ha/esp32-s3-box`](../esp32-s3-box/en.md) has since settled the same question per-generation for the BOX family, which is a usable precedent: pin the floor the upstream reference for that board pins, and treat a bump as a reviewed change
- Whether the archive/ convention should become a MUST once a second consumer repo adopts the axis
- **Fixture divergence** (opened 2026-08 by the unit-1 verification pass): the fixture satisfies neither the API-encryption nor the OTA-password requirement, and `src/box-01.yaml` references an include that no longer exists at that path. Filed upstream on 2026-08-02 as [nolte/esphome-configs#14](https://github.com/nolte/esphome-configs/issues/14) (unresolvable include, missing CI validation) and [#15](https://github.com/nolte/esphome-configs/issues/15) (unencrypted API, unprotected OTA). Tracked together with the *Fixture remediation* question in [`ha/esphome-project-structure`](../esphome-project-structure/en.md), which adds the re-flash consequence — resolve them as one decision, not two
