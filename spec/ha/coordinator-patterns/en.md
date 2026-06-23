# HA Integration: Coordinator Patterns

Status: draft

## Context

`homeassistant.helpers.update_coordinator.DataUpdateCoordinator` is HA's established pattern for bundling asynchronous polling of an API endpoint or device into a shared update loop. A Custom Integration with non-trivial data does not typically need a single mega-coordinator that polls everything every tick, but a **multi-coordinator topology**: one coordinator per logical data set with its own update interval, so fast data (alerts, status) is not stuck behind slow data (inventory, master data).

`nolte/kamerplanter-ha` validates this pattern with five coordinators (plants, locations, runs, alerts, tasks) — four with `300 s` default and `120 s` minimum interval, one (alerts) with `60 s` default and `30 s` minimum — and consistently maps API auth errors to `ConfigEntryAuthFailed`, connection errors to `UpdateFailed`. This spec lifts that convention into a generic obligation for every Custom Integration that skills in this plugin scaffold.

Quality scale marker: **Silver** (`DataUpdateCoordinator` usage with correct error mapping is a Silver requirement per the HA quality scale; the multi-coordinator topology is not a separate quality-scale criterion, but in practice elevates the pattern beyond plain Silver conformance).

## Goals

- Establish the multi-coordinator topology as the binding style for integrations with mixed update frequencies
- Enforce correct error mapping: API auth errors → `ConfigEntryAuthFailed` (triggers reauth flow); connection errors → `UpdateFailed` (marks entities `unavailable` without breaking the entry)
- Make configurable polling intervals per coordinator the default, with an enforced minimum cap that prevents server DDoS through misconfiguration
- Use `always_update=False` as the default — entities trigger updates only on actual data change
- Run a one-time master-data setup via `_async_setup()` separate from periodic updates
- Use a per-coordinator timeout (`async_timeout.timeout(...)`) so a hanging API call does not block the whole entry

## Non-Goals

- Push-based updates (WebSocket, MQTT, HTTP webhook into HA) — separate follow-up spec once a concrete need lands
- Cross-coordinator data aggregation — currently solved as ad-hoc helper functions inside the platform modules; separate spec if a robust pattern emerges
- Persistent caches of coordinator data across HA restarts — `homeassistant.helpers.storage` is the right place for that
- Throttling / rate-limiting beyond the update intervals — that belongs to `ha/security-hardening`, which defines API-client behaviour

## Requirements

### Coordinator topology

- **MUST** define a dedicated coordinator per logical data set instead of a single mega-coordinator that polls everything every tick
- **MUST** carry every coordinator in `RuntimeData` under named string keys (see `ha/runtime-data-pattern`); each key matches the functional role (`"plants"`, `"alerts"`, …)
- **SHOULD** make update intervals per coordinator configurable through the options flow (see `ha/config-flow-patterns`); the configuration triggers an entry reload that re-creates the coordinators with the new intervals
- **MAY** keep a coordinator that runs multiple API calls in parallel for tightly coupled endpoints (for example a coordinator that polls two endpoints per tick because their data only makes sense together in the platforms), as long as that is documented in the coordinator's `name` property
- **MUST NOT** split the same functional data set across multiple coordinators — exactly one coordinator per data set

### Coordinator definition

- **MUST** subclass `DataUpdateCoordinator` (or `TimestampDataUpdateCoordinator` where appropriate)
- **MUST** annotate the data type generically: `class <Domain><Role>Coordinator(DataUpdateCoordinator[<DataType>])` — `<DataType>` is the concrete type returned by `_async_update_data`
- **MUST** pass `config_entry=entry` to `super().__init__()` — HA requires this parameter for ConfigEntry lifecycle binding
- **MUST** set `name=f"{DOMAIN}_<role>"` — the name appears in HA logs and distinguishes the coordinators of a single entry
- **MUST** set `update_interval=timedelta(seconds=<interval>)`, where `<interval>` is derived from `entry.options` (with default and minimum cap, see next section)
- **SHOULD** set `always_update=False` — coordinator listeners (i.e. every entity) then trigger `_handle_coordinator_update` only when data has actually changed since the previous tick; that saves a pointless re-render per tick and entity
- **MAY** specify `update_method=<async-callable>` as an alternative to overriding `_async_update_data` — both paths are equivalent

### Default and minimum intervals

- **MUST** define default and minimum intervals in `const.py` — typically as `DEFAULT_POLL_<ROLE>` and `MIN_POLL_<ROLE>` in seconds
- **MUST** enforce the minimum cap in the coordinator constructor (`max(MIN_POLL_<ROLE>, entry.options.get(CONF_POLL_<ROLE>, DEFAULT_POLL_<ROLE>))`); buggy or hostile options values must never flood the API with sub-second polling
- **SHOULD** make the load implication of materially shorter intervals (for example alerts at `60 s`) visible in the spec doc or a code comment, so the interval is not accidentally copied to other coordinators

### Master-data setup

