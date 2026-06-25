# HA Automation: Using input_button

Status: draft

## Context

`input_button` is a **helper integration** (HA category *Helper*): it provides a **stateless button** that is "pressed" by user interaction in the UI or by an action. It has no `on`/`off` state — the state of an `input_button` entity is, per the docs, a **timestamp** of the last press. Its sole purpose is to emit a trigger pulse that automations react to.

At the configuration level, an `input_button` is created through the UI (Settings → Devices & Services → Helpers) or as YAML under the top-level key `input_button`. The integration has a real integration card; its real classification is **Helper**. Typical use: a manual "run now" button on a dashboard that starts an automation without any follow-up state to manage.

Verified source: [`/integrations/input_button/`](https://www.home-assistant.io/integrations/input_button/) (config keys `name`/`icon`, services `press`/`reload`, state = timestamp of last press, `state` trigger example). Naming mechanics referenced via `ha/naming-conventions`.

## When to Use

Use `input_button` for a **manual, UI-driven trigger pulse** with no follow-up state — a stateless button that kicks off an automation or a script. Typical use cases:

- **"Run now" button** — a dashboard button that manually starts an automation or script without any switch state to manage
- **Reacting via a `state` trigger** — react to the press because the timestamp changes (without a `to`/`from` check)
- **Programmatic triggering** — press the button via `input_button.press` from another automation or a script
- **Dashboard operation** — make it manually triggerable as a `button`/`tile` with an `input_button.press` action or an `entities` row
- **"Last pressed" display** — read the timestamp in a template/trigger context to show the last press

An `input_button` is the right tool as soon as a **manual pulse** with no follow-up state to store is needed. For a persistent state, a reusable sequence, a real event trigger, or an option selection, another building block applies (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration of an `input_button` (keys, statelessness) as binding
- Fix the correct use as a manual UI trigger that kicks off an automation or script
- Define the exposed service (`input_button.press`) and triggering via a `state` trigger
- Clearly delimit when an `input_button` is **not** the right tool and which building block applies instead

## Non-Goals

- The trigger/condition/action model of automation itself — `ha-automation/automation`
- Template syntax in general — `/docs/configuration/templating/`, only the trigger pattern here
- The naming dimension (`name`, snake_case `object_id`, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Persistent switch or value state — `input_boolean` (`ha-automation/input-boolean`) or `input_number` (`ha-automation/input-number`)

## Requirements

### Configuration

- **MUST** structure an `input_button` through the top-level key `input_button` with at least one object_id; per entry, the keys `name` and `icon` are optional (there is no value/initial-state key)
- **MUST** keep the `object_id` a snake_case slug and the `name` English and ≤50 characters (mechanics: `ha/naming-conventions`)
- **MUST NOT** expect an `initial` or value key — the `input_button` is stateless; its state is solely the timestamp of the last press and does not survive a restart as a meaningful value
- **MAY** set `icon` to label the element in the frontend

### Use in Automations & Templates

- **MUST** react to a press via a **`state` trigger** on the entity (per the doc example `trigger: state` / `entity_id: input_button.x`) — the trigger fires because the timestamp changes; a `to`/`from` is not required
- **SHOULD NOT** check for a specific state **value** of an `input_button` (it is only a changing timestamp) — the transition itself is the signal
- **MUST** use the documented service `input_button.press` (target via `target.entity_id`) to trigger it programmatically; `input_button.reload` reloads the YAML helpers
- **MAY** embed the element on a dashboard via a `button`/`tile` with an `input_button.press` action or an `entities` row, to make it manually triggerable
- **MAY** read the timestamp as "last pressed at" in a template/trigger context when displaying the last press is wanted

### Delimitation: When NOT to Use

- **MUST NOT** use an `input_button` to **store** a state (on/off, a value) — it is stateless and keeps only a timestamp; for a persistent switch state use an **`input_boolean`** (`ha-automation/input-boolean`), for a numeric value an **`input_number`** (`ha-automation/input-number`)
- **SHOULD NOT** mistake an `input_button` for a carrier of a reusable action **sequence** — the button has no `sequence`; it only fires a trigger. When the sequence should be callable from several places, it belongs in a **script** (`ha-automation/script`) that exposes a callable service; the button can then kick off the script
- **SHOULD NOT** introduce an `input_button` where the automation is already triggered by a real event (sensor, time, state change) — the dedicated trigger (`ha-automation/automation`) is more direct; an `input_button` is only for **manual/UI-driven** invocation
- **SHOULD NOT** create several `input_button` helpers as a disguised option selection (one button per value) to set a parameter — an **`input_select`** or an **`input_number`** is the right construct, because it actually holds the chosen value

## Acceptance Criteria

- [ ] Every helper is created through the top-level key `input_button` with a snake_case `object_id` and an English `name` ≤50 characters
- [ ] No `initial`/value key is used; statelessness is respected
- [ ] Reacting to a press uses a `state` trigger without checking a specific state value
- [ ] Programmatic triggering uses `input_button.press` with `target.entity_id`
- [ ] No `input_button` stores a switch or numeric value (use `input_boolean`/`input_number`)
- [ ] No `input_button` replaces a `script` (no `sequence`) or an `input_select`/`input_number` selection
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
