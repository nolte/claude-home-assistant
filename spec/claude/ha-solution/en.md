# Skill: `ha-solution`

Status: draft

## Context

There are four domain front doors — `ha-integration-solution` (Python custom-integration backend), `ha-lovelace-solution` (Lovelace/frontend), `ha-automation-solution` (YAML automations/helpers), and `ha-pixoo-solution` (Divoom Pixoo display) — but **no orchestrator above them**. Domain selection relies on implicit skill-description matching, and a genuinely cross-domain request (e.g. a custom card + its backing integration + an automation) falls between the four front doors: a user with a mixed requirement must land on the right domain solution themselves, and no single skill owns a request that spans domains.

This skill is the **top-level router**: it classifies a fuzzy Home Assistant requirement into one or more domains, routes each part to the owning `*-solution`, and threads the shared identities (`domain`, `entity_id`s, card tags, command types) across domain boundaries. It owns no domain artifacts and does no domain-internal decomposition — each domain solution keeps its own plan-approval gate, decomposition, dispatch, and spec conformance.

## Scope

Domain classification and cross-domain routing above the `ha-*-solution` family. One requirement per run → one domain plan → N dispatched `*-solution`s in dependency order → one aggregate report. The router decides *which domains* a requirement spans, *which order* to run them, and *which identities* to thread across boundaries — never the content of any single domain artifact.

## Goals

- Accept any Home Assistant requirement at a single entry point and route it to the correct domain solution(s), without the user knowing the domain landscape
- Classify the requirement into one or more of integration/backend, Lovelace/frontend, YAML-automation, and Pixoo
- Decompose a cross-domain requirement across the relevant `*-solution`s in dependency order and thread the shared identities (`domain`, `entity_id`s, device ids, card tag/`custom:<type>`, command `type`) across domain boundaries
- Resolve the domain solutions at runtime against the live `ha-*-solution` inventory, so an added or renamed domain solution is routable without editing this skill
- Delimit cleanly against the four domain solutions: a single-domain requirement routes straight to its owning `*-solution`

## Non-Goals

- A domain's own artifact decomposition, generation, and spec conformance — that stays with the owning `*-solution` and its family
- Generating any artifact itself
- Re-judging or re-planning a domain solution's internal decomposition or reports — the router relays them
- Deploying to or importing into a running HA instance — the domain solutions and their agents own that

## Requirements

### Activation triggers

- **MUST** activate on result-oriented HA requests where the domain is unclear or spans several:
  - "a custom card for my pump, the integration behind it, and an automation that reacts to it"
  - "a full solution: integration + dashboard + Pixoo status page"
  - "baue mir eine komplette HA-Lösung für …", "ich brauche Integration, Dashboard und Automation für …"
- **SHOULD** not activate when the domain is already unambiguous and single (the owning `ha-*-solution` applies directly) or when the requirement is a single clear artifact (the owning individual skill applies)

### Inputs

- **MUST** capture: `requirement` (prose, the desired HA result)
- **MAY** capture: `target_dir` (repo / HA config root, passed through to the domain solutions) and `known_identities` (an existing `domain`, `entity_id`s, or card tag to thread as sources)

### Pre-flight

- **MUST** check `requirement` is non-empty; on underspecification ask 1–3 targeted questions (which device/entity target, whether a dashboard surface is wanted, whether an automation should react) before classifying
- **MUST** route a clearly single-domain requirement straight to the owning `*-solution` instead of adding a routing layer

### Classification & routing rules

- **MUST** resolve the owning domain solution for each classified part at runtime by matching the requirement against the live `ha-*-solution` skill inventory (each candidate's stated responsibility), not from a frozen name list — the classification mappings are an illustrative anchor, re-resolved each run, so a domain solution added to or removed from the family is routable without editing the router (mirroring `issue-orchestrate`'s runtime-lookup dispatch)
- **MUST** classify the requirement into one or more domains — integration/backend → `ha-integration-solution`, Lovelace/frontend → `ha-lovelace-solution`, YAML-automation → `ha-automation-solution`, Pixoo → `ha-pixoo-solution`
- **MUST** present a domain plan as a table in dependency order before routing: per entry `#`, domain, owning `*-solution`, dependency (`depends-on`), threaded identities, purpose — and wait for explicit confirmation
- **MUST** dispatch the domain solutions in dependency order — a backend before the frontend/automation that consumes it; the typical order is integration/backend → Lovelace/frontend → automation → Pixoo — and thread the identities (`domain`, `entity_id`s, device ids, card tag/`custom:<type>`, command `type`) produced in one domain into the inputs of dependent domain solutions
- **MUST NOT** generate an artifact or perform a domain's own artifact decomposition; every domain runs through its owning `*-solution`, which keeps its own plan-approval gate
- **MUST** stop and report when a dispatched `*-solution` (or one of its steps) returns NEEDS-WORK, rather than routing a dependent domain onto an unfinished predecessor
- **MUST** keep all identifiers consistent across domains per `ha/naming-conventions` and verify cross-domain HA internals against the official docs (`ha/upstream-docs-verification`)

### Aggregate report

- **MUST** list, at the end, each domain, the `*-solution` that ran, and the identities threaded across boundaries
- **MUST** relay each domain solution's aggregate CONFORMANT / NEEDS-WORK report without re-judging it

### Prohibitions

- **MUST NOT** orchestrate more than one requirement per run
- **MUST NOT** execute a domain plan without user confirmation
- **MUST NOT** re-judge or re-plan a domain solution's internal decomposition or reports
- **MUST NOT** deploy to or import into a running HA instance

## Acceptance criteria

- [ ] A single entry point accepts any HA requirement and routes it to the correct domain solution(s)
- [ ] The requirement is classified into one or more of integration/backend, Lovelace/frontend, YAML-automation, Pixoo
- [ ] A cross-domain requirement is decomposed across the relevant `*-solution`s in dependency order with identities threaded across boundaries
- [ ] Domain solutions are resolved against the live `ha-*-solution` inventory each run (an added or renamed domain solution is routable without editing the router)
- [ ] A single-domain requirement routes straight to the owning `*-solution`; the skill delimits cleanly against the four domain solutions
- [ ] Stops on a NEEDS-WORK domain result instead of routing a dependent domain further
- [ ] Aggregate report lists each domain, the solution that ran, the threaded identities, and relays the individual reports

## Open questions

- **Solution vs. agent dispatch**: should the per-domain solutions run as skills (visible, sequential) or via agents (isolated, parallel)? Currently skill dispatch, because the cross-domain identity threading (backend `domain`/`entity_id`s → frontend card / automation) must stay visible in the user context.
- **Double gating**: each domain `*-solution` has its own plan-approval gate, and the router adds a domain-plan gate on top. Should the router's approval subsume the first domain solution's gate to avoid gate fatigue, or stay separate? Currently separate — the router plans domains, each solution plans its own artifacts.
- **Requirement confidence**: how should the router treat an under-specified cross-domain requirement — its own lightweight clarify, or dispatch `requirements-elicit` first? (See the sibling `ha-*-solution` requirements-elicit gate work.)
- **Identity source of truth**: when several domains could each define an `entity_id`, which domain owns it? Currently the backend/integration domain is the source and later domains consume it.
