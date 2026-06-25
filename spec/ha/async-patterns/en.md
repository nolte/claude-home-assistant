# HA Integration: Async Patterns

Status: draft

## Context

The HA core has run on Python's `asyncio` module since `0.29`: access to the non-thread-safe core API objects (for example the state of entities) is limited to a single thread — the *event loop*. All components schedule themselves as a task on the event loop, which guarantees that only a single task runs at a time and no locks are needed. The only problem with this model is when a task does blocking I/O: while the event loop is blocked, nothing else can run, and the entire system stalls for the duration of the blocking operation.

HA's sources phrase this as two hard invariants: no blocking I/O in the event loop (see `asyncio_blocking_operations.md`) and no non-thread-safe calls to core APIs from a foreign thread (see `asyncio_thread_safety.md`). Beginning in `2024.5.0`, HA detects and blocks some non-thread-safe operations; beginning in `2024.7.0`, HA detects additional blocking calls in the event loop — violations that previously led to instability or undefined behaviour are now actively reported. This spec lifts the HA async conventions (`async_` naming, `@callback` semantics, executor offloading, thread safety, function categorization, blocking imports) into a binding obligation for every Custom Integration that skills in this plugin scaffold.

Quality scale marker: **Platinum** (`async-dependency` requires fully asynchronous dependencies with no blocking I/O in the event loop; `strict-typing` requires consistent type annotation of the async/callback signatures). The rules in this spec are also part of HA's general code-review standards and apply regardless of the targeted quality-scale tier.

## Goals

- Keep the event loop strictly free of blocking I/O — blocking operations run either in the executor or via async libraries
- Enforce the HA naming convention: `async_` prefix for anything that must run from the event loop; `@callback` for non-blocking functions that run in the loop
- Enforce thread safety: calls to loop-only core APIs from a foreign thread go exclusively through the documented thread-safe bridges
- Categorize every function (coroutine, callback, thread- and loop-safe, other) and honour its constraints
- Move blocking or heavy imports outside the module level into the executor, or load them through the thread-safe import helpers
- Surface async errors early — enable `asyncio` debug mode and HA's debug mode during development

## Non-Goals

- Coordinator-specific async mechanics (`_async_update_data`, `async_config_entry_first_refresh`, error mapping) — belongs to `ha/coordinator-patterns`; this spec only covers the generic async rules underneath
- Selection of concrete async libraries (`aiohttp` vs. `httpx`) per integration — falls under `ha/integration-architecture` and the API-client definition in `ha/security-hardening`
- Migration of existing synchronous integrations to async — separate follow-up spec once a concrete migration case lands
- Performance tuning of the event loop beyond the never-block rule (profiling, task prioritization) — not currently covered

## Requirements

### Never block the event loop

- **MUST** ensure that no blocking operation runs in the event loop — per HA, the entire system stalls for the duration of the blocking operation
- **MUST** treat the blocking operations listed in `asyncio_blocking_operations.md` as blocking: `open` (blocking disk I/O), `sleep` (blocking instead of `await asyncio.sleep`), `putrequest`/`urllib` (blocking network I/O), `glob.glob`, `glob.iglob`, `os.walk`, `os.listdir`, `os.scandir`, `os.stat`, `pathlib.Path.write_bytes`/`write_text`/`read_bytes`/`read_text`, and `SSLContext.load_default_certs`/`load_verify_locations`/`load_cert_chain`/`set_default_verify_paths`
- **MUST** replace a blocking `time.sleep` with `await asyncio.sleep(...)` and switch blocking HTTP (`urllib`) to `aiohttp` or `httpx` rather than wrapping it in the executor when an async alternative exists
- **MUST** also move all associated blocking reads and writes into the executor when fixing an `open` call in the event loop — HA only detects the `open`, not the downstream I/O calls
- **SHOULD** enable `asyncio` debug mode and HA's built-in debug mode during development, since many blocking-I/O and thread-safety errors are then detected automatically
- **MUST NOT** perform I/O in entity properties — properties are read from the event loop; all data is fetched in the update method and cached on the entity

