# Skill: `ha-esphome-fleet-scaffold`

Status: draft

## Context

The ESPHome axis opened with the device-file slice (`ha-esphome-config-scaffold`, `ha-esphome-config-augment`), which assumes a repository already shaped to hold devices. `spec/ha/esphome-project-structure` then established what that shape is — config root, `common/` package tree, `include/`, `archive/`, keyed assets — and nothing operationalised it. This skill closes that gap: it is the structural entry point of the ESPHome family, run once per repository before the first device and again whenever an organically grown collection has to be brought onto the package architecture.

## Scope

One repository per invocation. Greenfield creation of the tree plus the base and board packages, or a plan-gated restructure of an existing flat collection. Ends at the written tree, the environment-variable documentation, and a validation report; device authoring is handed off.

## Goals

- Single discoverable entry point for "where does ESPHome configuration live in this repository"
- A tree that makes the flashable/included distinction visible, so a reader finds any device and any shared block without searching
- Base and board packages that make onboarding a device of an existing kind a one-file change
- Credential handling that is correct from the first commit: `!env_var`, per-device API keys, documented variables, nothing committed
- A restructure that is never silent — every move is listed and approved before it happens

## Non-Goals

- Device files themselves (owned by `ha-esphome-config-scaffold` / `ha-esphome-config-augment`)
- One package's cut, parameters, or deviation shape (owned by `ha-esphome-package-author`)
- CI validation (owned by `ha-esphome-ci-scaffold`)
- A conformance verdict on the result (owned by the read-only `ha-esphome-fleet-reviewer`)
- Portfolio-wide repository scaffolding that is not ESPHome-specific — Taskfile, pre-commit, Renovate, docs, release automation are governed by the inherited `project/` specs
- Compile, flash, and fleet OTA rollout

## Requirements

- **MUST** read `spec/ha/esphome-project-structure/en.md` before proposing a layout, and `spec/ha/esphome-config-patterns/en.md` for anything that reaches into a device file
- **MUST** present the current tree, the target tree, and the per-file move/create/edit list for explicit approval before writing on a repository that already holds device files
- **MUST** emit reuse as `packages:` in mapping form, never introduce a `<<: !include` merge key, and report existing merge keys as findings rather than extending them
- **MUST** group `common/` by consumer: entry points flat, building blocks in ESPHome-domain subdirectories
- **MUST** let the board package pull in the base package, so a device states one board plus its feature packages
- **MUST** emit credentials as `!env_var`, a per-device API encryption key consumed as `${api_key}`, a password-protected `ota:`, and `.gitignore` entries covering `.esphome/`, build output, and `secrets.yaml`
- **MUST** document every environment variable the scaffolded packages read, in the same run
- **MUST** give an explicit `id:` to any component a device might later extend or remove
- **MUST** consult the device spec when scaffolding a board package for known hardware (`spec/ha/esp32-s3-box/en.md`), rather than emitting a generic template
- **MUST** verify every emitted schema key against the official ESPHome docs per `spec/ha/upstream-docs-verification`
- **MUST** run `esphome config` for every existing device file after a restructure where the toolchain is available, and report it as the caller's open step where it is not
- **MUST NOT** author device files, and **MUST NOT** move or delete a file the operator has not seen listed

## Acceptance Criteria

- [ ] A greenfield run produces a tree that satisfies the layout checklist of `spec/ha/esphome-project-structure` §Acceptance Criteria
- [ ] A restructure run writes nothing before the move list is approved, and leaves legacy merge keys intact while reporting them
- [ ] The emitted base package carries no bare `api:` and no fleet-wide encryption key
- [ ] The report names every environment variable the scaffolded packages read

## Open Questions

_None at this time — the fixture-remediation question lives with the grounding spec._
