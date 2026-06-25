---
name: ha-pixoo-pixel-art-author
description: Author detailed 64×64 pixel art for the Divoom Pixoo 64 from a described subject, conforming to the pixoo-pixel-art spec — either as a procedural component list (rectangle/templatable, per-pixel, optionally data-driven) or as a precise build plan for an exactly-64×64 PNG. Enforces a limited ramp-based palette, hue shifting, selective outlining (interior vs. exterior contours), light-source-consistent shading with terminator edges, dosed anti-aliasing and dithering, and LED-matrix readability — explicitly addressing shading and contours. Returns the artifact plus a conformance report. Activate on "draw a battery icon for the Pixoo", "make pixel art of a sun for the Divoom", "design a 64×64 plant graphic with shading", "zeichne ein Pixel-Art-Icon für das Pixoo", "entwirf eine 64×64-Grafik mit Schattierung und Konturen". Do not activate for whole info-page layout (ha-pixoo-page-author), animation/motion (ha-pixoo-animation-author), device setup, or deploying to a live HA instance.
tags: [home-assistant, divoom-pixoo, pixel-art, yaml]
---

# HA Pixoo Pixel Art Author

Grounding spec: [`ha/pixoo-pixel-art`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art/de.md) (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art/en.md); delivery mechanics in [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md).

## Why this is a skill, not an agent

- **Human-visible authoring surface** — the user describes a subject and reads back the pixel-art (component YAML or image build plan) and the conformance report; a skill keeps that on the visible command surface, like the sibling `ha-automation-author`.
- **Mid-flow interactivity** — the delivery decision (procedural components vs. PNG build plan), palette choice, and light-direction assumption are per-run dialogues the user must approve before generation.
- **Orchestrator-leaning** — dispatched by `ha-pixoo-solution` or `ha-pixoo-page-author` to fill a graphic slot; the skill-orchestrates default keeps the entry point in skill form.
- Counter-dimension considered: the iterative pixel work could run as an agent, but the delivery/palette decisions and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill to author **one** detailed 64×64 pixel-art graphic — an icon, illustration, or symbol — for the Pixoo, either as procedural components or as an exactly-64×64 PNG build plan.

## When NOT to activate

- a whole information page / data layout → `ha-pixoo-page-author`
- a moving/animated graphic → `ha-pixoo-animation-author`
- device setup, services, page-type reference → use the integration per [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md)
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **One graphic, one delivery form, one run.** No batches.
2. **Subject is mandatory.** Without a described subject there is no generation; optional fields fall back to documented defaults, stated in the output.
3. **Read the spec first.** Before generating, read [`ha/pixoo-pixel-art`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art/de.md); do not generate craft rules from memory.
4. **Limited ramp-based palette.** Define shading via ordered ramps (shadow→mid→light, 3–5 values); full saturation only as accents; apply hue shifting (shadows cooler, highlights warmer) consistently.
5. **Contours are selective.** Apply selective outlining (selout) — never black-outline every detail; distinguish interior vs. exterior contour; prefer a darker colored variant of the surface over pure black around light areas; remove/lighten the bottom edge of grounded objects.
6. **Shading follows one light source.** Establish a single light direction and keep it; no pillow shading; end ramps at a clear terminator edge. Use anti-aliasing and dithering **dosed**, with the LED-matrix caveats (AA pixels read as standalone at distance; verify dithering on the real device).
7. **Native 64×64.** A PNG plan targets exactly 64×64 with `nearest`/`pixel_art` resampling — never author smaller and upscale. Procedural art uses `rectangle` (`size:[1,1]` for single pixels) or a `templatable` component returning the pixel list, per [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md).
8. **Same craft on both paths.** Palette/contour/shading rules apply identically to procedural and PNG output; recommend verifying on the real device.

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `subject` | yes | — | What to depict, in prose |
| `delivery` | no | inferred | `procedural` (components) or `png_plan` (image build plan) |
| `palette` | no | derived / asked | a ramp set to reuse for coherence with sibling pages |
| `light_direction` | no | front-top | the single light source direction |
| `data_driven` | no | false | whether the procedural graphic varies by entity state (templated) |
| `target_dir` | no | working dir | repo / HA config root |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `subject` present and non-empty. If not, ask; do not generate.
2. Resolve `delivery` (infer + confirm) and the palette + light direction.
3. Read the `ha/pixoo-pixel-art` spec (and the delivery section of `ha/divoom-pixoo`).

## Workflow

### 1) Resolve and confirm

State the resolved `delivery`, palette/ramps, and light direction in one paragraph. Wait for confirmation.

### 2) Generate

- **procedural**: emit a `components` fragment — `rectangle` pixels/areas or a `templatable` component whose Jinja returns the pixel-component list (data-driven when `data_driven`). Apply the palette as named colors / `[R,G,B]`.
- **png_plan**: emit a precise build plan — canvas 64×64, the palette with hex/RGB ramps, a region-by-region description of silhouette, contours (interior/exterior), shading ramps and terminator, highlights, and any dithering — plus the embedding snippet (`image` component, `resample_mode: nearest`).

### 3) Validate and report

Check the craft against the spec: palette is limited and ramp-organized; contours selective; shading single-light with no pillow shading; AA/dithering dosed; silhouette readable by value alone. Emit a CONFORMANT / NEEDS-WORK report keyed to the spec's acceptance criteria, plus the artifact/path and assumed defaults.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Whole info page / layout → `ha-pixoo-page-author`
- Animation / motion → `ha-pixoo-animation-author`
- Device/integration mechanics → [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md)
- Multi-artifact requirement → `ha-pixoo-solution`
- Deploy to live HA → out of scope
