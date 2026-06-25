# HA Device: Pixel Art Animation on the 64×64 Matrix

Status: draft

## Context

This spec standardizes **animating pixel art** on the Divoom Pixoo 64's 64×64 RGB LED matrix — i.e. how a **moving display** arises over time. The core the question addresses: animation is produced by **shifting pixels** (motion) and **adjusting colors** (color/value change) across successive frames.

The decisive factor is the integration's **frame model** (`gickowtf/pixoo-homeassistant`, verified against `pixoo64/_pixoo.py` v1.23.0): each push transmits **exactly one frame** (`Draw/SendHttpGif` with `PicNum: 1`, `PicOffset: 0`, an incrementing `PicID`, reset via `Draw/ResetHttpGifId`). An animation is therefore a **sequence of full page re-renders over time**, not a multi-frame sequence transmitted in a single call. Each rendered page state is a frame; "motion" and "color change" are functions of a **phase/time variable** evaluated anew per frame.

This implies a hard property of the delivery path: frames are pushed individually over HTTP (9 s timeout per command). The self-driving page rotation works in **integer seconds** — procedural animations over it run at roughly **~1 fps**. Higher frame rates require driven `update_page` loops (with crash risk, see below). This device/integration is therefore suited to **slow animations** (ticking, pulsing, slow travel, state changes), not smooth high-fps motion.

Delimitation: static image design (palette, contours, shading) lives in `ha/pixoo-pixel-art` and is presupposed here — every frame is a valid pixel-art image per that spec. The device/integration mechanics (page types, `update_page`/`show_message` services, resample modes) live in `ha/divoom-pixoo`. This spec covers only the **temporal dimension** on top.

## Goals

- Pin down the animation models: procedural frame animation (focus), pre-rendered GIF, native device effects
- Clarify the frame-driver and timing model (short `duration`, `update_page` loop, single-frame push, frame-rate ceiling) bindingly
- Standardize the **phase/time base** (from `now()`, `timer`, `counter`) as the source of frame selection
- Govern **motion through pixel displacement** (position as a function of phase, integer grid, looping)
- Govern **color animation** (palette cycling, value pulsing, hue shift over time, blink/fade in discrete steps)
- Secure frame coherence, flicker avoidance, and readability across the loop
- Tie the delivery paths to `ha/divoom-pixoo` and image design to `ha/pixoo-pixel-art`

## Non-Goals

- Static single-image design (palette, contours, shading) — belongs to `ha/pixoo-pixel-art`
- Device/integration mechanics (page types, service parameters, entities, resampling) — belongs to `ha/divoom-pixoo`
- Creating the GIF files themselves (external tooling, frame authoring, hosting)
- Native firmware animations not driven by the integration (clock faces, visualizer, app channels) beyond their embedding as a page
- Guarantees of smooth frame rates — the single-frame push model makes high, even FPS not promisable device-side

## Requirements

### Animation Models

