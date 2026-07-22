# Skill: `ha-integration-ci-scaffold`

Status: draft

## Context

A quality Custom Integration is validated in CI by two HA-domain gates that the generic portfolio CI does not emit: **hassfest** (`home-assistant/actions/hassfest@master`), which validates the manifest, strings, and service definitions (a Bronze floor per `ha/dev-workflow`), and the **HACS validation action** (`hacs/action@main` with `category: integration`), which validates the repository the same way HACS does at install time (`ha/hacs-release`). Alongside them runs a **pytest matrix** on `pytest-homeassistant-custom-component` (`ha/test-harness`). `ha-integration-scaffold` currently claims hassfest CI is "handled by the project-structure scaffold", but the generic `nolte-shared:project-structure` scaffold emits lint / pre-commit / release wiring, not these HA-specific validators — so a scaffolded integration has no hassfest or HACS gate.

This skill closes that gap: it scaffolds the HA-domain CI validation for a Custom Integration repository — hassfest, the HACS action, and the pytest matrix — as a GitHub Actions workflow in the **consumer** repo, complementing rather than replacing the generic CI. It is the CI-validation sibling of `ha-hacs-release` (which owns the HACS distribution layer).

## Scope

Scaffolding one HA-domain CI validation workflow into a Custom Integration repository: a `.github/workflows/validate.yml` with a `validate` job (`actions/checkout@v4` → `home-assistant/actions/hassfest@master` → `hacs/action@main` with `category: integration` when HACS-distributed) and a `pytest` job over a Python-version matrix, triggered on `push` / `pull_request` (+ an optional nightly `schedule`). The skill reads `domain`, detects HACS distribution, decides the matrix, and validates offline; it does not emit lint/release jobs the generic CI owns.

## Goals

- Emit the HA-domain CI validators (hassfest + HACS action + pytest matrix) that the generic portfolio CI does not, resolving the `ha-integration-scaffold` hassfest-CI claim
- Use the canonical action refs — `home-assistant/actions/hassfest@master` and `hacs/action@main` (`category: integration`)
- Run a pytest matrix on `pytest-homeassistant-custom-component` aligned with `ha/test-harness`
- Complement, not duplicate, the generic lint/release CI, and reference `nolte/gh-plumbing` reusables where the portfolio already provides them
- Keep all generated CI YAML English per the portfolio config-language rule

## Non-Goals

- The generic repo scaffold (lint, pre-commit, release-drafter wiring) — `nolte-shared:project-structure`
- The release publish flow (Draft → Published, version alignment, ZIP asset) — `release-automation` / `ha-hacs-release`
- Generating the Python integration code — `ha-integration-scaffold`
- The pytest tests themselves — `ha-test-harness-augment`
- Deploying/importing into a running HA instance — generation only

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add hassfest and HACS validation to CI", "set up the integration CI workflow", "add a pytest matrix job for the integration"
  - "richte die Integration-CI ein", "füge hassfest/HACS-Validierung zur CI hinzu"
- **MUST NOT** activate for the generic repo scaffold (`nolte-shared:project-structure`) or the release publish flow (`release-automation` / `ha-hacs-release`)

### Inputs

- **MUST** capture: `target_dir` (integration repo root)
- **MAY** capture: `hacs_distributed` (else inferred from `hacs.json` presence), `python_matrix` (else the current HA-supported versions), and `nightly` (default `true`)

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` is a git repo and `custom_components/<domain>/manifest.json` exists; read `domain` and detect `hacs.json`
- **MUST NOT** overwrite an existing `validate.yml` that already carries hassfest/HACS steps — offer to extend instead

### Generation rules

- **MUST** generate `.github/workflows/validate.yml` in English with a `validate` job running `actions/checkout@v4` then `home-assistant/actions/hassfest@master`
- **MUST** add a `hacs/action@main` step with `category: integration` when the repo is HACS-distributed
- **MUST** add a `pytest` job over a Python-version matrix installing the integration's test deps and running `pytest` (with coverage), aligned with `ha/test-harness`
- **MUST** trigger on `push` and `pull_request`; **MAY** add a nightly `schedule` (`cron: "0 0 * * *"`)
- **MUST NOT** re-emit lint / pre-commit / release jobs the generic CI owns; **SHOULD** reference `nolte/gh-plumbing` reusable workflows where one exists
- **MUST** verify the current action refs and supported Python matrix against the official docs (`ha/upstream-docs-verification`; hassfest per `ha/dev-workflow`, HACS gate per `ha/hacs-release`)

### Validation & report

- **MUST** validate offline: the YAML parses; the hassfest step is present; the HACS step is present with `category: integration` when applicable; the pytest matrix job is present; no lint/release duplication
- **MUST** deliver a CONFORMANT / NEEDS-WORK report keyed to these acceptance criteria plus the changed file paths and the quality-scale marker (**bronze** — hassfest is a Bronze validation gate)

### Prohibitions

- **MUST NOT** overwrite an existing HA-CI workflow
- **MUST NOT** duplicate the generic lint/release CI
- **MUST NOT** deploy to or import into a running HA instance

## Acceptance criteria

- [ ] `.github/workflows/validate.yml` is generated in English on `push` / `pull_request`
- [ ] The hassfest step uses `home-assistant/actions/hassfest@master`
- [ ] The HACS step uses `hacs/action@main` with `category: integration` when HACS-distributed
- [ ] A pytest matrix job runs on `pytest-homeassistant-custom-component`
- [ ] No generic lint/release job is duplicated; reusables are referenced where present
- [ ] Report names the changed file paths and the quality-scale marker **bronze**

## Open questions

- **Reusable vs. inline**: does `nolte/gh-plumbing` already ship a reusable HA-validate workflow to call instead of inlining hassfest/HACS/pytest? If so, this skill wires the reusable.
- **Python matrix source**: the matrix should track HA's currently-supported Python versions. Is the version set pinned in a portfolio config, or resolved per run against the docs?
- **hassfest for HACS-only repos**: hassfest validates core-style integrations; a purely-HACS integration may need a narrower config. Which hassfest checks are always applicable?
