# ESPHome Device: ESP32-S3-BOX Display (Rendering and Placement)

Status: draft

## Context

The ESP32-S3-BOX carries a 2.4-inch **320×240** colour panel on SPI — the one part of the device a user looks at continuously. [`ha/esp32-s3-box`](../esp32-s3-box/en.md) establishes *that* the panel exists and how it is wired and bound (SPI pins, model preset, `invert_colors`, backlight). This spec picks up where that stops: **what can be drawn on those 76 800 pixels, and where.**

ESPHome offers two mutually exclusive rendering paths on this panel, and the choice is architectural rather than cosmetic:

- the **`display:` component** with `pages:` and C++ `lambda` blocks — an immediate-mode canvas where every frame is redrawn from scratch by the config author. This is what all three official reference configs use `[ref-config]`.
- **`lvgl:`** — a retained-mode widget toolkit with objects, styles, layouts, and event handlers, where the framework tracks what changed and redraws only that `[doc]`.

Neither is a superset of the other. The immediate-mode path is compact and fully predictable, but every layout decision is a hard-coded pixel coordinate. The LVGL path brings alignment, layouts, and touch interaction, at the cost of memory, build size, and a second mental model. A device config picks one path per display and stays with it.

The pixel-level layout conventions in this spec are anchored on the ESPHome reference configuration for the BOX-3, which is a fully worked example of the immediate-mode path: full-bleed illustrations, framed text boxes at fixed coordinates, a progress bar in the bottom 15 pixels, and a centred timer widget `[ref-config]`. Those concrete constants are the empirical basis for the layout grid proposed here.

This spec is the BOX-3 sibling of the Pixoo rendering specs (`ha/pixoo-pixel-art`) — the same idea one axis over: the device spec says how the hardware is bound, the rendering spec says how to put something meaningful on it.

### Source tiers

Evidence tiers are used exactly as defined in [`ha/esp32-s3-box`](../esp32-s3-box/en.md) §"Source tiers": `[doc]` for the official ESPHome component documentation, `[ref-config]` for the official board configs in `esphome/wake-word-voice-assistants`, `[bsp]` for Espressif's board-support package, `[vendor]` for Espressif product documentation, and `[policy]` for a nolte-portfolio rule that is not an upstream fact. Layout constants marked `[ref-config]` are measured from a shipping configuration; the grid derived from them is `[policy]`.

Verified 2026-08.

## Goals

- Make the rendering-path choice (`display:` + `pages:` versus `lvgl:`) an explicit, justified decision instead of an accident of the first example someone copied
- Pin down the canvas: coordinate system, origin, safe areas, and a reusable layout grid for 320×240 derived from a shipping configuration
- Document the complete drawing surface — primitives, text, images, colours — with the constraints that actually bite on this panel (anti-aliasing needs a background colour, fonts cost flash, images cost a lot of flash)
- Define the refresh model: why this panel is driven with `update_interval: never`, who triggers a redraw, and how flicker is avoided
- Give data-driven content a discipline: how live values reach the screen and what happens when they are longer than the space allotted
- State the memory budget honestly — a full-screen framebuffer on this panel is ~150 KiB, and that number decides what else fits
- Cover the LVGL path far enough that a project can choose it deliberately and know what it changes

## Non-Goals

- Re-stating the hardware binding of the panel — SPI pins, model preset, `invert_colors`, reset-pin inversion, and the backlight light entity belong to [`ha/esp32-s3-box`](../esp32-s3-box/en.md) and are referenced, not repeated
- A complete LVGL widget reference — the LVGL section covers placement, styling, pages, touch binding, and runtime updates; per-widget option catalogues stay with the upstream documentation
- Graphic design guidance (colour theory, iconography, typography aesthetics) — this spec governs the mechanics of placement, not the taste applied to it
- Generalising these rules to every ESPHome display — the constants here are 320×240-specific; a generic rendering spec may be distilled later if a second panel geometry enters the portfolio
- Touch *gesture* semantics and screen-flow design — touch is covered only as far as it binds into LVGL or a page switch
- The voice-assistant state machine that drives the reference screens — that lifecycle lives in [`ha/esp32-s3-box`](../esp32-s3-box/en.md) §"Voice-assistant binding"; here it is only a consumer of pages

