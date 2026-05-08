# HA Integration: `runtime_data` Pattern

Status: draft

## Context

Before Home Assistant 2024.1, `hass.data[DOMAIN][entry.entry_id]` was the established storage slot where a Custom Integration parked its API client, its `DataUpdateCoordinator`s, and its cleanup listeners for the lifetime of a `ConfigEntry`. That pattern has three hard weaknesses: it is untyped (every lookup is a dynamic dict-get with `cast` theatre), it requires manual `pop()` cleanup in `async_unload_entry`, and platform modules must mirror the same lookup path or drift between setup and consumption emerges.

HA 2024.1 introduced `entry.runtime_data` for exactly this — a typed slot directly on `ConfigEntry` that delivers type safety via a generic type parameter (`ConfigEntry[YourRuntimeData]`) and is automatically discarded on entry unload. The nolte convention (validated in `nolte/kamerplanter-ha`, codified there as _Runtime Data Pattern (MANDATORY)_) requires this slot exclusively; any access to `hass.data[DOMAIN]` for setup artefacts is forbidden. This spec makes that requirement binding for every skill in `claude-home-assistant` that scaffolds Custom Integrations.

Quality scale marker: **Bronze** (typed `runtime_data` is a Bronze requirement per the HA quality scale).

## Goals

- Establish typed `runtime_data` as the sole storage slot for setup artefacts (API clients, coordinators, cleanup listeners)
- Eliminate drift between setup storage and platform lookup — both see the same typed slot
- Use automatic cleanup on entry unload instead of carrying manual `hass.data.pop()` logic
- Make skill output Bronze-quality-scale-conformant from the start, without a follow-up refactor step

## Non-Goals

- Multi-entry sharing (one API client across multiple entries against the same server) — separate follow-up spec if the need emerges
- Persistent storage across HA restarts — `runtime_data` is explicitly non-persistent; that is the job of the `homeassistant.helpers.storage` helpers
- Migration of existing `hass.data[DOMAIN]` integrations — skills in this plugin scaffold greenfield code; a migration spec materialises only when a concrete consumer asks
- Schema migration between versions of `entry.data` / `entry.options` — owned by `async_migrate_entry`, not by this spec

## Requirements

### `RuntimeData` dataclass

- **MUST** define exactly one `RuntimeData` dataclass per integration, typically in `__init__.py` or a dedicated `runtime.py` module
- **MUST** decorate the class with `@dataclass` (not `@dataclass(frozen=True)`, because listener refs may be added later)
- **MUST** carry every setup artefact as a typed field: API client, every `DataUpdateCoordinator` instance, cleanup callback refs, cache structures
- **SHOULD** carry coordinators as a typed mapping (`dict[str, DataUpdateCoordinator[Any]]`) when the integration has more than one coordinator — the key matches the coordinator role (see `ha/coordinator-patterns` for the topology)
- **MAY** carry additional fields (for example a pre-resolved lookup cache like `_fertilizer_lookup` in `nolte/kamerplanter-ha`), as long as they are deterministically derivable from the setup

### Typed `ConfigEntry` alias

- **MUST** export a type alias of the form `type <Domain>ConfigEntry = ConfigEntry[<Domain>RuntimeData]` — `<Domain>` in PascalCase
- **MUST** use this alias in the signature of every lifecycle function (`async_setup_entry`, `async_unload_entry`, `async_migrate_entry`) and every platform `async_setup_entry`
- **SHOULD** export the alias and the `RuntimeData` dataclass from the same module so platform modules can use a single import path

### `async_setup_entry` filling

- **MUST** assign `entry.runtime_data` with the fully populated `RuntimeData` instance **before** `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)` is called — platforms read `runtime_data` during their own setup
- **MUST** create the API client and every coordinator before the `runtime_data` assignment
- **SHOULD** call `await coordinator.async_config_entry_first_refresh()` for every coordinator before the `runtime_data` assignment, so platforms start with populated data and entities don't have to be registered as `unavailable` first
- **MUST NOT** half-fill `runtime_data` if `async_setup_entry` raises — either the full assignment happens or none; partial state is forbidden

