# Implementation Plan: Skill-Corpus Improvements (autonomous + parallel)

Status: draft · Date: 2026-07-22

## Context

This plan operationalizes the findings of the 2026-07-22 skill-corpus audit, which
assessed the plugin's skills against the official HA Integration Quality Scale
(54 rules, Bronze→Platinum, verified against `developers.home-assistant.io`) plus
the integration lifecycle. The corpus is strong and near lifecycle-complete
(43 skills, 5 agents, 126 specs, high spec↔skill fidelity). The audit surfaced a
small set of high-leverage gaps, the sharpest being that **`ha-quality-scale-audit`
checks rules (`parallel-updates`, `entity-unavailable`) that no generator emits** —
so the audit reports drift no skill can fix.

This plan turns every named improvement (F1–F6), missing skill (P1), and
consolidation (P2) into **18 work-packages (WPs)** structured for parallel
authoring and near-autonomous execution.

## 1. Execution model

| Principle | Consequence |
|---|---|
| **Author in parallel, merge serially** | The repo enforces serial merge (`pull-request-merge`: one PR at a time; remaining branches rebase after each merge). N WPs are authored simultaneously in N worktrees; merges happen one after another. |
| **Collision avoidance** | Each WP edits exactly one skill (`SKILL.md` + `spec/claude/<name>/{en,de}.md`). Findings touching the same file are bundled into one WP (no file tug-of-war). |
| **Two shared-file hotspots** | `spec/README.md` (index row) and `ha-integration-solution` (orchestrator wiring) are touched by every new skill — append-only, resolved trivially on rebase. |
| **Uniform per-WP gate** | Offline validation (frontmatter, EN/DE parity, spec↔skill) + `pre-commit run --files …` green → PR → serial merge. |
| **Autonomy tiers** | 🟢 fully autonomous (pattern-following) · 🟡 decision-gated (D1–D5) · 🔴 autonomy-limited (needs doc-verification; touches security-sensitive `.github/*` → `security-review` on merge). |

## 2. Decision gates (resolve first; recommendation baked into the WP catalog)

| Gate | Question | Recommendation | Affects |
|---|---|---|---|
| **D1** | Where does the shared redaction/PII classification (F6) live? | `spec/ha/security-hardening` (the enforcer owns it; diagnostics consumes) | WP0, WP6, WP7 |
| **D2** | Options-flow: own skill or a pattern in `ha-config-flow-augment`? | Own skill `ha-options-flow-augment` (symmetric with the augment family; clearest gap) | WP13 |
| **D3** | CI-scaffold & HACS-release: skill or agent? | Skills (interactive choices / user-gated outward action), with doc-verify + `.github/*` note | WP16, WP17 |
| **D4** | Icons: new skill or fold-in? | Fold into `ha-translation-sync` (TODO-marker mechanism generalizes; smaller surface) | WP11 |
| **D5** | New skills' orchestrator/README wiring | Self-contained per WP (rebase resolves append conflicts) | WP13–17 |

## 3. Work-package catalog

Effort S/M/L · Autonomy 🟢/🟡/🔴 · Deps = must be merged before this WP.

### Wave 0 — prerequisite

| WP | Title | Findings | Files | Deps | Auton. | Eff. | Done when |
|---|---|---|---|---|---|---|---|
| **WP0** | Shared redaction/PII classification | F6 | `spec/ha/security-hardening/{en,de}.md` | — | 🟡 D1 | S | Canonical MUST-redact key list incl. `latitude`/`longitude`; referenceable by A6/A7 |

### Wave 1 — per-skill fixes (all parallel, disjoint files)