## Requirements

### Choosing a rendering path

- **MUST** choose exactly one rendering path per display and record the choice in the config: `display:` with `pages:`/`lambda` (immediate mode) **or** `lvgl:` (retained mode) `[policy]`
- **MUST NOT** mix the two on one display: LVGL requires the display to be handed over to it (`auto_clear_enabled: false`, no display `lambda`), so a leftover page lambda either does nothing or fights LVGL for the buffer `[doc]`
- **SHOULD** choose the **immediate-mode** path for status-display devices — a fixed set of full-screen states driven by external events, little or no touch interaction; this is what the reference configs do and it keeps the whole UI reviewable in one file `[ref-config]` `[policy]`
- **SHOULD** choose **LVGL** when the screen is an interactive control surface — buttons, sliders, arcs, tabs, scrolling lists, or anything where touch changes state on the device itself `[doc]` `[policy]`
- **SHOULD** treat the decision as expensive to reverse: page lambdas and widget trees share no code, so switching paths later is a rewrite of the entire UI, not a refactor `[policy]`

### Canvas and coordinate system

- **MUST** treat the canvas as **320 wide × 240 high** with the origin `(0, 0)` at the **top left**; x grows right, y grows down `[doc]` `[ref-config]`
- **SHOULD** read the dimensions at runtime via `it.get_width()` / `it.get_height()` rather than hard-coding 320/240 wherever a centre or an edge is meant — the reference config centres its illustrations with `it.image(it.get_width() / 2, it.get_height() / 2, id(...), ImageAlign::CENTER)` `[ref-config]` `[doc]`
- **MUST** account for `rotation:` changing the effective width and height: a display rotated 90° or 270° presents a 240×320 canvas, and every hard-coded coordinate silently moves `[doc]`
- **MUST NOT** draw outside `0…319` / `0…239`; use `it.start_clipping(left, top, right, bottom)` / `it.end_clipping()` to bound a region deliberately when content may overflow `[doc]`
- **SHOULD** keep a **20-pixel outer margin** free of essential content and treat the bottom **15 pixels** as a status strip, matching the reference layout `[ref-config]` `[policy]`

### Refresh model and redraw discipline

- **MUST** set `update_interval: never` on the display and drive redraws explicitly; the reference configs render event-driven screens and call `component.update` / `id(display).update()` themselves rather than on a timer `[ref-config]`
- **MUST** funnel every redraw through **one** script (the reference config calls it `draw_display`) instead of scattering `update` calls across automations — a single entry point is what keeps screen state and application state from diverging `[ref-config]` `[policy]`
- **MUST** understand that a redraw is a **full-frame** operation in immediate mode: the display is cleared before the lambda runs unless `auto_clear_enabled: false`, and the lambda must repaint everything it wants visible `[doc]`
- **SHOULD** open each page lambda with an explicit `it.fill(<background colour>)` rather than relying on the implicit clear, so the page's background is a stated property of the page `[ref-config]` `[policy]`
- **SHOULD** redraw only on state changes that are actually visible — pipeline phase changes, connection changes, timer ticks — because every redraw pushes the full framebuffer over SPI `[ref-config]` `[policy]`
- **MUST NOT** call the redraw script from inside a page lambda; lambdas are render code, and triggering a render from a render is a re-entrancy bug `[policy]`

### Pages and state mapping

