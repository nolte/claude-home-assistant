# HA Integration: HACS Release and Distribution

Status: draft

## Context

A Home Assistant **custom integration** is, as a rule, distributed through [HACS](https://www.hacs.xyz/) (Home Assistant Community Store). HACS installs and updates the integration directly from its GitHub repository. This spec defines the complete, CI-covered release and distribution process: which artifacts the repository must carry (`hacs.json`, `manifest.json`, directory layout), how GitHub releases relate to the version HACS displays, how the version number is kept consistently in sync, and which reusable workflows in [`nolte/gh-plumbing`](https://github.com/nolte/gh-plumbing) carry the process.

**The central mechanism — source of truth for the version:** HACS sets the displayed and installable version from the **tag name of the most recently published GitHub release**, not from the `version` field of `manifest.json` ([hacs.xyz/docs/publish/start](https://www.hacs.xyz/docs/publish/start/): "If the repository uses GitHub releases, the tag name from the latest release is used to set the remote version. Just publishing tags is not enough, you need to publish releases."). A bare git tag is insufficient — a real GitHub release object must exist. The `version` field of `manifest.json` is nevertheless required for custom integrations (HA loader, hassfest, the installed version's self-report) and **must** match the release tag; it is, however, not the lever HACS reads for version selection.

**Relationship to the existing release system:** This portfolio operates an established flow normed by `release-automation` (in `claude-shared`): `release-drafter` derives the next version on `develop` push and maintains a draft release; a `chore(release): <tag>` alignment commit sets the version-bearing files; `reusable-release-publish.yml` verifies alignment before `draft=false` and publishes the release; `reusable-release-cd-refresh-master.yml` refreshes the presentation branch. The generic "version-bearing files" mechanism already recognizes HACS integrations (`custom_components/<domain>/manifest.json` → `$.version`). This spec adds the HACS-specific layer (`hacs.json`, HACS/hassfest validation, ZIP distribution, `brands`) and makes the version alignment binding for the HACS case without redefining the generic rules.

**Scope:** custom integrations (Python) under `custom_components/<domain>/`. Two distribution tiers are distinguished: **custom repository** (the user adds the repo URL into HACS manually — the baseline) and **default store** (inclusion in the official `hacs/default` index — an additional, stricter tier).

## Goals

- Cover the full release process with CI so that every published HACS release is produced reproducibly and without manual file edits
- Ensure that the GitHub release tag, the `manifest.json` `version`, and the version HACS displays always carry the same version number, and that a matching tag always exists for every release
- Make the required artifacts (`hacs.json`, `manifest.json`, directory layout) binding
- Anchor HACS and hassfest validation as a CI gate on push and pull request
- Norm ZIP release as the recommended distribution model and define the resulting CD obligation (build and attach the asset)
- Clearly delimit the pre-release mechanism as a beta channel and the `brands` handling
- Describe default-store inclusion as an optional, clearly bounded additional tier
- Name the load-bearing reusable workflows in `nolte/gh-plumbing` rather than duplicating CI logic per integration

## Non-Goals

- The generic rules from `release-automation` (Draft → Published, version-bearing files, `chore(release)` alignment, permissions) — this spec references them, it does not redefine them
- The substantive definition of `manifest.json` fields beyond their release relevance — that belongs to `ha/integration-manifest`
- Lovelace cards, themes, Python scripts, AppDaemon apps and other HACS categories — this spec covers only the `integration` category
- The substantive composition of release notes — that belongs to `release-skill-layer` (skill `release-notes-curate`)
- The concrete implementation of the gh-plumbing reusables (YAML details) — the spec defines their contract, the code lives in `nolte/gh-plumbing`
- Distribution via the official Home Assistant add-on repository or as a core integration

## Requirements

### Repository structure and required artifacts

- **MUST** place all integration files in exactly one subdirectory `custom_components/<domain>/`; exactly **one** integration per repository is allowed — with multiple subdirectories HACS manages only the first (a silent failure mode) ([publish/integration](https://www.hacs.xyz/docs/publish/integration/))
- **MUST** carry a `manifest.json` under `custom_components/<domain>/` setting at least `domain`, `documentation`, `issue_tracker`, `codeowners`, `name`, and `version` — the remaining manifest rules are governed by `ha/integration-manifest`
- **MUST** carry a `hacs.json` in the repository root (see `### hacs.json`)
- **MUST** create a real GitHub release object for every release (not just a tag); otherwise HACS falls back to the default-branch files and ignores release-based version selection ([publish/start](https://www.hacs.xyz/docs/publish/start/), [publish/integration](https://www.hacs.xyz/docs/publish/integration/))

### `hacs.json`

The `hacs.json` in the repo root controls how HACS treats the repository. Only `name` is required; the remaining fields are optional and form an open set.

- **MUST** set `name` — the integration's display name in the HACS UI
- **MUST** use the standard layout `custom_components/<domain>/` and therefore **not** set `content_in_root` (default `false`); `content_in_root: true` is reserved for repositories whose content sits directly in the root — atypical for integrations
- **MUST** set `zip_release: true` and accompany it with `filename: <domain>.zip` — the chosen distribution model (see `### ZIP release distribution`); per HACS, `zip_release` is supported for integrations only ([publish/include](https://www.hacs.xyz/docs/publish/include/))
- **SHOULD** set `homeassistant` to the minimum required Home Assistant version so HACS blocks installs on too-old cores
- **SHOULD** set `hide_default_branch: true` once distribution happens exclusively via releases — so HACS does not additionally offer the default branch for installation
- **MAY** set `hacs` to the minimum required HACS version, `render_readme: true` (render README instead of `info.md`), `country`, and `persistent_directory`
- **MUST** be valid JSON and live in the repo root — the HACS Action's `hacsjson` check verifies its existence

### Version source: GitHub release and tag

- **MUST** accept that HACS derives the remote version from the **tag name** of the most recently published release; HACS offers the user a selection of the **five newest** releases plus the default branch ([publish/integration](https://www.hacs.xyz/docs/publish/integration/))
- **MUST** use the tag scheme `v<MAJOR>.<MINOR>.<PATCH>` (e.g. `v0.1.2`), as produced by the portfolio-wide `release-drafter` (`tag-template: v$NEXT_PATCH_VERSION`)
- **MUST NOT** rely on any HACS comparison of the `manifest.json` version against the commit SHA when a release is absent — no such comparison exists; the sole version source is the release tag
- **SHOULD** note that custom repositories fetch their metadata live via the GitHub REST API (not from the pre-generated HACS data) — release freshness propagates immediately there, and GitHub rate limits apply directly ([faq/data_sources](https://www.hacs.xyz/docs/faq/data_sources/))

### `manifest.json` version synchronization

The version number is kept in sync via the existing mechanism normed in `release-automation`. This spec confirms it for the HACS case and makes clear that the alignment remains mandatory even though HACS reads the tag.

- **MUST** treat `custom_components/<domain>/manifest.json` → `$.version` as a version-bearing file; the value derives from the release tag under the `strip-leading-v` transform (tag `v0.1.2` → `version` `0.1.2`, unless the file itself carries the `v` convention)
- **MUST** establish the alignment via a `chore(release): <tag>` commit on `develop` before `reusable-release-publish.yml` calls `draft=false` — primary path (workflow-driven via the portfolio App token) or fallback path (maintainer PR), as defined in `release-automation`
- **MUST** refuse the publish when `$.version` at the draft's target SHA does not equal the tag; `reusable-release-publish.yml` already detects the HACS integration (source `hacs`) and verifies this before publishing
- **MUST NOT** change the `version` field in feature pull requests; the only permitted source of a version bump is the `chore(release): <tag>` path
- **SHOULD** make clear that the alignment serves correctness (avoiding the HA loader warning, hassfest, a correct self-report in the device-info dialog), not HACS version selection — HACS would display and install the tag version even on mismatch

### CI validation (HACS Action + hassfest)

Validation runs as a CI gate via the two official GitHub Actions; in this portfolio bundled in the reusable `reusable-hacs-validate.yml` (see `### Reusable workflows`).

- **MUST** run the HACS Action (`hacs/action`) with `category: integration` on `push` and `pull_request` — it uses the same code as HACS to validate a repository ([publish/action](https://www.hacs.xyz/docs/publish/action/), [hacs/action](https://github.com/hacs/action))
- **MUST** run the hassfest action (`home-assistant/actions/hassfest@master`) — the official HA tool for validating (including standalone/custom) integrations ([HA Devs hassfest](https://developers.home-assistant.io/blog/2020/04/16/hassfest/))
- **SHOULD** additionally run both actions on `release: published` so a published release is demonstrably validated
- **MAY**, for a pure custom repository, disable individual HACS Action checks via the `ignore` input (`archived`, `brands`, `description`, `hacsjson`, `images`, `information`, `issues`, `topics`, space-separated) — each ignore reduces validation coverage, however
- **MUST NOT** ignore any check for a default-store inclusion (see `### Default-store inclusion`)
- **SHOULD** pin `hacs/action` to a version or commit SHA; `home-assistant/actions/hassfest` is canonically referenced as `@master` per HA docs — a SHA pin is a hardening decision of your own

### ZIP release distribution

With `zip_release: true`, HACS downloads only the named release asset instead of cloning the repository — faster and more reliable, since only the integration files are shipped ([publish/include](https://www.hacs.xyz/docs/publish/include/): "Use zip releases instead of git clone (recommended)").

- **MUST** produce, in CD, a ZIP asset with exactly the name given in `hacs.json` as `filename` (`<domain>.zip`) and attach it to the release; if the asset is missing or misnamed, the HACS download fails
- **MAY** decouple the *build* name from `hacs.json` via the reusable's `asset-filename` input (`reusable-release-publish.yml`); when set it takes precedence, otherwise the reusable falls back to `hacs.json` `filename` and finally `<domain>.zip`. The input does **not** replace the `hacs.json` `filename`/`zip_release` keys — HACS reads `hacs.json` to choose the asset, so the build name and `hacs.json` `filename` **MUST** still agree (the reusable emits a warning on divergence)
- **MUST** attach the ZIP asset to the draft release **before** `reusable-release-publish.yml` calls `draft=false` — otherwise a race arises in which HACS sees the release without the asset and the download fails; a separate `on: release published` workflow for the asset is therefore **not permitted**
- **MUST** pack the integration files as ZIP content so HACS can extract them into `custom_components/<domain>/` (the integration directory's contents at the ZIP root level)
- **SHOULD** build the ZIP deterministically and reproducibly (no timestamp/path nondeterminism) so an identical source state produces identical assets

### Pre-releases / beta channel

- **SHOULD** model a beta/preview channel via the GitHub release **pre-release** flag; HACS does not propose a release marked as pre-release as the latest version and raises no standard update indicator ([issue #322](https://github.com/hacs/integration/issues/322), [PR #396](https://github.com/hacs/integration/pull/396))
- **MUST** accept that pre-releases are opt-in — users enable them per integration (in HACS 2.0 via a switch entity disabled by default); stable users remain unaffected
- **MUST NOT** publish a pre-release as a regular release when it is meant only for a beta audience — the pre-release flag is the correct mechanism

### `brands`

- **MAY**, for a pure custom repository, forgo `brands`; without brand assets HACS shows a fallback icon
- **SHOULD**, even in a custom repository, ship a local `brand/` directory with at least `icon.png` **or** register the domain in the [`home-assistant/brands`](https://github.com/home-assistant/brands) repository to get proper icons; the local `brand/icon.png` takes priority over the brands CDN
- **MUST**, for a default-store inclusion, satisfy the `brands` check: ship a `brand/` directory with `icon.png` **or** register the domain (matching `manifest.json` → `domain`) in the `home-assistant/brands` repository via PR ([publish/include](https://www.hacs.xyz/docs/publish/include/))

### Default-store inclusion (optional additional tier)

Inclusion in the official `hacs/default` index is optional; it raises the requirements over a custom repository.

- **MUST** pass the HACS Action **without errors and without `ignore`** and pass hassfest before submitting the inclusion PR ([publish/include](https://www.hacs.xyz/docs/publish/include/))
- **MUST** create a real GitHub release (not just a tag) after the actions succeed
- **MUST** satisfy the `brands` requirement (see `### brands`)
- **MUST** submit the inclusion PR against `hacs/default` per the rules: inserted alphabetically, the PR template filled out exactly, submitted by the repo owner or a major contributor — otherwise the PR is closed without further notice
- **SHOULD** note that default-store repositories are served from pre-generated HACS data (not live via the GitHub API) — updates propagate with a delay

### Reusable workflows (`gh-plumbing`)

The CI/CD logic lives as reusable workflows in `nolte/gh-plumbing` and is referenced by the integration via `uses:` — analogous to the existing `reusable-release-*` workflows.

- **MUST** provide HACS/hassfest validation as a reusable `reusable-hacs-validate.yml` that wraps `hacs/action` (category `integration`, optional `ignore` input) and `home-assistant/actions/hassfest@master`; the consuming integration calls it from its CI workflow on `push`/`pull_request`
- **MUST** anchor the ZIP asset build in the publish path so the asset is attached to the release before `draft=false` — either as a step in `reusable-release-publish.yml` (HACS source detected) or as a dedicated reusable executed before the publish; **not** as a downstream `on: release published` workflow
- **SHOULD** adopt the existing `app-id`/`token` pattern of the `reusable-release-*` workflows (portfolio App token with fallback to `GITHUB_TOKEN`) and pin action references
- **SHOULD** provide consuming integrations with workflow stubs as templates (CI call of `reusable-hacs-validate.yml`; a `hacs.json` template) so the process is set up reproducibly

### Relationship to other specs

- **MUST** reference `ha/integration-manifest` for the `manifest.json` field rules; this spec answers its open question "version-bump automation": the bump happens **not** in the scaffold but via the release workflow's `chore(release): <tag>` path
- **MUST NOT** redefine the rules established in `release-automation` (`claude-shared`) (Draft → Published, version-bearing files, alignment paths, permissions, cascade constraints) — reference rather than duplicate
- **SHOULD** cross-reference `ha/quality-scale` (release/owner-related rules) and `ha/dev-workflow` (local validation before the release)
- **SHOULD** stay delimited from `release-skill-layer`: release-notes curation and the local publish trigger live there, not in this spec

## Reference Templates

The following templates set up the process reproducibly in a consuming integration. Replace placeholders (`<domain>`, `<owner>`, `<repo>`, display name). Tag and version derivation, Draft → Published, the `main` refresh, and the ZIP asset build come from the `gh-plumbing` reusables and need not be rewritten per integration.

### `hacs.json` (repo root)

```json
{
  "name": "<Display Name>",
  "homeassistant": "2024.1.0",
  "zip_release": true,
  "filename": "<domain>.zip",
  "hide_default_branch": true
}
```

### `manifest.json` (release-relevant fields)

```json
{
  "domain": "<domain>",
  "name": "<Display Name>",
  "version": "0.0.0",
  "documentation": "https://github.com/<owner>/<repo>",
  "issue_tracker": "https://github.com/<owner>/<repo>/issues",
  "codeowners": ["@<owner>"]
}
```

`version` is not maintained by hand; the `chore(release): <tag>` path aligns it to the tag (see `### manifest.json version synchronization`).

### CI validation (`.github/workflows/ci.yml`)

```yaml
name: ci

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

permissions:
  contents: read

jobs:
  hacs-validate:
    uses: nolte/gh-plumbing/.github/workflows/reusable-hacs-validate.yaml@v1.1.24
    # Custom repo: disable individual checks via `ignore` (e.g. "brands").
    # Default store: NO ignore — see §Default-store inclusion.
    # with:
    #   ignore: "brands"
```

### Release workflows (standard from `gh-plumbing`)

The release workflows are identical to the portfolio-wide standard (`release-drafter.yml`, `release-publish.yml`, `release-cd-refresh-master.yml`). `reusable-release-publish.yml` detects the HACS integration via `custom_components/<domain>/manifest.json` itself and attaches the `<domain>.zip` asset before `draft=false` — no integration-specific addition required.

```yaml
# .github/workflows/release-publish.yml
on:
  workflow_dispatch:
    inputs:
      tag:
        description: "Draft tag to publish (must match an open draft)."
        required: true
        type: string
      dry_run:
        description: "Validate only (incl. ZIP build), without draft=false."
        required: false
        default: false
        type: boolean

permissions:
  contents: write

jobs:
  publish:
    uses: nolte/gh-plumbing/.github/workflows/reusable-release-publish.yml@v1.1.24
    with:
      tag: ${{ inputs.tag }}
      dry_run: ${{ inputs.dry_run }}
    secrets:
      token: ${{ secrets.GITHUB_TOKEN }}
```

## Acceptance Criteria

- [ ] The integration lives in exactly one directory `custom_components/<domain>/`; the repository contains no second integration
- [ ] `manifest.json` sets at least `domain`, `documentation`, `issue_tracker`, `codeowners`, `name`, `version`
- [ ] `hacs.json` lives in the repo root, is valid JSON, and sets `name`, `zip_release: true`, and `filename: <domain>.zip`
- [ ] Every release is a real GitHub release object with tag `v<MAJOR>.<MINOR>.<PATCH>` — no bare tag
- [ ] `manifest.json` → `$.version` equals the tag at the release's target SHA (under `strip-leading-v`); the alignment originates from a `chore(release): <tag>` commit
- [ ] `reusable-release-publish.yml` refuses the publish on a version mismatch (source `hacs` detected)
- [ ] CI runs `hacs/action` (`category: integration`) and `home-assistant/actions/hassfest@master` on `push` and `pull_request`
- [ ] A ZIP asset named exactly `<domain>.zip` is attached to the release **before** it is published
- [ ] Beta releases are marked as GitHub pre-releases and are not offered as an update to stable users
- [ ] `reusable-hacs-validate.yml` exists in `nolte/gh-plumbing` and is referenced by the integration
- [ ] For a default-store inclusion: HACS Action green without `ignore`, hassfest green, `brands` satisfied, a rule-conform `hacs/default` PR

## Open Questions

- **ZIP internal layout** (settled as an assumption, not primary-sourced): The `zip_release` asset contains the **contents** of `custom_components/<domain>/` at the ZIP root level (the established `integration_blueprint` pattern); HACS extracts the named asset into `custom_components/<domain>/`. This assumption carries the CD ZIP build in `reusable-release-publish.yml`. Before a default-store inclusion it **should** be cross-checked against HACS behavior via a real test install; `content_in_root` layouts are excluded.
- **Complete `hacs.json` schema**: The surviving sources confirm individual fields but no single canonical full-schema reference with exact defaults and the semantics of `content_in_root`, `country`, `persistent_directory`, `render_readme`. Should a canonical schema source be pulled in?
- **Versioning tooling alternative**: This spec confirms the `release-drafter`-plus-`chore(release)` path. Should `python-semantic-release` (stamping `manifest.json` via `version_variables`, since no `version_json` exists) be documented as an alternative, or does the existing path remain the only normed solution? Which tooling prevails in the HA community is not evidenced.
- **ZIP in primary vs. dedicated reusable**: Should the ZIP asset build be integrated into `reusable-release-publish.yml` (HACS source already detected) or be a dedicated reusable invoked before the publish — a trade-off between cohesion and separation of concerns.
- **`hide_default_branch` bindingness**: Should `hide_default_branch: true` move from `SHOULD` to `MUST`, given this spec requires real releases for every version state anyway?
