# HA Integration: Discovery Mechanisms (DHCP/SSDP/USB/HomeKit)

Status: draft

## Context

An integration should not force the user to type the IP address, host, or device identifier by hand when HA can discover the device on the network or on the USB bus itself. The quality-scale rule `discovery` (Gold) lists the supported discovery methods explicitly as App, Bluetooth, DHCP, HomeKit, mDNS, MQTT, SSDP, and USB. Discovery greatly reduces the setup effort — the user does not have to look up which integration matches the device, nor type a host.

`ha/zeroconf-discovery` already covers the mDNS / zeroconf path in full (manifest key `zeroconf`, `async_step_zeroconf`, TXT-record schema). This spec covers only the **other** network and bus discovery mechanisms: **DHCP**, **SSDP/uPnP**, **USB**, and **HomeKit** (plus **MQTT discovery**). Bluetooth discovery has its own sibling spec (`ha/bluetooth`). The manifest matcher keys belong to `ha/integration-manifest`; the multi-step-flow convention of the confirmation steps lives in `ha/config-flow-patterns`. This spec references those siblings by slug and does not duplicate them.

Every mechanism follows the same base shape: the manifest declares matchers; on a match HA loads the matching `dhcp`/`ssdp`/`usb`/`homekit` step of the config flow with typed discovery info. A network-based discovery additionally allows the configuration to be updated once a device receives a new IP address — that is the Gold rule `discovery-update-info`.

Quality scale marker: **Gold** (`discovery` and `discovery-update-info`).

## Goals

- Establish DHCP, SSDP/uPnP, USB, and HomeKit discovery as the standard pattern whenever the device offers one of these mechanisms
- Define the manifest matcher keys per mechanism (`dhcp`, `ssdp`, `usb`, `homekit`, `mqtt`) and what each matcher triggers
- Establish the config-flow discovery steps (`async_step_dhcp`, `async_step_ssdp`, `async_step_usb`, `async_step_homekit`) with their typed discovery-info objects
- Make the entry-update path from discovery (`discovery-update-info`) mandatory: set `unique_id`, `_abort_if_unique_id_configured(updates=...)` to refresh host/IP
- Keep the delimitation against `ha/zeroconf-discovery` and `ha/bluetooth` clean — no duplicated mDNS / Bluetooth material

## Non-Goals

- mDNS / zeroconf discovery — fully covered in `ha/zeroconf-discovery`, not duplicated here
- Bluetooth discovery — its own sibling spec `ha/bluetooth`
- The generic manifest-schema rules (required fields, `dependencies`, `quality_scale`) — `ha/integration-manifest`
- The multi-step-flow mechanics of the confirmation steps in detail — `ha/config-flow-patterns`
- HA-internal discovery cache and listener implementation — HA-internal detail; the plugin relies on HA's guarantees

## Requirements

### DHCP

- **MUST** set `manifest.json:dhcp` as a list of matcher dictionaries when the integration supports DHCP discovery — HA then listens passively and loads the `dhcp` step as soon as a device matches
- **MUST** provide per matcher at least one of the keys `hostname` (Unix fnmatch pattern), `macaddress` (OUI prefix), or `registered_devices: true` — discovery happens when **all** items of **any** matcher are found in the DHCP data
- **SHOULD** set `registered_devices: true` when the integration only wants to receive IP updates for already-configured devices and a `hostname` / OUI match would be too broad — this requires the MAC registered in the device registry via `CONNECTION_NETWORK_MAC`
- **SHOULD** prefer `zeroconf` or `ssdp` over `dhcp` when the device offers them — they generally offer the better user experience
- **MUST NOT** rely on a generic `hostname` or OUI matcher alone that catches foreign devices — the config flow must filter out duplicates itself

### SSDP/uPnP

- **MUST** set `manifest.json:ssdp` as a list of matcher dictionaries when the integration supports SSDP discovery — HA then loads the `ssdp` step
- **MUST** phrase matchers against SSDP / uPnP data: SSDP headers `st`, `usn`, `ext`, `server` (header names lowercase) or fields of the uPnP device description such as `manufacturer` and `deviceType` — discovery happens when **all** items of **any** matcher are found
- **MAY** use `ssdp.async_register_callback(hass, cb, {"st": ...})` from `homeassistant.components.ssdp` to receive runtime callbacks on new matches — the same matcher format as in the manifest, and the registration is cleaned up via `entry.async_on_unload(...)`
- **MUST NOT** assume HA resolves duplicates across multiple uPnP services of the same `UDN` — the config flow filters duplicates itself

### USB

- **MUST** set `manifest.json:usb` as a list of matcher dictionaries when the integration supports USB discovery — HA loads the `usb` step at startup, when the integrations page is accessed, and when plugged in (if `pyudev` is available)
- **MUST** build matchers from the USB descriptor values: `vid` (Vendor ID), `pid` (Device ID), `serial_number`, `manufacturer`, `description` — discovery happens when **all** items of **any** matcher are found in the USB data
- **MUST** also match on `description` or another identifier for generic bridge chips (for example `vid: 10C4` / `pid: EA60`, Silicon Labs CP2102) — otherwise an unexpected discovery triggers
- **MAY** use `usb.async_is_plugged_in(hass, {...})` from `homeassistant.components.usb` to check in `async_setup_entry` whether the adapter is plugged in, and otherwise raise `ConfigEntryNotReady`

