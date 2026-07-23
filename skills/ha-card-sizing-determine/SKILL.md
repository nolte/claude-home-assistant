---
name: ha-card-sizing-determine
description: "Determines the optimal size declaration for an existing custom Lovelace card or panel — getGridOptions() (sections) and getCardSize() (masonry/panel/stacks) — so it renders correctly across devices in view and edit mode, then hands the result to an implementation step patching both callbacks. Classifies as content-dependent (rows:\"auto\" + min_columns) or deterministic (numeric rows + min_rows:rows), verifies the rows:\"auto\" CSS preconditions, and treats edit-mode overlay overlap as a sizing defect, per spec/ha/card-panel-sizing. Activate on \"size this card correctly\", \"fix the edit-mode overlay overlap\", \"determine getGridOptions/getCardSize\", or equivalent German requests. Do not activate for scaffolding a new card (ha-lovelace-card-scaffold), a full frontend solution (ha-lovelace-solution), panels/UX (ha-panel-add/-author/-ux-audit), feature rows (ha-card-features-add), or live-instance deploy/verify (ha-integration-deploy/-verify)."
tags: [home-assistant, frontend, lovelace, sizing]
phase: design
summary: "Determines the optimal getGridOptions()/getCardSize() size declaration for an existing Lovelace card or panel and hands it to a step that patches both callbacks."
summary_de: "Bestimmt die optimale getGridOptions()/getCardSize()-Größendeklaration für eine bestehende Lovelace-Card oder ein Panel und übergibt sie einem Schritt, der beide Callbacks patcht."
use_when:
  - "you want to size an existing Lovelace card correctly"
  - "you want to fix an edit-mode overlay overlap on a card"
  - "you want to determine the right getGridOptions/getCardSize values"
dont_use_when:
  - situation: "You are scaffolding a brand-new card with its full lifecycle"
    alternative: ha-lovelace-card-scaffold
  - situation: "You are orchestrating a whole frontend solution across the card family"
    alternative: ha-lovelace-solution
  - situation: "You are adding a feature control row to a card"
    alternative: ha-card-features-add
  - situation: "You are working on panels, panel-mode views, or panel UX"
    alternative: ha-panel-ux-audit
  - situation: "You are deploying or runtime-verifying on a live HA instance"
    alternative: ha-integration-deploy
see_also:
  - ha-lovelace-card-scaffold
  - ha-lovelace-solution
  - ha-card-features-add
  - ha-card-editor-add
  - ha-card-preview-add
  - ha-panel-author
  - ha-panel-ux-audit
---

# HA Card Sizing Determine

Spec: `spec/ha/card-panel-sizing/en.md` (EN canonical) / `spec/ha/card-panel-sizing/en.md`. This skill operationalises that decision procedure; it does not restate it — read the spec for the field reference, the `.fit-rows` mechanics, the source citations, and the canonical card examples.

## Why this is a skill, not an agent

- **Mid-flow interactivity** — the content-shape classification (content-dependent vs. deterministic) and the determined declaration are approved by the user *before* the card is patched; that approval gate is the load-bearing dimension and belongs on the visible command surface.
- **Output flows back to the main conversation** — the determined `getGridOptions`/`getCardSize` values and the patch are read back inline, without a structured report boundary; the caller keeps working in the same context.
- **Bounded inline generation with a hand-off** — determination plus patching two small callbacks fits inline; where a specialist edit is warranted the skill orchestrates it (skill-orchestrates, agent-executes) rather than doing isolated heavy work itself.
- Counter-dimension considered: the source-grounded analysis could suggest an isolated agent (context-window protection), but the analysis reads one card file against a spec that is already loaded, so isolation buys nothing and the approval gate wins — skill.

## When this skill activates

Use this skill when an **existing** custom Lovelace card or panel needs its size declaration determined or corrected: it renders wrong in one view type or mode, its edit-mode overlays sit inside the content, it clips or leaves dead space, it reflows badly on tablet/mobile, or it simply lacks a considered `getGridOptions()` / `getCardSize()`. The skill determines the correct declaration and hands it to an implementation step that patches both callbacks in the target card file.

## When NOT to activate

- greenfield card scaffolding (new card file, full lifecycle) → `ha-lovelace-card-scaffold`
- orchestrating a whole frontend solution across the card family → `ha-lovelace-solution`
- panels, panel-mode views, custom views, or panel UX → `ha-panel-add` / `ha-panel-author` / `ha-panel-ux-audit`
- adding a feature control row to a card → `ha-card-features-add`
- the card lifecycle / rendering framework or the full layout-antipattern catalogue → `ha/lovelace-card-patterns` / `ha/lovelace-layout-antipatterns`
- deploying or runtime-verifying on a live HA instance → `ha-integration-deploy` / `ha-integration-verify`

## Hard rules

