---
name: ha-device-registry-augment
description: Wires the device-registry hierarchy of an existing Home Assistant Custom Integration so entities group into proper devices — DeviceInfo with identifiers / manufacturer / model / name, a via_device hub-to-child parent link, runtime addition of newly discovered devices, and removal of stale devices via async_remove_config_entry_device. Optionally adds async_get_device_diagnostics. Targets the Gold devices, stale-devices, dynamic-devices rules. Non-destructive to existing entities. Activate on phrasings like "group these entities into a device", "add a hub device with child devices via_device", "remove stale devices when they disappear", "gruppiere die Entitäten zu einem Gerät", "füge ein Hub-Gerät mit Kindgeräten hinzu". Do not activate for creating entity platforms (ha-entity-platform-add), config-entry diagnostics (ha-diagnostics-augment), device trigger/condition/action automations (ha-device-automation-add), greenfield scaffolding (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, device-registry]
phase: design
summary: "Wires the device-registry hierarchy — DeviceInfo, via_device hub-to-child links, runtime device add, and stale-device removal — so entities group into proper devices."
summary_de: "Verdrahtet die Device-Registry-Hierarchie — DeviceInfo, via_device-Hub-zu-Kind-Links, Laufzeit-Geräte und Entfernen veralteter Geräte — sodass Entities zu echten Geräten gruppieren."
use_when:
  - "you want to group entities into a device"
  - "you want a hub device with via_device child devices"
  - "you want stale devices removed when they disappear"
dont_use_when:
  - situation: "You are creating the entity platform itself"
    alternative: ha-entity-platform-add
  - situation: "You want config-entry diagnostics, not device wiring"
    alternative: ha-diagnostics-augment
  - situation: "You want device trigger/condition/action automations"
    alternative: ha-device-automation-add
  - situation: "You are scaffolding a brand-new integration from scratch"
    alternative: ha-integration-scaffold
see_also:
  - ha-entity-platform-add
  - ha-entity-description-mapper
  - ha-diagnostics-augment
  - ha-device-automation-add
  - ha-coordinator-add
---

# HA Device Registry Augment

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-device-registry-augment/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-device-registry-augment/en.md).

This skill owns the **device-registry hierarchy** — `DeviceInfo`, `via_device`, dynamic device add, and stale device removal — that `ha/entity-architecture` describes but no skill wires. It lifts an integration from flat entities toward the Gold `devices` / `stale-devices` / `dynamic-devices` rules.

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the device topology and reads back the `DeviceInfo` wiring, the `via_device` link, and the removal path; a skill keeps this on the visible command surface, like the sibling augment skills.
- **Mid-flow interactivity** — the device topology (one device, a hub with children, per-datapoint devices), the identifier source, and whether stale-device removal applies are per-run dialogues the user confirms.
- **Bounded, inline generation** — the `DeviceInfo` construction plus the removal hook fits inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the topology decision and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill when an existing integration's entities should group into one or more **devices** — a single device, a hub with `via_device` children, or per-physical-device grouping — and when devices that disappear from the backend must be removed from the registry.

## When NOT to activate

- creating the entity platform itself → `ha-entity-platform-add` / `ha-entity-description-mapper`
- config-entry diagnostics (the JSON dump) → `ha-diagnostics-augment`
- device trigger / condition / action automation platforms → `ha-device-automation-add`
- greenfield integration setup → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope (generation only)

## Hard rules

1. **Non-destructive.** Do not rewrite entity logic; add or complete the `DeviceInfo` / registry wiring only. Existing `unique_id`s stay unchanged so entities keep their registry entries.
2. **`DeviceInfo` carries the identity.** Every device sets `identifiers={(DOMAIN, <stable_device_id>)}` plus `manufacturer`, `model`, `name`, and `sw_version`/`hw_version` when known. Entities attach via the entity's `_attr_device_info` (or `device_info` property) — never by manually creating a device the entity does not reference.
3. **`via_device` for a hierarchy.** A child device attached to a hub sets `via_device=(DOMAIN, <hub_device_id>)`; the hub device is registered first (via a hub entity or `device_registry.async_get_or_create`). Never invent a `via_device` link to a device outside this integration.
4. **Dynamic devices.** When the backend can gain devices at runtime, add them from the coordinator update (create the new entities/devices on discovery) rather than only at setup — the Gold `dynamic-devices` rule.
5. **Stale device removal.** Implement `async_remove_config_entry_device(hass, config_entry, device_entry) -> bool` returning `True` when the device is no longer present in the integration's data, so HA lets the user delete it (the Gold `stale-devices` rule). Do not auto-delete a device that is merely temporarily unavailable.
6. **Device diagnostics are optional.** Add `async_get_device_diagnostics(hass, entry, device)` only on request; route its data through `async_redact_data` per `ha/diagnostics` / `ha/security-hardening`.
7. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)**, follow [`ha/device-registry`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/device-registry/de.md) and [`ha/entity-architecture`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/entity-architecture/de.md), and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root of the existing integration |
| `topology` | yes | — | `single` / `hub-and-children` / `per-device` |
| `identifier_source` | yes | — | the stable per-device id from the backend (serial, id, MAC, …) |
| `stale_removal` | no | inferred + confirmed | whether devices can disappear and must be removable |
| `device_diagnostics` | no | `false` | add `async_get_device_diagnostics` |

## Pre-flight (in order — abort on first failure)

1. `git -C <target_dir> rev-parse --is-inside-work-tree` and a clean working tree.
2. `custom_components/<domain>/` carries at least one entity platform; read `domain` and the coordinator/entity shape.
3. Resolve the `topology`, the `identifier_source`, and whether `stale_removal` applies.

## Workflow

### 1) Resolve and confirm

State `domain`, the `topology`, the identifier source, whether stale removal and device diagnostics apply, in one paragraph. Wait for confirmation.

### 2) Apply

- `entity.py` (or the base entity) — set `_attr_device_info = DeviceInfo(identifiers=…, manufacturer=…, model=…, name=…, via_device=…)`
- `__init__.py` — `async_remove_config_entry_device` when `stale_removal`; hub `device_registry.async_get_or_create` when a hub has no own entity
- the coordinator / setup — dynamic-device add on discovery when the backend can gain devices
- `diagnostics.py` — `async_get_device_diagnostics` (redacted) when `device_diagnostics`
- `tests/` — a device-registry test asserting the device(s), the `via_device` link, and (when applicable) the stale-removal predicate

### 3) Validate & report

Validate offline (`DeviceInfo` identifiers/manufacturer/model/name present; `via_device` points inside the integration; `async_remove_config_entry_device` present when `stale_removal`; device diagnostics redacted when present) and emit a CONFORMANT / NEEDS-WORK report keyed to the acceptance criteria plus the changed file paths and the quality-scale marker (**Gold** — `devices`, `stale-devices`, `dynamic-devices`).

## Boundaries

- Entity platform creation → `ha-entity-platform-add` / `ha-entity-description-mapper`
- Config-entry diagnostics dump → `ha-diagnostics-augment`
- Device trigger/condition/action automations → `ha-device-automation-add`