### Executor offloading

- **MUST** move blocking code inside HA into the executor via `await hass.async_add_executor_job(blocking_code, arg)`
- **MUST** use `await loop.run_in_executor(None, blocking_code, arg)` with `loop = asyncio.get_running_loop()` in library code (outside HA)
- **SHOULD** bind keyword arguments via `functools.partial` (`hass.async_add_executor_job(partial(blocking_code_with_kwargs, kwarg=True))`), since `async_add_executor_job` only forwards positional arguments
- **MAY** use the blocking-safe helpers for SSL-context creation — `homeassistant.helpers.aiohttp_client.async_get_clientsession` (aiohttp), `homeassistant.helpers.httpx_client.get_async_client` (httpx), or `homeassistant.util.ssl` for generic SSL — which already perform the blocking I/O in the executor
- **MUST NOT** call `async_add_executor_job` from a function that is itself blocked from a thread via `run_coroutine_threadsafe`/`asyncio.run_coroutine_threadsafe` — per HA, this combination can lead to a deadlock

### Callback vs. coroutine convention (`@callback`)

- **MUST** name every function that must run from the event loop with the `async_` prefix — HA uses this convention to mark loop-required functions
- **MUST** declare a coroutine via `async def` and `await` its loop-required dependencies; invoking a coroutine function only returns a not-yet-started object that executes only when awaited or scheduled on the event loop
- **MUST** decorate a non-blocking, loop-running function with `@callback` from `homeassistant.core` — a callback cannot suspend itself and therefore must not do I/O and must not call or `await` a coroutine (it may at most schedule a new task without waiting for its result)
- **MUST NOT** declare a function both as a coroutine (`async def`) and with `@callback` — `@callback` explicitly marks a normal, non-suspendable function
- **SHOULD** choose a callback over a coroutine when no suspension is needed — per HA, this saves a loop pass (the loop then runs only `A` instead of `A`, `B`, `A`) and improves the state consistency of the core API objects
- **MUST** decorate the handler of a built-in helper callback (for example `async_track_state_change_event`) with `@callback` when it should run in the event loop — without the decorator the handler runs in the executor and makes a non-thread-safe call to `async_write_ha_state`

### Thread safety

- **MUST** account for the fact that nearly all `asyncio` objects are not thread-safe and never call loop-only core APIs directly from a foreign thread
- **MUST** use the non-`async` variant of a core API where HA offers one when calling from a foreign thread — verbatim from `asyncio_thread_safety.md`: instead of `hass.async_create_task` → `hass.create_task`; instead of `hass.bus.async_fire` → `hass.bus.fire`; instead of `hass.services.async_register` → `hass.services.register`; instead of `hass.services.async_remove` → `hass.services.remove`; instead of `async_write_ha_state` → `self.schedule_update_ha_state`; instead of `async_dispatcher_send` → `dispatcher_send`
- **MUST** use `hass.add_job` to schedule a function in the event loop that calls the `async_` API for loop-only APIs without a sync variant (`hass.config_entries.async_update_entry`, `async_render_to_info`, and all `area_registry`, `category_registry`, `device_registry`, `entity_registry`, `floor_registry`, `issue_registry`, and `label_registry` mutations) — or the documented sync helpers `issue_registry.create_issue` / `issue_registry.delete_issue`
- **MUST** use `asyncio.run_coroutine_threadsafe(coro, hass.loop).result()` (or the equivalent `run_callback_threadsafe`/`hass.loop.call_soon_threadsafe` path) to schedule the coroutine thread-safely on the loop when calling an async-only function from a thread
- **MUST NOT** call `hass.config_entries.async_update_entry`, `async_render_to_info`, or a registry mutation directly from a foreign thread — these operations must run in the event loop thread, otherwise they corrupt the internal `asyncio` state

### Function categorization

