# HA Integration: System Health

Status: draft

## Context

Home Assistant shows a **system health page** for every integration — the user reaches the aggregated overview via **Settings** -> **System** -> **Repairs** and selects **System information** in the top-right three-dots menu. The system health platform lets integrations surface information there that helps the user understand the state of the integration — for example the reachability of an endpoint, the currently connected server, or the remaining request quota.

HA implements this through a `system_health.py` module with an `async_register(hass, register)` function that registers an info callback. The callback `async_health_info(hass)` returns a dict whose values may be of any type — including coroutines. For coroutine values the frontend shows a waiting indicator and updates the item automatically once the coroutine yields a result. For connectivity items the platform provides the `system_health.async_check_can_reach_url(hass, url)` helper.

This spec delimits itself from `ha/diagnostics`: system health is the **at-a-glance status** (short values shown directly in the frontend), diagnostics the **full downloadable dump** (structured JSON file for issue reports). Both are debugging surfaces, but with different purposes. Architecture context comes from `ha/integration-architecture`.

## Goals

- Establish `system_health.py` as the standard module for integrations with backend connectivity or quota limits
- Clearly delimit the at-a-glance status from `ha/diagnostics` — short values here, full dump there
- Standardise connectivity items through the `async_check_can_reach_url` helper instead of manual HTTP probes
- Use coroutine values for expensive checks so the frontend does not block

## Non-Goals

- Full diagnostic dumps — that is `ha/diagnostics`, with its own redaction obligation
- Repairs issues (`async_create_issue`) — separate HA mechanism, separate follow-up spec
- Translating the info keys through `strings.json` in detail — that is the translation spec's concern; referenced here only
- External monitoring systems (Prometheus, healthcheck endpoints) — live outside HA system health

## Requirements

### Purpose

- **MUST** use system health exclusively for **at-a-glance status** — short values the user reads directly in the frontend (reachability, connected server, quota)
- **MUST NOT** use system health as a replacement for `ha/diagnostics` — full, structured dumps belong in the diagnostics download, not on the system health page
- **MAY** be omitted for integrations without backend connectivity or quota semantics — not every integration has meaningful system health items

### `system_health.py` platform

- **MUST** include a `system_health.py` module in `custom_components/<domain>/` when the integration provides system health items
- **MUST** import the platform API from `homeassistant.components.system_health` (`SystemHealthRegistration` for the type annotation of the registration)
- **MUST** carry the `@callback` decorator on the synchronous `async_register` function — the registration is synchronous, only the info gathering is async

### `async_register` & info callback

- **MUST** export an `async_register(hass, register) -> None` function that HA calls when setting up the integration
- **MUST** register the info callback in `async_register` via `register.async_register_info(async_health_info)`
- **MUST** provide an `async_health_info(hass) -> dict` callback that returns the info dict shown on the system health page

```python
"""Provide info to system health."""

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback


@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(async_health_info)
```

### Info items (values & connectivity)

- **MUST** return a dict from `async_health_info` whose values may be of any type — including coroutines
- **SHOULD** set expensive checks (for example URL reachability) as a **coroutine** in the dict instead of awaiting them up front — the frontend then shows a waiting indicator and updates the item automatically once the result is available
- **SHOULD** translate every info key through the `system_health` section in `strings.json`, so the frontend shows readable descriptions instead of raw keys
- **MAY** include values like remaining request quota, consumed requests, or the currently connected server as info items

```python
async def async_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the info page."""
    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    quota_info = await config_entry.runtime_data.async_get_quota_info()

    return {
        "consumed_requests": quota_info.consumed_requests,
        "remaining_requests": quota_info.requests_remaining,
        # checking the url can take a while, so set the coroutine in the info dict
        "can_reach_server": system_health.async_check_can_reach_url(hass, ENDPOINT),
    }
```

### `async_check_can_reach_url`

- **SHOULD** use the `system_health.async_check_can_reach_url(hass, url)` helper for reachability items instead of writing a custom HTTP probe
- **MUST** place the helper call as a coroutine value (without a prior `await`) in the info dict — the check can take a while and must not block the frontend
- **MAY** carry several reachability items for different endpoints (for example API and auth server), each through its own helper call

### When to implement

- **SHOULD** implement `system_health.py` once the integration has a cloud or network backend with reachability- or quota-relevant state
- **MAY** be omitted when the integration works purely locally and has no meaningful at-a-glance status
- **MUST NOT** overload system health items with diagnostic data that belongs in the `ha/diagnostics` dump — the page is for short status values, not full data states

## Acceptance Criteria

- [ ] `custom_components/<domain>/system_health.py` exists (when the integration provides system health items)
- [ ] `async_register(hass, register) -> None` is decorated with `@callback` and exported
- [ ] `async_register` registers the info callback via `register.async_register_info(...)`
- [ ] `async_health_info(hass) -> dict` is defined as the info callback and returns the displayed dict
- [ ] Expensive reachability checks are set as a coroutine (without a prior `await`) in the info dict
- [ ] Reachability items use `system_health.async_check_can_reach_url(hass, url)` instead of manual HTTP probes
- [ ] Info keys are translated through the `system_health` section in `strings.json`

## Open Questions

- **Implementation threshold**: When does the spec require `system_health.py`? Currently SHOULD for backend-backed integrations; a calibrated trigger (for example "every integration with a cloud IoT class") is missing.
- **Multiple config entries**: The doc example grabs `async_entries(DOMAIN)[0]`. How should the callback aggregate across multiple entries of the same integration? Currently not standardised.
- **Delimitation from Repairs**: Reachability status on the system health page vs. a repairs issue on a persistent outage — when does a connectivity item escalate to a repairs issue? Separate follow-up spec.
- **Translation obligation**: Is the `strings.json` translation of the info keys a MUST or a SHOULD? Currently formulated as SHOULD.
