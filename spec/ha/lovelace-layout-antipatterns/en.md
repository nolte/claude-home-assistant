# HA Dashboard: Layout and Card-Arrangement Antipatterns

Status: draft

## Context

The Lovelace skills and agents this plugin ships (`ha-lovelace-card-scaffold`, `ha-panel-add`, `ha-strategy-add`, `ha-lovelace-solution`, `ha-card-features-add`, `ha-badge-add`) can produce dashboard layouts that **render, but are fragile**: they break on HA frontend updates, ignore the native grid model, or lean on third-party tooling HA core does not know. A layout that "works right now" is not the bar — HA compatibility must hold across releases and view types.

The existing `ha/lovelace-*` cluster describes **how** to build cards, views, panels, and strategies. None of them is an **antipattern catalogue** focused on layout and arrangement on the dashboard. This spec closes that gap across the cluster and serves as a guardrail reference: for each common layout mistake it names the error, the reason it is wrong (why it breaks HA compatibility), and the compatible alternative, so agents and skills do not implement something merely because it currently renders.

**Evidence tiers.** HA-internal facts must be verified against the official docs, not asserted from memory (`ha/upstream-docs-verification`). Every catalogue entry is tagged with its evidence tier so the verification discipline stays visible:

- `[doc: user]` / `[doc: dev]` — verified verbatim against the official Home Assistant user docs (`home-assistant.io/dashboards/*`) or developer docs (`developers.home-assistant.io/docs/frontend/custom-ui/*`); the source page is named.
- `[src]` — additionally confirmed against the HA frontend source (`github.com/home-assistant/frontend`) during the verification pass (see [Verification](#verification)).
- `[rationale]` — grounded in the documented model but not a verbatim prohibition; the reasoning is stated, not a doc quote.
- `[community]` — observed in real community practice (forum threads, dashboard showcases, real card code), not stated in the official docs; used as corroboration, never asserted as an HA fact.
- `[policy]` — a nolte-portfolio rule, marked as such; not presented as an HA fact.

This spec delimits against its siblings: card internals and lifecycle live in `ha/lovelace-card-patterns`, editor mechanics in `ha/lovelace-card-editor`, feature widgets in `ha/lovelace-card-features`, badge internals in `ha/lovelace-badges`, programmatic generation in `ha/lovelace-strategies`, and the view/panel element contract in `ha/lovelace-views-panels`. Overlaps are referenced by slug, not repeated.

Quality scale marker: dashboard layout and custom cards are **not part of the HA quality scale** — this catalogue is a nolte-portfolio guardrail and lives outside the scale.

## Goals

- Name the common dashboard layout and card-arrangement mistakes, each with the error, the reason it is wrong, and the compatible alternative
- Keep HA compatibility across releases and view types the binding constraint — reject "works right now but fragile" layouts
- Anchor every HA-internal claim to a concrete official-doc page and tag its evidence tier, so no requirement rests on memory
- Give agents and skills a checkable acceptance list that fails a layout before it ships, not after
- Draw the line between native HA layout constructs (mandatory) and third-party layout tooling (forbidden for generated artifacts)

## Non-Goals

- Card internals, `set hass` lifecycle, entity-change detection, shadow DOM, CSS custom properties — covered by `ha/lovelace-card-patterns`
- Card-editor UI mechanics (`ha-form`, `getConfigElement`) — covered by `ha/lovelace-card-editor`
- Card features / tile features — covered by `ha/lovelace-card-features`
- Badge internals — covered by `ha/lovelace-badges`; this spec only covers *where badges do and do not render*
- Programmatic dashboard/view generation — covered by `ha/lovelace-strategies`
- The custom view/panel element contract (properties, `setConfig`, `ll-*` events) — covered by `ha/lovelace-views-panels`
- Theme definition, Python integration code, blueprint YAML, and naming rules (`ha/naming-conventions`)

## Requirements

The catalogue is grouped A–E. Each entry states the **Antipattern**, **Why it is wrong**, and **Instead**, followed by a normative rule. RFC-2119 keywords are binding; the bracketed evidence tier records how the claim is substantiated.

### A. View-type selection

- **A1 — Many cards in a Panel view.** `[doc: user]` `[src]` A panel view "must have exactly one card. This card is rendered full-width" (`home-assistant.io/dashboards/panel/`); the frontend `hui-panel-view.ts` renders only `cards[0]` and shows a warning alert when more than one card is configured. **Why:** the constraint is a hard rule, not a hint — extra cards do not render (only the first does), so a panel is not a multi-card container. **Instead:** wrap the content in a single stack or grid card as the panel's one card, or use a Sections view for genuinely multi-card pages.
  - **MUST NOT** place more than one card directly in a `type: panel` view
  - **MUST** use a single container card (stack/grid) when a panel must show composed content
- **A2 — Expecting badges in Panel or Sidebar views.** `[doc: user]` "Sidebar and panel views do not support badges" and "badges do not show when view is in panel mode" (`home-assistant.io/dashboards/views/`). **Why:** the feature is unsupported by design in those views, so a status you meant to surface as a badge is simply absent. **Instead:** put that status into a card, or use a view type that supports badges (Sections, Masonry).
  - **MUST NOT** rely on `badges` in a `type: panel` or `type: sidebar` view
- **A3 — Omitting `type` and expecting Sections.** `[doc: user]` `[src]` When `type` is omitted, the frontend infers the view type from the view's shape (`get-view-type.ts`): a view carrying a top-level `cards:` list defaults to **`masonry`** (the legacy engine), whereas a `sections:` list or an empty view defaults to **`sections`**, and a `panel: true` shorthand yields a panel. The official docs are self-contradictory here — the prose says "Sections (default)" while the `type` parameter table says "default: masonry". **Why:** hand-writing a classic `cards:` view without `type:` silently lands you in Masonry — no section grouping, no drag-rearrange, size-based repacking — not the Sections layout you assumed; and because the inferred type depends on schema shape, it is not reliably predictable. **Instead:** set the view type explicitly.
  - **MUST** set `type: sections` explicitly when a Sections layout is intended; **MUST NOT** rely on the implicit, shape-inferred view-type default
- **A4 — Masonry for a grouped, arranged dashboard.** `[doc: user]` "The masonry view sorts cards in columns based on their card size" and "places the next card below the smallest card" (`home-assistant.io/dashboards/masonry/`); it has no native grouping ("to group cards, you have to use horizontal stack, vertical stack, or grid cards"). **Why:** Masonry arranges by card height, not by author intent — cards jump columns as their sizes change and there is no drag-rearrange, so a deliberate arrangement cannot be held. **Instead:** use a Sections view when the arrangement matters. (Third-party `custom:layout-card` can impose explicit placement, but that is a non-native dependency — see D1.)
  - **SHOULD** choose `type: sections` for any dashboard whose card arrangement is deliberate rather than incidental
- **A5 — Building in Sections and expecting to convert later.** `[doc: user]` "you can migrate from a masonry to a sections view. Currently, you cannot migrate a sections view type into another view type" (`home-assistant.io/dashboards/views/`); the built-in Convert action is one-way (masonry → sections) and creates a new additional view rather than transforming the original. **Why:** the automated converter cannot migrate a Sections view to Panel/Sidebar/Masonry — Sections is a terminal state for the tool. (You can always change a view's `type` by hand-editing YAML and re-laying-out the cards, but there is no automated path out of Sections.) **Instead:** choose the view type deliberately up front; only `masonry → sections` is a supported automated conversion.
  - **SHOULD** select the view type against the target layout up front rather than counting on a later automated type conversion

### B. Custom-card sizing in the grid

- **B1 — Omitting `getGridOptions()` on a custom card.** `[doc: dev]` `[src]` "If you don't define this method, the card will take 12 columns and will ignore the rows of the grid" (`developers.home-assistant.io/docs/frontend/custom-ui/custom-card/`); the frontend fallback is `DEFAULT_GRID_SIZE = { columns: 12, rows: "auto" }` (`compute-card-grid-size.ts`). **Why:** every section is 12 columns wide, so a card with no grid options is forced to full width and cannot sit beside another card — it loses row control. This is a poor default, not a crash: flagship cards ship without it (for example `mini-graph-card` implements only `getCardSize()`). **Instead:** implement `getGridOptions()` returning `columns` and `rows` (each a number, or `columns: "full"` / `rows: "auto"`) with `min_columns`/`max_columns`/`min_rows`/`max_rows` bounds.
  - **SHOULD** implement `getGridOptions()` on every custom card intended for the Sections view; omitting it is acceptable only for a card genuinely meant to span the full section width
  - **SHOULD** prefer `getGridOptions()` over the deprecated `getLayoutOptions()` (still shimmed by the frontend for backward compatibility)
- **B2 — Returning a wrong or guessed `getCardSize()`.** `[doc: dev]` `[src]` `getCardSize()` returns the card height as a number (or a promise), "a height of 1 is equivalent to 50 pixels", defaulting to 1, and Home Assistant uses it to "distribute the cards evenly over the columns in the masonry view". **Why:** it affects **Masonry-view** column balancing only (the Sections view sizes via `getGridOptions().rows`); a value that does not reflect the real height skews masonry's column balancing, so cards land in the wrong column. **Instead:** return a realistic height estimate in 50px units; for cards that wrap lazy/nested cards, resolve the child's `getCardSize()` asynchronously (`customElements.whenDefined(...).then(() => el.getCardSize())`).
  - **MUST** implement `getCardSize()` returning a realistic height; **MUST NOT** return an arbitrary constant that ignores the rendered height
- **B3 — Non-multiple-of-3 default columns.** `[doc: dev]` `[src]` "For the number of columns, it's highly recommended to use multiple of 3 for the default value (`3`, `6`, `9` or `12`)". **Why:** the 12-column grid divides cleanly into thirds, so a multiple-of-3 default snaps neatly against neighbours. This applies to the **default** `columns` only — a non-multiple-of-3 column count is an explicitly supported "precise mode" (`isPreciseMode = columns % 3 !== 0` in `compute-card-grid-size.ts`), not an error, and `min_columns`/`max_columns` may be any integer (for example Mushroom uses `min_columns: 4`). **Instead:** default `columns` to one of 3/6/9/12; leave intentional precise values and min/max bounds unconstrained.
  - **SHOULD** default `getGridOptions().columns` to a multiple of 3 (`3`, `6`, `9`, `12`); a non-multiple ("precise mode") is permitted where intentional
- **B4 — Hardcoded pixel widths, absolute positioning, or a needless `columns: full`.** `[rationale]` `[src]` The documented model has HA compute pixels from cell counts — "width of the section divided by 12 (approximately `30px`)" (`developers.home-assistant.io/.../custom-card/`) — and `columns: "full"` "enforce[s] your card to be full width". **Why:** a card that pins its own outer **width** in pixels or absolutely positions itself to force its grid footprint fights HA's responsive per-section pixel math and breaks on resize and on mobile. Fixed pixel **heights** for inner content are *not* the problem — `rows: "auto"` measures rendered content, so inner heights are fine. `columns: "full"` is a legitimate, documented option; the antipattern is setting it reflexively rather than when the card genuinely spans the section. **Instead:** declare cell counts via `getGridOptions()` and let HA size the card's footprint; use relative units and HA CSS custom properties (see `ha/lovelace-card-patterns`).
  - **MUST NOT** hardcode a fixed outer **width** in px, or absolutely position a custom card, to force its footprint in the grid
  - **MUST NOT** set `columns: "full"` unless the card genuinely requires the full section width
  - fixed pixel **heights** for inner content are acceptable — `rows: "auto"` measures them
- **B5 — Using React for a custom card or panel.** `[doc: dev]` `[src]` "You can use Polymer, Angular, Preact or any other popular framework (except for React …)" (`developers.home-assistant.io/.../custom-card/`); every surveyed mainstream card (button-card, mini-graph-card, apexcharts-card, Mushroom, Bubble-Card) is built on Lit, none on React. **Why:** a custom card must be a custom element, and React does not natively render one; the docs exclude it. **Caveat:** the docs' cited interop rationale predates React 19 (which improved custom-element interop), and React can be hosted *inside* a custom-element wrapper — but this is unconventional and off the beaten path. **Instead:** vanilla `HTMLElement` (portfolio default, see `ha/lovelace-card-patterns`), Lit, or Preact.
  - **MUST NOT** build a custom card or panel with React as the element-rendering layer

### C. Structure and grouping

- **C1 — Hand-building whole-page layout from deeply nested stacks.** `[policy]`, with a `[doc: user]` counterpoint: the Sections page states you can "group cards without using horizontal or vertical stack cards" (`home-assistant.io/dashboards/sections/`), while the stack pages *do* demonstrate combining a horizontal stack inside a vertical stack for a small grid. **Why:** nested stacks are the **pre-Sections legacy approach** — before the Sections view (shipped in HA 2024.3, the new-dashboard default from 2024.11) they were the only way to build multi-column layouts, and they still work today. But scaffolding an entire page from nested stacks yields a structure with no drag-rearrange, brittle nesting, and poor responsive reflow, and it is tedious to edit. This is an outdated approach to prefer against for new dashboards, **not a broken one** — nested stacks remain valid where Sections cannot yet express the layout. **Instead:** use a Sections view for page-level grouping and reserve stacks for tight local composition.
  - **SHOULD** use a Sections view for page-level grouping on new dashboards; **SHOULD NOT** scaffold whole-page layout from nested vertical/horizontal stacks when a Sections view expresses it
  - **MAY** combine a horizontal stack inside a vertical stack for a small, self-contained cluster, and **MAY** retain nested stacks where a Sections layout cannot express the intended arrangement
- **C2 — Horizontal stack for many or unequal cards.** `[rationale]` `[community]` A horizontal stack makes its cards "sit next to each other in the space of one column" (`home-assistant.io/dashboards/horizontal-stack/`), splitting that one column's width across them. **Why:** the more cards share the column, the narrower each becomes, and on a single-column mobile render the row squishes rather than reflowing. The equal-width split and mobile-squish are **observed community behaviour**, not stated in the official horizontal-stack docs (which are silent on width division and mobile reflow); the pain shows up clearly around four or more cards or mixed content. **Instead:** use a Sections grid or a grid card with a sensible `columns` count.
  - **SHOULD NOT** place more than a few cards (roughly four or more) in a single horizontal stack; **SHOULD** prefer a Sections grid or grid card for wider clusters
- **C3 — Confusing the Grid card with the Sections view grid.** `[doc: user]` `[src]` The grid **card** (`type: grid`) has `columns` (default `3`) and `square` (default `true`) and "will first fill the columns, automatically adding new rows as needed" (`home-assistant.io/dashboards/grid/`); Sections uses `type: grid` for the *section wrapper*, which participates in the responsive 12-column Sections grid and does **not** take the card's `columns`/`square` options. **Why:** the `type: grid` name collision leads to reaching for the wrong tool — a fixed local NxM cluster versus a whole-view responsive layout engine. **Instead:** use the grid card for a fixed local NxM cluster inside a view; use a Sections view (whose sections are `type: grid` wrappers) for whole-view layout.
  - **MUST** distinguish the grid card (a container placed in `cards:`) from the Sections section wrapper (also `type: grid`, but with the Sections column model) and pick the one matching the layout scope
- **C4 — Gaming Masonry with spacer or empty cards.** `[rationale]` `[community]` Masonry "places the next card below the smallest card on the dashboard" (`home-assistant.io/dashboards/masonry/`); the spacer/blank-card trick is a widespread community technique. **Why:** it is popular precisely because Masonry placement is size-coupled and unpredictable — but a fixed-size spacer only holds its position while every surrounding card keeps its current height; any height change (state update, expand, responsive breakpoint) reshuffles the columns and collapses the intended layout. No authoritative source endorses spacers. **Instead:** use a Sections view, where placement is explicit and deterministic rather than emergent.
  - **SHOULD NOT** insert spacer/empty cards to steer Masonry column placement; **SHOULD** switch to a Sections view when placement must be controlled

### D. Third-party tooling and compatibility

- **D1 — Depending on third-party layout tooling for generated artifacts.** `[policy]` Third-party HACS layout add-ons (for example layout-card, card-mod, stack-in-card) force layouts HA core does not natively support. **Why:** they break on HA frontend updates, require the user to install and register extra resources by hand, are not auto-registrable from an integration, and get no card-picker or editor integration — every one of which violates the "HA compatibility at all times" requirement for artifacts this plugin generates. **Instead:** native Sections / grid / stack constructs plus `getGridOptions()` for card sizing.
  - Scope: this prohibits *generated / distributed* artifacts from depending on third-party layout tooling. It does **not** judge a user's own **hand-built** dashboard, where these tools are standard and legitimate. The prohibition rests on two grounds — the consumer may not have the resource installed/registered (so the artifact does not render at all), and the tooling reaches into frontend internals that change across releases (card-mod styling regressed on concrete frontend updates, for example 2025.1 and 2026.4).
  - **MUST NOT** generate dashboard or card artifacts that depend on third-party layout tooling (layout-card, card-mod, stack-in-card, or equivalents)
  - **MUST** achieve the target layout with native HA constructs (Sections, grid card, stacks, `getGridOptions()`)
- **D2 — Assuming drag-rearrange or resize in non-Sections views.** `[doc: user]` In the Sections view "you can rearrange sections and cards by dragging them… This is not yet possible in other views" (`home-assistant.io/dashboards/sections/`). **Why:** designing a workflow around drag-rearrange (or drag-resize) in Masonry/Panel/Sidebar promises an editor affordance those views do not offer. **Instead:** use a Sections view when interactive rearrangement is part of the intended experience.
  - **SHOULD** choose a Sections view when drag-rearrange is expected; **MUST NOT** document non-Sections views as supporting drag-rearrange

### E. Responsive and device behaviour

- **E1 — Ignoring `narrow` and the mobile single-column collapse.** `[doc: dev]` A custom panel receives `narrow` (boolean), "if the panel should render in narrow mode" (`developers.home-assistant.io/docs/frontend/custom-ui/creating-custom-panels/`); `[doc: user]` a Sidebar view "on mobile, all cards are rendered in 1 column and kept in the order indicated in the YAML configuration" (`home-assistant.io/dashboards/sidebar/`) — this documented 1-column collapse is **sidebar-scoped**; other views' mobile column behaviour is undocumented (see Open Questions). **Why:** a panel that never reads `narrow`, or a sidebar whose card order ignores the mobile collapse, overflows or reads out of order on phones. **Instead:** handle the `narrow` property in custom panels, and order cards so the single-column collapse still reads correctly.
  - **SHOULD** read and honour the `narrow` property in custom panels
  - **SHOULD** order cards so a single-column collapse (the documented sidebar/mobile case) preserves a sensible reading order

## Acceptance Criteria

- [ ] Every `type: panel` view contains exactly one card (a container card when composed) — A1
- [ ] No `badges` are relied upon in `type: panel` or `type: sidebar` views — A2
- [ ] View `type` is set explicitly; no view relies on the implicit shape-inferred default when Sections is intended — A3
- [ ] Deliberately-arranged dashboards use `type: sections`, not Masonry — A4/A5
- [ ] Every generated custom card intended for sections implements `getGridOptions()` (or deliberately spans the full section width) — B1
- [ ] Every generated custom card implements a realistic `getCardSize()` — B2
- [ ] Default `getGridOptions().columns` is a multiple of 3 (`3`/`6`/`9`/`12`) unless a precise value is intentional — B3
- [ ] No custom card hardcodes a fixed outer pixel width or absolute positioning to force its grid footprint; `columns: "full"` is used only when the full row is genuinely required (fixed inner-content heights are fine) — B4
- [ ] No custom card or panel is built with React as the rendering layer — B5
- [ ] Page-level layout uses a Sections view on new dashboards, not a nested-stack scaffold — C1
- [ ] Horizontal stacks hold only a few cards; wider clusters use a Sections grid or grid card — C2
- [ ] Grid card vs Sections section wrapper are not conflated — C3
- [ ] No spacer/empty cards are used to steer Masonry placement — C4
- [ ] No generated artifact references third-party layout tooling (layout-card, card-mod, stack-in-card, …) — D1
- [ ] No non-Sections view is presented as supporting drag-rearrange — D2
- [ ] Custom panels read `narrow`; card order survives the single-column mobile collapse — E1
- [ ] Every HA-internal claim in a generated layout is traceable to an official-doc page or the frontend source; `[rationale]`/`[community]`/`[policy]` items are not presented as HA facts
- [ ] Quality scale marker: not part of the HA quality scale (portfolio guardrail)

## Verification

This catalogue was adversarially verified on 2026-07-22: for each antipattern a permissive negation ("this practice is actually fine") was tested against real HA dashboard/panel development — the HA frontend source (`github.com/home-assistant/frontend`: `get-view-type.ts`, `hui-panel-view.ts`, `types.ts`, `hui-card.ts`, `compute-card-grid-size.ts`), popular custom cards (button-card, mini-graph-card, apexcharts-card, Mushroom, Bubble-Card), and community practice. **No antipattern was refuted.** Outcomes:

- **Confirmed as written**: A2, A4, C3, C4, D2.
- **Confirmed, wording narrowed to the nuance now stated inline**: A1 (panel renders `cards[0]` plus a warning — not silent), A3 (an omitted `type` is shape-inferred, not a flat `masonry` default), A5 (one-way applies to the Convert tool; manual YAML re-typing is always possible), B2, B3, B4, B5, C1 (legacy approach, not broken), C2 (community-observed mechanism), D1 (scoped to generated/distributed artifacts), E1 (the collapse quote is sidebar-scoped).
- **Severity corrected**: **B1 downgraded MUST → SHOULD** — omitting `getGridOptions()` is a poor default (full width, rows ignored), not a crash; `mini-graph-card` ships without it.

Documentation hazards resolved during the pass (previously Open Questions):

- `getLayoutOptions()` is a real but `@deprecated` frontend method superseded by `getGridOptions()`, still shimmed for backward compatibility (`types.ts`, `hui-card.ts`). New cards use `getGridOptions()`; `LovelaceGridOptions` is `{ columns?: number | "full"; rows?: number | "auto"; min_columns?; max_columns?; min_rows?; max_rows? }`.
- The omitted-`type` default is shape-dependent in `get-view-type.ts` (`cards:` → masonry, `sections:` / empty → sections, `panel:` → panel); the docs' prose-vs-table contradiction is textual, but the behaviour is defined.
- A panel with more than one card renders only `cards[0]` and shows a warning alert (`hui-panel-view.ts`); it does not error.
- Sections shipped in HA 2024.3 and became the new-dashboard default in 2024.11.

## Open Questions

Remaining documentation hazards — recorded honestly rather than asserted. Each should be re-checked against the official docs or frontend source before a downstream spec hardens it.

- **`grid_options` user-override precedence**: the user-facing `grid_options` YAML key and the card-side `getGridOptions()` are both applied by the frontend (`hui-card`), but the precise merge precedence (user config vs card default) is not documented. Not encoded here beyond preferring the card-side method.
- **`max_columns` / `dense_section_placement`**: these appear only as UI labels ("Max number of sections wide", "Dense section placement") in the user docs, with no documented YAML key. Not encoded as config keys.
- **Sections resize handles**: the user docs describe drag-*rearrange* but not drag-*resize* of cards in grid units. The resize affordance exists in the product but is undocumented; D2's "or resize" clause stays a rationale extension, not a doc quote.
- **Masonry column count / breakpoints**: the user docs state no column count, no screen-width adaptation, and no numeric responsive breakpoints for any view. E1's responsive rules stay at the documented level (sidebar 1-column collapse; panel `narrow`).
- **`getGridOptions()` introduction release**: Sections shipped in 2024.3, but the exact release that introduced the `getGridOptions()` card method is not pinned to a doc statement.