- **MUST** choose the appropriate model: (a) **procedural frame animation** — a `components` page whose positions/colors are computed from a phase variable and which is re-rendered repeatedly (this spec's focus); (b) **pre-rendered GIF** via `page_type: gif` (`Device/PlayTFGif`, exactly 16/32/64 px, played natively by the device); (c) **native device effects** (e.g. clock/visualizer) only via their page embedding
- **MUST** understand that in the procedural model **each frame is a full page re-render** pushing exactly one buffer (`PicNum: 1`) — there is no frame list transmitted in a single call
- **SHOULD** prefer the pre-rendered GIF for **continuous, non-data-dependent** motion (logo loop, marquee); use the procedural path for **data-driven** animation (values, states, progress)
- **MUST NOT** assume the `components` `text` component scrolls natively — the protocol-level `Draw/SendHttpText` scroll (`speed`/`dir`) is not used by the component path; scrolling text must be solved procedurally via pixel displacement or as a GIF

### Frame Driver & Timing

- **MUST** choose a frame driver: **short `duration`** on the (single) page (self-driving — the page re-renders after each interval) **or** repeated **`update_page`** calls from an automation/script (event-driven)
- **MUST** accept that `duration`-driven rotation works in **integer seconds** — the practical floor is ~1 s/frame (~1 fps); "faster" animation requires an `update_page` loop
- **MUST NOT** excessively "spam" `update_page` — forcing re-renders frequently can crash the device (see `ha/divoom-pixoo` §Services); bound frame intervals deliberately
- **SHOULD** set frame rates **low and device-verified** — each frame is an HTTP push (9 s timeout); sub-second smoothness is not guaranteed
- **SHOULD** keep frames **cheap** (few components, simple templates) — an expensive re-render lengthens the effective frame interval
- **MAY** rely on the internal `PicID` counter and its automatic reset (`Draw/ResetHttpGifId`) — the integration manages it; custom frame IDs are unnecessary

### Phase/Time Base

- **MUST** define a **phase variable** as the source of frame selection, derived from `now()` (e.g. second/minute), a `timer`, or a `counter`; all positions/colors are functions of this phase
- **SHOULD** form the phase for a **seamless loop** modulo the frame count (`phase = tick % frames`), so the last frame transitions smoothly into the first
- **SHOULD** draw the phase from a **monotonically advancing** source (e.g. `now().timestamp() | int`), not from a value that can jump/jump back — otherwise the motion stutters
- **MAY** combine multiple independent phases (e.g. one for motion, a slower one for color cycling)

### Motion Through Pixel Displacement

- **MUST** implement motion as **position = f(phase)** — component `position`/`rectangle` coordinates are computed per frame from the phase; displacing the same shape across frames produces the perceived motion
- **MUST** respect the **integer 64×64 grid**: there is **no sub-pixel** — motion is stepwise; smooth speed comes from frame frequency and step sizes, not from floating-point positions
- **SHOULD** displace **at least 1 px** per frame so motion is visible, but **not so far** that the shape "jumps" between frames and becomes unreadable — choose the step size to match the frame rate
- **SHOULD** design looping/wrapping deliberately (run out at the 0…63 edge and re-enter on the opposite side) so the motion closes seamlessly
- **MAY** implement **easing** via a precomputed step-size table (phase → offset) instead of linear steps to suggest acceleration/deceleration
- **SHOULD** keep the **silhouette consistent across all frames** (same shape/shading, only displaced) so the eye sees a moving object and not a flickering pattern

### Color Animation

- **MUST** implement color change as **color = f(phase)** — component `color` is computed per frame from the phase
- **SHOULD** keep color animation **within the palette/ramps** from `ha/pixoo-pixel-art`: **palette cycling** (rotate the ramp index over the phase), **value pulsing** (move brightness up/down along the ramp), **hue shift over time** — instead of free RGB jumps
- **SHOULD** perform blink/fade in **discrete steps** along the ramp (e.g. 3–4 values) instead of a continuous RGB gradient — this fits the pixel-art aesthetic and stays readable on the LED panel
- **MUST NOT** produce unintended **flicker** — e.g. toggling between two strongly contrasting full-area colors every frame; on the bright LED panel this is fatiguing and reads as a fault
- **MAY** combine motion and color animation (e.g. a traveling specular highlight over a static shape: position **and** value vary with the phase)

### Frame Coherence & Readability

- **MUST** deliver in every frame a **valid pixel-art image** per `ha/pixoo-pixel-art` (consistent light source, contours, shading) — the light direction stays stable across frames even as objects move
- **SHOULD** hold frames **long enough** that the content is readable before the next arrives — at ~1 fps each frame is effectively a briefly held still image
- **SHOULD** avoid **hard, abrupt jumps** between frames (except as a deliberate effect); adjacent frames should differ only gradually
- **SHOULD** close the **loop seamlessly** (last → first frame without a visible jump) when the animation runs continuously

### Delivery Paths (tie-in)

- **MUST** build procedural frames as a `components` page with phase-dependent `position`/`color`; for **per-pixel** animation use a `templatable` component that returns, per frame, a list of pixel components computed from the phase (see `ha/divoom-pixoo` §Components and `ha/pixoo-pixel-art` §Delivery Paths)
- **MUST** for pre-rendered moving images embed a **GIF of exactly 16/32/64 px** via `page_type: gif` — other sizes are not rendered correctly (see `ha/divoom-pixoo`)
- **MAY** use `show_message` for a **one-off, short animation as a push** by sending the page repeatedly with an advancing phase — note: `enabled`/`variables` do not apply in the service (use HA `variables` from the automation)
- **SHOULD** verify the result **on the real device**: actual frame rate, flicker, motion smoothness, and loop transition deviate from the editor/preview

## Acceptance Criteria

- [ ] The animation model is chosen deliberately (procedural / GIF / native) and fits the data dependency
- [ ] A frame driver is set (short `duration` self-driving or `update_page` loop) without excessive spamming; the frame-rate ceiling (~1 fps via rotation) is accounted for
- [ ] A phase variable from a monotonically advancing source (`now()`/`timer`/`counter`) drives frame selection; the loop is formed modulo the frame count
- [ ] Motion is implemented as position=f(phase) on the integer grid; step size matches the frame rate; no "jumping" of the shape; wrapping is seamless
- [ ] Color animation is color=f(phase) **within** the ramps (cycling/pulsing/hue shift, discrete steps); no fatiguing full-area flicker
- [ ] Every frame is a valid pixel-art image per `ha/pixoo-pixel-art` with a stable light direction; frames differ only gradually; the loop closes seamlessly
- [ ] Per-pixel animation uses `templatable` with a phase-computed component list; the GIF path uses exactly 16/32/64 px
- [ ] The animation was verified on the real Pixoo against frame rate, flicker, motion smoothness, and loop transition

## Open Questions

- Is a reusable helper (script/macro) worthwhile that encapsulates an animation as a phase→frame table and standardizes the `update_page` cadence (incl. crash-safe minimum intervals)?
- What practical maximum frame rate does the concrete device sustain over the LAN before the `update_page` cadence causes dropouts/crashes — should a measured guideline be documented in `home-assistant-config`?
- Should a curated set of pre-rendered 64×64 GIFs (instead of procedural) be maintained for recurring moving images, to reduce device load and network traffic?
