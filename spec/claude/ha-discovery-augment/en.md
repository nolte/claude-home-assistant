# Skill: `ha-discovery-augment`

Status: draft

## Context

`ha/discovery-mechanisms` defines the network and bus discovery beyond mDNS/Zeroconf: **DHCP**, **SSDP/uPnP**, **USB**, **HomeKit**, and **MQTT discovery**. Every mechanism follows the same pattern — the manifest declares matchers (`dhcp`/`ssdp`/`usb`/`homekit`/`mqtt`), on a hit HA loads the matching config-flow step with typed discovery info, and a network-based mechanism pulls in new host/IP data via `unique_id` + `_abort_if_unique_id_configured(updates=...)` (the Gold rule `discovery-update-info`). The `ha-integration-scaffold` skill produces only the **Zeroconf** path (`ha/zeroconf-discovery`); no skill has augmented the other mechanisms so far. In practice developers forget the confirm step (a direct `async_create_entry` without user confirmation), the `unique_id` update path (a second entry on re-discovery), or match too broadly (generic OUI/bridge-chip matchers catch foreign devices).

This skill augments **one** discovery mechanism (DHCP/SSDP/USB/HomeKit/MQTT) into an **existing** integration: it sets the manifest matcher, implements the `async_step_<mechanism>` step in `config_flow.py`, forwards to a confirm step, and wires the `unique_id`/`discovery-update-info` path — conformant to `ha/discovery-mechanisms`. It augments the scaffold's Zeroconf with the Gold rule `discovery`.

## Scope

Augmenting exactly one discovery mechanism per run (`dhcp`, `ssdp`, `usb`, `homekit`, `mqtt`) into an existing `custom_components/<domain>/` integration: the manifest matcher key, the typed `async_step_<mechanism>` in `config_flow.py`, the forward to a confirm step, and the `unique_id` + `_abort_if_unique_id_configured(updates=...)` path. The skill reads `ha/discovery-mechanisms` and validates.

## Goals

- Pick the right mechanism from a described device-discovery situation and augment it spec-conformantly (manifest matcher + config-flow step)
- Make the matcher narrow enough that no foreign devices are caught (OUI/bridge-chip sharpening)
- Forward every discovery step into a confirm step — never a direct `async_create_entry` without user confirmation
- Make the `discovery-update-info` path mandatory: `unique_id` from a stable identifier, `_abort_if_unique_id_configured(updates=...)` to pull in host/IP
- Delimit sharply from `ha/zeroconf-discovery` (mDNS) and `ha/bluetooth` — no duplicated material

## Non-Goals

- mDNS/Zeroconf discovery — `ha/zeroconf-discovery` (produced by the scaffold)
- Bluetooth discovery — separate sibling spec `ha/bluetooth`
- Greenfield scaffolding of an integration — `ha-integration-scaffold`
- The generic config-flow multi-step mechanics (auth, selection) in detail — `ha-config-flow-augment` / `ha/config-flow-patterns`
- The generic manifest schema rules — `ha/integration-manifest`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add DHCP / SSDP / USB / HomeKit / MQTT discovery to the integration"
  - "discover the device by MAC / vid:pid / model / SSDP service"
  - "update the host when the device gets a new IP"
  - "füge DHCP-/SSDP-/USB-/HomeKit-Discovery hinzu", "entdecke das Gerät über die MAC / vid:pid"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the mechanism or discovery situation (prose), from which the skill derives and confirms the mechanism
