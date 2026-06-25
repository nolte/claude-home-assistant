---
name: ha-pixoo-animation-author
description: Author an animated 64×64 display for the Divoom Pixoo 64 from a described motion/effect, conforming to the pixoo-pixel-art-animation spec — a phase-driven components page (motion as position=f(phase), color animation as color=f(phase) within the ramps) plus the driving automation, or a pre-rendered GIF embedding. Builds the phase/time base, integer-grid stepwise motion with a seamless loop, palette-cycling/value-pulsing/hue-shift color animation, and a crash-safe frame driver (short duration vs. an update_page loop), accounting for the single-frame-push ~1 fps ceiling. Returns the artifacts plus a conformance report. Activate on "animate a bouncing icon on the Pixoo", "make the Pixoo pulse red when X", "scrolling/moving Pixoo display for…", "lass das Pixoo-Icon wandern", "animierte Pixoo-Page für…". Do not activate for a static page (ha-pixoo-page-author), a still graphic (ha-pixoo-pixel-art-author), device setup, or deploying to a live HA instance.
tags: [home-assistant, divoom-pixoo, animation, yaml]
---

# HA Pixoo Animation Author

Grounding spec: [`ha/pixoo-pixel-art-animation`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art-animation/de.md) (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art-animation/en.md); image craft in [`ha/pixoo-pixel-art`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art/de.md), delivery in [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md).

## Why this is a skill, not an agent

- **Human-visible authoring surface** — the user describes the motion/effect and reads back the animated page plus its driving automation and the conformance report; a skill keeps that on the visible command surface, like the sibling `ha-automation-author`.
- **Mid-flow interactivity** — the frame-driver decision (short `duration` vs. `update_page` loop) and its crash-safe interval, the phase source, and the motion/color model are per-run dialogues the user must approve before generation.
- **Orchestrator-leaning** — dispatched by `ha-pixoo-solution`, and builds on a page/graphic produced by the sibling authors; the skill-orchestrates default keeps the entry point in skill form.
- Counter-dimension considered: the frame-by-frame iteration could run as an agent, but the driver/phase decisions and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill to author **one** animated Pixoo display from a described motion or color effect — procedural (phase-driven `components`) or a pre-rendered GIF embedding.

## When NOT to activate

- a static information page → `ha-pixoo-page-author`
- a single still graphic → `ha-pixoo-pixel-art-author`
- device setup, services, page-type reference → use the integration per [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md)
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **One animation, one model, one run.** No batches.
2. **Motion/effect is mandatory.** Without a described animation there is no generation; optional fields fall back to documented defaults, stated in the output.
3. **Read the spec first.** Before generating, read [`ha/pixoo-pixel-art-animation`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art-animation/de.md); do not generate from memory.
4. **Single-frame-push model.** Each frame is a full page re-render pushing one buffer — there is no multi-frame transmission. Treat the practical ceiling as ~1 fps via `duration` rotation; higher needs an `update_page` loop.
5. **Crash-safe driver.** Choose a frame driver explicitly (self-driving short `duration`, or an `update_page` loop) and **never** spam `update_page` — bound the interval; document the chosen cadence.
6. **Phase discipline.** Drive frame selection from a monotonic phase (`now()`, a `timer`, or a `counter`), looped modulo the frame count for a seamless cycle. Motion is `position = f(phase)` on the integer 64×64 grid (no sub-pixel); color animation is `color = f(phase)` **within** the `ha/pixoo-pixel-art` ramps (cycling/pulsing/hue-shift, discrete steps).
7. **Coherent, flicker-free frames.** Every frame is a valid pixel-art image (stable light direction); adjacent frames differ only gradually; avoid full-area high-contrast flicker; close the loop seamlessly.
8. **Procedural vs. GIF.** Procedural per-pixel frames use a `templatable` component returning a phase-computed list; a pre-rendered GIF is exactly 16/32/64 px via `page_type: gif`. Recommend verifying frame rate, flicker, motion, and loop on the real device.

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `motion` | yes | — | The desired animation/effect, in prose |
| `model` | no | inferred | `procedural` (phase-driven components) or `gif` (pre-rendered embedding) |
| `driver` | no | `duration` | `duration` (self-driving) or `update_page` (looped automation) |
| `frame_interval` | no | 1 s | per-frame hold; crash-safe lower bound for `update_page` |
| `phase_source` | no | `now()` | `now()` / a `timer` / a `counter` |
| `data_driven` | no | false | whether the animation reacts to entity state |
| `target_dir` | no | working dir | repo / HA config root |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `motion` present and non-empty. If not, ask; do not generate.
2. Resolve `model` + `driver` + phase source (infer + confirm); confirm the frame interval is crash-safe.
3. Read the `ha/pixoo-pixel-art-animation` spec (and image craft / delivery sections).

## Workflow

### 1) Resolve and confirm

State the resolved `model`, `driver` + cadence, phase source, and the motion/color mapping in one paragraph. Wait for confirmation.

### 2) Generate

- **procedural**: emit the animated `components` page (positions/colors as functions of the phase, per-pixel via `templatable` when needed) **plus** the driving artifact — either a short `duration` on the page, or an `update_page` loop automation/script with a bounded interval.
- **gif**: emit the `page_type: gif` embedding (exactly 16/32/64 px) and note the GIF is authored externally.

### 3) Validate and report

Check against the spec: monotonic phase + modulo loop; integer-grid stepwise motion with seamless wrap; color animation within ramps; no fatiguing flicker; crash-safe driver cadence; each frame a valid pixel-art image. Emit a CONFORMANT / NEEDS-WORK report keyed to the spec's acceptance criteria, plus the artifact paths and assumed defaults.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Static page → `ha-pixoo-page-author`
- Still graphic → `ha-pixoo-pixel-art-author`
- Device/integration mechanics → [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md)
- Multi-artifact requirement → `ha-pixoo-solution`
- Deploy to live HA → out of scope
