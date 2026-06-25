# HA Integration: Repairs and Issue Registry

Status: draft

## Context

Home Assistant keeps an **issue registry** through which integrations bring problems to the user's attention that need their awareness or action — deprecations, outdated backend versions, misconfiguration. Such issues appear in the frontend under "Repairs". An issue is either **fixable** (the user can resolve it through a `RepairsFlow` directly in the UI) or **informational** (it links to a documentation page and the user fixes it themselves).

HA provides `homeassistant.helpers.issue_registry.async_create_issue(...)` for creation and `async_delete_issue(...)` for removal. Fixable issues need a `repairs.py` module with `async_create_fix_flow(...)` returning a `RepairsFlow`. The issue texts live, translated, in `strings.json` under `issues:`. The decisive line is the delimitation: repairs are meant for states the user *can act on* — transient connection errors do **not** belong in the issue registry but in the coordinator error handling (`UpdateFailed`, `entity-unavailable`).

Quality scale marker: **Gold** (`repair-issues` is a Gold rule: repair issues and repair flows are used once user intervention is needed).

## Goals

- Establish `async_create_issue` as the standard way to bring actionable problems to the user (deprecations, outdated backend versions, misconfiguration)
- Define the split between fixable (`RepairsFlow`) and informational issues cleanly
- Make issue texts consistently translatable through `strings.json`/`issues:` — no hardcoded strings
- Bind the issue life cycle (create, update, delete) to the actual problem state, so stale issues do not linger
- Delimit repairs sharply from transient runtime errors that belong in the coordinator error handling

## Non-Goals

- System-health module (`system_health.py`) — separate HA mechanism, separate follow-up spec
- Issues an integration creates on behalf of *another* integration (`issue_domain`) — rare and outside the standard pattern of this spec
- Multi-step repair flows with complex user input — this spec covers the `ConfirmRepairFlow` standard case; elaborate flows are a separate topic
- Frontend rendering of the repairs card — belongs to HA core, not the integration

## Requirements

### Creating an issue

- **MUST** create issues through `homeassistant.helpers.issue_registry.async_create_issue(hass, domain, issue_id, ...)` — manual registry manipulation or direct persistence is forbidden
- **MUST** set at least `domain`, `issue_id`, `is_fixable`, `severity` (`IssueSeverity`), and `translation_key` on creation — `issue_id` is unique within the `domain`
- **SHOULD** set `breaks_in_ha_version` for deprecations, so the user sees the version from which the behavior breaks
- **MAY** add `translation_placeholders`, `learn_more_url`, and `data` — `data` is arbitrary and not shown to the user but passed through to the repair flow
- **MUST** choose `severity` from `IssueSeverity` — `ERROR` when something is currently broken, `WARNING` when something breaks in the future (for example an API shutdown); `CRITICAL` is reserved and only for a true panic state

### Fixable vs. informational

- **MUST** set `is_fixable=True` only when a `RepairsFlow` exists that actually fixes the problem — a fixable issue without a flow is a defect
- **MUST** set `is_fixable=False` when the user can only resolve the problem themselves (for example updating the backend, changing configuration) — then **SHOULD** point `learn_more_url` at the instructions
- **MUST NOT** create repair issues for mere "something is broken" notifications the user cannot act on — repair issues must be actionable and informative about the problem

### Repair flow

- **MUST** include a `repairs.py` module in `custom_components/<domain>/` for fixable issues
- **MUST** export `async_create_fix_flow(hass, issue_id, data) -> RepairsFlow` as a top-level async function in `repairs.py` — HA calls it when the user starts the repair and routes by `issue_id` to the matching flow
- **MUST** derive the flow from `homeassistant.components.repairs.RepairsFlow` and implement an `async_step_init` as the entry point; for the pure confirmation case it **MAY** use `ConfirmRepairFlow` instead
- **MUST** finish the flow with `self.async_create_entry(title="", data={})` once the repair succeeded — a successfully completed flow removes the issue from the registry automatically

### Translations

- **MUST** define every issue's `translation_key` in `strings.json` under `issues:` with `title` and `description` — no hardcoded user-visible strings in Python code
- **MUST** resolve every placeholder referenced in `translation_placeholders` in the translation text, so the rendered text is complete
- **SHOULD** also map translations in `strings.json` to the repair-flow steps (`step_id`), so form title and description are localized
- Translation follows the sibling spec `ha/translations` in detail

### Issue life cycle (delete/update)

- **MUST** remove an issue through `async_delete_issue(hass, domain, issue_id)` as soon as the integration determines the underlying state is resolved — otherwise a stale issue lingers in the registry
- **SHOULD** use a repeated `async_create_issue` with the same `issue_id` to update an existing issue — the registry continues to track it under the unique `issue_id`
- **SHOULD** set `is_persistent=True` when the problem is only detectable at the moment it occurs (for example a failed update, an unknown action in an automation) — then the issue is shown again after an HA restart
- **SHOULD** leave `is_persistent=False` when the state is re-checkable on every start (for example an outdated backend version) — the integration recreates the issue on the next start anyway if it still applies
- **MUST NOT** rely on HA to clean up issues automatically — both creation *and* deletion are the integration's responsibility

### Delimitation from transient errors

- **MUST NOT** create transient connection or API errors as a repair issue — a temporarily unreachable backend is not an actionable problem for the user
- **MUST** report transient errors instead in the coordinator through `UpdateFailed`, so the entities are marked `entity-unavailable` — details in the sibling spec `ha/coordinator-patterns`
- **SHOULD** create an issue only when a recurring or permanent state exists that the user can concretely act on (for example invalid credentials after a password rotation, a deprecated API)

## Acceptance Criteria

- [ ] Every `async_create_issue` sets `domain`, `issue_id`, `is_fixable`, `severity`, and `translation_key`
- [ ] No `async_create_issue` with `is_fixable=True` without a corresponding `RepairsFlow` in `repairs.py`
- [ ] `repairs.py` exists and exports `async_create_fix_flow(hass, issue_id, data) -> RepairsFlow` once a fixable issue is created
- [ ] Every `translation_key` from `async_create_issue` is resolved in `strings.json` under `issues:` with `title` and `description`
- [ ] A `grep` for hardcoded user strings in `async_create_issue` calls (instead of `translation_key`) returns no hits
- [ ] For every fixable state there is an `async_delete_issue` path that removes the issue after resolution
- [ ] Transient connection errors are reported through `UpdateFailed` in the coordinator, not through `async_create_issue`
- [ ] Quality scale marker: **Gold**

## Open Questions

- **`is_persistent` default**: Should the spec mandate a default or decide per issue type? Currently formulated as SHOULD per case; a calibrated default trigger is missing.
- **Repair-flow complexity**: At what complexity is a multi-step flow worth it over `ConfirmRepairFlow` plus a documentation link? Currently not delimited.
- **Issue-vs-ConfigEntryError threshold**: The quality-scale example combines an informational issue with `raise ConfigEntryError`. When does the issue alone suffice, when is the hard setup abort additionally needed?
- **Deduplication across multiple entries**: With multiple config entries of the same domain — one `issue_id` per entry or one shared issue? Currently not standardised.
