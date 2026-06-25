---
name: ha-integration-solution
description: Plan and orchestrate a complete Home Assistant Python custom-integration backend from a result-oriented device/cloud/API requirement, so the user never has to pick which integration skill to use. The integration-side counterpart to ha-automation-solution. Decomposes the requirement into the minimal dependency-ordered set of integration skills, presents the plan for approval, then dispatches ha-integration-scaffold, ha-config-flow-augment, ha-coordinator-add, ha-oauth2-credentials-augment, ha-entity-description-mapper, ha-entity-platform-add, ha-service-definition-generator, ha-integration-events-add, ha-device-automation-add, ha-discovery-augment, ha-bluetooth-augment, ha-diagnostics-augment, ha-repairs-add, ha-system-health-add, ha-significant-change-add, ha-backup-platform-add, ha-media-source-add, ha-reproduce-state-add, ha-conversation-agent-augment, ha-translation-sync, ha-test-harness-augment, ha-quality-scale-audit, and ha-security-audit in order — threading the integration domain and entity_ids between steps. Activate on "build an integration for device/API X", "scaffold and wire up a full custom integration for …", "integrate my Acme thermostat over its cloud API", "baue mir eine Integration für …", "richte eine Custom-Integration für … ein". Do not activate for a single clear augment (let the owning skill handle it), a pure YAML automation/helper solution (ha-automation-solution), a Lovelace frontend (ha-lovelace-card-scaffold), or deploying to a live HA instance (ha-integration-deploy agent).
tags: [home-assistant, integration, orchestration, planning]
---

# HA Integration Solution

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-integration-solution/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-integration-solution/en.md).

This skill is the **front door** to the Python custom-integration backend cluster — the integration-side counterpart to `ha-automation-solution`. It does not generate any artifact itself — it decomposes the requirement, plans the dependency-ordered combination, and dispatches the owning individual skills, each of which owns its generation and spec conformance.

## Why this is a skill, not an agent

- **Plan-before-generate gate** — the skill plan must be presented and explicitly approved before any generation; that human-visible gate is core to the contract and an agent's fire-and-forget shape would lose it.
- **Mid-flow interactivity** — clarifying questions (protocol, auth type, entity domains, quality features), plan confirmation, and the "this is actually a YAML automation, not an integration" decision are per-run dialogues.
- **Orchestrator that dispatches other skills** — the skill-orchestrates-skill default (see `skill-vs-agent`) keeps the entry point in skill form, like `ha-automation-solution` dispatching its authoring skills.
- Counter-dimension considered: the per-building-block generation could run as parallel agents, but the plan approval and the `domain`/`entity_id` threading must stay visible in the user's context; skill wins.

## When this skill activates

Use this skill when the user describes a **device/cloud/API integration result** that likely needs more than one building block, and should not have to know which integration skill produces what — "build an integration for X", "integrate my Acme thermostat over its cloud API", "baue mir eine Integration für …".

## When NOT to activate

- a single clear augment (one config-flow pattern, one coordinator, one platform, one diagnostics enrichment) → let the owning skill activate directly
- a pure YAML automation/helper/template/blueprint solution (no own protocol, no config flow) → `ha-automation-solution`
- a Lovelace frontend card → `ha-lovelace-card-scaffold` (and the Lovelace skill family)
- deploying/verifying against a running HA instance → out of scope (generation only; the `ha-integration-deploy` / `ha-integration-verify` agents own that)

## Hard rules

1. **Never generate inline.** Every building block is produced by its owning skill. This skill plans and dispatches; it does not write code.
2. **Plan before generate.** Always present the dependency-ordered skill plan and wait for explicit approval before dispatching anything.
3. **One requirement, one run.** No multi-requirement batches.
4. **Scaffold first.** For a new integration, `ha-integration-scaffold` is step 1 (greenfield hub); when an integration already exists under `custom_components/<domain>/`, skip scaffold and build on it.
5. **Minimal building blocks.** Decompose to the fewest skills that satisfy the requirement; never plan a surface or quality feature the requirement does not call for.
6. **Thread identities.** Dispatch in dependency order and pass the `domain` plus the `entity_id`s/file paths produced in earlier steps as inputs to dependent steps. Keep all names consistent per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md).
7. **Stop on NEEDS-WORK.** If a dispatched skill returns NEEDS-WORK, stop and report — do not build a dependent building block on an unfinished predecessor.
8. **Relay reports verbatim.** Pass through each dispatched skill's CONFORMANT / NEEDS-WORK report and the read-only review findings without re-judging them.
9. **Recognize automation-shaped work.** When the requirement is really a YAML automation/helper solution rather than a custom integration, say so in the plan and point at `ha-automation-solution` instead of forcing an integration.
10. **Verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `requirement` | yes | — | The desired device/cloud/API result, in prose |
| `domain` | no | derived from scaffold | the integration domain; threaded into every step |
| `target_dir` | no | working dir | repo root; passed through to dispatched skills |
| `protocol` / `auth` | no | asked when needed | REST/MQTT/Bluetooth; API key/OAuth2 |

