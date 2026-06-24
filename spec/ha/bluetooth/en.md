# HA Integration: Bluetooth

Status: draft

## Context

With the `bluetooth` component, Home Assistant provides shared infrastructure for BLE discovery, advertisement reception, and connection brokering. A Custom Integration enters the central discovery through `manifest.json` matchers, subscribes to advertisements via callback APIs, and obtains `BLEDevice` objects for active connections from the shared scanner when needed — instead of running its own `BleakScanner`.

The core difference from the generic polling world is **advertisement-driven** data fetching: HA supports remote Bluetooth controllers, some of which only receive advertisements and cannot establish outgoing connections. From this follows the consistent distinction between `connectable` and non-connectable devices. Many sensors need advertisements only; an active connection is the exception, not the rule.

For data fetching, HA offers specialized coordinator families (`PassiveBluetoothProcessorCoordinator`, `ActiveBluetoothProcessorCoordinator`, `PassiveBluetoothDataUpdateCoordinator`, `ActiveBluetoothDataUpdateCoordinator`) that are driven by incoming advertisements instead of polling. This spec delimits itself against `ha/coordinator-patterns`, which defines the generic polling-based `DataUpdateCoordinator` for API/device endpoints — the Bluetooth coordinators are a separate family and are covered here.

## Goals

- Establish the `manifest.json` `bluetooth` matcher as the entry point into central BLE discovery
- Enforce advertisement reception through the shared callback APIs (`async_register_callback`) instead of running an own `BleakScanner`
- Anchor the `connectable` distinction consistently and prescribe passive data fetching as the default
- Standardize device/service-info lookups via the `bluetooth` APIs (`async_ble_device_from_address`, `async_last_service_info`, `async_address_present`, `async_scanner_count`)
- Make the right Bluetooth coordinator family selectable per use case and delimit it against the generic coordinator
- Enforce robust connection handling via `bleak` / `bleak-retry-connector` using the shared scanner

## Non-Goals

- The generic polling-based `DataUpdateCoordinator` for REST/cloud APIs — belongs to `ha/coordinator-patterns`
- Registering own external scanners (`async_register_scanner`, `async_get_advertisement_callback` as the provider side) — relevant only for integrations that themselves provide a Bluetooth adapter; separate follow-up spec if needed
- The full config-flow setup including the Bluetooth discovery step — belongs to `ha/config-flow-patterns`; this spec only supplies the matcher and the discovery trigger
- ESPHome Bluetooth-proxy configuration and add-on-side adapter provisioning
- Persistent caches of advertisement data across HA restarts

## Requirements

### Discovery via manifest matcher

- **MUST** set the `bluetooth` key in `manifest.json` to trigger central discovery for the integration's devices (see `ha/integration-manifest`)
- **MUST** form the matcher from the documented fields — valid are advertised `service_uuid`(s), `local_name`, `manufacturer_id`, `service_data_uuid`, and `connectable`
- **SHOULD** set `connectable` in the matcher to match the device: `False` when the device needs no outgoing connection, so non-connectable controllers also deliver the data; the default is `True`
- **MAY** use additional fields such as `manufacturer_data_first_byte` alongside `manufacturer_id` for HomeKit-style filters
- **MUST** add `bluetooth_adapters` to `dependencies` in `manifest.json` when the integration uses a Bluetooth adapter — this ensures all supported remote adapters are connected before the integration uses them
- **MUST NOT** build a matcher that cannot separate similar devices with differing connection needs without checking the `connectable` property of the `BluetoothServiceInfoBleak` in the config flow and rejecting flows for devices that are unreachable (see `ha/config-flow-patterns`)

### Advertisement callbacks

- **MUST** subscribe to advertisements via `bluetooth.async_register_callback(hass, callback, matcher, mode)` when the integration needs to be notified about new advertisements right away — instead of running its own scanner
- **MUST** implement the callback as `@callback` (synchronous, non-blocking) with the signature `(service_info: BluetoothServiceInfoBleak, change: BluetoothChange) -> None`
- **MUST** supply the matcher in the same format as the `manifest.json` `bluetooth` entry; in addition, `address` is allowed as a matcher field
- **MUST** pass the scanning mode explicitly via `bluetooth.BluetoothScanningMode` (`ACTIVE` / `PASSIVE`)
- **MUST** bind the cancel callback returned by `async_register_callback` to the entry lifecycle (`entry.async_on_unload(...)`) — otherwise the registration survives entry unload
- **MAY** request periodic active-scan windows for exactly that address via the optional keyword arguments `scan_interval` and `scan_duration` when the matcher is `address`-specific and the mode is not `PASSIVE`; without an `address` in the matcher the active-scan request is skipped

### Device/service-info lookup

- **MUST** obtain a `BLEDevice` via `bluetooth.async_ble_device_from_address(hass, address, connectable)` instead of starting an additional scanner to resolve the address; the API returns the `BLEDevice` of the nearest reachable adapter, or `None` when no adapter can reach the device
- **MUST** handle the `None` return value of `async_ble_device_from_address` — it means no adapter is currently in range
- **SHOULD** read the latest advertisement/device info via `bluetooth.async_last_service_info(hass, address, connectable)` — it returns the `BluetoothServiceInfoBleak` from the scanner with the best RSSI of the requested `connectable` type
- **MAY** check whether the device is still present via `bluetooth.async_address_present(hass, address, connectable)` when the integration needs presence for availability
- **SHOULD** check at setup via `bluetooth.async_scanner_count(hass, connectable=True)` whether a matching scanner is running at all, and raise a helpful error when no connectable-capable scanner is available

