# HA Integration: Zeroconf Discovery

Status: draft

## Context

Local integrations (with `iot_class: local_polling` or `local_push` from `ha/integration-architecture`) should not force the user to type the IP, port, and endpoint path of their backend by hand — when the backend announces over **mDNS / Zeroconf**, HA can suggest the setup automatically the moment the user adds the integration in the frontend. That is not just a UX improvement but also a quality-scale expectation: HA Silver requires an integration to support discovery if the backend offers a local discovery mechanism.

`nolte/kamerplanter-ha` validates this pattern with the service type `_kamerplanter._tcp.local.` and TXT records that carry `version`, `api_path`, `instance_id`, `tenant`, and `scheme`. The config flow uses these records as pre-fill for the user-confirmation page and sets `unique_id` from the `instance_id`, so re-discovery (for example after an IP change) does not create a second entry but updates the existing entry with the new IP.

This spec lifts the pattern into a generic obligation. DHCP, SSDP, MQTT, Bluetooth, and USB discovery follow the same shape but live in their own follow-up specs (`ha/dhcp-discovery`, `ha/ssdp-discovery`, …); this spec covers zeroconf only.

Quality scale marker: **Silver** (discovery for local integrations is a Silver requirement when the backend offers a discovery mechanism).

## Goals

- Establish zeroconf as the standard discovery mechanism for `iot_class: local_*` integrations whenever the backend announces over mDNS
- Define a TXT-record schema that skill output can derive from the backend's discovery code
- Make `async_step_zeroconf` a pre-fill source for the user step — discovery does not bypass the user-confirmation step
- Handle re-discovery with IP / port changes cleanly: `unique_id` stays stable, IP / port are updated in `entry.data`
- Resolve discovery conflicts in multi-instance setups (two backend instances on the same network) clearly

## Non-Goals

- Backend-side mDNS announce implementation — the backend is not part of this plugin; the spec only covers the HA-side behaviour
- DHCP, SSDP, MQTT, Bluetooth, USB discovery — separate follow-up specs
- Service-type reservation at IANA — backend authoring task, not a plugin task
- HA's own discovery cache behaviour — HA-internal detail; the plugin relies on HA's guarantees

## Requirements

### `manifest.json:zeroconf` key

- **MUST** set `manifest.json:zeroconf` as a list of mDNS service types as soon as the integration supports zeroconf discovery — typically `["_<domain>._tcp.local."]`
- **MUST** format the service-type string as `_<name>._tcp.local.` — the trailing dot is mandatory (mDNS convention)
- **MAY** list multiple service types when the backend produces multiple announces (for example one for auth, one for API) — rarely justified
- **MUST NOT** use `_<name>._udp.local.` without explicit reason — most REST / HTTP APIs use TCP

### TXT-record schema

- **SHOULD** announce at least these keys in the TXT record:
  - `instance_id` — a unique, stable backend instance ID; becomes the `unique_id` of the config entry
  - `version` — the backend version; useful for compatibility checks in the skill
  - `api_path` — the API path prefix (for example `/api`); together with IP / port it produces the full URL
  - `scheme` — `http` or `https`; default `http` when not set
- **MAY** announce additional keys (for example `tenant`, `mode`, `region`) when the integration needs them for multi-tenant or multi-mode resolution
- **MUST NOT** expect `api_key` or other secrets in the TXT record — TXT records are visible unencrypted on the LAN; secrets belong in the user-input step

### `async_step_zeroconf`

- **MUST** implement `async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult` in `config_flow.py` when `manifest.json:zeroconf` is set
- **MUST** derive `unique_id` from the TXT-record `instance_id` and set it via `await self.async_set_unique_id(<instance_id>)`
- **MUST** call `self._abort_if_unique_id_configured(updates={...})` immediately after `async_set_unique_id` — the `updates` map carries `host` / `port` / `api_path` updates, so an existing configuration is refreshed to the new IP
- **MUST** store discovery data as instance attributes between steps (`self._discovered_url`, `self._discovered_instance_id`), so the downstream user-confirmation step can pre-fill them
- **MUST** route into a confirmation step — typically `async_step_user` with pre-fill, or a dedicated `async_step_zeroconf_confirm` — never call `async_create_entry` directly without the user having seen the discovery data
- **SHOULD** run backend validation (test connection) only in the confirmation step after the user confirms the discovery data — validation during discovery reception would trigger uncommitted calls

### Pre-fill pattern

- **MUST** insert discovery data as suggested values into the schema of the downstream user step (`add_suggested_values_to_schema(SCHEMA, discovery_payload)`); the user sees IP, port, API path, and instance ID and can override every field
- **MUST** plan a separate step for auth credentials when the backend requires authentication — discovery does not deliver credentials
- **SHOULD** use multi-step flows when discovery pre-fill plus auth plus multi-tenant selection are all required — see `ha/config-flow-patterns` for the multi-step convention

### Re-discovery with IP change

- **MUST** update the existing entry on re-discovery (same `instance_id`, new IP / port) via `_abort_if_unique_id_configured(updates={CONF_HOST: discovery.host, CONF_PORT: discovery.port, CONF_API_PATH: discovery.properties["api_path"]})` — the entry receives the new endpoint data without user interaction
- **MUST NOT** create a second entry with the same `instance_id` on re-discovery — that is what `_abort_if_unique_id_configured` is for
- **SHOULD** notify the user in HA notifications when the IP / port change has been applied — typically via an `entry.async_create_issue` call

### Multi-instance handling

- **MUST** allow each backend instance on the LAN (each with its own `instance_id`) to be a separate config entry — `unique_id` disambiguation happens automatically via the differing `instance_id`s
- **MUST NOT** merge discovery results across multiple instances — each discovery is its own flow; the user clicks through two separate setup wizards

## Acceptance Criteria

- [ ] `manifest.json:zeroconf` is set as a list of service types (format `_<name>._tcp.local.`)
- [ ] `config_flow.py` contains `async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo)`
- [ ] `async_step_zeroconf` sets `unique_id` from the TXT-record `instance_id` and calls `_abort_if_unique_id_configured(updates={...})` with IP / port / API-path updates
- [ ] `async_step_zeroconf` routes into a confirmation step — never a direct `async_create_entry`
- [ ] The confirmation step uses `add_suggested_values_to_schema(...)` with the discovery data
- [ ] TXT records with `instance_id`, `version`, `api_path`, `scheme` are read
- [ ] Re-discovery with the same `instance_id` and changed endpoint data updates the existing entry, never creates a new one
- [ ] Quality scale marker: **Silver**

## Open Questions

- **Backend-authoring guidance**: Should the plugin carry a separate spec for the backend side (mDNS announce with recommended TXT schema), or does that remain a backend task only? `kamerplanter-ha` carries mock discovery in the test suite but no backend spec.
- **TXT-record minimum requirement**: `instance_id` is clearly mandatory; should `version`, `api_path`, `scheme` be raised to MUST as well, or remain SHOULD?
- **Issue creation on IP change**: Should the spec require `entry.async_create_issue` or keep it MAY? Currently SHOULD — user-feedback behaviour is not standardised.
- **Service-type collisions**: What happens when two different backends announce the same service type (for example two vendors using `_apex._tcp.local.`)? Currently not addressed; in practice a communication issue between backend authors.
- **Combined discovery (zeroconf + DHCP)**: Should skills supporting both mechanisms collapse into a combined spec, or stay separate? `kamerplanter-ha` covers only zeroconf; the question opens once the first DHCP-capable skill arrives.
