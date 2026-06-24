# HA Integration: Backup Platform

Status: draft

## Context

An integration can provide a **backup platform module** (`backup.py`) that covers two independent purposes. First, it can register a **backup agent** that uploads backups to a local or remote storage location. Second, it can hook into **pre/post operations** to pause integration activity or prepare data before a backup is created, and clean up after it finishes.

Both mechanisms live in the same platform module `backup.py` in the integration folder — analogous to `diagnostics.py`, `backup.py` is a convention-recognised platform module that HA loads automatically. Which of the two mechanisms (or both) is needed depends on the integration type: cloud-storage integrations provide agents, DB-writing or stateful integrations need pre/post hooks. This spec lifts the HA backup platform documentation into a generic obligation. Related specs: [`ha/integration-architecture`](../integration-architecture/en.md), [`ha/diagnostics`](../diagnostics/en.md) (sibling platform module), [`ha/security-hardening`](../security-hardening/en.md) (backup data may contain secrets).

## Goals

- Establish `backup.py` as the standard platform module for integrations that provide a storage location or must protect stateful operations
- Pin the `BackupAgent` contract (upload/download/list/delete) as a full implementation of the abstract base class
- Establish agent registration and the listener mechanism (`async_get_backup_agents`, `async_register_backup_agents_listener`) as a coupled pair, so stale agents are reliably removed and new ones added
- Mandate pre/post backup hooks for DB-writing and stateful integrations, so backups stay consistent and restorable

## Non-Goals

- Backup encryption, retention policy, and scheduling — owned by the backup manager, not the platform module
- Restore orchestration beyond the `BackupAgent` download — the actual restore flow lives in HA core
- The scaffold tool (`python3 -m script.scaffold backup`) itself — it is a convenience generator, not a contract part
- Frontend rendering of the upload-progress events — `UploadBackupEvent` processing lives outside the integration

## Requirements

### Purpose

- **MUST** place the backup platform module in `custom_components/<domain>/backup.py` once the integration provides a backup agent or hooks into pre/post operations
- **MUST** decide which of the two purposes is needed: a backup agent to upload backups to a local/remote storage location, and/or pre/post operations to pause or prepare integration activity around a backup
- **MAY** combine both purposes in the same `backup.py` module when the integration carries both a storage location and stateful operations

### Pre/post backup hooks (`backup.py`)

- **MUST** export `async_pre_backup(hass: HomeAssistant) -> None` in `backup.py` when the integration must pause operations or dump data before a backup so it can be restored properly
- **MUST** export `async_post_backup(hass: HomeAssistant) -> None`, which resumes the operations paused in `async_pre_backup` after the backup finishes
- **SHOULD** use the built-in scaffold template (`python3 -m script.scaffold backup`) to add support quickly, instead of creating the module manually

### Backup agent (storage location)

- **MUST** export `async_get_backup_agents(hass: HomeAssistant) -> list[BackupAgent]` in `backup.py` when the integration provides a storage location for backups
- **MUST** return an empty list when no loaded config entry exists for the domain (`hass.config_entries.async_loaded_entries(DOMAIN)`) — an agent without a loaded entry must not be offered
- **MUST** fully implement the abstract interface of the `BackupAgent` base class from `homeassistant.components.backup` and set `domain`, `name`, and `unique_id` as the agent identity

### Agent methods (upload/download/list/delete)

- **MUST** implement `async_upload_backup(*, open_stream, backup, on_progress, **kwargs) -> None`, which uploads the byte stream supplied via `open_stream` to the storage location
- **MUST** implement `async_download_backup(backup_id, **kwargs) -> AsyncIterator[bytes]`, which returns the backup file for the given `backup_id` as an async iterator over bytes
- **MUST** implement `async_list_backups(**kwargs) -> list[AgentBackup]` and `async_get_backup(backup_id, **kwargs) -> AgentBackup`, so the backup manager can list backups and query them individually
- **MUST** implement `async_delete_backup(backup_id, **kwargs) -> None`, which deletes the backup file for the given `backup_id` at the storage location
- **MUST** raise a `BackupAgentError` (or a subclass of it) on error — other exceptions should not leave the backup agent
- **MUST** raise `BackupNotFound` when the backup is missing in `async_download_backup`, `async_delete_backup`, and `async_get_backup`
- **SHOULD** call the `on_progress` callback periodically in `async_upload_backup` (for example after each sent chunk) with the total bytes uploaded so far (`on_progress(bytes_uploaded=bytes_sent)`), so the backup manager fires `UploadBackupEvent` events

### Registration & listener

- **MUST** export `async_register_backup_agents_listener(hass, *, listener, **kwargs) -> Callable[[], None]` as a `@callback`, which registers the listener and returns an unregister function
- **MUST** call the registered listener every time backup agents need to be reloaded — remove stale agents, add new ones
- **SHOULD** notify the listeners during `async_setup_entry` (for example via `entry.async_on_state_change`), so agent changes propagate on config-entry state changes

### When to implement

- **MUST** implement pre/post backup hooks when the integration must pause operations or dump data during a backup (typically DB-writing or otherwise stateful integrations), so the backup is consistent and restorable
- **MUST** implement a backup agent when the integration provides a storage location for backups (typically cloud-storage integrations)
- **MAY** omit the platform module when the integration neither provides a storage location nor must protect stateful operations around a backup

## Acceptance Criteria

- [ ] `custom_components/<domain>/backup.py` exists once the integration provides an agent or hooks into pre/post operations
- [ ] For pre/post operations, `async_pre_backup(hass)` and `async_post_backup(hass)` are exported as top-level async functions
- [ ] For a storage location, `async_get_backup_agents(hass)` and `async_register_backup_agents_listener(hass, *, listener)` are exported
- [ ] `async_get_backup_agents` returns `[]` when no loaded config entry exists for the domain
- [ ] The `BackupAgent` subclass sets `domain`, `name`, and `unique_id` and implements `async_upload_backup`, `async_download_backup`, `async_list_backups`, `async_get_backup`, and `async_delete_backup`
- [ ] Agent errors raise `BackupAgentError` (or a subclass); missing backups raise `BackupNotFound`
- [ ] `async_upload_backup` calls the `on_progress` callback during the upload
- [ ] The listener is notified during `async_setup_entry`, so agent changes propagate

## Open Questions

- **Hook-vs-agent separation**: The documentation carries both mechanisms in the same `backup.py`. Should the spec require an integration to weigh both deliberately against each other, or is the need-driven trigger enough?
- **Pre-backup pause duration**: How long may `async_pre_backup` pause operations before it blocks the backup window? The documentation states no upper bound.
- **Progress granularity**: "Periodically, for example after each chunk" is formulated as SHOULD; a concrete call frequency (for example every N bytes or N milliseconds) is not standardised.
- **Secret handling in the agent**: Backup data may contain secrets ([`ha/security-hardening`](../security-hardening/en.md)). Whether the agent must enforce server-side encryption is not covered by this documentation.
