# HA Integration: Device Registry and `DeviceInfo` Hierarchy

Status: draft

## Context

Home Assistant maintains two separate registries: the **entity registry** (see `ha/entity-architecture` for entity identification) and the **device registry**. A Custom Integration registers its devices through `homeassistant.helpers.device_registry.DeviceInfo` instances that every entity carries via `_attr_device_info` at setup. HA folds the `DeviceInfo` instances into one device entry per `(integration, identifiers)` pair — different `identifiers` produce different devices; the same `identifiers` with diverging `DeviceInfo` are merged.

A real integration rarely consists of a flat single device — the typical shape is a **hub hierarchy**: one central "hub" device represents the server / bridge / API endpoint, and all subordinate resources (managed devices, locations, tanks, rooms, …) are sub-devices that point to the hub via `via_device=(DOMAIN, hub_identifier)`. HA then renders the hierarchy in the UI as a tree, which dramatically improves overview in larger setups.

`nolte/kamerplanter-ha` validates this hub pattern with a central `server_device_info(entry)` factory function plus three sub-device factories (`plant_device_info`, `location_device_info`, `tank_device_info`) that all set `via_device=(DOMAIN, entry.entry_id)`. Every sub-`identifiers` prefixes `entry.entry_id`, so two entries (multi-instance) coexist without collisions. This spec lifts the pattern into a generic obligation.

Quality scale marker: **Silver** (device hierarchy via `via_device` and multi-instance-safe `identifiers` is a Silver requirement per the HA quality scale).

## Goals

- Establish the hub-and-sub-device hierarchy as the standard shape for Custom Integrations that create more than one device
- Centralise `DeviceInfo` factory functions in `entity.py`, so platform modules reference them rather than duplicating them
- Mandate `identifiers` construction with an `entry.entry_id` prefix — multi-instance setups (two entries against different servers) stay collision-free
- Require `via_device` setting on every sub-device, so HA renders the hierarchy correctly in the UI
- Guarantee stable, language- and installation-independent `identifiers` over the lifetime of a resource

## Non-Goals

- Entity identification (`unique_id`, `translation_key`, `_attr_has_entity_name`) — separate `ha/entity-architecture` spec
- HA area-registry management (area assignment) — areas are set by the user in the UI; skills do not assign them programmatically
- Device-discovery mechanics (zeroconf detection, DHCP match) — separate follow-up specs
- `connections` field (`connections={(CONNECTION_NETWORK_MAC, "...")}`) for MAC-/IP-based identification — only relevant for discovery-driven integrations; a separate follow-up spec covers it once the first discovery spec lands

## Requirements

### `DeviceInfo` factory functions

- **MUST** define every `DeviceInfo` construction in `entity.py` as a free factory function, one per resource type — typical function names: `<role>_device_info(entry, <resource>) -> DeviceInfo`
- **MUST** keep factory functions pure — no coordinator reads, no I/O, no mutations; they take `entry` plus an optional resource dict and return a `DeviceInfo`
- **MUST NOT** inline `DeviceInfo` construction in platform modules (`sensor.py`, `binary_sensor.py`, …) — fields would drift between platforms and HA stops merging
- **SHOULD** set `manufacturer`, `model`, and `name` in every factory function — `name` is shown in the HA UI; `manufacturer` / `model` land in the device-detail view
- **MAY** set `model_id`, `sw_version`, `hw_version`, `configuration_url` when available; `configuration_url` is particularly useful because HA renders it as a direct link to the backend's web UI

### Hub device

- **MUST** define a hub `DeviceInfo` with a unique `identifiers` and **without** `via_device` when the integration has `integration_type: "hub"` (see `ha/integration-architecture`)
- **MUST** set the hub `identifiers` as `{(DOMAIN, entry.entry_id)}` — the `entry.entry_id` prefix guarantees multi-instance collision freedom
- **SHOULD** derive the hub `name` from the entry title or a backend server identifier, so two hubs of the same integration stay distinguishable in the UI
- **MUST** keep at least one entity attached to the hub device — otherwise HA does not render the hub device; a status sensor entity or a refresh button is typical (see `ha/entity-architecture`)

