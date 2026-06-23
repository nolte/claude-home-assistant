# HA Integration: Security Hardening

Status: draft

## Context

A Custom Integration is third-party code that runs in the same process as HA Core, has full read / write access to the HA state, and routinely operates with stored user credentials. Security gaps in a Custom Integration are therefore not isolated bugs but reach straight into the HA system. Three classes of gap have appeared repeatedly in practice: (1) **API path injection** — the HTTP client builds requests from user input without path validation; (2) **bearer-token leakage** — tokens are sent for paths they were not meant for; (3) **multi-instance service ambiguity** — a service call hits the wrong backend because disambiguation logic is missing.

`nolte/kamerplanter-ha` shipped a coherent hardening bundle in commit `242c08f (2026-04-25 "fix(security): harden HTTP client, config flow, and service handlers")`: API path whitelist via `_API_PATH_RE`, bearer gating only for validated paths, input validation in the config flow (URL format, credential character set), ambiguity detection in service handlers. This spec lifts the individual hardening measures into a generic, skill-enforceable obligation.

Quality scale marker: **Silver** (input validation and safe defaults are a Silver requirement); individual measures (bearer gating, path whitelist) reach beyond Silver but are mandatory portfolio-wide.

## Goals

- Prevent API path injection through path whitelist validation in the HTTP client
- Send bearer tokens only to validated API paths — user-entered URLs must never "carry the token along"
- Harden user input in the config flow with strict format validation, so faulty or hostile input does not surface only inside the coordinator loop
- Establish multi-instance disambiguation in service handlers as a security obligation (not just UX) — a service call must not mutate the wrong backend
- Ensure diagnostics redaction (see `ha/diagnostics`) as a mandatory channel, so no secrets land in bug reports

## Non-Goals

- Backend-side authentication / authorization — outside plugin scope
- TLS configuration / certificate pinning at the HTTP client layer — separate follow-up spec once the first integration concretely needs it
- HA frontend hardening (XSS, CSP) — owned by HA Core itself; Lovelace cards do not interfere unless they use `dangerouslySetInnerHTML` equivalents
- Penetration-testing methodology — addresses review practice, not skill output
- Audit logging in HA — separate HA mechanism

## Requirements

### API path whitelist

- **MUST** carry a path whitelist in the integration's HTTP client as a module constant (typically a compiled regex `_API_PATH_RE`) — the whitelist entry matches the allowed paths of the concrete backend (for example `^/api/(v1|v2)/(plants|locations|tanks|tasks|alerts)(/[a-zA-Z0-9_-]+)*/?$`)
- **MUST** validate the target path against the whitelist before every HTTP request and raise a `ValueError` (or an integration-specific `<Domain>InvalidPathError`) on mismatch
- **SHOULD** keep the whitelist as a positive list (only allowed paths) instead of a negative list (forbidden paths) — positive lists fail safe; negative lists forget edge cases
- **MUST NOT** pass user-input paths to the HTTP client without whitelist validation — the path must never reach the client from user input without going through the validator

### Bearer-token gating

- **MUST** insert the bearer token (or API key, OAuth token) into the `Authorization` header of a request **only** when the target path passes the path whitelist
- **MUST NOT** send tokens to paths outside the whitelist — even when the path looks like `/api/...` but is not in the whitelist: drop the token
- **SHOULD** consolidate bearer setting in a single helper method (`_with_auth(headers)`) that includes the whitelist check — prevents token setting from being duplicated across multiple call sites and easily bypassed
- **MUST NOT** log tokens — not even at DEBUG level; logging statements must redact or omit tokens

### Config-flow input validation

- **MUST** strictly validate user-entered URLs in the user / reauth / reconfigure flow:
  - URL format (valid `scheme://host[:port]/path` schema)
  - Allowed schemes: `http`, `https` — no `file:`, `gopher:`, `data:`, or others
  - Hostname / IP within expected ranges when the integration is supposed to be LAN-only
