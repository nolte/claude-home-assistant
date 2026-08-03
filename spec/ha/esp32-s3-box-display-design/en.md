# ESPHome Device: ESP32-S3-BOX Display Design (Icons, Colour, Structure)

Status: draft

## Context

[`ha/esp32-s3-box-display`](../esp32-s3-box-display/en.md) governs the **mechanics** of putting pixels on the ESP32-S3-BOX panel — rendering path, canvas, refresh model, pages, primitives, placement. It names graphic design an explicit non-goal: "this spec governs the mechanics of placement, not the taste applied to it." This spec is that missing half. It is the design system a screen is composed *from*, so that "which colour, which icon, which size, and what goes where" stops being decided per page by whoever writes the lambda.

The audience is a designer, not primarily a config author. It therefore states what the surface actually is before it states rules for it — and the surface is smaller and harsher than a 320×240 figure suggests:

- The panel is **48.8 mm × 36.6 mm** of active area (2.4-inch diagonal at 320×240 → 166.7 ppi, one pixel = 0.152 mm) `[derived]`
- It renders **RGB565**, not true colour: 65 536 colours from 5 bits red, 6 green, 5 blue `[doc]`
- Its brightness is a user-controllable light entity that will not always be at 100 % `[ref-config]`

Two consequences drive everything below. First, **this is a near-field device**: at one metre, 16-pixel text subtends about 5.9 arc-minutes, barely above the ~5 arc-minute resolution limit of a 20/20 eye and far below the 16–20 arc-minutes normally quoted as comfortable. Only display-sized type survives room distance. Second, a design that is merely *legible* is not enough — it must stay legible at a dimmed backlight, which is a contrast problem, not a colour-taste problem.

The colour and type systems here are not invented. They are the **Home Assistant frontend design tokens**, resolved to concrete values and carried onto the panel, so a BOX screen and an HA dashboard agree on what "warning" looks like. HA's token layer separates *core* ramps (`--ha-color-<hue>-05` … `-95`) from *semantic* roles (`--ha-color-on-warning-normal`), and ships a distinct dark set; the dark set is the one used here, because a wall- or desk-mounted panel in a room is a dark-background surface.

### Source tiers

Extending the tiers defined in [`ha/esp32-s3-box`](../esp32-s3-box/en.md) §"Source tiers":

- `[doc]` — official ESPHome component documentation
- `[src]` — behaviour real but undocumented (or contradicted by the docs), established from the ESPHome source tree; undocumented API carries no compatibility promise
- `[ref-config]` — ESPHome's official board configs in `esphome/wake-word-voice-assistants`
- `[ha-tokens]` — Home Assistant frontend design tokens, read from `home-assistant/frontend` `src/resources/theme/`
- `[md-icons]` — Google's Material Design system-icon guidelines, which Material Design Icons follows
- `[wcag]` — W3C WCAG 2.2 success criteria
- `[derived]` — computed here from a stated input (panel geometry, RGB565 quantisation, WCAG contrast formula); reproducible, not a citation
- `[policy]` — a nolte-portfolio rule, not an upstream fact

Verified 2026-08.

## Goals

- Supply a **fixed, named colour palette** with concrete values, derived from the Home Assistant dark design tokens, so state colour is a lookup rather than a per-page decision
- Prove that palette on this panel: contrast ratios computed **after** RGB565 quantisation, not on the nominal hex values
- Supply a **type scale** and an **icon size scale** tied to viewing distance and to the layout zones the sibling spec already defines
- Settle how a Material Design Icon reaches this screen — sourcing, asset type, and the one mechanism that lets a single asset carry every state colour
- Give structure a rule that survives a 48 mm screen: what a single page may contain, and what has to become a second page
- Bind the same design system to both rendering paths, so the choice of `display:` versus `lvgl:` does not change what the device looks like
- State the flash cost of the resulting asset set, because on this device a design decision is a firmware-size decision

## Non-Goals

