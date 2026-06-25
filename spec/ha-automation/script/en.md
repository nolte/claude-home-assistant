# HA Automation: Using Script

Status: draft

## Context

The `script` domain wraps a **named sequence of actions** that Home Assistant runs when the script is explicitly called. Unlike an automation, a script has **no trigger**: the official docs make clear that automations trigger automatically, whereas scripts "only execute when explicitly called" and "do not have triggers". The script is therefore the reusable, callable action block of the `ha-automation` corpus that the automation spec refers to from its action part.

A script is authored through the visual editor or as YAML. The `sequence` key (the action list) is required; `alias`, `icon`, `description`, `variables`, `fields`, `mode`, `max`, and `max_exceeded` are optional. Every script appears as a `script.<object_id>` entity with an `on`/`off` state and is at the same time exposed as its own callable service `script.<object_id>`. The action part offers the **full script syntax** (action calls, `delay`, `wait_template`, `wait_for_trigger`, `choose`, `if/then/else`, `repeat`, `parallel`, `stop`, `variables`).

Real classification: the script is a **core configuration domain** (not a connectable device/service) and, although it has an integration card under `/integrations/script/`, it documents its action syntax centrally under `/docs/scripts/` — the same page the automation actions defer to.

Verified sources: [`/integrations/script/`](https://www.home-assistant.io/integrations/script/) (configuration keys, `fields`, modes, calling with variables, `script.turn_on`) and [`/docs/scripts/`](https://www.home-assistant.io/docs/scripts/) (sequence syntax, wait actions, `choose`/`if`/`repeat`/`parallel`/`stop`, `response_variable`, `continue_on_error`, the script variables `repeat`/`wait`/`trigger`).

## When to Use

Use `script` whenever a **reusable, explicitly callable action sequence** is needed — a named block with no trigger of its own, invoked as the service `script.<object_id>` from automations, scripts, and dashboards. Typical use cases:

- **Shared action sequence** — define a multi-step flow (`delay`, `wait_template`, `choose`, `repeat`) once and call it from several automations via `action: script.<object_id>` instead of duplicating it
- **Parameterized action** — offer a public call schema via `fields` with selectors (one script, many callers with different values), e.g. "notify device X with text Y"
- **Manual trigger** — an action sequence started deliberately by a dashboard button, a voice command, or `script.turn_on`, not event-driven
- **Function with a return value** — return a value declaratively via `response_variable`/`stop` to the caller, instead of carrying the result through a detour helper
- **Fire-and-forget flow** — start a long-running flow asynchronously via `script.turn_on` without the caller waiting for completion

A script is the right tool as soon as the logic should be **called** rather than **triggered**. For event-reactive behavior with a trigger, use an automation; for a purely derived value, use a template sensor (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the anatomy of a script (required `sequence`, optional keys) as binding
- Enforce the contract "parameterize via `fields` with selectors instead of hard-wired values"
- Fix the deliberate use of `mode`/`max` and the call semantics (direct vs. `script.turn_on`)
- Anchor the return path via `response_variable`/`stop` as the declarative way to return data
- Clearly delimit when a script is **not** the right tool and which building block applies instead

## Non-Goals

- The trigger/condition/run model of the rule engine — `ha-automation/automation`
- The full action/condition catalog in detail (the data shape of each individual action) — the HA page `/docs/scripts/`, referenced here only as a contract
- Blueprint schema and the `!input` bridge for script blueprints — `ha/blueprint-patterns`
- The naming dimension (`object_id`, `alias`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Template syntax in general — `/docs/configuration/templating/`, only the script-specific variables here

## Requirements

### Configuration and Structure

- **MUST** define every script through the required `sequence` key (a list of actions); `alias`, `icon`, `description`, `variables`, `fields`, `mode`, `max`, `max_exceeded` are optional additions
- **MUST** give the `object_id` (the key under `script:` or the UI name) a snake_case slug with no capital letters and no dashes — the docs explicitly forbid capitals and `-` — and keep the `alias` English and ≤50 characters (mechanics: `ha/naming-conventions`)
- **SHOULD** set `description` so the script is documented legibly in the **Actions** tab
- **SHOULD** choose `mode` deliberately and not blindly adopt the `single` default; justify the choice when it is not obvious (`single` = refuse a new run and warn, `restart` = stop the running run and start over, `queued` = start after all runs complete, `parallel` = start an independent run in parallel)
- **MUST** set an appropriate `max` for `mode: parallel`/`queued` when the expected load can exceed the default (`10`)
- **SHOULD NOT** set `max_exceeded` to `silent` without documenting why — the default `warning` keeps dropped runs visible

### Parameterization via `fields`

- **SHOULD** declare reusable inputs through the `fields` block instead of hard-wiring values into the `sequence`; each field carries at least `name`/`description` and — where useful — `required`, `example`, `default`, and a `selector`
- **SHOULD** give each field an appropriate `selector` so the UI editor renders a type-correct input (per the docs, `selector` controls "how the input is displayed in the frontend")
- **MUST** respect the difference between `fields` and `variables`: `fields` is the **public, documented call schema** for callers (UI metadata), whereas `variables` defines **internal** template variables inside the script — do not conflate the two
- **MAY** derive internal intermediate values via `variables` that are referenced in later actions through `{{ … }}`

### Calling, Returning, and Script Variables

- **MUST** distinguish the two call semantics deliberately: the **direct** call `action: script.<object_id>` **waits** for completion (and aborts on errors), whereas `action: script.turn_on` with `target.entity_id` starts the script **asynchronously** and continues immediately
- **MUST** pass variables consistently per call style: as `data:` keys (the `fields`) for the direct call, and as a nested `data.variables` map for `script.turn_on`
- **SHOULD** return values declaratively via `response_variable` or `stop` with `response_variable`, instead of carrying the result through a detour helper (`input_*`)
- **MAY** use the full script syntax in the action part (`action` calls, `delay`, `wait_template`, `wait_for_trigger`, `choose`, `if/then/else`, `repeat` with `count`/`while`/`until`/`for_each`, `parallel`, `stop`, `event`, `variables`); `continue_on_error` (default `false`) and `continue_on_timeout` (default `true`) control error/timeout behavior
- **MAY** use the documented script variables: `repeat` (`index`/`first`/`last`/`item`) inside loops, `wait` (`completed`/`remaining`/`trigger`) after wait actions, and `trigger` — the latter is **only available when the script runs within an automation**, not on a manual call

### Delimitation: When NOT to Use

- **MUST NOT** use a script where HA should **react to an event** — a script has no trigger and must be invoked; as soon as the logic should be triggered by state/time/event, the **automation** (`ha-automation/automation`) is the right construct
- **SHOULD NOT** copy the same script logic multiple times with hard-wired, slightly differing values — when the sequence is parameterizable, the differences belong in **`fields` with selectors** (one script, many callers) instead of n near-identical scripts
- **SHOULD NOT** misuse a script to compute/store a derived value ("as a sensor") by writing the result into an `input_number`/`input_text` — this loses the measurement source and is fragile; define a **template/derivative/statistics sensor** (`ha-automation/template`, `ha-automation/derivative`, `ha-automation/statistics`) that derives the value declaratively
- **SHOULD NOT** spread identical script logic by copy-paste across many installations or community sharing when it is generically parameterizable — that is what a **script blueprint** (`ha/blueprint-patterns`) is for: it encapsulates the logic once and instantiates it with `!input` inputs
- **SHOULD NOT** use the blocking direct call `script.<object_id>` for a long-running fire-and-forget script when the caller should not wait for completion — use `script.turn_on` instead (conversely: do not use `script.turn_on` when the result or a `response_variable` is needed, because the asynchronous start returns no value to the caller)

## Acceptance Criteria

- [ ] Every script has a required `sequence` block and a snake_case `object_id` with no capitals/dashes
- [ ] The `alias` is English and ≤50 characters; naming mechanics are referenced, not repeated
- [ ] `mode` is set deliberately; for `parallel`/`queued` an appropriate `max` is given; `max_exceeded: silent` only with justification
- [ ] Reusable inputs are declared as `fields` with selectors, not hard-wired
- [ ] `fields` (public call schema) and `variables` (internal template variables) are not conflated
- [ ] The call semantics are chosen deliberately: direct call (waits) vs. `script.turn_on` (asynchronous); variables are passed in the correct shape
- [ ] Return values go through `response_variable`/`stop`, not detour helpers
- [ ] The "when NOT to use" delimitation holds: no event-reactive logic in a script (automation), no derived-sensor substitute, no copy-paste where `fields`/a blueprint applies

## Open Questions

- **Entity attributes**: The integration card `/integrations/script/` does not explicitly enumerate the script entity's runtime attributes (`current`, `last_triggered`, `mode`, `max`) on the page read. Should this spec carry its own rule, anchored to a concrete doc location, for reading `last_triggered`/`current`, or does that stay outside the usage scope?
