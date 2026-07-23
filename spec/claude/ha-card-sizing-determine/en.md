# Skill: `ha-card-sizing-determine`

Status: draft

## Context

Sizing a custom Lovelace card or panel is a determination problem before it is an implementation problem: the correct `getGridOptions()` (sections view) and `getCardSize()` (masonry/panel/stacks) declaration depends on whether the content is deterministic or content-dependent, on the `rows: "auto"` CSS preconditions, and on edit-mode overlay behaviour — all governed by `spec/ha/card-panel-sizing/en.md`. Getting it wrong shows up as clipped cards or overlapping edit-mode chrome. This skill isolates the determination step so the sizing decision is explicit and hand-off-able instead of buried inside a scaffold.

## Scope

One existing card or panel per invocation. The skill classifies, verifies preconditions, and produces the size declaration plus a hand-off: inline patch of the two callbacks, or dispatch to the owning implementation specialist resolved from the live skill inventory.

## Goals

- Deterministic classification: content-dependent (`rows: "auto"` + `min_columns`) versus deterministic (numeric `rows` + `min_rows`)
- Verified `rows: "auto"` CSS preconditions before that variant is ever recommended
- Edit-mode overlay overlap treated as a sizing defect with a concrete fix, not cosmetics
- Explicit analyse-versus-apply boundary: determination here, patching in the hand-off

## Non-Goals

- Scaffolding cards or panels (`ha-lovelace-card-scaffold`, `ha-panel-add`/`ha-panel-author`), feature rows (`ha-card-features-add`), full frontend solutions (`ha-lovelace-solution`), live-instance work

## Requirements

- **MUST** read `spec/ha/card-panel-sizing/en.md` and the target source before classifying; never size from memory
- **MUST** verify the `rows: "auto"` CSS preconditions and refuse that variant when they fail, naming the failing precondition
- **MUST** produce both callbacks' declarations (sections and masonry paths) and state the classification rationale
- **MUST** keep the analyse-to-hand-off boundary: option (a) inline patch of exactly the two callbacks, option (b) dispatch to the specialist resolved from the live inventory
- **SHOULD** flag edit-mode overlap it detects as a sizing defect with the spec-anchored fix

## Acceptance Criteria

- [ ] A run on a content-dependent card yields `rows: "auto"` + `min_columns` with verified preconditions, or an explicit refusal naming the failing one
- [ ] A run on a deterministic card yields numeric `rows` + `min_rows` consistent with `getCardSize()`
- [ ] The hand-off names either the inline patch surface or a resolvable specialist
