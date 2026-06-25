# Skill: `ha-integration-solution`

Status: draft

## Context

The integration skill family breaks into more than twenty narrowly scoped individual skills, each adding **one** backend building block of a Python custom integration: `ha-integration-scaffold` lays down the skeleton (manifest, `__init__`, config entry, RuntimeData), `ha-config-flow-augment` and `ha-coordinator-add` build out the foundation, `ha-entity-description-mapper` and `ha-entity-platform-add` produce entities, and a broad layer of `ha-service-definition-generator`, `ha-integration-events-add`, `ha-device-automation-add`, `ha-discovery-augment`, `ha-bluetooth-augment`, `ha-diagnostics-augment`, `ha-repairs-add`, `ha-system-health-add`, `ha-significant-change-add`, `ha-backup-platform-add`, `ha-media-source-add`, `ha-reproduce-state-add`, and `ha-conversation-agent-augment` adds actions, surfaces, robustness, and quality features. `ha-translation-sync` and `ha-test-harness-augment` close out i18n and tests; `ha-quality-scale-audit` and `ha-security-audit` review read-only.

Real-world device/cloud/API requirements are almost never a single building block: "integrate my Acme thermostat over its cloud API" is a chain of scaffold → OAuth2/config-flow → coordinator → climate entity → diagnostics → translations → tests → review. A user who doesn't know the skill landscape would have to do that decomposition themselves — which skill, in which order, which `domain` and which `entity_id` thread through which step. That mapping burden is exactly what the user should not have to carry.

This skill is the **upstream planning and dispatch layer** for the integration backend cluster — the integration-side counterpart to `ha-automation-solution`. It takes a fuzzy device/cloud/API requirement, decomposes it into the minimal dependency-ordered set of integration skills, fixes the order, confirms the plan with the user, and then dispatches the owning individual skills one after another, threading the `domain` and the `entity_id`s/file paths of earlier steps into the inputs of later ones. It generates **no** artifact itself — generation and spec conformance stay with the individual skills.

## Scope

Planning and orchestration across the integration backend cluster. One requirement per run → one dependency-ordered skill plan → N dispatched individual calls → one aggregate report. The skill decides the *combination* (which skills, which order, which wiring via `domain`/`entity_id`), not the content of any single building block. The typical order: scaffold → (config-flow + coordinator [+ oauth2]) → entities → [services/events/device-automation/diagnostics/repairs/discovery/bluetooth/system-health/significant-change/backup-platform/media-source/reproduce-state/conversation as needed] → translations → tests → review.

## Goals

- Derive the right *combination* of integration skills from a prose requirement, without the user knowing the skill landscape
- Produce a processable dependency-ordered plan (per entry: step, building block, owning skill, dependency, purpose) and get it confirmed before any generation
- Dispatch the individual skills in correct order and thread the `domain` plus the `entity_id`s/file paths of earlier steps into the inputs of later ones
- Recognize requirements that are actually YAML-automation-shaped (no own protocol, no config-flow integration) and point at `ha-automation-solution` instead of forcing them into an integration
- Deliver an aggregate report naming every produced/changed file and its wiring, and relay the read-only review reports

## Non-Goals

- Generating a single building block and its spec conformance — that stays with the dispatched individual skills
- A pure YAML-automation/helper solution — that is `ha-automation-solution`
- A Lovelace frontend solution — that is `ha-lovelace-card-scaffold` (and the associated Lovelace skill family)
- Deploying to a running HA instance or runtime verification — those are the operator follow-ups via the `ha-integration-deploy` and `ha-integration-verify` agents (out of generation scope)
- Its own validation or conformance logic — each dispatched skill validates its own artifact; this skill only aggregates the reports

## Requirements

### Activation triggers

- **MUST** activate on composite, solution-oriented device/cloud/API requests where the user describes the result, not the building block:
  - "build an integration for device/API X", "scaffold and wire up a full custom integration for …", "integrate my Acme thermostat over its cloud API"
  - "baue mir eine Integration für …", "richte eine Custom-Integration für … ein"
- **SHOULD NOT** activate when the requirement is clearly a single augment (the owning individual skill applies directly); when in doubt, this skill plans and proposes a single-step plan

### Inputs

- **MUST** capture: `requirement` (prose, the desired device/cloud/API result)
- **MAY** capture: `domain` (integration domain, otherwise derived from the scaffold step), `target_dir` (repo root), and known protocol/auth details (REST/MQTT/Bluetooth; API key/OAuth2)

### Pre-flight

- **MUST** check `requirement` is non-empty; on underspecification ask 1–3 targeted questions (which protocol, which auth type, which entity domains, which quality features) before planning
- **MUST** check whether the requirement is actually YAML-automation-shaped (no own protocol, no config-flow integration); if so, mark it in the plan and point at `ha-automation-solution` instead of forcing an integration
- **MUST** check whether an integration already exists under `target_dir/custom_components/<domain>/`; if so, skip the scaffold step and build on the existing one

