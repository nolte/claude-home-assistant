# Skill: `ha-pixoo-animation-author`

Status: draft

## Context

Animation on the Pixoo 64 is phase mathematics, not video: a components page whose positions are `position = f(phase)` and whose colors are `color = f(phase)` inside the spec's ramps, driven by an automation that advances the phase — governed by `spec/ha/pixoo-pixel-art-animation/en.md`. Hand-built animations drift out of the ramp discipline or forget the driving automation entirely. This skill owns the motion slice of the device-specific Pixoo family.

## Scope

One described motion/effect per invocation, producing the phase-driven components page plus the driving automation. Static art is `ha-pixoo-pixel-art-author`'s; page kinds without motion are `ha-pixoo-page-author`'s.

## Goals

- Motion expressed as explicit phase functions, never frame-by-frame copies
- The driving automation ships with the page — an animation without its driver is an incomplete artifact
- Ramp-conformant color animation; coordinates stay inside 64×64 across the whole phase range

## Non-Goals

- Static art, non-animated pages, multi-artifact plans (`ha-pixoo-solution`), device deploy

## Requirements

- **MUST** read `spec/ha/pixoo-pixel-art-animation/en.md` before composing and express motion as `f(phase)` functions
- **MUST** verify coordinate bounds over the entire phase range, not just phase 0
- **MUST** emit both artifacts — the components page and the phase-advancing automation — and name the target device entity
- **SHOULD** guard the automation against the device being unavailable

## Acceptance Criteria

- [ ] A run yields the page plus its driving automation, both schema-valid
- [ ] Bounds hold across the full phase range; colors stay inside the ramps
- [ ] Static or page-kind requests route to the owning sibling
