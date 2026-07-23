---
name: ha-esphome-config-augment
description: "Augments an existing ESPHome device-config YAML with one addition — a sensor/actuator platform block, an I2C bus or multiplexer channel, a locally consumed external component, or a new shared-package binding — conforming to spec/ha/esphome-config-patterns. Reads the device file and its shared packages first, verifies the component schema against the official ESPHome docs, keeps naming substitution-derived and secrets referenced, and never duplicates a block a shared package already provides. Activate on \"add a sensor to my ESPHome device\", \"wire a BME280 into box-01\", \"add an i2c multiplexer channel\", \"consume my local component in this device\", or equivalent German requests. Do not activate for a brand-new device file (ha-esphome-config-scaffold), authoring the custom component itself (out of scope; no component axis yet), HA-side automations or dashboards (ha-automation-solution / ha-lovelace-solution), or compiling/flashing/deploying."
tags: [home-assistant, esphome, yaml]
phase: build
summary: "Adds one platform block, bus, component binding, or package to an existing ESPHome device-config YAML."
summary_de: "Ergänzt eine bestehende ESPHome-Device-Config-YAML um einen Plattform-Block, Bus, Component-Binding oder ein Package."
use_when:
  - "you want one more sensor, actuator, bus, or component wired into an existing ESPHome device file"
  - "you want a device file to adopt a shared package instead of its copied boilerplate"
dont_use_when:
  - situation: "You want a brand-new device config file"
    alternative: ha-esphome-config-scaffold
  - situation: "You want a Home Assistant Custom Integration in Python"
    alternative: ha-integration-scaffold
see_also:
  - ha-esphome-config-scaffold
---

# HA ESPHome Config Augment

Spec: `spec/claude/ha-esphome-config-augment/en.md` (EN canonical) / `spec/claude/ha-esphome-config-augment/de.md` (DE translation). Grounding spec: `spec/ha/esphome-config-patterns/en.md`.

Adds exactly one addition to one existing device file per invocation, conforming to every MUST in the grounding spec.

## Why this is a skill, not an agent

- **Quick, targeted change in the current context (decisive):** one block in one YAML file the conversation is already working on; per the change-scope and latency dimensions this routes to the main thread.
- **Mid-flow approval:** the component choice, target bus, and naming are confirmed with the operator before writing — a wrong bus binding on a multiplexed topology is expensive to debug on-device.
- **Counter-dimension considered:** schema lookup against the ESPHome docs is self-contained (agent bias), but the diff is small and iterated in conversation — isolation would cost more than it protects.

## When this skill activates

The user asks to extend an existing ESPHome device — "add an SCD30 to box-02", "füge einen Sensor zum ESPHome-Gerät hinzu" — and the named device file exists.

## When NOT to activate

- a brand-new device → `ha-esphome-config-scaffold`
- authoring the custom component itself (C++/Python) → out of scope; no owning skill yet
- HA-side reactions to the new entities (automations, cards) → `ha-automation-solution` / `ha-lovelace-solution`
- compiling, flashing, or deploying → the ESPHome toolchain / operator

## Hard rules

1. **Read `spec/ha/esphome-config-patterns/en.md` and the target device file (plus its shared packages/snippets) first.** Do not generate from memory, and never add a block a shared package already provides.
2. **Verify the component's schema against the official ESPHome docs** (<https://esphome.io>) per `spec/ha/upstream-docs-verification` before writing; deprecated keys are findings, not output.
3. **Naming stays substitution-derived** (`${friendly_name}_<platform>_<n>_<measurement>`); `update_interval` prefers the device's existing interval substitution.
4. **Secrets stay references.** A new block needing a credential adds a `!secret` key and reports it; never a literal.
5. **Explicit bus binding.** On multiplexed I2C topologies, bind the new block to a named `bus_id` — never the implicit default bus.
6. **One addition per run; one device file per run.** Legacy `<<: !include` merge keys in the file are left as-is (never extended, never newly introduced).
7. **No deploy.** The skill ends at the edited file plus the validation step report.

## Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `device_file` | yes | — | existing `<config_root>/<device>.yaml` |
| `addition` | yes | — | platform block, bus/channel, component binding, or package adoption |
| `bus` | conditional | — | required on multiplexed topologies |

## Pre-flight (every run, in order — abort on first failure)

1. Confirm the device file exists; read it and every shared file it pulls in.
2. Duplicate check: the requested block (same platform + address/bus) must not already exist, locally or via a shared package.
3. Resolve the target bus on i2c topologies; list the named buses back when ambiguous.
4. Confirm the planned addition (block shape, names, secrets keys) with the operator before writing.

## Workflow

1. Verify the component schema upstream; compose the block per the grounding spec.
2. Apply the edit to the device file (or, when the operator opts in, promote a copied block into a shared package instead).
3. When the ESPHome toolchain is available, offer `esphome config <file>`; otherwise report validation as the operator's next step.
4. Report: diff summary, any new secrets keys, validation status.

## Boundaries

- New device file → `ha-esphome-config-scaffold`
- Component authoring → out of scope; no owning skill yet
- HA-side consumption of the new entities → the automation/Lovelace families
