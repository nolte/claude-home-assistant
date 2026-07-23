---
name: ha-solution
description: The top-level front door for any Home Assistant requirement — classify a result-oriented request into one or more domains (integration/backend, Lovelace/frontend, YAML automation, Divoom Pixoo) and route it to the correct domain solution(s), so the user never has to pick a domain themselves. For a single-domain request it hands off to the owning ha-{integration,lovelace,automation,pixoo}-solution; for a genuinely cross-domain request (e.g. a custom card + its backing integration + an automation) it decomposes across the relevant solutions in dependency order and threads the shared identities (domain, entity_ids, card tags, command types) across domain boundaries. Resolves the domain solutions at runtime. Activate on "build me an X for Home Assistant" when the domain is unclear or spans several, "a custom card plus the integration behind it and an automation", "baue mir eine komplette HA-Lösung für …", "ich brauche Integration, Dashboard und Automation für …". Do not activate when the domain is already unambiguous and single (let the owning ha-*-solution activate directly), for a single clear artifact (the owning individual skill), or for deploying to a live HA instance.
tags: [home-assistant, orchestration, cross-domain, router]
phase: plan
summary: "Top-level router that classifies a Home Assistant requirement into one or more domains and routes each part to the owning ha-*-solution."
summary_de: "Oberster Router, der eine Home-Assistant-Anforderung in eine oder mehrere Domänen klassifiziert und jeden Teil an die zuständige ha-*-solution weiterleitet."
use_when:
  - "you want a full Home Assistant solution but aren't sure which domain it belongs to"
  - "you want a cross-domain result: a card plus its backing integration plus an automation"
  - "you want an integration, dashboard, and automation for one requirement"
dont_use_when:
  - situation: "The requirement is clearly a single integration/backend result"
    alternative: ha-integration-solution
  - situation: "The requirement is clearly a single Lovelace/frontend result"
    alternative: ha-lovelace-solution
  - situation: "The requirement is clearly a single YAML automation result"
    alternative: ha-automation-solution
  - situation: "The requirement is clearly a single Pixoo display result"
    alternative: ha-pixoo-solution
  - situation: "You are deploying or importing into a live HA instance"
    alternative: ha-integration-deploy
see_also:
  - ha-integration-solution
  - ha-lovelace-solution
  - ha-automation-solution
  - ha-pixoo-solution
---

# HA Solution

