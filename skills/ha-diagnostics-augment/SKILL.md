---
name: ha-diagnostics-augment
description: Enrich an existing Home Assistant Custom Integration's diagnostics beyond the scaffold baseline, conforming to spec/ha/diagnostics. Creates or edits diagnostics.py with async_get_config_entry_diagnostics (and optional async_get_device_diagnostics) returning structured dicts, and routes every secret/PII/credential/coordinate field through homeassistant.components.diagnostics.async_redact_data with an explicit module-constant TO_REDACT frozenset — never manual truncation or field deletion. Includes redacted coordinator snapshots and version strings in the dump. Pairs with the diagnostics quality-scale rule (Silver). Activate on "enrich diagnostics", "add device diagnostics", "make sure diagnostics redacts secrets", "erweitere die Diagnostics", "redacte die Secrets im Diagnostics-Dump". Do not activate to audit redaction gaps across modules (ha-security-audit), to scaffold the bare diagnostics stub at greenfield (ha-integration-scaffold), to score the quality-scale rule (ha-quality-scale-audit), or to deploy to a live HA instance.
tags: [home-assistant, custom-integration, diagnostics]
---

# HA Diagnostics Augment

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-diagnostics-augment/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-diagnostics-augment/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the integration and reads back `diagnostics.py`, the `TO_REDACT` set, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-repairs-add`, `ha-device-automation-add`).
- **Mid-flow interactivity** — the redaction-key classification (which `entry.data` fields are credentials/identifiers/coordinates) is a per-run dialogue the user confirms before generation.
- **Bounded, inline generation** — one module plus its `TO_REDACT` set and the dump structure fit inline; no isolated agent context is needed.
- Counter-dimension considered: the derive→validate loop could be an agent, but the redaction-key classification belongs in the user's working context; skill wins.

## When this skill activates

Use this skill to enrich an existing integration's diagnostics beyond the scaffold baseline — a complete, structured `async_get_config_entry_diagnostics` dump (and optionally `async_get_device_diagnostics`) that routes every sensitive field through `async_redact_data` and includes redacted coordinator snapshots.

## When NOT to activate

- auditing redaction gaps across modules (findings report) → `ha-security-audit`
- the bare diagnostics stub at greenfield creation → `ha-integration-scaffold`
- scoring the diagnostics quality-scale rule across all rules → `ha-quality-scale-audit` / `ha/quality-scale`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **Existing integration only.** `custom_components/<domain>/manifest.json` must exist. When `diagnostics.py` already exists, edit it — never blindly overwrite.
2. **Read [`ha/diagnostics`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/diagnostics/de.md) first.** Do not generate from memory.
3. **`async_get_config_entry_diagnostics` contract.** Export `async_get_config_entry_diagnostics(hass, entry) -> dict` as a top-level async function — HA invokes it automatically on "Download Diagnostics". Optionally export `async_get_device_diagnostics(hass, entry, device) -> dict` with the same redaction contract.
4. **`async_redact_data` is mandatory.** Wrap every `entry.data` and `entry.options` lookup — and every coordinator nesting that carries sensitive fields — in `homeassistant.components.diagnostics.async_redact_data(..., TO_REDACT)`. **Never** use manual logic (`if "api_key" in d: d["api_key"] = "***"`), a manual `"REDACTED"` string, or field deletion (`del d["api_key"]`); `**REDACTED**` preserves length/format debugging and is the HA convention.
5. **Module-constant `TO_REDACT` frozenset.** Define `TO_REDACT` as a module constant (or in `const.py` when shared across hooks) holding every `entry.data` key classified as a credential or identifier — typically `api_key`, `password`, `token`, `secret`, `auth`, `bearer`, plus integration-specific tenant/account slugs. Keep it in sync with the `entry.data` schema.
6. **Identifiers and coordinates too.** Include multi-tenant identifiers (`tenant_slug`, `tenant_id`, `org_id`) and coordinates (`latitude`, `longitude`) in `TO_REDACT` — identifying, therefore kept out of forum reports.
7. **Coordinator data in the dump.** Include the current `coordinator.data` of every registered coordinator and redact it when the API response carries sensitive fields; reduce to a subset only when the full dump would be too large. Never dump logs or stack traces.
8. **Derive, don't guess.** Derive the `entry.data` / `entry.options` key space from the config flow and setup; ask when uncertain.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `to_redact_extra` | no | derived | extra `TO_REDACT` keys beyond the derived credential/identifier set |
| `device_diagnostics` | no | asked when relevant | whether to add `async_get_device_diagnostics` |
| `coordinator_subset` | no | full | reduce coordinator data to a subset when the full dump would be too large |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Derive the `entry.data` / `entry.options` key space from the config flow and setup; collect every credential/identifier/coordinate key as a redaction candidate.
3. Determine the registered coordinators; check whether their data carries sensitive fields.
4. Read `ha/diagnostics`.
5. If `diagnostics.py` exists, plan an edit (not a replace).

## Workflow

### 1) Classify and confirm

State `domain`, the derived `TO_REDACT` set (credentials, identifiers, coordinates), the coordinators whose data enters the dump, and whether `async_get_device_diagnostics` will be added, in one paragraph. Wait for confirmation.

### 2) Generate

Create or edit `diagnostics.py`:

- the `TO_REDACT` frozenset (module constant, or `const.py` when shared);
- `async_get_config_entry_diagnostics(hass, entry) -> dict` returning a structured dict — `entry.data` and `entry.options` wrapped in `async_redact_data(..., TO_REDACT)`, the redacted `coordinator.data` per role, and the manifest + HA version strings;
- optionally `async_get_device_diagnostics(hass, entry, device) -> dict` with the same redaction contract.

### 3) Validate and report

Validate offline (`diagnostics.py` present; `async_get_config_entry_diagnostics` is a top-level async function; `TO_REDACT` is a module constant covering every auth/identifier field; every `entry.data`/`entry.options` lookup wrapped; coordinator data redacted when sensitive; `grep` for `del .*(api_key|password|token)` and for a manual `"REDACTED"` string returns no hits). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/diagnostics` acceptance criteria, plus the changed file paths and the quality-scale marker (**Silver**).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Auditing redaction gaps across modules → `ha-security-audit`
- Bare diagnostics scaffold stub → `ha-integration-scaffold`
- Quality-scale rule scoring → `ha-quality-scale-audit`
- Deploy to live HA → out of scope
