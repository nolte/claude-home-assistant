# Skill: `ha-hacs-release`

Status: draft

## Context

A Custom Integration is, as a rule, distributed through HACS, and `ha/hacs-release` defines the complete HACS-specific distribution layer: a valid `hacs.json`, the fact that HACS reads the installable version from the **tag name of the latest published GitHub release** (not `manifest.json:version`, which must nonetheless match the tag), the ZIP-release distribution model (`zip_release: true` + `filename: <domain>.zip`), the HACS/hassfest validation gate, and the `brands` registration. This layer sits on top of the portfolio's generic `release-automation` flow (release-drafter, `chore(release): <tag>` alignment, `reusable-release-publish`). The `ha/hacs-release` spec exists and is doc-anchored, but no skill or agent operationalizes it — a consumer integration has to wire `hacs.json`, the version alignment, and the ZIP CD by hand, where the common failures are a missing `filename` next to `zip_release`, a `manifest.json` version out of sync with the tag, and a bare tag without a published release object.

This skill closes that gap: it makes an existing integration HACS-release-ready by scaffolding and verifying the HACS layer per `ha/hacs-release`, on top of `release-automation` without redefining it. It is the distribution sibling of `ha-integration-ci-scaffold` (which owns the CI validation).

## Scope

Making exactly one existing `custom_components/<domain>/` integration HACS-release-ready: creating or verifying `hacs.json` (`name`, `zip_release` + `filename` for the ZIP model, `homeassistant` floor, `hide_default_branch`, optional keys), verifying the `manifest.json:version` alignment to the `v<MAJOR>.<MINOR>.<PATCH>` tag scheme, wiring the ZIP-asset CD obligation via a `nolte/gh-plumbing` reusable, and surfacing the `brands` registration and the generic `release-automation` prerequisites. The skill reads `ha/hacs-release`, decides the distribution model, and validates offline; it does not redefine the generic release flow.

## Goals

- Operationalize `ha/hacs-release` — make a consumer integration installable and updatable through HACS
- Produce a valid `hacs.json`, pairing `zip_release: true` with `filename: <domain>.zip` for the ZIP model, and set the HA-version floor and `hide_default_branch` sensibly
- Enforce that the version source is the GitHub release **tag**, that `manifest.json:version` equals it, and that a real published release (not a bare tag) is what HACS reads
- Wire the ZIP-asset CD obligation via a `nolte/gh-plumbing` reusable and surface `brands` and the `release-automation` prerequisites
- Add the HACS layer without redefining the generic release-automation rules

## Non-Goals

- The generic release publish flow (Draft → Published, version-bearing files, `chore(release)` alignment) — `release-automation`
- The CI validation workflow (hassfest / HACS action / pytest) — `ha-integration-ci-scaffold`
- The substance of `manifest.json` fields beyond their release relevance — `ha/integration-manifest`
- HACS categories other than `integration` (cards, themes, …) — out of scope
- Deploying/importing into a running HA instance — generation only

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "make this integration HACS-release-ready", "add a hacs.json", "set up ZIP release for HACS"
  - "mach die Integration HACS-release-fertig", "füge eine hacs.json hinzu"
- **MUST NOT** activate for the generic release publish flow (`release-automation`) or the CI validation workflow (`ha-integration-ci-scaffold`)

### Inputs

- **MUST** capture: `target_dir` (integration repo root)
- **MAY** capture: `distribution` (`zip` default, or `default-branch`), `min_ha_version` (`hacs.json:homeassistant`), and `min_hacs_version` (`hacs.json:hacs`)

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` is a git repo and `custom_components/<domain>/manifest.json` exists; read `domain`, `version`, `documentation`, `issue_tracker`, `codeowners`
- **MUST** read `ha/hacs-release` and detect an existing `hacs.json` and the release-automation wiring

### Generation rules

- **MUST** create/verify `hacs.json` carrying at least `name`; for the ZIP model set `zip_release: true` **and** `filename: <domain>.zip` together (integrations only); **SHOULD** set `homeassistant` and `hide_default_branch: true` when releases are the sole channel; **MAY** set `render_readme`, `hacs`, `country`
- **MUST** verify `manifest.json:version` aligns to the `v<MAJOR>.<MINOR>.<PATCH>` tag scheme and the required fields are present (field detail delegated to `ha/integration-manifest`)
- **MUST** state that HACS reads the version from the latest **published** release tag, not `manifest.json:version`, and that a bare tag without a release object is ignored
- **MUST** wire the ZIP-asset CD obligation (build + attach `<domain>.zip`) via a `nolte/gh-plumbing` reusable when `zip_release`, and delegate the validation workflow to `ha-integration-ci-scaffold`
- **MUST NOT** redefine the generic `release-automation` rules; reference them and surface `brands` registration as a checklist pointer to `home-assistant/brands`
- **MUST** verify HA/HACS internals against the official docs (`ha/upstream-docs-verification`; HACS publish rules anchored in `ha/hacs-release`)

### Validation & report

- **MUST** validate offline: `hacs.json` is valid; `zip_release` is paired with `filename`; `manifest.json:version` matches the tag scheme; the ZIP-CD obligation and validation gate are wired or named; `brands` is surfaced
- **MUST** deliver a CONFORMANT / NEEDS-WORK report keyed to the `ha/hacs-release` acceptance criteria plus the changed file paths

### Prohibitions

- **MUST NOT** set `zip_release` without `filename` (or vice versa)
- **MUST NOT** redefine or duplicate the generic release-automation flow
- **MUST NOT** deploy to or import into a running HA instance

## Acceptance criteria

- [ ] `hacs.json` is valid; `zip_release: true` is paired with `filename: <domain>.zip` for the ZIP model
- [ ] `manifest.json:version` aligns to the `v<MAJOR>.<MINOR>.<PATCH>` tag scheme
- [ ] The version-source rule (published release tag, not `manifest.json`) is stated
- [ ] The ZIP-asset CD obligation is wired via a `nolte/gh-plumbing` reusable or named; the validation gate is delegated to `ha-integration-ci-scaffold`
- [ ] `brands` registration and the `release-automation` prerequisites are surfaced
- [ ] Report names the changed file paths, keyed to `ha/hacs-release`

## Open questions

- **Reusable coverage**: does `nolte/gh-plumbing` already ship the ZIP-asset build reusable, or does this skill define the obligation and hand it to a follow-up? `ha/hacs-release` names the reusable layer.
- **Default-branch distribution**: `distribution: default-branch` is a fallback. When is it ever preferable to ZIP release, given `hide_default_branch` is the recommended end state?
- **`brands` automation**: `brands` registration is a PR to `home-assistant/brands`. Is that a manual checklist item forever, or a candidate for a future skill?