- **MUST** model discrete screen states as `pages:` with stable ids, one page per state, rather than as branches inside a single lambda `[ref-config]` `[doc]`
- **SHOULD** hold the current state in a `globals:` variable and map it to pages in exactly one place — the reference config keeps an integer `voice_assistant_phase` and switches on it in `draw_display`, with a `default:` branch that falls back to the idle page `[ref-config]`
- **MUST** provide a page for every reachable state, including the degraded ones: initializing, no Wi-Fi, and no Home Assistant are separate pages in the reference config, not an error overlay `[ref-config]`
- **MAY** switch pages with the `display.page.show`, `display.page.show_next`, and `display.page.show_previous` actions, and react to changes with the `on_page_change` trigger (which filters on `from` / `to`) `[doc]`
- **MUST** follow a page switch with an explicit update in an event-driven config: with `update_interval: never`, showing a page does not by itself put it on the panel `[ref-config]` `[doc]`
- **SHOULD** keep page lambdas free of business logic — compute in scripts or globals, render in the lambda — so a page stays a pure function of state `[policy]`

### Drawing primitives

- **MUST** address the full primitive set through the `it` object inside a lambda: `line`, `rectangle`, `filled_rectangle`, `circle`, `filled_circle`, `triangle`, `filled_triangle`, `filled_ring`, `filled_gauge`, `regular_polygon`, `filled_regular_polygon`, `draw_pixel_at`, plus `fill` and `clear` `[doc]`
- **SHOULD** build framed panels as the reference config does — a `filled_rectangle` in the fill colour followed by a `rectangle` in the border colour at identical coordinates — rather than drawing four lines `[ref-config]`
- **SHOULD** use `filled_gauge` / `filled_ring` for radial progress and a two-rectangle construction for linear progress; the reference timer bar draws a white track (`0, 225, 320, 15`) and an inset coloured fill (`0, 226, <n>, 13`) whose width is the remaining fraction of the total `[doc]` `[ref-config]`
- **MUST** compute progress widths in integer pixels and guard the divisor: the reference config divides by `max(total_seconds, 1)` before scaling to 320 px, and skips drawing entirely when the result is zero `[ref-config]`
- **MAY** render a `graph:`, `qr_code:`, or `image:` through the corresponding `it.graph` / `it.qr_code` / `it.image` calls, each of which accepts an alignment argument `[doc]`
- **SHOULD** verify a new panel or geometry with `show_test_card: true` before debugging a layout, so a wrong `color_order` or offset is ruled out first `[doc]`

### Text and fonts

- **MUST** declare every font as a `font:` component with an explicit `size:` in pixels; a font is rasterised at compile time, so a size that is not declared cannot be used at runtime `[doc]`
- **MUST** restrict the character set deliberately via `glyphs:` or `glyphsets:` — the reference config uses the Google-Fonts glyphset `GF_Latin_Core` plus an explicit allowed-character list — because every additional glyph at every declared size costs flash `[doc]` `[ref-config]`
- **MUST** pass a **background colour** to `print` / `printf` whenever the font is anti-aliased (`bpp` greater than 1): the documented signature for anti-aliased text is `it.printf(x, y, font, foreground, background, align, format, …)`, and omitting the background yields incorrectly blended text `[doc]`
- **SHOULD** keep `bpp` low (the default) for small UI text and raise it only for large display type, since higher bit depths "increase the binary size considerably" `[doc]`
- **MUST** position text with an explicit `TextAlign` value rather than relying on the default `TOP_LEFT` when the anchor is meant to be a centre or a right edge; the available values are the nine box alignments plus `BASELINE_LEFT` / `BASELINE_CENTER` / `BASELINE_RIGHT` `[doc]`
- **SHOULD** anchor centred text on `it.get_width() / 2` with `TextAlign::TOP_CENTER` (or a `CENTER` variant) instead of estimating a left offset from the expected string width `[doc]` `[policy]`
- **MUST** bound every variable-length string before it is drawn: the reference config truncates at 32 characters via `esphome::str_truncate(name, 31)` plus an ellipsis, applied in the text sensor's `on_value` rather than in the lambda `[ref-config]`
- **MUST** derive that limit by measurement and record it in a small per-project table (font × size × box width → character budget) rather than computing it at render time: the reference's 15-pixel Figtree in a 280-pixel frame fits roughly 32 characters, and every new font, size, or box width adds a measured row instead of reusing that number `[ref-config]` `[policy]`
- **MAY** render formatted time with `it.strftime(x, y, font, color, align, format, time)`; for elapsed/remaining durations the reference config formats the digits itself (`HH:MM` above one hour, else `MM:SS`) and prints with `printf` `[doc]` `[ref-config]`