1. **`spec/ha/card-panel-sizing` is normative.** Derive every sizing decision from it; never assert an HA sizing fact (field names, the `rows:"auto"` semantics, the `.fit-rows` height, edit-mode overlay heights) from memory. When the spec's cited source does not cover a case, verify against the official docs and the frontend source per `ha/upstream-docs-verification` — do not guess.
2. **Classify before declaring.** Decide content-dependent vs. deterministic first; when genuinely unsure, default to `rows:"auto"` (the frontend's own `DEFAULT_GRID_SIZE`), never a guessed numeric `rows`.
3. **Both callbacks, one model.** Determine `getGridOptions()` and `getCardSize()` together and keep them consistent with each other and with the chosen model — `getGridOptions()` governs sections; `getCardSize()` governs masonry, panel, and stacks. Never determine one and leave the other at its default.
4. **Verify the `rows:"auto"` preconditions before recommending it.** Confirm the card root has no fixed/`100%` height, no clipping `overflow:hidden`, and no `position:absolute` root; a fixed inner-content height is fine. If a precondition fails, either fix the CSS as part of the hand-off or fall back to the deterministic branch — do not ship `rows:"auto"` over a root that defeats measurement.
5. **Never resolve edit-mode overlap by tuning a guessed fixed `rows`.** Overlap is a sizing defect: fix it with `rows:"auto"` (content-dependent) or a correctly computed numeric `rows` + `min_rows:rows` (deterministic).
6. **Responsive columns.** Declare a `columns` default (multiple of 3) and a `min_columns` floor; set `max_columns` when the card has an upper useful width; use `columns:"full"` only when the card genuinely spans the section.
7. **No live deploy or verify.** This skill determines and patches source only; deploying or verifying on a running HA instance is out of scope (`ha-integration-deploy` / `ha-integration-verify`).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `card_file` | yes | — | path to the existing card/panel module whose sizing is determined |
| `content_shape` | no | inferred + confirmed | content-dependent vs. deterministic; inferred from the card, confirmed with the user |
| `view_targets` | no | all | which view types matter (sections / masonry / panel / stacks); default: all |
| `column_intent` | no | derived | intended `columns` default, `min_columns`/`max_columns`, or `"full"` span |
| `handoff` | no | inline patch | `inline` (patch the two callbacks here) or dispatch an implementation specialist |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `card_file` exists and contains an existing custom card/panel (a `getGridOptions`/`getCardSize` host, not a feature or badge).
2. Read `spec/ha/card-panel-sizing`. Do not proceed from memory.
3. Read the card: its render output, the CSS on the card root, and any current `getGridOptions()` / `getCardSize()`.
4. The reported symptom (overlap / clipping / dead space / bad reflow / missing declaration) is reproducible from the card, or the user has stated the sizing goal explicitly.

## Workflow

### 1) Classify and determine

Walk the spec's decision tree. Classify the card as **content-dependent** or **deterministic**. Determine the full declaration:

- content-dependent → `getGridOptions: { columns: <mult-of-3>, rows: "auto", min_columns: <floor> }`, and `getCardSize()` derived from content (sum of rows/children); confirm the R5 CSS preconditions hold.
- deterministic → compute `rows` from config, `getGridOptions: { columns, rows, min_columns, min_rows: rows[, max_*] }`, and `getCardSize()` as a fixed number consistent with `rows`.

State the classification, the determined `getGridOptions()` and `getCardSize()` values, any CSS-precondition fix required, and the responsive-column choice in one short block.

### 2) Confirm (approval gate)

Present the determined declaration and the intended hand-off (inline patch vs. dispatched specialist). Wait for user confirmation before editing the card. This is the mid-flow gate that makes this a skill.

### 3) Hand off to implementation

The determination is not the end — hand the declaration to an implementation step:

- **(a) inline patch** — generate or patch `getGridOptions()` and `getCardSize()` in `card_file` (and apply any required CSS-precondition fix on the card root), matching how the sibling scaffold/augment skills generate/patch callbacks.
- **(b) dispatch** — when the edit is larger than a two-callback patch, hand the determined declaration to the appropriate implementation specialist rather than doing heavy work here.

Keep the analyse→hand-off boundary explicit: determination produces the declaration; the hand-off applies it.

### 4) Validate and report

Validate offline against the spec's Acceptance Criteria: matching branch used; both callbacks present and consistent; `rows:"auto"` preconditions hold where used; edit-mode overlays would sit at the cell boundary; no clipping/dead space in view mode; reflow within `min_columns`/`max_columns`; sensible masonry/panel distribution. Emit a CONFORMANT / NEEDS-WORK report keyed to those criteria, plus the changed file paths and the quality-scale marker (dashboard layout and custom cards are **not part of the HA quality scale** — a portfolio guardrail). Do not deploy or verify on a live instance.

## Boundaries

- greenfield card scaffold → `ha-lovelace-card-scaffold`
- full frontend orchestration → `ha-lovelace-solution`
- panels / panel UX → `ha-panel-add` / `ha-panel-author` / `ha-panel-ux-audit`
- feature control rows → `ha-card-features-add`
- card lifecycle / rendering framework → `ha/lovelace-card-patterns`
- the full layout-antipattern catalogue → `ha/lovelace-layout-antipatterns`
- deploy / runtime verify on live HA → `ha-integration-deploy` / `ha-integration-verify`
