# Skill: `ha-pixoo-page-author`

Status: draft

## Context

The Divoom Pixoo 64 renders what the `divoom_pixoo` integration's `pages_data` list declares — components pages (text/image/rectangle/templatable), special pages (PV/progress_bar/fuel), and native pages (channel/clock/gif/visualizer), each with its own key schema and 64×64 coordinate discipline per `spec/ha/divoom-pixoo/en.md`. Hand-writing these pages invites off-by-one layout errors and schema drift. This skill is the single-page authoring entry of the device-specific Pixoo family (an optional family, not a general HA domain).

## Scope

Exactly one page per invocation, as spec-conformant YAML for the `pages_data` list, from a described information need. Static pixel-art content is `ha-pixoo-pixel-art-author`'s; motion is `ha-pixoo-animation-author`'s; multi-artifact combinations route through `ha-pixoo-solution`.

## Goals

- One discoverable entry for "show X on the Pixoo" that picks the right page kind (components/special/native) deliberately
- Template-driven dynamic values wired against real entity states, guarded for unavailable states
- 64×64 layout discipline: verified coordinates, no clipped text, palette per the grounding spec

## Non-Goals

- Detailed pixel art (`ha-pixoo-pixel-art-author`), animation (`ha-pixoo-animation-author`), multi-page plans (`ha-pixoo-solution`), device deploy

## Requirements

- **MUST** read `spec/ha/divoom-pixoo/en.md` before composing and choose the page kind with a stated rationale
- **MUST** verify every page key against the integration's documented schema; unknown keys are findings, never output
- **MUST** guard every template against unavailable/unknown states and keep coordinates inside 64×64
- **MUST** emit exactly one page entry, ready to paste into `pages_data`, and name the target device entity
- **SHOULD** hand off to the sibling skills when the request is actually art, motion, or a combination

## Acceptance Criteria

- [ ] A run yields one schema-valid page entry with kind rationale and guarded templates
- [ ] Coordinate/palette checks pass against the grounding spec
- [ ] Art/motion/combination requests are routed to the owning sibling instead of half-served here
