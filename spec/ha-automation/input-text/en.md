# HA Automation: Using input_text

Status: draft

## Context

`input_text` is a **helper integration**: it provides a user-settable free-text field, created through the UI or as YAML. Typical uses are a short resident-editable note, a display/status string, or a small value set by automations (e.g. a last-scanned identifier).

Its real HA classification is **Helper** (`ha_category: Helper`), not a connectable device/service and not a derived sensor. Quality Scale is **not applicable** here — it is a concept of integration *development*, not of usage.

The state is the text value itself. The docs set limits for the field: `min` (default `0`) and `max` (default `100`) bound the length, `pattern` allows client-side regex validation, and `mode` (`text` or `password`) controls the input presentation. The general HA state limit applies: "255 is the maximum number of characters allowed in an entity state".

Verified source: [`/integrations/input_text/`](https://www.home-assistant.io/integrations/input_text/).

## When to Use

Use `input_text` for a **short, user-settable free-text value** (≤255 characters) that HA persists and automations read — not a large store, not a secret, not a derived value. Typical use cases:

- **Editable note** — a short resident-set note or a display/status string on a dashboard
- **Value set by automations** — a small string an automation sets via `input_text.set_value` (e.g. a last-scanned identifier)
- **Reacting to a value change** — react via a `state` trigger to a change and compare the state directly as a string in conditions/templates (`states('input_text.<id>')`)
- **Validated/masked input** — use `min`/`max` and (client-side) `pattern` to bound length/format, `mode: password` for display masking
- **Dashboard text input** — embed the entity as a text input so the resident sets the value directly

An `input_text` is the right tool as soon as a **short, user-settable free text** is needed. For a large/structured store, secrets, a derived value, or a typed value (number/boolean/selection), another building block applies (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML/UI configuration (`name`, `min`, `max`, `initial`, `icon`, `pattern`, `mode`) as binding
- Fix the documented service `input_text.set_value` (with `value`) as the only write path
- Make reading the text state from automations, scripts, templates, and dashboards reliable
- Use the documented restore behavior (`initial` vs. restoring the last value) deliberately
- Clearly delimit when `input_text` is **not** the right tool (large store, secrets, derived values)

## Non-Goals

- The naming dimension (`object_id`, snake_case, English display name, ≤50 chars, ASCII) — `ha/naming-conventions`, only referenced here
- The trigger/condition/action mechanics of the automation itself — `ha-automation/automation`
- Template syntax in general — `/docs/configuration/templating/`, only the integration-specific reading here
- Template-driven text states — `ha-automation/template`

## Requirements

### Configuration

- **SHOULD** set `min` and `max` deliberately for the use case (defaults `min: 0`, `max: 100`) and never push `max` past the HA state limit — per the docs: "255 is the maximum number of characters allowed in an entity state"
- **MAY** set `pattern` as client-side regex validation; the docs call it "Regex pattern for client-side validation" — it is a UI aid, not a server-side enforcement, so do not treat it as a security/integrity boundary
- **SHOULD** set `mode: password` when the value should be masked in the UI — this only hides the display; the state is still stored in clear text and is not a secret store (see delimitation)
- **SHOULD** set `initial` only when a deterministic start value is wanted after every HA start; otherwise omit it so the last set value is restored
- **MUST** keep the `object_id` a snake_case slug and the display name English and ≤50 characters (mechanics: `ha/naming-conventions`) — this spec does not repeat the naming rules
- **MAY** set `name` and `icon` for frontend presentation

### Use in Automations & Templates

- **MUST** write the value exclusively through the documented service `input_text.set_value` (parameter `value`) — "Sets the value of an input text"
- **MUST** ensure a written `value` lies within `min`/`max` and (if set) `pattern`, since otherwise the server-side write fails or validation takes effect
- **SHOULD** react to value changes via a `state` trigger on the entity and compare the state directly as a string in conditions/templates (`states('input_text.<id>')`)
- **MAY** read the `min`, `max`, `pattern`, `mode` attributes to query the limits or mode dynamically
- **MUST** guard against the `unknown`/`unavailable` states as well as the empty string when reading from automations/templates (e.g. immediately after start, before restore) before processing the value
- **MAY** embed the entity as a dashboard text input so the resident sets the value directly

### Restore Behavior

- **MUST** account for the documented restore behavior: "If you set a valid value for `initial` this integration will start with state set to that value. Otherwise, it will restore the state it had before Home Assistant stopping."
- **SHOULD NOT** set `initial` when the value the resident last entered should survive a restart — `initial` overrides the restored value on every start

### Delimitation: When NOT to Use

- **MUST NOT** misuse `input_text` as a general data store or large state store — the HA state limit of 255 characters makes it unsuitable; structured or larger data belongs in a dedicated storage medium (file, external DB, add-on), not in a state
- **MUST NOT** use `input_text` for **secrets** (API keys, passwords, tokens) — the state is held in clear text, visible in history/logbook, and retrievable via the API; `mode: password` only masks the display. Secrets belong in `secrets.yaml` or the respective intended configuration/credentials mechanism
- **SHOULD NOT** use `input_text` to store a **computed/derived** string value (e.g. a formatted status line from several sensors) — it is user-editable and lags its source; instead define a **template sensor** (`ha-automation/template`) that derives the string declaratively
- **SHOULD NOT** use `input_text` as a substitute for typed helpers when the value is really a number, a boolean, or a closed selection — then an **`input_number`**, **`input_boolean`**, or **`input_select`** (`ha-automation/input-number`, `…/input-boolean`, `…/input-select`) is right, bringing validation and matching comparisons
- **MUST NOT** rely on `pattern` as a dependable integrity/security barrier — the docs explicitly call it "client-side validation"; a value set via service can bypass it, so secure the validation in the writing automation

## Acceptance Criteria

- [ ] `min`/`max` are set deliberately and never exceed the HA state limit of 255 characters
- [ ] The value is set exclusively through `input_text.set_value` and lies within `min`/`max`/`pattern`
- [ ] Automations react via a `state` trigger; templates guard against `unknown`/`unavailable` and the empty string
- [ ] `mode: password` is used only for display masking, never as a secret store
- [ ] `initial` is set only when a deterministic start value is wanted; otherwise the restore behavior applies
- [ ] The "when NOT to use" delimitation holds: no `input_text` as a large store, for secrets, for derived values (→ template sensor), or as a substitute for typed helpers
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
