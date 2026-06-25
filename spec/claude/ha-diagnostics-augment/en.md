# Skill: `ha-diagnostics-augment`

Status: draft

## Context

`ha/diagnostics` defines the diagnostics dump: HA serialises the config entry plus integration-supplied data into a JSON file per config entry as soon as the user clicks "Download Diagnostics" — that file typically ends up in issue reports and forum posts. That is exactly why proper redaction is mandatory: credentials, API keys, tokens, coordinates, and multi-tenant identifiers must not land in the dump in plain text. HA provides `homeassistant.components.diagnostics.async_redact_data(data, to_redact)` for this — a recursive walker that replaces every key in the `to_redact` set with `**REDACTED**`. The quality-scale marker is **Silver** once the integration stores auth credentials or other sensitive data in `entry.data`.

This skill enriches an **existing** integration's diagnostics beyond the bare scaffold baseline: it creates or edits `diagnostics.py` with `async_get_config_entry_diagnostics` and optionally `async_get_device_diagnostics`, returning structured dicts, and routes **every** secret / PII / credential / coordinate field through `async_redact_data` with an explicit module-constant `TO_REDACT` frozenset — conformant to `ha/diagnostics`.

## Scope

Enriching the diagnostics of exactly one existing `custom_components/<domain>/` integration: creating or editing `diagnostics.py` with `async_get_config_entry_diagnostics(hass, entry) -> dict` (mandatory) and optionally `async_get_device_diagnostics(hass, entry, device) -> dict`, the module-constant `TO_REDACT` frozenset, the `async_redact_data` wrapping of every sensitive nesting path (`entry.data`, `entry.options`, sensitive coordinator data), and the recommended dump structure incl. coordinator snapshots and version strings. The skill reads `ha/diagnostics` and validates.

## Goals

- Enrich `diagnostics.py` beyond the scaffold baseline: complete, structured dumps instead of a bare stub
- Establish the module-constant `TO_REDACT` frozenset and keep it in sync with the `entry.data` schema — anything stored as a credential/identifier appears in `TO_REDACT`
- Enforce `async_redact_data` for every sensitive path — forbid manual redaction logic and field deletion
- Include coordinator data as a standard part of the dump so bug reports reflect the data state, and redact it too
- Optionally add `async_get_device_diagnostics` when a per-device dump is useful, with the same redaction contract

## Non-Goals

- Auditing existing redaction gaps (a findings report across all modules) — `ha-security-audit`
- The bare scaffold stub of `diagnostics.py` at greenfield creation — `ha-integration-scaffold`
- The quality-scale assessment of the diagnostics rule across all rules — `ha-quality-scale-audit` / `ha/quality-scale`
- Redaction-schema migration between versions (field rename plus migrate path) — a separate follow-up spec
- External diagnostic tools (Sentry, OpenTelemetry) and repairs/system-health — separate HA mechanisms

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "enrich diagnostics", "add device diagnostics", "make sure diagnostics redacts secrets"
  - "route the API key through async_redact_data", "dump the coordinator data in diagnostics"
  - "erweitere die Diagnostics", "redacte die Secrets im Diagnostics-Dump", "füge Device-Diagnostics hinzu"

### Inputs

- **MUST** capture: `target_dir` (repo root), from which `custom_components/<domain>/` and the auth/identifier fields in `entry.data` are derived
- **MAY** capture: additional `TO_REDACT` keys beyond the derived ones, whether `async_get_device_diagnostics` is wanted, and whether coordinator data should be reduced to a subset

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** derive the `entry.data` / `entry.options` key space from the config flow and setup and collect every credential/identifier/coordinate key as a redaction candidate
- **MUST** determine the registered coordinators and check whether their data carries sensitive fields
- **MUST** read the `ha/diagnostics` spec
- **MUST NOT** blindly overwrite an existing `diagnostics.py` — when the module exists, edit, do not replace

### Generation rules (from `ha/diagnostics`)

- **MUST** create or edit `diagnostics.py` in `custom_components/<domain>/` and export at least `async_get_config_entry_diagnostics(hass, entry) -> dict` as a top-level async function
- **MUST** define a `TO_REDACT` frozenset as a module constant (or in `const.py` when shared across hooks) holding every `entry.data` key classified as a credential/identifier — typically `api_key`, `password`, `token`, `secret`, `auth`, `bearer`, plus integration-specific tenant/account slugs
- **SHOULD** include multi-tenant identifiers (`tenant_slug`, `tenant_id`, `org_id`) and coordinates (`latitude`, `longitude`) in the set — identifying and therefore kept out of forum reports
- **MUST** wrap every lookup of `entry.data` and `entry.options` in `async_redact_data(..., TO_REDACT)`
- **MUST NOT** use manual redaction logic (`if "api_key" in d: d["api_key"] = "***"`) or a manual `"REDACTED"` string — that does not scale across nesting
- **MUST NOT** delete sensitive fields before dumping (`del d["api_key"]`) — `**REDACTED**` is enough and is the HA convention, which preserves length/format debugging
- **SHOULD** include the current `coordinator.data` of every registered coordinator and **MUST** apply `async_redact_data` to it as well when the API response carries sensitive fields; **MAY** reduce the dump to a subset when the full dump would be too large
- **MAY** add `async_get_device_diagnostics(hass, entry, device) -> dict` with the same redaction contract when a per-device dump is wanted
- **SHOULD** carry the manifest and HA version strings; **MUST NOT** write logs or stack traces into the dump
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: `diagnostics.py` exists; `async_get_config_entry_diagnostics` is a top-level async function; `TO_REDACT` is a module constant and covers every auth/identifier field; every `entry.data` / `entry.options` lookup is wrapped; coordinator data appears with redaction (when sensitive); a `grep` for `del .*(api_key|password|token)` and for a manual `"REDACTED"` string returns no hits
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/diagnostics`, plus the changed file paths and the quality-scale marker (**Silver**)

### Prohibitions

- **MUST NOT** truncate or delete sensitive fields via manual logic instead of `async_redact_data`
- **MUST NOT** guess the `entry.data` key space — it is derived from the config flow/setup, and uncertainties are asked
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] `custom_components/<domain>/diagnostics.py` exists and `async_get_config_entry_diagnostics(hass, entry) -> dict` is exported as a top-level async function
- [ ] `TO_REDACT` is defined as a module constant (or in `const.py`) and contains every auth/identifier field from `entry.data`
- [ ] Every lookup of `entry.data` and `entry.options` is wrapped in `async_redact_data(..., TO_REDACT)`
- [ ] Coordinator data appears in the dump with redaction (when carrying sensitive fields)
- [ ] A `grep` for `del .*api_key`/`password`/`token` and for a manual `"REDACTED"` string in `diagnostics.py` returns no hits
- [ ] An optionally added `async_get_device_diagnostics` follows the same redaction contract
- [ ] Report names the file paths and the quality-scale marker **Silver**

## Open questions

- **`async_get_device_diagnostics` threshold**: When does the skill require the device hook instead of merely offering it? `ha/diagnostics` leaves it MAY; the skill adds it on request and asks when in doubt.
- **Coordinate classification**: Are `latitude`/`longitude` always redact-worthy? The skill includes them as SHOULD because they are identifying; a calibrated threshold is missing.
- **Coordinator-data size**: From which size does the skill reduce to a subset? `ha/diagnostics` formulates "first item per list typically suffices"; a concrete threshold is not standardised.
