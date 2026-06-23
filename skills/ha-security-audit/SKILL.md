---
name: ha-security-audit
description: Read-only security audit of an existing HA Custom Integration against every MUST rule in spec/ha/security-hardening — API path whitelist, bearer gating, config-flow input validation, multi-instance service disambiguation, diagnostics redaction, logging discipline. Produces a severity-sorted findings report; never modifies code. Activate on phrasings like "run a security audit on the integration", "audit security hardening", "prüfe die Integration gegen das Security-Hardening". Do not activate for auto-fix, backend penetration testing, or general code-quality audit.
tags: [home-assistant, custom-integration, security, audit]
---

# HA Security Audit

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-security-audit/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-security-audit/en.md).

## When this skill activates

Use this skill to audit an existing HA Custom Integration against every MUST rule in `ha/security-hardening` and emit a severity-sorted findings report.

## When NOT to activate

- auto-fixing findings → manual or via separate skill
- backend penetration testing → out of scope
- code-quality audit (ruff, types, coverage) → separate tools

## Hard rules

1. **Read-only.** The skill never modifies code. `git status` must be unchanged after the run.
2. **Severity-sorted output.** High → medium → low. Never bury high findings under low ones.
3. **Always cross-module.** Aggregate hits per rule; do not split findings about the same rule across multiple report entries.
4. **Always reference the relevant `ha/security-hardening` requirement** in every finding.
5. **Never suppress false positives silently.** When a pattern matches but the code is safe for other reasons, mark the finding as "review" and explain why.

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root |
| `severity_threshold` | no | `low` | report findings at or above this severity |

## Pre-flight

1. `git -C <target_dir> rev-parse --is-inside-work-tree`
2. `<target_dir>/custom_components/<domain>/manifest.json` exists; read `domain`
3. `api.py` is present (or the skill notes that no API client is present and skips the API audit)

## Workflow

### 1) Scan

Run `grep`-based pattern checks for each rule:

| Rule | Pattern / source |
|---|---|
| API path whitelist | `_API_PATH_RE` or similar in `api.py`; `session.{get,post,put,patch,delete}` calls |
| Bearer-token gating | `Authorization` header occurrences across modules |
| Config-flow input validation | `vol.Schema` constructs in `config_flow.py` |
| Multi-instance service disambiguation | service handlers vs. `_resolve_entry` helper |
| Diagnostics redaction | `async_redact_data` + `TO_REDACT` consistency with `entry.data` keys |
| Logging discipline | `_LOGGER.{level}(...api_key\|token\|password\|secret...)` |

### 2) Score

Classify every match as high / medium / low per the rules in the spec. Aggregate per-rule totals.

### 3) Report

Emit Markdown findings (one per logical issue, even when multiple call sites match):

```markdown
### Finding #N — <rule>

- **Severity:** high / medium / low
- **Path:** custom_components/<domain>/<file>:<line> (multi-site lists allowed)
- **Evidence:** <code snippet, max 5 lines>
- **Remediation:** <suggested skill or manual edit>
- **Quality-scale impact:** Bronze / Silver / Gold (or "tier unchanged")
```

End with a summary table:

| Severity | Count |
|---|---|
| high | N |
| medium | N |
| low | N |

Plus a Quality-Scale state line: Bronze ✓ / Silver ✓ / Gold ✗ / Platinum ✗.

### 4) No commit

The skill never commits. Surface the report and stop.

## Boundaries

- Auto-fix → manual or via the relevant edit skill
- Backend audit → out of scope
- General code-quality audit → ruff / pytest / mypy
- CI integration → not in scope today; the report is interactive
