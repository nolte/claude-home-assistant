---
name: ha-dev-workflow-apply
description: Apply and validate the HA code-style / strict-typing / validation workflow (spec/ha/dev-workflow) against an existing HA Custom Integration — Ruff format, ordered imports and alphabetical constants/lists, f-strings (logging excepted), file-header docstrings, full type annotations with `from __future__ import annotations`, a local mypy-strict profile as the standalone counterpart of Core's `.strict-typing` (the platinum strict-typing bridge), hassfest validation (manifest/strings/services), and voluptuous config validation for YAML-configurable platforms — then report CONFORMANT / NEEDS-WORK against the spec's MUST rules keyed to a target tier (bronze floor → platinum). Activate on "apply the HA dev workflow", "make this integration strict-typing / platinum-ready", "run ruff + mypy strict + hassfest on my integration", "enforce HA code style", "wende den HA-Dev-Workflow an", "mach die Integration platinum-tauglich". Do not activate for a read-only quality-scale tier check (ha-quality-scale-audit), a security audit (ha-security-audit), the pytest harness (ha-test-harness-augment), devcontainer / Kind setup (ha/dev-environment), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, code-style, strict-typing, validation]
phase: quality
summary: "Applies and validates the HA code-style, strict-typing, and validation workflow (ruff, mypy-strict, hassfest, voluptuous) on a Custom Integration, reporting CONFORMANT/NEEDS-WORK per target tier."
summary_de: "Wendet den HA-Code-Style-, Strict-Typing- und Validierungs-Workflow (ruff, mypy-strict, hassfest, voluptuous) auf eine Custom-Integration an und meldet CONFORMANT/NEEDS-WORK je Ziel-Tier."
use_when:
  - "you want to apply the HA dev workflow to an integration"
  - "you want to make an integration strict-typing / platinum-ready"
  - "you want to run ruff + mypy strict + hassfest on an integration"
  - "you want to enforce HA code style on an integration"
dont_use_when:
  - situation: "You want a read-only quality-scale tier check, not to apply fixes"
    alternative: ha-quality-scale-audit
  - situation: "You want a security-hardening audit"
    alternative: ha-security-audit
  - situation: "You want the pytest test harness"
    alternative: ha-test-harness-augment
  - situation: "You want to deploy or verify against a live HA instance"
    alternative: ha-integration-deploy
see_also:
  - ha-quality-scale-audit
  - ha-security-audit
  - ha-test-harness-augment
  - ha-translation-sync
  - ha-integration-solution
  - ha-integration-deploy
  - ha-integration-verify
---

# HA Dev-Workflow Apply

