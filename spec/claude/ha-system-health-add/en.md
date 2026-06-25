# Skill: `ha-system-health-add`

Status: draft

## Context

`ha/system-health` defines the system health layer: an integration participates by providing a `system_health.py` module with a `@callback`-decorated, synchronous `async_register(hass, register)` function that registers an info callback via `register.async_register_info(async_health_info)`. The `async_health_info(hass) -> dict` callback returns the dict shown on the system health page, whose values may be of any type — including coroutines. For coroutine values the frontend shows a waiting indicator and updates the item automatically once the result is available. For reachability items the platform provides the `system_health.async_check_can_reach_url(hass, url)` helper. No skill augments this so far. Importantly: system health is the **at-a-glance status** (short values shown directly in the frontend), not the full downloadable dump — that is `ha/diagnostics`.

This skill augments a system health info layer into an **existing** integration: the `system_health.py` module, the `@callback async_register` function, the `async_health_info` callback with its info dict, the reachability items via `async_check_can_reach_url`, and the `system_health` `strings.json` entries — conformant to `ha/system-health`. Before generating it checks whether the integration even has a meaningful at-a-glance status.

## Scope

Augmenting the system health info layer into an existing `custom_components/<domain>/` integration: the `system_health.py` module, the `@callback async_register(hass, register) -> None` function, the `register.async_register_info(...)` call (optionally with a manage URL `/config/<domain>`), the `async_health_info(hass) -> dict` callback, the info items (values and reachability checks via `async_check_can_reach_url`), and the `strings.json` `system_health:` entries. The skill reads `ha/system-health` and validates.

## Goals

- Derive meaningful at-a-glance items from the described backend state (reachability, connected server, quota) and augment them spec-conformantly
- Enforce the registration contract: a `@callback`-decorated, synchronous `async_register` that calls `register.async_register_info(async_health_info)`
- Set expensive checks as a **coroutine** (without a prior `await`) in the info dict so the frontend does not block
- Standardise reachability items through `system_health.async_check_can_reach_url(hass, url)` instead of manual HTTP probes
- Save the user from diagnostic overload: short status values here, full dumps in `ha/diagnostics`

## Non-Goals

- Full, redacted diagnostic dumps — `ha-diagnostics-augment` / `ha/diagnostics` (its own redaction obligation)
- User-facing problems that require an action (repairs issues, `async_create_issue`) — `ha-repairs-add` / repairs
- The detailed translation of the info keys through `strings.json` — the translation spec's concern; referenced here only
- External monitoring systems (Prometheus, healthcheck endpoints) — live outside HA system health
- Greenfield scaffolding of an integration — `ha-integration-scaffold`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add system health info", "show my integration on the system health page"
  - "surface the backend reachability / remaining quota on the system health page"
  - "füge System-Health-Infos hinzu"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the backend state (prose), from which the skill derives the info items
- **MAY** capture: the reachability URLs to check (`endpoints`), additional values (quota, connected server), and the optional manage URL (`/config/<domain>`)

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** run the value check: does the integration have a meaningful at-a-glance status (backend connectivity or quota semantics)? A purely local integration **MAY** omit `system_health.py`; the skill **SHOULD** point that out instead of generating empty items
- **MUST** read the `ha/system-health` spec
- **MUST NOT** overwrite an existing `system_health.py`; on collision abort

### Generation rules (from `ha/system-health`)

- **MUST** create a `system_health.py` module in the `custom_components/<domain>/` folder
- **MUST** import the platform API from `homeassistant.components.system_health` (`SystemHealthRegistration` for the type annotation of the registration)
- **MUST** export a `@callback`-decorated, **synchronous** `async_register(hass, register) -> None` function — the registration is synchronous, only the info gathering is async
- **MUST** register the info callback in `async_register` via `register.async_register_info(async_health_info)`; **MAY** pass a manage URL as a second argument (e.g. `register.async_register_info(async_health_info, "/config/<domain>")`)
- **MUST** provide an `async_health_info(hass) -> dict` callback that returns the displayed info dict
- **SHOULD** set expensive checks (for example URL reachability) as a **coroutine** (without a prior `await`) in the dict — the frontend then shows a waiting indicator and updates the item automatically
- **SHOULD** use the `system_health.async_check_can_reach_url(hass, url)` helper for reachability items instead of a custom HTTP probe; **MAY** carry several reachability items for different endpoints, each through its own helper call
- **MAY** include values like remaining request quota, consumed requests, or the currently connected server as info items
- **MUST NOT** overload system health items with diagnostic data that belongs in the `ha/diagnostics` dump — the page is for short status values
- **SHOULD** translate every info key through the `system_health` section in `strings.json`, so the frontend shows readable descriptions instead of raw keys
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: `system_health.py` exists; `async_register(hass, register) -> None` is decorated with `@callback` and exported; `async_register` registers the info callback via `register.async_register_info(...)`; `async_health_info(hass) -> dict` is defined; expensive reachability checks are set as a coroutine (without a prior `await`); reachability items use `async_check_can_reach_url`; info keys are translated in `strings.json` under `system_health:`
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/system-health`, plus the changed file paths

### Prohibitions

- **MUST NOT** use system health as a replacement for `ha/diagnostics` — full, structured dumps belong in the diagnostics download
- **MUST NOT** escalate a connectivity item into a repairs issue — that is `ha-repairs-add` / repairs
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill runs the at-a-glance value check and discourages purely local integrations without a meaningful status
- [ ] `custom_components/<domain>/system_health.py` exists
- [ ] `async_register(hass, register) -> None` is decorated with `@callback` and exported
- [ ] `async_register` registers the info callback via `register.async_register_info(...)`
- [ ] `async_health_info(hass) -> dict` is defined as the info callback and returns the displayed dict
- [ ] Expensive reachability checks are set as a coroutine (without a prior `await`) in the info dict
- [ ] Reachability items use `system_health.async_check_can_reach_url(hass, url)` instead of manual HTTP probes
- [ ] Info keys are translated through the `system_health` section in `strings.json`; report names the file paths

## Open questions

- **Implementation threshold**: When does the skill require `system_health.py`? Currently SHOULD for backend-backed integrations; a calibrated trigger (for example "every integration with a cloud IoT class") is missing — `ha/system-health` leaves it open.
- **Multiple config entries**: The doc example grabs `async_entries(DOMAIN)[0]`. How should the callback aggregate across multiple entries of the same integration? Currently not standardised; the skill asks when in doubt.
- **Translation obligation**: Is the `strings.json` translation of the info keys a MUST or a SHOULD? `ha/system-health` formulates SHOULD; the skill follows it.