- Rendering mechanics — canvas, coordinates, refresh model, page state mapping, primitives, truncation mechanics, and the layout-zone geometry belong to [`ha/esp32-s3-box-display`](../esp32-s3-box-display/en.md) and are referenced, not restated
- Hardware binding of the panel (SPI pins, model preset, `invert_colors`, backlight entity) — [`ha/esp32-s3-box`](../esp32-s3-box/en.md)
- Where the displayed values come from — [`ha/esphome-ha-driven-content`](../esphome-ha-driven-content/en.md)
- Pixel-art illustration craft (contours, shading, ramps, dithering) — that is [`ha/pixoo-pixel-art`](../pixoo-pixel-art/en.md), a different surface (self-emissive 64×64 matrix, 24-bit colour) with a deliberately open palette; this spec governs UI design on a 320×240 LCD with a closed one
- A light-theme variant — the dark set is normative here; a light variant is an open question below, not a shipped alternative
- Motion and animation design — the sibling spec keeps multi-frame assets an open question, and this spec does not pre-empt it
- Touch gesture and screen-flow design — only the visual side of interactive states is covered
- Icon declarations for HA integrations (`icons.json`) — that is [`ha/icons`](../icons/en.md), a different artefact entirely

## Requirements

### Viewing distance and the legibility floor

- **MUST** treat the BOX as a **near-field device** designed for roughly **0.5 m**, and **MUST NOT** expect anything below the display size to be readable across a room. Cap heights are computed at 0.70 em on a 0.152 mm pixel `[derived]`:

  | Size | Cap height | At 0.5 m | At 1.0 m | Verdict |
  |---|---|---|---|---|
  | 12 px | 1.28 mm | 8.8′ | 4.4′ | below the ~5′ resolution limit at 1 m — near-field only |
  | 16 px | 1.71 mm | 11.7′ | 5.9′ | readable at 0.5 m, at the limit at 1 m |
  | 20 px | 2.13 mm | 14.7′ | 7.3′ | comfortable at 0.5 m |
  | 28 px | 2.99 mm | 20.5′ | 10.3′ | comfortable at 0.5 m, readable at 1 m |
  | 48 px | 5.12 mm | 35.2′ | 17.6′ | the only body size comfortable at 1 m |
  | 96 px | 10.24 mm | 70.4′ | 35.2′ | glanceable across a room |

- **MUST** ensure that on every page exactly **one** element is legible from room distance — the hero value or the hero icon — and treat everything else on that page as detail the user steps closer to read `[policy]`
- **SHOULD** design against a **dimmed** backlight rather than a full-brightness one, since brightness is a user-controlled entity; a design that only works at 100 % is a design that fails in the evening `[ref-config]` `[policy]`

### The colour palette

- **MUST** use this palette, and **MUST** declare each entry as a `color:` component carrying exactly the id in the first column, so pages reference roles rather than literals `[policy]`. Values resolve the Home Assistant **dark** semantic tokens through their core ramps `[ha-tokens]`:

  | Colour id | Hex | HA dark token | Role |
  |---|---|---|---|
  | `c_bg` | `000000` | `surface-lower` | full-bleed page background |
  | `c_surface` | `202020` | `surface-default` (neutral-10) | panels and framed boxes |
  | `c_surface_low` | `141414` | `surface-low` (neutral-05) | recessed areas, status strip |
  | `c_text` | `FFFFFF` | `text-primary` | primary text |
  | `c_text_dim` | `CCCCCC` | `text-secondary` (neutral-80) | secondary text, labels, units |
  | `c_disabled` | `7A7A7A` | `on-disabled-normal` (neutral-50) | unavailable / inactive |
  | `c_border` | `5E5E5E` | `border-neutral-quiet` (neutral-40) | box borders, dividers |
  | `c_accent` | `37C8FD` | `on-primary-normal` (primary-60) | active, selected, in-progress |
  | `c_ok` | `00AC49` | `on-success-normal` (green-60) | healthy, closed, done |
  | `c_warn` | `F36D00` | `on-warning-normal` (orange-60) | attention, degraded |
  | `c_alarm` | `F3676C` | `on-danger-normal` (red-60) | fault, open, alarm |

