# Skill: `ha-bluetooth-augment`

Status: draft

## Context

`ha/bluetooth` defines how a Custom Integration enters Home Assistant's shared `bluetooth` infrastructure: through `manifest.json` matchers into central BLE discovery, through the callback APIs (`bluetooth.async_register_callback`) for advertisement-driven reception, through the `bluetooth` lookup APIs (`async_ble_device_from_address`, `async_last_service_info`, `async_address_present`, `async_scanner_count`), and through the specialized Bluetooth coordinator families — instead of running its own `BleakScanner`. The core difference from the polling world is the consistent `connectable` distinction: many devices deliver their data exclusively through advertisements; an active connection is the exception. No skill augments this so far. Bluetooth is part of the Gold discovery family (quality-scale marker: `discovery`), sibling of `ha-discovery-augment`.

This skill augments **an existing** integration with Bluetooth support — conformant to `ha/bluetooth`: the `manifest.json` `bluetooth` matcher (and `bluetooth_adapters` in `dependencies` on adapter use), advertisement callbacks with a `BluetoothCallbackMatcher` and `BluetoothScanningMode`, the passive or active coordinator family, and the device/service-info lookups. The skill reads `ha/bluetooth`, keeps passive data fetching as the default, and validates offline.

## Scope

Augmenting Bluetooth discovery and data fetching into an existing `custom_components/<domain>/` integration: the `bluetooth` matcher (`connectable`, `service_uuid`, `service_data_uuid`, `manufacturer_id`, `local_name`) in `manifest.json` (plus `bluetooth_adapters` in `dependencies` on adapter use); the advertisement registration via `bluetooth.async_register_callback(hass, callback, matcher, mode)` with a `@callback` signature and lifecycle binding; the use-case-correct Bluetooth coordinator family (`PassiveBluetoothProcessorCoordinator` / `ActiveBluetoothProcessorCoordinator` or the DataUpdate variants); the lookups `async_ble_device_from_address` / `async_last_service_info` and the `bleak`/`bleak-retry-connector` connection handling via the shared scanner.

## Goals

- Form the `manifest.json` `bluetooth` matcher from the documented fields, as the entry point into central BLE discovery, and add `bluetooth_adapters` to `dependencies` when the integration uses an adapter
- Enforce advertisement reception via `bluetooth.async_register_callback` with a `BluetoothCallbackMatcher` and an explicit `BluetoothScanningMode` — instead of running its own `BleakScanner`
- Anchor the `connectable` distinction consistently and prescribe passive data fetching (`connectable=False`) as the default
- Choose the right Bluetooth coordinator family per use case (passive/active processor vs. DataUpdate) and delimit it against the generic `DataUpdateCoordinator`
- Standardize device/service-info lookups via `async_ble_device_from_address` (incl. `None` handling) and `async_last_service_info`, and enforce robust connection handling via the shared scanner

## Non-Goals

- DHCP/SSDP/USB/HomeKit/Zeroconf network discovery — `ha-discovery-augment` / `ha/discovery-mechanisms`
- The full config-flow setup incl. the Bluetooth discovery step — `ha-config-flow-augment` / `ha/config-flow-patterns` (this skill only supplies the matcher and the trigger)
- The generic polling-based `DataUpdateCoordinator` for REST/cloud APIs — `ha/coordinator-patterns`
- Registering own external scanners (`async_register_scanner`) for integrations that themselves provide an adapter — a separate follow-up spec
- Greenfield scaffolding of an integration — `ha-integration-scaffold`; ESPHome Bluetooth-proxy configuration

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add bluetooth discovery / support", "listen for BLE advertisements", "discover this device over Bluetooth"
  - "use a passive/active bluetooth coordinator for this sensor"
  - "füge Bluetooth-Unterstützung hinzu", "höre auf BLE-Advertisements"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the description of how the device announces itself and whether it delivers data over advertisements only or needs an active connection
- **MAY** capture: the matcher fields (`service_uuid`, `service_data_uuid`, `manufacturer_id`, `local_name`, `connectable`), the `BluetoothScanningMode` (`PASSIVE`/`ACTIVE`), and the coordinator family

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** delimit the mechanism: on DHCP/SSDP/USB/HomeKit/Zeroconf redirect to `ha-discovery-augment` and stop; point the config-flow discovery step at `ha-config-flow-augment`
- **MUST** read the `ha/bluetooth` spec
- **MUST NOT** overwrite an existing `bluetooth` matcher or an existing callback/coordinator registration; on collision abort

### Generation rules (from `ha/bluetooth`)

