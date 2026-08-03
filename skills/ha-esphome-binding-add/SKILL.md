---
name: ha-esphome-binding-add
description: "Wires one Home-Assistant-driven value or command into an ESPHome device per spec/ha/esphome-ha-driven-content — choosing the mechanism by the spec's rule (continuously mirrored value → state subscription, one-shot instruction → callable action, person-set value → writable template entity, something HA must learn → event or action back), then emitting the verified configuration for it, always defining what the device does before the first value arrives and while the API connection is down, and routing anything visible through the display's single redraw script. Activate on \"show a Home Assistant value on my device\", \"let an automation tell the device to do X\", or equivalent German requests. Do not activate for rendering (ha-esphome-display-author), the voice pipeline (ha-esphome-voice-satellite-add), a local sensor (ha-esphome-config-augment), or HA-side automations (ha-automation-solution)."
tags: [home-assistant, esphome, yaml, integration]
phase: build
summary: "Wires one Home-Assistant-driven value or command into an ESPHome device — subscription, callable action, writable entity, or return channel."
summary_de: "Bindet einen Home-Assistant-getriebenen Wert oder Befehl in ein ESPHome-Gerät ein — Subscription, aufrufbare Action, beschreibbare Entity oder Rückkanal."
use_when:
  - "a Home Assistant entity's value must be mirrored on the device"
  - "an automation should send the device a one-shot instruction with arguments"
  - "a person should set a value on the device from the Home Assistant UI"
  - "the device must fire an event or call an action back into Home Assistant"
dont_use_when:
  - situation: "You want the value drawn on a display"
    alternative: ha-esphome-display-author
  - situation: "You want the voice pipeline bound to the device"
    alternative: ha-esphome-voice-satellite-add
  - situation: "You want a local sensor, bus, or component on the device"
    alternative: ha-esphome-config-augment
  - situation: "You want the Home-Assistant-side automation that drives it"
    alternative: ha-automation-solution
see_also:
  - ha-esphome-display-author
  - ha-esphome-config-augment
  - ha-esphome-config-reviewer
  - ha-automation-solution
  - ha-esphome-solution
---

# HA ESPHome Binding Add

Spec: `spec/claude/ha-esphome-binding-add/en.md` (EN canonical) / `spec/claude/ha-esphome-binding-add/de.md` (DE translation). Grounding spec: `spec/ha/esphome-ha-driven-content/en.md`; rendering of the resulting values is owned by `spec/ha/esp32-s3-box-display/en.md`.

Adds exactly one Home-Assistant-driven binding per invocation, and the mechanism choice is the substance of the run — not the YAML that follows from it.

## Why this is a skill, not an agent

- **Mid-flow approval is the contract (decisive):** the mechanism decision (subscription vs. action vs. writable entity vs. return channel) is made *with* the operator against the spec's rule; picking wrong produces a device that polls what it should have been told, or an automation firing into a device with no receiver — and neither fails loudly.
- **Quick, targeted change in the current context:** one block in one device file or package, iterated in conversation.
- **Counter-dimension considered:** the six documentation pages this spans make the schema lookup self-contained (agent bias), but the boot-state and offline-behaviour decisions belong in the operator's context, not in a report; skill wins.

## When this skill activates

The user wants Home Assistant to drive what an ESPHome device shows or does — "der ESPHome-Node soll den Strompreis anzeigen", "HA should be able to tell the box to show a message", "the button press should reach Home Assistant".

## When NOT to activate

- how the value is *drawn* (pages, zones, fonts, redraw script) → `ha-esphome-display-author`
- the voice pipeline and satellite binding → `ha-esphome-voice-satellite-add`
- a locally measured sensor or a local component → `ha-esphome-config-augment`
- the automation, script, or template on the Home Assistant side → `ha-automation-solution`
- MQTT as an alternative transport → out of scope; the grounding spec assumes the native API

## Hard rules

