# HA Automation: Using Python Script

Status: draft

## Context

The `python_script` integration lets you run small Python files as callable actions. Every `.py` file in the `<config>/python_scripts/` folder is automatically exposed as a `python_script.<filename>` action and can be invoked from automations and scripts. The integration is enabled by the empty `python_script:` entry in `configuration.yaml`.

Execution runs in a **heavily restricted sandbox**: only the prepared objects `hass`, `data`, `logger`, `output` (plus limited `time`, `datetime`, `dt_util`, and builtins such as `min`/`max`) are available. **`import` is not possible** — the docs state explicitly: "It is not possible to use Python imports with this integration." `hass` is also trimmed: "Access is only allowed to perform actions, set/remove states and fire events." So `python_script` is not a full Python interpreter but a tightly bounded escape hatch for the few cases where the declarative script/template syntax is not enough.

Real classification: `python_script` is an **advanced configuration/helper integration** with an integration card under `/integrations/python_script/`, but no connectable device/service. Within the `ha-automation` corpus it is the last resort, not the default tool: the official docs themselves advise using it only where declarative means fall short.

Verified source: [`/integrations/python_script/`](https://www.home-assistant.io/integrations/python_script/) (enabling, the `python_scripts/` folder, the sandbox objects `hass`/`data`/`logger`/`output`, the import ban, `response_variable`, `services.yaml`).

## When to Use

Use `python_script` as a **last resort** for the few cases where the declarative script/template syntax is not enough and a short, import-free Python logic in the sandbox suffices. Typical use cases:

- **Imperative data transformation** — a computation over `data` inputs whose result is returned via `output` with `response_variable`, when a template would be too awkward
- **Dynamic multi-action call** — trigger actions for a runtime-determined set of entities in a loop via `hass.services.call(...)`
- **Programmatic state setting** — set/remove several states via the `hass` sandbox API where declarative YAML would be too repetitive
- **Custom event bridge** — fire a named event with computed data via `hass.bus.fire("event_name", {...})` that automations trigger on
- **Sandbox-safe helper logic** — small, self-contained logic using the allowed builtins (`min`/`max`) and `time`/`datetime`/`dt_util`, documented via `services.yaml`

A `python_script` is the right tool only when the logic is **not expressible declaratively** and needs no imports, third-party libraries, or network. If it can be written as a script/template/automation or needs HTTP/libraries/concurrency, another building block is right (see `### Delimitation: When NOT to Use`).

## Goals

- Fix enabling, placement (`<config>/python_scripts/`), and the invocation contract (`python_script.<name>`) as binding
- Fix the sandbox contract (available objects, import ban, trimmed `hass`) as a hard boundary
- Anchor the data flow `data` (input) → `output` (return via `response_variable`) as the only documented path
- Fix `logger` as the only logging path and documentation via `services.yaml`
- Clearly delimit that `python_script` is the escape hatch and **when NOT** to choose it

## Non-Goals

- The declarative script/action syntax (`choose`, `repeat`, `wait_*`, `response_variable` at script level) — `ha-automation/script`
- The trigger/condition/run-mode model of the rule engine — `ha-automation/automation`
- Template (Jinja) syntax as a declarative alternative — `/docs/configuration/templating/`
- The naming dimension (file/slug name, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Developing a full custom integration in Python (imports, network, libraries) — that is integration *development*, not a usage scope

## Requirements

### Configuration and Placement

- **MUST** enable the integration through the empty `python_script:` entry in `configuration.yaml`; each script file lives as a `.py` file in `<config>/python_scripts/`
- **MUST** give the file name as a snake_case slug (lowercase, underscores) — it becomes the action `python_script.<filename>`; naming mechanics in `ha/naming-conventions`
- **SHOULD** document each script via a `<config>/python_scripts/services.yaml` with name, description, and fields so the UI editor shows meaningful metadata
- **MAY** rely on changes taking effect immediately without a restart (no caching per the docs); a `python_script.reload` is not required to activate a changed file

### Sandbox Contract

- **MUST NOT** use `import` — the docs state that imports are not possible in this integration; a script that needs a library does not belong here
- **MUST** use only the provided objects: `hass` (run actions, set/remove states, fire events only), `data` (input dictionary), `logger` (logging), `output` (return dictionary); additionally limited `time`, `datetime`, `dt_util`, and builtins such as `min`/`max` are available
- **MUST** account for `hass` being trimmed: only actions, state manipulation, and event firing are allowed — no arbitrary access to internal HA objects
- **SHOULD NOT** attempt to access the filesystem, network, or external processes — the sandbox provides no objects for that; such needs are a signal to switch tools (see delimitation)

### Invocation, Input, Return, and Logging

- **MUST** read input parameters only via the `data` dictionary (`data.get("name", "world")`); on invocation they are passed as the action's `data:` keys
- **MUST** return values only via the `output` dictionary and collect them on the caller side with `response_variable` (`response_variable: python_script_output`) — not via a workaround helper (`input_*`)
- **MUST** log via the provided `logger` object (`logger.info()`/`logger.warning()`/`logger.error()`); `print` or custom loggers are not provided in the sandbox
- **MAY** fire events via `hass.bus.fire("event_name", {...})` and call actions via `hass.services.call(domain, service, data, blocking)` — the latter with `blocking=True, return_response=True` when a service response must be collected

### Delimitation: When NOT to Use

- **SHOULD NOT** use `python_script` for logic expressible declaratively in **script/template/automation** — the docs themselves position it as an escape hatch for the rest; branching sequence logic belongs in `ha-automation/script` (`choose`/`if`/`repeat`), derived values in a template sensor (`ha-automation/template`), because the declarative construct is versioned, UI-editable, and free of sandbox pitfalls
- **MUST NOT** use `python_script` when the task needs an **import**, a **third-party library**, or **network/HTTP access** — that is impossible in the sandbox; HTTP is handled by `rest_command` (`ha-automation/rest-command`), and anything beyond that by a real **custom integration**, because only it may run libraries and a long-lived client
- **SHOULD NOT** put complex or long-running computation into a `python_script` — the sandbox offers no concurrency/background primitives; compute-heavy or periodic work belongs in a **custom integration** with a coordinator (`ha/coordinator-patterns`), because it runs cleanly on the event loop or executor there
- **SHOULD NOT** write a `python_script` merely to force a value into a state machine that a **template** could deliver directly — `states('…')`, filters, and `is_state(…)` in a Jinja template are more robust and carry no sandbox risk
- **MUST NOT** drop unbounded/unreviewed code from an untrusted source into a `python_script`, because despite the sandbox it can manipulate `hass` actions, states, and events — the sandbox limits the API surface but does not replace review

## Acceptance Criteria

- [ ] The integration is enabled via `python_script:`; each file is a snake_case `.py` under `<config>/python_scripts/`
- [ ] No script contains an `import`; it uses only `hass`/`data`/`logger`/`output` (plus allowed `time`/`datetime`/`dt_util`/builtins)
- [ ] Inputs are read via `data`, returns delivered via `output` and collected with `response_variable`
- [ ] Logging goes through the provided `logger` object
- [ ] Scripts are documented via `python_scripts/services.yaml`
- [ ] No `python_script` replaces logic expressible declaratively as a script/template/automation
- [ ] No `python_script` attempts imports, third-party libraries, or network access (HTTP via `rest_command`, beyond that via a custom integration)
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Multi-file/module structure**: The fetched doc page anchors no mechanism to structure a `python_script` across multiple files (no import between scripts). Should this spec carry its own rule "one script = one file, no module splitting", or is that implicitly covered by the import ban?
