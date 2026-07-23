# Requirements — Three-plugin split (ESPHome / HA end-user / developer)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
Do not record a requirement before declaring the bounded context below.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What**: Restructuring the `claude-home-assistant` monorepo into three audience-aligned
  Claude Code plugins — `ha-esphome`, `ha-automation`, `ha-dev` — with three marketplace
  entries, exactly one plugin-local router each, a shared spec base package, and the
  CI/release flow adapted to the multi-plugin layout. Decision record: `AUDIENCES.md`
  §"Offene Fragen → Plugin-Schnitt" (2026-07-23); work item: issue #90.
- **For whom**: the three audiences from `AUDIENCES.md` — ESPHome device-config author,
  HA automation/blueprint author (power user, incl. Pixoo device family), and HA developer
  (custom integrations + Lovelace/frontend) — plus the repo maintainer.
- **Out of scope**: splitting the repository itself (monorepo stays), the new end-user
  dashboard-assembly skill (explicit plugin-2 backlog per issue #90), and content changes
  to existing domain skills beyond the restructure.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `12`
  (spec defaults; budget is an engineering default recorded here)
- `U_gate = min_d c_d` over required dimensions = **0.8**
- Termination: `saturation` (all required dimensions ≥ `τ_high` after teach-back; no
  remaining candidate question had positive net EVPI; 7 of 12 budgeted questions used)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | specification (fold-in shape was undecided) | answer (router-invariant decision) + teach-back 2026-07-23; `k = 2` divergence check (merge vs. sub-orchestrators) drove the question |
| `non_functional` | yes | 0.8 | specification (versioning undecided) | answer (lockstep versioning) + teach-back 2026-07-23 |
| `constraints` | yes | 0.85 | specification (base-package distribution undecided) | answer (spec-only `inherits:`) + teach-back; `k = 2` check (fourth marketplace entry vs. `inherits:`) drove the question |
| `domain_objects` | yes | 0.85 | interpretation | issue #90 target table + naming answer (`ha-esphome` / `ha-automation` / `ha-dev`) + teach-back |
| `actors` | yes | 0.85 | interpretation | `AUDIENCES.md` audience artifact (run `20260723T190738Z-b4e2`) + operator scope confirmation |
| `acceptance_criteria` | yes | 0.8 | interpretation | teach-back confirmation of R1–R9 acceptance shape 2026-07-23 |
| `edge_cases` | yes | 0.8 | specification (legacy-entry migration undecided) | answer (hard cut + migration mapping) + teach-back |
| `scope_boundaries` | yes | 0.8 | interpretation | bounded-context confirmation (turn 1); discretionary follow-up withheld (EVPI below cost, see risks) |

## Requirements

- **R1** — WHEN the split release is published, the repository SHALL ship exactly three
  marketplace entries in `.claude-plugin/marketplace.json` — `ha-esphome`, `ha-automation`,
  `ha-dev` — each backed by its own `plugin.json`.
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: naming answer "ha-esphome / ha-automation / ha-dev" + teach-back
- **R2** — WHEN the restructure lands, every existing skill and agent SHALL be shipped by
  exactly one of the three plugins per the assignment table in issue #90; no skill or agent
  is dropped or duplicated.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: operator scope confirmation of issue #90 target structure
- **R3** — Each plugin SHALL advertise exactly one router as its entry point; `ha-solution`
  SHALL be removed; the four family solution skills (`ha-automation-solution`,
  `ha-pixoo-solution`, `ha-integration-solution`, `ha-lovelace-solution`) SHALL no longer be
  advertised entry points; a plugin router SHALL dispatch only within its own plugin (no
  cross-plugin routing or fallback). The internal fold-in shape (merge vs. internal
  sub-orchestrators) remains an implementation-time decision per plugin.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "Invariante fixieren, Form offen" + teach-back
- **R4** — The three plugins SHALL be versioned in lockstep: one release tag, one release
  draft, and an identical version string in all three `plugin.json` files.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: "Gemeinsame Version, Lockstep" + teach-back
- **R5** — Shared base specs (`naming-conventions`, `upstream-docs-verification`, shared
  architecture foundations) SHALL live exactly once in the monorepo `spec/` tree and be
  referenced by the plugins via the `inherits:` mechanism analogous to
  `spec/project/portfolio-inherited-spec-layer/`; a verbatim copy in a plugin payload
  remains a Critical finding.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: "Spec-only inherits:" + teach-back
- **R6** — WHEN the split release is published, the legacy `claude-home-assistant`
  marketplace entry SHALL be removed (hard cut), and the release notes and README SHALL
  carry a migration mapping from old to new slash-command namespaces.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: "Harter Schnitt" + teach-back
- **R7** — The EN-canonical + DE-translation contract for specs and docs SHALL remain
  intact through the restructure.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: bounded-context confirmation + teach-back
- **R8** — WHEN the restructure lands, `task lint`, `task test`, and `task docs` SHALL pass
  in the new layout, and per-plugin dogfooding (`claude --plugin-dir`) SHALL work for each
  of the three plugins.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: teach-back of R8
- **R9** — BEFORE directory restructuring begins, the multi-entry marketplace schema (one
  repo → several `marketplace.json` entries, per-plugin `plugin.json`, skill/agent directory
  layout) SHALL be verified against the current Claude Code plugin documentation (issue #90
  phase 1).
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: issue #90 phase 1 + teach-back

## Surviving assumptions / open risks

- **A1 (assumed)** — Skill and agent names remain globally unique across the three plugins
  (already true today by construction); a future skill added to one plugin must not collide
  with another plugin's names. Withheld as a question (EVPI below cost); flagged for the
  implementation review instead.
- **A2 (assumed)** — No confirmed external consumers exist (`AUDIENCES.md`: all audiences
  `assumed`), so the hard cut of the legacy marketplace entry (R6) is acceptable. If a real
  consumer surfaces before the split release, R6 must be revisited (deprecated-stub option).
- **Withheld question (discretionary-zone restraint)** — the marketplace publication
  threshold ("ab welchem Reifegrad lohnt die Listung") stays an open `AUDIENCES.md` question;
  it shapes release timing, not the split's requirements.
- **Risk** — the multi-plugin marketplace schema is unverified until R9 executes; structural
  decisions cemented before R9 would rest on an assumption.
