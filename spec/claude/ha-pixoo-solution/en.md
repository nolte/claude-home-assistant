# Skill: `ha-pixoo-solution`

Status: draft

## Context

The Divoom Pixoo skill family each produces **one** artifact from a narrowly scoped intent: `ha-pixoo-page-author` builds a `pages_data` page (the info layout and canvas), `ha-pixoo-pixel-art-author` fills a page slot with a detailed pixel-art graphic (shading/contours, procedural components or a 64×64 image plan), and `ha-pixoo-animation-author` adds the temporal dimension (an animated `components` page plus the driving automation). Real-world Pixoo requirements are rarely a single artifact: "an animated rain page driven by the weather entity with a battery icon" is a chain of page → pixel-art → animation, where each add-on builds on the page generated before it. A user who doesn't know the skills would have to do that decomposition themselves — which artifact, which order, which page structure and target entity feed the next step. That mapping burden is exactly what the user should not have to carry.

This skill is the **front door and upstream planning/dispatch layer** of the Pixoo cluster: it takes a fuzzy Pixoo display requirement, decomposes it into the minimal combination of artifacts, fixes the dependency order, confirms the plan with the user, and then dispatches the owning skills one after another, threading the identities (the `pages_data` page structure, component positions, the chosen palette/ramps, and the target `sensor.<name>_current_page` entity) of earlier steps into the inputs of later ones. It generates **no** artifact itself — generation and spec conformance stay with the individual skills. Device setup, discovery, config flow, and services are **using** the existing `divoom_pixoo` integration (per `ha/divoom-pixoo`), not authoring, and stay out of scope.

## Scope

Planning and orchestration across the Divoom Pixoo skill family: `ha-pixoo-page-author`, `ha-pixoo-pixel-art-author`, and `ha-pixoo-animation-author`. One requirement per run → one artifact plan → N dispatched owning calls → one aggregate report. The skill decides the *combination* (which artifacts, which type per artifact, which order, which wiring), not the content of any single artifact. Grounding specs for the domain contract: `ha/divoom-pixoo`, `ha/pixoo-pixel-art`, `ha/pixoo-pixel-art-animation`.

## Goals

- Derive the right *combination* of artifacts from a prose Pixoo requirement, without the user knowing the Pixoo skill landscape
- Produce a processable artifact plan in dependency order (per entry: artifact, type, owning skill, dependency, purpose) and get it confirmed before any generation
- Dispatch the individual skills in correct order and thread the identities (`pages_data` page structure, component positions, palette/ramps, target `sensor.<name>_current_page` entity) of earlier artifacts into the inputs of later ones
- Distinguish authoring a display from **using** the integration (device setup, IP/`scan_interval`, entity wiring) and keep the latter out of scope, pointing at `ha/divoom-pixoo`
- Deliver an aggregate report naming every produced artifact and its wiring

## Non-Goals

- Generating a single artifact and its spec conformance — that stays with `ha-pixoo-page-author`, `ha-pixoo-pixel-art-author`, `ha-pixoo-animation-author`
- Device/integration setup, discovery, config flow, IP/`scan_interval` changes, or entity wiring — that is **using** the existing `divoom_pixoo` integration per `ha/divoom-pixoo`, not authoring
- Deploying to a running HA instance or writing the generated config into a live HA config — generation only
- Its own validation or conformance logic — each dispatched skill validates its own artifact; this skill only aggregates the reports

## Requirements

### Activation triggers

- **MUST** activate on composite, result-oriented Pixoo requests where the user describes the display, not the artifact:
  - "build me a Pixoo display for my heat-pump power and a battery icon"
  - "an animated rain page driven by the weather entity"
  - "a progress page for the dishwasher plus a buzzer alert"
  - "baue mir eine Pixoo-Anzeige für…", "zeig den Status von X auf dem Divoom"
- **SHOULD** not activate when the requirement is clearly a single Pixoo artifact (one page, one pixel-art graphic, one animation — the owning individual skill applies directly); when in doubt, this skill plans and proposes a single-artifact plan

### Inputs

- **MUST** capture: `requirement` (prose, the desired Pixoo display result)
- **MAY** capture: `target_dir` (repo / HA config root, passed through to dispatched skills), `device_entity` (the target `sensor.<name>_current_page` entity, the service target per `ha/divoom-pixoo`), and `palette` (a shared palette/ramp set to keep pages coherent, per `ha/pixoo-pixel-art`)

### Pre-flight

- **MUST** check `requirement` is non-empty; on underspecification ask 1–3 targeted questions (which info, static vs. animated, target device entity, palette) before planning
- **MUST** distinguish an authoring requirement from mere integration setup; when the request is device setup / config flow / `scan_interval` / entity wiring, name it as **using** the existing integration per `ha/divoom-pixoo` and stop instead of planning artifacts

