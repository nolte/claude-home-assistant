# HA Integration: Diagnostics

Status: draft

## Context

Home Assistant lets the user pull a **diagnostics dump** for any config entry — the user clicks "Download Diagnostics" in the frontend; HA serialises the config entry plus integration-supplied data into a JSON file and offers it as a download. That file typically ends up in issue reports and forum posts. That is exactly why proper **redaction** is mandatory: credentials, API keys, tokens, and multi-tenant identifiers must not land in the dump in plain text, otherwise they leak publicly by accident.

HA provides `homeassistant.components.diagnostics.async_redact_data(data, to_redact)` for this — a recursive walker that replaces every key in the `to_redact` set with `**REDACTED**`. `nolte/kamerplanter-ha` validates the pattern with a `TO_REDACT` set (`api_key`, `password`, `token`, `tenant_slug`) and a slim `async_get_config_entry_diagnostics(hass, entry)` function that dumps config entry data plus coordinator snapshots. This spec lifts the pattern into a generic obligation.

Quality scale marker: **Silver** (diagnostics with redaction is a Silver requirement once the integration stores auth credentials or other sensitive data in `entry.data`).

## Goals

- Establish `diagnostics.py` as the standard module for every Custom Integration with an auth-based backend
- Make redaction through `async_redact_data` mandatory — forbid manual truncation logic
- Define coordinator data as a standard part of the diagnostics dump, so bug reports reflect the data state
- Prevent drift between setup keys and the redaction set — anything stored as a credential in `entry.data` must appear in `TO_REDACT`

## Non-Goals

- Device-specific diagnostics (`async_get_device_diagnostics`) — separate follow-up spec when the first integration needs it
- Redaction-schema migration between versions — when fields are renamed, `TO_REDACT` and the migrate path must stay consistent, but that is not a spec concern
- External diagnostic tools (Sentry, OpenTelemetry) — live outside HA diagnostics
- Repairs and system-health modules — separate HA mechanisms, separate follow-up specs

## Requirements

### `diagnostics.py` existence

- **MUST** include a `diagnostics.py` module in `custom_components/<domain>/` once the integration stores auth credentials or other data classified as sensitive in `entry.data`
- **MUST** export at least `async_get_config_entry_diagnostics(hass, entry) -> dict` as a top-level async function — HA invokes it automatically when the user clicks "Download Diagnostics" on the entry
- **MAY** additionally export `async_get_device_diagnostics(hass, entry, device) -> dict` when a per-device dump is useful; that is a separate HA entry in the device detail menu

### `async_redact_data` as mandatory

- **MUST** use `homeassistant.components.diagnostics.async_redact_data(data, to_redact)` for every nesting that contains a user-input path (`entry.data`, `entry.options`, diagnostic coordinator data when API responses contain sensitive fields)
- **MUST NOT** use manual redaction logic (`if "api_key" in d: d["api_key"] = "***"`) — that does not scale across nesting and is brittle on refactoring
- **MUST NOT** delete sensitive fields from the data before dumping (`del d["api_key"]`) — that prevents debugging of the field (for example length verification or format check); `**REDACTED**` is enough and is the HA convention

### `TO_REDACT` set

- **MUST** define a `TO_REDACT` set as a module constant in `diagnostics.py`
- **MUST** include every key in `entry.data` classified as a credential or identifier — typical entries: `api_key`, `password`, `token`, `secret`, `auth`, `bearer`, plus integration-specific tenant / account slugs
- **MUST** maintain the set in sync with every `entry.data` schema change — new auth fields trigger an entry in `TO_REDACT`
- **SHOULD** carry multi-tenant identifiers (`tenant_slug`, `tenant_id`, `org_id`) in the set — even though they are not strictly "credentials", they are identifying and therefore typically kept out of forum reports
- **MAY** share the set across platform modules when the integration carries multiple diagnostic hooks — a central constant in `const.py` is then cleaner than duplicates

### Coordinator data in the dump

- **SHOULD** include the current `coordinator.data` of every registered coordinator in the dump — that makes bug reports debuggable because the data state at the time of failure remains visible
- **MUST** apply `async_redact_data` to coordinator data as well when the API response carries sensitive fields (for example `tenant_slug` in resource lists)
- **MAY** reduce coordinator data to a subset when the full dump would be too large — typically "first item per list" or "aggregate statistics" is enough

### Dump structure

Recommended (not mandatory) top-level structure of the return dict:

```text
{
  "entry_data": <async_redact_data(entry.data, TO_REDACT)>,
  "entry_options": <async_redact_data(entry.options, TO_REDACT)>,
  "coordinator_data": {
    "<role>": <async_redact_data(coordinator.data, TO_REDACT)>,
    ...
  },
  "manifest_version": <manifest.json:version>,
  "ha_version": <homeassistant.const.__version__>
}
```

- **SHOULD** carry the manifest and HA version strings in the dump — simplifies triage
- **MAY** include additional fields like last coordinator update timestamp, entity count, or cache statistics
- **MUST NOT** dump arbitrary logs or stack traces in the dump — HA logs live in a separate file; the diagnostics dump is for structured data

## Acceptance Criteria

- [ ] `custom_components/<domain>/diagnostics.py` exists
- [ ] `async_get_config_entry_diagnostics(hass, entry) -> dict` is exported as a top-level async function
- [ ] `TO_REDACT` is defined as a module constant (or in `const.py`) and contains every auth / identifier field that lands in `entry.data`
- [ ] Every lookup of `entry.data` and `entry.options` is wrapped in `async_redact_data(..., TO_REDACT)`
- [ ] Coordinator data appears in the dump with redaction (when carrying sensitive fields)
- [ ] A `grep` for `del .*api_key`, `del .*password`, `del .*token` in `diagnostics.py` returns no hits
- [ ] A `grep` for `"REDACTED"` as a manual string in `diagnostics.py` (instead of an `async_redact_data` call) returns no hits
- [ ] Quality scale marker: **Silver**

## Open Questions

- **`async_get_device_diagnostics` threshold**: When does the spec require the device hook? Currently MAY; a calibrated trigger is missing.
- **Coordinator-data size**: Up to which size is a full dump tolerable? Currently formulated as "first item per list typically suffices"; a concrete threshold (for example 500 KB) is not standardised.
- **Redaction depth**: `async_redact_data` walks recursively. Is that enough for deeply nested structures (multi-level API responses), or does it need a path-based override mechanism?
- **Multi-tenant identifier classification**: Are `tenant_slug` / `org_id` always redact-worthy, or only in public forum context? Currently formulated as SHOULD.
