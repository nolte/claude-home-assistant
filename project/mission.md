---
mission_statement: "claude-home-assistant gives the plugin author and later public users a Claude Code skill and agent set that authors Home Assistant artefacts (custom integrations, Lovelace cards, blueprints, automations, ESPHome work) against Home Assistant Core and HACS conventions."
relevant_outcomes: [O-1, O-2]
audiences:
  - "Plugin-Autor beim Dogfooding in diesem Repo (nolte)"
  - "Spätere öffentliche Nutzer (HA-Custom-Integration- und Card-Autoren-Community)"
verifies_via: F-1:acceptance-1
time_bound:
  kind: mvp_completion
mvp_status: achieved
created: 2026-07-02
revised_at: null
---

## Statement

`claude-home-assistant` gives the plugin author and later public users a Claude
Code skill and agent set that authors Home Assistant artefacts (custom
integrations, Lovelace cards, blueprints, automations, ESPHome work) against Home
Assistant Core and HACS conventions.

- **Specific** — the statement names *what* (a Claude Code skill and agent set for
  Home Assistant development) and *for whom* (the dogfooding plugin author and the
  later public community, resolved in `audiences`).
- **Measurable** — `verifies_via: F-1:acceptance-1`: the plugin author invokes a
  bundled skill or agent that authors a Home Assistant artefact against Core and
  HACS conventions.
- **Achievable** — the minimum viable product is the shipped
  `claude-code-skills-and-agents-for-home-assistant` capability; roadmap item R-1
  is `mvp: true`, `detail: fine`, `target_sprint: 1`.
- **Relevant** — `relevant_outcomes: [O-1, O-2]`, each resolving to an outcome in
  `project/goals.md`.
- **Time-bound** — `time_bound: { kind: mvp_completion }`; the bound is the moment
  the shipped MVP is recorded as achieved.

## Audiences

- **Plugin-Autor beim Dogfooding in diesem Repo (nolte)** — the MVP delivers the
  skills and agents the author invokes while building Home Assistant integrations,
  cards, blueprints, automations, and ESPHome work in this repository, with
  consistent, spec-grounded tooling.
- **Spätere öffentliche Nutzer (HA-Custom-Integration- und Card-Autoren-Community)**
  — the MVP delivers the same skill and agent set for later public users, who
  adopt it through the Claude Code plugin marketplace to author their own Home
  Assistant artefacts.

## Verification

The mission is verified by feature **F-1 — Authored Home Assistant artefact**,
acceptance criterion 1: *"The plugin author invokes a bundled skill or agent that
authors a Home Assistant artefact (integration, card, blueprint, automation, or
ESPHome component) against Home Assistant Core and HACS conventions."* This is the
`verifies_sprint_value` criterion for sprint 0001 and holds against the shipped
skill and agent set, so the MVP is recorded as `achieved`.

## Source

- **Audience artefact**: `AUDIENCES.md` at the `claude-home-assistant` repository
  root (consulted at its current develop tip); the two `audiences` entries are the
  dogfooding author and the later public community.
- **Outcomes referenced**: O-1, O-2 from `project/goals.md`.
- **Authored by**: the `mission-define` cascade (issue nolte/claude-shared#262
  mission-authoring backfill), 2026-07-02. The MVP is modelled retroactively: the
  skill and agent set was already `status: active` when the repository adopted the
  planning suite, so R-1 is recorded `status: done` and `mvp_status` opens at
  `achieved`. The audience identifiers are kept verbatim in their authored German.
