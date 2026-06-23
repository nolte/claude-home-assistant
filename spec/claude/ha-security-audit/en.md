# Skill: `ha-security-audit`

Status: draft

## Context

`ha/security-hardening` defines the hardening bundle: API path whitelist, bearer gating, config-flow input validation, multi-instance service disambiguation, diagnostics redaction, logging discipline. An existing integration may have implemented these measures fully, partially, or not at all — without an audit you cannot decide which state applies. Human review catches individual risks but regularly forgets the cross-module view (for example bearer setting is whitelist-protected at *one* call site but not at a second).

This skill audits an integration against every MUST rule in `ha/security-hardening`, produces a structured report with findings per rule, and ships per finding a concrete code location plus remediation suggestion. It **writes nothing** — remediation stays manual or runs through a different skill.

## Scope

Read-only audit. The skill reads code files, runs `grep`-based pattern checks, parses `manifest.json`, checks `diagnostics.py:TO_REDACT` consistency with `entry.data` keys. It performs no destructive operations, no auto-fix, no commit.

## Goals

- Coverage report across every `ha/security-hardening` MUST rule per audited integration
- Per finding: file-path-line reference, classification (high / medium / low), remediation suggestion (which skill fixes it, which manual edit is needed)
- Cross-module view: findings aggregate hits across multiple modules per rule (for example bearer setting at multiple call sites)
- Quality-scale awareness: every finding carries a quality-scale tier marker showing which tier the fix unlocks

## Non-Goals

- Auto-fix of findings — destructive edits stay manual
- Backend penetration testing — the skill audits the integration; backend security is outside
- Performance audit — separate skill, if useful at all
- Code-quality audit (Ruff, type hints, test coverage) — separate tools / skills

## Requirements

### Activation triggers

- **MUST** activate on:
  - "run a security audit on the integration"
  - "audit security hardening"
  - "check the integration against ha/security-hardening"
  - "prüfe die Integration gegen das Security-Hardening"

### Inputs

- **MUST** collect: `target_dir` (repo root)
- **MAY** collect: `severity_threshold` (`low` / `medium` / `high`); default `low` (report every finding)

### Pre-flight

- **MUST** check:
  1. `target_dir` is a git repo
  2. `target_dir/custom_components/<domain>/manifest.json` exists
  3. `target_dir/custom_components/<domain>/api.py` exists (or the skill notes that no API client is present and skips the API audit)

### Audit checks

Per `ha/security-hardening` rule the skill runs the following check:

#### API path whitelist

- **MUST** look for a compiled regex constant (`_API_PATH_RE` or similar) in `api.py` and check whether every HTTP call (`session.get`, `session.post`, `session.put`, `session.patch`, `session.delete`) goes through a validation function
- **Finding when**: no path whitelist found → high; whitelist exists but at least one HTTP call bypasses it → high

#### Bearer-token gating

- **MUST** look for `Authorization` header settings in `api.py` and every other module; every setting outside a dedicated `_with_auth(...)` helper is a finding
- **Finding when**: `Authorization` set in more than one place → high; setting without prior path-whitelist check → high

#### Config-flow input validation

- **MUST** look for `vol.Schema(...)` constructs in `config_flow.py` and check whether URL fields are validated with `vol.Match` (or `cv.url`) and API-key fields with `vol.Length` / `vol.Match`
- **Finding when**: URL field without `vol.Match` → medium; API-key field without pattern / length validation → medium

#### Multi-instance service disambiguation

- **MUST** look for service handlers in `__init__.py` (or `services.py`) and check whether a `_resolve_entry` helper is called that raises `ServiceValidationError` on ambiguity
- **Finding when**: service handler without `_resolve_entry` call → medium; `_resolve_entry` helper exists but does not catch ambiguity → high

#### Diagnostics redaction

- **MUST** look for `async_redact_data` calls in `diagnostics.py` and check whether `TO_REDACT` carries every key from `entry.data` that has an auth or identifier character (heuristic: `*key`, `*token`, `*password`, `*secret`, `*auth`, `*tenant*`)
- **Finding when**: `diagnostics.py` missing → medium; `async_redact_data` missing → medium; `TO_REDACT` has gaps (for example `tenant_slug` is missing while the key appears in `entry.data`) → low (or medium, depending on key character)

#### Logging discipline

- **MUST** `grep` for `_LOGGER\.[a-z]+\(.*api_key`, `_LOGGER\.[a-z]+\(.*token`, `_LOGGER\.[a-z]+\(.*password`
- **Finding when**: hits in any of those patterns → high

### Report format

- **MUST** emit the report as a structured Markdown list with these fields per finding:
  - `id` — finding number
  - `rule` — the `ha/security-hardening` rule
  - `severity` — high / medium / low
  - `path` — file + line number
  - `evidence` — the concrete code snippet
  - `remediation` — recommended fix; reference the skill name when skill-fixable
  - `quality_scale_impact` — which quality-scale tier the fix reaches
- **MUST** end with a summary: count of findings per severity, count per rule, quality-scale state (Bronze ✓ / Silver ✓ / Gold ✗ / …)

### Forbidden

- **MUST NOT** modify code — read-only audit
- **MUST NOT** suppress false positives without justification — when a pattern matches but the code is safe for other reasons, report it and mark as "review"

## Acceptance Criteria

- [ ] The skill reads `manifest.json`, `api.py`, `config_flow.py`, `__init__.py`, `services.py` (when present), `diagnostics.py`
- [ ] The skill produces an audit entry per `ha/security-hardening` rule (also on "pass")
- [ ] Findings are sorted by severity (high → low)
- [ ] The skill makes no file modifications (`git status` is unchanged after the run)
- [ ] Skill output carries the quality-scale state summary

## Open Questions

- **Auto-fix threshold**: When does an auto-fix skill make sense? Currently every finding requires manual fixing.
- **AST-based vs. grep-based checks**: Grep is fast and adequate for these patterns; AST-based checks (via the `ast` module) would be more precise. Worth the effort?
- **CI integration**: Should the skill be consumable as a CI hook (exit code != 0 on high findings)? Currently an interactive skill only.
- **Backend audit**: What kind of backend audit (against the HTTP API itself) makes sense in parallel? Currently a non-goal.
