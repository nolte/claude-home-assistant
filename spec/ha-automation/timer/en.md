# HA Automation: Using Timer

Status: draft

## Context

The `timer` integration is a helper that exposes a **counting-down countdown** as an entity. A timer is started via an action, counts down a configured duration, and fires an event when it elapses — which makes it the natural tool for "X happens, then after N minutes do Y" without a blocking `delay` in an automation's action part.

Its real HA classification is **Helper** — an auxiliary object created via UI or YAML, not a connectable device. A timer carries a state (`idle`/`active`/`paused`) and attributes (`duration`, `remaining`, `finishes_at`, `restore`, `editable`), is driven by `timer.*` actions, and fires its own events that automations trigger on. Unlike a `delay` or a trigger's `for` option, a timer is a **persistent, observable entity**: several automations can read it, control it, and react to its events.

Verified source: [`/integrations/timer/`](https://www.home-assistant.io/integrations/timer/) (configuration variables, actions, triggers, conditions, states, restart limitation). The trigger/condition/action base model comes from `ha-automation/automation`.

## When to Use

Use `timer` for a **relative, observable countdown duration** that an automation starts and that fires an event when it elapses. A timer pays off as soon as the wait must be readable, controllable, or restart-durable from the outside. Typical use cases:

- **Auto-off after inactivity** — turn a light off after N minutes of no motion, restarted with `timer.start` on each motion and reacting to `timer.finished`
- **Restart-durable delay** — a delay that survives an HA restart (`restore: true`), where a `delay` or the `for` option would be lost
- **Countdown shared across automations** — a timer that several automations read, start, and control via `timer.pause`/`timer.cancel`/`timer.change`
- **Interruptible wait** — a running countdown that can be canceled via `timer.cancel` (without the `timer.finished` event) or extended/shortened via `timer.change` at runtime
- **Remaining-time display** — read the `remaining` and `finishes_at` attributes in a template to show the time left

A timer is the right tool as soon as the duration must be **observable, controllable, or restart-durable**. For just a plain hold condition, an absolute wall-clock time, a recurring schedule, or an event count, another building block is right (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration of a timer (`name`, `duration`, `icon`, `restore`) as binding
- Fix the control contract over the actions `timer.start`/`pause`/`cancel`/`finish`/`change` (incl. the `duration` field)
- Fix the read contract over the state (`idle`/`active`/`paused`) and attributes (`remaining`, `finishes_at`, `restore`)
- Anchor the event triggers (`timer.started`, `timer.finished`, `timer.cancelled`, `timer.paused`, `timer.restarted`) as the preferred reaction path
- Clearly delimit when a timer is **not** the right tool (vs. `for`, vs. a `time` trigger, vs. `schedule`)

## Non-Goals

- The trigger/condition/action base model of automations — `ha-automation/automation`
- Script syntax in the action part (`delay`, `wait_template`, `choose`) — `ha-automation/script`
- The naming dimension (`name`/entity id, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Recurring weekly schedules — `ha-automation/schedule`
- Discrete event counters — `ha-automation/counter`

## Requirements

### Configuration

- **MUST** create a YAML timer under the `timer:` domain with a snake_case key (the alias that determines the entity id); mechanics of id/`name` assignment: `ha/naming-conventions`
- **SHOULD** set a `duration` as the default duration (seconds or the `"00:00:00"` form); if absent, the default is `0` and the timer must supply an explicit `duration` on every start
- **MUST** set `restore: true` when the timer should survive an HA restart — without `restore` (default `false`), active and paused timers are lost on restart
- **SHOULD** assign a `name` (friendly name) and optionally `icon` for the UI display; the `name` stays English and ≤50 characters (`ha/naming-conventions`)
- **MAY** define several timers under `timer:` as sibling entries

### Use in Automations & Templates

- **MUST** control the timer through the documented actions: `timer.start` (starts/restarts, optionally with a different `duration`), `timer.pause`, `timer.cancel` (without firing the `finished` event), `timer.finish` (early, regularly-firing finish), `timer.change` (adds/subtracts `duration` on a running timer)
- **SHOULD** trigger on the event triggers `timer.finished`/`timer.started`/`timer.restarted`/`timer.paused`/`timer.cancelled` instead of polling the state; the firing timer is in the event data `entity_id`
- **MUST** account for the fact that `timer.cancel` fires **no** `timer.finished` event — cancel and elapse logic must not expect the same trigger
- **MAY** read the state (`active`/`idle`/`paused`) and the attributes `remaining` (remaining time) and `finishes_at` (absolute end time) in the action part/template, e.g. to display the remaining time
- **MAY** use the conditions `timer.is_active`/`timer.is_idle`/`timer.is_paused` as a gate
- **MUST** account for the fact that a timer that elapses **while HA was down** does **not** replay the `timer.finished` event after startup (documented limitation) — critical logic that depends on the elapse needs an additional state check at startup

### Delimitation: When NOT to Use

- **SHOULD NOT** use a timer where a plain, in-place hold condition suffices — for "state X holds for N minutes, then act" a `state` trigger's `for` option is simpler; a timer pays off **because** it survives an HA restart (`restore: true`) and is observable/controllable, which `for` is not (background model: `ha-automation/automation`)
- **MUST NOT** misuse a timer for a **fixed wall-clock time** (e.g. "at 22:00") — a timer counts down a relative duration, not an absolute time; use a `time` trigger or an `input_datetime` instead
- **MUST NOT** use a timer as a **recurring scheduler** (repeats daily/weekly) — a timer is a one-shot countdown; for recurring weekly windows `ha-automation/schedule` is the right construct
- **SHOULD NOT** repurpose a timer as a **counter of discrete events** — that is what `ha-automation/counter` is for; a timer models elapsing time, not an event count
- **SHOULD NOT** replace a blocking `delay` in the action part with a timer when the wait is short and no other automation needs to observe or interrupt the elapse — a timer only pays off once observability, restart durability, or external control (`pause`/`cancel`/`change`) is needed

## Acceptance Criteria

- [ ] Every timer is created under `timer:` with a snake_case alias; `name` stays English and ≤50 characters (`ha/naming-conventions` referenced)
- [ ] `restore: true` is set when the timer should survive a restart
- [ ] Control happens exclusively through `timer.start`/`pause`/`cancel`/`finish`/`change`
- [ ] Reactions use the event triggers (`timer.finished` etc.), not state polling
- [ ] Cancel vs. elapse logic distinguishes `timer.cancel` (no `finished` event) from a regular elapse
- [ ] Critical logic that depends on the elapse accounts for the fact that a timer elapsed while HA was down fires no retroactive `finished` event
- [ ] No timer is used instead of `for`, a `time` trigger/`input_datetime`, `schedule`, or `counter` where those are the right tool
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