## Decomposition heuristic (requirement shape → building block → owning skill)

| The requirement needs… | Building block | Owning skill |
|---|---|---|
| a new integration skeleton (manifest, `__init__`, config entry, RuntimeData) | greenfield hub | `ha-integration-scaffold` |
| user setup, multi-step/tenant, reauth, reconfigure, or discovery config step | config flow | `ha-config-flow-augment` |
| OAuth2 / Application Credentials cloud auth | OAuth2 flow | `ha-oauth2-credentials-augment` |
| a separate polling role / update interval | DataUpdateCoordinator | `ha-coordinator-add` |
| declarative read-type entities from a datapoint/schema table | EntityDescription lists | `ha-entity-description-mapper` |
| an active command-driven platform (climate/cover/light/fan/lock/media_player/…) | platform entity | `ha-entity-platform-add` |
| a registered service action | service | `ha-service-definition-generator` |
| firing/listening on the HA event bus | integration events | `ha-integration-events-add` |
| a device trigger/condition/action | device automation | `ha-device-automation-add` |
| DHCP/SSDP/USB/HomeKit/Zeroconf network discovery | discovery matcher | `ha-discovery-augment` |
| BLE advertisements / Bluetooth support | bluetooth | `ha-bluetooth-augment` |
| redacted diagnostics dump | diagnostics | `ha-diagnostics-augment` |
| a user-facing fixable/informative issue | repairs issue | `ha-repairs-add` |
| at-a-glance system-health info | system health | `ha-system-health-add` |
| throttling insignificant continuous-value updates | significant-change checker | `ha-significant-change-add` |
| backup hooks or a backup agent | backup platform | `ha-backup-platform-add` |
| a browsable media source | media source | `ha-media-source-add` |
| scene / reproduce-state support | reproduce_state | `ha-reproduce-state-add` |
| intents / a conversation agent / LLM API tools | voice & AI surfaces | `ha-conversation-agent-augment` |
| translation/icon structural sync after string changes | i18n drift fix | `ha-translation-sync` |
| tests for the added code paths | test harness | `ha-test-harness-augment` |
| a read-only tier check | quality-scale audit | `ha-quality-scale-audit` |
| a read-only security check | security audit | `ha-security-audit` |
| a YAML automation/helper solution (no own protocol, no config flow) | — | **out of scope** → `ha-automation-solution` |

## Workflow

### 1) Clarify

If the requirement is underspecified, ask 1–3 targeted questions (which protocol, which auth type, which entity domains, which quality features) before planning. Check whether an integration already exists under `custom_components/<domain>/`, and whether the work is actually YAML-automation-shaped. Do not plan on guesses.

### 2) Plan

Decompose into a dependency-ordered plan and present it as a table:

```markdown
| # | Building block | Skill | Depends on | Purpose |
|---|---|---|---|---|
| 1 | scaffold (domain=acme) | ha-integration-scaffold | — | manifest/__init__/config entry/RuntimeData |
| 2 | OAuth2 / Application Credentials | ha-oauth2-credentials-augment | #1 | cloud auth |
| 3 | config flow | ha-config-flow-augment | #1,#2 | account setup + reauth |
| 4 | coordinator | ha-coordinator-add | #1 | poll the Acme cloud API |
| 5 | climate entity | ha-entity-platform-add | #4 | thermostat control |
| 6 | diagnostics | ha-diagnostics-augment | #5 | redacted dump |
| 7 | translations | ha-translation-sync | #3,#5,#6 | string/icon sync |
| 8 | tests | ha-test-harness-augment | #5 | climate platform tests |
| 9 | quality-scale audit | ha-quality-scale-audit | all | read-only tier check |
| 10 | security audit | ha-security-audit | all | read-only security check |
```

The typical order is scaffold → (config-flow + coordinator [+ oauth2]) → entities → [surfaces/robustness as needed] → translations → tests → review. State any "this is actually a YAML automation" finding here and point at `ha-automation-solution`. Wait for explicit approval.

### 3) Dispatch

Invoke each owning skill in plan order, passing the `domain` and the `entity_id`s/file paths resolved in earlier steps as inputs to the dependent steps. After each, check the returned report; stop on NEEDS-WORK rather than building on an unfinished predecessor.

### 4) Aggregate report

List every produced/changed file, its building block, and the wiring (the `domain`, which `entity_id` references which). Relay each dispatched skill's CONFORMANT / NEEDS-WORK report and the read-only review findings verbatim — do not re-judge them. Point at the operator follow-ups (a bundled whole-picture pass via the `ha-integration-review` agent, deploy via the `ha-integration-deploy` agent, runtime verify via the `ha-integration-verify` agent) without executing them. Do not deploy.

## Boundaries

- Single-building-block generation + spec conformance → the owning individual skill
- A YAML automation/helper solution → `ha-automation-solution` (this skill only recognizes and points)
- A Lovelace frontend card → `ha-lovelace-card-scaffold`
- Deploy / runtime verify against a live HA instance → out of scope; the `ha-integration-deploy` / `ha-integration-verify` agents