### Images

- **MUST** declare each image as an `image:` component with an `id:`, and size it at compile time with `resize:` to the box it will occupy — a full-screen illustration on this panel is `resize: 320x240` `[doc]` `[ref-config]`
- **MUST** choose `type:` deliberately (`BINARY`, `GRAYSCALE`, `RGB565`, `RGB`, `RGBA`), because the type sets the per-pixel cost in flash; the reference config ships full-screen illustrations as `type: RGB` with `transparency: alpha_channel` `[doc]` `[ref-config]`
- **SHOULD** budget image flash before adding one: a 320×240 `RGB565` image is ~150 KiB and an `RGB` image is larger still, so a handful of full-screen images dominates the firmware `[doc]` `[policy]`
- **MAY** use `transparency: chroma_key` or `alpha_channel` to compose an image over a background instead of pre-baking the background into every asset; grayscale images with transparency remain one byte per pixel `[doc]`
- **MUST** place images with an explicit `ImageAlign` when the anchor is not the top left — ESPHome aligns at the top left by default, so a centred illustration is `it.image(w / 2, h / 2, id(img), ImageAlign::CENTER)` `[doc]` `[ref-config]`
- **MAY** source an image from a URL at **compile** time (the reference config pulls its illustrations from a GitHub raw URL) or from Material Design Icons; runtime downloading is a different platform (`online_image`) with its own memory cost `[doc]` `[ref-config]`
- **MUST** vendor image assets into the config repository under version control rather than depending on an upstream URL staying reachable at build time — the build stays reproducible and offline-capable, at the cost of repository size `[policy]`

### Colours

- **MUST** define reusable colours as `color:` components with ids (hex, percentage, or integer form) and reference them by id in lambdas, rather than repeating literals across pages — the reference config defines one colour per screen state plus the two timer-bar colours `[doc]` `[ref-config]`
- **MAY** construct an ad-hoc colour inline as `Color(r, g, b)` inside a lambda where a one-off value is genuinely local `[doc]`
- **MAY** use the `Color::WHITE` / `Color::BLACK` constants, which the reference config relies on for frames and text: they are declared in ESPHome's own `esphome/core/color.h` as `static const Color BLACK;` / `static const Color WHITE;`, so they are real API rather than an undocumented accident — they are simply absent from the component documentation `[ref-config]` `[doc]`
- **MUST** parameterise per-state background colours through substitutions when a config is meant to be re-themed, as the reference config does with its `*_illustration_background_color` substitutions `[ref-config]`
- **SHOULD** verify contrast on the physical panel rather than on a monitor — this is a small, bright 2.4-inch LCD, and the backlight level is a user-controllable light entity that will not always be at 100 % `[policy]`

### Layout zones and placement

- **SHOULD** compose screens from this zone grid, derived from the reference layout, instead of inventing coordinates per page `[ref-config]` `[policy]`:

| Zone | Rectangle (x, y, w, h) | Purpose |
|---|---|---|
| Full-bleed background | `0, 0, 320, 240` | `fill()` or centred full-screen illustration |
| Header box | `20, 20, 280, 30` | primary line (request / title), text inset at `30, 25` |
| Centre widget | `80, 40, 160, 50` | modal value (timer, big number), text anchored at `120, 47` |
| Footer box | `20, 190, 280, 30` | secondary line (response / status), text inset at `30, 195` |
| Status strip | `0, 225, 320, 15` | progress bar / timeline, inset fill at `0, 226, …, 13` |

