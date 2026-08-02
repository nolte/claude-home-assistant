# ESPHome: Home-Assistant-Driven Device Content

Status: draft

## Context

The ESPHome specs in this portfolio describe one direction well: a device publishes entities, and Home Assistant consumes them. The opposite direction — **Home Assistant decides what the device shows or does** — is not covered anywhere. That gap is what makes a display device half-configured: [`ha/esp32-s3-box-display`](../esp32-s3-box-display/en.md) requires live values to be staged in `text_sensor: {platform: template}` or `globals:` before rendering, but never says where those values come from.

ESPHome offers four distinct mechanisms for this, and they are not interchangeable:

1. **State subscription** — the device imports a Home Assistant entity's state through the native API (`platform: homeassistant` on `sensor` and `text_sensor`). Home Assistant changes an entity; the device follows.
2. **Callable actions** — the device declares actions under `api:` that appear in Home Assistant as `esphome.{node_name}_{action_name}` and accept typed arguments. Home Assistant calls; the device acts once.
3. **Writable entities** — the device exposes a `template` **text** entity with a `set_action`, which Home Assistant's frontend can set. Home Assistant writes a value; the device stores and reacts.
4. **Return channel** — the device fires events or calls actions back into Home Assistant (`homeassistant.event`, `homeassistant.action`, `api.respond`).

The choice between them is the substance of this spec: a continuously mirrored value is a subscription, a one-shot command is an action, and a user-settable value is a writable entity. Picking the wrong one produces either a device that polls what it should have been told, or an automation that fires into a device with no receiver.

This spec is device-agnostic and applies to any ESPHome node bound to Home Assistant. Rendering the resulting values is owned by [`ha/esp32-s3-box-display`](../esp32-s3-box-display/en.md); the device's own configuration shape by [`ha/esphome-config-patterns`](../esphome-config-patterns/en.md); repository-level reuse by [`ha/esphome-project-structure`](../esphome-project-structure/en.md).

### Source tiers

