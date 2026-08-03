---
name: ha-esphome-solution
description: "Plans and orchestrates a complete ESPHome device or fleet result from a requirement, so the user never has to pick which ESPHome skill produces what. Decomposes it into the minimal dependency-ordered set of artifacts across the ha-esphome-* family — repository layout and packages, the device file, sensors and buses, Home-Assistant-driven bindings, display content, the voice satellite, CI validation — presents that plan for approval, then dispatches the owning skills resolved from the live inventory at runtime, threading device identities, package parameters, and entity ids between steps. Generation only: it never compiles, flashes, or rolls out, and never runs the review itself — the read-only reviewer agents stay a separately triggered pass, so an artifact is never judged by its own author. Activate on \"build me an ESPHome device for…\", \"set up my ESPHome fleet\", or equivalent German requests. Do not activate for a single clear artifact (the owning skill). Supports resume."
tags: [home-assistant, esphome, orchestration, yaml]
phase: plan
summary: "Plans and orchestrates a complete ESPHome device or fleet result, dispatching the ha-esphome-* skills in dependency order; generation only."
summary_de: "Plant und orchestriert ein vollständiges ESPHome-Geräte- oder Fleet-Ergebnis und dispatcht die ha-esphome-*-Skills in Abhängigkeitsreihenfolge; nur Generierung."
use_when:
  - "you want a whole ESPHome device built and don't know which skills it takes"
  - "you want a fleet set up: layout, packages, first devices, and CI"
  - "you want a device that shows Home Assistant data and answers voice commands"
dont_use_when:
  - situation: "You need only one new device config file"
    alternative: ha-esphome-config-scaffold
  - situation: "You need only one more sensor or bus on an existing device"
    alternative: ha-esphome-config-augment
  - situation: "The result is a Python Home Assistant custom integration"
    alternative: ha-integration-solution
  - situation: "The display is a Divoom Pixoo 64"
    alternative: ha-pixoo-solution
see_also:
  - ha-esphome-fleet-scaffold
  - ha-esphome-config-scaffold
  - ha-esphome-display-author
  - ha-esphome-voice-satellite-add
  - ha-esphome-config-reviewer
  - ha-esphome-fleet-reviewer
  - ha-solution
resumable: true
---

# HA ESPHome Solution

Spec: `spec/claude/ha-esphome-solution/en.md` (EN canonical) / `spec/claude/ha-esphome-solution/de.md` (DE translation). This spec governs the front-door dispatch/plan contract, structurally consistent with its `ha-{integration,lovelace,automation,pixoo}-solution` siblings; the grounding specs below govern the ESPHome artifacts themselves.

Grounding specs: `spec/ha/esphome-config-patterns/en.md`, `spec/ha/esphome-project-structure/en.md`, `spec/ha/esphome-ha-driven-content/en.md`, and — where the device is one — `spec/ha/esp32-s3-box/en.md`, `spec/ha/esp32-s3-box-display/en.md`, `spec/ha/esp32-s3-box-display-design/en.md`, `spec/ha/assist-pipeline/en.md`.

This skill is the **front door** to the ESPHome skill family. It generates nothing itself: it decomposes the requirement, plans the combination, and dispatches the owning skills, each of which owns its generation and spec conformance.

## Why this is a skill, not an agent

- **Plan-before-generate gate** — the artifact plan must be presented and explicitly approved before any generation; that human-visible gate is core to the contract and an agent's fire-and-forget shape would lose it.
- **Mid-flow interactivity** — the clarifying questions (which board, which values come from Home Assistant, is there a screen, is it a voice satellite) and the plan confirmation are per-run dialogues.
- **Orchestrator that dispatches other skills** — the skill-orchestrates-skill default keeps the entry point in skill form, exactly as the sibling `*-solution` skills do.
- Counter-dimension considered: the per-artifact generation could run as parallel agents, but the identity threading (device name → package parameters → entity ids → redraw script) must stay visible in the operator's context; skill wins.

## When this skill activates

The user describes an **ESPHome result** that likely needs more than one artifact and should not have to know which skill produces what — "ein Node im Gewächshaus, der Feuchte misst und den Sollwert aus HA anzeigt", "set up my ESPHome repo and add the first two plugs", "make the box a voice satellite with a status screen".

## When NOT to activate

