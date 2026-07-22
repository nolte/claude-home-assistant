# Skill: `ha-dev-workflow-apply`

Status: draft

## Context

`spec/ha/dev-workflow` bundles the HA coding workflow — code style (Ruff format, ordered imports, alphabetical constants/lists, f-strings), strict typing (`from __future__ import annotations`, full annotations, mypy, the `.strict-typing` opt-in) and validation (`hassfest`, voluptuous config validation) — into an enforceable obligation. Until now it had **no owning skill**: `ha-integration-solution`'s Platinum tier resolved to a bare `ha/dev-workflow` checklist item, and the local strict-typing obligation was implemented by nothing. This skill closes that spec-vs-skill gap: it applies the spec's MUST rules to an existing Custom Integration and reports conformance, and is the skill `ha-integration-solution` dispatches for `target_tier: platinum` instead of surfacing a checklist item.

## Scope

Applying and validating the `spec/ha/dev-workflow` MUST rules against one existing Custom Integration under `custom_components/<domain>/`, scoped by a target tier (style + `hassfest` as the bronze floor, strict typing as the platinum bridge). It is the apply/validate counterpart of the read-only `ha-quality-scale-audit`. One integration per run → mechanical fixes applied (or a dry-run diff) → one CONFORMANT / NEEDS-WORK report.

## Goals

- Apply HA code style (PEP8/PEP257, `ruff format`, ordered imports, alphabetical constants/lists, f-strings with the logging exception, header docstrings)
- Apply the strict-typing bridge for Platinum — full annotations, `from __future__ import annotations`, a local mypy-strict profile as the standalone counterpart of Core's `.strict-typing`, and a clean mypy run
- Run the available `hassfest` variant and shape the integration until it passes (manifest, strings, services)
- Apply voluptuous config validation for YAML-configurable platforms (`const.py` constants, `required` before `optional`, valid defaults)
- Emit a CONFORMANT / NEEDS-WORK report keyed to the `spec/ha/dev-workflow` acceptance criteria
- Be dispatchable by `ha-integration-solution` for the Platinum tier

## Non-Goals

- The read-only quality-scale tier assessment — `ha-quality-scale-audit`
- Security hardening — `ha-security-audit`
- The pytest harness (fixtures, `MockConfigEntry`, snapshot tests, coverage) — `ha-test-harness-augment` / `ha/test-harness`
- Devcontainer / Kind / `script/setup` / venv setup — `ha/dev-environment`
- Async / event-loop patterns — `ha/async-patterns`
- Manifest-schema authoring in detail — `ha/integration-manifest`; this skill only requires that `hassfest` validates it
- Deploying / verifying against a running HA instance — the `ha-integration-deploy` / `ha-integration-verify` agents

## Requirements

### Activation triggers

- **MUST** activate on requests to apply or enforce the HA dev workflow on an existing integration:
  - "apply the HA dev workflow", "enforce HA code style"
  - "make this integration strict-typing / platinum-ready"
  - "run ruff + mypy strict + hassfest on my integration"
  - "wende den HA-Dev-Workflow an", "mach die Integration platinum-tauglich"
- **SHOULD** not activate for a read-only tier check (`ha-quality-scale-audit`), a security audit (`ha-security-audit`), or test authoring (`ha-test-harness-augment`)

### Inputs

- **MUST** capture: `target_dir` (repo root containing `custom_components/<domain>/`)
- **MAY** capture: `target_tier` (default `bronze`; `platinum` enables the strict-typing pass) and `apply` (default `true`; `false` = dry-run report only)

### Pre-flight

- **MUST** confirm `target_dir` is a git work tree and `custom_components/<domain>/manifest.json` exists (read `domain`)
- **MUST** detect available tooling (`ruff`, `mypy`, a `hassfest` path) and record any missing tool for the report rather than failing silently

### Apply rules

- **MUST** apply the bronze-floor style rules always: `ruff format`, Ruff import ordering, alphabetical constants/lists, f-strings (logging keeps percentage formatting), header docstrings
- **MUST** apply the strict-typing pass only when `target_tier` is `platinum` (or explicitly requested): `from __future__ import annotations`, full annotations, a `[tool.mypy]` strict profile in `pyproject.toml` scoped to `custom_components.<domain>` (the standalone `.strict-typing` counterpart), and a mypy run whose residual errors become NEEDS-WORK items
- **MUST** keep `assert`-based type narrowing exclusively inside `if TYPE_CHECKING:` blocks
- **MUST** run the available `hassfest` variant (the `home-assistant/actions` hassfest action, a vendored `hassfest`, or the pre-commit hook) and shape the integration until it passes; when no variant is available, record it as a NEEDS-WORK gap instead of skipping silently
- **MUST** apply voluptuous config validation for YAML-configurable platforms using `const.py` constants, `required` before `optional`, and valid non-`None` defaults for `cv.string`
- **MUST NOT** log secrets, and **MUST NOT** fold in setup mechanics, the pytest harness, or async patterns — reference the sibling spec by slug and stop
- **MUST** verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Report format

- **MUST** end with a CONFORMANT / NEEDS-WORK report as a table keyed to the `spec/ha/dev-workflow` acceptance criteria, plus a one-line verdict
- **MUST** name the concrete remaining action for each NEEDS-WORK item (file:line or the missing artifact/tool)

### Prohibitions

- **MUST NOT** process more than one integration per run
- **MUST NOT** apply the strict-typing pass below the Platinum tier unless explicitly requested
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Applies the bronze-floor style rules (ruff format, ordered imports, sorted constants/lists, f-strings with the logging exception, header docstrings)
- [ ] For Platinum, applies the strict-typing bridge (annotations, `from __future__ import annotations`, local mypy-strict profile, mypy run) and moves `assert` narrowing into `if TYPE_CHECKING:`
- [ ] Runs the available `hassfest` variant and records a missing variant as a NEEDS-WORK gap
- [ ] Applies voluptuous config validation for YAML-configurable platforms
- [ ] Emits a CONFORMANT / NEEDS-WORK report keyed to the `spec/ha/dev-workflow` acceptance criteria with a concrete action per NEEDS-WORK item
- [ ] `ha-integration-solution` dispatches this skill for `target_tier: platinum` instead of surfacing a checklist item

## Open questions

- **`.strict-typing` counterpart**: the Core `.strict-typing` file is unavailable outside Core, so this skill uses a `pyproject.toml` `[tool.mypy]` strict profile scoped to the integration package. Should that snippet be pinned normatively in `spec/ha/dev-workflow` (its open question) and only consumed here?
- **`hassfest` variant preference**: action vs. vendored vs. pre-commit — the portfolio-wide preferred variant is still open in `spec/ha/dev-workflow`; this skill runs whichever is present and reports a gap otherwise.
- **`apply: false` scope**: should the dry-run mode still run mypy/hassfest (read-only) to populate the report, or only compute the style diffs? Currently it runs the read-only checks and lists the style diffs without writing.
