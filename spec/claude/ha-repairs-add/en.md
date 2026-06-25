# Skill: `ha-repairs-add`

Status: draft

## Context

`ha/repairs` defines how an HA integration surfaces actionable problems through the **issue registry** (deprecations, outdated backend versions, misconfiguration): `async_create_issue(...)` to raise, a `repairs.py` module with `async_create_fix_flow(...)` for **fixable** issues, translated text in `strings.json` under `issues:`, and `async_delete_issue(...)` to clear once the state is resolved. The `repair-issues` rule is a **Gold** quality-scale rule. So far no skill operationalizes it: developers hard-code issue text, set `is_fixable=True` without a matching flow, forget the `async_delete_issue` path (a stale issue lingers), or misuse repairs for transient connection errors that belong in the coordinator's error handling.

This skill augments **one** repair issue (fixable or informative) into an **existing** integration: it produces the `async_create_issue` call site, for fixable issues the `repairs.py` with `async_create_fix_flow` and a `RepairsFlow`/`ConfirmRepairFlow`, the `issues:` entries in `strings.json`, and the `async_delete_issue` lifecycle path — conformant to `ha/repairs`. It is the repairs sibling of `ha-quality-scale-audit`: that one grades, this one builds the Gold rule.

## Scope

Augmenting exactly one repair issue per run into an existing `custom_components/<domain>/` integration: the `async_create_issue` call site (at the point of state detection), the `strings.json` `issues:` entry (`title`/`description`), for fixable issues `repairs.py` (`async_create_fix_flow` + flow), and the `async_delete_issue` path. The skill decides fixable vs. informative and the `severity`, reads `ha/repairs`, and validates.

## Goals

- Augment a spec-conformant repair issue from a described problem situation that satisfies every MUST rule in `ha/repairs`
- Decide fixable vs. informative deliberately and enforce the consequence: `is_fixable=True` only with a matching `RepairsFlow`; informative with a `learn_more_url`
- Make every user-visible string translatable via `strings.json`/`issues:` — no hard-coded strings
- Bind the issue lifecycle to the problem state: produce an `async_delete_issue` path that removes the issue once resolved
- Delimit repairs sharply from transient errors and redirect the latter to the coordinator's `UpdateFailed` handling

## Non-Goals

- Greenfield scaffolding of an integration — that is `ha-integration-scaffold`
- System health (`system_health.py`) — a separate HA mechanism
- Multi-step repair flows with complex user input — this skill covers the `ConfirmRepairFlow`/simple `async_step_init` standard case
- Issues raised on behalf of *another* integration (`issue_domain`) — outside the standard pattern
- Quality-scale grading of the whole integration — that is `ha-quality-scale-audit`
- Transient error handling (`UpdateFailed`, `entity-unavailable`) — that is `ha-coordinator-add` / `ha/coordinator-patterns`

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a repair issue for …", "create a fixable repair flow for …", "warn the user about a deprecation"
  - "surface an issue when the backend version is too old"
  - "füge ein Repair-Issue für … hinzu", "erstelle einen Repair-Flow für …", "weise den User auf eine Deprecation hin"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the problem situation (prose, what the issue points at)
- **MAY** capture: `issue_id` (default derived from the situation, `snake_case`), `fixable` (else derived from the situation and confirmed), `severity` (`error`/`warning`), `breaks_in_ha_version`, `learn_more_url`, `is_persistent`

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain` from it
- **MUST** check the problem situation against the transience delimitation: if it is a transient connection/API error, the skill **MUST** redirect to the coordinator's `UpdateFailed` handling instead of raising an issue
- **MUST** read the `ha/repairs` spec before generating
- **MUST NOT** overwrite an existing issue with the same `issue_id`; on collision abort with the `issue_id` quoted

### Generation rules (from `ha/repairs`)

- **MUST** raise the issue via `homeassistant.helpers.issue_registry.async_create_issue(hass, domain, issue_id, ...)` and set at least `is_fixable`, `severity` (`IssueSeverity`), and `translation_key`; `issue_id` is unique within the `domain`
- **MUST** choose `severity` deliberately: `ERROR` when something is currently broken, `WARNING` when something will break in the future; not `CRITICAL` for normal cases
- **SHOULD** set `breaks_in_ha_version` for deprecations
- **MUST** for `is_fixable=True` produce a `repairs.py` with `async_create_fix_flow(hass, issue_id, data) -> RepairsFlow` as a top-level async function that routes to the flow by `issue_id`; the flow derives from `RepairsFlow` (or uses `ConfirmRepairFlow`), implements `async_step_init`, and completes with `self.async_create_entry(title="", data={})` (which removes the issue automatically)
- **MUST** for `is_fixable=False` point `learn_more_url` at the instructions and require **no** `repairs.py` for this issue
- **MUST** place the `translation_key` in `strings.json` under `issues:` with `title` and `description`, resolve every `translation_placeholders` in the text, and leave **no** hard-coded user strings in the Python code (translation detail follows `ha/translations`)
- **MUST** produce or name an `async_delete_issue(hass, domain, issue_id)` path that removes the issue once the underlying state is resolved
- **SHOULD** set `is_persistent=True` when the problem is only detectable at the moment it occurs; otherwise `is_persistent=False`
- **MUST** name identifiers per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline: every `async_create_issue` sets the mandatory fields; no `is_fixable=True` without a `repairs.py` flow; every `translation_key` is resolved in `strings.json`; an `async_delete_issue` path exists; no hard-coded strings
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/repairs`, plus the written/changed file paths and the quality-scale marker (**Gold**)

### Prohibitions

- **MUST NOT** augment more than one issue per run
- **MUST NOT** raise a repair issue for a transient error or a pure "something is broken" message with no user action
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill decides fixable vs. informative and confirms it before generating
- [ ] Skill reads `ha/repairs` and checks the transience delimitation in pre-flight
- [ ] `async_create_issue` sets `domain`, `issue_id`, `is_fixable`, `severity`, `translation_key`
- [ ] `is_fixable=True` always comes with a `repairs.py`/`async_create_fix_flow`
- [ ] `translation_key` is resolved in `strings.json` under `issues:` with `title`/`description`; no hard-coded user strings
- [ ] An `async_delete_issue` path removes the issue once resolved
- [ ] A transient situation is redirected to `UpdateFailed`/coordinator instead of raised as an issue
- [ ] Report names the file paths and the quality-scale marker **Gold**

## Open questions

- **Call-site placement**: should the skill place `async_create_issue` automatically at the detected state location (coordinator, setup, service) or deliver the snippet and leave embedding to the user? Currently it places at the obvious location and names it in the report.
- **Dedup across multiple entries**: one `issue_id` per ConfigEntry or a shared issue? `ha/repairs` leaves this open; the skill asks when in doubt.
- **Flow complexity**: when is a multi-step flow worth it over `ConfirmRepairFlow` + a docs link? The skill currently covers only the standard case.