### Sub-devices

- **MUST** define a `<role>_device_info(entry, resource)` factory function per resource type (managed device, location, tank, room, …)
- **MUST** set the sub `identifiers` as `{(DOMAIN, f"{entry.entry_id}_<role>_<resource_slug>")}` — the `entry.entry_id` prefix is mandatory; the `<role>` marker keeps the identifier human-readable in the device registry; the `<resource_slug>` is stable across the resource's lifetime
- **MUST** bind the sub-device to the hub via `via_device=(DOMAIN, entry.entry_id)` (the tuple matches the hub's `identifiers` representation)
- **SHOULD** derive the resource slug deterministically from a stable backend key (resource ID, resource key, backend UUID) — never from a user-mutable display name; otherwise the slug shifts on rename
- **MUST NOT** create two sub-devices with identical `identifiers` tuples — HA merges them into a single device that carries both entity sets; that is only desired when the two sub-devices are logically the same device

### Sub-sub hierarchies

- **MAY** carry multi-level hierarchies (for example `tank_device_info` with `via_device` to a `location_device_info` that itself points to the hub) — HA supports arbitrarily deep nesting via `via_device`
- **SHOULD** keep the hierarchy depth minimal; every additional level complicates the mental model for end users without yielding a technical benefit on the HA side
- **MUST** document — in follow-up skill-output documentation — why the depth is justified for multi-level hierarchies

### `identifiers` stability

- **MUST** keep `identifiers` stable over a resource's lifetime — changing the identifier string produces a **new** device from the device registry's perspective; the entities on the old device are orphaned
- **MUST NOT** include display names, user-mutable slugs, or random UUIDs in the `identifiers` string
- **SHOULD** use backend IDs / keys that the backend itself guarantees stable (database primary key, backend UUID, hardware MAC, …)

### Multi-instance behaviour

- **MUST** ensure that two config entries of the same integration (against different backends) produce collision-free `identifiers` — automatically achieved by the `entry.entry_id` prefix
- **MUST NOT** use the backend identifier without the entry prefix — two servers with the same backend-internal resource ID would otherwise merge into the same device entry, scrambling entities of both entries

### Lifecycle

- **MUST** make sub-device factory calls in `async_setup_entry` (or in the platform `async_setup_entry`), based on fresh coordinator data — not from cached or hard-coded lists
- **MUST NOT** call `async_remove_device(...)` directly to remove sub-devices manually — HA cleans up orphaned devices when the last entity on the device is removed; an explicit remove call is needed only in rare special cases

## Acceptance Criteria

- [ ] Every `DeviceInfo` construction lives as a free factory function in `entity.py`
- [ ] When `manifest.json:integration_type` is `hub`: a hub device with `identifiers={(DOMAIN, entry.entry_id)}` and without `via_device` is defined
- [ ] At least one entity is anchored on the hub device
- [ ] Every sub-device has `identifiers` with an `entry.entry_id` prefix and `via_device=(DOMAIN, entry.entry_id)`
- [ ] Platform modules set `_attr_device_info` via factory functions from `entity.py`, not inline
- [ ] A `grep` for `DeviceInfo(` in the platform modules returns no hits
- [ ] Sub-device slugs derive from stable backend keys, not display names or UUIDs
- [ ] Quality scale marker: **Silver**

## Open Questions

- **`connections` field**: Should the spec require MAC- / IP-connections for discovery-capable integrations once the first discovery spec lands?
- **Multi-level hierarchies**: Heuristic for sensible depth? Currently formulated as "keep minimal"; a measurable threshold (for example "no deeper than 2") is missing.
- **`async_remove_device` use case**: Are there legitimate cases where the integration should explicitly remove a device (for example a resource deleted in the backend)? Currently forbidden / SHOULD-NOT; experience with kamerplanter-ha shows HA solves this automatically once the last entity disappears — does that always hold?
- **Hub-device requirement for `integration_type: "device"`**: With `integration_type: "device"` there is conventionally no hub. Should sub-device factories be forbidden for such integrations, or are mixed forms allowed?