| WP | Skill | Findings + backlog | Deps | Auton. | Eff. | Done when |
|---|---|---|---|---|---|---|
| **WP1** | `ha-integration-scaffold` | F1 (emit `PARALLEL_UPDATES` in platform modules), F4 (stale markers), CI-claim note | — | 🟢 | M | Scaffold emits `PARALLEL_UPDATES`; "(planned)" refreshed; hassfest-CI claim reconciled with WP16 |
| **WP2** | `ha-coordinator-add` | F1 (PU note), `runtime_data` typing re-verify, promote push coordinator | — | 🟢 | S | PU note + typed `RuntimeData` hard rule |
| **WP3** | `ha-entity-platform-add` | F1 (`available`/`entity-unavailable` hard rule + emit PU), test-harness pointer | — | 🟢 | M | `available` + `PARALLEL_UPDATES` mandatory; report points at `ha-test-harness-augment` |
| **WP4** | `ha-entity-description-mapper` | F1 (PU), F4, `entity_category∈EntityCategory` validation, test pointer | — | 🟢 | S | PU + enum validation + test pointer |
| **WP5** | `ha-service-definition-generator` | F2 (translated exceptions), register-once guard, `services.py` threshold | — | 🟢 | M | Exceptions carry `translation_key`; duplicate-registration guard; fixed threshold |
| **WP6** | `ha-diagnostics-augment` | F6 (coordinates MUST-redact), `entry.subentries` | WP0 | 🟢 | S | Coordinates MUST-redact; subentries in key space |
| **WP7** | `ha-security-audit` | F5 (TLS-verify + timeout checks), F6 (severity align), `services.py` scan align | WP0 | 🟢 | M | `ssl=False`/`verify=False`/timeout checks; coordinate severity == diagnostics |
| **WP8** | `ha-test-harness-augment` | F3 (snapshot kind), `test-before-setup` ownership | — | 🟢 | M | `snapshot` kind (`snapshot_platform` + registry/state + diagnostics snapshot) |
| **WP9** | `ha-repairs-add` | `async_delete_issue` placement hard-req, deprecation recipe, placeholder-type note | — | 🟢 | S | Delete path mandatory; `breaks_in_ha_version` recipe |
| **WP10** | `ha-quality-scale-audit` | CI/exit-code mode, auto-remediation dispatch, **report-template owner** | — | 🟢 | M | Drift-gate mode; per-finding edit-skill dispatch; shared report template defined |
| **WP11** | `ha-translation-sync` | `data_description` presence, **icons fold-in** | — | 🟡 D4 | M | `icons.json` auto-fill integrated; `data_description` in drift report |

### Wave 1b — consolidation (two skills, land together)

| WP | Title | Findings | Files | Deps | Auton. | Eff. |
|---|---|---|---|---|---|---|
| **WP12** | Discovery consolidation | Zeroconf ownership + OAuth disentanglement | `ha-discovery-augment` (zeroconf retrofit, `unique_id` lookup table, `config.abort.*` strings) **+** `ha-config-flow-augment` (remove zeroconf pattern, add `application_credentials` to `oauth`, read reauth trigger for real) | — | 🟢 | L |

WP12 bundles all `ha-config-flow-augment` edits once (the collision hotspot) and lands with the discovery retrofit so no zeroconf gap opens.

### Wave 2 — new skills (parallel authored; shared files via rebase)

| WP | New skill | Prio | Deps | Auton. | Eff. | Core |
|---|---|---|---|---|---|---|
| **WP13** | `ha-options-flow-augment` | P1 | — | 🟡 D2 | M | Generic option-key retrofit (`OptionsFlow`, `entry.options`), tests |
| **WP14** | `ha-config-entry-migrate` | P1 | — | 🟢 | M | `async_migrate_entry` + `version`/`minor_version` bump, migration tests |
| **WP15** | `ha-device-registry-augment` | P2 | — | 🟢 | M | `device_info`/`via_device`/multi-device, `stale-devices` (Gold `devices`/`stale-devices`) |
| **WP16** | `ha-integration-ci-scaffold` | P1 | WP1 | 🔴 D3 | L | `.github/workflows/*` (hassfest, `hacs/action`, pytest matrix); doc-verify; **security-review on merge** |
| **WP17** | `ha-hacs-release` | P1 | — | 🔴 D3 | L | Tag-driven HACS release (`ha/hacs-release`); release semantics doc-verify; outward-action-gated |

**Total:** 1 prereq + 11 fixes + 1 consolidation + 5 new skills = **18 WPs**.

## 4. Dependency DAG & waves

