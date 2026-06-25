---
name: ha-system-health-add
description: Augment an existing Home Assistant Custom Integration with a system health info provider, conforming to spec/ha/system-health. Creates system_health.py with a @callback-decorated synchronous async_register(hass, register) that calls register.async_register_info(async_health_info) (optionally with a /config/<domain> manage URL), plus the async async_health_info(hass) -> dict callback returning short at-a-glance values — reachability via system_health.async_check_can_reach_url(hass, url) set as a coroutine so the frontend does not block, remaining quota, connected server — and the system_health strings.json entries. Runs an at-a-glance value check and keeps diagnostic dumps out. Activate on "add system health info", "show my integration on the system health page", "füge System-Health-Infos hinzu". Do not activate for redacted diagnostic dumps (ha-diagnostics-augment), user-facing problems needing an action (ha-repairs-add), greenfield scaffolding (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, system-health]
---

# HA System Health Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-system-health-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-system-health-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the backend state and reads back the `system_health.py` module and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-diagnostics-augment`, `ha-repairs-add`, `ha-coordinator-add`).
- **Mid-flow interactivity** — the at-a-glance value check (does the integration even have a meaningful status?) and the choice of info items are a per-run dialogue the user approves before generation.
- **Bounded, inline generation** — one module plus the `strings.json` entries fit inline; no isolated agent context is needed.
- Counter-dimension considered: the validate loop could be an agent, but the value check and the diagnostics-vs-system-health distinction belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add a system health info provider to an existing integration — to surface short at-a-glance status (backend reachability, connected server, remaining quota) on the integration's system health page.

## When NOT to activate

- a full, redacted diagnostic dump → `ha-diagnostics-augment` / `ha/diagnostics`
- a user-facing problem that needs an action (a repairs issue) → `ha-repairs-add` / repairs
- greenfield integration scaffolding → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **At-a-glance only.** System health carries short status values, never a full diagnostic dump. Run the value check first: a purely local integration with no meaningful status should be steered to skip `system_health.py`; full dumps go to `ha-diagnostics-augment`.
2. **Read [`ha/system-health`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/system-health/de.md) first.** Do not generate from memory.
3. **`@callback`, synchronous registration.** Export `async_register(hass, register) -> None` decorated with `@callback`; the registration is synchronous — only the info gathering is async. Import `SystemHealthRegistration` from `homeassistant.components.system_health` for the annotation.
4. **Register via `async_register_info`.** Inside `async_register`, call `register.async_register_info(async_health_info)`; optionally pass a manage URL as the second argument, e.g. `register.async_register_info(async_health_info, "/config/<domain>")`.
5. **Info callback contract.** Provide `async def async_health_info(hass) -> dict` returning the displayed info dict; values may be of any type, including coroutines.
6. **Coroutine for expensive checks.** Set URL reachability and other expensive checks as a **coroutine** in the dict **without** a prior `await` — the frontend shows a waiting indicator and updates the item automatically.
7. **Use the reachability helper.** For reachability items use `system_health.async_check_can_reach_url(hass, url)` instead of a custom HTTP probe; one helper call per endpoint.
8. **Translate every key.** Each info key has a string under `system_health:` in `strings.json` (see [`ha/translations`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/translations/de.md)); a missing string shows the user a raw key.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `backend_state` | yes | — | the backend state the page should surface, in prose |
| `endpoints` | no | derived | reachability URLs for `async_check_can_reach_url` |
| `values` | no | asked when needed | extra items (quota, consumed requests, connected server) |
| `manage_url` | no | omitted | optional `/config/<domain>` second arg to `async_register_info` |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Run the at-a-glance value check; if the integration is purely local with no meaningful status, surface that and steer the user away (or to `ha-diagnostics-augment`) before proceeding.
3. Read `ha/system-health`.
4. `system_health.py` is not already present. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the chosen info items (reachability endpoints, quota/server values), whether a manage URL is used, and the at-a-glance distinction in one paragraph. Wait for confirmation.

### 2) Generate

- `custom_components/<domain>/system_health.py` with the platform import, the `@callback async_register(hass, register) -> None` function calling `register.async_register_info(async_health_info[, "/config/<domain>"])`, and the `async def async_health_info(hass) -> dict` callback.
- Set reachability items as a coroutine via `system_health.async_check_can_reach_url(hass, url)` (no `await`); add quota/server values as needed.
- Add the `system_health:` `strings.json` entries for every info key.

### 3) Validate and report

Validate offline (`system_health.py` present; `async_register` is `@callback`, synchronous, exported, and registers via `async_register_info`; `async_health_info` defined and returns a dict; expensive checks set as coroutines without a prior `await`; reachability via `async_check_can_reach_url`; every info key resolved under `system_health:` in `strings.json`). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/system-health` acceptance criteria, plus the changed file paths.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Full redacted diagnostic dump → `ha-diagnostics-augment` / `ha/diagnostics`
- User-facing problem needing an action → `ha-repairs-add` / repairs
- Greenfield scaffold → `ha-integration-scaffold`
- Deploy to live HA → out of scope