- **MUST** keep the 20-pixel side margin and the 10-pixel text inset consistent across pages: the reference boxes start at x = 20 with a width of 280 (leaving 20 px on the right), and their text starts at x = 30 `[ref-config]`
- **SHOULD** treat 30 pixels as the standard row height for a 15-pixel font — one text row plus padding — and 50 pixels for the 30-pixel display font `[ref-config]` `[policy]`
- **SHOULD** centre a fixed-width widget arithmetically rather than by eye: the reference timer widget is 160 px wide at x = 80, which is exactly `(320 − 160) / 2` `[ref-config]`
- **MUST NOT** let two zones overlap on the same page unless the overlap is deliberate layering (illustration underneath, framed box on top) — in immediate mode the later call simply overwrites the earlier one, with no warning `[doc]` `[policy]`
- **SHOULD** draw shared furniture (status strip, timer widget) from small reusable `script:` entries called by each page, as the reference config does with `draw_timer_timeline` and `draw_active_timer_widget`, rather than copying the drawing code into every page lambda `[ref-config]` `[policy]`

### Data-driven content

- **SHOULD** stage live values in `text_sensor: {platform: template}` or `globals:` and read them in the lambda, instead of reaching into other components' state from render code `[ref-config]` `[policy]`
- **MUST** apply formatting, truncation, and unit handling **before** the render step — in the sensor's `on_value` or in a script — so the lambda only positions already-presentable strings `[ref-config]` `[policy]`
- **MUST** render an explicit placeholder for a value that is not yet available rather than an empty region; the reference config publishes `"..."` into its request/response sensors when a pipeline turn starts `[ref-config]`
- **SHOULD** clear transient strings when the state that produced them ends, so a stale response cannot linger behind a later screen `[ref-config]`
- **MUST** guard lambdas against unavailable inputs — an unavailable entity, an empty timer list, or a division by a zero total will otherwise fault inside render code, where the failure surfaces as a frozen screen `[ref-config]` `[policy]`

### LVGL path

- **MUST**, when LVGL is chosen, hand the display over to it: `auto_clear_enabled: false`, no display `lambda`, and `update_interval: never` on the display, with LVGL owning the refresh cycle (16 ms default) `[doc]`
- **MUST** bind the touchscreen through LVGL's `touchscreens:` key rather than handling raw coordinates, so widgets receive `on_pressed` / `on_long_pressed` events and coordinates follow LVGL's rotation `[doc]`
- **SHOULD** position widgets with `align:` against the parent plus `x` / `y` offsets, rather than absolute coordinates — the alignment constants (`TOP_LEFT`, `TOP_CENTER`, `CENTER`, `BOTTOM_RIGHT`, …) are what make a layout survive a size or rotation change `[doc]`
- **SHOULD** use a `flex` or `grid` layout on a container for anything list-like or tabular, and reserve manual `x`/`y` placement (`layout: NONE`, the default) for genuinely free-form screens `[doc]`
- **MUST** model screen states as LVGL `pages:` and switch with `lvgl.page.show` / `lvgl.page.next` / `lvgl.page.previous`; pages excluded from cycling carry `skip: true` `[doc]`
- **SHOULD** style through the documented style keys (`bg_color`, `bg_opa`, `text_color`, `text_font`, `border_width`, `border_color`, `radius`, `pad_*`, `margin_*`) rather than drawing decorative primitives behind widgets `[doc]`
- **MUST** update widget content at runtime through the update actions (`lvgl.label.update`, `lvgl.style.update`, and the widget-bound component platforms) instead of rebuilding a page — LVGL then redraws only the affected region `[doc]`
- **SHOULD** size `buffer_size` deliberately: it defaults to 100 % with a runtime fallback to 12 % if the allocation fails, and on a PSRAM board a 12 % buffer in internal RAM can outperform a full buffer in PSRAM `[doc]`

### Memory and performance budget

