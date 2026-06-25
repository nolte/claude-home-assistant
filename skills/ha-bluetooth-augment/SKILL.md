---
name: ha-bluetooth-augment
description: Augment an existing Home Assistant Custom Integration with Bluetooth support, conforming to spec/ha/bluetooth. Sets the manifest.json bluetooth matcher list (connectable, service_uuid, service_data_uuid, manufacturer_id, local_name) plus bluetooth_adapters in dependencies on adapter use, subscribes to advertisements via bluetooth.async_register_callback with a BluetoothCallbackMatcher and an explicit BluetoothScanningMode (@callback bound through entry.async_on_unload), picks the right Bluetooth coordinator family (PassiveBluetoothProcessorCoordinator / ActiveBluetoothProcessorCoordinator or the DataUpdate variants), and wires async_ble_device_from_address / async_last_service_info lookups over the shared scanner. Keeps passive (connectable=False) as the default. Part of the Gold discovery family, sibling of ha-discovery-augment. Activate on "add bluetooth discovery/support", "listen for BLE advertisements", "füge Bluetooth-Unterstützung hinzu". Do not activate for DHCP/SSDP/USB/HomeKit/Zeroconf network discovery (ha-discovery-augment), the config-flow discovery step (ha-config-flow-augment), the generic polling DataUpdateCoordinator (ha/coordinator-patterns), greenfield scaffolding (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, bluetooth]
---

