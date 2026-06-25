---
name: ha-reproduce-state-add
description: Augment an existing Home Assistant Custom Integration with scene / reproduce-state support, conforming to spec/ha/reproduce-state. Creates a reproduce_state.py platform module exporting the top-level async function async_reproduce_states(hass, states, context=None) that gathers per-entity async_reproduce_state coroutines; each maps a target State (state string plus relevant attributes) onto the domain's own service actions, skips entities already in the desired state, and passes the supplied context through. Sources Context/HomeAssistant/State from homeassistant.core, never manipulates state directly via hass.states.async_set, and reports the Bronze quality-scale marker. Activate on "add reproduce_state", "make my entities scene-capable", "füge Scene-/Reproduce-State-Support hinzu". Do not activate for writing or using scenes in config (ha-automation/scene), for the called service actions themselves (ha-service-definition-generator / ha/services), for the entity command methods that set the states (the entity platform), or for deploying to a live HA instance.
tags: [home-assistant, custom-integration, reproduce-state]
---

# HA Reproduce State Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-reproduce-state-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-reproduce-state-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the domain's settable states and reads back the `reproduce_state.py` module and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-coordinator-add`, `ha-repairs-add`, `ha-device-automation-add`).
- **Mid-flow interactivity** — the state-to-service-call mapping and the "is this domain actually scene-relevant" check are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — a single platform module with one entry function and its per-entity coroutines fits inline; no isolated agent context is needed.
- Counter-dimension considered: the map-and-validate loop could be an agent, but the mapping decisions and the scene-relevance advice belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add scene / reproduce-state support to an existing integration whose entities have settable target states — so they can be included in a scene and restored when that scene is activated.

## When NOT to activate

- writing or using scenes in config / automations → `ha-automation/scene`
- the service actions or `services.yaml` the mapping calls → `ha-service-definition-generator` / `ha/services`
- the entity command methods that actually set the states (`async_turn_on` etc.) → the entity platform
- greenfield integration scaffolding → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One module, offline.** Add exactly one `reproduce_state.py`; generation never touches a live HA instance.
2. **Read [`ha/reproduce-state`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/reproduce-state/de.md) first.** Do not generate from memory.
3. **Scene-relevance check.** Confirm the domain is expectably used in scenes and has settable target states; discourage it for pure read-only sensor domains (reproduce state may be omitted there).
4. **Signature contract.** Export `async_reproduce_states(hass, states, context=None)` as a top-level async function; `states` is an `Iterable[State]`, `context` an optional `Context`, and it returns `None` (the effect comes from service calls). Source `Context`/`HomeAssistant`/`State` from `homeassistant.core`.
5. **Per-entity coroutines.** `async_reproduce_states` only aggregates; gather one `async_reproduce_state` coroutine per supplied `State` and execute them (`asyncio.gather` when parallel reproduction is wanted).
6. **Map to service actions, not state.** Map each `State` (state string plus relevant attributes) onto the domain's own service action(s) that drive the entity into that state. **Never** set state directly via `hass.states.async_set`.
7. **Idempotent.** Skip entities already in the target state — no service call for those.
8. **Context pass-through.** Forward the supplied `context` to every triggered service call so reproduction actions stay attributed to the same context.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `states` | yes | — | the domain's settable states, in prose, that a scene should restore |
| `service_map` | no | derived + confirmed | the service action(s) per state |
| `attributes` | no | derived | the relevant `State` attributes per state |
| `parallel` | no | sequential | reproduce entities in parallel via `asyncio.gather` |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Confirm the domain is scene-relevant (settable target states). If it is a read-only sensor domain, surface that reproduce state may be omitted before proceeding.
3. Read `ha/reproduce-state`.
4. `reproduce_state.py` is not already present. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the states to reproduce, the service action mapped to each (incl. relevant attributes), and whether reproduction runs in parallel, in one paragraph. Wait for confirmation.

### 2) Generate

Create `custom_components/<domain>/reproduce_state.py` (following the HA scaffold pattern as the reference skeleton):

- top-level `async def async_reproduce_states(hass, states, context=None)` returning `None`, with `Context`/`HomeAssistant`/`State` imported from `homeassistant.core`;
- a per-entity `async def async_reproduce_state(...)` coroutine that skips entities already in the target state, otherwise maps the `State` (state string plus relevant attributes) onto the domain's service action(s) and passes `context` through;
- `async_reproduce_states` gathers the per-entity coroutines (sequentially, or via `asyncio.gather` when parallel).

### 3) Validate and report

Validate offline (`reproduce_state.py` present; `async_reproduce_states(hass, states, context=None)` top-level async returning `None`; `states` typed `Iterable[State]`; types from `homeassistant.core`; each `State` mapped onto service action(s); `grep` for `hass.states.async_set` returns no hits; already-matching entities skipped; `context` forwarded). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/reproduce-state` acceptance criteria, plus the changed file paths and the quality-scale marker (**Bronze**).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Writing / using scenes → `ha-automation/scene`
- Called service actions → `ha-service-definition-generator` / `ha/services`
- Entity command methods that set the states → the entity platform
- Greenfield scaffold → `ha-integration-scaffold`
- Deploy to live HA → out of scope