- **MUST** account for the framebuffer before adding other PSRAM consumers: the `mipi_spi` driver allocates a buffer sized by `buffer_size`, defaulting to 100 % of the screen when PSRAM is present — at 320×240 and 16-bit colour that is ~150 KiB `[doc]`
- **SHOULD** keep the default full-size buffer on this board, since it has 16 MB of octal PSRAM; reducing `buffer_size` forces multiple drawing passes per frame and costs performance to save memory the BOX does not need to save `[doc]` `[policy]`
- **MUST** keep the display `data_rate` at the board's documented `40MHz` unless a measured problem justifies changing it — the BSP pins the panel's pixel clock at 40 MHz `[bsp]` `[ref-config]`
- **SHOULD** treat full-screen redraws as the dominant cost on this panel and reduce redraw *frequency* first (redraw on state change, not on a timer) before optimising individual draw calls `[ref-config]` `[policy]`
- **SHOULD** leave `draw_rounding` at its default of 2 unless artifacts appear; it exists to prevent display glitches on certain controllers and must remain a power of two `[doc]`
- **MUST** count font and image assets against flash, not RAM: both are compiled into the firmware, and a few full-screen images plus several font sizes will dominate the binary `[doc]` `[policy]`

### Verification

- **MUST** verify every rendering API, config key, and default against the official ESPHome documentation before it enters a config or this spec, per [`ha/upstream-docs-verification`](../upstream-docs-verification/en.md) `[policy]`
- **MUST** treat the official board reference configs as the normative example of the immediate-mode path on this panel, and prefer them over third-party configs when the two disagree `[policy]`
- **SHOULD** validate a layout on the physical panel before it is considered done — coordinates, contrast, and truncation limits are only provable on the device, and `esphome config` will happily accept a layout that renders off-screen `[policy]`
- **SHOULD** re-verify the layout constants in this spec whenever the upstream reference config changes its screens, since they are measured from it rather than specified by it `[policy]`

## Acceptance Criteria

- [ ] The rendering path (`display:` + `pages:` or `lvgl:`) is chosen explicitly, recorded, and not mixed on one display
- [ ] The display runs with `update_interval: never`, and every redraw goes through a single named script
- [ ] Every reachable state — including initializing, no Wi-Fi, and no Home Assistant — has its own page with a stable id, and an unknown state falls back to a defined default
- [ ] Page lambdas contain rendering only; state lives in globals or text sensors, and formatting/truncation happens before the render step
- [ ] All coordinates respect the 320×240 canvas with a 20-pixel outer margin, and the bottom 15 pixels are reserved for the status strip
- [ ] Centres and edges are derived from `it.get_width()` / `it.get_height()` or from arithmetic, not from eyeballed offsets
- [ ] Anti-aliased text is drawn with an explicit background colour, and every text anchor states its `TextAlign`
- [ ] Every font declares an explicit `size` and a bounded glyph set; every image declares an explicit `resize` and `type`
- [ ] Variable-length strings are truncated to a limit measured for the actual font and box width, with a visible ellipsis
- [ ] Reusable colours exist as `color:` components with ids; per-state background colours are parameterised via substitutions
- [ ] Shared furniture (status strip, widgets) is drawn from reusable scripts rather than duplicated per page
- [ ] Lambdas are guarded against unavailable entities, empty collections, and zero divisors
- [ ] The framebuffer budget (~150 KiB at 100 % `buffer_size`) is accounted for, and font/image flash cost has been checked against the firmware size
- [ ] Where LVGL is used, the display is handed over correctly (`auto_clear_enabled: false`, no lambda), the touchscreen is bound through `touchscreens:`, and widgets are placed by `align:` plus offsets
- [ ] The finished layout has been verified on the physical panel, not only through `esphome config`

## Open Questions

- **Animation**: ESPHome ships an `animation:` platform alongside `image:`. Is there a use case on this device that justifies the flash cost of multi-frame assets, given that page switching already covers state transitions? Genuinely undecidable without a concrete design wish, so it stays open.

Settled by decision (kept here so the rationale stays findable, not as open work): the rendering path stays a **per-project** choice on the criterion already stated in *Choosing a rendering path* — no portfolio-wide default; a shared layout **package** is deferred until a second BOX screen would actually reuse it, to avoid abstracting from a single example; the truncation budget is a **measured table**, not a render-time computation; **rotation** is out of scope while the zone grid is defined for 320×240; and image assets are **vendored** into the config repository.
