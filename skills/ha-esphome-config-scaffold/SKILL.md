---
name: ha-esphome-config-scaffold
description: "Scaffolds one complete ESPHome device-config YAML file — substitutions-driven naming, shared blocks via packages, environment-variable-referenced wifi with AP fallback, natively encrypted api with a per-device key, password-protected ota, logger, and the first sensor/actuator platform blocks — conforming to spec/ha/esphome-config-patterns. Gathers device name, board family, shared-concern set, and initial platforms, runs a pre-flight (collision, credential inventory, device-config root), writes the new <device-name>.yaml, and reports which environment variables the operator must set. Activate on \"scaffold an ESPHome device config\", \"new ESPHome device YAML\", or equivalent German requests. Do not activate for extending an existing device file (ha-esphome-config-augment), for the repository layout and shared packages (ha-esphome-fleet-scaffold), for an ESPHome custom component in C++/Python (out of scope), for an HA Custom Integration (ha-integration-scaffold), or for compiling/flashing."
tags: [home-assistant, esphome, scaffolding, yaml]
phase: build
summary: "Scaffolds one spec-conformant ESPHome device-config YAML (packages, env-var credentials, encrypted api, ota) for a new device."
summary_de: "Scaffoldet eine spec-konforme ESPHome-Device-Config-YAML (packages, Env-Var-Credentials, verschlüsselte api, ota) für ein neues Gerät."
use_when:
  - "you want a new ESPHome device described as a fresh, spec-conformant YAML file"
  - "you want the wifi/api/ota/logger boilerplate composed from shared packages instead of copied"
dont_use_when:
  - situation: "You want to add a sensor, bus, or component to an existing device file"
    alternative: ha-esphome-config-augment
  - situation: "You want the repository layout and the shared packages"
    alternative: ha-esphome-fleet-scaffold
  - situation: "You want a Home Assistant Custom Integration in Python"
    alternative: ha-integration-scaffold
see_also:
  - ha-esphome-config-augment
  - ha-esphome-fleet-scaffold
  - ha-esphome-config-reviewer
  - ha-esphome-solution
  - ha-integration-scaffold
---

# HA ESPHome Config Scaffold

Spec: `spec/claude/ha-esphome-config-scaffold/en.md` (EN canonical) / `spec/claude/ha-esphome-config-scaffold/de.md` (DE translation). Grounding spec: `spec/ha/esphome-config-patterns/en.md`.

Scaffolds exactly one new ESPHome device-config YAML per invocation, in the consumer repository's device-config root, conforming to every MUST in the grounding spec.

## Why this is a skill, not an agent

- **Mid-flow approval is the contract (decisive):** device name, board family, shared-concern set, and the initial platform list are elicited and confirmed with the operator before any file exists; a fire-and-forget agent would guess where the spec demands answers.
- **Quick, targeted change:** one new YAML file in the repository the conversation is scoped to — main-conversation territory per the change-scope dimension.
- **Counter-dimension considered:** the boilerplate composition is template-like and self-contained (agent bias), but the scaffold is the first step of device work the conversation continues, so a report boundary would only add friction.

## When this skill activates

The user asks for a new ESPHome device config — "scaffold an ESPHome config for a soil-moisture node", "neues ESPHome-Gerät anlegen" — in a repository that holds ESPHome device YAML (fixture layout: `src/*.yaml`).

## When NOT to activate

- extending an existing device file (new sensor, bus, component) → `ha-esphome-config-augment`
- the repository layout, the `common/` tree, or the shared packages themselves → `ha-esphome-fleet-scaffold` / `ha-esphome-package-author`
- authoring an ESPHome custom component (C++/Python) → out of scope; no component axis exists yet
- a Home Assistant Custom Integration → `ha-integration-scaffold`
- compiling, flashing, or deploying → the ESPHome toolchain / operator, never this skill

## Hard rules

1. **Read `spec/ha/esphome-config-patterns/en.md` first.** Do not generate from memory.
2. **Verify every schema key against the official ESPHome docs** (<https://esphome.io>) per `spec/ha/upstream-docs-verification` — components, platforms, and their keys change between releases.
3. **No literal credentials, ever.** wifi, api encryption, and ota resolve from environment variables (`!env_var`), never from `!secret` and never from a literal — the portfolio's credential mechanism per the grounding spec, chosen because it reaches a local build and a CI build alike and works in packages where `!secret` provably cannot. The api encryption key is **per device**: the device file sets `api_key: !env_var <DEVICE>_API_KEY` and the shared package consumes `${api_key}`. Report every variable the operator must set.
4. **`packages:` for shared blocks.** Never introduce `<<: !include` merge keys in a new file; reuse existing shared files where they fit, propose a new concern-scoped one when none does.
5. **Substitution-driven naming.** `name` / `friendly_name` declared once; every entity name derives from `${friendly_name}` per the spec's naming rule.
6. **One device, one file.** No multi-device batches; no edits to other device files.
7. **No deploy.** The skill ends at the written file plus the validation step report.

## Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `device_name` | yes | — | kebab-case; becomes file name and `${name}` |
| `board` | yes | — | board/platform family; decides which shared package applies |
| `concerns` | no | `base` + board family | shared concerns to compose (e.g. i2c) |
| `platforms` | no | none | initial sensor/actuator blocks to include |
| `config_root` | no | auto-detected (`src/`) | where device YAML lives in this repo |

## Pre-flight (every run, in order — abort on first failure)

1. Detect the device-config root (existing `*.yaml` device files); ask when ambiguous.
2. Collision check: `<config_root>/<device_name>.yaml` must not exist.
3. Inventory shared packages/snippets and the repository's environment-variable documentation; note which variables already exist and which the new device adds.
4. Confirm the gathered inputs back to the operator before writing.

## Workflow

1. Compose the file per the grounding spec: `substitutions` → shared `packages:` → `esphome:` → connectivity/security blocks (only where not already provided by a shared package) → `external_components:` (only when the operator names one) → platform blocks with substitution-derived names.
2. Write `<config_root>/<device_name>.yaml`.
3. When the ESPHome toolchain is available, offer `esphome config <file>` as the validation step; otherwise report it as the operator's next step.
4. Report: written path, environment variables to set, validation status, and the augment skill as the follow-up entry point.

## Boundaries

- Adding to an existing device file → `ha-esphome-config-augment`
- Repository layout and the shared packages this file composes → `ha-esphome-fleet-scaffold`
- Home-Assistant-driven values, screen content, or a voice path on the new device → `ha-esphome-binding-add` / `ha-esphome-display-author` / `ha-esphome-voice-satellite-add`
- Custom-component authoring → out of scope; no owning skill yet
- HA-side dashboards/automations for the new entities → the Lovelace/automation families
- A conformance verdict on the result → `ha-esphome-config-reviewer` (independent, read-only)