### `async_unload_entry` cleanup

- **MUST NOT** contain `hass.data[DOMAIN].pop(entry.entry_id, None)` logic — `runtime_data` is automatically discarded by HA on unload
- **SHOULD** run cleanup callbacks (listeners, subscription cancellations) that are not registered via `entry.async_on_unload(...)` before the platform unload — typically by storing the callback refs in `runtime_data` and invoking them in `async_unload_entry`
- **SHOULD** prefer `entry.async_on_unload(callback)` during setup for listeners — HA then invokes the callbacks automatically on unload without `RuntimeData` having to carry them
- **MUST** return `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` from `async_unload_entry` (see `ha/integration-architecture`)

### Platform lookup

- **MUST** read `runtime_data` exclusively via `entry.runtime_data` in every platform module (`sensor.py`, `binary_sensor.py`, …), never via `hass.data[DOMAIN]`
- **MUST** annotate the `entry` parameter of each platform `async_setup_entry` with the typed alias: `entry: <Domain>ConfigEntry`
- **SHOULD** look up coordinators via the mapping (`entry.runtime_data.coordinators["<role>"]`) instead of via per-coordinator fields — that keeps the `RuntimeData` dataclass stable when the coordinator count changes

### Forbidden patterns

- **MUST NOT** use `hass.data[DOMAIN][entry.entry_id]` as the storage location for API clients, coordinators, or cleanup listeners
- **MUST NOT** use `hass.data` as a cache for the setup artefacts of a single integration — the only acceptable reason is cross-integration sharing, which is a separate open question (see Open Questions)
- **MUST NOT** abuse `runtime_data` as configuration storage — `entry.data` and `entry.options` remain the configuration sources; `runtime_data` is the cross-flow storage for **derived** setup artefacts
- **MUST NOT** mutate `runtime_data` in place to mirror configuration updates — config updates trigger `async_unload_entry` + `async_setup_entry` reload (or explicit `entry.async_reload()`); incremental in-place mutation is not the intended path

## Acceptance Criteria

- [ ] A `@dataclass` named `<Domain>RuntimeData` is exported in code and carries every setup artefact as a typed field
- [ ] A type alias `<Domain>ConfigEntry = ConfigEntry[<Domain>RuntimeData]` is exported
- [ ] `async_setup_entry`, `async_unload_entry`, and (when present) `async_migrate_entry` use the typed alias in the signature
- [ ] `async_setup_entry` sets `entry.runtime_data` before `async_forward_entry_setups`
- [ ] `async_setup_entry` calls `async_config_entry_first_refresh()` for every coordinator before the `runtime_data` assignment
- [ ] `async_unload_entry` contains no `hass.data.pop()` call
- [ ] Every platform module uses `entry.runtime_data` for coordinator / API lookups; no platform module references `hass.data[DOMAIN]`
- [ ] A `grep` for `hass.data[DOMAIN]` inside `custom_components/<domain>/` returns no hits (migration paths excepted)
- [ ] Quality scale marker for this pattern is set: **Bronze**

## Open Questions

- **Multi-entry sharing**: How do we handle two config entries that target the same server / cloud and want to share an API client? `runtime_data` is per-entry; the sharing mechanism would have to fall back on `hass.data` or introduce an external singleton. Separate spec once the need is concrete.
- **Cleanup-listener style**: `entry.async_on_unload(...)` (HA-managed) vs. callback refs in `RuntimeData` (self-managed) — when does the spec prescribe which style? Currently formulated as a SHOULD for `async_on_unload`; for patterns with complex cleanup logic (for example a WebSocket with backoff reconnect) self-managed may be more appropriate.
- **`RuntimeData` mutation**: Is it acceptable to extend `runtime_data` with new fields at runtime (for example an on-demand registered service listener)? Currently formulated as "do not mutate in place"; a definitive style decision waits for the first concrete use case.
- **`@dataclass(slots=True)`**: Should `RuntimeData` be declared with `slots=True`? Saves memory per entry, but prevents dynamic attribute extension — which the mutation question above already disallows.
