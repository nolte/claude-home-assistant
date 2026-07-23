---
name: ha-integration-ci-scaffold
description: "Scaffolds the Home-Assistant-specific CI validation for a Custom Integration repository — a GitHub Actions workflow running hassfest and the HACS validation action on push and pull_request, plus a pytest job using pytest-homeassistant-custom-component across a Python matrix. Complements the portfolio's generic lint/release CI rather than replacing it; adds only the HA-domain validators. Grounded in spec/ha/dev-workflow (hassfest) and spec/ha/hacs-release (HACS validation gate). Activate on \"add hassfest and HACS validation to CI\", \"set up the integration CI workflow\", \"add a pytest matrix job for the integration\", or equivalent German requests. Do not activate for the generic repo scaffold (nolte-shared:project-structure-apply), the release publish flow (spec/project/release-automation and ha-hacs-release), the Python code itself (ha-integration-scaffold), or deploying to a live HA instance."
tags: [home-assistant, custom-integration, ci, hassfest]
phase: design
summary: "Scaffolds the HA-specific CI validators for a Custom Integration repo — hassfest, the HACS validation action, and a pytest matrix — complementing the generic portfolio CI."
summary_de: "Scaffolded die HA-spezifischen CI-Validatoren für ein Custom-Integration-Repo — hassfest, HACS-Validierungs-Action und eine pytest-Matrix — als Ergänzung zur generischen Portfolio-CI."
use_when:
  - "you want to add hassfest and HACS validation to CI"
  - "you want a pytest matrix job for the integration"
dont_use_when:
  - situation: "You want the release publish flow with version alignment"
    alternative: ha-hacs-release
  - situation: "You need to generate the Python integration code"
    alternative: ha-integration-scaffold
see_also:
  - ha-integration-scaffold
  - ha-hacs-release
  - ha-test-harness-augment
  - ha-quality-scale-audit
  - ha-dev-workflow-apply
---

# HA Integration CI Scaffold

Spec: `spec/claude/ha-integration-ci-scaffold/en.md` (EN canonical) / `spec/claude/ha-integration-ci-scaffold/de.md` (DE translation).

This skill scaffolds the **HA-domain CI validators** — hassfest, the HACS validation action, and the pytest matrix — that the generic portfolio CI (`nolte-shared:project-structure`, `quality-gate`, `release-automation`) does not emit. It closes the audit finding that `ha-integration-scaffold` claims hassfest CI is "handled by the project-structure scaffold" when in fact nothing HA-specific is generated. The generated YAML targets the **consumer integration repository**, not this plugin repo.

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user reads back the generated `validate.yml` and the pytest matrix and confirms the Python-version set; a skill keeps this on the visible command surface, like the sibling scaffolders.
- **Mid-flow interactivity** — the Python-version matrix, whether the repo is HACS-distributed (so the HACS action applies), and the ZIP-mode toggle are per-run dialogues the user confirms.
- **Bounded, inline generation** — one or two workflow files fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft loop could be an agent, but the matrix and delimitation decisions belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add the HA-specific CI validation to a Custom Integration repo — hassfest + HACS validation + a pytest matrix — when the repo has the integration code but no HA-domain CI gate yet.

## When NOT to activate

- the generic repo scaffold (lint, pre-commit, release-drafter wiring) → `nolte-shared:project-structure`
- the release publish flow (Draft → Published, version alignment, ZIP asset) → `release-automation` / `ha-hacs-release`
- generating the Python integration code → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **All generated CI YAML is English**, per the portfolio config-language rule, regardless of the conversation language.
2. **hassfest via the official action.** Add a job step `uses: home-assistant/actions/hassfest@master` after `actions/checkout@v4` — the canonical custom-integration hassfest validator.
3. **HACS validation via `hacs/action@main`.** When the repo is HACS-distributed, add a step `uses: hacs/action@main` with `category: integration` — HACS validates with the same code it uses at install time.
4. **pytest matrix on `pytest-homeassistant-custom-component`.** Add a pytest job over a Python-version matrix (the versions HA currently supports), installing the integration's test deps and running `pytest` with coverage; align with `ha/test-harness`.
5. **Triggers.** Run on `push` and `pull_request`; a nightly `schedule` (`cron: "0 0 * * *"`) is a MAY (catches upstream HA/HACS breakage).
6. **Complement, do not duplicate.** Do not re-emit lint / pre-commit / release jobs the generic CI owns; add only the HA-domain validators. Reference `nolte/gh-plumbing` reusable workflows where the portfolio already provides one instead of inlining bespoke logic.
7. **Verify HA internals against the official docs.** Confirm the current action refs and supported Python matrix before pinning them (see `spec/ha/upstream-docs-verification/en.md`; hassfest per `spec/ha/dev-workflow/en.md`, HACS gate per `spec/ha/hacs-release/en.md`).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root of the integration repository |
| `hacs_distributed` | no | inferred from `hacs.json` presence | whether to add the HACS validation step |
| `python_matrix` | no | current HA-supported versions | the pytest Python-version matrix |
| `nightly` | no | `true` | add the nightly `schedule` trigger |

## Pre-flight (in order — abort on first failure)

1. `git -C <target_dir> rev-parse --is-inside-work-tree`.
2. `custom_components/<domain>/manifest.json` exists; read `domain`. Detect `hacs.json` for `hacs_distributed`.
3. `.github/workflows/validate.yml` does not already carry hassfest/HACS steps (else offer to extend, not overwrite).

## Workflow

### 1) Resolve and confirm

State `domain`, the Python matrix, whether the HACS step applies, and the nightly toggle in one paragraph. Wait for confirmation.

### 2) Generate

- `.github/workflows/validate.yml` — a `validate` job (`actions/checkout@v4` → `home-assistant/actions/hassfest@master` → `hacs/action@main` with `category: integration` when `hacs_distributed`) and a `pytest` job over the `python_matrix`, on `push` / `pull_request` (+ nightly `schedule` when `nightly`)

### 3) Validate & report

Validate offline (YAML parses; hassfest and — when applicable — the HACS step present with `category: integration`; pytest job over the matrix; no duplication of generic lint/release jobs) and emit a CONFORMANT / NEEDS-WORK report keyed to the acceptance criteria plus the changed file paths and the quality-scale marker (**bronze** floor — hassfest is a Bronze validation gate).

## Boundaries

- Generic repo scaffold / lint CI → `nolte-shared:project-structure`
- Release publish + version alignment + ZIP asset → `release-automation` / `ha-hacs-release`
- The pytest tests themselves → `ha-test-harness-augment`
