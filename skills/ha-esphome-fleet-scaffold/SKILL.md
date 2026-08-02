---
name: ha-esphome-fleet-scaffold
description: "Scaffolds the repository layout of an ESPHome fleet per spec/ha/esphome-project-structure — the config root with flat device files, a common/ package tree grouped by consumer, include/ for C++ lambda headers, archive/ for retired devices, a keyed asset tree, the base package plus a first board package that pulls it in, the environment-variable documentation every credential needs, and the .gitignore entries keeping tool state and secrets out of version control. Works greenfield and on an existing flat collection, where it proposes the layout as a migration plan before touching anything. Activate on \"set up an ESPHome repository\", \"restructure my ESPHome configs\", or equivalent German requests. Do not activate to write or extend one device file (ha-esphome-config-scaffold / ha-esphome-config-augment), to cut a single package (ha-esphome-package-author), to wire CI validation (ha-esphome-ci-scaffold), or to audit a layout (ha-esphome-fleet-reviewer)."
tags: [home-assistant, esphome, scaffolding, yaml]
phase: build
summary: "Scaffolds the ESPHome fleet repository layout — config root, common/ package tree, include/, archive/, base and board packages, env-var docs."
summary_de: "Scaffoldet das Repository-Layout einer ESPHome-Fleet — Config-Root, common/-Package-Baum, include/, archive/, Base- und Board-Package, Env-Var-Doku."
use_when:
  - "you are starting an ESPHome repository and want the fleet layout right from the first device"
  - "your device files grew organically and you want them on the spec's package architecture"
  - "you want a base package plus a first board package instead of copied boilerplate"
dont_use_when:
  - situation: "You want one new device config file"
    alternative: ha-esphome-config-scaffold
  - situation: "You want to cut, parameterise, or refactor a single shared package"
    alternative: ha-esphome-package-author
  - situation: "You want the CI that validates the fleet"
    alternative: ha-esphome-ci-scaffold
  - situation: "You want to know whether an existing layout conforms"
    alternative: ha-esphome-fleet-reviewer
see_also:
  - ha-esphome-package-author
  - ha-esphome-config-scaffold
  - ha-esphome-ci-scaffold
  - ha-esphome-fleet-reviewer
  - ha-esphome-solution
---

# HA ESPHome Fleet Scaffold

Spec: `spec/claude/ha-esphome-fleet-scaffold/en.md` (EN canonical) / `spec/claude/ha-esphome-fleet-scaffold/de.md` (DE translation). Grounding spec: `spec/ha/esphome-project-structure/en.md`; the device-file half is `spec/ha/esphome-config-patterns/en.md`.

Establishes the repository structure an ESPHome fleet is built in — once, at the top — so every later device is one new file and every shared concern has exactly one home.

## Why this is a skill, not an agent

- **Mid-flow approval is the contract (decisive):** the config root, the package cut, and — on an existing repository — which files move where are decisions the operator confirms before anything is written; a fire-and-forget agent would restructure a repository on guesses.
- **Repository-shaping change in the current context:** the operator iterates on the proposed tree ("keep `src/`", "no `images/` yet") in conversation, which is main-thread territory per the change-scope dimension.
- **Counter-dimension considered:** the inventory pass over an existing repository is read-heavy and self-contained (agent bias) — but the read volume is bounded by the fleet's YAML files, and the migration decision must stay visible; skill wins. The read-only conformance verdict on an existing layout is the agent case, and it is owned by `ha-esphome-fleet-reviewer`.

## When this skill activates

The user is setting up or restructuring an ESPHome **repository** — "set up a repo for my ESPHome devices", "meine ESPHome-Configs aufräumen", "wo soll das gemeinsame Zeug hin" — as opposed to writing a single device.

## When NOT to activate

- one device file, new or extended → `ha-esphome-config-scaffold` / `ha-esphome-config-augment`
- one package to cut, parameterise, or de-duplicate → `ha-esphome-package-author`
- the CI workflow that validates the fleet → `ha-esphome-ci-scaffold`
- a conformance verdict on an existing layout → `ha-esphome-fleet-reviewer` (read-only)
- portfolio-wide repository scaffolding that is not ESPHome-specific (Taskfile, pre-commit, Renovate, docs) → the inherited `project/` specs and their skills
- compiling, flashing, or fleet OTA rollout → the ESPHome toolchain / operator

## Hard rules