- **MUST NOT** add a further hue to carry meaning. Home Assistant's semantic layer has exactly these channels — primary, neutral, success, warning, danger, plus disabled — and notably ships **no** distinct `info` role; informational emphasis is `c_accent` `[ha-tokens]` `[policy]`
- **MAY** use the one-step-lighter `-70` ramp variants where a large filled area needs more separation from the background: accent `7BD4FB`, success `5DC36F`, warning `FF9342`, danger `FD8F90` `[ha-tokens]`
- **MUST NOT** hard-code a hex literal inside a page lambda or widget where a role exists; a new literal is a request to extend this table, decided once, not per page `[policy]`
- **SHOULD** keep `c_bg` (true black) as the default page background rather than `c_surface`: it maximises contrast for every foreground role and, on this panel, is the one grey guaranteed to render exactly as specified (see below) `[derived]` `[policy]`

### What RGB565 does to these colours

- **MUST** accept that the panel stores 5 bits red, 6 green, 5 blue (`pixel_mode: 16bit`, the `mipi_spi` default), so every colour in the table above is quantised before it is shown `[doc]`
- **MUST** understand that **neutral greys do not stay neutral**. Green has one bit more than red and blue, so a grey `(v,v,v)` generally quantises to unequal channels — `141414` reaches the panel as `101410` and `202020` as `212021`. Only **8** of the 256 greys survive exactly (`00`, `08`, `10`, `18`, `E7`, `EF`, `F7`, `FF`), and they all sit at the extremes; in the entire mid-range an exactly neutral grey **does not exist** `[derived]`
- **MUST NOT** respond to that by snapping greys onto the neutral set — the nearest exact neutral to `neutral-50` is 98 steps away, which destroys the ramp to fix an invisible defect. The deviation is bounded at **4/255 (1.57 %)** with a mean of 2/255, which is below the perceptual threshold on a 2.4-inch panel. Specify the HA value, accept the cast `[derived]` `[policy]`
- **MUST NOT** use large-area gradients. Across the 240-pixel height, red and blue have only 32 levels — one band every 7.5 pixels — so a full-screen gradient bands visibly. Fills are flat; separation comes from contrast, not from shading `[derived]` `[policy]`
- **SHOULD** verify a suspect colour rendering with `show_test_card: true` before suspecting the palette — but note that the test card **requires** a real `update_interval`: the documentation states it is not drawn when `update_interval: never` is set, which is exactly the mode the sibling spec mandates. Testing the card therefore means temporarily changing that key `[doc]`

### Contrast

- **MUST** meet **4.5:1** for text below 24 px, **3:1** for text at 24 px and above, and **3:1** for any icon or graphic that carries meaning `[wcag]`
- **MUST** compute contrast against the **quantised** colour, not the nominal hex. Measured for this palette on the two normative backgrounds `[derived]`:

  | Foreground | on `c_bg` `000000` | on `c_surface` `202020` |
  |---|---|---|
  | `c_text` `FFFFFF` | 21.00 | 16.24 |
  | `c_text_dim` `CCCCCC` | 13.44 | 10.39 |
  | `c_accent` `37C8FD` | 11.12 | 8.60 |
  | `c_ok` `00AC49` | 7.15 | 5.53 |
  | `c_warn` `F36D00` | 7.14 | 5.52 |
  | `c_alarm` `F3676C` | 7.03 | 5.43 |
  | `c_border` `5E5E5E` | 3.15 | 2.43 |
  | `c_disabled` `7A7A7A` | 4.86 | 3.76 |

- **MUST** read that table as the reason the palette is safe: every text and state role clears 4.5:1 on both backgrounds, and quantisation moves the ratios by at most ±0.3 `[derived]`
- **MUST NOT** use `c_disabled` for text that is meant to be read — at 3.76:1 on `c_surface` it is below the body-text threshold. It is legitimate precisely because WCAG exempts inactive components: it *should* read as unavailable. Secondary readable text is `c_text_dim` `[wcag]` `[derived]`
- **MUST NOT** use `c_border` as a foreground for text or for a meaning-bearing icon; at 2.43:1 on `c_surface` it fails even the 3:1 graphic threshold and is a structural line only `[derived]`
- **SHOULD** re-run the computation rather than trusting this table whenever a colour, a background, or `pixel_mode` changes `[policy]`

### Colour semantics and redundant coding

