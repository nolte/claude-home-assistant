# Skill: `ha-device-registry-augment`

Status: draft

## Context

`ha/device-registry` and `ha/entity-architecture` describe how entities group into physical **devices** via `DeviceInfo` (identifiers, manufacturer, model, name), how a child device links to its hub via `via_device`, how newly discovered devices are added at runtime, and how devices that disappear are removed. These are the Gold quality-scale rules `devices`, `stale-devices`, and `dynamic-devices`. But no skill wires them: the scaffold and `ha-entity-platform-add` produce entities, `ha-entity-description-map` maps datapoints, and both delegate the device hierarchy to `ha/entity-architecture` without a skill that owns it. The common failures are flat entities with no device, a missing `via_device` so a hub and its children are unrelated, and stale devices that linger because `async_remove_config_entry_device` was never implemented.

This skill closes that gap: it wires the device-registry hierarchy of an existing integration — `DeviceInfo`, `via_device`, dynamic add, stale removal, and optional device diagnostics — non-destructively to the existing entities. It is the device-hierarchy sibling of `ha-entity-platform-add` (which owns the entity), lifting an integration toward the Gold device rules.

## Scope

Wiring the device-registry hierarchy of exactly one existing `custom_components/<domain>/` integration: the `DeviceInfo` on the entities (identifiers / manufacturer / model / name, `via_device` for a hierarchy), the runtime addition of newly discovered devices, the `async_remove_config_entry_device` stale-removal hook, and optionally `async_get_device_diagnostics`, plus a device-registry test. The skill reads the coordinator/entity shape, decides the topology, and validates offline; it does not rewrite entity logic.

## Goals

- Own the device-registry hierarchy (`DeviceInfo`, `via_device`, dynamic add, stale removal) that `ha/entity-architecture` describes but no skill wires
- Group entities into proper devices with full `DeviceInfo` (identifiers/manufacturer/model/name), non-destructively to existing `unique_id`s
- Link a hub and its children via `via_device`, registering the hub first and never pointing outside the integration
- Add newly discovered devices at runtime (Gold `dynamic-devices`) and remove stale ones via `async_remove_config_entry_device` (Gold `stale-devices`), never auto-deleting a merely-unavailable device
- Optionally add redacted device diagnostics; land a device-registry test

## Non-Goals

- Creating the entity platform itself — `ha-entity-platform-add` / `ha-entity-description-map`
- The config-entry diagnostics JSON dump — `ha-diagnostics-augment`
- Device trigger / condition / action automation platforms — `ha-device-automation-add`
- Greenfield scaffold — `ha-integration-scaffold`
- Deploying/importing into a running HA instance — generation only

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "group these entities into a device", "add a hub device with child devices via_device", "remove stale devices when they disappear"
  - "gruppiere die Entitäten zu einem Gerät", "füge ein Hub-Gerät mit Kindgeräten hinzu"
- **MUST NOT** activate for entity-platform creation (`ha-entity-platform-add`), config-entry diagnostics (`ha-diagnostics-augment`), or device automations (`ha-device-automation-add`)

### Inputs

- **MUST** capture: `target_dir` (repo root), `topology` (`single` / `hub-and-children` / `per-device`), and `identifier_source` (the stable per-device id)
- **MAY** capture: `stale_removal` (else inferred and confirmed) and `device_diagnostics` (default `false`)

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` is a git repo with a clean working tree and that `custom_components/<domain>/` carries at least one entity platform; read `domain` and the coordinator/entity shape
- **MUST** resolve the `topology`, the `identifier_source`, and whether `stale_removal` applies

### Generation rules

- **MUST** set `_attr_device_info = DeviceInfo(...)` with `identifiers={(DOMAIN, <stable_device_id>)}`, `manufacturer`, `model`, `name` (and `sw_version`/`hw_version` when known); entities attach via their own `device_info`, never by manually creating an unreferenced device; existing `unique_id`s stay unchanged
- **MUST** set `via_device=(DOMAIN, <hub_device_id>)` for a child in a hub hierarchy, register the hub first, and never point `via_device` outside this integration
- **MUST** add newly discovered devices from the coordinator update at runtime when the backend can gain devices (Gold `dynamic-devices`)
- **MUST** implement `async_remove_config_entry_device(hass, config_entry, device_entry) -> bool` returning `True` only when the device is genuinely gone from the integration's data (Gold `stale-devices`); a temporarily-unavailable device is not removed
- **MUST** route any `async_get_device_diagnostics` data through `async_redact_data` per `ha/diagnostics` / `ha/security-hardening` when `device_diagnostics`
- **MUST** follow `ha/device-registry` + `ha/entity-architecture`, name identifiers per `ha/naming-conventions`, and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: `DeviceInfo` carries identifiers/manufacturer/model/name; `via_device` points inside the integration; `async_remove_config_entry_device` is present when `stale_removal`; device diagnostics are redacted when present; a device-registry test exists
- **MUST** deliver a CONFORMANT / NEEDS-WORK report keyed to these acceptance criteria plus the changed file paths and the quality-scale marker (**Gold** — `devices`, `stale-devices`, `dynamic-devices`)

### Prohibitions

- **MUST NOT** rewrite entity logic or change existing `unique_id`s
- **MUST NOT** point `via_device` at a device outside this integration, or auto-delete a merely-unavailable device
- **MUST NOT** deploy to or import into a running HA instance

## Acceptance criteria

- [ ] Entities carry `DeviceInfo` with identifiers, manufacturer, model, and name; existing `unique_id`s are unchanged
- [ ] A hub hierarchy links children via `via_device`, with the hub registered first and inside the integration
- [ ] Newly discovered devices are added at runtime when the backend can gain devices
- [ ] `async_remove_config_entry_device` removes only genuinely-gone devices (Gold `stale-devices`)
- [ ] Device diagnostics, when added, are redacted
- [ ] A device-registry test and the changed file paths are reported; quality-scale marker **Gold**

## Open questions

- **Device-only vs. entity-attached**: a hub with no own entity needs a `device_registry.async_get_or_create`. When is a device registered device-only vs. always through an entity's `device_info`?
- **Stale-removal signal**: `async_remove_config_entry_device` decides removability from current data. Is a stronger "seen at" timestamp needed, or is presence-in-data enough?
- **Migration overlap**: grouping previously-flat entities into devices can strand old registry entries. Does this skill hand off to `ha-config-entry-migrate` when a device restructuring needs a version bump?
