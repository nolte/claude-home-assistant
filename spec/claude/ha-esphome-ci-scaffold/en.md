# Skill: `ha-esphome-ci-scaffold`

Status: draft

## Context

`spec/ha/esphome-project-structure` §Validation states the rule that distinguishes a fleet repository from a folder of files: `esphome config` runs for **every** device file on every change, because a package edit breaks devices whose files nobody touched — and it records that the portfolio's own fixture repository does not do this, which is how an unresolvable include survived in a device config. This skill is the operationalisation of that rule, and the ESPHome sibling of `ha-integration-ci-scaffold`.

## Scope

One repository per invocation: the pull-request validation workflow, the separately-cadenced compile workflow, the static checks beside them, the version pin, and the environment-variable strategy that lets a validation run resolve credentials without a real secret.

## Goals

- Make the fleet-wide validation the default rather than a diff-scoped matrix that misses the characteristic failure
- Separate the fast schema pass from the slow compile so per-pull-request cost stays bounded as the fleet grows
- Give credentials in CI a stated, documented resolution path that never requires a real secret for schema validation
- Emit workflows that satisfy the inherited GitHub-Actions rules rather than a hand-rolled YAML
- State honestly what the resulting pipeline does and does not prove

## Non-Goals

- The repository layout and package architecture (owned by `ha-esphome-fleet-scaffold`)
- Fixing what CI finds (owned by `ha-esphome-package-author` / `ha-esphome-config-augment`)
- Triaging a red run (owned by `workflow-health-triage`)
- Auditing an existing pipeline (owned by `cicd-pipeline-reviewer` and `ha-esphome-fleet-reviewer`)
- Flashing and OTA rollout from CI — the grounding spec places fleet rollout out of scope

## Requirements

- **MUST** read `spec/ha/esphome-project-structure/en.md` §Validation plus the inherited `spec/project/github-actions-best-practices/` and `spec/project/continuous-integration/` before emitting a workflow
- **MUST** emit a validation job that runs `esphome config` for **every** device file on every change, never a diff-scoped subset
- **MUST** separate `esphome compile` onto a scheduled or pre-release cadence
- **MUST** pin the ESPHome version CI uses and state that a bump is a reviewed change
- **MUST** document how `!env_var` credentials resolve in CI and **MUST NOT** let a placeholder credential reach an artifact that could be flashed
- **MUST** follow the inherited workflow rules: digest-pinned actions, least-privilege permissions, a concurrency group, no untrusted input in a `run:` block, and cache keys that cannot mask a failure
- **MUST** fail the job on any device file that cannot be validated, and **MUST NOT** silently skip one
- **MUST** report what the static checks genuinely cover, rather than implying that a whitespace hook or a security scanner validates YAML
- **MUST NOT** emit a deploy, flash, or OTA-rollout step

## Acceptance Criteria

- [ ] The emitted validation workflow iterates every device file in the config root and fails on the first invalid one while still reporting the rest
- [ ] The compile job runs on its own cadence and reuses the same version pin and environment strategy
- [ ] The report names every environment variable CI sets and where its value comes from
- [ ] The report states what the pipeline does not prove — on-device behaviour above all

## Open Questions

_None at this time._