- **MUST NOT** let colour be the only carrier of a meaning. Every state distinguished by colour **MUST** also differ in at least one of: the icon glyph, the text, or the position on screen `[wcag]` `[policy]`
- **MUST** map states onto the roles consistently across every page of a device — `c_ok` never means "attention" on one screen and "healthy" on another `[policy]`
- **MUST** give the unavailable state its own visual treatment (`c_disabled` plus a placeholder glyph or string) rather than rendering a stale last-known value in a live colour; the sibling spec already requires an explicit placeholder, and this is its visual half `[ref-config]` `[policy]`
- **SHOULD** reserve `c_alarm` for states that warrant interrupting someone; a screen where the danger colour is always present has spent it `[policy]`

### The type scale

- **MUST** use exactly these four steps, and **MUST** declare one `font:` component per step, since a font is rasterised per size at compile time `[doc]` `[policy]`:

  | Font id | Size | HA token | Zone fit (sibling spec) | Use |
  |---|---|---|---|---|
  | `f_caption` | 12 px | `--ha-font-size-s` | status strip (15 px) | units, timestamps, strip labels |
  | `f_body` | 16 px | `--ha-font-size-l` | header / footer box (30 px) | primary and secondary lines |
  | `f_display` | 28 px | `--ha-font-size-3xl` | centre widget (50 px) | the modal value |
  | `f_hero` | 48 px | above the HA scale | full-bleed | the one room-distance value |

- **MUST** treat `f_hero` as a deliberate departure: Home Assistant's scale stops at 40 px (`--ha-font-size-5xl`), which reaches only 14.7 arc-minutes at one metre on this panel. 48 px is chosen from the legibility table above, not from the token set, because HA's scale is calibrated for screens read at desk distance `[ha-tokens]` `[derived]` `[policy]`
- **MUST** use **Roboto** as the family (`file: "gfonts://Roboto"`), which is Home Assistant's `--ha-font-family-body`. This deliberately departs from the reference configs' Figtree: the tie-break is consistency with the HA frontend, not with the upstream sample `[ha-tokens]` `[ref-config]` `[policy]`
- **MUST** set an explicit `size:` on every font — it is optional in the schema and **defaults to 20**, so an omitted size renders silently at the wrong step `[doc]`
- **MUST** set `bpp: 4` on `f_display` and `f_hero`, and **MAY** leave the default `bpp: 1` on `f_caption` and `f_body`. Large glyphs show their staircase; small ones mostly do not, and higher bit depths "increase the binary size considerably" `[doc]` `[policy]`
- **MUST**, wherever `bpp` is above 1, pass the **background colour** to the print call, and pass it in the position that overload expects — `print` takes it **after** the text, `printf` takes it **fifth**, before the align. Both are documented and both are real signatures; passing it in the wrong position binds a different overload and the colour is silently consumed as a format argument `[doc]` `[src]`
- **MUST** use weight to separate label from value instead of introducing a fifth size: `gfonts://Roboto@500` for the value against the regular face for its label. HA's own scale is 300/400/500/700 `[doc]` `[ha-tokens]` `[policy]`
- **MUST NOT** set text below `f_caption`; 12 px is the floor and is already near-field-only `[derived]`
- **SHOULD** bound `glyphsets:` to `GF_Latin_Core` and add `GF_Latin_Kernel` where digits and whitespace are needed, since every glyph at every size costs flash `[doc]`

### Icons: sourcing and sizing

- **MUST** source icons from **Material Design Icons**, which ESPHome resolves natively: `file: mdi:<icon-name>` on the `file` platform, or the typed form `source: mdi` / `icon: <name>`. The sibling families `mdil:` (Material Design Light) and `memory:` are also accepted `[doc]`
- **MUST NOT** mix icon families within one device; MDI is the default set and the one Home Assistant itself uses `[doc]` `[policy]`
- **MUST** exploit that these icons are fetched as **SVG** and rasterised at compile time to the `resize:` box — so an icon is scaled from vector geometry at every size, with no resampling loss, and there is no reason to author raster icon assets by hand `[doc]`
- **MUST** use exactly these icon sizes, each pairing with a type step `[policy]`:

  | Size | Pairs with | Use |
  |---|---|---|
  | 24 px | `f_body` (16 px) | inline status icon in a header or footer line |
  | 40 px | `f_display` (28 px) | leading icon beside the modal value |
  | 96 px | — | the hero glyph that carries a full-screen state |

