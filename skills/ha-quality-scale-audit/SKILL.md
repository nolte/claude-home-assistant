---
name: ha-quality-scale-audit
description: Read-only quality-scale audit of an existing HA Custom Integration against ha/quality-scale — reads the declared tier from manifest.json, parses quality_scale.yaml, checks cumulative tier satisfaction (a tier requires all rules below it), verifies key rules against code evidence via the tier-to-spec mapping, and flags exempt rules missing a comment. Produces a severity-sorted findings report contrasting declared / documented / verified tier; never modifies code. Activate on phrasings like "run a quality-scale audit", "which tier does this integration reach", "prüfe die Integration gegen die Quality-Scale". Do not activate for auto-fix, security audit (ha-security-audit), or a hassfest-grade full rule prover.
tags: [home-assistant, custom-integration, quality-scale, audit]
---

# HA Quality-Scale Audit

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-quality-scale-audit/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-quality-scale-audit/en.md).

## Why this is a skill, not an agent

- **Human-visible audit surface** — like its sibling `ha-security-audit`, this is an interactive audit the user invokes directly and reads the report from; a skill keeps it on the visible command surface rather than behind an agent's fire-and-forget contract.
- **Orchestrator that may dispatch fixes** — findings route to edit skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-translation-sync`, `ha-test-harness-augment`); the skill-orchestrates-agent-executes default keeps the orchestrator in skill form.
- **Bounded read volume** — `manifest.json`, `quality_scale.yaml`, and a handful of code files fit inline, so the context-window pressure that would bias toward an isolated agent does not apply.
- Counter-dimension considered: a read-only one-shot audit could be an agent (cf. `ha-integration-verify`), but the report is meant to be read and acted on interactively, and consistency with the `ha-security-audit` skill wins.

## When this skill activates

Use this skill to audit an existing HA Custom Integration against `ha/quality-scale` and emit a severity-sorted report that contrasts the **declared** tier (`manifest.json`), the **documented** tier (`quality_scale.yaml`), and the **verified** tier (code evidence). It is the quality-scale sibling of `ha-security-audit`.

## When NOT to activate

- auto-fixing findings → manual or via the relevant edit skill (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-translation-sync`, `ha-test-harness-augment`)
- security hardening audit → separate skill `ha-security-audit`
- a `hassfest`-grade prover that semantically validates every one of the ~45 rules → out of scope; this skill verifies the key rules with sibling specs and trusts `quality_scale.yaml` for the rest
- code-quality audit (ruff, types, coverage) → separate tools

## Hard rules

1. **Read-only.** The skill never modifies `manifest.json`, `quality_scale.yaml`, or code. `git status` must be unchanged after the run.
2. **Never overstate the verified tier.** Report a tier as "verified" only when the cumulative rule set (the tier plus every tier below) is `done`/justified-`exempt` *and* the key rules carry code evidence.
3. **Cumulative semantics.** A tier requires all of its own rules plus every rule of the tiers below it. Always evaluate the full cumulative set, never a single tier in isolation.
4. **Always reference the relevant `ha/quality-scale` rule** (and its tier) in every finding.
5. **Exempt needs a comment.** An `exempt` rule without a justifying `comment` is a high finding. When the `comment` is present and plausible, mark a matching finding "review" instead of suppressing it silently.
6. **Severity-sorted output.** High → medium → low. Never bury high findings under low ones.
7. **Verify HA internals against the official docs.** Don't reproduce HA API signatures, lifecycle hooks, conventions, or schemas from memory — when uncertain, consult the official docs before asserting it: Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant), architecture/blueprint/YAML docs [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root |
| `target_tier` | no | declared tier, else `bronze` | `bronze` / `silver` / `gold` / `platinum` |
| `severity_threshold` | no | `low` | report findings at or above this severity |

## Pre-flight

1. `git -C <target_dir> rev-parse --is-inside-work-tree`
2. `<target_dir>/custom_components/<domain>/manifest.json` exists; read `domain` and `quality_scale`
3. `<target_dir>/custom_components/<domain>/quality_scale.yaml` exists (else note its absence as the first high finding and audit on against code evidence)

## Workflow

### 1) Read declarations

Parse `manifest.json:quality_scale` (the declared tier) and `quality_scale.yaml:rules` (the per-rule status map). Resolve the target tier from `target_tier`, else the declared tier, else `bronze`.

### 2) Check

| Check | Source | Finding |
|---|---|---|
| Tier declared | `manifest.json:quality_scale` ∈ {bronze,silver,gold,platinum} | missing → high; `no_score`/`internal`/`legacy`/`custom` → high |
| YAML shape | `quality_scale.yaml:rules` per-rule status | file missing → high; `exempt` without `comment` → high |
| Cumulative | rule set of target tier + all tiers below | any rule `todo`/missing/unjustified-`exempt` → high |
| Bronze baseline | the 18 Bronze rules incl. `has-entity-name` (`grep _attr_has_entity_name = True`) and `config-flow` subcheck (`data_description`, data/options split) | unmet → medium |
| Key-rule evidence | tier-to-spec mapping (`runtime-data`→`runtime_data`, `parallel-updates`→`PARALLEL_UPDATES`, `diagnostics`→`diagnostics.py`, `discovery`→`zeroconf`, `reauthentication-flow`→`async_step_reauth`, `integration-owner`→`codeowners`, …) | `done` but no evidence → medium; evidence but `todo`/missing → low |
| Silver (tier ≥ silver) | `action-exceptions`, `config-entry-unloading`, `entity-unavailable`, `log-when-unavailable`, `test-coverage`, … | unmet when declared → high; unmet when only recommended → low |

### 3) Report

Emit Markdown findings (one per rule, even when several call sites match):

```markdown
### Finding #N — <rule>

- **Tier:** Bronze / Silver / Gold / Platinum
- **Severity:** high / medium / low
- **Path:** custom_components/<domain>/<file>:<line> (or the missing artifact)
- **Evidence:** <code snippet or quality_scale.yaml excerpt, max 5 lines>
- **Remediation:** <suggested skill or manual edit>
```

End with a summary table:

| Severity | Count |
|---|---|
| high | N |
| medium | N |
| low | N |

Plus a tier-state line contrasting declared / documented / verified, e.g.
`declared: silver / documented: silver / verified: bronze ✓ · silver ✗`.

### 4) No commit

The skill never commits. Surface the report and stop.

## Boundaries

- Auto-fix → manual or via the relevant edit skill
- Security audit → `ha-security-audit`
- Full `hassfest`-grade rule proving → out of scope; key rules verified, the rest trusted from `quality_scale.yaml`
- CI integration → not in scope today; the report is interactive