- **MUST** assign every function to one of the four HA categories from `asyncio_categorizing_functions.md`: coroutine (`async def`, loop-required, `async_` prefix), callback (`@callback`, in the loop, non-blocking), event-loop- and thread-safe (pure in-memory computation/transform, no I/O), or other (uses `sleep` or I/O and is not loop-safe)
- **MUST** treat a function as event-loop- and thread-safe only when it does no I/O — per HA, anything that does I/O explicitly does not fall into this category
- **SHOULD** inspect the implementation of a called function when in doubt before using it from the event loop — there is no annotation for the thread- and loop-safe category, so the classification is the caller's responsibility
- **MUST** call functions in the "other" category (with `sleep` or I/O) from the event loop through the executor rather than directly

### Blocking imports

- **SHOULD** keep imports at module level (top-level) in `__init__.py` — HA then loads the integration either before the event loop starts or in the import executor, so the imports are safe
- **MUST** consider each import outside the module level individually, since the import machinery does blocking disk I/O when loading the module and CPython imports are not thread-safe
- **MUST** move a conditional late import that happens in a single place into the executor (`hass.async_add_executor_job(_function_that_does_late_import)` inside HA, or `loop.run_in_executor(None, _function_that_does_late_import)` outside)
- **MAY** use the thread-safe helper `homeassistant.helpers.importlib.import_module` or `async_import_module` for potentially concurrent imports from multiple paths
- **SHOULD** put imports needed only for type checking into an `if TYPE_CHECKING:` block so they are not loaded at runtime
- **SHOULD** not import rarely used, CPU- and I/O-intensive code at module level, but defer the import so resources are only used when needed

## Acceptance Criteria

- [ ] No blocking I/O (file, network, `sleep`, `requests`/`urllib`) runs in the event loop; each operation listed in `asyncio_blocking_operations.md` is either moved into the executor or replaced by an async alternative
- [ ] Blocking code is offloaded via `hass.async_add_executor_job(...)` (inside HA) or `loop.run_in_executor(None, ...)` (library code); keyword arguments are bound via `functools.partial`
- [ ] Every loop-required function carries the `async_` prefix; coroutines are `async def`, non-blocking loop functions are decorated with `@callback`
- [ ] No function is both `async def` and decorated with `@callback`; no `@callback` handler does I/O or `await`s a coroutine
- [ ] Built-in helper handlers (for example for `async_track_state_change_event`) are decorated with `@callback`
- [ ] Calls to core APIs from a foreign thread go through the documented sync variant, `hass.add_job`, or `asyncio.run_coroutine_threadsafe(...).result()` — no direct call to `async_write_ha_state`, `async_update_entry`, `async_render_to_info`, or a registry mutation from a thread
- [ ] Every function is unambiguously assignable to one of the four HA categories (coroutine / callback / loop- and thread-safe / other)
- [ ] Imports are at module level in `__init__.py` or moved as conditional late imports into the executor or the thread-safe import helper
- [ ] Pure type-checking imports sit in an `if TYPE_CHECKING:` block
- [ ] Quality scale marker for this pattern is set: **Platinum** (`async-dependency`, `strict-typing`)

## Open Questions

- **Executor-vs.-async heuristic**: When is executor offloading acceptable and when is migration to an async library mandatory? The spec currently requires the async alternative "when it exists" — a measurable threshold (call frequency, latency, thread-pool pressure) is missing.
- **Executor pool saturation**: Many parallel `async_add_executor_job` calls can saturate the default thread pool. Should the spec require a limit or a dedicated executor for I/O-heavy integrations?
- **Debug mode in CI**: Should the spec enforce `asyncio` debug mode and HA's debug mode in the test harness (see `ha/test-harness`) as well, so blocking-I/O and thread-safety errors surface in CI rather than only at runtime?
- **`async_import_module` threshold**: At what point does the spec require the thread-safe import helper instead of a plain executor late import? The HA docs distinguish by "possibly concurrent from multiple paths" — a concrete criterion in the repo context is missing.
- **`run_callback_threadsafe`-vs.-`hass.add_job` delimitation**: When is `hass.loop.call_soon_threadsafe`/`run_callback_threadsafe` the right path and when is `hass.add_job`? The HA docs predominantly mention `hass.add_job`; a decision rule for the low-level variants is missing.
