---
name: ha-pixoo-solution
description: Plan and orchestrate a complete Divoom Pixoo 64 display from a result-oriented requirement, so the user never has to pick which Pixoo skill to use. Decomposes the requirement into the minimal combination of artifacts across the Pixoo skill family, presents a dependency-ordered artifact plan for approval, then dispatches ha-pixoo-page-author, ha-pixoo-pixel-art-author, and ha-pixoo-animation-author in order — threading the page structure, component positions, palette, and the target sensor.<name>_current_page entity between steps. Generation only; never deploys. Activate on "build me a Pixoo display for…", "show X's status on the Divoom", "I want an animated Pixoo page", "baue mir eine Pixoo-Anzeige für…", "zeig den Status von X auf dem Divoom". Do not activate for a single clear artifact (let the owning skill handle it), device setup / config flow (using the existing integration, not authoring), or deploying to a live HA instance.
tags: [home-assistant, divoom-pixoo, display, orchestration]
---

# HA Pixoo Solution

Grounding specs: [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md) (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/en.md), [`ha/pixoo-pixel-art`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art/de.md), [`ha/pixoo-pixel-art-animation`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art-animation/de.md).

This skill is the **front door** to the Divoom Pixoo skill family. It does not generate any artifact itself — it decomposes the requirement, plans the combination, and dispatches the owning authoring skills, each of which owns its generation and spec conformance.

## Why this is a skill, not an agent

- **Plan-before-generate gate** — the artifact plan must be presented and explicitly approved before any generation; that human-visible gate is core to the contract and an agent's fire-and-forget shape would lose it.
- **Mid-flow interactivity** — clarifying questions (which info, static vs. animated, target device entity, palette), plan confirmation, and the "this is just device setup, not authoring" decision are per-run dialogues.
- **Orchestrator that dispatches other skills** — the skill-orchestrates-skill default (see `skill-vs-agent`) keeps the entry point in skill form, like `ha-lovelace-solution` dispatching its frontend family.
- Counter-dimension considered: the per-artifact generation could run as parallel agents, but the plan approval and the identity threading (page structure → pixel-art slot → animation phase, target entity) must stay visible in the user's context; skill wins.

## When this skill activates

Use this skill when the user describes a **Pixoo display result** that likely needs more than one artifact, and should not have to know which Pixoo skill produces what — e.g. "show my heat-pump power and a battery icon on the Pixoo", "an animated rain page driven by the weather entity", "a progress page for the dishwasher plus a buzzer alert".

## When NOT to activate

- a single clear artifact (one page, one pixel-art graphic, one animation) → let the owning skill activate directly
- device setup, discovery, config flow, IP/`scan_interval` changes, entity wiring → that is **using** the existing `divoom_pixoo` integration per [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md), not authoring; out of scope
- deploying/importing the config into a running HA instance → out of scope (generation only)

## Hard rules

1. **Never generate inline.** Every artifact is produced by its owning skill — `ha-pixoo-page-author`, `ha-pixoo-pixel-art-author`, or `ha-pixoo-animation-author`. This skill plans and dispatches; it does not write artifacts.
2. **Plan before generate.** Always present the dependency-ordered artifact plan and wait for explicit approval before dispatching anything.
3. **One requirement, one run.** No multi-requirement batches.
4. **Minimal artifacts.** Decompose to the fewest artifacts that satisfy the requirement; a plain info page does not need a pixel-art or animation add-on.
5. **Thread identities.** Dispatch in dependency order and pass the identities produced in earlier steps — the `pages_data` page structure, component positions, the chosen palette/ramps, and the target `sensor.<name>_current_page` entity (the service target per [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md)) — as inputs to dependent steps.
6. **Stop on NEEDS-WORK.** If a dispatched skill returns NEEDS-WORK, stop and report — do not build a dependent artifact on an unfinished predecessor.
7. **Generation only.** Never deploy to a live HA instance and never modify the device or its config entry.
8. **Verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)); for the integration's own contract read the grounding specs above, not memory.

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `requirement` | yes | — | The desired Pixoo display result, in prose |
| `target_dir` | no | working dir | repo / HA config root, passed through to dispatched skills |
| `device_entity` | no | asked when needed | the target `sensor.<name>_current_page` entity (service target) |
| `palette` | no | asked / derived | a shared palette/ramp set to keep pages coherent (per `ha/pixoo-pixel-art`) |

## Decomposition heuristic (requirement → artifact → skill)

| The requirement needs… | Artifact | Owning skill |
|---|---|---|
| an info layout (text/data, special page PV/progress_bar/fuel, native channel/clock/gif/visualizer) | a `pages_data` page | `ha-pixoo-page-author` (step 1 — owns the page structure) |
| a detailed pixel-art graphic (icon, illustration) with shading/contours, embedded in a page | pixel-art (procedural components or a 64×64 image plan) | `ha-pixoo-pixel-art-author` (fills a page slot) |
| a moving display (motion, color animation, ticking/pulsing) | animated `components` page + driving automation | `ha-pixoo-animation-author` (adds the temporal dimension to a page) |

Dispatch order is page → pixel-art → animation: the page defines the canvas and target entity, pixel-art fills graphic slots within it, and animation wraps the result in a phase-driven frame loop.

## Boundaries

- Device/integration setup, services, page-type reference → use, per [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md) (not authoring)
- Single page → `ha-pixoo-page-author`
- Single pixel-art graphic → `ha-pixoo-pixel-art-author`
- Single animation → `ha-pixoo-animation-author`
- Deploy to live HA → out of scope
