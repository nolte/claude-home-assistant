# HA Integration: Setup Lifecycle

Status: draft

## Context

Every Custom Integration with config-entry support runs through a fixed lifecycle: Home Assistant calls `async_setup_entry(hass, entry)` at startup (and when a new entry is created at runtime), forwards the setup to platforms, and calls `async_unload_entry(hass, entry)` on removal or reload. The lifecycle has explicit states — `not loaded`, `setup in progress`, `loaded`, `setup error`, `setup retry`, `unload in progress`, `failed unload` — that HA derives from the return value or the exceptions raised by these functions.

The lifecycle decides whether an integration handles transient outages, expired credentials, and reloads robustly, or whether it forces HA restarts and leaks resources. For that, HA provides three distinct setup-failure exceptions (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`), a teardown protocol (`async_unload_platforms` + `async_on_unload` callbacks), and the `PARALLEL_UPDATES` module constant for load limiting. This spec lifts the HA lifecycle documentation and the relevant quality-scale rules into a binding convention for every integration that skills in this plugin scaffold.

The coordinator-internal update failures (`UpdateFailed`, periodic error mapping) are governed by `ha/coordinator-patterns` and are deliberately not duplicated here; this spec covers the entry lifecycle only.

Quality scale marker: **Bronze** (`test-before-setup`), **Silver** (`config-entry-unloading`, `parallel-updates`).

## Goals

- Establish the config-entry setup entry point (`async_setup_entry`) as a binding contract: platform forwarding via `async_forward_entry_setups`, returning `True` on success
- Clearly distinguish the three setup-failure exceptions: `ConfigEntryNotReady` (temporary failure → retry with backoff), `ConfigEntryAuthFailed` (→ reauth), `ConfigEntryError` (permanent failure, no retry)
- Enforce complete teardown in `async_unload_entry`: unload platforms, unsubscribe listeners, close connections — no leftover state in `hass.data` or among listeners
- Establish `entry.async_on_unload(...)` as the standard mechanism for cleanup callbacks
- Set `PARALLEL_UPDATES` explicitly in every platform module, per the coordinator/non-coordinator distinction of the rule
- Make reload via `async_reload` (instead of a manual unload + setup) the standard path on options changes

## Non-Goals

- Coordinator-internal error mapping of periodic updates (`UpdateFailed`) — governed by `ha/coordinator-patterns`
- The config flow itself including the `async_step_reauth` implementation — governed by `ha/config-flow-patterns`; this spec only requires that `ConfigEntryAuthFailed` is raised correctly
- `async_setup_platform` / YAML-based setup and `PlatformNotReady` — legacy path; this spec covers config-entry-based setup only
- Config-entry migration (`async_migrate_entry`) and entry removal (`async_remove_entry`) — separate follow-up spec once a concrete need lands
- The structure of `runtime_data` itself — governed by `ha/runtime-data-pattern`; this spec only requires the correct assignment and teardown

## Requirements

### Setup entry point (`async_setup_entry`)

- **MUST** define `async_setup_entry(hass, entry)` in `__init__.py` and return `True` on successful setup
- **MUST** initialise the API client / device during setup and assign the result to `entry.runtime_data` **before** platforms are forwarded (see `ha/runtime-data-pattern`)
- **MUST** run the first refresh via `await coordinator.async_config_entry_first_refresh()` when using a `DataUpdateCoordinator` — that call raises the correct setup exceptions automatically (see `ha/coordinator-patterns`)
- **MUST NOT** return any value other than `True` on success — a wrong return value puts the entry into `setup error` instead of marking it `loaded`

### Setup failures & retry (`ConfigEntryNotReady`/`AuthFailed`/`Error`)

- **MUST** raise `homeassistant.exceptions.ConfigEntryNotReady` from `async_setup_entry` on temporary failures (device offline, network timeout, service unreachable) — HA then puts the entry into `setup retry` and retries the setup automatically with increasing backoff (`test-before-setup` rule)
- **MUST** raise `homeassistant.exceptions.ConfigEntryAuthFailed` on expired or invalid credentials (wrong password, invalid API key, expired token) — HA puts the entry into a failure state and starts the reauth flow (see `ha/config-flow-patterns`)
- **MUST** raise `homeassistant.exceptions.ConfigEntryError` on permanent failures where the integration is not expected to work in the foreseeable future (for example a closed account) — HA then does **not** retry the setup
- **MUST** raise the setup exceptions only from `async_setup_entry` in `__init__.py` (or from the `DataUpdateCoordinator`) — raised from a platform's `async_setup_entry`, `ConfigEntryNotReady` is ineffective because it is too late to be caught by the config-entry setup
- **MUST** preserve the originating exception as cause (`raise ConfigEntryNotReady("...") from ex`) — HA extracts the error message for UI and log from it
- **SHOULD** pass an error message as the first argument to the setup exception — HA logs `ConfigEntryNotReady` at `debug` level and shows the message on the integrations page
- **MUST NOT** emit own non-debug log messages about the retry — the logic built into `ConfigEntryNotReady` prevents log spam and is the authoritative place for it

### Platform forwarding

- **MUST** forward the setup to all platforms via `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)`, where `PLATFORMS` is the list of supported platform domains declared in `const.py`
- **MUST** call the forwarding only after `entry.runtime_data` has been assigned — the platform setups read `runtime_data` to create their entities
- **MUST** provide an `async_setup_entry(hass, config_entry, async_add_entities)` function in every platform module so the platform supports config entries at all

### Unload & cleanup (`async_unload_entry`)

- **MUST** implement `async_unload_entry(hass, entry)` — `entry.async_on_unload` alone is not enough; the function is mandatory for unload support (`config-entry-unloading` rule)
- **MUST** forward the unloading for every forwarded platform via `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` and return its result as the return value of `async_unload_entry`
- **MUST** clean up every resource created during setup when unloading: unsubscribe event listeners, close sessions / connections, release registered callbacks — per `config-entry-unloading`, no leftover state may remain after the unload
- **MUST NOT** leave leftover state in `hass.data` or among listeners — a leaking listener causes memory leaks after repeated reloads
- **SHOULD** couple cleanup steps that may only run on successful platform unload to the result of `async_unload_platforms` (`if unload_ok: ...`), and return exactly that `unload_ok`

### `entry.async_on_unload`

- **SHOULD** register cleanup callbacks via `entry.async_on_unload(<callback>)` instead of tracking the removal methods yourself — HA calls the registered callbacks automatically
- **MUST** account for `async_on_unload` callbacks running in two cases: when `async_setup_entry` raises `ConfigEntryError`, `ConfigEntryAuthFailed`, or `ConfigEntryNotReady`, **and** when `async_unload_entry` returns `True` successfully
- **MAY** bind state-change subscriptions to the entry lifecycle via `entry.async_on_unload(entry.async_on_state_change(<callback>))` so they are released automatically on unload

### `PARALLEL_UPDATES`

- **MUST** set the `PARALLEL_UPDATES` module constant explicitly in every platform module — the rule considers this good practice, and it limits the number of concurrent entity updates and action calls
- **MUST** set `PARALLEL_UPDATES = 0` for coordinator-based read-only platforms (`binary_sensor`, `sensor`, `device_tracker`, `event`) — per the rule the coordinator already centralises the data updates, so only action calls would remain relevant to limit
- **MUST** set `PARALLEL_UPDATES` to a positive integer without a coordinator (or for platforms with action calls) — `PARALLEL_UPDATES = 1` updates a platform's entities one after another (per the rule: "if there are more entities on the sensor platform, they will be updated one by one")
- **SHOULD** size the value by how many concurrent requests the device or service tolerates — some devices "don't like receiving a lot of requests at the same time"

### Reload

- **SHOULD** trigger the entry reload via `await hass.config_entries.async_reload(entry.entry_id)` instead of manually chaining unload and setup — `async_reload` runs the full unload/setup lifecycle including state transitions
- **SHOULD** register a reload on options changes (typically via an update listener bound to the lifecycle through `entry.async_on_unload`), so changed intervals / options take effect (see `ha/coordinator-patterns`, `ha/config-flow-patterns`)
- **MUST NOT** mutate the `ConfigEntry` (data or options) directly — changes run exclusively through `hass.config_entries.async_update_entry`

## Acceptance Criteria

- [ ] `async_setup_entry` is defined in `__init__.py` and returns `True` on success
- [ ] `entry.runtime_data` is assigned before platforms are forwarded
- [ ] Platforms are forwarded via `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)`
- [ ] Temporary setup failures raise `ConfigEntryNotReady`; expired credentials raise `ConfigEntryAuthFailed`; permanent failures raise `ConfigEntryError`
- [ ] Setup exceptions are chained with `from ex` and carry an error message as the first argument
- [ ] `async_unload_entry` is implemented and returns the result of `async_unload_platforms(entry, PLATFORMS)`
- [ ] `async_unload_entry` unsubscribes every listener and closes every connection opened during setup — no leftover state in `hass.data` or among listeners
- [ ] Cleanup callbacks are registered via `entry.async_on_unload(...)`
- [ ] Every platform module sets `PARALLEL_UPDATES` explicitly: `0` for coordinator-based read-only platforms, otherwise a positive integer
- [ ] Reloads run via `async_reload(entry.entry_id)`, not via a manual unload + setup
- [ ] Quality scale markers for this lifecycle are set: **Bronze** (`test-before-setup`), **Silver** (`config-entry-unloading`, `parallel-updates`)

## Open Questions

- **`ConfigEntryError`-vs.-`ConfigEntryNotReady` heuristic**: When does a failure count as "permanent" enough for `ConfigEntryError` instead of a retry via `ConfigEntryNotReady`? The HA docs give only examples (closed account); a sharp classification of API error classes is missing.
- **`PARALLEL_UPDATES` for mixed platforms**: How is the value set for a platform that provides both read-only entities and action calls (for example `switch` with a coordinator)? The rule addresses read-only platforms and action calls separately; the mixed case is unspecified.
- **Migration & removal**: This spec excludes `async_migrate_entry` and `async_remove_entry`. At what complexity does a dedicated `ha/entry-migration` spec become justified?
- **Reload debounce**: When several options changes occur in quick succession, each change can trigger a reload. Should the spec require a debounce of the reload listener?
- **Teardown verification in tests**: Should the spec require an explicit test that asserts, after `async_unload_entry`, that no listeners / `hass.data` entries remain (see `ha/test-harness`)?