- **MAY** override `_async_setup()` as an async method without parameters to load master data once on first refresh (for example a lookup table for foreign-key resolution)
- **MUST** keep `_async_setup()` idempotent — HA does guarantee single invocation within an entry lifecycle, but a re-setup after reload is to be expected
- **MAY** store lookup caches as instance attributes on the coordinator (for example `self._fertilizer_lookup`); these are then used in `_async_update_data` for data enrichment
- **MUST NOT** reload master data in every `_async_update_data` iteration when it is not refreshable — that pushes slow I/O into the polling path

### Update method

- **MUST** override `_async_update_data()` as an async method without parameters (or supply an equivalent `update_method`)
- **MUST** wrap the API call in an explicit timeout (`async with async_timeout.timeout(<seconds>): ...`) — typical value `30 s`; the timeout must not exceed the update interval
- **MUST** avoid generic exception catches — only catch the API-specific exception classes and map them onto HA exceptions (see next section); every other error propagates upwards
- **MUST NOT** switch the data type between iterations — the generic parameter is a contract declaration to the platforms

### Error mapping

- **MUST** map API-specific auth exceptions (HTTP 401 / 403, expired token, invalid API key) to `homeassistant.exceptions.ConfigEntryAuthFailed` — HA then triggers the `async_step_reauth` flow (see `ha/config-flow-patterns`)
- **MUST** map API-specific connection failures (network timeout, HTTP 5xx, DNS error) to `homeassistant.helpers.update_coordinator.UpdateFailed` — HA then marks the associated entities `unavailable` while keeping the entry alive
- **MUST** preserve the original exception as cause: `raise ConfigEntryAuthFailed(str(err)) from err` or `raise UpdateFailed(str(err)) from err` — otherwise the stack trace gets lost in the HA log
- **MAY** use more specific HA exceptions when the situation requires it (for example `ConfigEntryNotReady` when the initial setup fails due to a transient connection error) — the coordinator constructor can carry its own try/except outside `_async_update_data` for that

### Enrichment failures

- **MAY** perform per-item enrichment in `_async_update_data` (for example lookup resolution for foreign keys)
- **MUST** not abort the entire update on a single enrichment failure; leave the affected entry with the original value (or `None`), log the error
- **SHOULD** surface enrichment failures in diagnostics (see `ha/diagnostics`) so they don't require log-tail sleuthing
- **MUST NOT** silently swallow enrichment failures — every logged error carries enough context (`entry_id`, coordinator role, affected entry key) to make it locatable

### First refresh

- **MUST** call `await coordinator.async_config_entry_first_refresh()` for every coordinator inside `async_setup_entry` **before** `entry.runtime_data` is assigned (see `ha/runtime-data-pattern`)
- **MUST** parallelise first refreshes sequentially or with `asyncio.gather(...)`, depending on API tolerance; `gather` is allowed when the backend handles concurrent calls
- **MUST NOT** call `coordinator.async_refresh()` directly during setup — `async_config_entry_first_refresh` carries the right error handling for the setup stage

## Acceptance Criteria

- [ ] Exactly one coordinator per logical data set; no mega-coordinator
- [ ] Every coordinator is referenced in `RuntimeData` under a named key
- [ ] Every coordinator class subclasses `DataUpdateCoordinator[<DataType>]` with an explicit generic parameter
- [ ] `super().__init__(...)` includes `config_entry`, `name`, `update_interval`, `always_update=False`
- [ ] Default and minimum intervals exist in `const.py` as `DEFAULT_POLL_<ROLE>` and `MIN_POLL_<ROLE>`
- [ ] The minimum cap is enforced in the constructor via `max(min, requested)`
- [ ] `_async_update_data` is wrapped in `async with async_timeout.timeout(<seconds>)`
- [ ] `_async_update_data` raises `ConfigEntryAuthFailed` for auth errors and `UpdateFailed` for connection errors — both chained with `from err`
- [ ] `_async_update_data` contains no generic `except Exception:` catch
- [ ] `async_setup_entry` calls `async_config_entry_first_refresh()` for every coordinator before `runtime_data`
- [ ] Quality scale marker for this pattern is set: **Silver**

## Open Questions

- **Coordinator consolidation heuristic**: When is a multi-coordinator setup better than a mega-coordinator? Currently the multi-coordinator style is required as soon as multiple logical data sets exist — a measurable heuristic (number of endpoints, data volume, update frequency spread) is missing.
- **Push coordinator**: How does the spec handle push-based updates (webhook, MQTT, WebSocket)? Separate `ha/coordinator-push` spec once the first push-capable integration shows up.
- **First-refresh stagger**: When every coordinator of an entry starts its first refresh simultaneously, the backend may serialise or rate-limit. Should the spec require a staggered first refresh (for example with small `asyncio.sleep` offsets)?
- **Per-role timeout**: Should `async_timeout.timeout(...)` be configurable per coordinator role (for example a longer timeout for master-data coordinators), or does the global `30 s` default suffice?
- **`TimestampDataUpdateCoordinator` threshold**: When does the spec require the timestamp variant instead of the base class? `kamerplanter-ha` uses the base; a concrete use case for the timestamp variant has not yet appeared in the repo.
