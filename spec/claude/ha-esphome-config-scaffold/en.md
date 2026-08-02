# Skill: `ha-esphome-config-scaffold`

Status: draft

## Context

The ESPHome axis was declared in `AUDIENCES.md` from the start but shipped no artifacts; the 2026-07 skills-and-agents audit flagged the gap and the operator decided to build the device-YAML slice first, sharpened against the round-trip fixture `nolte/esphome-configs`. This skill is the greenfield entry point of that slice: it turns "new ESPHome device" into one spec-conformant YAML file per `spec/ha/esphome-config-patterns/en.md`.

## Scope

One device, one new YAML file per invocation, in the consumer repository's device-config root. Composition prefers shared `packages:`; credentials stay `!env_var` references; the skill ends at the written file plus a validation-step report.

## Goals

- Single discoverable entry point (`/claude-home-assistant:ha-esphome-config-scaffold`) for new device configs
- Interactive gathering of device name, board family, shared concerns, and initial platforms before any write
- Pre-flight that catches collisions and undocumented credential variables before composition
- Output that is HA-ready by construction: natively encrypted api with a per-device key, password-protected ota, AP-fallback wifi — every credential resolved from an environment variable

## Non-Goals

- Extending existing device files (owned by `ha-esphome-config-augment`)
- ESPHome custom-component authoring (C++/Python) and HA add-ons — later axes
- Compile/flash/deploy and fleet rollout — the ESPHome toolchain and operator own those

## Requirements

- **MUST** read `spec/ha/esphome-config-patterns/en.md` before composing and satisfy every MUST it declares (naming, packages-over-merge-keys, credentials, api encryption, ota)
- **MUST** read `spec/ha/esphome-project-structure/en.md` as well and place the file accordingly: device files flat in the config root, reuse composed from a board package rather than copied blocks, and the `name` / `id` / `comment` substitution trio present
- **SHOULD** consult the device spec when scaffolding for known hardware (`spec/ha/esp32-s3-box/en.md` for the BOX family), so generation-specific pins and codecs come from the spec instead of from a generic template
- **MUST** verify every emitted schema key against the official ESPHome docs per `spec/ha/upstream-docs-verification`
- **MUST** run the pre-flight (config-root detection, collision check, credential-variable inventory, operator confirmation) before writing
- **MUST** emit credentials as `!env_var` references — never `!secret`, never a literal — with a per-device api encryption key supplied as a substitution, and **MUST** report every environment variable the operator has to set, extending the repository's environment-variable documentation when it ships one
- **SHOULD** offer `esphome config <file>` validation when the toolchain is present; otherwise report it as the caller's next step
- **MUST NOT** write more than the one device file (plus the optional example-file extension) per run

## Acceptance Criteria

- [ ] A scaffold run against the fixture layout produces a file that satisfies every checklist item of `spec/ha/esphome-config-patterns` §Acceptance Criteria
- [ ] Re-running with the same device name aborts on the collision pre-flight instead of overwriting
- [ ] The report names every environment variable the generated file references

## Open Questions

_None at this time — the version-pin question lives with the grounding spec._
