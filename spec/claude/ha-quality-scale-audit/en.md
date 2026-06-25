# Skill: `ha-quality-scale-audit`

Status: draft

## Context

`ha/quality-scale` defines HA's tier framework (🥉 Bronze / 🥈 Silver / 🥇 Gold / 🏆 Platinum) plus the two-step declaration: a `quality_scale:` key in `manifest.json` names the achieved tier, while a companion `quality_scale.yaml` carries the per-rule status (`done` / `exempt` with `comment` / `todo`). An existing integration may declare a tier in `manifest.json` that neither the `quality_scale.yaml` nor the actual code supports — the cumulative semantics (a tier requires *all* of its own rules plus all rules below) are easily overstated, and individual `done` rules drift away from the code after refactors.

This skill audits an integration against `ha/quality-scale`: it reads the declared tier, parses `quality_scale.yaml`, checks cumulative satisfaction of the declared tier, verifies the key rules against code evidence (via the tier-to-spec mapping), and reports one finding per rule. It **writes nothing** — remediation stays manual or runs through a different skill (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-translation-sync`, `ha-test-harness-augment`).

## Scope

Read-only audit. The skill reads `manifest.json`, `quality_scale.yaml`, and the integration's code files, runs `grep`-based pattern checks, and compares declared rule status against code evidence. It performs no destructive operations, no auto-fix, no commit. It is the quality-scale sibling of `ha-security-audit`.

## Goals

- Coverage report across the declared tier plus every tier below it per audited integration
- Surface the difference between the **declared** tier (`manifest.json`), the **documented** tier (`quality_scale.yaml` status), and the **verified** tier (code evidence)
- Per finding: rule, file-path-line reference, classification (high / medium / low), remediation suggestion (which skill fixes it, which manual edit is needed)
- Tier-to-spec traceability: trace every key rule with a sibling spec back to the mapped spec and its code evidence
- `exempt` discipline: every exempted rule needs a `comment`; an `exempt` without justification is a finding

## Non-Goals

- Auto-fix of findings — remediation runs through the edit skills or manually
- Maintaining the HA checklist PR for a tier upgrade against the HA core repo — that is a contribution workflow, not a plugin artifact
- A full `hassfest` replacement that semantically proves each of the ~45 rules against the code — the skill verifies the key rules with sibling specs heuristically; deeper rules are checked against the `quality_scale.yaml` declaration
- Security audit (`ha/security-hardening`) — separate skill `ha-security-audit`
- Code-quality audit (Ruff, type hints, test coverage) — separate tools / skills (`strict-typing` is checked only as a Platinum rule status, not via real type checking)

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "run a quality-scale audit on the integration"
  - "audit the integration against the quality scale"
  - "which quality-scale tier does this integration reach"
  - "prüfe die Integration gegen die Quality-Scale"
  - "welches Quality-Scale-Tier erreicht die Integration"

### Inputs

- **MUST** capture: `target_dir` (repo root)
- **MAY** capture: `target_tier` (`bronze` / `silver` / `gold` / `platinum`); when absent, the tier declared in `manifest.json` is assumed as target, falling back to `bronze`
- **MAY** capture: `severity_threshold` (`low` / `medium` / `high`); default `low` (report every finding)

### Pre-flight

- **MUST** check:
  1. `target_dir` is a git repo
  2. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain` from it
  3. `target_dir/custom_components/<domain>/quality_scale.yaml` exists (or the skill notes its absence as the first high finding and audits on against code evidence)

### Audit checks

#### Tier declaration (`manifest.json`)

- **MUST** read the `quality_scale:` key from `manifest.json` and validate it against `{bronze, silver, gold, platinum}`
- **Finding when**: `quality_scale` missing → high (a new integration MUST declare at least Bronze); value is `no_score` / `internal` / `legacy` / `custom` for a custom integration on the tiered scale → high

#### `quality_scale.yaml` shape

- **MUST** check the file exists and, under `rules:`, carries a status per rule (`done`, or `status: exempt` with `comment`, or `todo`)
- **MUST** check every `exempt` rule for a non-empty `comment`
- **Finding when**: `quality_scale.yaml` missing → high; an `exempt` rule without `comment` → high; a rule expected in the tier rule set missing entirely from the file → medium

#### Cumulative tier satisfaction

- **MUST** for the target tier (`target_tier` or the declared tier) build the rule set of that tier **and all tiers below it** and check every rule is `done` or justifiably `exempt`
- **Finding when**: a rule of the target tier (or a lower one) is `todo` / missing / unjustified `exempt` → high (the declared tier is overstated)

#### Bronze baseline

- **MUST** independently of the declared tier check that every Bronze mandatory rule from `ha/quality-scale` is `done` or justifiably `exempt` (`action-setup`, `appropriate-polling`, `brands`, `common-modules`, `config-flow-test-coverage`, `config-flow`, `dependency-transparency`, `docs-*`, `entity-event-setup`, `entity-unique-id`, `has-entity-name`, `runtime-data`, `test-before-configure`, `test-before-setup`, `unique-config-entry`)
- **MUST** verify the `has-entity-name` subcheck via `grep` for `_attr_has_entity_name = True` (or `has_entity_name` on the EntityDescription) in the platform modules
- **MUST** check the `config-flow` subcheck: `data_description` present in `strings.json`/`translations` and `ConfigEntry.data` vs. `ConfigEntry.options` cleanly separated
- **Finding when**: a Bronze rule unmet → medium (or high if Bronze is the declared tier — the cumulative check already covers that)

#### Key-rule traceability (code evidence)

- **MUST** check every key rule with a sibling spec declared `done` against code evidence:

  | Rule | Spec | Evidence check |
  |---|---|---|
  | `runtime-data` | `ha/runtime-data-pattern` | `entry.runtime_data` used, **no** `hass.data[DOMAIN]` |
  | `config-flow`, `test-before-configure`, `test-before-setup`, `unique-config-entry` | `ha/config-flow-patterns` | `config_flow.py` present; `_abort_if_unique_id_configured`; setup tests |
  | `parallel-updates` | `ha/entity-architecture`, `ha/coordinator-patterns` | `PARALLEL_UPDATES` constant per platform module |
  | `entity-translations`, `exception-translations` | `ha/translations` | entries in `strings.json` |
  | `diagnostics` | `ha/diagnostics` | `diagnostics.py` with `async_get_config_entry_diagnostics` |
  | `discovery`, `discovery-update-info` | `ha/zeroconf-discovery` | `zeroconf` in `manifest.json` + `async_step_zeroconf` |
  | `reauthentication-flow` | `ha/coordinator-patterns` | `async_step_reauth` in `config_flow.py` |
  | `integration-owner` | `ha/integration-manifest` | non-empty `codeowners` in `manifest.json` |

- **Finding when**: a rule is `done` in `quality_scale.yaml` but the code evidence is missing → medium (declaration drift); conversely evidence present but the rule `todo`/missing → low (under-recorded)

#### Silver rules (when target tier ≥ Silver)

- **MUST** additionally check the Silver rules: `action-exceptions` (`ServiceValidationError` / `HomeAssistantError` in service handlers), `config-entry-unloading` (`async_unload_entry`), `entity-unavailable`, `log-when-unavailable`, `parallel-updates`, `reauthentication-flow`, `integration-owner`, `test-coverage`, `docs-configuration-parameters`, `docs-installation-parameters`
- **Finding when**: a Silver rule unmet when Silver is declared → high; unmet when Silver is only recommended (connection-based) → low

### Report format

- **MUST** emit the report as a Markdown list sorted by severity (high → medium → low) with per finding:
  - `id` — finding number
  - `rule` — the `ha/quality-scale` rule (or the declaration artifact)
  - `tier` — the tier the rule belongs to (Bronze / Silver / Gold / Platinum)
  - `severity` — high / medium / low
  - `path` — file + line number (or the missing artifact)
  - `evidence` — code snippet or `quality_scale.yaml` excerpt (max 5 lines)
  - `remediation` — suggested fix; for skill-fixable findings reference the skill name
- **MUST** end with a summary: finding count per severity, plus a **tier-state line** contrasting the declared, documented, and verified tier (e.g. `declared: silver / documented: silver / verified: bronze ✓ · silver ✗`)

### Prohibitions

- **MUST NOT** modify code, `manifest.json`, or `quality_scale.yaml` — read-only audit
- **MUST NOT** report a higher tier as "verified" than the code evidence and cumulative rule satisfaction support
- **MUST NOT** silently suppress false positives — when a rule is `exempt` and the `comment` is plausible, mark the finding as "review" instead of hiding it

## Acceptance criteria

- [ ] Skill reads `manifest.json` and `quality_scale.yaml` and the referenced code files
- [ ] Skill reports a missing `quality_scale` key or a missing `quality_scale.yaml` as a high finding
- [ ] Skill checks the target tier cumulatively (every rule below it)
- [ ] Skill verifies every key rule with a sibling spec against code evidence and reports declaration drift
- [ ] Every `exempt` rule without a `comment` is a high finding
- [ ] Findings are sorted by severity (high → low)
- [ ] Skill makes no file modifications (`git status` unchanged after the run)
- [ ] Skill output contains the tier-state line (declared / documented / verified)

## Open questions

- **Depth of code verification**: the skill verifies only the key rules with sibling specs against code; the remaining ~30 rules are checked against the `quality_scale.yaml` declaration. When does a deeper, `hassfest`-like check become worthwhile?
- **`quality_scale.yaml` drift gate**: should the skill be consumable as a CI hook (exit code != 0 when declared ≠ verified tier)? Currently interactive only.
- **Marker synchronization**: should the skill also check the quality-scale markers of the sibling specs against HA's `tiers.json`, or does that stay a review task?
- **Auto-remediation chain**: is a chain that hands high findings straight to the responsible edit skill worthwhile? Currently every finding is dispatched manually.