### Decomposition heuristic (requirement → artifact type → skill)

- **MUST** resolve each owning skill at runtime by matching the requirement against the live Pixoo `ha-pixoo-*` skill inventory (each candidate's stated responsibility), not from a frozen name list — the mappings below are an illustrative anchor, re-resolved each run, so a skill added to or removed from the family is dispatchable without editing the orchestrator (mirroring `issue-orchestrate`). When running inside the plugin source tree, `Glob skills/ha-pixoo-*/SKILL.md` and read each `description:`; if the live inventory genuinely cannot be enumerated, fall back to the anchor table and note the degraded resolution
- **MUST** map an info layout (text/data, special page PV/progress_bar/fuel, native channel/clock/gif/visualizer) to a `pages_data` page via `ha-pixoo-page-author` — step 1 whenever a page is needed, as it owns the canvas and target entity
- **MUST** map a detailed pixel-art graphic (icon, illustration with shading/contours, embedded in a page) to `ha-pixoo-pixel-art-author`, depending on the page whose slot it fills
- **MUST** map a moving display (motion, color animation, ticking/pulsing) to `ha-pixoo-animation-author` (animated `components` page plus the driving automation), depending on the page it animates
- **MUST** keep artifacts minimal — a plain info page does not need a pixel-art or animation add-on

### Plan & dispatch

- **MUST** present an artifact plan as a table in dependency order before any generation: per entry `#`, artifact, type, owning skill, dependency (`depends-on`), purpose — and wait for explicit confirmation
- **MUST NOT** generate an artifact inline itself; every generation runs through the owning individual skill
- **MUST** dispatch the skills in dependency order — page → pixel-art → animation: the page defines the canvas and target entity, pixel-art fills graphic slots within it, animation wraps the result in a phase-driven frame loop — and thread the identities (`pages_data` page structure, component positions, palette/ramps, target `sensor.<name>_current_page` entity) into the inputs of dependent steps
- **MUST** stop and report when a dispatched skill returns a NEEDS-WORK report, rather than building on an unfinished predecessor artifact
- **MUST** keep all identifiers consistent across artifacts and verify HA internals against the official docs (`ha/upstream-docs-verification`); for the integration's own contract read the grounding specs (`ha/divoom-pixoo`, `ha/pixoo-pixel-art`, `ha/pixoo-pixel-art-animation`), not memory

### Aggregate report

- **MUST** list, at the end, every produced artifact, its type, and the wiring (which pixel-art fills which page slot; which animation drives which page; the target entity)
- **MUST** relay the aggregated CONFORMANT / NEEDS-WORK reports of the individual skills without re-judging them

### Prohibitions

- **MUST NOT** orchestrate more than one requirement per run
- **MUST NOT** execute a plan without user confirmation
- **MUST NOT** fold device/integration setup (config flow, `scan_interval`, entity wiring) into the authoring flow — that is **using** the integration
- **MUST NOT** deploy to a running HA instance or modify the device or its config entry

## Acceptance criteria

- [ ] Owning skills are resolved against the live Pixoo `ha-pixoo-*` inventory each run (a newly added or renamed family skill is dispatchable without editing the orchestrator); the decomposition mappings are illustrative, not a frozen closed set
- [ ] Skill asks for missing essentials (which info, static vs. animated, target entity, palette) before planning
- [ ] Skill presents an artifact plan in dependency order and waits for confirmation
- [ ] Skill dispatches the owning individual skills instead of generating itself
- [ ] Identities (page structure, component positions, palette/ramps, target `sensor.<name>_current_page` entity) of earlier artifacts are threaded into the inputs of dependent steps
- [ ] Authoring is distinguished from integration setup; a device-setup request is named as **using** the integration per `ha/divoom-pixoo` and not planned as artifacts
- [ ] Stops on a NEEDS-WORK predecessor instead of building further
- [ ] Aggregate report lists every artifact and the wiring and relays the individual reports

## Open questions

- **Agent vs. skill dispatch**: should the individual steps run as skills (visible, sequential) or via a generation agent (isolated, parallel)? Currently skill dispatch, because the plan confirmation and the identity threading (page structure → pixel-art slot → animation phase, target entity) should stay visible in the user context.
- **Palette coherence**: should the skill enforce a single shared palette across all pages of a multi-page requirement, or leave it per artifact to the owning skill? Currently a shared palette is captured up front and threaded, but not hard-enforced.
- **Existing-config awareness**: should the skill read the existing `pages_data` / device configuration to catch page-index or entity collisions early? Currently named by the user.