1. **Read `spec/ha/esphome-project-structure/en.md` first**, and `spec/ha/esphome-config-patterns/en.md` for anything that reaches into a device file. Do not generate a layout from memory.
2. **Plan before write on an existing repository.** Present the current tree, the target tree, and the per-file move/create/edit list; wait for explicit approval. Never move or delete a file the operator has not seen listed.
3. **`packages:` is the only reuse mechanism.** Emit packages in the mapping form with meaningful keys. Never introduce a `<<: !include` merge key; leave existing ones untouched and report them as findings for `ha-esphome-package-author`.
4. **Group `common/` by consumer.** Packages a device includes directly stay flat; building blocks only other packages include move into an ESPHome-domain subdirectory (`common/sensor/`, `common/binary_sensor/`, `common/text_sensor/`).
5. **The board package pulls in the base package.** A device states one board plus its feature packages — never both board and base.
6. **Credentials are `!env_var`, never `!secret` and never literals.** Every environment variable a scaffolded package reads gets documented in the same run, and `.gitignore` covers `.esphome/`, build directories, and `secrets.yaml`.
7. **Per-device API encryption key.** The base or board package consumes `key: ${api_key}`; the device file supplies `api_key: !env_var <DEVICE>_API_KEY`. Never a fleet-wide key in a shared package, never a bare `api:`.
8. **Components a device may override carry an `id:`.** Without one the merge concatenates instead of extending.
9. **No device authoring.** This skill creates the tree and the shared packages, not the device files — it hands off to `ha-esphome-config-scaffold`.
10. **Validation is reported, not skipped.** Where the toolchain is available, run `esphome config` for every existing device file after a restructure; where it is not, report it as the operator's open step.

## Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `mode` | no | auto-detected | `greenfield` (no device files yet) or `restructure` (existing ones found) |
| `config_root` | no | `src/` | where device YAML lives; existing root wins over the default |
| `board_families` | no | asked | the board(s) the fleet starts with — one board package each |
| `feature_concerns` | no | none | initial feature packages (`time`, `active-duration`, …) |
| `asset_tree` | no | omitted | `images/<device-type>/` when the fleet ships display assets |

## Pre-flight (every run, in order — abort on first failure)

1. Inventory the repository: existing YAML, an existing config root, `common/`-like directories, `include/` headers, `secrets.yaml`, `.gitignore`, and any `<<: !include` merge keys.
2. Decide `mode` from that inventory; on `restructure`, map every existing file to its target location.
3. Detect credential handling in use today (`!secret`, literals, `!env_var`) and list every variable the target packages will read.
4. Confirm the target tree and the move/create list with the operator before writing.

## Workflow

1. **Create the tree:** `<config_root>/` (device files, flat), `<config_root>/common/` (entry points flat, building blocks in domain subdirectories), `include/` (C++ lambda headers), `archive/` (retired devices), and the keyed asset tree when requested.
2. **Write the base package** — logger, `api:` with `encryption: {key: ${api_key}}`, `ota:` password-protected via `!env_var OTA_PASSWORD`, wifi with `ap:` fallback plus `captive_portal:`, the standard diagnostic entities, and `esphome.project.name` / `.version` — with a `defaults:` block for every variable not every consumer sets.
3. **Write one board package per declared family**, pulling in the base package and carrying that board's plumbing (platform, framework, flash/PSRAM, buses, pins). For known hardware, take the values from the device spec (`spec/ha/esp32-s3-box/en.md`), not from a generic template.
4. **Write the feature packages** the operator named, each covering one concern, each parameterised through `substitutions` with documented `defaults:`.
5. **On `restructure`:** move files per the approved list, rewrite device files to consume the new packages, and leave every legacy `<<: !include` in place while reporting it.
6. **Document the environment variables** — one table of variable, purpose, and which package reads it, in the repository's README or a `docs/` page — plus the `.gitignore` entries.
7. **Validate** every device file with `esphome config` where the toolchain is available; otherwise report it as the open caller step.
8. **Report:** the written tree, the packages created, every environment variable to be set, the legacy merge keys found, validation status, and `ha-esphome-config-scaffold` as the next entry point for the first device.

## Boundaries

- A device file → `ha-esphome-config-scaffold` / `ha-esphome-config-augment`
- One package's cut, parameters, or `!extend` / `!remove` shape → `ha-esphome-package-author`
- Fleet-wide validation in CI → `ha-esphome-ci-scaffold`
- A conformance verdict on the result → `ha-esphome-fleet-reviewer` (independent, read-only)
- Compile, flash, OTA rollout → the ESPHome toolchain / operator
