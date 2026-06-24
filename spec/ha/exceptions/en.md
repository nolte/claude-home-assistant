# HA Integration: Exceptions and Error Translations

Status: draft

## Context

When something goes wrong in a Custom Integration — a service-action call, an entity method (for example *Set HVAC Mode*), or a background task — the failure must be signalled via an HA exception whose message is shown to the user in the UI. HA generates that message either from an attached translation string or from the exception argument. A clean exception strategy distinguishes **who** caused the failure: a user operating incorrectly (`ServiceValidationError`) or the system / device / API (`HomeAssistantError`).

The HA docs require integrations to raise `ServiceValidationError` instead of `ValueError` when the user did something wrong — in that case the stack trace is only logged at debug level, not printed in full. For other failures (for example a problem communicating with a device) they require `HomeAssistantError`; here the full stack trace is written to the log. Both classes and their subclasses support localization via `translation_domain` / `translation_key`, with the strings living in `strings.json` under the `exceptions:` key.

Quality scale marker: **Silver** (`action-exceptions` — service actions raise exceptions on failure) and **Gold** (`exception-translations` — exception messages are translatable). This spec lifts both rules into a binding convention for every Custom Integration that skills in this plugin scaffold.

## Goals

- Establish the HA exception hierarchy as the binding vocabulary: `HomeAssistantError` as the base (message shown to the user), `ServiceValidationError` for invalid user input, the `ConfigEntryError` family for setup/lifecycle failures
- Enforce the causation distinction: user errors → `ServiceValidationError` (no full stack trace); system/device errors → `HomeAssistantError` (stack trace in the log)
- Require translatable exceptions as the default: `translation_domain` + `translation_key` (+ optional `translation_placeholders`) instead of hard-coded message strings
- Draw a clear line between `raise` (signal a failure) and `log` (diagnostic information without aborting)
- Forbid generic catches and silent swallowing of errors

## Non-Goals

- Coordinator error mapping (`UpdateFailed`, `ConfigEntryAuthFailed`, `ConfigEntryNotReady` in the `_async_update_data` path) — defined in `ha/coordinator-patterns` and only referenced here, not duplicated
- Service/action schema definition (fields, selectors, response types) — that belongs to `ha/services`
- The full translation workflow (`strings.json` structure, `translations/<lang>.json`, sync mechanics) — that belongs to `ha/translations`; this spec only requires the `exceptions:` block and the wiring of the exception to the translation key
- Frontend-side error presentation (toasts, repair issues, `ir.async_create_issue`) — separate follow-up spec once a concrete need lands

## Requirements

### Exception hierarchy

- **MUST** raise only HA exceptions from `homeassistant.exceptions` whose message may be shown to the user — `HomeAssistantError` is the base class and its message is shown in the UI
- **MUST** use `ServiceValidationError` (a `HomeAssistantError` subclass) for invalid user input to a service / action — it is raised **before** the actual work begins and printed without a full stack trace
- **MUST** use the `ConfigEntryError` family (`ConfigEntryError`, `ConfigEntryAuthFailed`, `ConfigEntryNotReady`) only in the setup/lifecycle context, not in action handlers (the coordinator mapping of these classes lives in `ha/coordinator-patterns`)
- **MUST NOT** let bare `Exception`, `ValueError`, or other non-HA exceptions propagate to the UI — they produce a full stack trace without a usable user message

### User errors vs. system errors

- **MUST** raise failures caused by incorrect usage (invalid input, referencing something that does not exist) as `ServiceValidationError` — the stack trace then appears only at debug level
- **MUST** raise failures originating in the service / system itself (network error, device communication problem, bug) as `HomeAssistantError` — the full stack trace is written to the log
- **MUST** validate user input **before** costly or side-effecting work begins — `ServiceValidationError` signals "nothing was changed"
- **SHOULD** preserve the original low-level exception as cause when a system error is mapped onto `HomeAssistantError` (`raise HomeAssistantError(...) from err`), so the stack trace is not lost in the log