- **MUST** check API keys and similar credentials against format patterns (typical `^[A-Za-z0-9_-]{20,}$` or integration-specific prefix like `sk_live_…`) — prevents typos, but more importantly catches HTML / shell escapes that slip through
- **SHOULD** declaratively check format violations with `vol.Match` / `vol.All(str, vol.Length(min=N))` directly in `vol.Schema(...)` instead of imperative `if` chains in the handler
- **MUST** raise validation errors before the first API call — bad input must not surface only at the backend

### Multi-instance service disambiguation

- **MUST** apply the disambiguation logic from `ha/services` in service handlers — no service call must hit the wrong config entry
- **MUST** ask explicitly for `entry_id` or abort with `ServiceValidationError` whenever multi-match risk exists (multiple entries of the same integration, multiple resources with the same backend key)
- **MUST NOT** silently fall back to the first entry when multiple match — that is a security risk because the user thinks a different action was triggered

### Diagnostics redaction

- **MUST** use `async_redact_data` for every credential entry stored in `entry.data` / `entry.options` (see `ha/diagnostics`) — diagnostics dumps land in forum posts and must not contain secrets
- **MUST NOT** leak credentials into coordinator data — if the backend itself returns auth material in API responses (for example refresh tokens), it belongs in `TO_REDACT` as well

### Logging discipline

- **MUST NOT** carry API keys, bearer tokens, passwords, or other credentials in log statements — at any log level
- **MUST NOT** dump full API responses unredacted into DEBUG logs when the response carries sensitive fields
- **SHOULD** define a dedicated helper function (`_safe_log(payload)`) for DEBUG diagnostics that strips sensitive fields before logging
- **MAY** carry request IDs / correlation IDs in logs — that helps tracing without containing credentials

### Cross-references

- API path whitelist implementation and HTTP client shape: consumer-specific reference in `nolte/kamerplanter-ha/custom_components/kamerplanter/api.py:50–64`; a dedicated `ha/api-client-patterns` spec is a follow-up spec once skills scaffold HTTP clients directly
- Multi-instance disambiguation helper: detail in `ha/services` § multi-instance disambiguation
- Redaction-set shape: detail in `ha/diagnostics` § `TO_REDACT` set

## Acceptance Criteria

- [ ] The integration's HTTP client carries a compiled path whitelist (regex or similar construct)
- [ ] Every HTTP request runs through the whitelist validation; mismatches raise an integration-specific exception
- [ ] Bearer-token setting is encapsulated in a single helper method; the helper method is the only place where auth headers are set
- [ ] A `grep` for `Authorization` across source files (excluding the API-client helper) returns no hits
- [ ] Config-flow schema uses `vol.Match` / `vol.Length` for URL and credential fields
- [ ] Service handlers call the `_resolve_entry` helper from `ha/services` and abort with `ServiceValidationError` on ambiguity
- [ ] `diagnostics.py` redacts every credential and multi-tenant identifier (see `ha/diagnostics`)
- [ ] A `grep` for `_LOGGER\.[a-z]+\(.*api_key`, `_LOGGER\.[a-z]+\(.*token`, `_LOGGER\.[a-z]+\(.*password` returns no hits
- [ ] Quality scale marker: **Silver**

## Open Questions

- **API-client spec maturity**: Currently the HTTP client shape (`api.py` layout, exception hierarchy, path whitelist form) is defined only indirectly through cross-reference to kamerplanter-ha. When does that become a dedicated `ha/api-client-patterns` spec?
- **TLS-verification default**: Should skills force `verify=True` (TLS-cert validation) as the default, or remain backend-specific (some self-signed local backends)?
- **Whitelist granularity**: How specific does the path whitelist need to be? Currently formulated as "match the matching backend paths"; a heuristic (per-endpoint vs. top-level area) is missing.
- **Hard-enforce bearer-token-in-log ban**: A `grep`-based CI rule as an acceptance criterion; should that become a mandatory lint hook (for example a bandit / semgrep pattern), or is code review sufficient?
- **Audit-log addition**: Should the spec mirror audit-relevant actions (service calls, reauth events) into HA system events, so users can trace them in the logbook?
