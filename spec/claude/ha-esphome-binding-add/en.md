# Skill: `ha-esphome-binding-add`

Status: draft

## Context

`spec/ha/esphome-ha-driven-content` was written because the corpus described only one direction — a device publishes, Home Assistant consumes — while the opposite direction left display devices half-configured: the rendering spec requires live values to be staged before drawing, and never said where they come from. That spec names four non-interchangeable mechanisms and makes the choice between them the substance of the work. This skill operationalises exactly that: it decides the mechanism against the spec's rule and then emits the verified configuration for it.

## Scope

One binding per invocation, in one device file or the package that owns the concern. Covers state subscription, callable action, writable entity, return channel, and time synchronisation, plus the boot-state and disconnected-state handling each of them requires.

## Goals

- Make the mechanism choice explicit and rule-driven rather than a copy of whichever example was seen first
- Emit only keys verified against the component page they belong to, across the six-plus pages this axis spans
- Close the two edge states every Home-Assistant-driven value has: before the first value arrives, and after the connection drops
- Keep incoming changes routed through the display's single redraw entry point instead of drawing from a trigger
- Name the Home-Assistant-side identifier and any permission the operator must enable, so the other half of the binding is not left implicit

## Non-Goals

- Rendering — coordinates, pages, fonts (owned by `ha-esphome-display-author`)
- The Assist pipeline's own device interaction (owned by `ha-esphome-voice-satellite-add`)
- Home-Assistant-side automations, scripts, and templates (owned by `ha-automation-solution`)
- MQTT as an alternative transport — the grounding spec assumes the native API
- Compile, flash, and rollout

## Requirements

- **MUST** read `spec/ha/esphome-ha-driven-content/en.md`, the target device file, and its packages before choosing a mechanism
- **MUST** choose per value using the spec's rule — continuously mirrored → subscription, one-shot instruction → callable action, person-set → writable entity, Home Assistant must learn → return channel — and state the choice and its reason in the report
- **MUST NOT** emulate a subscription with a periodically called action, or an action with a rapidly changing subscribed value
- **MUST** emit subscriptions with an explicit `entity_id`, an explicit `internal`, and an `id:`, and **MUST NOT** use `attribute:` on an import platform that has no such key
- **MUST** emit callable actions with typed `variables:`, argument validation, and an `api.respond` answer for a bad call, and **MUST** report the Home-Assistant-side identifier as `esphome.{node_name}_{action_name}` together with the rename consequence
- **MUST** respect the documented exclusions of a writable template text (`optimistic`, `initial_value`, `restore_value` versus `lambda`) and **MUST NOT** transfer them to an unread template platform
- **MUST** name the integration's explicit opt-in as a trust decision whenever the device calls Home Assistant actions
- **MUST** define the boot state and the API-disconnected state, and **MUST** account for `api.reboot_timeout` in the offline design
- **MUST** route every change that must become visible through the display's single redraw entry point
- **MUST** verify every key against the component page it belongs to per `spec/ha/upstream-docs-verification`, and tier a source-derived behaviour as such rather than asserting it as documented
- **MUST NOT** add more than one binding per run, and **MUST NOT** deploy

## Acceptance Criteria

- [ ] The report states the chosen mechanism, the rule that produced it, and the Home-Assistant-side identifier
- [ ] A subscription run emits an explicit `entity_id` and `internal`, and the config defines what is shown before the first value arrives
- [ ] An action run emits typed variables with validation and an `api.respond` path for bad input
- [ ] The disconnected state is defined and `reboot_timeout` is accounted for
- [ ] No emitted trigger draws directly; visible changes call the redraw script

## Open Questions

- The grounding spec's open question on action-name coupling to the node name is inherited rather than answered here: until it is settled, this skill prefers subscriptions and writable entities where the requirement allows either, and reports the coupling whenever it emits an action.