```
Wave 0:   WP0 ─────────────┐
                           ▼
Wave 1:   WP1 WP2 WP3 WP4 WP5 [WP6 WP7←WP0] WP8 WP9 WP10 [WP11←D4]   ← all parallel
Wave 1b:  WP12                                                        ← parallel to Wave 1
Wave 2:   WP13 [WP14] [WP15] [WP16←WP1] WP17                          ← parallel authored
```

Only two real authoring dependencies: **WP6/WP7 after WP0** (consume the classification) and **WP16 coordinates with WP1** (CI claim). Everything else is freely parallelizable.

## 5. Collision matrix & merge order

| File | Touched by | Strategy |
|---|---|---|
| own `SKILL.md` + `spec/claude/<name>` | exactly 1 WP (except WP12 = 2 skills) | collision-free |
| `spec/ha/security-hardening` | WP0 | merge before WP6/WP7 |
| `spec/README.md` (index) | WP13–17 (marker WPs do **not** touch it) | append-row → trivial on rebase |
| `ha-integration-solution` (orchestrator) | WP13–17 | append-wiring → trivial on rebase |

**Recommended merge sequence** (serial lane, minimizes rebase pain):
1. **WP0** (prereq).
2. **WP1–WP12** in any order — disjoint files, clean rebases (no text conflicts).
3. **WP13 → WP14 → WP15 → WP16 → WP17** one at a time — each rebase resolves only the `README` row + orchestrator append (mechanical).

## 6. Orchestration recipe (autonomous + parallel)

**Per WP (autonomous authoring cycle):**
1. Worktree `feat/<wp-slug>` off `origin/develop` (parallel worktree; primary stays on `develop`).
2. Author strictly to the WP spec + the sibling skill it mirrors (🟢 WPs mirror existing patterns 1:1).
3. **Self-gate:** frontmatter valid (`name`==folder), EN/DE structurally parallel (identical headers / RFC-2119), spec↔skill consistent, `pre-commit run --files …` green.
4. PR → `develop`.
5. **Merge serially** via `pull-request-merge` (review gate + labels + `automerge` + verify), then rebase the next branch.

**Parallelization options:**
- **Fork fan-out (recommended):** one fork agent per 🟢 WP, all Wave-1/1b/2 WPs at once — each in its own worktree; collect PRs and merge serially.
- **Workflow:** authoring as a parallel stage (`pipeline`/`parallel`); merge stays outside (serial, review-gated). Requires explicit workflow opt-in.
- **Guardrail:** 🔴 WPs (WP16/WP17) do NOT run fully autonomously — they need doc-verification (Actions/hassfest/HACS mechanics) and trigger `security-review` on merge (`.github/*`). Pause before the PR for human review there.

## 7. Recommended execution sequence (batches)

| Batch | WPs | Rationale |
|---|---|---|
| **B0** | resolve gates D1–D5, WP0 | foundation (classification) + switches |
| **B1 (max parallelism)** | WP1–WP11 + WP12 | 12 disjoint authoring jobs; closes the entire audit↔generator drift (F1–F6) — largest quality effect |
| **B2** | WP13, WP14, WP15 | 3 new P1/P2 skills, net-new files |
| **B3 (gated)** | WP16, WP17 | CI/release — doc-verify + security-review, last |

After **B1** the core is reached: the quality-scale audit no longer reports anything a generator can't emit, and the security/translation gaps are closed. **B2/B3** raise coverage and release readiness.

## 8. Provenance & limits

- The 54 quality-scale rules (Bronze 20 / Silver 10 / Gold 21 / Platinum 3) are verified against the official Checklist page; rule ids exact, descriptions summarized.
- Coverage and skill findings come from reading the repo (`SKILL.md` + `spec/claude/*`).
- Flagged (not click-verified this run): a few doc URLs (services.yaml/options-flow/device-registry) and the exact numeric `PARALLEL_UPDATES` semantics (0 = unlimited) — re-check on the `parallel-updates` rule page before hard-coding.
- This is a static analysis of the corpus, not a live test of generated integrations. WP16/WP17 in particular require official-doc verification of CI/release mechanics before authoring.
