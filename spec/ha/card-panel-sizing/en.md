# HA Dashboard: Card and Panel Sizing

Status: draft

## Context

A custom Lovelace card or panel must declare how large it is. Home Assistant has
**two** independent sizing channels and **three** view types that consume them
differently, and the most useful value is undocumented — so authors routinely
guess and ship cards that render correctly in one view and break in another.

- **Sections view** reads `getGridOptions()` — a 12-column grid where each card
  occupies a rectangle of grid cells (`columns` × `rows`).
- **Masonry and panel views, and stacks** read the legacy `getCardSize()` — a
  height in ~50px units used to distribute cards down columns.

The originating case: the `nolte/kamerplanter-ha` custom cards each declared a
**fixed, guessed** `rows` count. In the **sections-view edit mode** a numeric
`rows` pins the card to a fixed pixel height (the `.fit-rows` height `calc`);
taller, content-dependent cards overflowed their grid cell, and HA anchors its
edit-mode overlays (drag handle, dashed `+` add-zone, drop indicator) to the
**grid-cell boundary**, not the real content box — so the overlays landed in the
middle of the card content. The fix was `rows: "auto"`. Finding it required
reading the frontend source, because the developer docs do not document the
`"auto"` value.

This spec is the canonical, source-grounded **decision procedure**: given a
card's design and content variability, which size declaration (`getGridOptions` +
`getCardSize`) renders correctly across **all** view types, **both** modes
(view / edit), and **all** device sizes.

**Delimitation.** This spec owns only the *sizing decision procedure*. Card
internals and the `getGridOptions`/`getCardSize` lifecycle live in
`ha/lovelace-card-patterns`; the broader layout/arrangement guardrail catalogue
(including the pixel-width and `columns: "full"` antipatterns) lives in
`ha/lovelace-layout-antipatterns`; the view/panel element contract lives in
`ha/lovelace-views-panels`; card features in `ha/lovelace-card-features`. Overlaps
are referenced by slug, not repeated.

**Evidence tiers.** HA-internal facts are verified against the official docs and
the frontend source, not asserted from memory (`ha/upstream-docs-verification`).
Each claim carries its tier:

- `[doc: dev]` — verified against the developer docs
  (`developers.home-assistant.io/docs/frontend/custom-ui/*`); the page is named.
- `[src]` — confirmed against the HA frontend source
  (`github.com/home-assistant/frontend@dev`); the file is named.
- `[rationale]` — grounded in the documented/sourced model but reasoned, not a
  verbatim quote.

Quality-scale marker: dashboard layout and custom cards are **not part of the HA
quality scale** — this is a nolte-portfolio guardrail and lives outside the scale.

## Goals

- Give a deterministic decision tree that maps a card's content shape to a size
  declaration correct in sections, masonry, and panel views, in view and edit mode.
- Make the `getGridOptions` ↔ `getCardSize` relationship explicit: which view type
  reads which, and when both must be implemented.
- Codify the CSS preconditions a card must satisfy for `rows: "auto"` to measure
  its real content.
- Record the `rows: "auto"` value and the `.fit-rows` height mechanics with source
  citations, since the developer docs omit them.
- Explain the edit-mode overlay anchoring so authors understand *why* a wrong
  height produces overlap.

## Non-Goals

- The card lifecycle, registration, and rendering framework choice — see
  `ha/lovelace-card-patterns` and `ha/lovelace-views-panels`.
- The full layout/arrangement antipattern catalogue — see
  `ha/lovelace-layout-antipatterns` (this spec references it, does not restate it).
- A build stack, TypeScript, or Lit migration — separate concern.
- Runtime verification on a live HA instance — `ha-integration-deployer` /
  `ha-integration-verifier`.

## Field reference (source of truth)

`getGridOptions()` returns `LovelaceGridOptions` `[src: src/panels/lovelace/types.ts]`:

```ts
export interface LovelaceGridOptions {
  columns?: number | "full";
  rows?: number | "auto";
  max_columns?: number;
  min_columns?: number;
  min_rows?: number;
  max_rows?: number;
}
```

- `columns` — grid-cell width. A number, or `"full"` (span the whole section).
  Default `12` when `getGridOptions` is absent `[doc: dev]`; the frontend fallback
  is `DEFAULT_GRID_SIZE = { columns: 12, rows: "auto" }`
  `[src: src/panels/lovelace/common/compute-card-grid-size.ts]`. The docs recommend
  a multiple of 3 (`3, 6, 9, 12`) for the default `[doc: dev]`.
- `rows` — grid-cell height. A number (**fixed** height) **or** `"auto"`
  (**content-measured** height). The `"auto"` value is **not documented** on the
  custom-card page `[doc: dev]`; it is source-attested `[src: types.ts]` and is the
  frontend's own default.