- **MAY** capture: the matcher values per mechanism (`hostname`/`macaddress`/`registered_devices`; `st`/`manufacturer`/`deviceType`; `vid`/`pid`/`serial_number`/`description`; `models`; `mqtt` topics) and the `unique_id` source

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` and `config_flow.py` exist; read `domain`
- **MUST** resolve the mechanism and check the delimitation: if the situation is mDNS/Zeroconf (→ `ha/zeroconf-discovery`/scaffold) or Bluetooth (→ `ha/bluetooth`), the skill **MUST** redirect instead of augmenting a wrong mechanism
- **MUST** read the `ha/discovery-mechanisms` spec
- **MUST NOT** overwrite an already-declared mechanism matcher/step; on collision abort

### Generation rules (per mechanism, from `ha/discovery-mechanisms`)

- **MUST** set the manifest matcher as a list of matcher dictionaries under the matching key — discovery happens when **all** items of **any one** matcher are found in the discovery data:
  - `dhcp`: at least one of `hostname` (fnmatch), `macaddress` (OUI prefix), `registered_devices: true`
  - `ssdp`: SSDP headers (`st`/`usn`/`server`, lowercase) or uPnP fields (`manufacturer`/`deviceType`)
  - `usb`: `vid`/`pid`/`serial_number`/`manufacturer`/`description`
  - `homekit`: `models` as a list of model-name **prefixes** (prefix match)
  - `mqtt`: a list of topics; add `mqtt` to `dependencies`
- **MUST** for generic USB bridge chips (e.g. `vid: 10C4`/`pid: EA60`) additionally match on `description` or similar so no unexpected discovery fires
- **MUST** implement the matching typed step in `config_flow.py`: `async_step_dhcp(self, discovery_info: DhcpServiceInfo)`, `async_step_ssdp(self, discovery_info: SsdpServiceInfo)`, `async_step_usb(self, discovery_info: UsbServiceInfo)`, `async_step_homekit(self, discovery_info: ZeroconfServiceInfo)`, or `async_step_mqtt(self, discovery_info: MqttServiceInfo)`
- **MUST** forward into a confirm step (typically `async_step_discovery_confirm` with `self._set_confirm_only()`) before calling `async_create_entry` — never an entry without user confirmation
- **MUST** in the discovery step set `await self.async_set_unique_id(<stable_id>)` and immediately call `self._abort_if_unique_id_configured(updates={CONF_HOST: host})`; a second entry on re-discovery is forbidden
- **MUST** for DHCP IP-update flows register the MAC via `CONNECTION_NETWORK_MAC` in the device info and set `registered_devices: true`
- **SHOULD** run backend validation (test connection) in the discovery step and on failure return `self.async_abort(reason="cannot_connect")`; for MQTT use `await mqtt.async_wait_for_mqtt_client(hass)` before subscribing
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: the manifest matcher is a list of dicts; the matching `async_step_<mechanism>` exists in `config_flow.py`; every step forwards into a confirm step; every step sets `unique_id` + `_abort_if_unique_id_configured(updates=...)`; for DHCP updates `registered_devices: true`
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/discovery-mechanisms`, plus the changed file paths and the quality-scale marker (**Gold**: `discovery`, `discovery-update-info`)

### Prohibitions

- **MUST NOT** augment more than one mechanism per run
- **MUST NOT** let a discovery step create an entry without the user confirming the discovery
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill derives the mechanism (or asks) and checks the Zeroconf/Bluetooth delimitation in pre-flight
- [ ] The manifest matcher is a list of matcher dictionaries under the correct key
- [ ] The matching typed `async_step_<mechanism>` exists in `config_flow.py`
- [ ] Every discovery step forwards into a confirm step — no direct `async_create_entry`
- [ ] Every discovery step sets `unique_id` and calls `_abort_if_unique_id_configured(updates={...})`
- [ ] Generic USB bridge chips carry an additional `description` matcher
- [ ] For DHCP IP-updates the MAC is registered and `registered_devices: true` is set
- [ ] Report names the file paths and the quality-scale marker **Gold**

## Open questions

- **Stable identifier per mechanism**: which `unique_id` source is canonical per mechanism (DHCP MAC, SSDP `udn`, USB `serial_number`, HomeKit model+ID)? Currently generic as "stable identifier"; the skill asks when in doubt.
- **Combined discovery**: when an integration offers several mechanisms (SSDP + DHCP for IP updates) — a shared confirm step or one mechanism per run? Currently one mechanism per run.
- **MQTT special case**: MQTT discovery is topic- rather than network-based. Does it stay in this skill or earn its own once MQTT integrations become common?
