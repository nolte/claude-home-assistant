# HA Integration: Significant Change

Status: draft

## Context

Home Assistant doesn't only collect data, it also exports it to various consumers — HomeKit, voice assistants, logbook aggregators, external bridges. Not all of these services are interested in every state change. A temperature sensor that wobbles by 0.1 degrees Celsius, a battery that loses 0.1 % charge, a light that jumps by 2 brightness steps — such micro-changes create noise at the consumer without value.

To let consumers filter out insignificant changes, HA provides the **significant-change platform**: the integration adds a `significant_change.py` platform module with a function `async_check_significant_change`. This function is passed a state that was previously considered significant and the new state — not the last two known states — and decides whether the difference is significant enough to be reported to consumers. The source (`developers.home-assistant`, `docs/core/platform/significant_change.md`) describes the pattern; this spec lifts it into an obligation for integrations with continuous values.

This spec delimits clearly from `ha/coordinator-patterns`: `always_update` controls whether a **coordinator listener** (that is, an entity) re-renders at all on a tick; significant change controls whether an already-rendered state is reported to **external consumers**. These are two different filter layers.

## Goals

- Establish `significant_change.py` as the standard module for integrations with continuous values (sensors, climate)
- Make `async_check_significant_change` mandatory with HA's prescribed signature and the three-value semantics (`True` / `False` / `None`)
- Prescribe device-class-based threshold logic, so entity types are treated differently
- Draw the boundary to `always_update` (coordinator-listener trigger) clearly, so the two filter layers are not confused

## Non-Goals

- Coordinator `always_update` logic — belongs in `ha/coordinator-patterns`; significant change is reporting to consumers, `always_update` is triggering the coordinator listeners
- Consumer-side filter implementation (how HomeKit or voice evaluates the return value) — lives outside the integration
- Significant change for purely discrete entities (binary sensor, switch, select) without a continuous value range — there the default behavior is sufficient
- Per-consumer threshold calibration — the function yields a single significance decision, not consumer-specific thresholds

## Requirements

### Purpose & consumers

- **MUST** understand significant-change support as the mechanism by which the integration tells HA and downstream consumers (HomeKit, voice, bridges) whether a state change is significant enough to be reported
- **MUST** make insignificant changes filterable — the examples named in the source (battery loses 0.1 % charge, temperature sensor changes by 0.1 Celsius, light changes by 2 brightness steps) count as insignificant
- **MUST NOT** assume the function receives the last two known states — it is passed a state that was previously considered significant and the new state

### `significant_change.py` platform

- **MUST** provide the support through a `significant_change.py` platform module in `custom_components/<domain>/` once the integration exports continuous values
- **MUST** export the function `async_check_significant_change` as a top-level function in that module — HA invokes it automatically when a consumer checks the significance of a change
- **MAY** scaffold the module via `python3 -m script.scaffold significant_change` (upstream core workflow); in a Custom Integration the file is created manually following the same scheme

### `async_check_significant_change` signature

- **MUST** use HA's prescribed signature:

```python
from typing import Any, Optional
from homeassistant.core import HomeAssistant, callback

@callback
def async_check_significant_change(
    hass: HomeAssistant,
    old_state: str,
    old_attrs: dict,
    new_state: str,
    new_attrs: dict,
    **kwargs: Any,
) -> bool | None:
```

- **MUST** decorate the function with `@callback` — it runs synchronously in the event loop and must not block
- **MUST** carry the `**kwargs: Any` parameter in the signature, so future HA extensions do not break the function

### Thresholds & device-class logic

- **MUST** take all known attributes into account in the significance decision (`old_attrs`, `new_attrs`), not just the bare state value
- **MUST** use device classes to differentiate between entity types — a temperature threshold does not apply to a brightness or battery value
- **SHOULD** define an absolute threshold per device class (for example temperature changes by >= X degrees), below which the change counts as insignificant
- **MAY** use existing HA helpers like `check_absolute_change` and `check_valid_float` from the significant-change module to validate float values and check absolute differences against a threshold

### Return semantics (True/False/None)

- **MUST** return `True` when the change is significant and should be reported to consumers
- **MUST** return `False` when the change counts as insignificant and should not be reported
- **MUST** return `None` when the function cannot decide — HA then applies its default behavior
- **MUST NOT** handle `unknown` and `unavailable` transitions itself — HA handles these cases automatically

### When to implement

- **SHOULD** implement significant change when the integration exports entities with continuous values (sensors with measurement scales, climate entities with temperature/humidity values)
- **MUST NOT** implement significant change for purely discrete entities without a continuous value range — there HA's default behavior is sufficient and an extra filter only adds effort
- **MAY** omit the module when the integration exclusively exports state transitions with discrete, already infrequent change

## Acceptance Criteria

- [ ] `custom_components/<domain>/significant_change.py` exists once the integration exports continuous values
- [ ] `async_check_significant_change` is exported as a top-level function with the prescribed signature (`hass`, `old_state`, `old_attrs`, `new_state`, `new_attrs`, `**kwargs`)
- [ ] The function is decorated with `@callback` and carries the `**kwargs: Any` parameter
- [ ] The significance decision takes `old_attrs`/`new_attrs` into account and differentiates via device classes
- [ ] An absolute threshold is defined per relevant device class (for example via `check_absolute_change`)
- [ ] The function returns exclusively `True`, `False`, or `None` — `None` for "don't know"
- [ ] There is no own handling of `unknown`/`unavailable` in the function

## Open Questions

- **Threshold source**: Should the device-class thresholds (temperature, brightness, battery) be standardised as portfolio-wide constants, or calibrated per integration? Currently formulated as SHOULD per device class.
- **`check_absolute_change` availability**: The helpers `check_absolute_change`/`check_valid_float` come from the core significant-change module. Up to which HA minimum version are they stably importable, and is a fallback needed when the portfolio-wide minimum version does not guarantee them?
- **Delimitation from `always_update`**: Both filters act on micro-changes, but at different layers (coordinator listener vs. consumer report). Is the textual delimitation enough, or is a shared example needed that shows both filters in the same data flow?
- **Discrete-vs-continuous threshold**: When does an entity count as "continuous enough" to require the module? Currently formulated as SHOULD for sensors/climate; a calibrated trigger is missing.
