---
name: ha-pixoo-page-author
description: Author one Divoom Pixoo 64 page as spec-conformant YAML for the divoom_pixoo integration's pages_data list — a components page (text/image/rectangle/templatable), a special page (PV/progress_bar/fuel), or a native page (channel/clock/gif/visualizer) — from a described information requirement. Lays out the 64×64 canvas, wires entity-state Jinja templates onto the display, picks fonts/colors/alignment, applies the static pixel-art rules for embedded graphics, and returns a conformance report. Activate on "show my heat-pump power on the Pixoo", "make a Pixoo page with the dishwasher progress", "put the weather and temperature on the Divoom", "zeig mir X auf dem Pixoo als Seite", "bau eine Pixoo-Page für…". Do not activate for detailed pixel-art graphics (ha-pixoo-pixel-art-author), animated/moving displays (ha-pixoo-animation-author), device setup/config flow, or deploying to a live HA instance.
tags: [home-assistant, divoom-pixoo, display, yaml]
---

# HA Pixoo Page Author

Grounding specs: [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md) (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/en.md), and [`ha/pixoo-pixel-art`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art/de.md) for embedded graphics.

## Why this is a skill, not an agent

- **Human-visible authoring surface** — the user describes the information they want and reads back the generated `pages_data` YAML and the conformance report; a skill keeps that on the visible command surface, like the sibling `ha-automation-author`.
- **Mid-flow interactivity** — page-type confirmation (components vs. special vs. native) and the layout/entity assumptions are per-run dialogues the user must approve before generation.
- **Orchestrator-leaning** — dispatched by `ha-pixoo-solution`, and may itself defer a graphic slot to `ha-pixoo-pixel-art-author`; the skill-orchestrates default keeps the entry point in skill form.
- Counter-dimension considered: the draft→validate loop could be an agent, but the page-type decision and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill to author **one** Pixoo `pages_data` page from an information requirement: a `components` page, a special page (`PV` / `progress_bar` / `fuel`), or a native page (`channel` / `clock` / `gif` / `visualizer`).

## When NOT to activate

- a detailed pixel-art graphic (shading/contours, illustration, icon) → `ha-pixoo-pixel-art-author`
- a moving/animated display → `ha-pixoo-animation-author`
- device setup, discovery, config flow, service reference → using the integration per [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md), not authoring
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **One page, one type, one run.** No multi-page batches.
2. **Requirement is mandatory.** Without a described information need there is no generation; optional fields fall back to documented defaults, stated in the output.
3. **Read the spec first.** Before generating, read [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md) (and [`ha/pixoo-pixel-art`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/pixoo-pixel-art/de.md) for embedded graphics); do not generate from memory.
4. **64×64 grid discipline.** All positions use the top-left origin grid 0…63; content beyond is clipped. Lay out for high contrast and readability per `ha/pixoo-pixel-art`.
5. **Templating + guards.** Entity states reach the display via Jinja in `content`/`color`/`enabled`/image fields; guard `unavailable`/`unknown` (`has_value()`, `float(default)`) so a dead sensor never renders garbage or a false value.
6. **Config-only vs. service.** `enabled`, `duration`, and component `variables` apply only in the `pages_data` config — never in `show_message`. State which context the page targets.
7. **Image-path safety.** `image_path` points to a stable path (e.g. `/config/img/…`), never the integration's own `/config/custom_components/divoom_pixoo/img/` folder (overwritten on update). Text renders upper-cased — account for it.
8. **Defer graphics, don't fake them.** A detailed illustration/icon slot is delegated to `ha-pixoo-pixel-art-author`, not hand-drawn inline here.

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `requirement` | yes | — | The information to display, in prose |
| `page_type` | no | inferred | `components` / `PV` / `progress_bar` / `fuel` / `channel` / `clock` / `gif` / `visualizer` |
| `entities` | no | asked when needed | source entities for the templated fields |
| `target_dir` | no | working dir | repo / HA config root |
| `device_entity` | no | noted | the `sensor.<name>_current_page` target (for `show_message` examples) |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `requirement` present and non-empty. If not, ask; do not generate.
2. Resolve `page_type` (infer + confirm).
3. Read the matching spec section(s).
4. Confirm the source entities exist / are named, or mark them as placeholders to fill.

## Workflow

### 1) Resolve and confirm

State the resolved `page_type`, the intended layout (which field at which position), and every assumed default in one paragraph. Wait for confirmation.

### 2) Generate

Write the page per the spec's MUST rules:

| Type | Load-bearing rules |
|---|---|
| `components` | each component has `type` + `position`; `text` sets `content` (templated, upper-cased) with deliberate `font`/`color`/`align`; `image` uses exactly one source; `rectangle` for bars/areas; defer rich graphics to `ha-pixoo-pixel-art-author` |
| `PV` / `progress_bar` / `fuel` | fill the spec's required fields with guarded templates; choose colors within a coherent palette |
| `channel` / `clock` / `visualizer` | provide the device/app `id`; note that catalogs are device-specific (`CurClockId` debug method) |
| `gif` | reference a GIF of exactly 16/32/64 px via `gif_url` |

### 3) Validate and report

Validate offline (YAML lint; mentally render templates against `unavailable`/`unknown` sources; confirm positions fit 64×64). Emit a CONFORMANT / NEEDS-WORK report keyed to the spec's acceptance criteria, plus the written file/path and assumed defaults.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Detailed pixel-art graphics → `ha-pixoo-pixel-art-author`
- Animated displays → `ha-pixoo-animation-author`
- Device/integration setup & services → use per [`ha/divoom-pixoo`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/divoom-pixoo/de.md)
- Multi-artifact requirement → `ha-pixoo-solution`
- Deploy to live HA → out of scope
