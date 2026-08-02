# Skill: `ha-esphome-solution`

Status: draft

## Context

Every other Home Assistant domain in this plugin has a front door; ESPHome did not. `ha-solution`'s routing table proves the gap: it routes an ESPHome device request straight at two individual skills and, for repository structure, HA-driven content, and the BOX family, at specs with no owning skill at all. With the ESPHome family now covering structure, devices, bindings, rendering, voice, and CI, a router is what keeps the operator from having to know which of them produces what.

This skill is the structural sibling of `ha-integration-solution`, `ha-lovelace-solution`, `ha-automation-solution`, and `ha-pixoo-solution`, and takes one deliberate position they do not share uniformly: the review layer stays outside the generation pass.

## Scope

One requirement per invocation. Classification, a dependency-ordered artifact plan, approval, dispatch of the owning `ha-esphome-*` skills, identity threading, and an aggregate report. Generation only; an opt-in, separately gated review pass may follow.

## Goals

- One discoverable entry point for an ESPHome result, whatever combination of artifacts it takes
- A plan the operator approves before anything is generated, in dependency order with the threaded identities named
- Structure before device: a repository without a fleet layout gets one before its first device file
- Dispatch resolved from the live skill inventory, so the family can grow without editing this skill
- A review layer that stays independent of authoring, so a generated artifact is never judged by the run that produced it

## Non-Goals

- Generating any artifact inline — every artifact belongs to its owning skill
- Custom components in C++/Python — no owning skill exists; the grounding specs place authoring one on a later axis
- Home Assistant integrations, cards, automations, and the Pixoo family — the sibling `*-solution` skills
- Compile, flash, and fleet OTA rollout, in every mode
- Producing the review verdict itself — that belongs to the two reviewer agents

## Requirements

- **MUST** classify and dispatch only; **MUST NOT** generate an artifact inline
- **MUST** resolve owning skills at runtime from the live `ha-esphome-*` inventory rather than a frozen name list, falling back to the anchor table only when the inventory genuinely cannot be enumerated, and saying so when it does
- **MUST** present the dependency-ordered artifact plan and wait for explicit approval before dispatching anything
- **MUST** gauge requirement confidence first, dispatching `requirements-elicit` (or an equivalent structured questioning path when that skill is unavailable) below the threshold instead of decomposing a fuzzy requirement
- **MUST** plan structure before devices: where no fleet layout exists, `ha-esphome-fleet-scaffold` precedes any device file
- **MUST** thread the identities earlier steps produce — the `name` / `id` / `comment` substitutions, the per-device API-key variable, package names and parameters, Home Assistant `entity_id`s, and the redraw script id — into dependent steps' inputs
- **MUST** stop and report on a NEEDS-WORK result rather than dispatching a dependent step onto an unfinished predecessor
- **MUST** relay each dispatched skill's report verbatim without re-judging it
- **MUST NOT** run a review as part of the generation pass, **MUST NOT** treat a reviewer verdict as its own acceptance gate, and **MUST** point at the independent reviewer agents as the operator's follow-up
- **MAY** run the review pass when `review_ready` is set, and then **MUST** require a second explicit approval distinct from the plan gate, **MUST** route each finding back to the owning skill rather than applying it inline, and **MUST** re-run the reviewer after a fix rather than declaring the finding closed
- **MUST NOT** compile, flash, or roll out in any mode
- **MUST** verify ESPHome facts against the official ESPHome documentation and Home-Assistant-side facts against the official Home Assistant documentation per `spec/ha/upstream-docs-verification`
- **MUST** support resume per `spec/claude/resumable-work/`, checkpointing the approved plan and per-step dispatch status

## Acceptance Criteria

- [ ] A single-artifact requirement is routed to the owning skill rather than decomposed into a plan
- [ ] A run against a repository with no fleet layout plans `ha-esphome-fleet-scaffold` as step 0
- [ ] No generation happens before the plan is explicitly approved
- [ ] The default run ends without any reviewer being dispatched, and names both reviewer agents as follow-ups
- [ ] A `review_ready` run gates the review separately and routes findings to owning skills rather than applying them

## Open Questions

- Whether the ESPHome family should keep a router of its own once the three-plugin split lands, or whether the `ha-esphome` plugin's single advertised router absorbs it, is settled by that restructure (requirement R3) rather than here.