Spec: [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-dev-workflow-apply/en.md) (EN canonical) / [`de.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-dev-workflow-apply/de.md). Grounding spec: [`ha/dev-workflow`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/dev-workflow/en.md) — this skill operationalises that spec's MUST rules; read it for the pinned HA-original rules.

This skill is the owning skill of `spec/ha/dev-workflow`: it **applies** the HA coding workflow (style, strict typing, validation) to an existing Custom Integration and **validates** the result, closing the spec-vs-skill gap where the Platinum tier of `ha-integration-solution` previously resolved to a bare checklist item.

## Why this is a skill, not an agent

- **Human-visible apply surface** — like the sibling `ha-translation-sync`, the user invokes it directly, watches the format/typing/validation edits land, and reads the CONFORMANT / NEEDS-WORK report; a skill keeps that on the visible command surface.
- **Bounded, tool-driven work** — it runs `ruff`, `mypy`, and `hassfest` over one integration and applies mechanical fixes; the read/edit volume fits inline, so the pressure that biases toward an isolated agent does not apply.
- **Dispatched by an orchestrator** — `ha-integration-solution` dispatches it for `target_tier: platinum`; the skill-orchestrates-skill default keeps it in skill form.
- Counter-dimension considered: the strict-typing pass could run as a fire-and-forget agent, but the annotation edits and the mypy-strict decisions should stay visible and reviewable in the user context; skill wins.

## When this skill activates

Use this skill to bring an existing Custom Integration under `custom_components/<domain>/` up to the `spec/ha/dev-workflow` obligations — code style, full typing, hassfest, config validation — for a chosen `target_tier` (bronze floor through platinum). It is the tooling counterpart of the read-only `ha-quality-scale-audit`: that one *checks* the tier, this one *applies* the code-workflow rules that a tier requires.

## When NOT to activate

- a read-only quality-scale tier assessment → `ha-quality-scale-audit`
- a security hardening audit → `ha-security-audit`
- the pytest harness (fixtures, `MockConfigEntry`, snapshot tests, coverage) → `ha-test-harness-augment` / `ha/test-harness`
- devcontainer / Kind / `script/setup` / venv bootstrap → `ha/dev-environment`
- async / event-loop patterns → `ha/async-patterns`
- deploying / verifying against a running HA instance → the `ha-integration-deploy` / `ha-integration-verify` agents

## Hard rules

1. **Own `spec/ha/dev-workflow`, nothing more.** Apply exactly its style/typing/validation MUST rules; never fold in setup mechanics, the pytest harness, or async patterns — reference the sibling spec by slug and stop.
2. **Tier-scoped.** The style rules and `hassfest` are the **bronze floor** (always applied); the strict-typing bridge (full annotations, `from __future__ import annotations`, mypy strict, `.strict-typing`/local-mypy-strict inclusion) is the **platinum** `strict-typing` rule. Apply the strict-typing pass only when `target_tier` is `platinum` (or explicitly requested).
3. **Standalone-integration reality.** A Custom Integration lives outside HA Core, so Core's root `.strict-typing` file and `python3 -m script.hassfest` are not directly available. Use the local equivalents: a `[tool.mypy]` strict profile in `pyproject.toml` (scoped to the integration package) as the `.strict-typing` counterpart, and hassfest via the `home-assistant/actions` hassfest action / a vendored `hassfest` / the pre-commit hook. If neither hassfest variant is available, run what is present, and record the gap as a NEEDS-WORK item rather than silently skipping it.
4. **Format is non-negotiable.** Run `ruff format` and Ruff import-ordering; HA never merges submissions that diverge. Sort constants and the contents of lists/dicts alphabetically.
5. **Logging is the f-string exception.** Convert `%`/`str.format` to f-strings everywhere except logging calls, which keep percentage formatting (`_LOGGER.info("... %s ...", value)`) so the message renders only when needed. Never log secrets.
6. **Type narrowing discipline.** `assert`-based type narrowing appears **only** inside `if TYPE_CHECKING:` blocks.
7. **Validate, don't just format.** Shape the integration so hassfest passes (manifest, strings, services); for YAML-configurable platforms, validate input via voluptuous using `const.py` constants, `required` before `optional`, and valid non-`None` defaults for `cv.string`.
8. **Report against the spec's acceptance criteria.** End every run with a CONFORMANT / NEEDS-WORK report keyed to the `spec/ha/dev-workflow` acceptance-criteria list; a NEEDS-WORK item names the concrete remaining action.
9. **Verify HA internals against the official docs.** Don't reproduce HA conventions from memory — consult the developer docs when uncertain (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root containing `custom_components/<domain>/` |
| `target_tier` | no | `bronze` | `bronze`/`silver`/`gold`/`platinum`; `platinum` enables the strict-typing pass |
| `apply` | no | `true` | `true` applies the mechanical fixes; `false` reports only (dry-run) |

## Pre-flight

1. `git -C <target_dir> rev-parse --is-inside-work-tree` — a clean-enough tree so applied edits are reviewable
2. `<target_dir>/custom_components/<domain>/manifest.json` exists; read `domain`
3. Detect available tooling: `ruff`, `mypy`, and a hassfest path (action / vendored / pre-commit); note any missing tool for the report

## Workflow

### 1) Code style (bronze floor)

Run `ruff format` and Ruff import-sorting over the integration package. Convert non-logging `%`/`.format` strings to f-strings. Ensure every file carries a header docstring. Sort constants and list/dict contents alphabetically. Apply when `apply: true`; otherwise list the diffs.

### 2) Strict typing (platinum bridge — only when `target_tier: platinum`)

Add `from __future__ import annotations` at each module top. Fill in missing annotations. Add/point at a `[tool.mypy]` strict profile in `pyproject.toml` scoped to `custom_components.<domain>` (the standalone counterpart of Core's `.strict-typing`), and run `mypy` against the package. Move any `assert` type-narrowing into `if TYPE_CHECKING:`. Report every residual mypy error as NEEDS-WORK.

### 3) Validation (hassfest + config)

Run the available hassfest variant; shape the integration until it passes (manifest, strings, services). For YAML-configurable platforms, generate/verify the voluptuous schema (`const.py` constants, `required` before `optional`, valid defaults). Record a missing hassfest path as a NEEDS-WORK gap.

### 4) Report

Emit a CONFORMANT / NEEDS-WORK report keyed to the `spec/ha/dev-workflow` acceptance criteria:

```markdown
## Dev-workflow report — <domain> (target_tier: <tier>)

| Acceptance criterion | Status | Note |
|---|---|---|
| PEP8/PEP257 + ruff format | CONFORMANT | applied |
| Imports ordered; constants/lists sorted | CONFORMANT | applied |
| f-strings (logging excepted) | NEEDS-WORK | 2 `.format` calls in sensor.py:41,88 |
| Fully typed + local mypy-strict profile | … | … |
| `from __future__ import annotations` + mypy passes | … | … |
| hassfest passes (manifest/strings/services) | … | … |
| voluptuous config validation | … | … |

**Verdict:** CONFORMANT / NEEDS-WORK — <one-line summary>
```

## Boundaries

- Read-only tier check → `ha-quality-scale-audit`
- Security audit → `ha-security-audit`
- Pytest harness → `ha-test-harness-augment` / `ha/test-harness`
- Setup mechanics (devcontainer, Kind, `kill 1`, `kubectl cp`) → `ha/dev-environment`
- Async / event-loop patterns → `ha/async-patterns`
- Deploy / verify on a live HA instance → the `ha-integration-deploy` / `ha-integration-verify` agents
