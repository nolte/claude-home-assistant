# Skill: `ha-significant-change-add`

Status: draft

## Context

`ha/significant-change` defines the significant-change platform: HA doesn't only export states, it also reports them to consumers (HomeKit, voice assistants, logbook, external bridges). An integration participates by providing a `significant_change.py` platform module with the top-level function `async_check_significant_change`. HA invokes this function automatically when a consumer checks the significance of a change — it is passed a state that was previously considered significant and the new state (not the last two known states). The function decides with the three-value semantics (`True` significant, `False` insignificant, `None` no decision) whether the change should be reported. No skill augments this so far. Significant change must be delimited clearly from `always_update`: `always_update` triggers the coordinator listener (re-render of an entity), significant change filters the reporting to external consumers — two different filter layers.

This skill augments the `significant_change.py` module into an **existing** integration once it exports continuous values: the platform module, the `@callback async_check_significant_change` function with the prescribed signature, the per-device-class threshold logic, and the three-value return — conformant to `ha/significant-change`. Before generating it checks whether the integration exports continuous values at all.

## Scope

Augmenting significant-change support per run into an existing `custom_components/<domain>/` integration: the `significant_change.py` platform module, the top-level function `async_check_significant_change` with HA's signature (`hass`, `old_state`, `old_attrs`, `new_state`, `new_attrs`, `**kwargs`), the `@callback` decoration, the per-domain / per-device-class threshold logic (optionally via `check_absolute_change` / `check_valid_float`), and the three-value return (`True`/`False`/`None`). The skill reads `ha/significant-change` and validates.

## Goals

- Derive the relevant thresholds from the exported entity types (device classes) and augment the module spec-conformantly
- Enforce HA's prescribed signature and the `@callback` decoration — including `**kwargs: Any`, so future HA extensions do not break it
- Prescribe per-device-class threshold logic so entity types are treated differently (a temperature threshold does not apply to brightness or battery)
- Enforce the three-value semantics: `True` significant, `False` insignificant, `None` no decision (HA default)
- Save the user from unnecessary modules: only integrations with continuous values need the module, and draw the boundary to `always_update` clearly

## Non-Goals

- The native value of the entity itself (how the state comes to be) — entity platform / `ha/entity-architecture`
- Coordinator `always_update` logic (triggering the coordinator listener) — `ha/coordinator-patterns`
- Consumer-side filter implementation (how HomeKit/voice evaluates the return value) — lives outside the integration
- Significant change for purely discrete entities without a continuous value range — there HA's default suffices
- Greenfield scaffolding of an integration — `ha-integration-scaffold`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add significant change", "add a significant_change checker", "throttle insignificant updates"
  - "stop reporting micro-changes to HomeKit / voice"
  - "füge Significant-Change-Logik hinzu", "filtere unbedeutende Updates"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the exported entity types / device classes with continuous values
- **MAY** capture: the per-device-class thresholds (e.g. temperature >= X degrees) and whether HA helpers (`check_absolute_change`/`check_valid_float`) should be used

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** run the need check: does the integration export continuous values (sensors with measurement scales, climate)? For purely discrete entities the skill **MUST NOT** augment the module and **SHOULD** discourage it. The skill **MUST** name the boundary to `always_update` (coordinator listener vs. consumer report)
- **MUST** read the `ha/significant-change` spec
- **MUST NOT** overwrite an existing `significant_change.py`; on collision abort

### Generation rules (from `ha/significant-change`)

- **MUST** create the `significant_change.py` platform module in `custom_components/<domain>/`
- **MUST** export `async_check_significant_change` as a top-level function with the prescribed signature: `(hass: HomeAssistant, old_state: str, old_attrs: dict, new_state: str, new_attrs: dict, **kwargs: Any) -> bool | None`
- **MUST** decorate the function with `@callback` — it runs synchronously in the event loop and must not block — and carry the `**kwargs: Any` parameter
- **MUST** take `old_attrs`/`new_attrs` into account in the decision, not just the bare state value
- **MUST** use device classes to differentiate between entity types; **SHOULD** define an absolute threshold per relevant device class, below which the change counts as insignificant
- **MAY** use HA helpers like `check_absolute_change` and `check_valid_float` to validate float values and check absolute differences against a threshold
- **MUST** return exclusively `True` (significant, report), `False` (insignificant, do not report), or `None` (no decision, HA default)
- **MUST NOT** handle `unknown`/`unavailable` transitions itself — HA handles these cases automatically
- **MUST NOT** assume the function receives the last two known states — it is passed a state previously considered significant and the new state
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: `significant_change.py` exists; `async_check_significant_change` is top-level with the prescribed signature and `**kwargs: Any`; the function is `@callback`-decorated; the decision uses `old_attrs`/`new_attrs` and differentiates via device classes; a threshold is defined per relevant device class; the return is restricted to `True`/`False`/`None`; there is no own `unknown`/`unavailable` handling
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/significant-change`, plus the changed file paths and the note on the boundary to `always_update`

### Prohibitions

- **MUST NOT** augment the module for purely discrete entities without a continuous value range
- **MUST NOT** implement consumer-specific thresholds or filter evaluation — the function yields a single significance decision
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill runs the need check (continuous values?) incl. the delimitation from `always_update`
- [ ] `custom_components/<domain>/significant_change.py` exists
- [ ] `async_check_significant_change` is top-level with the prescribed signature (`hass`, `old_state`, `old_attrs`, `new_state`, `new_attrs`, `**kwargs`)
- [ ] The function is `@callback`-decorated and carries the `**kwargs: Any` parameter
- [ ] The decision takes `old_attrs`/`new_attrs` into account and differentiates via device classes with an absolute threshold per relevant device class
- [ ] The function returns exclusively `True`, `False`, or `None`; no own `unknown`/`unavailable` handling
- [ ] Report names the file paths and the boundary to `always_update`

## Open questions

- **Threshold source**: Should the device-class thresholds (temperature, brightness, battery) be standardised portfolio-wide as constants, or calibrated per integration? `ha/significant-change` formulates it as SHOULD per device class; the skill asks when in doubt.
- **`check_absolute_change` availability**: The helpers come from the core significant-change module. Up to which HA minimum version are they stably importable, and is a fallback needed? Open in `ha/significant-change`; the skill follows the MAY rule stated there.
- **Discrete-vs-continuous threshold**: When does an entity count as "continuous enough" to require the module? Currently the skill runs the need check as a dialogue and discourages it for purely discrete entities.