### Translatable exceptions

- **MUST** annotate raised exceptions with `translation_domain=DOMAIN` and `translation_key="<key>"` instead of hard-coding the message strings — the exception class must inherit `HomeAssistantError` for the translation to apply
- **MUST** define the corresponding message strings in `strings.json` under the `exceptions:` key, with one `message` field per `translation_key`
- **MAY** pass `translation_placeholders={...}` to the exception to insert dynamic values into the translated message (for example the affected entity name or time value)
- **SHOULD** choose `translation_key` names that are descriptive and stable (for example `end_date_before_start_date`, `cannot_connect_to_schedule`), since they are part of the translation contract toward `ha/translations`
- **MUST NOT** reuse the same `translation_key` with differing placeholder expectations — every key has a fixed message contract

### Action/service error handling

- **MUST** raise invalid input as `ServiceValidationError` and actual execution failures as `HomeAssistantError` in every service/action handler (see `ha/services` for the schema side of the handler)
- **MUST** catch API-specific low-level exceptions in the handler and map them onto the appropriate HA exception (`except MyConnectionError as err: raise HomeAssistantError(...) from err`) instead of passing them through raw
- **MUST NOT** silently swallow a failure in the handler (empty `except`, `pass`, or returning a success sentinel despite a failure) — every failure is signalled as an exception or deliberately logged
- **MUST NOT** use bare `raise Exception(...)` or `raise ValueError(...)` in a handler — the user would then get no usable message

### Logging delineation

- **MUST** use `raise` when the operation fails and an error must be reported to the user — a logged line without `raise` lets the caller wrongly assume success
- **SHOULD** use `_LOGGER.debug/warning/error` for non-aborting diagnostic information (for example a single skipped enrichment entry), with each logged line carrying enough context for localisation
- **MUST NOT** both log and raise the same error so it appears twice in the log — either `raise` (HA logs it) or deliberately log without `raise`
- **MUST NOT** write secrets (API keys, tokens, passwords) or full raw payloads into logged errors or exception messages (see `ha/security-hardening` for the redaction obligation)

## Acceptance Criteria

- [ ] Every service/action handler raises `ServiceValidationError` for invalid user input and `HomeAssistantError` for execution failures
- [ ] No handler propagates bare `Exception` or `ValueError` to the UI
- [ ] User input is validated before side-effecting work begins
- [ ] System errors mapped onto `HomeAssistantError` preserve the original exception via `from err`
- [ ] Raised exceptions carry `translation_domain` and `translation_key`, and their class inherits `HomeAssistantError`
- [ ] `strings.json` contains an `exceptions:` block with one `message` per used `translation_key`
- [ ] Dynamic values in messages are inserted via `translation_placeholders`, not by string interpolation
- [ ] No handler silently swallows failures (no empty `except` / `pass` over an error path)
- [ ] No error is both logged and raised (no duplicate log output)
- [ ] Quality scale markers are set: **Silver** (`action-exceptions`) and **Gold** (`exception-translations`)

## Open Questions

- **`ServiceValidationError` placeholder convention**: Should validation exceptions carry `translation_placeholders` with the affected field name by default, or does a static message per validation case suffice? `kamerplanter-ha` does not yet have a uniform pattern for this.
- **Repair issues vs. exceptions**: When is a persistent repair issue (`ir.async_create_issue`) the right channel instead of a per-call exception? Separate `ha/repairs` spec once the first integration reports long-lived error states.
- **Entity-method coverage**: The HA docs name entity methods (for example *Set HVAC Mode*) on equal footing with service actions. Should this spec carry separate acceptance criteria for entity-method handlers, or does the handler generalisation suffice?
- **Translation coverage gate**: Should a test enforce that every `translation_key` used in code has an entry in the `exceptions:` block (and conversely that no dead key exists)? The mechanics for that belong to `ha/translations`.
