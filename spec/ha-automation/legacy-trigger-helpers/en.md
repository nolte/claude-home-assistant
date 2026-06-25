# HA Automation: Avoiding Legacy Trigger Helpers

Status: draft

## Context

Under the HA **Automation** category sits a cluster of integrations that appear as domain slugs — `door`, `garage_door`, `gate`, `window`, `humidity`, `illuminance`, `moisture`, `motion`, `occupancy`, `power`, `temperature` — plus the older automation helpers `flux`, `device_sun_light_trigger`, and the automation role of `hdmi_cec`. This collective spec is a **delimitation spec**: it does not teach usage but binds which parts of this cluster should be **avoided** in new artifacts and what to use instead.

Verification against the official docs corrects a common assumption: the device-class slugs (`door`, `motion`, `temperature`, …) are **no longer** the thin pre-`device_automation` helpers of the past. According to the current integration cards they were **introduced in Home Assistant 2026.4** and provide "dedicated triggers and conditions" for entities of a given `device_class` — UI-configurable, with no YAML configuration (`door`: "provides automation triggers and conditions for entities that represent doors"; `temperature`: "provides automation triggers and conditions for climate, water heater, and weather entities, as well as sensors with device class temperature", with the triggers "Temperature changed" / "Temperature crossed threshold"). This modern device-class layer is **not** a target for avoidance — it is a recommended alternative.

The actually-to-be-avoided legacy building blocks in this cluster are the **old YAML automation helpers**: `flux` (a `switch` platform helper with `platform: flux` that computes light color temperature/brightness by time of day "similar to the way flux works on your computer", IoT class "Calculated"), `device_sun_light_trigger` (a presence-based light helper: "Fade in the lights when the sun is setting and there are people home … Turn off the lights when all people leave the house", categories Automation/Light/Presence detection), and the automation role of `hdmi_cec` (marked **"Legacy integration"** on its card). These helpers predate blueprints and the modern device-class layer; their logic is wired into `configuration.yaml`, is not UI-editable, and is not shareable as a blueprint.

Real classification / category honesty: HA lists the whole cluster under the **Automation** category. That is not a homogeneous unit, however — it splits into a **modern device-class trigger/condition layer (2026.4, recommended)** and a **remainder of genuine legacy automation helpers (to be avoided)**. This spec makes the split explicit so authors do not accidentally take the legacy path.

Verified sources: `/integrations/motion/`, `/integrations/door/`, `/integrations/garage_door/`, `/integrations/gate/`, `/integrations/window/`, `/integrations/occupancy/`, `/integrations/humidity/`, `/integrations/illuminance/`, `/integrations/moisture/`, `/integrations/power/`, `/integrations/temperature/`, `/integrations/flux/`, `/integrations/device_sun_light_trigger/`, `/integrations/hdmi_cec/`, and `/docs/automation/trigger/` for `state`/`numeric_state`/`sun`.

## When to Use

Consult `ha-automation/legacy-trigger-helpers` whenever you are about to build trigger/light/presence logic in the **Automation** cluster and must decide whether the modern or the legacy path applies — this spec binds what to avoid and which modern alternative to use instead. Typical decision situations:

- **Adding a device-class trigger** — you want to react to motion, a door/window, or a temperature threshold; this spec points to the modern 2026.4 device-class layer (`door`, `motion`, `temperature`, …) instead of a hand-built `platform:` helper
- **Considering f.lux-style light control** — you are eyeing `flux` for circadian/color-temperature control; this spec points instead to a `sun`-triggered automation calling `light.turn_on` (`color_temp_kelvin`/`brightness`) or an adaptive-lighting solution
- **Considering presence-based light logic** — you are eyeing `device_sun_light_trigger` for "lights on when people are home and the sun sets"; this spec points to an explicit `sun`-triggered automation with a person/`device_tracker` condition
- **Telling modern from legacy** — you see an integration under the **Automation** category and must separate the modern device-class layer from genuine legacy (`flux`, `device_sun_light_trigger`, the `hdmi_cec` automation role)
- **Evaluating the `hdmi_cec` automation** — you are considering the automation role of `hdmi_cec`; this spec flags it as a "Legacy integration" and points to the devices' `media_player` entities/services
- **Bridging a missing device-class source** — you want to write a derived value into an `input_number`/`input_text`; this spec points to a `template` sensor with a set `device_class`

So consult this spec before authoring any new artifact in the Automation cluster — the negative prohibitions and their justifications live in `### Delimitation: When NOT to Use`.

## Goals

- Provide a single authoritative "don't use — use X instead" reference for this cluster
- Establish category honesty: separate what is modern (the 2026.4 device-class layer) from what is genuine legacy (the old YAML helpers)
- For each legacy building block, name the modern alternative **and** the justification (not UI-configurable, opaque, superseded, not portable)
- Prevent generated artifacts from accidentally introducing `flux`, `device_sun_light_trigger`, or the `hdmi_cec` automation role
- Explicitly protect the modern device-class layer as a permitted alternative rather than discarding it along with the rest

## Non-Goals

