# Branching Model

Status: draft

## Context
Repositories in this portfolio use `main` as a presentation-only branch that always reflects the most recently published GitHub Release. Active development happens on `develop`; feature branches target `develop` via pull request. When a GitHub Release is published, reusable workflows from [`nolte/gh-plumbing`](https://github.com/nolte/gh-plumbing) fast-forward `main` to the released tag, so `main` remains a mechanically-maintained, read-only view of the last shipped artifact. Humans and AI agents that look at `main` see exactly what was released—never a work-in-progress state.

## Goals
- `main` always equals the last published GitHub Release, nothing else
- No manual commits, pushes, or merges land on `main`: every change flows through `develop` and a release
- The promotion from `develop` to `main` is automated, auditable, and triggered only by a published release
- Branch roles are unambiguous for humans and AI agents reading the repository

## Non-Goals
- Tag naming scheme (handled by release-drafter configuration; the portfolio convention is the `v`-prefixed SemVer tag, for example `v1.2.3`, set centrally in `nolte/gh-plumbing:.github/commons-release-drafter.yml`)
- Changelog generation (handled by release-drafter)
- Publication to external registries (HACS, PyPI, container registries)
- Project-level Taskfile / CI target contents (covered by the project-structure spec)

## Requirements

### Branch roles
- **MUST** designate `develop` as the integration branch where all feature work lands via pull request
- **MUST** designate `main` as a release-presentation branch reflecting the most recently published GitHub Release
- **MUST NOT** allow manual commits, pushes, or merges directly to `main`; the branch is written to only by the release automation
- **MUST** use feature branches named with one of the prefixes `feat/`, `fix/`, `chore/`, `docs/`, or `exp/` and target `develop` in their pull request; these prefixes are identical to the Conventional Commits types used in PR titles so that the branch name and the commit type align without translation
- **SHOULD** reserve the `exp/` prefix for experimental or iteration-scoped work that bundles loosely related exploration; an `exp/` branch has an explicitly bounded lifetime and its merge is treated as a throwaway integration rather than as a stable feature, fix, chore, or documentation change
- **SHOULD** name `exp/` branches with either a calendar-week marker (`exp/YYYY-WW-<theme>`, for example `exp/2026-W17-skill-agent-split`) or a monotonic counter (`exp/NNN-<theme>`, for example `exp/003-skill-agent-split`) so iterations sort chronologically; the theme portion follows the same kebab-case rule as every other branch prefix
- **SHOULD** exclude `exp` PR titles from user-facing release notes—either by mapping them to a hidden category in `.github/release-drafter.yml` (directly or via the `nolte/gh-plumbing:.github/commons-release-drafter.yml` extension) or by leaving the `exp` type out of the configured categories entirely; experimental work isn't a shipped feature and must not appear as one

### Branch protection
- **MUST** declare all branch-protection rules as code in `.github/settings.yml` (directly or via `_extends: nolte/gh-plumbing:.github/commons-settings.yml`) and synchronize them through the [Probot Settings app](https://probot.github.io/apps/settings/); protection rules **MUST NOT** be configured ad-hoc in the GitHub UI
- **MUST** protect `main` so that direct pushes from humans are blocked and only the release workflow (via `GITHUB_TOKEN`) can update it
- **SHOULD** protect `develop` so that pull requests require passing CI before merge
- **SHOULD** require linear history on `main` so the fast-forward from release tags stays clean

### Release flow
- **MUST** cut GitHub Releases from tags created on the `develop` branch—release-drafter maintains the draft as PRs land
- **MUST** flip the draft to a published GitHub Release through `release-publish.yml` as the primary Draft → Published path, gated by the pre-publish verification of the release-automation workflow; running `gh release edit <tag> --draft=false` directly is a documented fallback for incident response only, when `release-publish.yml` is itself broken
- **MAY** be dispatched by sprint-side closure: the sibling specs `release-artifact` §Dispatch boundary to release machinery and `release-skill-layer` define an optional, operator-opt-in chain in which `sprint-review` invokes `release-notes-curate` (for body curation) and `release-publish-trigger` (which dispatches the workflow declared above). The dispatch boundary is one-way—this spec governs the workflow itself, the sprint-side specs govern the trigger conditions—and the consuming specs **MUST NOT** redefine any rule declared here
- **MUST** update `main` exclusively through the release workflow on `release: [published]`
- **MUST** derive `main` content mechanically from the release; editing files directly on `main` is a bug
- **SHOULD** keep the default pull-request base set to `develop`, not `main`

### `Hotfix` flow
- **MUST** handle an emergency hotfix as a standard `fix/` pull request against `develop`, followed by a new patch release that fast-forwards `main` through `release-cd-refresh-master.yml` like any other release
- **MUST NOT** branch off `main` or merge a hotfix back into `main`; the "no manual writes to `main`" rule in §Branch roles and §Release flow admits no hotfix carve-out
- **MUST** record the resulting release as an out-of-band artefact under `project/release-artifacts/out-of-band/<NNNN>-<slug>.md` following the out-of-band convention; mid-sprint hot-fixes are tracked the same way, and the release-automation defers the hotfix flow to this subsection

### Required GitHub workflows
The repository **MUST** include the following workflows under `.github/workflows/`, each wired to the corresponding reusable workflow from `nolte/gh-plumbing`:

- **`release-drafter.yml`**: triggers on `push: [develop]`; uses `nolte/gh-plumbing/.github/workflows/reusable-release-drafter.yml` to maintain the draft GitHub Release that collects the next version's changes
- **`release-publish.yml`**: triggers on `workflow_dispatch` only; uses `nolte/gh-plumbing/.github/workflows/reusable-release-publish.yml` to flip the open draft to `draft: false` once the pre-publish gates of the release-automation workflow have all passed; requires `contents: write` permission
- **`release-cd-refresh-master.yml`**: triggers on `release: [published]`; uses `nolte/gh-plumbing/.github/workflows/reusable-release-cd-refresh-master.yml` with `target_branch: main` to fast-forward `main` to the released commit; requires `contents: write` permission
- **`automerge.yaml`**: triggers on pull-request / review / check-suite events; uses `nolte/gh-plumbing/.github/workflows/reusable-automerge.yaml` so approved, green pull requests against `develop` merge automatically

`target_branch` is `main` for every repository, including HACS integrations; the `master` token in the reusable-workflow filename `reusable-release-cd-refresh-master.yml` is a `nolte/gh-plumbing` naming legacy and doesn't imply a `master` branch.

The repository **SHOULD** also include, where applicable:

- **`release-cd-deliver-docs.yml`**: on `release: [published]`; publishes MkDocs output via `nolte/gh-plumbing/.github/workflows/reusable-mkdocs.yaml`
- Any additional `release: [published]` packaging workflow (for example `release.yml` producing an HACS ZIP) specific to the repository's delivery artifact

### Workflow integrity
- **MUST** keep the four required workflows (`release-drafter.yml`, `release-publish.yml`, `release-cd-refresh-master.yml`, `automerge.yaml`) in every repository that follows this branching model
- **SHOULD** pin the `nolte/gh-plumbing` reusable-workflow reference to a tag (for example `@v1.1.12`) rather than a moving branch, so the refresh behavior of `main` is reproducible
- The bump cadence for the pinned tag is governed by the workflow-health discipline (§Upstream drift) (candidate bump applied through a single gated PR, with Renovate automerge forbidden for `nolte/gh-plumbing` tag bumps); each repository pins the latest validated tag, and no single fixed version is mandated portfolio-wide

## Acceptance Criteria
- [ ] `develop` exists and is the default pull-request base
- [ ] `main` exists and is branch-protected so that humans can't push directly
- [ ] Branch-protection rules for `main` and `develop` are declared in `.github/settings.yml` (directly or via the `nolte/gh-plumbing` commons extension), not only through the GitHub UI
- [ ] `.github/workflows/release-drafter.yml` is present and triggers on `push: [develop]`
- [ ] `.github/workflows/release-publish.yml` is present, declares only `workflow_dispatch` as its trigger, requests `contents: write`, and invokes `nolte/gh-plumbing/.github/workflows/reusable-release-publish.yml`
- [ ] `.github/workflows/release-cd-refresh-master.yml` is present, triggers on `release: [published]`, and sets `target_branch: main`
- [ ] `.github/workflows/automerge.yaml` is present and invokes the `nolte/gh-plumbing` reusable automerge workflow
- [ ] The HEAD of `main` corresponds to a published GitHub Release tag (`git tag --points-at main` returns a release tag)
- [ ] There are no human-authored commits on `main` between two consecutive releases—only commits introduced by the refresh workflow
- [ ] Feature branches in the repository use one of the prefixes `feat/`, `fix/`, `chore/`, `docs/`, `exp/`
- [ ] If `.github/release-drafter.yml` is present, the `exp` type either lands in a non-user-facing category or is excluded from the configured categories, so experimental PRs don't surface as shipped features
- [ ] If MkDocs is used **and** `.github/workflows/release-cd-deliver-docs.yml` is shipped, the workflow triggers on `release: [published]` (the workflow itself is SHOULD, per Requirements §Required GitHub workflows; this AC checks its trigger when present, not its presence)

## Open Questions
_None at this time._
