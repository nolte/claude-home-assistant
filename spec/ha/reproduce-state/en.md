# HA Integration: Reproduce State (Scene Support)

Status: draft

## Context

Home Assistant supports **scenes**. A scene is a collection of (partial) entity states. When a scene is activated, HA tries to call the right service actions to get the states specified in the scene into place. Integrations are responsible for adding the ability for HA to call the right service actions to reproduce the states of a scene for their domain.

HA provides the entry point through a **scaffold template**: from an HA dev environment, `python3 -m script.scaffold reproduce_state` generates the module plus the method skeleton. Going the manual route means creating a file `reproduce_state.py` in the integration folder and implementing the method `async_reproduce_states`. That method receives a list of `State` objects and drives the entities into exactly those states through the appropriate service calls. This spec lifts the HA reproduce-state platform pattern into a generic obligation for integrations whose domain should carry scene support.

Quality scale marker: **Bronze** (reproduce state is the precondition for a domain's entities to be included in scenes and restored at all).

## Goals

- Establish `reproduce_state.py` as the standard module for every domain whose entities should be part of scenes
- Define `async_reproduce_states` as the single entry point through which HA reproduces the states of a scene
- Fix the mapping of a target `State` onto service calls as the sole reproduction logic — no direct state manipulation
- Keep reproduction idempotent — entities already in the target state are skipped

## Non-Goals

- Writing/defining scenes themselves — scenes are an HA core component; this spec only covers reproducing the states from the domain
- Service definition and `services.yaml` — the called service actions are defined through `ha/services`, here only consumed
- Significant change and diagnostics — separate small HA platform modules, separate specs
- Persistence or history of states — reproduce state establishes a target state but manages no state histories

## Requirements

### Purpose (scene support)

- **MUST** exist once a domain's entities should be includable in scenes and restorable through scene activation — without `reproduce_state.py` HA cannot reproduce that domain's states
- **MUST** establish the states through the appropriate service actions — a scene is a collection of (partial) entity states, and activating a scene calls the right service actions to get those states into place
- **MAY** also be used beyond the classic scene-activation path by applying states directly — the mechanism reproduces a supplied list of states regardless of where they originate

### `reproduce_state.py` platform

- **MUST** include a `reproduce_state.py` module in the integration folder once the domain should carry scene support
- **SHOULD** use the HA scaffold template as the entry point — `python3 -m script.scaffold reproduce_state` from an HA dev environment generates the module and the method skeleton
- **MUST** export the platform function at module level as a top-level async function — HA recognises `reproduce_state.py` as a convention-based platform module and invokes the function

### `async_reproduce_states` signature

- **MUST** export an async function `async_reproduce_states(hass, states, context=None)`, where `states` is an `Iterable[State]` and `context` an optional `Context`
- **MUST** source the types from `homeassistant.core` — `Context`, `HomeAssistant`, `State`
- **MUST** return `None` — the function produces its effect through service calls, not through a return value

### State-to-service-call mapping

- **MUST** map each supplied `State` onto the appropriate service action(s) that drive the entity into exactly that state — the target state is not set directly but established through service calls
- **MUST** take the state attributes of the `State` object into account during mapping insofar as the target-state reproduction requires them — a state carries attributes in addition to the state string
- **MUST NOT** manipulate the entity's state directly (for example via `hass.states.async_set`) instead of through service actions — the HA convention is reproduction through the right service calls

### Idempotency & context

- **SHOULD** skip entities that are already in the target state — no service call is needed for those
- **SHOULD** pass the supplied `context` through to the triggered service calls, so the actions triggered by the reproduction stay attributed to the same context
- **MAY** reproduce multiple entities in parallel (`asyncio`) when several states are to be reproduced at the same time

### When to implement

- **MUST** be implemented once the domain is expectably used in scenes — otherwise its entities are captured by a scene but not restored when the scene is activated
- **MAY** be omitted as long as the domain has no scene-restorable states (for example pure read-only sensor domains without a settable target state)

## Acceptance Criteria

- [ ] `reproduce_state.py` exists in the domain's integration folder
- [ ] `async_reproduce_states(hass, states, context=None)` is exported as a top-level async function and returns `None`
- [ ] `states` is typed as `Iterable[State]`; `Context`/`HomeAssistant`/`State` come from `homeassistant.core`
- [ ] Each supplied `State` is mapped onto appropriate service action(s) (including relevant attributes)
- [ ] A `grep` for `hass.states.async_set` in `reproduce_state.py` returns no hits (reproduction runs through service calls)
- [ ] Entities already in the target state are skipped
- [ ] The supplied `context` is passed through to the triggered service calls
- [ ] Quality scale marker: **Bronze**

## Open Questions

- **Idempotency comparison**: How strictly does the skip path compare "already in the target state" — only the state string or all attributes too? Currently formulated as SHOULD without a calibrated comparison depth.
- **`reproduce_options` parameter**: Newer HA versions pass reproduction-specific options through. The underlying source carries only `context`; whether/how `reproduce_options` becomes mandatory is open.
- **Parallelism**: Up to how many entities is parallel reproduction via `asyncio` sensible, and when do backend rate limits become a risk? Currently formulated as MAY without a threshold.
- **Partial states**: A scene can contain partial states. How does the mapping handle missing attributes — best-effort or strict validation? Not standardised.
