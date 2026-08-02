---
name: ha-esphome-ci-scaffold
description: "Scaffolds the CI that validates an ESPHome fleet per spec/ha/esphome-project-structure §Validation — a pull-request workflow running esphome config for every device file on every change rather than only the diff, because a package edit breaks devices nobody touched, plus a scheduled or pre-release job for the far slower esphome compile, the static checks alongside them, a pinned ESPHome version, and the environment-variable strategy that lets a validation run resolve credentials without a secret ever being real. Emits workflows following the inherited GitHub-Actions rules: digest-pinned actions, least-privilege permissions, concurrency groups, no untrusted input in a run block. Activate on \"add CI for my ESPHome repo\", \"validate all device configs in CI\", or equivalent German requests. Do not activate to lay out the repository (ha-esphome-fleet-scaffold), to fix a red run (workflow-health-triage), to author CI for a custom integration (ha-integration-ci-scaffold), or to compile and flash locally."
tags: [home-assistant, esphome, ci, yaml]
phase: build
summary: "Scaffolds ESPHome fleet CI — fleet-wide esphome config on every change, scheduled compile, static checks, pinned version, env-var strategy."
summary_de: "Scaffoldet die CI einer ESPHome-Fleet — flottenweites esphome config bei jeder Änderung, geplanter Compile, statische Checks, gepinnte Version, Env-Var-Strategie."
use_when:
  - "your ESPHome repository has no CI validation and a package edit can break devices silently"
  - "you want every device config validated on every pull request, not only the changed files"
  - "you want the slow compile step separated from the fast per-PR validation"
dont_use_when:
  - situation: "You want the repository layout and the package tree"
    alternative: ha-esphome-fleet-scaffold
  - situation: "You want CI for a Python Home Assistant custom integration"
    alternative: ha-integration-ci-scaffold
  - situation: "You want a verdict on whether the fleet's validation coverage conforms"
    alternative: ha-esphome-fleet-reviewer
  - situation: "You want the package or device defect the pipeline found fixed"
    alternative: ha-esphome-package-author
see_also:
  - ha-esphome-fleet-scaffold
  - ha-esphome-fleet-reviewer
  - ha-integration-ci-scaffold
  - ha-esphome-solution
---

# HA ESPHome CI Scaffold

Spec: `spec/claude/ha-esphome-ci-scaffold/en.md` (EN canonical) / `spec/claude/ha-esphome-ci-scaffold/de.md` (DE translation). Grounding spec: `spec/ha/esphome-project-structure/en.md` §Validation. Workflow mechanics follow the inherited `spec/project/github-actions-best-practices/` and `spec/project/continuous-integration/`.

Scaffolds the validation pipeline of an ESPHome fleet — the one gate that catches the failure mode a shared-package repository is built to produce.

## Why this is a skill, not an agent

- **Mid-flow approval is the contract (decisive):** the credential strategy for a validation run, the compile cadence, and the ESPHome version floor are operator decisions with cost and security consequences.
- **Quick, targeted change in the current context:** one or two workflow files in the repository the conversation is scoped to.
- **Counter-dimension considered:** enumerating the fleet and the existing pipeline is self-contained (agent bias), but the resulting workflow is iterated with the operator; the read-only audit of an existing pipeline is a different job and belongs to `cicd-pipeline-reviewer` / `ha-esphome-fleet-reviewer`.

## When this skill activates

The user wants an ESPHome repository validated automatically — "ESPHome-Configs in CI prüfen", "add a GitHub Actions workflow for my device configs", "how do I catch a broken package before it reaches a device".

## When NOT to activate

- the repository tree and the package architecture → `ha-esphome-fleet-scaffold`
- a red run to triage → `workflow-health-triage`
- an audit of the existing pipeline → `cicd-pipeline-reviewer` (general) / `ha-esphome-fleet-reviewer` (ESPHome-specific)
- CI for a Python custom integration → `ha-integration-ci-scaffold`
- local compile, flash, or OTA rollout → the ESPHome toolchain / operator

## Hard rules

1. **Read `spec/ha/esphome-project-structure/en.md` §Validation first**, plus the inherited GitHub-Actions and CI specs and any workflow the repository already has.
2. **Validate the whole fleet, not the diff.** `esphome config` runs for **every** device file on every change; a diff-scoped matrix is exactly what lets a package edit break an untouched device.
3. **Separate the cadences.** Schema validation runs per pull request; `esphome compile` runs scheduled or pre-release, because compile time grows with the fleet while the fleet-wide `config` pass already catches the characteristic failure.
4. **Pin the ESPHome version** used by CI and state that a bump is a reviewed change — the same discipline the device configs' `min_version` follows.
5. **A validation run needs no real credential.** Resolve `!env_var` credentials in CI through workflow-level placeholder values or repository secrets, and never let a placeholder reach a compile artifact that could be flashed. Document which variables the run sets and where their values come from.
6. **Follow the inherited workflow rules:** actions pinned by digest, least-privilege `permissions:`, a concurrency group per ref, no untrusted input interpolated into a `run:` block, and caching keyed so a stale cache cannot mask a failure.
7. **Keep the repository's static checks alongside**, and be honest in the report about what they do and do not cover — a pre-commit config with whitespace hooks is not YAML validation, and neither is a security scanner.
8. **Fail loudly, never skip silently.** A device file that cannot be validated fails the job; a missing toolchain is reported as an open step, never swallowed.
9. **No deploy, no flash, no OTA rollout from CI** in this scaffold. Fleet rollout is a separate decision the grounding spec places out of scope.

## Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `config_root` | no | auto-detected | where device YAML lives |
| `esphome_version` | no | asked | the pinned version CI validates with |
| `compile_cadence` | no | scheduled nightly | `scheduled`, `pre-release`, or `manual` |
| `credential_mode` | no | placeholder defaults | how `!env_var` credentials resolve in CI |
| `platform` | no | GitHub Actions | the CI platform in use |

## Pre-flight (every run, in order — abort on first failure)

1. Inventory the fleet: every device file under the config root, the packages they consume, and every environment variable those packages read.
2. Inventory existing CI: workflows, static checks, and whether any ESPHome validation already runs.
3. Determine the credential strategy — which variables need a value for `config` to resolve, and whether a placeholder default or a repository secret supplies it.
4. Confirm the version pin, the compile cadence, and the workflow file names with the operator before writing.

## Workflow

1. Write the **validation workflow**: checkout, a pinned Python/ESPHome setup, the environment-variable block, and a step that iterates every device file with `esphome config`, reporting each file's result and failing on the first error while still listing the rest.
2. Write the **compile workflow** on the chosen cadence, reusing the same version pin and environment strategy, with the build artifacts treated as immutable per the inherited delivery spec.
3. Wire the **static checks** — the repository's pre-commit configuration and a YAML linter where none exists — as a separate, fast job.
4. Document what CI covers and what it does not, in the repository's README or docs page: fleet-wide schema validation yes, on-device behaviour no.
5. **Report:** the workflows written, the version pinned, the environment variables CI sets and where their values come from, the cadence split, what the static checks actually cover, and the first run the operator should watch.

## Boundaries

- Repository layout and package architecture → `ha-esphome-fleet-scaffold`
- Package-level fixes for a validation failure → `ha-esphome-package-author`
- Device-level fixes → `ha-esphome-config-augment`
- A red run → `workflow-health-triage`
- Flash and OTA rollout → out of scope; the operator and the ESPHome toolchain own those