- Detailed usage of the modern device-class triggers/conditions — that belongs to the respective integration or `ha-automation/automation`
- The full trigger/condition/action model — `ha-automation/automation`
- Device-centric triggers/conditions/actions (backend contract, the `device_automation` platform) — `ha/device-automations`
- Template sensors and the `template` trigger in detail — `ha-automation/template`
- The naming dimension (snake_case `id`, English `alias`, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Migration of existing production `flux`/`device_sun_light_trigger` setups (maintaining what exists stays allowed) — this spec governs **new** artifacts

## Requirements

### What These Integrations Are

- **MUST** understand the device-class slugs (`door`, `garage_door`, `gate`, `window`, `humidity`, `illuminance`, `moisture`, `motion`, `occupancy`, `power`, `temperature`) as the **modern trigger/condition layer introduced in 2026.4** over a `device_class` — per the docs they have **no configuration options** and become available automatically once another integration provides matching entities
- **MUST** classify `flux` as an old `switch` platform helper (`platform: flux`, YAML in `configuration.yaml`, IoT class "Calculated") that computes light color temperature/brightness by time of day
- **MUST** classify `device_sun_light_trigger` as a presence-based light helper that switches lights based on `device_group`/persons and sun position (keys including `light_group`, `device_group`, `light_profile`, `disable_turn_off`)
- **MUST** treat the automation role of `hdmi_cec` as a **"Legacy integration"** as flagged on the integration card
- **SHOULD NOT** infer from the shared "Automation" category label that all cluster members are equivalent or equally modern

### Modern Alternatives

- **SHOULD** use the cluster's modern **device-class trigger/condition layer** for reactive logic where it fits (e.g. "Motion detected"/"Motion cleared", "Temperature crossed threshold") — it is UI-configurable and bound to the `device_class` rather than to a concrete entity ID
- **MUST** use a documented core trigger where the device-class layer does not apply: `state` for discrete states, `numeric_state` (with `above`/`below`/`for`) for thresholds, `sun` (`event: sunset`/`sunrise`, `offset`) for sun-position logic (`ha-automation/automation`)
- **SHOULD** encapsulate reusable, parameterized trigger logic as a **blueprint** (`ha/blueprint-patterns`) instead of as a built-in YAML helper
- **SHOULD** model derived numeric quantities via a **template sensor** with a set `device_class` (`ha-automation/template`) when no native device-class source exists
- **SHOULD** use modern means for f.lux-style light control: an explicit automation with a `sun` trigger that calls `light.turn_on` with `color_temp_kelvin`/`brightness`, or an established adaptive-lighting solution — not the `flux` switch

### Delimitation: When NOT to Use

- **MUST NOT** hand-build an old `platform:`/`switch` helper in new YAML that reproduces what the modern device-class layer (`door`, `motion`, `temperature`, …) or a `state`/`numeric_state` trigger already does — **because** such a helper is not UI-configurable, is wired to a concrete entity, and is not shareable as a blueprint; use the device-class triggers/conditions, a `state`/`numeric_state` trigger, or a `template` binary sensor with `device_class` instead
- **MUST NOT** introduce `flux` (`platform: flux`) in new setups — **because** it wires its entire circadian logic opaquely into `configuration.yaml`, is not UI-editable, and has been superseded by declarative means; use an adaptive-lighting solution or a `sun`-triggered automation that calls `light.turn_on` with `color_temp_kelvin`/`brightness` (modern `light` color-temperature control) instead
- **MUST NOT** introduce `device_sun_light_trigger` in new setups — **because** its presence-and-sun light logic is hard-wired, not parameterizable, and not portable; use an **explicit automation** with a `sun` trigger (and, where needed, a person/`device_tracker` condition) that performs the desired `light` actions instead — visible, editable, and shareable as a blueprint
- **SHOULD NOT** choose the automation role of `hdmi_cec` as the preferred automation path — **because** the integration is flagged as a "Legacy integration" on its own card; prefer the devices' `media_player` entities/services where possible and encapsulate special cases in an explicit automation
- **SHOULD NOT** misread the shared category slug as an endorsement and equate the old YAML helpers (`flux`, `device_sun_light_trigger`) with the modern device-class layer — **because** while both sit under "Automation", they are different generations; use the 2026.4 device-class layer as the modern path
- **SHOULD NOT** have an automation write a derived value into an `input_number`/`input_text` to fake a missing device-class source — **because** that loses the measurement source; define a `template` sensor with a fitting `device_class` (`ha-automation/template`) instead

## Acceptance Criteria

- [ ] No generated artifact introduces `flux` (`platform: flux`)
- [ ] No generated artifact introduces `device_sun_light_trigger`; presence-/sun-based light logic is implemented as an explicit `sun`-triggered automation
- [ ] f.lux-style color-temperature control uses `light.turn_on` with `color_temp_kelvin`/`brightness` or an adaptive-lighting solution, not the `flux` switch
- [ ] The automation role of `hdmi_cec` is chosen only as a deliberately justified legacy path, otherwise replaced via `media_player` means
- [ ] Reactive device-class logic uses the modern 2026.4 trigger/condition layer or a `state`/`numeric_state`/`sun` trigger instead of a hand-built `platform:` helper
- [ ] Derived quantities without a native source are modeled as a `template` sensor with `device_class`, not written into `input_*`
- [ ] The spec does not wrongly equate the modern device-class layer with the old YAML helpers (category honesty preserved)
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Adaptive-lighting recommendation**: The official HA docs name no concrete adaptive-lighting custom integration as a successor to `flux`. Should this spec recommend a specific (third-party) solution, or stay with the generic "`sun`-triggered automation + `light.turn_on color_temp_kelvin`" formulation, which is fully doc-anchored?
- **Existing-setup migration**: Should a follow-up rule/spec normalize the migration path from existing `flux`/`device_sun_light_trigger` setups toward explicit automations/blueprints, or does this spec stay scoped to the prohibition in **new** artifacts?
