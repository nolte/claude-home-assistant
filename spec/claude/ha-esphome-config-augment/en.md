# Skill: `ha-esphome-config-augment`

Status: draft

## Context

Sibling of `ha-esphome-config-scaffold` in the device-YAML slice of the ESPHome axis (2026-07 audit decision; fixture `nolte/esphome-configs`). Where the scaffold owns the greenfield file, this skill owns the far more frequent case: one more sensor, bus, component binding, or shared-package adoption in a device file that already exists — the fixture's multiplexed I²C topologies show why a guessed bus binding is expensive on-device and the addition deserves an interactive, spec-anchored skill.

## Scope

One addition to one existing device file per invocation, per `spec/ha/esphome-config-patterns/en.md`. Legacy merge-key includes in the file are tolerated but never extended; duplication of shared-package content is refused.

## Goals

- Single entry point for extending a device (`/claude-home-assistant:ha-esphome-config-augment`)
- Schema verification against the official ESPHome docs before any write
- Explicit bus binding on multiplexed topologies; substitution-derived naming preserved
- Refusal to duplicate what a shared package already provides — package adoption offered instead

## Non-Goals

- New device files (`ha-esphome-config-scaffold`), component authoring, add-ons, compile/flash/deploy
- HA-side consumption of the new entities (automation/Lovelace families)

## Requirements

- **MUST** read the grounding spec, the target device file, and every shared file it pulls in before composing
- **MUST** run the duplicate check (same platform + address/bus, locally or via package) and refuse duplicates
- **MUST** verify the component schema upstream per `spec/ha/upstream-docs-verification`; deprecated keys are findings, never output
- **MUST** bind new I2C blocks to a named `bus_id` on multiplexed topologies and confirm the choice with the operator
- **MUST** keep naming substitution-derived and credentials as reported `!env_var` references
- **MUST** consult `spec/ha/esphome-ha-driven-content/en.md` when the addition is driven by Home Assistant, and pick the mechanism it prescribes — state subscription, callable action, writable entity, or return channel — instead of inventing one
- **SHOULD** refuse an addition that duplicates content a shared package already provides, per `spec/ha/esphome-project-structure/en.md`, and point at the package instead
- **MUST NOT** introduce or extend `<<: !include` merge keys, edit other device files, or perform more than one addition per run
- **SHOULD** offer `esphome config <file>` validation when the toolchain is present

## Acceptance Criteria

- [ ] An augment run on a fixture-style multiplexed device binds the new block to an explicitly named channel bus
- [ ] Requesting a block a shared package already provides is refused with the package named
- [ ] The diff summary names every new environment variable and leaves unrelated blocks byte-identical

## Open Questions

_None at this time._