- `[doc]` — official documentation, quoted from the page named in the requirement: ESPHome at <https://esphome.io> for device-side keys, Home Assistant at <https://www.home-assistant.io> for the integration's own settings.
- `[policy]` — a nolte-portfolio rule, not an upstream fact.
- `[src]` — behaviour that is real but undocumented, established from the ESPHome source tree ([`esphome/esphome`](https://github.com/esphome/esphome)). Weaker than `[doc]`: it can change without a documentation change.
- **Not stated** — where the documentation is silent, this spec says so rather than inferring.

Verified 2026-08; re-verified 2026-08-02, when the two documentation gaps this spec originally recorded were closed from the source rather than left open. Every YAML key in this spec was read from its component page; nothing here is reproduced from memory.

## Goals

- Close the documented gap between "Home Assistant has the data" and "the device shows it"
- Make the choice between subscription, action, writable entity, and return channel an explicit decision with stated criteria
- Fix the exact configuration surface of each mechanism, quoted from the component documentation
- Connect Home-Assistant-driven values to the redraw discipline the display spec already mandates, so an incoming value does not bypass the single redraw entry point
- Separate what the documentation guarantees from what it merely does not contradict, especially for the update mechanism
- Give the failure case a rule: what the device does while Home Assistant is unreachable

## Non-Goals

- Rendering — coordinates, fonts, layout zones, and page mechanics belong to [`ha/esp32-s3-box-display`](../esp32-s3-box-display/en.md)
- The Home Assistant side of automation authoring (triggers, conditions, scripts) — see the `ha-automation/` corpus
- The Assist pipeline's own device interaction (`announce`, `start_conversation`), which is owned by [`ha/assist-pipeline`](../assist-pipeline/en.md)
- MQTT as an alternative transport — this spec assumes the native API
- Bluetooth-proxy and other pass-through roles a device may also fill

## Requirements

### Choosing a mechanism

- **MUST** choose per value, not per device, using this rule `[policy]`:
  - a value the device must **mirror continuously** (a temperature, a state name, an occupancy flag) → **state subscription**
  - a **one-shot instruction** with arguments ("show this message", "run this sequence") → **callable action**
  - a value a **person should set** from the Home Assistant UI → **writable entity** on the device
  - something Home Assistant must learn about → **return channel**
- **MUST NOT** emulate a subscription with a periodically called action, or an action with a rapidly changing subscribed value — both work briefly and fail under load or disconnection `[policy]`
- **SHOULD** prefer a subscription when Home Assistant already owns the value as an entity: it needs no automation, and the device stays correct after a reboot on either side without anyone re-triggering anything `[policy]`

### Subscribing to Home Assistant state

- **MUST** import a numeric value with `sensor: {platform: homeassistant, entity_id: <entity>}`; `entity_id` is required and `attribute` optionally selects a state attribute instead of the state itself `[doc]`
- **MUST** import a textual value with `text_sensor: {platform: homeassistant, entity_id: <entity>}`, which takes the same `entity_id` and optional `attribute` keys — the sensor platform handles numeric values only `[doc]`
- **MAY** use the other import platforms the component ships, which the documentation covers unevenly: `binary_sensor` for a boolean state, and `number` / `switch` for values the device both reads and writes back. The read-only trio (`sensor`, `text_sensor`, `binary_sensor`) shares `HOME_ASSISTANT_IMPORT_SCHEMA` and therefore supports `attribute:`; `number` and `switch` use `HOME_ASSISTANT_IMPORT_CONTROL_SCHEMA`, which has **no** `attribute` key, so they can bind only to an entity's state `[src]`
- **MUST** know that imported values are **`internal` by default**, documented for the `sensor` platform as being so "to avoid exporting them back to Home Assistant"; set `internal: false` only when a round trip is genuinely wanted `[doc]`
- **MUST** apply that same default to **every** Home Assistant import platform, `text_sensor` included. The documentation states it only for `sensor`, but all of them extend one shared schema, `HOME_ASSISTANT_IMPORT_SCHEMA`, which declares `cv.Optional(CONF_INTERNAL, default=True)` — the default is structurally identical because it is literally the same line of code. Setting `internal:` explicitly remains worthwhile for readability, but no longer to guard against an unknown `[src]` `[doc]`
- **MUST** understand that these subscriptions are **push-based**, even though no component page says so. The device registers each subscription once by sending a `SubscribeHomeAssistantStateResponse` over the native API connection, carrying a `once` flag that distinguishes a one-shot read from a standing subscription; Home Assistant then pushes `HomeAssistantStateResponse` messages, which `APIConnection::on_home_assistant_state_response` dispatches to the registered callbacks. There is no device-side polling loop. The practical consequence: update latency is Home Assistant's, and a value arrives only *after* the API client connects — which is why the boot-state requirement below is not optional `[src]`
- **SHOULD** give every subscribed value an `id:` and consume it in lambdas through that id, so the subscription is the single source and no lambda reaches into Home Assistant conceptually `[policy]`
- **SHOULD** attach `on_value` to a subscribed sensor when a change must become visible, and have that trigger call the display's single redraw script rather than drawing directly `[policy]`

### Actions Home Assistant can call

- **MUST** declare a callable action under `api:` as an entry in `actions:` with an `action:` name and a `then:` block `[doc]`:

  ```yaml
  api:
    actions:
      - action: start_laundry
        then:
          - switch.turn_on: relay
  ```

- **MUST** declare typed `variables:` when the caller passes arguments, and read them in lambdas by name `[doc]`:

  ```yaml
  api:
    actions:
      - action: start_effect
        variables:
          my_brightness: int
          my_effect: string
        then:
          - light.turn_on:
              id: my_light
              brightness: !lambda 'return my_brightness;'
              effect: !lambda 'return my_effect;'
  ```

- **MUST** address the action from Home Assistant as **`esphome.{node_name}_{action_name}`** — the documented example resolves `start_laundry` on node `livingroom` to `esphome.livingroom_start_laundry` `[doc]`
- **MUST** account for the node name being part of that identifier: a device rename changes the action name and breaks every automation calling it, which is one more reason the naming rules in [`ha/esphome-project-structure`](../esphome-project-structure/en.md) treat `name` as stable `[doc]` `[policy]`
- **MAY** return data to the caller with `api.respond`, either as a status (`success: true` / `success: false` with `error_message:`) or as structured data built in a lambda through `root[…]` `[doc]`
- **MAY** declare an action as a pure query with `supports_response: only`, which the documentation shows returning device facts such as `App.get_name()` and `ESPHOME_VERSION` `[doc]`
- **SHOULD** validate arguments inside the action and answer a bad call with `api.respond: {success: false, error_message: …}` rather than acting on nonsense — the documentation's own example does exactly this for a negative number `[doc]` `[policy]`

### Writable entities on the device

- **MAY** let Home Assistant write a value by exposing a `text: {platform: template}` entity with a `set_action`, documented as "the action that should be performed when the remote (like Home Assistant's frontend) requests to set the text value", with the new value available to lambdas as `x` `[doc]`
- **MUST NOT** carry the rules in this section over to the other template platforms (`number`, `select`, `switch`, …) without reading their pages first: only `text/template` was read for this spec, and its documented exclusions are stated for it alone `[policy]`
- **MUST** choose between `optimistic: true` and `set_action` deliberately: optimistic mode means "any command sent to the template text will immediately update the reported state", and the documentation states it **cannot be used with `lambda`** `[doc]`
- **MUST** respect the documented mutual exclusions on a template text: `optimistic`, `initial_value`, and `restore_value` each **cannot be used with `lambda`** `[doc]`
- **SHOULD** set `restore_value: true` where a Home-Assistant-set value must survive a device reboot, and accept that it "saves and loads the state to RTC/Flash" `[doc]` `[policy]`
- **SHOULD** treat a writable entity as the right mechanism only for values a **person** sets; a value an automation computes belongs in a subscription or an action argument `[policy]`

### Return channel

- **MAY** fire an event into Home Assistant's event bus with `homeassistant.event`, naming the event and passing `data:`, `data_template:`, and lambda-computed `variables:` `[doc]`:

  ```yaml
  on_...:
    - homeassistant.event:
        event: esphome.button_pressed
        data:
          message: Button was pressed
  ```

- **MAY** call a Home Assistant action from the device with `homeassistant.action`, passing `data:`, `data_template:`, and `variables:` whose values come from lambdas `[doc]`
- **MAY** capture the result of such a call with `capture_response: true` plus `response_template:`, handling the outcome in `on_success:` / `on_error:` — the documented example reads a forecast temperature back into a lambda `[doc]`
- **SHOULD** prefer an event over an action when Home Assistant should decide what happens: an event carries the fact, an action presumes the reaction `[policy]`
- **MUST** enable the corresponding permission when a device calls Home Assistant actions — the ESPHome integration's setup exposes an explicit opt-in for letting devices perform Home Assistant actions, described there as requiring trust; it is a trust decision, not a formality `[doc]` `[policy]`

### Time from Home Assistant

- **MAY** take the device's clock from Home Assistant with `time: {platform: homeassistant, id: <id>}`, which synchronises over the native API connection `[doc]`
- **MUST** register the node in Home Assistant for this to work — the documentation notes that "this component still requires you to register the node under Home Assistant" even when the device exports nothing `[doc]`
- **SHOULD** decide the timezone deliberately: when it is not set explicitly it is inferred from the build host and then updated from Home Assistant at runtime, whereas setting it explicitly prevents that runtime update `[doc]`

### Redraw and availability

- **MUST** route every Home-Assistant-driven change that must become visible through the display's single redraw entry point, per [`ha/esp32-s3-box-display`](../esp32-s3-box-display/en.md) — an `on_value` that draws directly bypasses the discipline that keeps screen state and application state aligned `[policy]`
- **MUST** define what the device shows before Home Assistant has ever delivered a value: a subscribed sensor has no state at boot, and a lambda that formats it unguarded renders garbage or faults `[policy]`
- **MUST** define what the device shows when the API connection drops. `api:` provides `on_client_connected` / `on_client_disconnected` triggers for exactly this, and the reference configuration in [`ha/esp32-s3-box`](../esp32-s3-box/en.md) uses them to switch to a dedicated screen `[doc]` `[policy]`
- **SHOULD** keep the device usable for what it can do alone while disconnected, rather than freezing the last Home-Assistant-driven frame as though it were current `[policy]`
- **MUST** account for `api.reboot_timeout` (default 15 minutes) when designing offline behaviour: a device with no connected client reboots on that cycle unless the timeout is changed, so "shows the offline screen indefinitely" is not the default behaviour `[doc]` `[policy]`

### Verification

- **MUST** verify every key in this spec against the component page it belongs to before use, per [`ha/upstream-docs-verification`](../upstream-docs-verification/en.md) — the mechanisms here span at least six separate pages (`api`, `sensor/homeassistant`, `text_sensor/homeassistant`, `time/homeassistant`, `text/template`, and the display components) `[policy]`
- **MUST NOT** fill a documentation gap by inference — but **MUST** try the source before declaring one. Both gaps this spec originally recorded (the update mechanism of subscriptions, the `internal` default outside `sensor`) were answerable from `esphome/components/homeassistant/` and `esphome/components/api/` in minutes; neither needed hardware and neither needed an assumption. Where the source settles it, tier the result `[src]` and state it; where even the source is ambiguous, record the gap and write a configuration correct either way `[policy]`
- **SHOULD** confirm an unverified behaviour empirically on the device (log the subscribed value and change the Home Assistant entity) before a configuration depends on it `[policy]`

## Acceptance Criteria

- [ ] Every Home-Assistant-driven value has a chosen mechanism, and the choice matches the rule: continuous → subscription, one-shot → action, person-set → writable entity
- [ ] Subscriptions use `platform: homeassistant` with an explicit `entity_id`, and `attribute` where an attribute rather than the state is meant
- [ ] `internal` is set explicitly on every subscription for readability, in the knowledge that the default is `true` on all import platforms
- [ ] No value is rendered before it has arrived: subscriptions are push-based, so between boot and the first API client there is no value
- [ ] Callable actions declare typed `variables:`, validate them, and answer bad input through `api.respond`
- [ ] Every automation calling a device action uses the `esphome.{node_name}_{action_name}` form, and the consequence of a device rename is understood
- [ ] Writable `text` template entities respect the documented exclusions (`optimistic`, `initial_value`, `restore_value` versus `lambda`), and no rule from that section was applied to an unread template platform
- [ ] Devices calling Home Assistant actions have the corresponding permission deliberately enabled
- [ ] Every incoming change that must be visible goes through the single redraw entry point
- [ ] The device defines a state for "value not yet received" and for "API disconnected", and `reboot_timeout` is accounted for in the offline design
- [ ] Any behaviour the documentation does not state has been confirmed on hardware before being relied upon

## Open Questions

- **Action-name coupling to the node name**: `esphome.{node_name}_{action_name}` binds automations to a device's name. Should the portfolio prefer subscriptions and writable entities over callable actions for that reason, or accept the coupling and treat device renames as a breaking change with a migration step?
- **Round-trip loops**: a subscribed value with `internal: false` is re-exported to Home Assistant. Is there a legitimate use for that in this portfolio, or should it be forbidden outright to rule out feedback loops?

Closed on 2026-08-02 from the ESPHome source, and kept here so the answers stay findable rather than being re-asked at the next reading:

- **Update mechanism of subscriptions** — **push**. The device registers each subscription once via `SubscribeHomeAssistantStateResponse` (whose `once` flag separates a one-shot read from a standing subscription) and Home Assistant pushes `HomeAssistantStateResponse` messages back, dispatched by `APIConnection::on_home_assistant_state_response`. No device-side polling exists. Neither hardware nor an upstream documentation issue was needed.
- **`internal` default outside `sensor`** — **the same, `true`**, and not by coincidence: every import platform extends one shared `HOME_ASSISTANT_IMPORT_SCHEMA` carrying `cv.Optional(CONF_INTERNAL, default=True)`.
- **Binary state** — a `binary_sensor` platform does exist, and so do `number` and `switch`. The read-only platforms share the schema above; `number` and `switch` use `HOME_ASSISTANT_IMPORT_CONTROL_SCHEMA`, which omits `attribute:`.
