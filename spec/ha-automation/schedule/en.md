# HA Automation: Using Schedule

Status: draft

## Context

The `schedule` integration is a helper that exposes a **recurring weekly schedule** as a binary entity. Per weekday, time windows (`from`/`to`) are defined; the entity is `on` while a window is active, otherwise `off`. This makes it the natural tool for "every Monday–Friday 07:00–09:00, X applies" — a declarative, weekly-recurring on/off state.

Its real HA classification is **Helper**. Unlike timer and counter, schedule is **purely configuration-/UI-defined**: there is **no mutating `schedule.*` action** to change the time windows at runtime — only `schedule.reload` (reloads the YAML) and `schedule.get_schedule` (reads the configured ranges). The schedule is maintained in the UI editor or in YAML. The entity carries the `on`/`off` state and the `next_event` attribute (the time of the next state change); per-window `data` values appear as attributes while that window is active.

Verified source: [`/integrations/schedule/`](https://www.home-assistant.io/integrations/schedule/) (weekday keys, `from`/`to`/`data`, states, `next_event`, `schedule.reload`/`get_schedule`, triggers). The trigger/condition/action base model comes from `ha-automation/automation`.

## When to Use

Use `schedule` for a **recurring weekly plan** of fixed `from`/`to` time windows that can be expressed declaratively as an `on`/`off` state. A schedule pays off as soon as "always on these weekdays at these times, X applies" is the question. Typical use cases:

- **Weekly active window** — define Monday–Friday 07:00–09:00 as an `on` window and react to `schedule.turned_on`/`schedule.turned_off`
- **Time gate for automations** — use the `on`/`off` state as a condition to let an automation act only within the plan windows
- **Day-dependent night/quiet hours** — maintain per-weekday differing windows (e.g. later on weekends) declaratively
- **Per-window parameters** — provide values as attributes per window via the `data` mapping (e.g. a target temperature) that are visible only in the active window
- **Display of the next change** — read the `next_event` attribute in a template to show the next state change

A schedule is the right tool as soon as fixed, **weekly-recurring on/off windows** are needed. For a one-off appointment, a countdown, runtime-changeable bounds, or complex calendar logic, another building block is right (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration of a schedule (`name`, `icon`, the weekday keys with `from`/`to`, optional `data`) as binding
- Fix the read contract over the `on`/`off` state and the `next_event` attribute
- Make clear that schedule has **no mutating action** — only `reload`/`get_schedule`
- Anchor the event triggers (`schedule.turned_on`, `schedule.turned_off`) and state triggers as the reaction path
- Clearly delimit when a schedule is **not** the right tool (vs. one-off appointments, vs. countdowns, vs. calendar logic)

## Non-Goals

- The trigger/condition/action base model of automations — `ha-automation/automation`
- The naming dimension (`name`/entity id, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- One-off date/time values — `ha-automation/input-datetime`
- Elapsing time / countdowns — `ha-automation/timer`
- Appointment-/calendar-based triggering — the `calendar` integration

## Requirements

### Configuration

- **MUST** create a YAML schedule under the `schedule:` domain with a snake_case key (the alias that determines the entity id) and a `name`; mechanics of id/`name` assignment: `ha/naming-conventions`
- **MUST** provide, per used weekday (`monday`…`sunday`), a list of windows with the required fields `from` (start time, marks `on`) and `to` (end time, marks `off` again)
- **MAY** set a `data` mapping per window; its keys/values appear as entity attributes while that window is active
- **SHOULD** optionally assign `icon` for the UI; the `name` stays English and ≤50 characters (`ha/naming-conventions`)

### Use in Automations & Templates

- **MUST** treat the schedule as a **read source** — it has no mutating action; at runtime only `schedule.reload` (reload YAML) and `schedule.get_schedule` (read ranges) are available
- **SHOULD** react to the event triggers `schedule.turned_on`/`schedule.turned_off` or a `state` trigger on `on`/`off` instead of polling the state
- **MAY** use the `on`/`off` state as a condition/gate (e.g. "only act when the schedule is currently `on`")
- **MAY** read the `next_event` attribute (next state change) and per-window `data` attributes in templates, e.g. for display or branching

### Delimitation: When NOT to Use

- **MUST NOT** use a schedule for a **one-off appointment** at a fixed date/time — a schedule recurs weekly and knows no date; for a one-off, user-settable time an `input_datetime` plus automation is the right construct
- **MUST NOT** misuse a schedule as a **countdown** — it models recurring wall-clock windows, not an elapsing duration; for "after N minutes" `ha-automation/timer` is responsible
- **SHOULD NOT** represent complex **calendar logic** (holidays, exceptions, one-off appointments, external calendars, "every second Tuesday") in a schedule — a schedule can only do fixed weekly `from`/`to` windows; for appointment-/calendar-based triggering the **`calendar` integration** is the right tool
- **SHOULD NOT** use a schedule for a window meant to be **changed** at runtime by an automation — there is no mutating action; changeable bounds belong in `input_datetime`/`input_number`, which can be set via `set_value`

## Acceptance Criteria

- [ ] Every schedule is created under `schedule:` with a snake_case alias and a `name`; `name` stays English and ≤50 characters (`ha/naming-conventions` referenced)
- [ ] Every used weekday lists windows with `from`/`to`; optional `data` is used only as active attributes
- [ ] The schedule is treated as a read source; no mutating `schedule.*` action is expected (only `reload`/`get_schedule`)
- [ ] Reactions use `schedule.turned_on`/`turned_off` or `state` triggers, not state polling
- [ ] `next_event` and `data` attributes are used read-only
- [ ] No schedule is used for one-off appointments, countdowns, changeable bounds, or complex calendar logic where `input_datetime`, `timer`, or the `calendar` integration is the right tool
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
