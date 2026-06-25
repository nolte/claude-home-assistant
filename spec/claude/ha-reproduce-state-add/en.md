# Skill: `ha-reproduce-state-add`

Status: draft

## Context

`ha/reproduce-state` defines an integration's scene-support pattern: for a domain's entities to be includable in **scenes** and restored on activation, the integration folder needs a convention-based platform module `reproduce_state.py` with the top-level async function `async_reproduce_states(hass, states, context=None)`. That function receives an `Iterable[State]` and drives each entity into exactly that state through its own domain's **appropriate service actions** — never through direct state manipulation. No skill augments this so far. The quality-scale marker is **Bronze**, because reproduce state is the precondition for a domain's entities to be includable in scenes and restored at all.

This skill augments scene/reproduce-state support into an **existing** integration: the `reproduce_state.py` module, the `async_reproduce_states` function with its per-entity `async_reproduce_state` coroutines, the state-to-service-call mapping (state string plus relevant attributes), the idempotency skip for entities already in the desired state, and the context pass-through — conformant to `ha/reproduce-state`. Generation is offline; the skill never deploys to a running HA instance.

## Scope

Augmenting the reproduce-state platform module into an existing `custom_components/<domain>/` integration: the `reproduce_state.py` file, the top-level function `async_reproduce_states(hass, states, context=None)`, the per-entity `async_reproduce_state` coroutines it gathers, the state-to-service-call mapping incl. relevant attributes, the idempotency skip, and the context pass-through to the triggered service calls. The skill reads `ha/reproduce-state` and validates.

## Goals

- Derive a spec-conformant `reproduce_state.py` from a domain's settable states, with `async_reproduce_states(hass, states, context=None)` as the single entry point
- Enforce the signature: `states` as `Iterable[State]`, `context` optional, returning `None`; `Context`/`HomeAssistant`/`State` from `homeassistant.core`
- Fix the state-to-service-call mapping as the sole reproduction logic — the target state is established through service actions, never via `hass.states.async_set`
- Take the state attributes into account during mapping insofar as the target-state reproduction requires them
- Keep reproduction idempotent (skip entities already in the desired state) and pass the `context` through to the triggered service calls

## Non-Goals

- Writing/defining scenes themselves — `ha-automation/scene` (scenes are an HA core component; only the reproduction by the domain is augmented here)
- The service actions / `services.yaml` the mapping calls — `ha-service-definition-generator` / `ha/services` (here only consumed)
- The entity command methods themselves (`async_turn_on` etc.) that actually set the states — the respective entity platform
- Significant change and diagnostics — separate small HA platform modules, separate specs
- Greenfield scaffolding of an integration — `ha-integration-scaffold`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add reproduce_state", "make my entities scene-capable", "add scene support to this integration"
  - "let these entities be restored when a scene is activated"
  - "füge Scene-/Reproduce-State-Support hinzu", "mach meine Entities scene-fähig"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the domain's settable states (prose), from which the skill derives the state-to-service-call mapping
- **MAY** capture: the concrete service actions per state, the relevant attributes per state, and whether reproduction should run in parallel (`asyncio`)

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** confirm the domain is expectably used in scenes and has settable target states; pure read-only sensor domains without a settable target state **SHOULD** be discouraged (reproduce state **MAY** be omitted there)
- **MUST** read the `ha/reproduce-state` spec
- **MUST NOT** overwrite an existing `reproduce_state.py`; on collision abort

### Generation rules (from `ha/reproduce-state`)

- **MUST** create a `reproduce_state.py` module in the integration folder and **SHOULD** follow the HA scaffold pattern (`python3 -m script.scaffold reproduce_state` as the reference skeleton, not run live)
- **MUST** export `async_reproduce_states(hass, states, context=None)` as a top-level async function; `states` is an `Iterable[State]`, `context` an optional `Context`, the return value `None`
- **MUST** source `Context`, `HomeAssistant`, and `State` from `homeassistant.core`
- **MUST** gather one `async_reproduce_state` coroutine per entity (one per supplied `State`) and execute them — `async_reproduce_states` only aggregates, the per-entity reproduction logic lives in the per-entity coroutine
- **MUST** map each supplied `State` onto the appropriate service action(s) of its own domain that drive the entity into exactly that state — the target state is never set directly
- **MUST** take the state attributes of the `State` object into account during mapping insofar as the target-state reproduction requires them
- **MUST NOT** manipulate the state directly (for example `hass.states.async_set`) instead of through service actions
- **SHOULD** skip entities that are already in the target state (state string, and relevant attributes where applicable) — no service call is needed for those
- **SHOULD** pass the supplied `context` through to the triggered service calls, so the reproduction actions stay attributed to the same context
- **MAY** reproduce multiple entities in parallel (`asyncio.gather` over the per-entity coroutines) and provide for a forward-compatible `reproduce_options` parameter where the target HA version passes it through
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: `reproduce_state.py` exists; `async_reproduce_states(hass, states, context=None)` is top-level async and returns `None`; `states` is an `Iterable[State]`; `Context`/`HomeAssistant`/`State` come from `homeassistant.core`; each `State` is mapped onto service action(s); a `grep` for `hass.states.async_set` returns no hits; entities already in the desired state are skipped; `context` is passed through
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/reproduce-state`, plus the changed file paths and the quality-scale marker (**Bronze**)

### Prohibitions

- **MUST NOT** set the entity's state directly instead of through service actions
- **MUST NOT** define scenes or implement the called service actions themselves
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] `reproduce_state.py` exists in the domain's integration folder
- [ ] `async_reproduce_states(hass, states, context=None)` is exported as a top-level async function and returns `None`
- [ ] `states` is typed as `Iterable[State]`; `Context`/`HomeAssistant`/`State` come from `homeassistant.core`
- [ ] Each supplied `State` is mapped onto appropriate service action(s) (incl. relevant attributes), via per-entity `async_reproduce_state` coroutines
- [ ] A `grep` for `hass.states.async_set` in `reproduce_state.py` returns no hits
- [ ] Entities already in the target state are skipped
- [ ] The supplied `context` is passed through to the triggered service calls
- [ ] Report names the file paths and the quality-scale marker **Bronze**

## Open questions

- **Idempotency comparison**: How strictly does the skip path compare "already in the target state" — only the state string or all attributes too? `ha/reproduce-state` formulates it as a SHOULD without a calibrated comparison depth; the skill follows the doc pattern and asks when in doubt.
- **`reproduce_options` parameter**: Newer HA versions pass reproduction-specific options through. The underlying source carries only `context`; whether/how the skill mandates `reproduce_options` in the signature is open — currently a MAY.
- **Parallelism**: Up to how many entities is parallel reproduction via `asyncio` sensible, and when do backend rate limits become a risk? Currently formulated as a MAY without a threshold.
- **Partial states**: A scene can contain partial states. How does the mapping handle missing attributes — best-effort or strict validation? Not standardised; case-by-case.
