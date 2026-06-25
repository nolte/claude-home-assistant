---
name: ha-significant-change-add
description: Augment an existing Home Assistant Custom Integration with a significant-change checker, conforming to spec/ha/significant-change. Creates significant_change.py with a top-level @callback async_check_significant_change(hass, old_state, old_attrs, new_state, new_attrs, **kwargs) -> bool | None, applying per-domain / per-device-class threshold logic (return True if significant, False if insignificant, None if undecided) so recorder/cloud/Google/Alexa/HomeKit can throttle insignificant updates. Runs a need check (only integrations exporting continuous values qualify) and draws the boundary to coordinator always_update. Activate on "add significant change", "throttle insignificant updates", "stop reporting micro-changes to HomeKit", "füge Significant-Change-Logik hinzu". Do not activate for the entity's native value (ha/entity-architecture), coordinator always_update (ha/coordinator-patterns), greenfield scaffolding (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, significant-change]
---

# HA Significant Change Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-significant-change-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-significant-change-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the exported entity types and reads back the `significant_change.py` module, the thresholds, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-repairs-add`).
- **Mid-flow interactivity** — the need check (continuous values?) and the per-device-class threshold choices are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — one platform module with one function and its threshold logic fits inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the need check and the threshold calibration belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add the `significant_change.py` module to an existing integration that exports **continuous values** (sensors with measurement scales, climate entities), so consumers (recorder, cloud, Google, Alexa, HomeKit, voice) can throttle insignificant updates.

## When NOT to activate

- the entity's native value / how the state comes to be → `ha/entity-architecture`
- coordinator `always_update` (re-rendering the coordinator listener) → `ha/coordinator-patterns`
- greenfield integration scaffolding → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **Continuous values only.** Run a need check first: the module is for integrations exporting continuous values; for purely discrete entities (binary sensor, switch, select) HA's default suffices — discourage it and abort. State the boundary to `always_update` in the report.
2. **Read [`ha/significant-change`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/significant-change/de.md) first.** Do not generate from memory.
3. **Prescribed signature.** Export `async_check_significant_change(hass: HomeAssistant, old_state: str, old_attrs: dict, new_state: str, new_attrs: dict, **kwargs: Any) -> bool | None` as a **top-level** function. Carry `**kwargs: Any` so future HA extensions do not break it.
4. **`@callback`, non-blocking.** Decorate the function with `@callback` — it runs synchronously in the event loop and must not block.
5. **Three-value return.** Return `True` (significant → report), `False` (insignificant → do not report), or `None` (cannot decide → HA applies its default). Nothing else.
6. **Device-class thresholds.** Use `old_attrs`/`new_attrs`, not just the bare state. Differentiate via device classes; define an absolute threshold per relevant device class (a temperature threshold does not apply to brightness or battery). You **may** use `check_absolute_change` / `check_valid_float` from the core significant-change module.
7. **No `unknown`/`unavailable` handling.** HA handles those transitions automatically; do not reimplement them.
8. **Previously-significant state, not last-two.** The function is passed a state previously considered significant and the new state — never assume the last two known states.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `entity_types` | yes | — | the exported entity types / device classes with continuous values |
| `thresholds` | no | derived + confirmed | per-device-class absolute thresholds (e.g. temperature >= X) |
| `use_helpers` | no | asked when relevant | use `check_absolute_change` / `check_valid_float` |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Run the need check: does the integration export continuous values? If purely discrete, discourage and abort. Name the boundary to `always_update`.
3. Read `ha/significant-change`.
4. `significant_change.py` is not already present. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the exported entity types / device classes, the per-device-class thresholds, whether HA helpers are used, and the `always_update` boundary in one paragraph. Wait for confirmation.

### 2) Generate

Write `custom_components/<domain>/significant_change.py` with the top-level `@callback async_check_significant_change(hass, old_state, old_attrs, new_state, new_attrs, **kwargs) -> bool | None`. Implement per-device-class branches that compare `old_attrs`/`new_attrs` against the absolute thresholds (optionally via `check_absolute_change` / `check_valid_float`), returning `True`/`False`, and fall through to `None` for undecided cases. Do not handle `unknown`/`unavailable`.

### 3) Validate and report

Validate offline (module present; `async_check_significant_change` top-level with the prescribed signature and `**kwargs: Any`; `@callback`-decorated; decision uses `old_attrs`/`new_attrs` and differentiates via device classes with a threshold per relevant device class; return restricted to `True`/`False`/`None`; no `unknown`/`unavailable` handling). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/significant-change` acceptance criteria, plus the changed file paths and the note on the boundary to `always_update`.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- The entity's native value → `ha/entity-architecture`
- Coordinator `always_update` → `ha/coordinator-patterns`
- Greenfield scaffold → `ha-integration-scaffold`
- Deploy to live HA → out of scope
