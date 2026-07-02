---
number: 1
status: closed
started: 2026-07-02
ended: 2026-07-02
value_statement: The plugin author invokes a bundled skill or agent and authors a Home Assistant artefact (integration, card, blueprint, automation, or ESPHome component) against Home Assistant Core and HACS conventions.
artifact_ref: develop (shipped capability, pre-planning-suite)
roadmap_items: [R-1]
features: [F-1]
---

## Goal

The plugin author uses the bundled Claude Code skills and agents to author Home
Assistant artefacts against Home Assistant Core and HACS conventions. Success is
verified by F-1 `acceptance-1`: invoking a bundled skill or agent authors a Home
Assistant artefact against those conventions.

## Features

- [F-1](../features/authored-home-assistant-artefact.md) — Authored Home Assistant artefact — status: done

## Out of scope

- claude-shared's portfolio-wide skills and agents (a separate repository).
- Home Assistant Core and HACS themselves (upstream conventions the skills target).

## Review notes

Retroactive reconciliation (2026-07-02): the
`claude-code-skills-and-agents-for-home-assistant` capability was already
`status: active` before this repository adopted the planning suite (issue
nolte/claude-shared#262 mission-authoring backfill). This sprint records roadmap
item R-1 and feature F-1 as `done`, and itself as `closed`, to document the
delivered MVP rather than to plan new work.
