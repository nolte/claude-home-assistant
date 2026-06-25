# HA Device: Pixel Art on the 64×64 Matrix (Shading & Contours)

Status: draft

## Context

The Divoom Pixoo 64 is a **64×64 RGB LED matrix** (4096 pixels, full 24-bit color). This spec standardizes the **design of information as pixel art** on this surface — with the goal of producing the most detailed, readable images possible. The focus is the two craft dimensions that were explicitly requested: **contours** (outlining) and **shading**, embedded in palette, anti-aliasing, dithering, and the peculiarities of a self-emissive LED panel.

The spec is **delivery-path-neutral**: the design core (palette, contours, shading, dithering) applies regardless of whether the image reaches the display as a **pre-rendered PNG** (via the `image` component) or **procedurally** (via `rectangle`/`templatable` components, per-pixel from entity states). Both paths are referenced as application sections.

Delimitation: the device/integration mechanics (connection, entities, page types, service calls, the `image` component's resample modes) live in `ha/divoom-pixoo`. This spec builds on top and addresses **what** is drawn on the matrix and **how it looks good**, not **how** it is technically transmitted.

Primary sources for the craft: Arne Niklas Jansson's pixel-art tutorial ([androidarts.com/pixtut](https://androidarts.com/pixtut/pixelart.htm)), the Lospec tutorials ([lospec.com](https://lospec.com/pixel-art-tutorials)), and established pixel-art color theory (ramps, hue shifting). Render/hardware constraints are verified against the integration code (`pixoo64/_pixoo.py`, `sensor.py`) of `gickowtf/pixoo-homeassistant` v1.23.0.

## Goals

- Pin down the hardware/render constraints of the 64×64 LED matrix as the binding frame for pixel art
- Mandate a **limited, ramp-based palette** with hue shifting as the basis for shading
- Standardize **contours**: selective outlining, interior vs. exterior contour, black vs. colored lines
- Standardize **shading**: consistent light source, shading ramps, terminator, avoidance of pillow shading
- Govern **anti-aliasing** and **dithering** as dosed tools with LED-matrix-specific limits
- Explicitly rule out typical mistakes (banding, jaggies, pillow shading)
- Tie the two delivery paths (exact 64×64 PNG with `nearest` resampling; procedural components) to `ha/divoom-pixoo`

## Non-Goals

- Device/integration mechanics (connection, config flow, entities, service parameters, page types) — belongs to `ha/divoom-pixoo`
- Animation/timing across multiple frames (GIF sequences, page rotation) beyond single still images
- Typography/font rendering of the `text` component in detail (font catalog lives in `ha/divoom-pixoo`); this spec treats text only insofar as it needs contour/contrast as a graphic element
- A concrete, project-fixed palette catalog — the spec mandates palette **rules**, not a fixed color list
- Tooling recommendations (Aseprite, Pixelorama, etc.) — tool-neutral

## Requirements

### Canvas & Hardware Constraints

- **MUST** design the image on the **64×64 grid** with origin top-left (coordinates 0…63); every pixel is a deliberate decision — with only 4096 pixels the detail budget is tight
- **MUST** accept that the panel is **self-emissive**: colors appear more vivid/brighter than on a monitor, the black point is a true off (dark pixel = invisible), and adjacent bright/dark pixels contrast strongly
- **SHOULD** prioritize **high contrast and clear silhouettes**; fine tonal nuances that work on a monitor blur on the LED matrix at viewing distance
- **SHOULD** use **1-px details sparingly** — single isolated pixels and 1-px lines can "bloom"/blur on the LED grid or get lost in contrast; lay out load-bearing shapes at least 2 px wide
- **MUST** treat the full RGB color space as given but **not as a license to mix freely** — readability comes from a disciplined palette (see next section), not from color richness

### Palette & Color Ramps

- **MUST** work with a **limited palette**; a small, deliberately chosen set of colors enforces clarity and coherence better than free 24-bit mixing
- **MUST** define shading via **color ramps** — per material/object an ordered series shadow → midtone → light (typically 3–5 values)
- **SHOULD** use **fully saturated colors** only as accents; slightly desaturated tones increase readability and avoid "neon" flicker on the LED matrix
- **SHOULD** **share** ramps between materials where possible, instead of inventing a separate ramp for every object — this keeps the overall palette small and coherent
- **SHOULD** spread values (lightness) so the silhouette stays readable **by brightness alone** (test: check in grayscale)

### Hue Shifting

- **SHOULD** when darkening/lightening **not just pull the color toward black/white** but **shift the hue**: shadows toward cool (blue/violet), highlights toward warm (yellow/orange) — this reads as more three-dimensional and lively
- **SHOULD** apply hue shifting **consistently** across the whole ramp so that adjacent ramps harmonize
- **MAY** align the light's color hue with a set light source (e.g. warm sunlight → warmer highlights, cool shadow)

### Contours / Outlining

- **MUST** apply **selective outlining (selout)**: place contours deliberately where shapes must be separated — do **not** compulsively black-outline every detail
- **SHOULD** distinguish **exterior contour** (silhouette against the background) from **interior contour** (separation of shape parts); interior contours may be thinner/colored/partial
- **SHOULD** use **black lines sparingly** — they act "subtractively" and make adjacent colors appear darker/muddier; around light areas prefer a **colored, darker variant of the surface color** as the contour ("additive" contour)
- **SHOULD** **remove or lighten the bottom contour** when an object sits on the ground — a continuous dark bottom edge makes it "float"
- **MAY** drop a closed exterior contour entirely and separate shapes by contrast/shading alone, if the background provides enough contrast (contourless style)

### Shading & Light Source

- **MUST** establish a **consistent light direction** and keep it across the whole image (front-top is a robust default); all shadows/highlights follow this direction
- **MUST NOT** produce **pillow shading** — lightening uniformly from the contour toward the center without a light source; this flattens the form
- **SHOULD** end shading ramps cleanly at a **terminator edge** (the form's light-dark boundary) instead of fading softly — the sharp boundary defines the form
- **SHOULD** **build up value and then terminate it abruptly** against a shadow value to break the "pillow" look
- **MAY** place a **specular highlight** as the smallest, brightest accent area on the light-facing side and **ambient occlusion** (slight darkening in contact/inner corners), sparingly and consistent with the light source

### Anti-Aliasing

- **SHOULD** apply **manual anti-aliasing** (intermediate tones at edges/curves) deliberately to smooth stair-stepping — but **dosed**
- **MUST NOT** **over-anti-alias** — too many intermediate tones make the image muddy and blurry; pixel art prioritizes graphical clarity over smooth curves
- **SHOULD** note on the LED matrix that AA intermediate pixels can be read at distance as **standalone pixels** rather than a soft edge — keep AA restrained on exposed outer edges against a dark background
- **MUST NOT** stack AA pixels over more than ~2 steps at a single edge — this creates blurry "double edges"

### Dithering

- **MAY** use **dithering** (alternating pixels of two colors) to smooth color transitions or suggest textures without enlarging the palette
- **SHOULD** use dithering **sparingly and with a consistent pattern** (e.g. 50% checkerboard for an intermediate step, thinning patterns for gradients) — inconsistent dithering reads as noise
- **SHOULD** prefer dithering between **two tonally close colors**; with strong LED contrast and short viewing distance the eye "blends" less, so the pattern stays visible — verify on the real device beforehand
- **MAY** use dithering for a double purpose: create a gradient **and** suggest material texture at once

### Mistake Avoidance (Banding & Jaggies)

- **MUST NOT** produce **banding** — value bands that run as parallel strips along a contour/diagonal; this draws attention to the transition instead of the form
- **SHOULD** break banding by narrower bands, moving the transition to a natural shadow boundary, or dissolving it via dithering/clusters
- **MUST NOT** allow **jaggies** — irregular, "jittery" pixel stairs; build curves over **clean, even pixel progressions** (e.g. 1-1-2-3 lengths)
- **SHOULD** lay out lines and curves so segment lengths grow or shrink monotonically/regularly instead of jumping irregularly

### Delivery Paths (tie-in to `ha/divoom-pixoo`)

- **MUST** for **pre-rendered images** author the file at **exactly 64×64 px** and embed it via the `image` component with resample mode **`nearest`** (resp. `pixel_art`) — any scaling with a smoothing mode (`box`, `bilinear`, …) destroys the pixel-art edges (see `ha/divoom-pixoo` §Components)
- **MUST NOT** author pixel art smaller than 64×64 and have it upscaled — non-integer multiples produce unevenly wide pixels; work natively at target size
- **MAY** generate pixel art **procedurally** from entity states: individual pixels/areas via `rectangle` components (`size: [1,1]` for single pixels) or dynamically via a `templatable` component that returns a list of pixel components (see `ha/divoom-pixoo` §Components)
- **SHOULD** apply the same palette/contour/shading rules on the procedural path as on the image path — the delivery form does not change the craft
- **SHOULD** verify the result **on the real device** (brightness, contrast, 1-px readability, dithering effect), not only in the editor — the LED panel deviates noticeably from a monitor

## Acceptance Criteria

- [ ] The subject is designed natively at 64×64; for PNG embedding `nearest`/`pixel_art` resampling is used, no smoothing mode
- [ ] The palette is limited and organized in ramps (shadow→mid→light, 3–5 values); fully saturated colors only as accents
- [ ] Shading follows a consistent light direction; no pillow shading; terminator edges are clearly set
- [ ] Hue shifting is discernible (shadows cooler, highlights warmer) and consistent across adjacent ramps
- [ ] Contours are selective (no full-black around every detail); interior vs. exterior contour differentiated; bottom edge not "floating"
- [ ] No banding and no jaggies; curves use clean pixel progressions; AA is dosed
- [ ] Dithering (if used) is consistently patterned and checked for effect on the real device
- [ ] The silhouette is still readable in grayscale (value only); the image was verified on the real Pixoo against brightness/contrast/1-px readability
- [ ] For procedural generation (`rectangle`/`templatable`) the same palette/contour/shading rules apply as on the image path

## Open Questions

- Should a project-fixed palette catalog (e.g. a 16–32 color ramp collection) be defined for `home-assistant-config` so all Pixoo pages look coherent?
- Is a reusable helper (script/macro) worthwhile that translates a 64×64 pixel grid from a compact data representation into a `templatable` component list (procedural pixel art from entity states)?
- Is there a device-specific gamma/brightness correction that should be calibrated between editor preview and LED display (value drift)?