1. **Read `spec/ha/esphome-ha-driven-content/en.md` first**, then the target device file and its packages. Do not generate a mechanism from memory.
2. **Choose per value, not per device**, using the spec's rule: continuously mirrored → subscription; one-shot instruction with arguments → callable action; person-set → writable entity; Home Assistant must learn something → return channel. State the choice and its reason in the report.
3. **Never emulate one mechanism with another.** A periodically called action is not a subscription, and a rapidly changing subscribed value is not an action — both work briefly and fail under load or disconnection.
4. **Verify every key against the official ESPHome docs** per `spec/ha/upstream-docs-verification` — this axis spans at least six component pages (`api`, `sensor/homeassistant`, `text_sensor/homeassistant`, `time/homeassistant`, `text/template`, and the display components).
5. **Subscriptions are push-based and `internal: true` by default** on every import platform. Set `internal` explicitly for readability, give every subscribed value an `id:`, and use `attribute:` only on the read-only import platforms — `number` and `switch` have no such key.
6. **Actions carry typed `variables:` and validate them**, answering a bad call through `api.respond` with `success: false`. Name the Home-Assistant-side identifier as `esphome.{node_name}_{action_name}` in the report, and state that a device rename breaks every automation calling it.
7. **A writable `text: {platform: template}` respects its documented exclusions:** `optimistic`, `initial_value`, and `restore_value` each cannot be used with `lambda`. Do not carry these rules over to an unread template platform.
8. **A device calling Home Assistant actions needs the integration's explicit opt-in.** Name it as a trust decision the operator has to make, never as a formality.
9. **Define the two edge states, always.** What the device shows or does before the first value has ever arrived, and what it does when the API connection drops (`on_client_connected` / `on_client_disconnected`) — including the consequence of `api.reboot_timeout` (default 15 minutes).
10. **Route anything visible through the single redraw entry point** of the display spec; an `on_value` that draws directly is a finding, not a shortcut.
11. **One binding per run, one device file per run.** No deploy; the run ends at the edited file plus the validation report.

## Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `device_file` | yes | — | the existing device YAML (or the package that owns the concern) |
| `value_or_command` | yes | — | what Home Assistant should drive, in prose |
| `mechanism` | no | derived from the rule | override only with a stated reason |
| `entity_id` | conditional | asked | required for a subscription |
| `redraw_script` | conditional | discovered | required when the value must become visible |

## Pre-flight (every run, in order — abort on first failure)

1. Read the device file and its packages; find the existing redraw entry point, the API block, and any existing bindings.
2. Apply the mechanism rule to the requested value and present the choice with its reason; wait for confirmation.
3. On a subscription: confirm the Home Assistant `entity_id` exists as spelled (and whether an attribute rather than the state is meant).
4. On an action: confirm the argument types and the resulting `esphome.{node_name}_{action_name}` identifier.
5. On a return channel: confirm the trust opt-in is acceptable, and prefer an event over an action where Home Assistant should decide the reaction.

## Workflow

1. Verify the component schema upstream, then emit the block:
   - **subscription** — `sensor` / `text_sensor` / `binary_sensor` (`number` / `switch` where a round trip is genuinely wanted) with `platform: homeassistant`, explicit `entity_id`, explicit `internal`, an `id:`, and an `on_value` that calls the redraw script when the value must be visible.
   - **action** — an `api: actions:` entry with `action:`, typed `variables:`, validation, and `then:`; `api.respond` where the caller needs an answer, `supports_response: only` for a pure query.
   - **writable entity** — `text: {platform: template}` with `set_action`, a deliberate `optimistic` / `restore_value` decision, and the exclusions respected.
   - **return channel** — `homeassistant.event` (preferred where HA decides) or `homeassistant.action` with `data:` / `data_template:` / `variables:`, optionally `capture_response: true` with `on_success:` / `on_error:`.
   - **time** — `time: {platform: homeassistant}` with a deliberate timezone decision, noting the node must be registered in Home Assistant.
2. Add or extend the boot-state and disconnected-state handling; never leave a lambda formatting a value that has not arrived.
3. Validate with `esphome config <file>` where the toolchain is available; otherwise report it as the operator's next step.
4. **Report:** the chosen mechanism and why, the emitted block, the Home-Assistant-side identifier (entity, `esphome.{node}_{action}`, or event name), any permission the operator must enable, the boot/offline behaviour, and validation status.

## Boundaries

- Drawing the value → `ha-esphome-display-author`
- The Home-Assistant-side automation that calls the action or sets the entity → `ha-automation-solution`
- The device's own local sensors and buses → `ha-esphome-config-augment`
- Voice pipeline interaction (`announce`, `start_conversation`) → `ha-esphome-voice-satellite-add`
- Deploy, flash, rollout → the ESPHome toolchain / operator
