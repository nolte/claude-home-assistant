---
name: ha-backup-platform-add
description: Augment an existing Home Assistant Custom Integration with one backup-platform surface — either pre/post backup hooks or a backup agent — conforming to spec/ha/backup-platform. For hooks it generates custom_components/<domain>/backup.py with the top-level async functions async_pre_backup(hass) and async_post_backup(hass) that symmetrically pause and resume stateful operations around a backup. For an agent it generates async_get_backup_agents(hass) (empty list when no config entry is loaded), the async_register_backup_agents_listener @callback, and a BackupAgent subclass setting domain/name/unique_id and implementing the full upload/download/list/get/delete contract with BackupAgentError/BackupNotFound error handling. Disambiguates hooks-vs-agent by integration type before generating. Activate on "add backup hooks", "make my integration backup-aware", "provide a backup agent", "füge Backup-Platform-Hooks hinzu". Do not activate for greenfield scaffolding (ha-integration-scaffold), the sibling diagnostics module (ha/diagnostics), encryption/retention/restore orchestration (owned by the backup manager), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, backup]
---

# HA Backup Platform Add

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-backup-platform-add/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-backup-platform-add/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes the integration type and reads back the `backup.py` module and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-repairs-add`, `ha-device-automation-add`).
- **Mid-flow interactivity** — the hooks-vs-agent disambiguation is a per-run dialogue the user approves before generation.
- **Bounded, inline generation** — one platform module (the two hook functions, or the agent class plus its registration) fits inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the surface decision belongs in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one** backup-platform surface — pre/post backup hooks (for DB-writing or stateful integrations) or a backup agent (for storage-providing integrations) — to an existing integration via its `backup.py` platform module.

## When NOT to activate

- greenfield integration scaffolding → `ha-integration-scaffold`
- the sibling diagnostics platform module → `ha/diagnostics`
- backup encryption, retention, scheduling, or restore orchestration → owned by the backup manager / HA core, out of scope
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **One surface, one run.** Either pre/post hooks or a backup agent — no combined batch.
2. **Read [`ha/backup-platform`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/backup-platform/de.md) first.** Do not generate from memory.
3. **Disambiguate the surface.** Stateful / DB-writing integration → pre/post hooks; storage-providing (cloud-storage) integration → backup agent. When both apply, have the user pick the one this run augments.
4. **Hooks contract.** `async_pre_backup(hass: HomeAssistant) -> None` and `async_post_backup(hass: HomeAssistant) -> None` are top-level async functions; whatever `async_pre_backup` pauses, `async_post_backup` resumes.
5. **Agent registration.** `async_get_backup_agents(hass)` returns `list[BackupAgent]` and **must** return `[]` when no loaded config entry exists for the domain (`hass.config_entries.async_loaded_entries(DOMAIN)`). `async_register_backup_agents_listener(hass, *, listener, **kwargs)` is a `@callback` returning an unregister function; notify listeners during `async_setup_entry`.
6. **Agent contract.** The `BackupAgent` subclass (from `homeassistant.components.backup`) sets `domain`/`name`/`unique_id` and implements `async_upload_backup`, `async_download_backup`, `async_list_backups`, `async_get_backup`, and `async_delete_backup` — the full abstract interface.
7. **Error semantics.** Errors raise `BackupAgentError` (or a subclass) — no other exception leaves the agent; a missing backup raises `BackupNotFound` in `async_download_backup`/`async_delete_backup`/`async_get_backup`. Call the `on_progress` callback periodically in `async_upload_backup`.
8. **No backup-manager territory.** Never implement encryption, retention, scheduling, or restore orchestration; those belong to the backup manager or the core.
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `need` | yes | — | the integration type / backup need, in prose |
| `surface` | no | inferred + confirmed | `hooks` / `agent` |
| `name` / `unique_id` | no | derived | agent identity (agent surface only) |
| storage / paused operations | no | asked when needed | storage binding (agent) or operations to pause (hooks) |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Resolve `surface` (infer + confirm). Disambiguate hooks vs. agent by integration type; when both apply, have the user pick the one for this run.
3. Read `ha/backup-platform`.
4. The targeted exports are not already declared in `backup.py`. If they are, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the resolved `surface`, and (for an agent) the `name`/`unique_id` and storage binding in one paragraph. Wait for confirmation.

### 2) Generate

| Surface | Module exports |
|---|---|
| hooks | `async_pre_backup(hass)` + `async_post_backup(hass)` (top-level async, symmetric pause/resume) |
| agent | `async_get_backup_agents(hass)` (empty list without a loaded config entry) + `async_register_backup_agents_listener` (`@callback`) + a `BackupAgent` subclass (`domain`/`name`/`unique_id`, upload/download/list/get/delete, `BackupAgentError`/`BackupNotFound`) |

Write to `custom_components/<domain>/backup.py`. Mention the `python3 -m script.scaffold backup` template as a quick start; the skill itself generates offline.

### 3) Validate and report

Validate offline (`backup.py` present; for hooks both top-level functions exported; for an agent `async_get_backup_agents` + the listener `@callback` exported, the empty-list-without-entry guard present, the `BackupAgent` subclass sets the identity and implements the five methods, errors raise `BackupAgentError`/`BackupNotFound`). Emit a CONFORMANT / NEEDS-WORK report keyed to `ha/backup-platform` acceptance criteria, plus the changed file paths and the chosen surface.

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Greenfield scaffold → `ha-integration-scaffold`
- Sibling diagnostics module → `ha/diagnostics`
- Encryption / retention / scheduling / restore → backup manager / HA core, out of scope
- Deploy to live HA → out of scope
