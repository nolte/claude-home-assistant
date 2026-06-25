# Skill: `ha-backup-platform-add`

Status: draft

## Context

`ha/backup-platform` defines an integration's backup platform module `backup.py`, which covers two independent purposes. First, **pre/post backup hooks**: the top-level async functions `async_pre_backup(hass)` and `async_post_backup(hass)` that pause and resume integration activity around a backup — typical for DB-writing or otherwise stateful integrations, so the backup stays consistent and restorable. Second, **backup agents**: `async_get_backup_agents(hass)` returns `BackupAgent` subclasses that upload backups to a local/remote storage location — typical for cloud-storage integrations, coupled with `async_register_backup_agents_listener`. Analogous to `diagnostics.py`, `backup.py` is a convention-recognised platform module that HA loads automatically. No skill augments this so far.

This skill augments **one** of the two backup-platform surfaces (pre/post hooks or a backup agent) into an **existing** integration: the `backup.py` module with the matching exports — conformant to `ha/backup-platform`. Before generating it disambiguates with the user which of the two purposes (or both) fits the integration type.

## Scope

Augmenting exactly one backup surface per run (`hooks` or `agent`) into an existing `custom_components/<domain>/` integration: the platform module `backup.py`. For `hooks` the top-level functions `async_pre_backup(hass)` and `async_post_backup(hass)`. For `agent` the `async_get_backup_agents(hass)` function (with an empty list when no config entry is loaded), the `async_register_backup_agents_listener` `@callback`, and a `BackupAgent` subclass with the full upload/download/list/get/delete contract including `BackupAgentError`/`BackupNotFound` error handling. The skill reads `ha/backup-platform` and validates.

## Goals

- Pick the right surface (pre/post hooks vs. backup agent) from the described integration type and augment it spec-conformantly
- Enforce `async_pre_backup`/`async_post_backup` as top-level async functions for hooks, whose pausing in `async_pre_backup` is symmetrically resumed in `async_post_backup`
- Enforce the full `BackupAgent` contract for agents (upload/download/list/get/delete), set the agent identity (`domain`, `name`, `unique_id`), and offer agents only when a config entry is loaded
- Enforce the error semantics: `BackupAgentError` (or a subclass) leaves the agent, missing backups raise `BackupNotFound`
- Establish registration and the listener as a coupled pair, so stale agents are reliably removed and new ones added

## Non-Goals

- Backup encryption, retention policy, and scheduling — owned by the backup manager, not the platform module
- Restore orchestration beyond the `BackupAgent` download — the actual restore flow lives in HA core
- Frontend rendering of the upload-progress events (`UploadBackupEvent`) — lives outside the integration
- Greenfield scaffolding of an integration — `ha-integration-scaffold`
- The sibling platform module `diagnostics.py` — `ha/diagnostics`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add backup hooks", "make my integration backup-aware", "provide a backup agent"
  - "pause my integration before a backup / upload backups to my storage"
  - "füge Backup-Platform-Hooks hinzu", "mach meine Integration backup-fähig"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the integration type/need (prose), from which the skill derives the surface (hooks vs. agent)
- **MAY** capture: `surface` (`hooks`/`agent`), the agent `name`/`unique_id`, and the storage binding (local/remote) or the operations to pause

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** disambiguate the surface: stateful/DB-writing integration → pre/post hooks; storage-providing (cloud-storage) integration → backup agent; when both apply, let the user choose which surface this run augments
- **MUST** read the `ha/backup-platform` spec
- **MUST NOT** overwrite existing exports in `backup.py`; on collision abort

### Generation rules (per surface, from `ha/backup-platform`)

- **MUST** write the module to `custom_components/<domain>/backup.py`; **SHOULD** mention the built-in scaffold template (`python3 -m script.scaffold backup`) as a quick start instead of mandatorily starting by hand
- **MUST** for hooks export `async_pre_backup(hass: HomeAssistant) -> None` and `async_post_backup(hass: HomeAssistant) -> None` as top-level async functions; `async_post_backup` resumes the operations paused in `async_pre_backup`
- **MUST** for an agent export `async_get_backup_agents(hass: HomeAssistant) -> list[BackupAgent]` and return an empty list when no loaded config entry exists for the domain (`hass.config_entries.async_loaded_entries(DOMAIN)`)
- **MUST** for an agent fully implement the `BackupAgent` base class from `homeassistant.components.backup`, set `domain`/`name`/`unique_id`, and implement `async_upload_backup`, `async_download_backup`, `async_list_backups`, `async_get_backup`, and `async_delete_backup`
- **MUST** for an agent export `async_register_backup_agents_listener(hass, *, listener, **kwargs) -> Callable[[], None]` as a `@callback` that registers the listener, returns an unregister function, and is called on a needed reload; **SHOULD** notify the listeners during `async_setup_entry`
- **MUST** for an agent raise `BackupAgentError` (or a subclass) on error and raise `BackupNotFound` when the backup is missing in `async_download_backup`/`async_delete_backup`/`async_get_backup`
- **SHOULD** call the `on_progress` callback periodically in `async_upload_backup` (for example after each chunk) with the total bytes uploaded so far (`on_progress(bytes_uploaded=bytes_sent)`)
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: `backup.py` exists; for hooks `async_pre_backup(hass)` and `async_post_backup(hass)` are exported as top-level async functions; for an agent `async_get_backup_agents(hass)` and `async_register_backup_agents_listener(hass, *, listener)` are exported, `async_get_backup_agents` returns `[]` when no config entry is loaded, the `BackupAgent` subclass sets `domain`/`name`/`unique_id` and implements the five agent methods, errors raise `BackupAgentError`/`BackupNotFound`
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/backup-platform`, plus the changed file paths and the chosen surface

### Prohibitions

- **MUST NOT** augment more than one surface per run
- **MUST NOT** implement encryption, retention, scheduling, or restore orchestration — those belong to the backup manager or the core
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill derives the surface (or asks) and disambiguates hooks vs. agent by integration type
- [ ] `custom_components/<domain>/backup.py` exists after the run
- [ ] For hooks, `async_pre_backup(hass)` and `async_post_backup(hass)` are exported as top-level async functions (symmetric pause/resume)
- [ ] For an agent, `async_get_backup_agents(hass)` and `async_register_backup_agents_listener(hass, *, listener)` are exported; `async_get_backup_agents` returns `[]` when no config entry is loaded
- [ ] The `BackupAgent` subclass sets `domain`/`name`/`unique_id` and implements `async_upload_backup`/`async_download_backup`/`async_list_backups`/`async_get_backup`/`async_delete_backup`
- [ ] Errors raise `BackupAgentError` (or a subclass); missing backups raise `BackupNotFound`
- [ ] Report names the file paths and the chosen surface

## Open questions

- **Hook-vs-agent separation**: The documentation carries both mechanisms in the same `backup.py`. Should the skill require an integration to weigh both deliberately, or is the need-driven trigger enough? Currently it augments exactly one surface per run.
- **Scaffold template**: Should the skill mandatorily call `python3 -m script.scaffold backup`, or write the module itself? Currently it mentions the template as a SHOULD and generates offline.
- **Progress granularity**: "Periodically, for example after each chunk" is formulated as SHOULD; a concrete call frequency is not standardised — the skill follows the doc pattern and asks when in doubt.
