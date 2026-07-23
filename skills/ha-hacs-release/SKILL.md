---
name: ha-hacs-release
description: "Makes an existing Home Assistant Custom Integration HACS-release-ready by scaffolding and verifying the HACS-specific distribution layer defined in spec/ha/hacs-release — a valid hacs.json (name, zip_release plus filename, homeassistant floor, hide_default_branch, render_readme), the manifest.json version aligned to the vMAJOR.MINOR.PATCH release-tag scheme, the ZIP-release CD obligation (build and attach the domain.zip asset), and the brands registration pointer. Operationalizes the HACS layer on top of the generic release flow (spec/project/release-automation) without redefining it. Activate on \"make this integration HACS-release-ready\", \"add a hacs.json\", \"set up ZIP release for HACS\", or equivalent German requests. Do not activate for the generic release publish flow itself (nolte-shared:release-publish-trigger), the CI validation workflow (ha-integration-ci-scaffold), the integration code (ha-integration-scaffold), or deploying to a live HA instance."
tags: [home-assistant, custom-integration, hacs, release]
phase: close-release
summary: "Makes an existing HA Custom Integration HACS-release-ready — valid hacs.json, tag-aligned manifest version, ZIP-release CD obligation, and brands pointer."
summary_de: "Macht eine bestehende HA-Custom-Integration HACS-release-fertig — valide hacs.json, tag-abgeglichene Manifest-Version, ZIP-Release-CD-Pflicht und brands-Pointer."
use_when:
  - "you want to make an integration installable through HACS"
  - "you want to add a hacs.json to the integration"
  - "you want to set up a ZIP release for HACS"
dont_use_when:
  - situation: "You need the CI validation workflow (hassfest / HACS action / pytest)"
    alternative: ha-integration-ci-scaffold
  - situation: "You need to generate the integration code itself"
    alternative: ha-integration-scaffold
see_also:
  - ha-integration-ci-scaffold
  - ha-integration-scaffold
  - ha-integration-solution
  - ha-integration-review
---

# HA HACS Release

Spec: `spec/claude/ha-hacs-release/en.md` (EN canonical) / `spec/claude/ha-hacs-release/de.md` (DE translation).

This skill operationalizes `spec/ha/hacs-release/en.md` — the HACS-specific distribution layer (`hacs.json`, version alignment, ZIP release, `brands`) — on top of the portfolio's generic `release-automation` flow. It closes the audit finding that the `ha/hacs-release` spec exists but no skill or agent makes a consumer integration HACS-release-ready.

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user reads back `hacs.json`, the version-alignment check, and the ZIP-CD wiring and confirms the distribution model; a skill keeps this on the visible command surface.
- **Mid-flow interactivity** — the ZIP-vs-default-branch distribution choice, the minimum HA version, and whether `brands` is already registered are per-run dialogues the user confirms.
- **Orchestrator-leaning** — it surfaces the generic `release-automation` prerequisites and points at `nolte/gh-plumbing` reusable workflows rather than duplicating release logic; the skill-orchestrates default keeps it in skill form.
- Counter-dimension considered: the verify loop could be an agent, but the distribution-model decision and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill to make an existing integration installable and updatable through HACS — scaffold or verify `hacs.json`, the manifest/tag version alignment, and the ZIP-release CD obligation — per `ha/hacs-release`.

## When NOT to activate

- the generic release publish flow (Draft → Published, `chore(release)` alignment, version-bearing files) → `release-automation`
- the CI validation workflow (hassfest / HACS action / pytest) → `ha-integration-ci-scaffold`
- generating the Python integration code → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **All generated config is English**, per the portfolio config-language rule.
2. **`hacs.json` is mandatory and minimal-correct.** It carries at least `name`; for the ZIP distribution model it sets `zip_release: true` **plus** `filename: <domain>.zip` (HACS requires both together, integrations only). SHOULD set `homeassistant` (minimum HA version) and `hide_default_branch: true` once releases are the sole channel; MAY set `render_readme`, `hacs`, `country`.
3. **Version source is the release tag.** HACS reads the installable version from the **tag name of the latest published GitHub release**, not `manifest.json:version`. The `manifest.json` `version` is still required and **MUST** equal the release tag. Use the tag scheme `v<MAJOR>.<MINOR>.<PATCH>` produced by `release-drafter`.
4. **A real GitHub release, not a bare tag.** State that HACS ignores a tag without a published release object; the generic `release-automation` flow (`reusable-release-publish`) produces the release.
5. **ZIP-release CD obligation.** When `zip_release: true`, the release CD must build and attach `<domain>.zip` (the `custom_components/<domain>/` tree) as a release asset; point at the `nolte/gh-plumbing` reusable that does this rather than inlining it.
6. **Do not redefine `release-automation`.** Reference the generic Draft → Published, version-bearing-files, and `chore(release): <tag>` alignment rules; add only the HACS-specific layer. `brands` registration is a pointer to the `home-assistant/brands` repo, not generated here.
7. **Verify HA/HACS internals against the official docs** (see `spec/ha/upstream-docs-verification/en.md`; the HACS publish rules are anchored in `ha/hacs-release`).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root of the integration repository |
| `distribution` | no | `zip` | `zip` (recommended) or `default-branch` |
| `min_ha_version` | no | asked when relevant | `hacs.json:homeassistant` floor |
| `min_hacs_version` | no | unset | `hacs.json:hacs` floor |

## Pre-flight (in order — abort on first failure)

1. `git -C <target_dir> rev-parse --is-inside-work-tree`.
2. `custom_components/<domain>/manifest.json` exists; read `domain`, `version`, `documentation`, `issue_tracker`, `codeowners`.
3. Read `ha/hacs-release`; detect an existing `hacs.json` and the release-automation wiring.

## Workflow

### 1) Resolve and confirm

State `domain`, the distribution model, the min HA version, and the current `manifest.json:version` vs. the tag scheme in one paragraph. Wait for confirmation.

### 2) Apply

- `hacs.json` — create/verify (`name`, `zip_release` + `filename` for ZIP, `homeassistant`, `hide_default_branch`, optional keys)
- `manifest.json` — verify `version` aligns to the `v<MAJOR>.<MINOR>.<PATCH>` tag scheme and the required fields are present (delegating field detail to `ha/integration-manifest`)
- CI/CD — wire the ZIP-asset build via the `nolte/gh-plumbing` reusable and the HACS/hassfest validation gate (delegating the validation workflow to `ha-integration-ci-scaffold`); surface the `brands` registration as a checklist item

### 3) Validate & report

Validate offline (`hacs.json` valid; `zip_release` paired with `filename`; `manifest.json:version` matches the tag scheme; the ZIP-CD obligation and validation gate are wired or named; `brands` surfaced) and emit a CONFORMANT / NEEDS-WORK report keyed to the `ha/hacs-release` acceptance criteria plus the changed file paths.

## Boundaries

- Generic release publish flow → `release-automation`
- CI validation workflow (hassfest / HACS action / pytest) → `ha-integration-ci-scaffold`
- `manifest.json` field substance → `ha/integration-manifest`