- `min_columns` / `max_columns` / `min_rows` / `max_rows` — the responsive bounds
  the user may resize within. Documented defaults: `min_columns = 1`,
  `min_rows = 1` `[doc: dev]`.

A legacy analogue `LovelaceLayoutOptions` carries the same fields under a `grid_`
prefix (`grid_columns`, `grid_rows`, …) `[src: types.ts]`; new cards use
`getGridOptions()` / `LovelaceGridOptions`.

`getCardSize()` returns a height where **1 unit ≈ 50px**; the default is `1` when
undefined; it may return a `Promise<number>` for lazy content `[doc: dev]`.

### How the section renders the fields `[src: src/panels/lovelace/sections/hui-grid-section.ts]`

- The section grid declares `grid-auto-rows: auto;`.
- The `fit-rows` class — which pins a **fixed** pixel height — is applied **iff**
  `typeof rows === "number"`. A `rows: "auto"` card is never `.fit-rows`; it grows
  with `grid-auto-rows`.
- `--row-size` / `--column-size` are set from the options **only when numeric**;
  for `"auto"` / `"full"` they stay `undefined`.
- The fixed height is:

  ```css
  .card.fit-rows {
    height: calc(
      (var(--row-size, 1) * (var(--row-height) + var(--row-gap))) - var(--row-gap)
    );
  }
  ```

  With the section defaults `--row-height: 56px` and `--row-gap: 8px`
  (`--ha-section-grid-row-height` / `--ha-section-grid-row-gap`; column gap
  `--ha-section-grid-column-gap: 8px`), a numeric `rows = N` is exactly
  `N × (56 + 8) − 8` px.
- **Edit mode** adds `min-height: calc((var(--row-height) - var(--row-gap)) / 2)`
  (= `24px`) to every card, and the add-zone is `.add { height: var(--row-height) }`
  (= `56px`). These overlays are laid out against the **grid cell**, so a cell
  shorter than the content places them over the content — the originating bug.

## Requirements

### R1 — Choose the sizing model from content shape `[rationale]`

- **MUST** classify the card before declaring size: is its rendered height
  **content-dependent** (entity lists, timelines, logbooks, variable sections whose
  height is not known from config) or **deterministic** (a fixed layout whose height
  follows from the config)?
- Content-dependent → the `"auto"` branch (R2). Deterministic → the computed-fixed
  branch (R3). A card that is unsure **MUST** default to `"auto"`, matching the
  frontend's own `DEFAULT_GRID_SIZE`
  `[src: compute-card-grid-size.ts]`.

### R2 — Content-dependent cards use `rows: "auto"` `[src: hui-entities-card.ts]`

- **MUST** return `rows: "auto"` from `getGridOptions()`, plus a `columns` default
  and a `min_columns` floor. The canonical example is `hui-entities-card`:

  ```ts
  public getGridOptions(): LovelaceGridOptions {
    return { columns: 12, rows: "auto", min_columns: 3 };
  }
  ```

- **MUST** satisfy the CSS preconditions in R5 so `grid-auto-rows: auto` can
  measure the real content.
- **MUST NOT** set `min_rows` / `max_rows` on an `"auto"` card except to bound a
  genuinely resizable range; a fixed `min_rows` reintroduces a floor the content may
  exceed.

### R3 — Deterministic cards compute a numeric `rows` and pin `min_rows: rows` `[src: hui-tile-card.ts]`

- **MUST** compute `rows` from the config and return `min_rows: rows`, so the user
  cannot shrink the card below its real content. The canonical example is
  `hui-tile-card`:

  ```ts
  public getGridOptions(): LovelaceGridOptions {
    const columns = 6;
    let min_columns = 6;
    let rows = 1;
    // … increment rows per feature row / vertical layout …
    return { columns, rows, min_columns, min_rows: rows };
  }
  ```

- **MUST** keep the numeric `rows` in sync with the real rendered height; an
  under-count reproduces the edit-mode overlay overlap (see R6).

### R4 — Implement `getCardSize()` alongside `getGridOptions()` `[doc: dev]` `[rationale]`

- **SHOULD** implement **both** callbacks. `getGridOptions()` governs the
  **sections** view only; `getCardSize()` governs **masonry** and **panel** views
  and **stacks**. A card with only `getGridOptions()` defaults to size `1` (≈50px)
  in masonry and mis-distributes; a card with only `getCardSize()` falls back to
  `{ columns: 12, rows: "auto" }` in sections (full width).
- **MUST** make `getCardSize()` reflect the same content model: content-dependent
  cards derive it from content (as `hui-entities-card` sums title/entities/header/
  footer) `[src]`; deterministic cards return a fixed number consistent with the
  computed `rows` (as `hui-tile-card`) `[src]`.