### HomeKit

- **MUST** set `manifest.json:homekit` with the key `models` as a list of model names when the integration supports HomeKit discovery — HA loads the `homekit` step when the `zeroconf` integration is loaded
- **MUST** note that HomeKit discovery works by prefix match: it triggers when the discovered model name **starts with** **any** of the listed model names
- **MAY** talk to the device over any protocol — a `homekit` manifest declaration does not require speaking the HomeKit protocol
- **MUST NOT** expect the same discovery info to also reach HomeKit zeroconf listeners — once it is routed to the integration because of the `homekit` manifest entry, it no longer reaches those listeners

### MQTT discovery

- **MUST** set `manifest.json:mqtt` as a list of MQTT topics when the integration supports MQTT discovery — HA loads the `mqtt` step when the `mqtt` integration is loaded, by subscribing to the listed topics
- **MUST** add `mqtt` to `dependencies` in the manifest when the integration requires MQTT (see `ha/integration-manifest`)
- **SHOULD** wait for the MQTT client to become available with `await mqtt.async_wait_for_mqtt_client(hass)` before subscribing — the call blocks and returns `True` once the client is available

### Config-flow discovery steps

- **MUST** implement the matching step in `config_flow.py` for each declared manifest matcher: `async_step_dhcp(self, discovery_info: DhcpServiceInfo)`, `async_step_ssdp(self, discovery_info: SsdpServiceInfo)`, `async_step_usb(self, discovery_info: UsbServiceInfo)`, `async_step_homekit(self, discovery_info: ZeroconfServiceInfo)` — each receives its typed discovery info
- **MUST** route into a confirmation step (typically `async_step_discovery_confirm` with `self._set_confirm_only()`) before calling `async_create_entry` — never create an entry without the user having confirmed the discovery
- **SHOULD** run backend / device validation (test connection) in the discovery step and return `self.async_abort(reason="cannot_connect")` on failure before branching into the confirmation step
- **SHOULD** use the multi-step-flow convention from `ha/config-flow-patterns` when confirmation plus auth plus selection are required

### Entry update from discovery

- **MUST** set the `unique_id` in the discovery step from a stable device identifier — `await self.async_set_unique_id(<stable_id>)` — and immediately call `self._abort_if_unique_id_configured(updates={CONF_HOST: host})` (Gold rule `discovery-update-info`)
- **MUST** perform the IP / host update only when the integration is sure it is the same previously-configured device — `unique_id` equality is exactly that proof
- **MUST** register the MAC address in the device info and set `registered_devices: true` in the manifest for DHCP IP-update flows — otherwise no discovery flows are created for IP updates of already-configured devices
- **MUST NOT** create a second entry on re-discovery of the same device — `_abort_if_unique_id_configured` aborts the flow and refreshes the new endpoint data instead

## Acceptance Criteria

- [ ] `manifest.json:dhcp` is a list of matcher dictionaries with `hostname`/`macaddress`/`registered_devices`, and `config_flow.py` contains `async_step_dhcp(self, discovery_info: DhcpServiceInfo)`
- [ ] `manifest.json:ssdp` is a list of matcher dictionaries (`st`/`manufacturer`/`deviceType` …), and `config_flow.py` contains `async_step_ssdp(self, discovery_info: SsdpServiceInfo)`
- [ ] `manifest.json:usb` is a list of matcher dictionaries (`vid`/`pid`/`serial_number`/`manufacturer`/`description`), and `config_flow.py` contains `async_step_usb(self, discovery_info: UsbServiceInfo)`
- [ ] `manifest.json:homekit` sets `models` as a list of model-name prefixes, and `config_flow.py` contains `async_step_homekit(self, discovery_info)`
- [ ] `manifest.json:mqtt` is a list of topics, `mqtt` is in `dependencies` when required, and the code waits with `async_wait_for_mqtt_client`
- [ ] Each discovery step routes into a confirmation step — never a direct `async_create_entry` without user confirmation
- [ ] Each discovery step sets `unique_id` and calls `_abort_if_unique_id_configured(updates={...})` to refresh host/IP
- [ ] For DHCP IP updates the MAC is registered in the device info and `registered_devices: true` is set in the manifest
- [ ] Quality scale marker: **Gold** (`discovery`, `discovery-update-info`)

## Open Questions

- **MQTT delimitation**: MQTT discovery shares the matcher / step shape but is topic- rather than network-based. Does it stay in this spec, or does it deserve its own `ha/mqtt-discovery` once the first MQTT skill arrives?
- **`registered_devices` requirement**: Should `registered_devices: true` for IP-update flows be raised from SHOULD to MUST once the integration targets `discovery-update-info` (Gold)?
- **Stable identifier per mechanism**: Zeroconf uses a TXT `instance_id`. Which identifier is the canonical `unique_id` source per mechanism (DHCP MAC, SSDP `udn`, USB `serial_number`, HomeKit model + ID)? Currently kept generic as "stable device identifier".
- **HomeKit-vs-zeroconf routing**: The `homekit` entry pulls the discovery info away from HomeKit zeroconf listeners. Is a cross-reference rule with `ha/zeroconf-discovery` needed to avoid double declarations?
- **Combined discovery**: Should integrations that declare multiple mechanisms at once (for example SSDP + DHCP for IP updates) share a common confirmation-step pattern, or does each step stay standalone?
