---
name: ha-esphome-display-author
description: "Authors the on-screen content of an ESPHome display device per spec/ha/esp32-s3-box-display — fixing the rendering path (display with pages and lambdas, or lvgl, never mixed), then emitting a page for every reachable state including the degraded ones, the single redraw script that update_interval: never requires, the layout-zone geometry, fonts with explicit size and bounded glyph sets, images with explicit type and resize in the form matching the config's min_version, id-carrying colours, and lambdas guarded against unavailable values and zero divisors. Records the measured truncation budget and the framebuffer and asset flash cost. Activate on \"design the screen for my ESPHome device\", \"add a page to the box display\", or equivalent German requests. Do not activate for the panel's hardware binding (ha-esphome-config-augment), for where the values come from (ha-esphome-binding-add), for the voice pipeline (ha-esphome-voice-satellite-add), or for a Divoom Pixoo display (ha-pixoo-solution)."
tags: [home-assistant, esphome, display, yaml]
phase: build
summary: "Authors ESPHome display content — rendering path, pages per state, the single redraw script, layout zones, fonts, images, colours, guarded lambdas."
summary_de: "Erstellt ESPHome-Display-Inhalte — Rendering-Pfad, Pages je Zustand, das einzelne Redraw-Skript, Layout-Zonen, Fonts, Bilder, Farben, abgesicherte Lambdas."
use_when:
  - "you want screen content designed for an ESPHome device with a panel"
  - "you want one more page for a device state, including a degraded one"
  - "you want the redraw discipline and layout zones done properly instead of ad-hoc coordinates"
dont_use_when:
  - situation: "You want the panel's hardware binding — SPI pins, model preset, backlight"
    alternative: ha-esphome-config-augment
  - situation: "You want to define where the displayed values come from"
    alternative: ha-esphome-binding-add
  - situation: "You want the voice pipeline that drives the screens"
    alternative: ha-esphome-voice-satellite-add
  - situation: "The display is a Divoom Pixoo 64"
    alternative: ha-pixoo-solution
see_also:
  - ha-esphome-binding-add
  - ha-esphome-voice-satellite-add
  - ha-esphome-config-augment
  - ha-esphome-config-reviewer
  - ha-esphome-solution
---

# HA ESPHome Display Author

Spec: `spec/claude/ha-esphome-display-author/en.md` (EN canonical) / `spec/claude/ha-esphome-display-author/de.md` (DE translation). Grounding specs: `spec/ha/esp32-s3-box-display/en.md` (rendering, canonical for the 320×240 panel) and `spec/ha/esp32-s3-box/en.md` §Display binding (the hardware side, referenced not repeated).

Authors what is on the screen and where — the pages, the redraw discipline, and the geometry — for one display of one device per invocation.

## Why this is a skill, not an agent

- **Mid-flow approval is the contract (decisive):** the rendering-path choice is expensive to reverse (page lambdas and widget trees share no code, so switching later is a rewrite of the whole UI), and the state-to-page mapping is a design conversation, not a derivation.
- **Iterated visual work in the current context:** layouts are adjusted in rounds — a zone moved, a font size dropped, a string truncated — which is main-thread territory.
- **Counter-dimension considered:** the asset and memory budgeting is mechanical enough to isolate (agent bias), but it feeds directly back into the layout decisions being discussed; skill wins.

## When this skill activates

The user wants content on an ESPHome device's panel — "was soll auf dem Display der Box stehen", "add a page for the timer", "design the idle screen" — for a device whose display is already bound.

## When NOT to activate

- the panel's hardware binding (SPI pins, `model:` preset, `invert_colors`, backlight light) → `ha-esphome-config-augment`, taking the values from `spec/ha/esp32-s3-box/en.md`
- where the displayed values come from → `ha-esphome-binding-add`
- the voice-assistant lifecycle that drives the reference screens → `ha-esphome-voice-satellite-add`
- a Divoom Pixoo 64 → `ha-pixoo-solution` (a different device family with its own specs)
- a panel geometry other than 320×240 → the grounding spec's constants are 320×240-specific; state that limit rather than extrapolating

## Hard rules

