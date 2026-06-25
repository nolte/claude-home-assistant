# HA Automation: Using Shell Command

Status: draft

## Context

The `shell_command` integration turns named command-line commands into callable actions. In `configuration.yaml`, under the `shell_command:` key, an alias maps to a command string (e.g. `restart_pow: touch ~/.pow/restart.txt`); each alias is exposed as the action `shell_command.<alias>` and is callable from automations and scripts.

The command string supports **templating**, but with templates it runs in a **secured environment**: the docs make clear that no shell helpers are allowed there — no home-directory shorthand `~`, no pipes `|`, no redirection operators — and that **only the part after the first space** may come from a template; the command name itself must be literal. Commands run with working directory `/config`, are stopped after **60 seconds**, and their `stdout`/`stderr` are logged at log level `debug`. Callers can collect a dictionary with `stdout`, `stderr`, and `returncode` via `response_variable`.

Real classification: `shell_command` is a **system/command integration** with an integration card under `/integrations/shell_command/`, but no connectable device. It is security-sensitive: the command runs (on HA OS) inside the `homeassistant` container as root. Within the `ha-automation` corpus it is the escape hatch for exactly the local system interaction no integration covers.

Verified source: [`/integrations/shell_command/`](https://www.home-assistant.io/integrations/shell_command/) (configuration mapping, invocation `shell_command.<alias>`, template restrictions, `~`/`|`/redirect ban with templates, "only content after the first space", `response_variable` with `stdout`/`stderr`/`returncode`, 60-second timeout, working directory `/config`, debug logging).

## When to Use

Use `shell_command` for a **local, short-lived system interaction** that no native integration covers and that runs as a named command with controlled values. Typical use cases:

- **Trigger a local CLI tool** — call a command-line tool available in HA from an automation that has no matching integration counterpart
- **Touch a file in the `/config` directory** — create/update a file (e.g. a trigger/flag file), with the command running in the working directory `/config`
- **Exit-code-driven branching** — run a command and branch on `returncode`/`stdout`/`stderr` via `response_variable` instead of assuming success blindly
- **Parameterized command with controlled data** — insert action data into the literal command via the documented template variable (only the part after the first space)
- **Short, non-interactive task** — a non-interactive command that completes in under 60 seconds without pipes/redirects/`~` in the template

A `shell_command` is the right tool only for **local, short-lived commands with fully controlled values**. For an HTTP call, a long-running/interactive process, untrusted input, or an already existing native action, another building block is right (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the configuration mapping (`shell_command:` alias → command) and invocation contract (`shell_command.<alias>`) as binding
- Fix the **security rule against shell injection** (no unchecked template/untrusted input in the command string) as a core requirement
- Anchor the documented template restrictions (no `~`/`|`/redirect, only after the first space, literal command name)
- Fix the return/exit-code path via `response_variable` (`stdout`/`stderr`/`returncode`)
- Clearly delimit when a `shell_command` is **not** the right tool

## Non-Goals

- The declarative script/action syntax the call is embedded in — `ha-automation/script`
- The trigger/condition model of the rule engine — `ha-automation/automation`
- HTTP calls to external services — `ha-automation/rest-command`
- In-sandbox Python without a subprocess — `ha-automation/python-script`
- The naming dimension (alias, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here

## Requirements

### Configuration and Invocation

- **MUST** define each command under `shell_command:` as a mapping `<alias>: <command-string>`; the alias becomes the action `shell_command.<alias>`
- **MUST** give the alias as lowercase snake_case — the docs explicitly forbid camel-case ("Use lowercase names and separate words with underscores"); naming mechanics in `ha/naming-conventions`
- **MUST** keep the **command name literal** in the string — per the docs only the part **after the first space** may come from a template, not the command name itself
- **SHOULD** assume the command runs in the working directory `/config` and choose paths relative or absolute accordingly
- **MUST** account for commands being stopped after **60 seconds** — longer-running work does not belong in a `shell_command`

### Templating, Security, and Return

- **MUST NOT** interpolate unchecked/untrusted input (user input, entity attributes from foreign sources, freely editable helpers) unquoted into the command string — this is the classic **shell-injection** path; use only controlled, validated values
- **MUST** respect the documented restrictions of the secured environment when using templates: **no** `~` (home expansion), **no** pipes `|`, **no** redirection operators — these helpers are unavailable with templates
- **MUST** bring action data into the command only via the documented bridge: the data passed to the action is available "as a variable within the template" — no string concatenation in YAML outside this mechanism
- **SHOULD** evaluate success/failure via `response_variable` and branch on the `returncode` (`response_variable` yields a dictionary with `stdout`, `stderr`, `returncode`) — a non-zero exit must not be silently ignored
- **MAY** use debug logging for diagnostics: `stdout` and `stderr` are logged at log level `debug`

### Delimitation: When NOT to Use

- **MUST NOT** build untrusted or template-generated input into the command string without strictly controlling it — shell injection allows arbitrary command execution (on HA OS as root inside the `homeassistant` container); if the value is not fully controlled, `shell_command` is the wrong tool and the task belongs in an **integration** with typed parameters
- **SHOULD NOT** misuse `shell_command` for an **HTTP call** (`curl`/`wget`) to an external service — `rest_command` (`ha-automation/rest-command`) is meant for that, mapping `method`/`url`/`payload`/`headers`/`verify_ssl`/`timeout` declaratively and without shell risk, and returning the response structured
- **SHOULD NOT** start long-running or interactive processes (daemons, watchers, processes expecting input) via `shell_command` — the **60-second timeout** kills them; such needs belong in an **add-on/integration** that manages a long-lived process cleanly
- **SHOULD NOT** use a `shell_command` where a **native integration or action** already exists for the target system — the native action is more portable, tested, and free of subprocess/path assumptions (`/config` working directory) than the shell-out
- **SHOULD NOT** expect pipes/redirects/`~` in a templated command — the secured environment disallows them; if you need a pipeline, encapsulate it in a versioned script file (literal command name) rather than in the template, or switch tools

## Acceptance Criteria

- [ ] Each command is defined as a `shell_command:` alias (lowercase snake_case) → command string; the command name is literal
- [ ] No untrusted/template-generated input is interpolated unchecked into the command string (injection protection)
- [ ] Templated commands use no `~`, no pipes `|`, no redirects (secured-environment restrictions)
- [ ] Action data reaches the command only via the documented template variable
- [ ] Success/failure is evaluated via `response_variable` (`returncode`); a non-zero exit is not silently ignored
- [ ] No command conceptually runs longer than 60 seconds or interactively
- [ ] HTTP calls use `rest_command`, not `shell_command`; existing native actions are preferred
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Quoting help for templates**: The fetched doc page names the injection risk but anchors no concrete quoting/escaping filter for the template part. Should this spec make its own rule on safe quoting (or on the obligation to carry dynamic values through the data variable rather than string concatenation) binding, or does it stay at the "controlled values only" rule?
