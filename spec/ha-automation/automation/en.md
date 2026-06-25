# HA Automation: Using Automation

Status: draft

## Context

The `automation` domain is the rule engine of Home Assistant: it lets HA "automatically respond to things that happen" — such as turning the lights on at sunset. An automation is built from three concepts: **triggers** (what starts it), **conditions** (an optional gate), and **actions** (what runs). It is authored through the visual editor or as YAML; the official docs recommend starting from blueprints.

Unlike helper integrations, automation has **no integration card** in the catalog — it is documented under [`/docs/automation/`](https://www.home-assistant.io/docs/automation/), not under `/integrations/`. Its real classification is a **core configuration domain**, not a connectable device/service. This spec turns the official usage docs into a binding convention for plugin-generated automations and is the root spec of the `ha-automation` corpus: it defines the trigger/condition/action model the helper and sensor specs refer back to.

Verified sources: `/docs/automation/` (+ `basics`, `trigger`, `condition`, `action`, `modes`, `templating`, `yaml`), the action/condition catalogs under `/docs/scripts/` (which the automation docs defer to), and the 2024.10 release blog for the key rename.

## When to Use

Use `automation` whenever Home Assistant should **respond, event-driven, to a state change or an event** without anyone triggering it manually. An automation ties a trigger to an action and is the default building block for reactive behavior. Typical use cases:

- **Reacting to sensors** — turn on a light on motion, notify on an open door or water leak, move a cover based on the sun position
- **Time/sun-driven** — fire actions at a time of day, at sunrise/sunset (with offset), or on a schedule
- **Presence/zone logic** — switch heating, lights, or scenes based on presence and zone enter/leave
- **Threshold monitoring** — act when a measured value crosses a bound (`numeric_state`), optionally with a hold time
- **Event bridge** — react to MQTT messages, webhooks, NFC tags, calendar events, or custom events

An automation is the right tool as soon as a **trigger** should start the flow. For an action sequence invoked manually or repeatedly with no trigger, use a script; for purely derived values, use a template/helper sensor (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the anatomy of an automation (top-level keys, plural syntax) as binding
- Fix the trigger/condition/action model and the run modes as the foundation for high-quality automations
- Enforce deliberate, documented use of `mode`/`max` instead of blindly adopting defaults
- Turn the documented pitfalls (trigger↔condition race, `for` not surviving a restart, silent dropping of runs) into checkable rules
- Clearly delimit when an automation is **not** the right tool and which building block applies instead

## Non-Goals

- The full action/condition catalogs in detail — these live in `ha-automation/script` (script syntax), which HA itself defers to
- Blueprint schema, selectors, and the templating bridge — `ha/blueprint-patterns`
- Device-centric triggers/conditions/actions (backend contract) — `ha/device-automations`
- The naming dimension (`alias`, `id`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Template syntax in general — `/docs/configuration/templating/`, only the automation-specific variables here

## Requirements

### Configuration and Structure

- **MUST** structure a YAML automation through the top-level keys `id`, `alias`, `triggers`, `actions` and — when a gate is needed — `conditions`; `description`, `mode`, `max`, `max_exceeded`, `variables`, `trigger_variables`, `initial_state`, `trace` are optional additions
- **MUST** use the **plural keys** `triggers`/`conditions`/`actions` and, in list items, `trigger:`/`condition:` (the current syntax since 2024.10); the old singular/`platform:` form is non-breaking but new artifacts do not use it
- **MUST** give every generated automation a stable `id` as a snake_case slug (not the volatile UI timestamp) and keep the `alias` English and ≤50 characters (mechanics: `ha/naming-conventions`)
- **SHOULD** choose `mode` deliberately and not blindly adopt the `single` default; justify the choice in the `description` field or a comment when it is not obvious
- **MUST** set an appropriate `max` for `mode: parallel`/`queued` when the expected load can exceed the default (`10`; `1` for `single`)
- **SHOULD NOT** set `max_exceeded: silent` without documenting why — it hides that runs are being dropped

### Triggers, Conditions, Actions, and Run Modes

- **MUST** use at least one trigger from the documented catalog (`state`, `numeric_state`, `time`, `time_pattern`, `template`, `event`, `mqtt`, `sun`, `zone`, `geo_location`, `calendar`, `tag`, `webhook`, `homeassistant`, `persistent_notification`, `conversation`, device triggers); multiple triggers are OR-combined
- **SHOULD** prefer event-driven triggers (`state`, `event`, `mqtt`) over polling `time_pattern` loops when the state change emits an event
- **MUST** account for the fact that a trigger's `for` option **does not survive a restart or reload** (documented limitation) — time-critical hold logic must not rely on it alone
- **MUST** use conditions (AND-combined by default; `and`/`or`/`not` to group) only as a gate, and account for the **race condition** between trigger and condition: conditions see only the current state, not the event that already occurred
- **SHOULD** name triggers via `id` and branch on them in the action part via a `trigger` condition or `choose`/`if`, instead of maintaining several near-identical automations
- **MAY** use the full script syntax in the action part (`action` calls, `delay`, `wait_template`, `wait_for_trigger`, `choose`, `if/then/else`, `repeat`, `parallel`, `stop`, `variables`, `response_variable`) — detailed contract in `ha-automation/script`
- **MAY** use the template variables `this` (own state object), `trigger` (the firing object, incl. `trigger.platform`/`.id`/`.entity_id`/`.to_state`/`.from_state`), and `trigger_variables` in templates

### Delimitation: When NOT to Use

- **MUST NOT** use an automation for a reusable action sequence meant to be invoked multiple times or manually — a **script** (`ha-automation/script`) is the right construct, because it exposes a callable service and is referenceable from several automations
- **SHOULD NOT** use an automation to write a derived/computed value into an `input_number`/`input_text` to store it "as a sensor" — this is fragile and loses the measurement source; instead define a **template/derivative/statistics sensor** (`ha-automation/template`, `ha-automation/derivative`, `ha-automation/statistics`) that derives the value declaratively
- **SHOULD NOT** copy-paste recurring logic across many automations when it is parameterizable — that is what a **blueprint** (`ha/blueprint-patterns`) is for: it encapsulates the logic once and instantiates it many times
- **SHOULD NOT** use a `time_pattern` polling loop where an event/state trigger serves the same purpose — polling adds needless load and reacts with delay
- **MUST NOT** misuse conditions as a substitute for precise triggers (e.g. a broad trigger plus a downstream condition) when a targeted trigger avoids the race condition in the first place
- **SHOULD NOT** prefer device-centric triggers/conditions/actions from the UI editor in generated YAML when an entity/state-based trigger is more portable and installation-independent (background: `ha/device-automations`)

## Acceptance Criteria

- [ ] Every generated automation uses plural syntax (`triggers`/`conditions`/`actions`, `trigger:`/`condition:` in lists)
- [ ] Every automation carries a stable snake_case `id` and an English `alias` ≤50 characters
- [ ] `mode` is set deliberately; for `parallel`/`queued` an appropriate `max` is given
- [ ] `max_exceeded: silent` appears only with a documented justification
- [ ] At least one trigger comes from the documented catalog; event triggers are preferred over polling
- [ ] No time-critical logic relies on the `for` option alone (restart/reload loss accounted for)
- [ ] Conditions are used as a gate and the trigger↔condition race condition is accounted for
- [ ] The "when NOT to use" delimitation holds: no automation where a script, template/derivative sensor, or blueprint is the right tool
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Unavailable/unknown handling**: A cross-cutting rule for guarding against `unavailable`/`unknown` states in trigger/condition templates is not anchored as a dedicated warning across the eight automation doc pages (it lives in the templating/blueprint docs). Should this spec carry its own rule anchored there, or defer to a future `ha-automation/template` rule?
