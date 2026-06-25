# HA Automation: Using input_select

Status: draft

## Context

`input_select` is a **helper integration**: it provides a user-selectable option list (dropdown) whose current state is one of the predefined options. Typical uses are a mode/preset selector (e.g. "Home/Away/Vacation", "Day/Night/Party") that the resident or an automation switches and that other automations react to.

Its real HA classification is **Helper** (`ha_category: Helper`), not a connectable device/service and not a computed state. Quality Scale is **not applicable** here — it is a concept of integration *development*, not of usage.

An `input_select` entity needs an `options` list per the docs ("List of options to choose from"); the state is always one of those options, and `initial` defines the start value (otherwise the first list element).

Verified source: [`/integrations/input_select/`](https://www.home-assistant.io/integrations/input_select/).

## When to Use

Use `input_select` for a **user-selectable choice from a closed set of named options**, whose current state is always one of those options and that automations react to. Typical use cases:

- **Mode/preset selector** — a house mode like "Home/Away/Vacation" or a scene like "Day/Night/Party" the resident switches manually
- **Branching in the action part** — react to an option change via a `state` trigger and branch on the state in the action part via `choose`/`if`
- **Programmatic setting** — set an option via `input_select.select_option` (with a value contained in `options`) or via `select_next`/`select_previous`/`select_first`/`select_last`
- **Dynamic option list** — replace the list at runtime via `input_select.set_options` from a dynamic source
- **Dashboard dropdown** — embed the entity as a dropdown so the resident selects the option directly

An `input_select` is the right tool as soon as a **user-selectable choice from named, closed options** is needed. For a derived enum, a real device state, an on/off state, or a numeric quantity, another building block applies (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration (`options`, `name`, `icon`, `initial`) as binding
- Fix the documented services (`select_option`, `select_next`, `select_previous`, `select_first`, `select_last`, `set_options`) as the only write paths
- Make reading the state and the `options` list from automations, scripts, templates, and dashboards reliable
- Use the documented restore behavior (`initial` vs. restoring the last value) deliberately
- Clearly delimit when `input_select` is **not** the right tool (derived enum, real device state)

## Non-Goals

- The naming dimension (`object_id`, snake_case, English display name, ≤50 chars, ASCII) — `ha/naming-conventions`, only referenced here; also applies to the option strings
- The trigger/condition/action mechanics of the automation itself — `ha-automation/automation`
- Template syntax in general — `/docs/configuration/templating/`, only the integration-specific reading here
- Template-driven enum states — `ha-automation/template`

## Requirements

### Configuration

- **MUST** define a non-empty `options` list — per the docs "List of options to choose from"; the state is always one of those options
- **SHOULD** treat the `options` as a stable, closed value range and set an `initial` value only when a deterministic start value is wanted after every HA start; otherwise omit it (default is the first element or the restored value)
- **MUST** keep the `object_id` a snake_case slug and the display name English and ≤50 characters (mechanics: `ha/naming-conventions`); the option strings also follow its language/stability rules and carry no volatile data
- **SHOULD NOT** use options that later need renaming via translation or display — an option string is at the same time the state value automations match on
- **MAY** set `name` and `icon` for frontend presentation

### Use in Automations & Templates

- **MUST** set an option exclusively through the documented services: `input_select.select_option` (with `option`), `select_next`/`select_previous` (with optional `cycle`), `select_first`/`select_last` — never write the state "from outside"
- **MUST** pass `input_select.select_option` only an `option` value contained in the configured `options` list
- **SHOULD** react to changes via a `state` trigger on the entity (`to:`/`from:` on an option string) and branch on the state in the action part via `choose`/`if`
- **SHOULD** compare the state directly against an option string in conditions and templates (`states('input_select.<id>')`) instead of assuming substrings or ordering
- **MAY** read the `options` attribute to determine the available values dynamically (e.g. in a template or dashboard logic)
- **MAY** replace the option list at runtime via `input_select.set_options` when it comes from a dynamic source — note that the current state can become invalid if it is no longer contained
- **MUST** guard against the `unknown`/`unavailable` states when reading from automations/templates (e.g. immediately after start, before restore) before branching on the option value
- **MAY** embed the entity as a dashboard dropdown so the resident selects the option directly

### Restore Behavior

- **MUST** account for the documented restore behavior: "If you set a valid value for `initial` this integration will start with the state set to that value. Otherwise, it will restore the state it had before Home Assistant stopping."
- **SHOULD NOT** set `initial` when the option the resident last chose should survive a restart — `initial` overrides the restored value on every start

### Delimitation: When NOT to Use

- **SHOULD NOT** use `input_select` to hold a **computed/derived enum state** (e.g. a "house mode" from several sensors) — it is user-editable and can diverge from the logic; instead define a **template sensor** (`ha-automation/template`) that derives the enum state declaratively from its inputs
- **SHOULD NOT** use `input_select` as a substitute for a **real device state** (e.g. mirroring the fan mode of a climate device) — the helper and the device can drift apart; instead address and read the device's `select`/`climate` entity directly
- **MUST NOT** model a simple on/off or yes/no state as a two-element `input_select` — an **`input_boolean`** (`ha-automation/input-boolean`) is meant for that, bringing toggle semantics and matching UI/service verbs
- **SHOULD NOT** map a numeric, user-settable quantity (e.g. a target brightness) as an option list — an **`input_number`** (`ha-automation/input-number`) is meant for that, providing min/max/step and numeric comparisons
- **SHOULD NOT** rely on the **ordering** of options via `select_next`/`select_previous` as dependable semantics when the use case means a concrete option — `select_option` with an explicit `option` is robust against later list changes

## Acceptance Criteria

- [ ] Every `input_select` entity defines a non-empty `options` list; the state is always one of those options
- [ ] Options are set exclusively through the documented services; `select_option` receives only a value contained in `options`
- [ ] Automations react via a `state` trigger and compare the state directly against an option string
- [ ] Runtime `set_options` accounts for the current state possibly becoming invalid; `unknown`/`unavailable` is guarded when reading
- [ ] `initial` is set only when a deterministic start value is wanted; otherwise the restore behavior applies
- [ ] The "when NOT to use" delimitation holds: no `input_select` for derived enums (→ template sensor), device states (→ device entity), booleans (→ `input_boolean`), or numeric quantities (→ `input_number`)
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