- **MUST NOT** render an MDI icon below **24 px**. MDI follows Google's system-icon grid: a 24 dp trim area, a 20 × 20 dp live area, and a **2 dp** stroke. Rendered at N px the stroke scales to `N/24 × 2` px — 2.0 px at 24, but 1.33 px at 16 and 1.0 px at 12, at which point strokes drop below a pixel and thin out or break `[md-icons]` `[derived]`
- **MUST** size the box against the **trim** area, not the drawing: `resize:` fits the image inside the given box preserving aspect ratio, and MDI's 2 dp of padding is part of the asset — a 24 px icon therefore paints roughly 20 px of ink, which is the correct optical size beside 16 px text `[doc]` `[md-icons]`
- **SHOULD** prefer icons whose silhouette differs from its neighbours on the same screen over icons that are semantically precise but visually similar; at 24 px on a 48 mm panel, silhouette is what the eye resolves `[md-icons]` `[policy]`

### Icons: asset type and runtime colour

The choice of `type:` is the single most consequential icon decision, because it decides whether one asset can carry every state colour or whether each colour needs its own asset.

- **MUST** declare monochrome icons as **`type: GRAYSCALE` with `transparency: alpha_channel`**, and draw them with both colour arguments: `it.image(x, y, id(icon), <foreground>, <background>)`. This form stores **one byte per pixel** (the alpha channel only) and blends `color_on` against `color_off` per pixel by the alpha value — so a single asset renders in any state colour **with anti-aliasing intact** `[doc]` `[src]`
- **MUST** treat that as an `[src]` fact deliberately, because the documentation states the opposite: it says the display lambda "will draw or not draw the pixel, no blending with the background will be done" and that `alpha_channel` is "useful mainly when using LVGL". That holds for `RGB565` and `RGB`, which take a binary decision on `alpha >= 0x80`, but **not** for `GRAYSCALE`, whose draw path computes `on = gray/255` and mixes the two colours. Verified in `esphome/components/image/image.cpp`; being undocumented, it carries no compatibility promise and belongs in the re-verification list below `[doc]` `[src]`
- **MUST** pass the **actual** background colour of the zone as the second colour argument. It defaults to `COLOR_OFF` (black), so an icon blended over a `c_surface` panel while defaulting produces a dark halo around every edge — the same failure mode as an anti-aliased font printed without its background `[src]` `[policy]`
- **MAY** use `type: BINARY` with `transparency: chroma_key` where flash matters more than edge quality: that combination is **one bit per pixel** and is still runtime-colourable (the unset pixels are simply skipped), but it has no anti-aliasing, so at 24 px the 2 px strokes render with visible stair-stepping `[doc]` `[src]`
- **MUST NOT** use `type: RGB` with `transparency: alpha_channel` for a monochrome icon. It costs **four bytes per pixel** — 32× the GRAYSCALE form — cannot be recoloured at runtime, and buys nothing on the immediate-mode path, where its alpha is reduced to a binary test. It is the reference configs' choice for full-screen *illustrations*, which is a different asset class `[doc]` `[ref-config]` `[src]`
- **MUST NOT** declare one asset per state colour. Three states of one icon are one GRAYSCALE asset drawn with three foregrounds, not three images `[policy]`
- **MUST NOT** use the `RGBA` type — it does not exist; an alpha channel is requested through `transparency:` `[doc]`

### Structure

- **MUST** hold each page to **one message**: a single subject, its state, and at most two supporting facts. The zone grid in the sibling spec offers four content zones; filling all four with unrelated readings produces a screen nobody can parse at 48 mm `[policy]`
- **MUST** compose a page from this hierarchy, top to bottom in reading priority `[policy]`:
  1. **Identity** — what this is about (header line, `f_body`, `c_text_dim`)
  2. **State** — the hero icon or value, in the state colour (`f_display` / `f_hero`, 40 or 96 px icon)
  3. **Qualifier** — a unit, a timestamp, a secondary reading (`f_caption`, `c_text_dim`)
  4. **System status** — connectivity and progress, confined to the status strip
- **MUST** keep the status strip (bottom 15 px) for device-level state only — connection, pipeline phase, progress — never for content, so the user learns one fixed place to check whether the screen is even current `[ref-config]` `[policy]`
- **MUST** split rather than shrink: when content does not fit at the mandated sizes, it becomes a second page, not smaller type. The sibling spec already models states as pages with a single redraw entry point `[policy]`
- **SHOULD** keep alignment consistent across pages — a value centred on one page and left-aligned on the next reads as two different devices; centre hero content, left-align lines of text `[policy]`
- **SHOULD** repeat position rather than re-explaining: the same fact belongs in the same zone on every page it appears, which is what lets a glance replace reading `[policy]`