- **MAY** return `Promise<number>` from `getCardSize()` when the height depends on
  lazily-defined child elements `[doc: dev]`.

### R5 — CSS preconditions for `rows: "auto"` `[src: hui-grid-section.ts]` `[rationale]`

For `grid-auto-rows: auto` to measure the card, the card root **MUST NOT**:

- set a fixed `height` or `height: 100%` on the card root (defeats measurement);
- `overflow: hidden` in a way that clips the measured content;
- use `position: absolute` on the root (collapses the measured box to 0).

Fixed pixel **heights on inner content are fine** — `"auto"` measures the rendered
box (this delimits to `ha/lovelace-layout-antipatterns` B4, which distinguishes
inner heights from outer width pinning).

### R6 — Account for edit mode explicitly `[src: hui-grid-section.ts]`

- **MUST** treat the edit-mode overlay overlap as a sizing defect, not a cosmetic
  one: because overlays anchor to the grid cell (`min-height 24px`, add-zone `56px`),
  a cell shorter than the content mislocates them.
- **MUST** resolve it by the correct branch — `rows: "auto"` (R2) for
  content-dependent cards, or a correctly computed numeric `rows` with
  `min_rows: rows` (R3) — never by tuning a fixed `rows` guess.

### R7 — Responsive columns across devices `[doc: dev]` `[rationale]`

- **MUST** declare a `columns` default (a multiple of 3 is recommended) and a
  `min_columns` floor so the card reflows sensibly as the section narrows on tablet
  and mobile; **SHOULD** set `max_columns` when the card has an upper useful width.
- **MUST** reserve `columns: "full"` for cards that genuinely span the section, not
  as a reflex (see `ha/lovelace-layout-antipatterns` B4). The device-specific
  mobile single-column collapse is view-type-dependent and is owned by
  `ha/lovelace-layout-antipatterns` E1 — referenced, not restated here.

## Decision tree

```
Is the card's rendered height known from its config alone?
│
├─ NO  (lists, timelines, logbooks, variable content)
│     → getGridOptions: { columns: <mult-of-3>, rows: "auto", min_columns: <floor> }
│     → getCardSize:    derive from content (sum of rows/children)
│     → satisfy R5 CSS preconditions
│
└─ YES (deterministic, fixed layout)
      → compute rows from config
      → getGridOptions: { columns, rows, min_columns, min_rows: rows[, max_*] }
      → getCardSize:    a fixed number consistent with rows
```

## Acceptance Criteria

- [ ] The card classifies as content-dependent or deterministic, and uses the
      matching branch (`rows: "auto"` vs. numeric `rows` + `min_rows: rows`).
- [ ] `getGridOptions()` and `getCardSize()` are **both** implemented and consistent
      with each other and with the chosen model.
- [ ] For `rows: "auto"` cards, the R5 CSS preconditions hold (no root fixed/`100%`
      height, no clipping `overflow: hidden`, no `position: absolute` root).
- [ ] In sections-view **edit mode** there is no overlay overlap: the drag handle,
      the dashed `+` add-zone, and the drop indicator sit at the cell boundary, not
      inside the content.
- [ ] In sections-view **view mode** there is no content clipping and no dead space.
- [ ] On desktop, tablet, and mobile the card reflows within its
      `min_columns`/`max_columns` bounds without overflow.
- [ ] In masonry and panel views the card distributes sensibly (a correct
      `getCardSize()`, not the default `1`).
- [ ] Every HA-internal claim in the produced card/spec carries a `[doc: dev]` or
      `[src]` citation; no claim is asserted from memory.

## Verification

The field set, the `"auto"` value, the `.fit-rows` height `calc`, the
`grid-auto-rows: auto` default, the `typeof rows === "number"` gate for `.fit-rows`,
the edit-mode `min-height`/add-zone heights, and the two canonical card patterns
were confirmed on 2026-07-22 against `github.com/home-assistant/frontend@dev`
(`src/panels/lovelace/types.ts`, `.../common/compute-card-grid-size.ts`,
`.../sections/hui-grid-section.ts`, `.../cards/hui-entities-card.ts`,
`.../cards/hui-tile-card.ts`) and the developer docs
(`developers.home-assistant.io/docs/frontend/custom-ui/custom-card/`). The
developer-docs omission of `rows: "auto"` is recorded above; the source is
authoritative for it.

## Open Questions

- Exact HA release in which each `LovelaceGridOptions` field first shipped is not
  pinned here; sections view is HA 2024.3+ and the field set is present on `@dev`.
  A per-field "since version" table is deferred until a versioned source is cited.
- The precise mobile column-count behaviour per view type (beyond the
  sidebar 1-column collapse owned by `ha/lovelace-layout-antipatterns` E1) is
  undocumented upstream and left open.
