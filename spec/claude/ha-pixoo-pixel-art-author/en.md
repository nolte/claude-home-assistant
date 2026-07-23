# Skill: `ha-pixoo-pixel-art-author`

Status: draft

## Context

Detailed 64×64 pixel art for the Pixoo 64 has two legitimate build paths per `spec/ha/pixoo-pixel-art/en.md`: a procedural component list (rectangle/templatable, per-pixel, optionally data-driven) rendered by the integration, or a precise build plan for an exactly-64×64 PNG. Both stand or fall with palette discipline, silhouette-first construction, and coordinate exactness. This skill owns the static-art slice of the device-specific Pixoo family.

## Scope

One subject per invocation, one chosen build path, output either the component list or the PNG build plan. Motion belongs to `ha-pixoo-animation-author`; page embedding to `ha-pixoo-page-author`.

## Goals

- Deliberate path choice (procedural versus PNG plan) with stated criteria per the grounding spec
- Silhouette-first construction with the spec's palette ramps; no muddy anti-aliasing artifacts
- Data-driven art stays templatable where the subject calls for it

## Non-Goals

- Animation (`ha-pixoo-animation-author`), page composition (`ha-pixoo-page-author`), plans spanning several artifacts (`ha-pixoo-solution`), rendering/uploading to the device

## Requirements

- **MUST** read `spec/ha/pixoo-pixel-art/en.md` before drawing and pick the build path with a stated rationale
- **MUST** keep every coordinate inside 64×64 and every color inside the spec's ramp discipline
- **MUST**, on the procedural path, emit components the `divoom_pixoo` schema accepts; on the PNG path, a plan precise enough to reproduce the art pixel-exactly
- **SHOULD** propose the templatable variant when the subject is state-driven

## Acceptance Criteria

- [ ] A run yields exactly one artifact (component list or PNG plan) with the path rationale
- [ ] Palette and coordinate checks pass against the grounding spec
- [ ] Motion or page-embedding requests route to the owning sibling