### The immediate-mode path

- **MUST** declare the palette as `color:` components and the four fonts as `font:` components once per device, and reference them by id from every page lambda `[doc]` `[policy]`
- **MUST** open each page with `it.fill(id(c_bg))` so the background is a stated property of the page rather than an inherited accident `[ref-config]` `[policy]`
- **MUST** draw shared design furniture — status strip, hero-icon block, label/value pair — from reusable `script:` entries rather than copying draw calls between page lambdas, so a design change lands in one place `[ref-config]` `[policy]`
- **SHOULD** build a framed panel as a `filled_rectangle` in `c_surface` followed by a `rectangle` in `c_border` at identical coordinates `[ref-config]`
- **MAY** print an MDI glyph **inline in a text run** instead of placing an image, by adding the glyph to a font's `extras:` block with its codepoint (`\U000F02D1` for `mdi-heart`); the icon then inherits the text's size, colour, and baseline, which is the cleanest way to put a symbol *inside* a sentence. It costs a glyph in that font rather than a separate asset `[doc]`
- **MUST**, when using that inline form, escape codepoints exactly — lowercase `\u` with 4 hex digits up to `0xFFFF`, capital `\U` with 8 digits above it; MDI sits in the private use area above `0xFFFF`, so it is always the `\U` form `[doc]`

### The LVGL path

- **MUST** reproduce the same palette and scale on the LVGL path, so the design system is independent of the rendering decision. LVGL accepts an ESPHome `color:` id directly wherever a colour is expected, so the `color:` block is shared, not duplicated `[doc]` `[policy]`
- **MUST** set `theme:` with `dark_mode: true` as the baseline, then override per widget type, rather than styling each widget individually `[doc]` `[policy]`
- **MUST** express the palette as `style_definitions:` entries named for their roles and apply them through `styles:` on widgets; precedence runs state styles > local > `style_definitions` > theme > top-level, which is what makes a role-based system hold `[doc]`
- **MUST** bind interactive feedback to LVGL's own states — `pressed`, `checked`, `disabled`, `focused` — instead of repainting widgets from automations: `disabled` uses `c_disabled`, `checked` uses `c_accent` `[doc]` `[policy]`
- **MUST** recolour an icon through `image_recolor` **together with** `image_recolor_opa`, which defaults to `TRANSP` — setting the colour alone has no visible effect `[doc]`
- **SHOULD** set `text_font` to the ESPHome `font:` ids from the type scale rather than LVGL's built-in `montserrat_*` faces, so both paths render the same typography; the built-in default is `montserrat_14`, which is not a step in this scale `[doc]` `[policy]`
- **SHOULD** use `radius` and `pad_all` for separation instead of drawing borders where a surface change suffices; LVGL follows the CSS border-box model, so padding shrinks the content area `[doc]`
- **MUST NOT** introduce gradients through `bg_grad` on large areas, for the banding reason above `[derived]` `[policy]`

### Asset and flash budget

- **MUST** budget icons before adding them, at this panel's per-pixel costs `[doc]` `[derived]`:

  | Form | Bytes/px | 24 px icon | 40 px icon | 96 px icon |
  |---|---|---|---|---|
  | `BINARY` + `chroma_key` | 0.125 | 72 B | 200 B | 1.1 KiB |
  | `GRAYSCALE` + `alpha_channel` | 1 | 576 B | 1.6 KiB | 9 KiB |
  | `RGB` + `alpha_channel` | 4 | 2.3 KiB | 6.3 KiB | 36 KiB |

- **MUST** note the scale this settles: a **full-screen** `RGB` + `alpha_channel` illustration is **300 KiB**, so the design difference between an icon system and an illustration system is roughly two orders of magnitude per asset `[doc]` `[ref-config]` `[derived]`
- **SHOULD** keep the whole icon set under ~64 KiB of flash, which the GRAYSCALE form affords comfortably — around forty 24 px icons plus a handful of hero glyphs `[derived]` `[policy]`
- **MUST** count fonts against the same budget: four sizes, two of them at `bpp: 4`, over a bounded glyph set — and **MUST** re-check firmware size after changing `bpp` or a glyph set, since both multiply `[doc]`
- **MUST** vendor icon and font assets into the config repository rather than relying on an upstream URL resolving at build time, keeping the build reproducible and offline-capable `[policy]`