### Passive vs. connectable

- **MUST** operate passively (`connectable=False`) whenever the device delivers its data exclusively through advertisements — opting in to non-connectable controllers then delivers data from connectable and non-connectable controllers
- **MUST** use `connectable=True` only where an outgoing connection is actually needed; the default for `connectable` is `True`
- **SHOULD** set the `connectable` flag per device appropriately in `manifest.json` for mixed devices instead of forcing the whole integration to `connectable=True`
- **MAY** exchange a non-connectable obtained `BLEDevice` for a connectable one when a connection becomes necessary — as long as at least one connectable controller is in range (`async_ble_device_from_address(..., connectable=True)`)

### Bluetooth coordinators (passive/active)

- **MUST** choose the coordinator family by use case: `PassiveBluetoothProcessorCoordinator` for sensors/binary sensors/events whose data comes entirely from advertisements; `ActiveBluetoothProcessorCoordinator` when some sensors need an active connection
- **MUST** choose the matching non-processor variant for non-sensor entities: `PassiveBluetoothDataUpdateCoordinator` (purely advertisement-driven) or `ActiveBluetoothDataUpdateCoordinator` (with `needs_poll_method` / `poll_method` for active connections)
- **MUST** use the generic polling-based `DataUpdateCoordinator` (see `ha/coordinator-patterns`) only when the device communicates exclusively over an active connection and uses no advertisements at all
- **MUST** format the library data for the processor coordinators into a `PassiveBluetoothDataUpdate` object (with `devices`, `entity_descriptions`, `entity_names`, `entity_data`, indexed by `PassiveBluetoothEntityKey`) so the framework creates entities on demand
- **MUST** construct the coordinator with `address`, `mode` (`BluetoothScanningMode`), and `update_method`, and bind `coordinator.async_start()` to `entry.async_on_unload(...)` only after `async_forward_entry_setups`, so all platforms could subscribe beforehand
- **MUST** check in the `needs_poll_method` of `ActiveBluetoothProcessorCoordinator` / `ActiveBluetoothDataUpdateCoordinator` that HA is running (`CoreState.running`) and a connectable `BLEDevice` is reachable before `poll_method` opens a connection
- **MAY** request a periodic active-scan window for the address via the optional `scan_interval` / `scan_duration` arguments of the processor coordinators; only `AUTO` mode scanners honor the request, `PASSIVE`/`ACTIVE` scanners are left untouched

### Connection handling (bleak/retry-connector)

- **MUST** obtain the shared scanner via `bluetooth.async_get_scanner(hass)` and pass it to the library instead of instantiating an own `BleakScanner` — this avoids the significant overhead of multiple scanners and survives the user's adapter changes
- **MUST** not reuse a `BleakClient` between connections — this makes connecting less reliable
- **MUST** use a connection timeout of at least ten (10) seconds, since `BlueZ` must resolve the services when connecting to a new or updated device for the first time
- **SHOULD** use the PyPI package `bleak-retry-connector` to establish connections reliably — transient connection errors are frequent and the first attempt does not always succeed
- **MUST NOT** hold a permanent connection for ongoing data fetching when the data is available from advertisements — the active connection is only the poll path of the active coordinators

## Acceptance Criteria

- [ ] `manifest.json` contains a `bluetooth` matcher built from the documented fields (`service_uuid`, `local_name`, `manufacturer_id`, `service_data_uuid`, `connectable`)
- [ ] Advertisement subscriptions run via `bluetooth.async_register_callback(hass, callback, matcher, mode)` with a `@callback` signature `(BluetoothServiceInfoBleak, BluetoothChange)`
- [ ] The cancel callback from `async_register_callback` is bound to the lifecycle via `entry.async_on_unload(...)`
- [ ] Device lookups use `async_ble_device_from_address` and handle the `None` case
- [ ] Service-info / presence lookups use `async_last_service_info` or `async_address_present`
- [ ] `async_scanner_count` is checked at setup when the integration needs a connectable scanner
- [ ] Passive data fetching (`connectable=False`) is the default; `connectable=True` only on actual connection need
- [ ] The coordinator family is chosen correctly per use case (passive/active processor vs. DataUpdate vs. generic `DataUpdateCoordinator`)
- [ ] Processor coordinators format library data into `PassiveBluetoothDataUpdate` and start via `async_start()` after `async_forward_entry_setups`
- [ ] Connections use `async_get_scanner`, a fresh `BleakClient` per connection, a timeout ≥ 10 s, and `bleak-retry-connector`

## Open Questions

- **Coordinator-selection heuristic**: The HA docs distinguish processor from DataUpdate coordinators primarily by whether the main function is "sensor/binary sensor/event". Does this spec need a sharper, measurable heuristic for the edge case (for example devices with mixed entity types)?
- **`scan_interval` / `scan_duration` default**: Should the skills of this plugin actively set the periodic active-scan windows, or adopt the habluetooth default (5 min interval, 10 s duration)? A recommendation per device class is missing.
- **macOS unavailable behaviour**: On macOS, CoreBluetooth caches advertisement data, so `_async_handle_unavailable` may never fire. Should the spec require a fallback availability pattern (for example `async_track_unavailable` plus a timestamp check) for this platform?
- **Delimitation of external scanners**: Registering own scanners (`async_register_scanner`) is a non-goal here. From when does the portfolio need a dedicated `ha/bluetooth-scanner-provider` spec for it?
- **Rediscovery after entry removal**: The docs require `async_rediscover_address` when removing an entry/device. Should this spec take that up as a hard requirement, or does it stay part of the `ha/setup-lifecycle` spec?
