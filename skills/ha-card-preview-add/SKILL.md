---
name: ha-card-preview-add
description: "Ensures an existing custom Lovelace card's preview is completely and correctly implemented, conforming to spec/ha/lovelace-card-preview — the card-picker gallery preview (preview flag plus a getStubConfig rendering a real non-error tile), the editor live preview (deterministic from setConfig/hass, re-rendered on config-changed), reading the preview element property (and legacy editMode), and preview correctness (no real service calls while previewing, a graceful placeholder over a thrown render). Completes the missing preview pieces on an existing card and validates them; produces a CONFORMANT / NEEDS-WORK report. Activate on \"make my card show a preview in the card picker\", \"the card preview is broken / empty\", or equivalent German requests. Do not activate for scaffolding a new card (ha-lovelace-card-scaffold), the config editor itself (ha-card-editor-add), card layout/sizing (ha/lovelace-layout-antipatterns), or deploying to a live HA instance."
tags: [home-assistant, custom-integration, lovelace, preview]
phase: design
summary: "Completes and validates the preview of an existing custom Lovelace card — picker gallery preview, editor live preview, and preview-mode correctness."
summary_de: "Vervollständigt und validiert die Vorschau einer bestehenden Custom-Lovelace-Card — Picker-Galerie-Vorschau, Editor-Live-Vorschau und Vorschau-Korrektheit."
use_when:
  - "you want your card to show a preview in the card picker"
  - "the card preview is broken or empty and you want it fixed"
  - "you want to ensure the card preview is implemented correctly"
dont_use_when:
  - situation: "You are scaffolding a brand-new card"
    alternative: ha-lovelace-card-scaffold
  - situation: "You want to build the card's graphical config editor"
    alternative: ha-card-editor-add
see_also:
  - ha-lovelace-card-scaffold
  - ha-card-editor-add
  - ha-card-features-add
---

# HA Card Preview Add

Spec: `spec/claude/ha-card-preview-add/en.md` (EN canonical) / `spec/claude/ha-card-preview-add/de.md` (DE translation).

This skill makes an existing custom card's **preview** complete and correct, per `spec/ha/lovelace-card-preview/en.md`. It completes the missing preview pieces (picker preview, editor live preview, the `preview` property guard, preview correctness) and validates them — it does not scaffold the card (`ha-lovelace-card-scaffold`) or build the editor (`ha-card-editor-add`).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the card and reads back the `window.customCards` change, the `getStubConfig`, the `preview`-property guard, and a conformance report; a skill keeps this on the visible command surface, like the sibling `ha-card-editor-add`.
- **Mid-flow interactivity** — whether a live picker preview is wanted (`preview: true`), the demo entity/placeholder for the stub config, and which side-effects to guard are per-run dialogues the user confirms.
- **Bounded, inline generation** — the customCards flag, the `getStubConfig`, and the preview guards fit inline; no isolated agent context is needed.
- Counter-dimension considered: the audit-then-complete loop could be an agent, but the demo-entity choice and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill to ensure an **existing** custom card previews completely and correctly — its card-picker gallery tile renders a real live preview, its editor live preview tracks the config, and it behaves correctly while being previewed.

## When NOT to activate

- scaffolding a brand-new card → `ha-lovelace-card-scaffold`
- building the graphical config editor (`getConfigElement` / `getConfigForm`) → `ha-card-editor-add`
- card layout / sizing / grid behaviour → `ha/lovelace-layout-antipatterns`
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **Read `spec/ha/lovelace-card-preview/en.md` first.** Do not generate from memory. Honour its evidence tiers — `[doc]` / `[src]` / `[policy]` — and never present a source-verified or policy rule as a documented HA fact.
2. **Picker preview flag.** Set `preview: true` on the card's `window.customCards` entry when a live picker preview is intended; `[src]` without it the tile shows only `description`. Keep `description` set as the fallback text.
3. **Valid `getStubConfig`.** Ensure a `getStubConfig` returns a config the card's `setConfig` accepts, so the `preview: true` tile renders a real, non-error preview (detail per `ha/lovelace-card-editor`; delegate the editor to `ha-card-editor-add`).
4. **Editor live preview is deterministic.** The render must follow `setConfig`/`hass` so the editor live preview reflects each `config-changed`; never cache first-render state that ignores a later `setConfig`.
5. **Read the `preview` property.** Read the boolean `preview` property HA sets on the card element (editor-preview context), and the legacy `editMode` alias for older frontends; `[src]` the picker tile does not set `preview`, so do not depend on it there.
6. **Preview correctness.** `[policy]` **Never** fire a real service call, action, or side-effect while `preview` (or `editMode`) is `true`; render representative content; render a graceful placeholder (never throw) for a missing entity or incomplete config.
7. **Do not size the picker tile via `getCardSize`/`getGridOptions`.** `[src]` the gallery tile is CSS-governed; those methods govern the editor preview and the real dashboard.
8. **Name per `spec/ha/naming-conventions/en.md`** and **verify HA internals against the official docs** (see `spec/ha/upstream-docs-verification/en.md`).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; the card lives under `custom_components/<domain>/www/<card>.js` |
| `card_file` | no | discovered | the card JS module to complete the preview for |
| `picker_preview` | no | `true` | whether a live card-picker preview is wanted (`preview: true`) |
| `stub_entity` | no | asked when relevant | a stable demo/representative entity (or placeholder) for `getStubConfig` |

## Pre-flight (in order — abort on first failure)

1. `git -C <target_dir> rev-parse --is-inside-work-tree`.
2. Locate the card JS module and read its `window.customCards` push, `setConfig`, render, and any `getStubConfig`.
3. Read `ha/lovelace-card-preview`.

## Workflow

### 1) Audit the current preview

Report, per `ha/lovelace-card-preview`: is `preview` set on `window.customCards`? Is there a valid `getStubConfig`? Does the render read the `preview`/`editMode` property? Are there un-guarded `callService`/action calls that would fire during preview? Does an incomplete/missing-entity config throw?

### 2) Complete the missing pieces

- `window.customCards` — set `preview: true` (when `picker_preview`) and keep `description`
- `getStubConfig` — add or fix so it returns a `setConfig`-valid config (a representative `stub_entity` or placeholder)
- the render — guard real service calls/actions behind a `!this.preview && !this.editMode` check; add a graceful placeholder for a missing entity / incomplete config instead of throwing; keep the render deterministic from `setConfig`/`hass`

### 3) Validate & report

Validate offline (`preview` flag present when intended; `getStubConfig` returns a `setConfig`-valid config; the `preview`/`editMode` guard wraps every side-effect; a missing-entity/incomplete config renders a placeholder, not a throw) and emit a CONFORMANT / NEEDS-WORK report keyed to the `ha/lovelace-card-preview` acceptance criteria, plus the changed file paths and the quality-scale marker (**not part of the HA quality scale**).

## Boundaries

- Scaffolding a new card → `ha-lovelace-card-scaffold`
- The config editor (`getConfigElement` / `getConfigForm`) and `getStubConfig` field detail → `ha-card-editor-add` / `ha/lovelace-card-editor`
- Card sizing / layout → `ha/lovelace-layout-antipatterns`
