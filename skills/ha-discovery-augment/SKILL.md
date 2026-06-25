---
name: ha-discovery-augment
description: Augment an existing Home Assistant Custom Integration with one network or bus discovery mechanism beyond Zeroconf — DHCP, SSDP/uPnP, USB, HomeKit, or MQTT discovery — conforming to spec/ha/discovery-mechanisms. Sets the manifest matcher list, implements the typed async_step_<mechanism> in config_flow.py, forwards into a confirm step (never a direct async_create_entry), and wires the unique_id plus _abort_if_unique_id_configured(updates=...) host/IP update path (the Gold discovery-update-info rule). Narrows generic OUI/bridge-chip matchers. Activate on "add DHCP/SSDP/USB/HomeKit/MQTT discovery", "discover the device by MAC/vid:pid/model", "füge DHCP-Discovery hinzu". Do not activate for mDNS/Zeroconf (ha/zeroconf-discovery, scaffold), Bluetooth (ha/bluetooth), greenfield scaffolding (ha-integration-scaffold), generic config-flow auth steps (ha-config-flow-augment), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, discovery]
---

# HA Discovery Augment

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-discovery-augment/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-discovery-augment/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes how the device announces itself and reads back the manifest matcher, the config-flow step, and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-repairs-add`).
- **Mid-flow interactivity** — the mechanism choice, the matcher narrowing, and the Zeroconf/Bluetooth redirect are per-run dialogues the user approves before generation.
- **Bounded, inline generation** — one mechanism's manifest matcher plus its discovery step fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the mechanism decision and the report belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** discovery mechanism — DHCP, SSDP/uPnP, USB, HomeKit, or MQTT — to an existing integration so the user doesn't have to type a host or pick the integration manually.

## When NOT to activate

- mDNS/Zeroconf discovery → `ha/zeroconf-discovery` (the scaffold already produces it)
- Bluetooth discovery → separate sibling spec `ha/bluetooth`
- greenfield integration scaffolding → `ha-integration-scaffold`
- generic config-flow auth/selection steps → `ha-config-flow-augment` / `ha/config-flow-patterns`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One mechanism, one run.** No multi-mechanism batches.
2. **Read [`ha/discovery-mechanisms`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/discovery-mechanisms/de.md) first.** Do not generate from memory.
3. **Right mechanism, with delimitation.** mDNS/Zeroconf → `ha/zeroconf-discovery`/scaffold; Bluetooth → `ha/bluetooth`. Redirect rather than augmenting the wrong one.
4. **Manifest matcher is a list of matcher dicts** under the correct key (`dhcp`/`ssdp`/`usb`/`homekit`/`mqtt`); discovery fires when **all** items of **any one** matcher are present. Narrow generic OUI/bridge-chip matchers (e.g. add a `description` match for `vid: 10C4`/`pid: EA60`).
5. **Typed discovery step.** Implement `async_step_dhcp(self, discovery_info: DhcpServiceInfo)` / `async_step_ssdp(... SsdpServiceInfo)` / `async_step_usb(... UsbServiceInfo)` / `async_step_homekit(... ZeroconfServiceInfo)` / `async_step_mqtt(... MqttServiceInfo)` in `config_flow.py`.
6. **Always confirm.** Forward into a confirm step (`async_step_discovery_confirm` + `self._set_confirm_only()`) before `async_create_entry` — never an entry without user confirmation.
7. **Own the update path.** Set `await self.async_set_unique_id(<stable_id>)` then `self._abort_if_unique_id_configured(updates={CONF_HOST: host})`; never a second entry on re-discovery. For DHCP IP-updates register the MAC (`CONNECTION_NETWORK_MAC`) and set `registered_devices: true`; for MQTT add `mqtt` to `dependencies` and `await mqtt.async_wait_for_mqtt_client(hass)` before subscribing.
8. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` + `config_flow.py` must exist |
| `mechanism` | yes | inferred from situation | `dhcp` / `ssdp` / `usb` / `homekit` / `mqtt` |
| matcher values | no | asked when needed | per mechanism (see hard rule 4) |
| `unique_id` source | no | asked when needed | stable device identifier (MAC / udn / serial / model+id) |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` and `config_flow.py` exist; read `domain`.
2. Resolve `mechanism` (infer + confirm). On a Zeroconf/Bluetooth situation, redirect and stop.
3. Read `ha/discovery-mechanisms`.
4. The mechanism's matcher/step is not already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the resolved `mechanism`, the matcher, the `unique_id` source, and every assumed default in one paragraph. Wait for confirmation.

### 2) Generate

| Mechanism | Manifest key | Step | Matcher fields |
|---|---|---|---|
| DHCP | `dhcp` | `async_step_dhcp` | `hostname` / `macaddress` / `registered_devices` |
| SSDP/uPnP | `ssdp` | `async_step_ssdp` | `st` / `usn` / `server` / `manufacturer` / `deviceType` |
| USB | `usb` | `async_step_usb` | `vid` / `pid` / `serial_number` / `description` |
| HomeKit | `homekit` | `async_step_homekit` | `models` (prefix match) |
| MQTT | `mqtt` | `async_step_mqtt` | topic list (+ `mqtt` in `dependencies`) |

Each step forwards to the confirm step and sets the `unique_id` + `_abort_if_unique_id_configured(updates=...)` path.

### 3) Validate and report

Validate offline (matcher is a list of dicts; the typed step exists; it forwards to a confirm step; it sets `unique_id` + the update abort; DHCP updates carry `registered_devices: true`). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/discovery-mechanisms` acceptance criteria, plus the changed file paths and the quality-scale marker (**Gold**: `discovery`, `discovery-update-info`).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- mDNS/Zeroconf → `ha/zeroconf-discovery` / `ha-integration-scaffold`
- Bluetooth → `ha/bluetooth`
- Generic config-flow auth/selection → `ha-config-flow-augment`
- Deploy to live HA → out of scope