- **MUST** set the `bluetooth` key in `manifest.json` as a list of matcher dicts from the documented fields (`service_uuid`, `local_name`, `manufacturer_id`, `service_data_uuid`, `connectable`); **MUST** add `bluetooth_adapters` to `dependencies` when the integration uses an adapter
- **SHOULD** set `connectable` in the matcher to match the device: `False` when no outgoing connection is needed, so non-connectable controllers also deliver the data; the default is `True`
- **MUST** subscribe to advertisements via `bluetooth.async_register_callback(hass, callback, matcher, mode)` with a `BluetoothCallbackMatcher` (same format as the manifest entry, plus `address` allowed) and an explicit `bluetooth.BluetoothScanningMode` (`ACTIVE`/`PASSIVE`) when the integration needs to be notified about advertisements right away
- **MUST** implement the callback as `@callback` (synchronous, non-blocking) with the signature `(service_info: BluetoothServiceInfoBleak, change: BluetoothChange) -> None` and bind the returned cancel callback to the entry lifecycle via `entry.async_on_unload(...)`
- **MUST** obtain device lookups via `bluetooth.async_ble_device_from_address(hass, address, connectable)` and handle the `None` return value (no adapter in range) instead of starting an additional scanner; **SHOULD** read the latest info via `bluetooth.async_last_service_info(hass, address, connectable)` and check at setup via `bluetooth.async_scanner_count(hass, connectable=True)` for a connectable scanner when the integration must connect
- **MUST** choose the coordinator family by use case: `PassiveBluetoothProcessorCoordinator` for sensors/binary sensors/events from advertisements, `ActiveBluetoothProcessorCoordinator` on connection need, the DataUpdate variants for non-sensor entities; the generic `DataUpdateCoordinator` only on pure connection communication without advertisements
- **MUST** for processor coordinators format the library data into a `PassiveBluetoothDataUpdate` (with `devices`, `entity_descriptions`, `entity_names`, `entity_data`, indexed by `PassiveBluetoothEntityKey`), construct the coordinator with `address`, `mode`, and `update_method`, and bind `coordinator.async_start()` to `entry.async_on_unload(...)` only after `async_forward_entry_setups`; for the active variants check `CoreState.running` and a reachable connectable `BLEDevice` in `needs_poll_method` before `poll_method` connects
- **MUST** for active connections obtain the shared scanner via `bluetooth.async_get_scanner(hass)`, use a fresh `BleakClient` per connection, set a timeout ≥ 10 s, and use `bleak-retry-connector`; **MUST NOT** hold a permanent connection when the data is available from advertisements
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: `manifest.json` carries a `bluetooth` matcher from the documented fields (and `bluetooth_adapters` in `dependencies` on adapter use); advertisement subscriptions run via `async_register_callback` with a `@callback` signature and are bound via `entry.async_on_unload(...)`; device lookups use `async_ble_device_from_address` with `None` handling; passive fetching (`connectable=False`) is the default; the coordinator family is use-case-correct; processor coordinators format `PassiveBluetoothDataUpdate` and start after `async_forward_entry_setups`; connections use `async_get_scanner`, a fresh `BleakClient`, a timeout ≥ 10 s, and `bleak-retry-connector`
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/bluetooth`, plus the changed file paths and the quality-scale marker (**Gold**: `discovery`)

### Prohibitions

- **MUST NOT** instantiate its own `BleakScanner` — the shared scanner is mandatory
- **MUST NOT** handle network discovery (DHCP/SSDP/USB/HomeKit/Zeroconf) or the config-flow discovery step in this skill
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] `manifest.json` contains a `bluetooth` matcher from the documented fields (`service_uuid`, `local_name`, `manufacturer_id`, `service_data_uuid`, `connectable`); `bluetooth_adapters` is in `dependencies` when the integration uses an adapter
- [ ] Advertisement subscriptions run via `bluetooth.async_register_callback` with a `BluetoothCallbackMatcher`, an explicit `BluetoothScanningMode`, and a `@callback` signature `(BluetoothServiceInfoBleak, BluetoothChange)`
- [ ] The cancel callback is bound to the lifecycle via `entry.async_on_unload(...)`
- [ ] Device lookups use `async_ble_device_from_address` and handle the `None` case; service info via `async_last_service_info`
- [ ] Passive data fetching (`connectable=False`) is the default; `connectable=True` only on actual connection need
- [ ] The coordinator family is chosen correctly per use case (passive/active processor vs. DataUpdate vs. generic `DataUpdateCoordinator`)
- [ ] Processor coordinators format `PassiveBluetoothDataUpdate` and start via `async_start()` after `async_forward_entry_setups`; connections use `async_get_scanner`, a fresh `BleakClient`, a timeout ≥ 10 s, and `bleak-retry-connector`
- [ ] Report names the file paths and the quality-scale marker **Gold** (`discovery`)

## Open questions

- **Coordinator-selection heuristic**: `ha/bluetooth` distinguishes processor from DataUpdate coordinators primarily by "sensor/binary sensor/event". Does the skill need a sharper heuristic for devices with mixed entity types, or does it ask in the edge case?
- **`scan_interval`/`scan_duration` default**: Should the skill actively set periodic active-scan windows or adopt the habluetooth default? `ha/bluetooth` leaves a per-device-class recommendation open.
- **macOS unavailable behaviour**: CoreBluetooth caches advertisements, so `_async_handle_unavailable` may never fire. Should the skill require a fallback availability pattern? Currently it follows `ha/bluetooth` and only points it out.