1. **Read `spec/ha/esp32-s3-box-display/en.md` first**, plus the device file and its packages. Do not generate coordinates, keys, or defaults from memory.
2. **One rendering path per display, recorded in the config, never mixed.** Immediate mode (`display:` + `pages:`) for status devices; `lvgl:` for interactive control surfaces. Under LVGL the display is handed over (`auto_clear_enabled: false`, no display `lambda`, `update_interval: never`) and touch is bound through `touchscreens:`.
3. **`update_interval: never` plus exactly one redraw script.** Every redraw goes through that script; a page lambda never triggers a render, and a page switch is followed by an explicit update.
4. **Every reachable state gets its own page with a stable id** — including initializing, no Wi-Fi, and no Home Assistant — with a `default:` fallback in the state-to-page mapping.
5. **Lambdas render, they do not compute.** State lives in `globals:` or template text sensors; formatting, truncation, and unit handling happen in `on_value` or a script before the render step.
6. **Geometry comes from the zone grid**, with the 20-pixel outer margin, the 10-pixel text inset, and the bottom 15 pixels reserved for the status strip. Centres derive from `it.get_width()` / `it.get_height()` or arithmetic, never from eyeballed offsets.
7. **Anti-aliased text carries an explicit background colour in the right position** — last for `it.print`, fifth for the undocumented `it.printf` overload — and every anchor states its `TextAlign`.
8. **Fonts declare an explicit `size:` and a bounded glyph set**; one face at two sizes is two font components. Images declare an explicit `type:` (there is no `RGBA`) and `resize:`, in the declaration form matching the config's `min_version` — platform form at `2026.7.0` and later, legacy form below, which disappears in `2027.1.0`.
9. **Budget flash and RAM before adding assets.** State the per-pixel cost of the chosen image type against the panel's pixel count and the ~150 KiB framebuffer; on the immediate-mode path `alpha_channel` buys nothing that `chroma_key` does not.
10. **Truncation limits are measured, not computed at render time.** Record a per-project table of font × size × box width → character budget, and bound every variable-length string with a visible ellipsis.
11. **Guard every lambda** against unavailable entities, empty collections, and zero divisors — a fault inside render code surfaces as a frozen screen.
12. **Vendor image assets into the repository**; a build must not depend on an upstream URL staying reachable.
13. **`esphome config` proves nothing about a layout.** Always report on-device verification as the closing step — a layout that renders off-screen validates cleanly.

## Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `device_file` | yes | — | the device YAML whose display is being authored |
| `states` | yes | — | the reachable states, including the degraded ones |
| `rendering_path` | no | asked | `display-pages` or `lvgl`; existing choice in the config wins |
| `assets` | no | none | images and fonts the screens need |
| `theme` | no | derived | per-state background colours, parameterised as substitutions |

## Pre-flight (every run, in order — abort on first failure)

1. Read the device file: confirm the display is bound, read its platform/model, `update_interval`, rotation, and any existing pages, fonts, colours, and redraw script.
2. Determine the rendering path — existing choice, or the operator's decision against the spec's criterion; refuse to mix paths on one display.
3. Enumerate the reachable states with the operator and check that every one, degraded states included, maps to a page.
4. Inventory the assets: which fonts and images exist, their sizes and types, and the flash they already cost.
5. Present the page list, the zone assignment per page, and the asset budget; wait for approval before writing.

## Workflow

1. Verify every rendering API, key, and default against the official ESPHome documentation per `spec/ha/upstream-docs-verification`.
2. Emit or extend the shared furniture first: `color:` components with ids, `font:` components with explicit sizes and glyph sets, `image:` declarations in the correct form, and the reusable drawing scripts for status strip and widgets.
3. Emit the pages — one per state, each opening with an explicit `it.fill(...)`, composed from the zone grid, drawing only already-presentable strings.
4. Emit or extend the single redraw script and the state-to-page mapping (a `globals:` variable switched in exactly one place, with a `default:` branch).
5. Record the truncation table for every new font × box-width combination, and apply the limits in `on_value` rather than in the lambda.
6. Validate with `esphome config <file>` where the toolchain is available; otherwise report it as the open caller step.
7. **Report:** the rendering path and why, the pages written and the states they cover, the zone assignment, new assets with their flash cost, the framebuffer budget, the truncation table, validation status, and the on-device verification that is still owed.

## Boundaries

- Panel hardware binding, touch controller, backlight → `ha-esphome-config-augment` with `spec/ha/esp32-s3-box/en.md`
- The source of the displayed values → `ha-esphome-binding-add`
- The voice-assistant state machine that switches the pages → `ha-esphome-voice-satellite-add`
- A conformance verdict on the result → `ha-esphome-config-reviewer` (independent, read-only)
- Compile, flash, on-device verification → the ESPHome toolchain / operator
