# HA Automation: Using Scene

Status: draft

## Context

The `scene` integration bundles a set of entities into a named **target state**: "A scene captures the states you want certain entities to be in." On activation, HA sets every entity listed in the scene to its defined states and attributes — e.g. "Romantic" = ceiling light dimmed, TV back light on. A scene therefore describes only a static target state, no sequence and no logic.

Its **real category**, per the integration card, is **"Organization"**, not Automation — the scene is an organization building block that is *referenced* from automations, scripts, and dashboards. This spec files it under the `ha-automation` corpus because, from the automation author's point of view, it is an action target (`scene.turn_on`), not because HA classifies it under Automation. That is disclosed honestly here.

A scene entity is **stateless** in the usual sense: its state is "the timestamp of when it was last called, either via the Home Assistant UI or via an action." Possible values are that timestamp plus `unavailable`/`unknown`. There is deliberately **no** `scene.turn_off`.

Verified sources: [`/integrations/scene/`](https://www.home-assistant.io/integrations/scene/) (YAML schema, services `scene.turn_on`/`apply`/`create`/`delete`/`reload`, `snapshot_entities`, state = timestamp of last activation, "Organization" category, trigger `scene.activated`) and [`/docs/scene/`](https://www.home-assistant.io/docs/scene/) (scene definition, `transition`, inline `scene.apply`).

## When to Use

Use `scene` whenever a **named static target state** for a set of entities should be defined and activated via `scene.turn_on` — with no sequence, logic, or computed values. Typical use cases:

- **Mood/mode preset** — define "Romantic", "Movie night", "Wake up" as a fixed target state of several lights (dimmed, color, on/off) and activate it on a button press or from an automation
- **Setting several entities at once** — bring a collection of lights, switches, and media to defined states and attributes (`brightness`, `color_mode`, `xy_color`) in a single step
- **Smooth light change** — pass a `transition` (seconds) to `scene.turn_on` for capable light entities so the state is set softly rather than hard
- **One-off inline state** — apply a target state directly with `scene.apply` without defining it as a scene first (for non-reused states)
- **Save/restore** — snapshot via `scene.create` with `snapshot_entities` before an intervention and restore via `scene.turn_on` afterwards (short-lived, does not survive a reload)

A scene is the right tool as soon as the matter is an **absolute, static target state**. Once order, time, or logic is involved, a script is right; to bundle several entities under one combined state, use a group (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the YAML schema of a scene (`scene:` list with `name`, `entities`, optional `icon`) as binding
- Fix the two forms of per-entity state (direct state vs. state + attributes)
- Govern the correct use of `scene.turn_on` (incl. `transition`), `scene.apply` (inline states), and `scene.create` (snapshot scenes, `snapshot_entities`)
- Turn the documented properties (no `scene.turn_off`, `transition` lights only, `scene.create` does not survive a reload, state = timestamp) into checkable rules
- Clearly delimit when a scene is **not** the right tool (script, group, toggle, dynamic values)

## Non-Goals

- Action/sequence syntax (sequence, `delay`, `choose`, `repeat`) — `ha-automation/script`
- The trigger/condition/action model that calls scenes — `ha-automation/automation`
- Group semantics (one entity from many) — `ha-automation/group`
- Computed/derived state values — `ha-automation/template`
- The naming dimension (`name`/`id`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here

## Requirements

### Configuration

- **MUST** define a static scene through the top-level key `scene:` as a **list**; each entry carries `name` and `entities`, optionally `icon`
- **MUST** map each entity under `entities` to its target state — either as a **direct state** (`light.tv_back_light: "on"`) or as **state + attributes** via the nested `state:` key plus attribute keys (`brightness`, `color_mode`, `xy_color`, etc.)
- **MUST** use attribute keys only under the nested form; a direct scalar value sets the state only, no attributes
- **SHOULD** keep the `name` English and ≤50 characters and not use a volatile UI timestamp as identity (mechanics: `ha/naming-conventions`)
- **SHOULD** call `scene.reload` after changes to the YAML configuration instead of restarting HA
- **MUST** be aware that the scene sets **only the listed entities**; entities not listed are left untouched (a scene is additive, not exclusive)

### Use in Automations & Templates

- **MUST** activate a predefined scene through the action `scene.turn_on` with `target: { entity_id: scene.<id> }`; there is **no** `scene.turn_off` — a scene is not "turned off"
- **MAY** pass a `transition` (seconds) to `scene.turn_on`; per the docs, `transition` is supported by **lights only**, and only when the light itself supports it
- **MAY** apply a target state **inline** with `scene.apply` without defining it as a scene first (`data.entities` in the same format as the configuration, optional `transition`) — useful for one-off, non-reused states
- **MAY** create a scene at runtime with `scene.create`; `scene_id` is required (lowercase, underscores), and at least one of `entities` (explicit target states) or `snapshot_entities` (current state of the named entities at creation time) MUST be given — both can be combined
- **MUST** note that scenes created via `scene.create` are **not persistent**: "This scene will be discarded after reloading the configuration" — they survive neither a restart nor `scene.reload`; the same `scene_id` overwrites an existing created scene
- **MAY** use the classic save/restore pattern: snapshot via `scene.create` with `snapshot_entities` before an intervention and restore via `scene.turn_on` afterwards; `scene.delete` removes a created scene
- **MAY** read the scene state — it is the **timestamp of the last activation**, not "on/off" — and react to the `scene.activated` trigger when an action should run on scene activation

### Delimitation: When NOT to Use

- **MUST NOT** use a scene for a **sequence** with steps, waits, or branching — a scene only sets a static target state and knows neither `delay`/`wait_template` nor `choose`/`repeat`; once order, time, or logic is involved, a **script** (`ha-automation/script`) is the right construct
- **MUST NOT** misuse a scene to **toggle** — a scene sets an **absolute** target state and has no counterpart (there is no `scene.turn_off`); for "on↔off depending on current state" use `homeassistant.toggle`/`light.toggle` or a `choose` branch in an automation/script
- **SHOULD NOT** use a scene for **dynamic or computed** values (e.g. "brightness = outdoor brightness × factor") — the `entities` states are static and fixed at definition time; derived target values belong in a **template**/script (`ha-automation/template`, `ha-automation/script`) that computes the value at runtime
- **SHOULD NOT** repurpose a scene as a **group** to bundle several entities under one name — a scene *sets* states, it does not *aggregate* a combined state and provides no shared control entity; for bundling use a **group** (`ha-automation/group`)
- **SHOULD NOT** rely on a snapshot scene created via `scene.create` surviving a restart or `scene.reload` — for persistent scenes use the YAML/UI definition; `scene.create` is only for short-lived save/restore within a single run
- **SHOULD NOT** expect `transition` on `scene.turn_on` for non-light entities — per the docs only lights (and only capable ones) support the smooth transition; for other domains the state is set hard

## Acceptance Criteria

- [ ] Every static scene is defined under `scene:` as a list entry with `name` and `entities`
- [ ] Entity states use either the direct form or the nested `state:`+attribute form; attributes never sit on a scalar value
- [ ] Activation is done exclusively via `scene.turn_on` (no `scene.turn_off` assumed)
- [ ] `transition` is set only for light entities
- [ ] `scene.create` uses `scene_id` plus at least `entities` or `snapshot_entities`; non-persistence is accounted for
- [ ] The snapshot/restore pattern does not rely on a reload-surviving snapshot
- [ ] The scene state is read as the timestamp of the last activation (not on/off)
- [ ] The "when NOT to use" delimitation holds: no scene for sequences (→ script), toggling, dynamic values, or as a group
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

No open questions.