### Verification

- **MUST** verify every colour, size, and asset decision on the **physical panel** before it is considered done; `esphome config` validates schema, not legibility, and contrast at a dimmed backlight is only provable on the device `[policy]`
- **MUST** check each screen at the **intended viewing distance** and at a **reduced backlight**, not only at arm's length at full brightness `[policy]`
- **MUST** re-verify the `GRAYSCALE` + `alpha_channel` blending behaviour against the ESPHome source on every major version bump, since it is `[src]`-tier and contradicted by the documentation — a silent change there turns every recoloured icon into a flat block `[policy]`
- **MUST** verify each ESPHome key and default against the official documentation before it enters a config, per [`ha/upstream-docs-verification`](../upstream-docs-verification/en.md) `[policy]`
- **SHOULD** re-run the contrast computation whenever the palette, a background, or `pixel_mode` changes, rather than trusting the table above `[derived]` `[policy]`

## Acceptance Criteria

- [ ] Every colour used on the device is one of the eleven palette roles, declared as a `color:` component with the specified id; no hex literal appears in a page lambda or widget
- [ ] Contrast has been computed on the **quantised** values, and every text and meaning-bearing icon clears 4.5:1 (below 24 px) or 3:1 (24 px and above)
- [ ] `c_disabled` carries no readable text and `c_border` carries no text or meaning-bearing icon
- [ ] No state is distinguished by colour alone — each also differs in glyph, text, or position
- [ ] Exactly four fonts are declared, at 12 / 16 / 28 / 48 px, in Roboto, each with an explicit `size:`; `f_display` and `f_hero` use `bpp: 4`
- [ ] Every anti-aliased print call passes a background colour, in the position its overload expects
- [ ] Icons come from MDI, are rendered at 24 / 40 / 96 px only, and none is smaller than 24 px
- [ ] Monochrome icons are `GRAYSCALE` + `alpha_channel`, drawn with an explicit foreground **and** the zone's actual background colour; no state colour is carried by a duplicate asset
- [ ] No icon uses `RGB` + `alpha_channel`, and no image declares the non-existent `RGBA` type
- [ ] Each page carries one message, follows the identity → state → qualifier → system-status hierarchy, and the status strip carries device state only
- [ ] Content that does not fit at the mandated sizes became a second page, not smaller type
- [ ] On the LVGL path the same palette and scale are used, `dark_mode: true` is the baseline, roles are `style_definitions:`, interactive feedback is bound to LVGL states, and every `image_recolor` is paired with `image_recolor_opa`
- [ ] No large-area gradient exists on either path
- [ ] The icon and font asset set has been costed against flash and the firmware size re-checked
- [ ] The result has been reviewed on the physical panel at the intended viewing distance and at a reduced backlight

## Open Questions

- **Light variant**: the palette is dark-only. Home Assistant ships a full light token set, and a BOX on a bright desk may want it — but a runtime theme switch means every `color:` id becomes a lambda, which the immediate-mode path does not model cheaply. Whether to ship a second static palette selected at build time, or nothing, needs a real deployment that wants it.
- **Hero icon versus illustration**: this spec makes the 96 px MDI glyph the room-distance state carrier, at ~9 KiB. The reference configs instead use full-screen illustrations at ~300 KiB each. The trade is legibility-per-byte against warmth, and it has not been tested with users on this panel.
- **Type scale versus the reference zone grid**: the sibling spec's zone heights were measured from a layout using 15 px and 30 px fonts; this spec specifies 16 px and 28 px from the HA scale. The steps fit the existing 30 px and 50 px zone heights, but the zone table was not re-derived for them — whether the insets still centre optically is a measurement to make on the device.
- **`mdil:` for large glyphs**: Material Design Light is a lighter-stroke family. At 96 px the standard MDI stroke may read as heavy, and `mdil:` may be the better hero family — untested here, and it covers far fewer icons, which would split the set across two families against the rule above.