### Dispatch / plan rules

- **MUST** present a plan as a table in dependency order before any generation: per entry `#`, building block, owning skill, dependency (`depends-on`), purpose — and wait for explicit confirmation
- **MUST NOT** generate a building block inline itself; every generation runs through the owning individual skill
- **MUST** dispatch `ha-integration-scaffold` as step 1 whenever a *new* integration is created (greenfield hub)
- **MUST** plan the foundation before the entities: `ha-config-flow-augment` and `ha-coordinator-add`; `ha-oauth2-credentials-augment` only for OAuth2/cloud auth
- **MUST** map declarative read-type entities (datapoint/schema driven) to `ha-entity-description-mapper` and active, command-driven platforms (climate/cover/light/fan/lock/media_player/…) to `ha-entity-platform-add`
- **SHOULD** plan actions/surfaces/robustness only as the requirement needs: `ha-service-definition-generator` (services), `ha-integration-events-add` (event bus), `ha-device-automation-add` (device automations), `ha-discovery-augment` (DHCP/SSDP/USB/HomeKit/Zeroconf), `ha-bluetooth-augment` (BLE), `ha-diagnostics-augment`, `ha-repairs-add`, `ha-system-health-add`, `ha-significant-change-add`, `ha-backup-platform-add`, `ha-media-source-add`, `ha-reproduce-state-add`, `ha-conversation-agent-augment`
- **MUST** plan i18n and tests near the end: `ha-translation-sync` after all string-producing steps, `ha-test-harness-augment` for the added code paths
- **SHOULD** close the run with the read-only reviews: `ha-quality-scale-audit` and `ha-security-audit` (the bundled review path; they never modify code)
- **MUST** dispatch the skills in dependency order and thread the `domain` plus the `entity_id`s/file paths produced in one step into the inputs of dependent steps
- **MUST** stop and report when a dispatched skill returns a NEEDS-WORK report, rather than building on an unfinished predecessor building block
- **MUST** keep artifacts minimal — never plan a building block the requirement does not call for
- **MUST** keep all identifiers consistent across building blocks per `ha/naming-conventions` and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** list, at the end, every produced/changed file path, its building block, and the wiring (`domain`, which `entity_id` references which)
- **MUST** relay the aggregated CONFORMANT / NEEDS-WORK reports of the individual skills plus the read-only review findings without re-judging them
- **MUST** point at the operator follow-ups (deploy/verify via the `ha-integration-deploy` and `ha-integration-verify` agents) without executing them

### Prohibitions

- **MUST NOT** orchestrate more than one requirement per run
- **MUST NOT** execute a plan without user confirmation
- **MUST NOT** re-judge a dispatched skill report
- **MUST NOT** deploy to or verify against a running HA instance

## Acceptance criteria

- [ ] Skill asks for missing essentials (protocol, auth type, entity domains, quality features) before planning
- [ ] Skill presents a dependency-ordered skill plan and waits for confirmation
- [ ] Skill dispatches the owning individual skills instead of generating itself
- [ ] `ha-integration-scaffold` is step 1 for a new integration; an existing one is built upon
- [ ] `domain` and `entity_id`s of earlier steps are threaded into the inputs of dependent steps
- [ ] A YAML-automation-shaped requirement is recognized and pointed at `ha-automation-solution`
- [ ] Stops on a NEEDS-WORK predecessor instead of building further
- [ ] Run ends with the read-only reviews (`ha-quality-scale-audit`, `ha-security-audit`)
- [ ] Aggregate report lists every file and the wiring, relays the individual reports, and points at the deploy/verify follow-ups

## Open questions

- **Review agent vs. review skills**: the bundled `ha-integration-review` agent (one call summarizing quality-scale, security, and cross-cutting consistency read-only) already exists, but by contract it is a *fire-and-forget* operator follow-up check (pre-PR/pre-release) that is never dispatched by an orchestrator and never replaces the single-dimension audit skills. This skill therefore keeps dispatching `ha-quality-scale-audit` and `ha-security-audit` in-flow (interactive, visible) and points at the `ha-integration-review` agent in the aggregate report as an optional operator follow-up, without executing it.
- **Agent vs. skill dispatch**: should the generation steps run as skills (visible, sequential) or via generation agents (isolated, parallel)? Currently skill dispatch, because the plan confirmation and the `domain`/`entity_id` wiring should stay visible in the user context.
- **Plan persistence**: should the skill plan be persisted as a file so an interrupted run is resumable? Currently in-conversation.
- **Existing-integration awareness**: how deep should the skill read an existing `custom_components/<domain>/` to detect already-present building blocks (coordinator, platforms) and avoid duplicate steps? Currently a pre-flight existence check plus user statement.
