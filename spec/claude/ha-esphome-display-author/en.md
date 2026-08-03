# Skill: `ha-esphome-display-author`

Status: draft

## Context

`spec/ha/esp32-s3-box-display` is the largest rendering spec in the ESPHome cluster and had no operationalising artifact: it fixes the rendering-path decision, a layout grid measured from a shipping configuration, the redraw discipline that `update_interval: never` forces, and the asset costs that decide what fits in flash. Those rules are not derivable from the ESPHome component pages — they are the accumulated result of reading a reference configuration closely — which is exactly why generating screen content from memory produces layouts that validate and render wrong.

Its sibling `spec/ha/esp32-s3-box-display-design` supplies the layer that spec explicitly excludes: the palette, type scale, icon scale, and page structure a screen is composed from. This skill operationalises both, because the split is a spec-authoring boundary, not a workflow one — nobody places a page without also choosing its colours and sizes, and letting those be chosen per page is what produces a device where every screen looks like a different product.

## Scope

One display of one device per invocation. Pages, the single redraw script, layout zones, fonts, images, colours, the design system applied to them, and the guards that keep render code from faulting. Both rendering paths are supported; the choice is made once and never mixed, and the design system is identical across both.

## Goals

- Make the rendering-path decision explicit and recorded, in the knowledge that reversing it is a rewrite rather than a refactor
- Give every reachable state — including the degraded ones — a page, so a device never shows a stale frame in place of a problem
- Keep render code pure: state in globals or text sensors, formatting before the render step, guards against everything that can be missing
- Anchor geometry on the spec's zone grid rather than on per-page invention
- Make colour, type, and icon size a lookup against the design system rather than a per-page decision, so a device reads as one product
- Make asset cost a stated number before it becomes a firmware that no longer fits

## Non-Goals

- The panel's hardware binding — SPI pins, model preset, backlight (owned by `ha-esphome-config-augment` with `spec/ha/esp32-s3-box`)
- Where the displayed values come from (owned by `ha-esphome-binding-add`)
- The voice-assistant lifecycle that drives the reference screens (owned by `ha-esphome-voice-satellite-add`)
- Divoom Pixoo displays — a separate device family with its own specs and skills
- Extending the design system itself — a colour role, a type step, or an icon size that does not exist is a change to `spec/ha/esp32-s3-box-display-design`, decided once, not improvised in a run
- Panel geometries other than the one the grounding specs measure

## Requirements

- **MUST** read `spec/ha/esp32-s3-box-display/en.md` and `spec/ha/esp32-s3-box-display-design/en.md` before emitting any coordinate, key, default, colour, or size, and consult `spec/ha/esp32-s3-box/en.md` for the binding it depends on
- **MUST** establish exactly one rendering path per display, record it, and **MUST NOT** mix immediate-mode pages with LVGL on the same display
- **MUST** emit `update_interval: never` with a single redraw script, an explicit update after a page switch, and no redraw triggered from inside a lambda
- **MUST** give every reachable state its own page with a stable id — including initializing, no Wi-Fi, and no Home Assistant — with a default fallback in the state mapping
- **MUST** keep computation, formatting, and truncation out of lambdas, and **MUST** guard lambdas against unavailable values, empty collections, and zero divisors
- **MUST** compose geometry from the spec's zone grid, keep the 20-pixel margin and the 15-pixel status strip, and derive centres arithmetically rather than by eye
- **MUST** pass an explicit background colour for anti-aliased text in the position the chosen overload expects, and state a `TextAlign` on every anchor
- **MUST** declare fonts with an explicit `size:` and a bounded glyph set, and images with an explicit `type:` and `resize:` in the declaration form matching the config's `min_version`
- **MUST** take every colour from the design spec's palette roles and every text size from its four-step scale, and **MUST NOT** emit a hex literal into a lambda or widget or introduce a size outside the scale
- **MUST** source icons from MDI at the sanctioned sizes only, declare monochrome icons as `GRAYSCALE` + `alpha_channel`, and draw them with an explicit foreground **and** the zone's actual background colour
- **MUST NOT** let colour alone distinguish a state — each state also differs in glyph, text, or position — and **MUST** report which second cue carries each state
- **MUST** hold each page to one message in the identity → state → qualifier → system-status hierarchy, and split into a further page rather than shrinking below the scale
- **MUST** state the flash and framebuffer budget for the assets it adds, against the panel's pixel count
- **MUST** record truncation limits as a measured table per font, size, and box width, and apply them before the render step
- **MUST** vendor image assets into the repository rather than referencing an upstream URL at build time
- **MUST** verify every rendering API and key against the official ESPHome documentation per `spec/ha/upstream-docs-verification`
- **MUST** report on-device verification as an owed step, because `esphome config` accepts a layout that renders off-screen

## Acceptance Criteria

- [ ] A run records the rendering path and produces no configuration that mixes the two
- [ ] Every state named in the pre-flight, degraded ones included, has a page and is reachable through the state mapping
- [ ] The emitted lambdas contain no formatting, no business logic, and no unguarded division or entity access
- [ ] Every colour emitted resolves to a palette role and every text size to a scale step; no hex literal reaches a lambda or widget
- [ ] Icons are MDI at 24 / 40 / 96 px, monochrome ones are `GRAYSCALE` + `alpha_channel` drawn with both colour arguments, and no state colour is carried by a duplicated asset
- [ ] The report states the added assets' flash cost, the framebuffer budget, the truncation table, the palette roles and type steps used, the second cue for every colour-distinguished state, and the on-device verification still owed including the dimmed-backlight check

## Open Questions

- The grounding spec's open animation question is inherited: this skill emits multi-frame assets only on an explicit operator decision, and states the per-frame flash cost when it does.
- The design spec's `GRAYSCALE` + `alpha_channel` blending behaviour is `[src]`-tier and contradicted by the ESPHome documentation. This skill emits it as the default icon form; if a future ESPHome release changes that draw path, every recoloured icon becomes a flat block, and the skill's icon rule has to be revisited rather than patched per device.
