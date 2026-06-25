# HA Automation: Using input_datetime

Status: draft

## Context

`input_datetime` is a **helper integration**: it provides a user-settable date and/or time entity, created through the UI or as YAML. Typical uses are a resident-settable alarm time, a start time, or a date that automations react to — not a computed or measured time.

Its real HA classification is **Helper** (`ha_category: Helper`), not a connectable device/service and not a sensor. Quality Scale is **not applicable** here — it is a concept of integration *development*, not of usage.

An `input_datetime` entity needs at least one of its two axes: per the docs, "At least one of `has_time` or `has_date` must be defined." Both together yield a full timestamp; `has_date` alone yields a pure date, `has_time` alone a pure time.

Verified source: [`/integrations/input_datetime/`](https://www.home-assistant.io/integrations/input_datetime/).

## When to Use

Use `input_datetime` for a **user-settable date and/or time** that HA persists and automations react to — not a computed or measured time. Typical use cases:

- **Settable alarm time** — a pure time (`has_time: true`) the resident sets and a `time` trigger references directly (`at: input_datetime.<id>`)
- **Start time/date** — a pure date (`has_date: true`) or a full timestamp (both axes) at which an automation should act
- **User-editable time trigger** — change the time through the entity without touching the automation, so the resident controls the trigger point themselves
- **Programmatic setting** — write the value via `input_datetime.set_datetime` (`date`/`time`/`datetime`/`timestamp`) from an automation
- **Dashboard control** — embed the entity so the resident sets date/time directly, and read the `timestamp` attribute in templates

An `input_datetime` is the right tool as soon as a **fixed, user-editable point in time** is needed. For a recurring weekly schedule, a countdown, or a derived timestamp, another building block applies (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration (`has_date`, `has_time`, `name`, `icon`, `initial`) as binding
- Fix the documented service `input_datetime.set_datetime` and its parameter variants (`date`, `time`, `datetime`, `timestamp`) as the only write path
- Make reading the state and attributes (especially `timestamp`) from automations, scripts, templates, and dashboards reliable
- Use the documented restore behavior (`initial` vs. restoring the last value) deliberately
- Clearly delimit when `input_datetime` is **not** the right tool (schedule, timer, derived time)

## Non-Goals

- The naming dimension (`object_id`, snake_case, English display name, ≤50 chars, ASCII) — `ha/naming-conventions`, only referenced here
- The trigger/condition/action mechanics of the automation itself — `ha-automation/automation`
- Template syntax in general (`strftime`, `as_timestamp`, `as_datetime`) — `/docs/configuration/templating/`, only the integration-specific reading here
- Recurring weekly schedules — `ha-automation/schedule`; countdown/remaining time — `ha-automation/timer`

## Requirements

### Configuration

- **MUST** set at least one of the axes `has_date: true` or `has_time: true` — the docs require: "At least one of `has_time` or `has_date` must be defined."
- **MUST** align the axis choice with the use case: pure date (`has_date: true`), pure time (`has_time: true`), or full timestamp (both `true`) — do not set more axes than are read
- **SHOULD** set `initial` only when a deterministic start value is wanted after every HA start; otherwise omit it so the last set value is restored (see restore behavior)
- **MUST** keep the `object_id` a snake_case slug and the display name English and ≤50 characters (mechanics: `ha/naming-conventions`) — this spec does not repeat the naming rules
- **MAY** set `name` and `icon` for frontend presentation

### Use in Automations & Templates

- **MUST** write the value exclusively through the documented service `input_datetime.set_datetime`, choosing exactly one matching parameter variant: `date` (`"2020-08-24"`), `time` (`"05:30:00"`), `datetime` (`"2020-08-25 05:30:00"`), or `timestamp` (UNIX timestamp)
- **MUST** make the set parameter variant match the configuration: `date`/`datetime` only with `has_date: true`, `time`/`datetime` only with `has_time: true`
- **SHOULD** reference the time directly in triggers — the `time` trigger accepts an `input_datetime` entity (`at: input_datetime.<id>`), so the time stays user-editable without changing the automation
- **SHOULD** read the `timestamp` attribute (present only with `has_time: true`) in templates as the canonical numeric time source and format it with `as_datetime`/`strftime`, instead of parsing the string state
- **MAY** read the `has_date`/`has_time` attribute to query which axes exist; with a pure date the day information (`year`/`month`/`day`) is also available
- **MUST** guard against the `unknown`/`unavailable` states when reading from automations/templates (e.g. immediately after start, before restore) before accessing `timestamp`
- **MAY** embed the entity as a dashboard control so the resident sets date/time directly

### Restore Behavior

- **MUST** account for the documented restore behavior: "If you set a valid value for `initial`, this integration will start with the state set to that value. Otherwise, it will restore the state it had before Home Assistant stopping."
- **SHOULD NOT** set `initial` when the value the resident last set should survive a restart — `initial` overrides the restored value on every start

### Delimitation: When NOT to Use

- **MUST NOT** misuse `input_datetime` as a recurring weekly schedule (e.g. "weekdays 7–9 on/off") — the **`schedule` helper** (`ha-automation/schedule`) is meant for that, mapping periodic on/off windows declaratively instead of reconstructing them from a single point in time
- **MUST NOT** use `input_datetime` as a countdown or remaining-time display — a **`timer`** (`ha-automation/timer`) is the right construct, encapsulating an elapsing duration and emitting a `timer.finished` event; a date/time helper holds a fixed point in time, not a running remaining duration
- **SHOULD NOT** use `input_datetime` to store a **computed or derived** timestamp (e.g. "last door opening", "next sunrise") — it is user-editable and loses its source; instead define a **template/trigger-based sensor** (`ha-automation/template`) with `device_class: timestamp` that derives the point in time declaratively
- **SHOULD NOT** parse the string `state` in templates when `has_time: true` — the documented `timestamp` attribute delivers the same value numerically and timezone-safe
- **MUST NOT** enable more axes than are read (e.g. `has_date` for a pure alarm time) — superfluous axes create attributes and UI fields without purpose and obscure intent

## Acceptance Criteria

- [ ] Every `input_datetime` entity defines at least `has_date: true` or `has_time: true`, and the axis choice fits the use case
- [ ] The value is set exclusively through `input_datetime.set_datetime` with a parameter variant matching the configuration
- [ ] Time triggers reference the entity directly (`at: input_datetime.<id>`) where a user-editable time is required
- [ ] Templates read the `timestamp` attribute (with `has_time: true`) instead of the string state and guard against `unknown`/`unavailable`
- [ ] `initial` is set only when a deterministic start value is wanted; otherwise the restore behavior applies
- [ ] The "when NOT to use" delimitation holds: no `input_datetime` for weekly schedules (→ `schedule`), countdowns (→ `timer`), or derived timestamps (→ template sensor)
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
