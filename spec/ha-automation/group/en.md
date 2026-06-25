# HA Automation: Using Group

Status: draft

## Context

The `group` integration combines several entities into a single group entity whose state is computed from its members. It serves two purposes: controlling several entities together (e.g. "all lights off") and deriving an aggregated state (e.g. "is any window open?"). Per the official docs, the integration is used by roughly 31% of active HA installations.

Its real classification is **Helper / Organization** — it is an internal, fully configurable helper integration, **not** an automation. This spec turns the official usage docs into a convention for which kind of group the plugin generates and how its combined state is computed in a binding way, so that downstream triggers and templates can rely on a predictable state.

The integration has two generations: the **old `group:` YAML** (generic entity groups under the top-level `group:` key in `configuration.yaml`) and the **modern per-domain groups** (light, switch, cover, fan, lock, media_player, binary_sensor, sensor, button, event, notify — created via the UI helper or as per-domain YAML). Both are covered here; for new artifacts the modern form is mandatory.

Verified source: [`/integrations/group/`](https://www.home-assistant.io/integrations/group/).

## When to Use

Use `group` whenever several entities of the same domain should be combined into **one entity with a combined state** — either for joint control or as an aggregated trigger/condition basis. Typical use cases:

- **Joint control** — switch several lights, switches, or covers through the group `entity_id` in a single call (`homeassistant.turn_on`/`turn_off` fans out to the members), e.g. "all lights off"
- **"Is any member on?"** — query via the OR default whether at least one window is open / one light is on, and use the group state as a trigger/condition
- **"Do all members satisfy?"** — enforce AND semantics via `all: true` (for `binary_sensor`/`light`/`switch`), e.g. "are all doors locked?", including `unknown`/`unavailable` propagation
- **Numeric aggregation** — form a sensor group with a `type` (`min`, `max`, `mean`, `median`, `sum`, `range`, …) over homogeneous sensors, with deliberate `ignore_non_numeric` behavior
- **Domain aggregation as a trigger** — use the domain-specific state computation (cover `open`, lock priority order, fan `on`) as a predictable basis for downstream automations

A group is the right tool as soon as a **consumed combined state** or **joint control** is needed. For pure room/category assignment, areas/labels are intended; for freely computed values, a template sensor (see `### Delimitation: When NOT to Use`).

## Goals

- Bind the choice between old `group:` YAML and a modern per-domain group to the modern form
- Fix the documented state computation (OR by default; AND via `all: true`) as a checkable convention so triggers interpret the group state correctly
- Set the `all` switch deliberately and with justification instead of blindly adopting the OR default
- Make the sensor-group `type` (aggregation function) and the `unknown` behavior for non-numeric members (`ignore_non_numeric`) binding
- Clearly delimit when a group is **not** the right tool (area/label, min_max/statistics, template sensor)

## Non-Goals

- The full trigger/condition/action syntax that consumes a group — `ha-automation/automation`
- Numeric aggregation beyond the few `type` functions (moving averages, derivative, long-term statistics) — `ha-automation/statistics`, `ha-automation/derivative`, `ha-automation/min-max`
- Declaratively computed, freely formulated states/attributes — `ha-automation/template`
- The naming dimension (`name`, `unique_id`, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here
- Areas and labels as the registry's pure organization/assignment mechanic — they have no spec card of their own and are named here only for delimitation

## Requirements

### Configuration

- **MUST** use a **modern per-domain group** (light, switch, cover, fan, lock, media_player, binary_sensor, sensor, button, event, notify) for new artifacts and not use the old generic `group:` YAML for new entries
- **MUST** declare `entities` as the list of members in every group; `name` is optional, `unique_id` is optional but enables UI customization — both following the mechanics in `ha/naming-conventions`
- **MUST** pick the members of a per-domain group from the **same domain** (a light group contains lights, a sensor group contains sensors), because the state/attribute aggregation is domain-specific
- **SHOULD** set the `all` switch (available for `binary_sensor`, `light`, and `switch` groups) deliberately: the default is `false` (OR — `on` when at least one member is `on`); `all: true` enforces AND semantics
- **MUST** pick the `type` for a **sensor group** from the documented catalog: `min`, `max`, `last`, `first_available`, `mean`, `median`, `range`, `product`, `stdev`, or `sum`
- **SHOULD** set `ignore_non_numeric` deliberately on sensor groups: the default `false` makes the group state `unknown` as soon as a member has no numeric state; `true` computes only from the available numeric members
- **MAY** set `unit_of_measurement` and `state_class` on sensor groups and a `device_class` on `binary_sensor` groups
- **SHOULD** keep the old `group:` YAML only where existing configuration already uses it, and then use `entities`, optional `name`, `icon`, and `all` correctly — `all: true` here means the group is `on` only when **all** members are `on`

### Use in Automations & Templates

- **MUST** understand the documented combined state of the modern group as the basis for triggers/conditions: without `all`, the group is `on` when **at least one** member is `on`; with `all: true` it is `unknown` as soon as a member is `unknown`/`unavailable`, `off` as soon as a member is `off`, otherwise `on`
- **MUST** account for the domain-specific aggregation when the group state serves as a trigger — e.g. cover/valve: `open` when a member is `opening`/`open`; fan: `on` when a member is `on`; lock with the priority order `jammed > opening > locking > open > unlocking > locked`
- **MUST** factor the `unknown`/`unavailable` propagation rule of `all: true` groups into trigger/condition design instead of checking only for `on`/`off`
- **SHOULD** resolve the group's `entity_id` attribute (the list of all `entity_id`s in the group) in templates via `expand()` when iterating over members, instead of duplicating the member list
- **MAY** control a group together by applying `homeassistant.turn_on`/`homeassistant.turn_off` to the group `entity_id`; the action fans out to the members
- **SHOULD NOT** use the old-style services `group.set`/`group.remove`/`group.reload` for modern per-domain groups — per the docs `group.set` and `group.remove` operate on **old-style groups**; modern groups are managed via the UI helper or per-domain YAML

### Delimitation: When NOT to Use

- **SHOULD NOT** create a group as a pure organization/assignment device when the only intent is to assign entities to a room or a category — **areas** and **labels** of the registry are made for that; a group is justified only by a **consumed combined state** or **joint control**
- **SHOULD NOT** use the old generic `group:` YAML for new entries — the **modern per-domain groups** deliver correct domain-specific aggregation (cover/lock/media_player), the `all` switch, and clean `unavailable` behavior that the generic group does not provide
- **SHOULD NOT** use a sensor group for numeric aggregation that goes beyond the fixed `type` functions (e.g. weighted averages, a moving window over time, a derivative) — **min_max**, **statistics**, or **derivative** (`ha-automation/min-max`, `ha-automation/statistics`, `ha-automation/derivative`) are made for that; the sensor group offers only the few documented aggregates. For an in-catalog numeric aggregate that does **not** also need to be a group entity, `ha-automation/min-max` is the focused tool
- **MUST NOT** misuse a sensor group as a substitute for a template sensor when the value must be freely computed from several sources or formed with conditional logic — a sensor group can apply only **one** of the fixed aggregation functions over homogeneous members; free formulas belong in a **template sensor** (`ha-automation/template`)
- **SHOULD NOT** mix members of foreign domains in a per-domain group (light + switch + sensor in one group) to capture "everything" — the aggregation is domain-specific and the result is then undefined; create one group per domain or combine via a template
- **SHOULD NOT** rely on the OR default where the intent is "all members satisfy the condition" — without `all: true` the group reports `on` as soon as a single member is `on`, which silently falsifies an "all off" check

## Acceptance Criteria

- [ ] New groups are modern per-domain groups; the old `group:` YAML is not used for new entries
- [ ] Every group declares `entities`; `name`/`unique_id` follow `ha/naming-conventions`
- [ ] Members come from the same domain as the group
- [ ] The `all` switch is set deliberately (OR default vs. AND via `all: true`), matching the trigger intent
- [ ] Sensor groups carry a documented `type`; `ignore_non_numeric` is set deliberately
- [ ] Triggers/conditions account for the documented state computation incl. `unknown`/`unavailable` propagation under `all: true`
- [ ] Members are iterated via `expand()` over the `entity_id` attribute instead of a duplicated list
- [ ] The "when NOT to use" delimitation holds: no group where area/label, min_max/statistics/derivative, or a template sensor is the right tool
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Sensor group vs. statistics sensor for `range`**: The sensor group offers `range` (the span across the current members), while `statistics` provides time-based spans. The dividing line "concurrent members vs. time window" is named here but not anchored in a dedicated rule — should this spec carry an explicit `range` delimitation rule, or is the pointer to `ha-automation/statistics` sufficient?
