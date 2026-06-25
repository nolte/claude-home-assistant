# HA Automation: Using input_boolean

Status: draft

## Context

`input_boolean` is a **helper integration** (HA category *Helper*): it provides a user-switchable, binary value whose state is `on` or `off`. Unlike a `binary_sensor`, it measures nothing in the real world — it is a virtual switch that humans flip through the UI and automations flip through actions. Typical uses are manual overrides ("vacation mode on"), feature flags for automations, and gates that let an automation run only when the user has enabled it.

At the configuration level, an `input_boolean` is created either through the UI (Settings → Devices & Services → Helpers) or as YAML under the top-level key `input_boolean`. The integration has a real integration card in the catalog; its real classification is **Helper**, not sensor and not device.

Verified source: [`/integrations/input_boolean/`](https://www.home-assistant.io/integrations/input_boolean/) (config keys `name`/`initial`/`icon`, services `turn_on`/`turn_off`/`toggle`/`reload`, states `on`/`off`, restore behavior). Naming mechanics referenced via `ha/naming-conventions`.

## When to Use

Use `input_boolean` for a **user-switchable on/off state** that HA persists and both humans and automations flip — not a measured real-world true/false state. Typical use cases:

- **Manual override** — a resident-set mode switch like "vacation mode on" or "guest mode" that deliberately suspends normal behavior
- **Automation flag** — a feature flag that enables/disables an automation without changing the automation itself
- **Condition gate** — as a `state` condition (`state: "on"`) let an automation run only when the flag is enabled
- **Reacting to a toggle** — react via a `state` trigger (`to: "on"`) to a manual override by the user
- **Dashboard switch** — make it operable in the frontend as an `entities` row, a `button`/`tile` with a `toggle` action, or an `input_boolean` card

An `input_boolean` is the right tool as soon as a **user-switchable, persistent on/off state** is needed. For a measured state, a one-shot trigger, a callable sequence, or a multi-way selection, another building block applies (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration of an `input_boolean` (keys, restore semantics) as binding
- Fix the correct use as an automation flag, manual override, and condition gate
- Define the exposed services (`turn_on`/`turn_off`/`toggle`) and how the state is read from trigger/condition/template
- Clearly delimit when an `input_boolean` is **not** the right tool and which building block applies instead

## Non-Goals

- The trigger/condition/action model of automation itself — `ha-automation/automation`
- Template syntax in general — `/docs/configuration/templating/`, only the read patterns here
- The naming dimension (`name`, snake_case `object_id`, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Measured true/false real-world states — `binary_sensor` or `ha-automation/template`

## Requirements

### Configuration

- **MUST** structure an `input_boolean` through the top-level key `input_boolean` with at least one object_id; per entry, the keys `name`, `initial`, `icon` are optional (there is no mandatory value key)
- **MUST** keep the `object_id` a snake_case slug and the `name` English and ≤50 characters (mechanics: `ha/naming-conventions`)
- **SHOULD** treat the `initial` key deliberately: if `initial` is set, HA always starts with that value; if `initial` is unset, the state before the stop is restored (and `off` when there is none) — per the docs
- **SHOULD NOT** set `initial` when the user's last chosen state should survive a restart — a hard-set `initial` overrides the restore behavior on every start
- **MAY** set `icon` to label the element in the frontend

### Use in Automations & Templates

- **MUST** read the state as `on`/`off`: in conditions via a `state` condition (`state: "on"`), in triggers via a `state` trigger (`to: "on"`), in templates via `is_state('input_boolean.x', 'on')` or `states('input_boolean.x')`
- **SHOULD** use an `input_boolean` as a **gate condition** to let an automation run only when the flag is enabled, instead of checking the gate in every action separately
- **MUST** use the documented services `input_boolean.turn_on`, `input_boolean.turn_off`, and `input_boolean.toggle` (target via `target.entity_id`) to switch it programmatically; `input_boolean.reload` reloads the YAML helpers
- **MAY** react to an `input_boolean`'s `state` trigger to respond to a manual override by the user
- **MAY** embed the element on a dashboard via an `entities` row, a `button`/`tile` with a `toggle` action, or an `input_boolean` card

### Delimitation: When NOT to Use

- **MUST NOT** use an `input_boolean` to carry a **measured** real-world true/false state (e.g. "door open", "motion detected") — a **`binary_sensor`** or a **template binary sensor** (`ha-automation/template`) is the right construct, because it has a real measurement source and is not user-editable
- **SHOULD NOT** use an `input_boolean` to "store" a **computed/derived** boolean expression that an automation keeps in sync via `turn_on`/`turn_off` — this is fragile (race conditions, drift after restart) and loses the source; instead define a **template binary sensor** that derives the expression declaratively
- **SHOULD NOT** repurpose an `input_boolean` as the trigger for a reusable action sequence (set flag → automation listens) when the sequence should be invocable manually/repeatedly — a **script** (`ha-automation/script`) is the right tool, exposing a callable service
- **SHOULD NOT** use an `input_boolean` as a pure one-shot trigger (a press with no follow-up state) — an **`input_button`** (`ha-automation/input-button`) is the right tool, being stateless and leaving no `off` state behind
- **SHOULD NOT** create several near-identical `input_boolean` helpers for one selectable option (e.g. three booleans for three modes) — an **`input_select`** is the right helper, because it enforces exactly one option

## Acceptance Criteria

- [ ] Every helper is created through the top-level key `input_boolean` with a snake_case `object_id` and an English `name` ≤50 characters
- [ ] `initial` is set only when a fixed start value is wanted; when the state should survive a restart, `initial` stays unset
- [ ] State is read solely as `on`/`off` via `state` trigger/condition or `is_state(...)`/`states(...)`
- [ ] Switching uses `input_boolean.turn_on`/`turn_off`/`toggle` with `target.entity_id`
- [ ] No `input_boolean` carries a measured or computed real-world state (use `binary_sensor`/template sensor)
- [ ] No `input_boolean` replaces an `input_button`, a `script`, or an `input_select`
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