- a single clear artifact (one device file, one sensor, one package, one page) → let the owning skill activate directly
- a Python custom integration, a Lovelace card, or a YAML automation → the sibling `ha-*-solution` skills
- a Divoom Pixoo 64 display → `ha-pixoo-solution`
- ESPHome **custom components** in C++/Python → out of scope; no owning skill exists yet, and the grounding specs place authoring one on a later axis
- compiling, flashing, or fleet OTA rollout → out of scope in every mode

## Hard rules

1. **Never generate inline.** Every artifact is produced by its owning skill, resolved at runtime from the live `ha-esphome-*` inventory (see [Runtime skill resolution](#runtime-skill-resolution)). This skill plans and dispatches.
2. **Plan before generate.** Present the dependency-ordered artifact plan and wait for explicit approval before dispatching anything.
3. **Confidence-gate the requirement.** When it is clearly specified, ask 1–3 targeted questions (which board, which values come from Home Assistant, screen, voice). When it is below a confidence threshold, dispatch `requirements-elicit` (from the nolte-shared plugin; when it is not installed, reach the same rigor through a structured series of targeted questions) and plan against the confirmed artifact instead of decomposing a fuzzy requirement.
4. **Structure before device.** When the repository has no fleet layout, the plan starts with `ha-esphome-fleet-scaffold`; a device file is never the first artifact in an unstructured repository, because onboarding a device that has to touch a package means the package was cut wrong.
5. **Thread identities.** Dispatch in dependency order and pass what earlier steps produced — the device `name` / `id` / `comment` substitutions, the per-device `<DEVICE>_API_KEY` variable, the package names and their parameters, the resulting Home Assistant `entity_id`s, and the display's single redraw script id — into the inputs of dependent steps.
6. **Minimal artifacts.** Decompose to the fewest artifacts that satisfy the requirement; a sensor node needs no display author and no voice binding.
7. **Stop on NEEDS-WORK.** If a dispatched skill returns NEEDS-WORK, stop and report — never build a dependent artifact on an unfinished predecessor.
8. **Generation only.** Never compile, flash, or roll out; never modify a running Home Assistant instance. Validation is `esphome config` where the toolchain exists, reported as an open caller step where it does not.
9. **The review stays independent.** This skill never runs a review as part of the generation pass and never treats a reviewer's verdict as its own acceptance gate. The two read-only reviewer agents — `ha-esphome-config-reviewer` and `ha-esphome-fleet-reviewer` — are a separate, caller-triggered pass, so what was generated is never judged by its own author in the same breath. The closing report points at them; the operator decides when to run them (see [Independent review](#5-independent-review)).
10. **Relay reports verbatim.** Pass each dispatched skill's report through without re-judging it.
11. **One requirement, one run.** No multi-requirement batches.
12. **Verify upstream facts, never memory.** ESPHome keys against <https://esphome.io>, Home-Assistant-side facts against the official Home Assistant documentation, per `spec/ha/upstream-docs-verification/en.md`.

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `requirement` | yes | — | The desired ESPHome result, in prose |
| `target_dir` | no | working dir | the ESPHome config repository, passed through to dispatched skills |
| `board` | no | asked | the board or device family the result runs on |
| `known_identities` | no | asked when needed | an existing device name, package, or Home Assistant `entity_id` to thread |
| `review_ready` | no | `false` | opt-in: after a **second** explicit gate, run the independent review pass (§5) and route findings back; the default ends at generation |

## Runtime skill resolution

Resolve the owning skill for each artifact **at runtime**, by matching the requirement against the live inventory of this plugin's `ha-esphome-*` skills — read each candidate's stated responsibility from your available-skills registry, or, when running inside the plugin source tree, `Glob skills/ha-esphome-*/SKILL.md` and read its `description:`. Match on responsibility, not on a remembered name. The decomposition heuristic below is an **illustrative anchor**, not an authoritative or exhaustive list: re-resolve on every run, so a skill newly added to (or renamed within) the family is dispatchable immediately without editing this skill. If you genuinely cannot enumerate the live inventory, fall back to the anchor table and note the degraded resolution.

## Decomposition heuristic (requirement → artifact → skill)

| The requirement needs… | Artifact | Owning skill |
|---|---|---|
| a repository to hold devices, or shared configuration to live somewhere | config root, `common/` tree, base + board package | `ha-esphome-fleet-scaffold` (step 0 — only when the layout is missing) |
| a shared concern cut, parameterised, or deviated from without forking | one package under `common/` | `ha-esphome-package-author` |
| a new device to exist | one `<device-name>.yaml` | `ha-esphome-config-scaffold` |
| one more sensor, bus, component, or package binding on a device | a block in the device file | `ha-esphome-config-augment` |
| Home Assistant to drive what the device shows or does | subscription, action, writable entity, or return channel | `ha-esphome-binding-add` |
| something on a panel | pages, redraw script, layout zones, fonts, images, and the design system applied to them | `ha-esphome-display-author` |
| the device to hear and speak | audio path, `voice_assistant:`, wake word, mute | `ha-esphome-voice-satellite-add` |
| every device validated on every change | validation + compile workflows | `ha-esphome-ci-scaffold` |

Typical order: **fleet layout → packages → device file → sensors/buses → Home-Assistant bindings → display → voice → CI**. Structure precedes the device, the device precedes its content, and the bindings precede the rendering that consumes them.

## Workflow

### 1) Understand

Gauge requirement confidence and either ask the 1–3 targeted questions or dispatch `requirements-elicit`. Establish the board or device family, whether the repository already has a fleet layout, and which values are Home Assistant's rather than the device's.

### 2) Plan

Present the artifact plan as a table in dependency order, then wait for explicit approval:

```markdown
| # | Artifact | Skill | Depends on | Threaded identities | Purpose |
|---|---|---|---|---|---|
| 1 | board package | ha-esphome-fleet-scaffold | — | → common/esp32-s3-box-3.yaml | the board baseline |
| 2 | device file | ha-esphome-config-scaffold | #1 | name=box-02, BOX_02_API_KEY | the device itself |
| 3 | HA binding | ha-esphome-binding-add | #2 | sensor.target_temperature | the setpoint from HA |
| 4 | display pages | ha-esphome-display-author | #2, #3 | draw_display, id(setpoint) | what the screen shows |
```

### 3) Dispatch

Dispatch each skill in plan order, passing the identities earlier steps produced. Each skill runs its own pre-flight, confirmation, and conformance. Check each returned report; stop on NEEDS-WORK rather than dispatching a dependent step onto an unfinished one.

### 4) Report

List every produced or changed file, the artifact it is, and the wiring between them (which substitution feeds which package, which entity feeds which page). Relay each skill's report verbatim. Name the environment variables the operator must set, the validation status per device file, and the on-device bring-up that is still owed. Point at the independent review as the operator's follow-up **without running it**, unless `review_ready` is set — then continue into §5 after a second explicit gate.

### 5) Independent review

Runs **only** when `review_ready` is set, and **only** after a second explicit approval distinct from the plan gate:

1. Dispatch `ha-esphome-config-reviewer` for the device-level verdict, and `ha-esphome-fleet-reviewer` where the run touched the repository structure, packages, or CI. Both are read-only and both re-read the specs themselves rather than trusting this run's account of them.
2. Relay the verdicts verbatim. On NEEDS-WORK, route each finding to the owning skill named in it, re-dispatch the fix, and re-run the reviewer — a closed loop, not a terminal report — until the verdict is CONFORMANT or the operator stops the loop.
3. Never apply a reviewer's finding inline, and never let this skill's own account of what it generated substitute for the reviewer's reading of the files.

## Boundaries

- A single artifact → the owning individual skill
- Custom components in C++/Python → out of scope; no owning skill yet
- A Home Assistant integration, card, or automation → the sibling `ha-*-solution` skills
- Compile, flash, OTA rollout → out of scope in every mode
- The review verdict itself → the two reviewer agents, independently and read-only

## Nested approval gates

When this skill dispatches a skill that itself asks for confirmation, the approval applies at the highest level that presented a plan: once the operator approves this skill's artifact plan, the dispatched skills execute their slice under it and only surface a fresh gate when their own decomposition materially deviates (a new artifact, a changed dependency order, a package interface change that affects other devices). Re-asking for an identical, already-approved step is noise, not diligence.

## Resumability

Re-invoking this skill with the same requirement resumes per `spec/claude/resumable-work/`: the checkpoint under `.resume/<skill-name>/` records the approved plan and per-step dispatch status, so an interrupted orchestration continues at the first incomplete step instead of re-planning from scratch.