# HA Bluetooth Augment

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-bluetooth-augment/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-bluetooth-augment/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes how the device advertises and reads back the manifest matcher, the callback registration, the coordinator family, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-discovery-augment`, `ha-config-flow-augment`, `ha-coordinator-add`).
- **Mid-flow interactivity** — the passive-vs-connectable decision, the coordinator-family choice, and the network-discovery redirect are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — the manifest matcher plus the callback registration and the coordinator wiring fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the connectable decision and the trade-off advice belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add Bluetooth support — central BLE discovery plus advertisement-driven data fetching — to an existing integration, typically for a device that delivers its data over BLE advertisements (the passive default) or needs an occasional active connection.

## When NOT to activate

- DHCP/SSDP/USB/HomeKit/Zeroconf network or bus discovery → `ha-discovery-augment` / `ha/discovery-mechanisms`
- the config-flow Bluetooth discovery step / generic config-flow auth steps → `ha-config-flow-augment` / `ha/config-flow-patterns`
- the generic polling-based `DataUpdateCoordinator` for REST/cloud APIs → `ha/coordinator-patterns`
- greenfield integration scaffolding → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **Read [`ha/bluetooth`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/bluetooth/de.md) first.** Do not generate HA internals from memory.
2. **Right mechanism, with delimitation.** DHCP/SSDP/USB/HomeKit/Zeroconf → `ha-discovery-augment`; the full config-flow discovery step → `ha-config-flow-augment`. Redirect rather than augmenting the wrong one.
3. **Manifest matcher + dependency.** The `bluetooth` key is a list of matcher dicts from the documented fields (`service_uuid`, `local_name`, `manufacturer_id`, `service_data_uuid`, `connectable`); add `bluetooth_adapters` to `dependencies` when the integration uses an adapter.
4. **Passive is the default.** Operate `connectable=False` whenever the device delivers data through advertisements only — that opts in to non-connectable controllers. Use `connectable=True` (the field default) only where an outgoing connection is actually needed; set the flag per device for mixed devices.
5. **Advertisement callbacks.** Subscribe via `bluetooth.async_register_callback(hass, callback, matcher, mode)` with a `BluetoothCallbackMatcher` and an explicit `bluetooth.BluetoothScanningMode` (`ACTIVE`/`PASSIVE`). The callback is `@callback`, synchronous, signature `(service_info: BluetoothServiceInfoBleak, change: BluetoothChange) -> None`. Bind the returned cancel callback via `entry.async_on_unload(...)`.
6. **Lookups, never an own scanner.** Get a `BLEDevice` via `bluetooth.async_ble_device_from_address(hass, address, connectable)` and handle the `None` case (no adapter in range); read latest info via `bluetooth.async_last_service_info`; check `bluetooth.async_scanner_count(hass, connectable=True)` at setup when connecting. **Never** instantiate an own `BleakScanner`.
7. **Right coordinator family.** `PassiveBluetoothProcessorCoordinator` for sensors/binary sensors/events from advertisements; `ActiveBluetoothProcessorCoordinator` on connection need; the DataUpdate variants for non-sensor entities; the generic `DataUpdateCoordinator` only on pure connection communication with no advertisements. Processor coordinators format `PassiveBluetoothDataUpdate` (indexed by `PassiveBluetoothEntityKey`) and bind `coordinator.async_start()` to `entry.async_on_unload(...)` only **after** `async_forward_entry_setups`. Active variants check `CoreState.running` and a reachable connectable `BLEDevice` in `needs_poll_method`.
8. **Connection handling.** For active connections use `bluetooth.async_get_scanner(hass)`, a fresh `BleakClient` per connection, a timeout ≥ 10 s, and `bleak-retry-connector`; never hold a permanent connection when the data is in advertisements.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `device_behaviour` | yes | — | how the device advertises, and whether data is advertisement-only or needs an active connection |
| matcher fields | no | asked when needed | `service_uuid` / `service_data_uuid` / `manufacturer_id` / `local_name` / `connectable` |
| `mode` | no | derived (`PASSIVE` default) | `BluetoothScanningMode` `PASSIVE` / `ACTIVE` |
| coordinator family | no | inferred + confirmed | passive/active processor vs. DataUpdate variant |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Delimit the mechanism: on a DHCP/SSDP/USB/HomeKit/Zeroconf situation redirect to `ha-discovery-augment` and stop; point a full config-flow discovery step at `ha-config-flow-augment`.
3. Read `ha/bluetooth`.
4. No `bluetooth` matcher / callback / coordinator registration is already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the matcher fields, the resolved `connectable` (default `False` for advertisement-only) and `BluetoothScanningMode`, the chosen coordinator family, and every assumed default in one paragraph. Wait for confirmation.

### 2) Generate

| Concern | Artifact | Key contract |
|---|---|---|
| discovery | `manifest.json` `bluetooth` list (+ `bluetooth_adapters` in `dependencies` on adapter use) | matcher dicts from the documented fields; `connectable` per device |
| advertisements | `async_register_callback` + `@callback` | `BluetoothCallbackMatcher`, explicit `BluetoothScanningMode`, bound via `entry.async_on_unload` |
| coordinator | passive/active processor or DataUpdate variant | `PassiveBluetoothDataUpdate`; `async_start()` after `async_forward_entry_setups` |
| connection (active only) | `async_get_scanner` + `bleak-retry-connector` | fresh `BleakClient`, timeout ≥ 10 s |

Use lookups (`async_ble_device_from_address` with `None` handling, `async_last_service_info`, `async_scanner_count`) instead of starting an own scanner.

### 3) Validate and report

Validate offline (manifest matcher, plus `bluetooth_adapters` in `dependencies` on adapter use; `async_register_callback` with `@callback` signature, bound via `entry.async_on_unload`; `async_ble_device_from_address` with `None` handling; passive default; use-case-correct coordinator family formatting `PassiveBluetoothDataUpdate` and starting after `async_forward_entry_setups`; connections via `async_get_scanner`, fresh `BleakClient`, timeout ≥ 10 s, `bleak-retry-connector`). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/bluetooth` acceptance criteria, plus the changed file paths and the quality-scale marker (**Gold**: `discovery`).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- DHCP/SSDP/USB/HomeKit/Zeroconf network discovery → `ha-discovery-augment`
- Config-flow Bluetooth discovery step / generic config-flow steps → `ha-config-flow-augment`
- Generic polling `DataUpdateCoordinator` → `ha/coordinator-patterns`
- Greenfield scaffold → `ha-integration-scaffold`
- Deploy to live HA → out of scope