Spec: [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-solution/en.md) (EN canonical) / [`de.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-solution/de.md).

This skill is the **top-level router** above the four domain front doors (`ha-integration-solution`, `ha-lovelace-solution`, `ha-automation-solution`, `ha-pixoo-solution`). It owns no domain artifacts itself — it classifies the requirement into one or more domains, routes each part to the owning `*-solution`, and threads the shared identities across domain boundaries. Each domain solution keeps its own plan-approval gate, decomposition, dispatch, and spec conformance.

## Why this is a skill, not an agent

- **Plan-before-route gate** — the domain classification and the cross-domain plan must be presented and explicitly approved before any domain solution runs; that human-visible gate is core to the contract and an agent's fire-and-forget shape would lose it.
- **Mid-flow interactivity** — the "which domains does this span, and in which order" decision and the identity-threading across boundaries are per-run dialogues the user confirms.
- **Orchestrator that dispatches other skills** — the skill-orchestrates-skill default (see `skill-vs-agent`) keeps the entry point in skill form, exactly as each `*-solution` dispatches its own family.
- Counter-dimension considered: the per-domain solutions could run as parallel agents, but a cross-domain plan needs the backend's identities (domain, entity_ids) threaded into the frontend and automation parts *in order*, and that wiring must stay visible in the user's context; skill wins.

## When this skill activates

Use this skill when the user describes a **Home Assistant result** and either the domain is unclear or the requirement genuinely spans domains, so the user should not have to land on the right domain solution themselves — e.g. "a custom card for my pump, the integration behind it, and an automation that reacts to it", "a full solution: integration + dashboard + Pixoo status page".

## When NOT to activate

- the domain is already unambiguous and single → let the owning `ha-*-solution` activate directly (`ha-integration-solution`, `ha-lovelace-solution`, `ha-automation-solution`, `ha-pixoo-solution`)
- a single clear artifact (one card, one platform, one automation, one Pixoo page) → let the owning individual skill activate directly
- deploying/importing into a running HA instance → out of scope (the domain solutions and their agents own that)

## Hard rules

1. **Route, never generate or plan artifacts inline.** This skill classifies and dispatches domain solutions; it never generates an artifact and never does a domain's own artifact decomposition — that belongs to the owning `*-solution`. Each domain solution's own plan gate still applies.
2. **Resolve the domain solutions at runtime.** Match the requirement against the live inventory of `ha-*-solution` skills (see [Runtime solution resolution](#runtime-solution-resolution)), never a frozen name list — a domain solution added to or renamed within the family is routable without editing this skill.
3. **Classify into one or more domains.** Bucket the requirement into integration/backend, Lovelace/frontend, YAML-automation, and Pixoo parts; a single-domain requirement routes to exactly one solution, a cross-domain one to several.
4. **Plan before route.** Present the domain plan (which domains, which `*-solution`, dependency order, threaded identities) and wait for explicit approval before dispatching any solution.
5. **Order by dependency and thread shared identities across boundaries.** Dispatch a backend before the frontend/automation that consumes it, and pass the identities produced in one domain — `domain`, `entity_id`s, device ids, card tag / `custom:<type>`, WebSocket command `type` — into the inputs of the dependent domain solution(s). Keep all names consistent per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md).
6. **One requirement, one run.** No multi-requirement batches.
7. **Stop on a NEEDS-WORK domain result.** If a dispatched `*-solution` returns NEEDS-WORK (or one of its steps does), stop and report — do not route a dependent domain onto an unfinished predecessor.
8. **Delegate domain judgement.** Do not re-judge or re-plan a domain solution's internal decomposition or reports; relay them. Verify cross-domain HA internals against the official docs ([`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `requirement` | yes | — | The desired Home Assistant result, in prose |
| `target_dir` | no | working dir | repo / HA config root, passed through to the domain solutions |
| `known_identities` | no | asked when needed | an existing `domain`, `entity_id`s, or card tag to thread as sources |

## Runtime solution resolution

Resolve the owning domain solution for each classified part **at runtime**, by matching the requirement against the live inventory of this plugin's `ha-*-solution` skills — read each candidate's stated responsibility from your available-skills registry, or, when running inside the plugin source tree, `Glob skills/ha-*-solution/SKILL.md` and read its `description:`. Match on responsibility, not on a remembered name. The classification heuristic below is an **illustrative anchor** of the typical mappings, **not** an authoritative or exhaustive list: re-resolve against the current inventory on every run, so a domain solution newly added to (or renamed within) the family is routable immediately — without editing this skill (the runtime-lookup pattern of `issue-orchestrate`). If you genuinely cannot enumerate the live inventory, fall back to the anchor table and note the degraded resolution.

## Domain classification heuristic (requirement part → domain → solution)

| The requirement part is… | Domain | Owning solution |
|---|---|---|
| an own device/cloud/API protocol, config flow, coordinator, entities, services, or a WebSocket-command backend (Python custom integration) | integration / backend | `ha-integration-solution` |
| a dashboard surface — custom cards, editors, features, badges, strategies, custom panels | Lovelace / frontend | `ha-lovelace-solution` |
| a YAML automation / helper / template / blueprint (no own protocol, no config flow) | automation | `ha-automation-solution` |
| a Divoom Pixoo 64 display (pages, pixel-art, animation) | Pixoo | `ha-pixoo-solution` |

A cross-domain requirement maps to several rows; the typical order is **integration/backend → Lovelace/frontend → automation → Pixoo**, since the backend produces the `domain` and `entity_id`s the later domains consume.

## Workflow

### 1) Classify

Bucket the requirement into its domain parts. If it is single-domain, route straight to the owning `*-solution`. First gauge requirement confidence: when clearly specified, use the lightweight path — ask 1–3 targeted questions (which device/entity target, whether a dashboard surface is wanted, whether an automation should react) before classifying. When it is below a confidence threshold (vague or broad cross-domain result, unnamed targets, unclear scope), dispatch `requirements-elicit` first and classify against the confirmed requirement artifact — mirroring the `issue-orchestrate` upstream gate. Do not classify on guesses.

### 2) Plan

Present the cross-domain plan as a table in dependency order, then wait for explicit approval:

```markdown
| # | Domain | Solution | Depends on | Threaded identities | Purpose |
|---|---|---|---|---|---|
| 1 | integration | ha-integration-solution | — | → domain=pump, sensor.pump_power | the pump integration |
| 2 | frontend | ha-lovelace-solution | #1 | domain, entity_ids → card tag custom:pump-card | the pump dashboard card |
| 3 | automation | ha-automation-solution | #1 | sensor.pump_power | react to the pump |
```

### 3) Route

Dispatch each domain `*-solution` in plan order, passing the identities produced by earlier domains (`domain`, `entity_id`s, device ids, card tag, command `type`) as inputs. Each domain solution runs its own plan-approval, decomposition, and dispatch. Check the returned domain report; stop on NEEDS-WORK rather than routing a dependent domain onto an unfinished one.

### 4) Aggregate report

List each domain, the `*-solution` that ran, and the identities threaded across boundaries. Relay each domain solution's aggregate CONFORMANT / NEEDS-WORK report verbatim — do not re-judge them. Do not deploy.

## Boundaries

- A single-domain requirement → the owning `ha-*-solution` directly (this skill only classifies and routes)
- A single artifact → the owning individual skill
- A domain's internal artifact decomposition, generation, and conformance → the owning `*-solution` and its family
- Deploy / import into a live HA instance → out of scope; the domain solutions and their agents own that
