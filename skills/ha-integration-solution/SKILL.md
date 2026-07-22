---
name: ha-integration-solution
description: Plan and orchestrate a complete Home Assistant Python custom-integration backend from a result-oriented device/cloud/API requirement, driven by a chosen quality-scale target tier (Bronze through Platinum) and optionally finishing with CI validation and HACS-release readiness, so the user never has to pick which integration skill to use. The integration-side counterpart to ha-automation-solution. Decomposes the requirement into the minimal dependency-ordered set of integration skills for the target tier, presents the plan for approval, then dispatches ha-integration-scaffold, ha-config-flow-augment, ha-options-flow-augment, ha-config-entry-migrate, ha-oauth2-credentials-augment, ha-coordinator-add, ha-entity-description-mapper, ha-entity-platform-add, ha-device-registry-augment, ha-service-definition-generator, ha-integration-events-add, ha-device-automation-add, ha-discovery-augment, ha-bluetooth-augment, ha-diagnostics-augment, ha-repairs-add, ha-system-health-add, ha-significant-change-add, ha-backup-platform-add, ha-media-source-add, ha-reproduce-state-add, ha-conversation-agent-augment, ha-translation-sync, ha-test-harness-augment, ha-dev-workflow-apply, ha-quality-scale-audit, ha-security-audit, ha-integration-ci-scaffold, and ha-hacs-release in order — threading the integration domain and entity_ids between steps. Activate on "build an integration for device/API X", "scaffold and wire up a full custom integration for …", "build a Gold-tier integration for my Acme thermostat cloud API", "baue mir eine vollständige Integration für …", "richte eine Custom-Integration für … ein". Do not activate for a single clear augment (let the owning skill handle it), a pure YAML automation/helper solution (ha-automation-solution), a Lovelace frontend (ha-lovelace-card-scaffold), or deploying to a live HA instance (ha-integration-deploy agent).
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
- deploying/verifying against a running HA instance as a standalone task → not an activation reason; deploy/verify happens only inside the opt-in `deploy_ready` lifecycle phase (§5) of a build run, behind a second gate, via the `ha-integration-deploy` / `ha-integration-verify` agents

## Hard rules

1. **Never generate inline.** Every building block is produced by its owning skill, resolved at runtime from the live integration `ha-*` inventory (see [Runtime skill resolution](#runtime-skill-resolution)), never from a frozen snapshot of names. This skill plans and dispatches; it does not write code.
2. **Plan before generate.** Always present the dependency-ordered skill plan and wait for explicit approval before dispatching anything.
3. **One requirement, one run.** No multi-requirement batches.
4. **Scaffold first.** For a new integration, `ha-integration-scaffold` is step 1 (greenfield hub); when an integration already exists under `custom_components/<domain>/`, skip scaffold and build on it.
5. **Minimal building blocks.** Decompose to the fewest skills that satisfy the requirement; never plan a surface or quality feature the requirement does not call for.
6. **Thread identities.** Dispatch in dependency order and pass the `domain` plus the `entity_id`s/file paths produced in earlier steps as inputs to dependent steps. Keep all names consistent per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md).
7. **Stop on NEEDS-WORK.** If a dispatched skill returns NEEDS-WORK, stop and report — do not build a dependent building block on an unfinished predecessor.
8. **Relay reports verbatim.** Pass through each dispatched skill's CONFORMANT / NEEDS-WORK report and the read-only review findings without re-judging them.
9. **Recognize automation-shaped work.** When the requirement is really a YAML automation/helper solution rather than a custom integration, say so in the plan and point at `ha-automation-solution` instead of forcing an integration.
10. **Verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).
11. **Tier-driven completeness, audit-gated.** Plan the building blocks the `target_tier` requires (cumulative Bronze→Platinum); finish `release_ready` runs with `ha-integration-ci-scaffold` + `ha-hacs-release`; run `ha-quality-scale-audit` + `ha-security-audit` last as the acceptance gate, routing any shortfall back to the named remediation skill per finding. These two audits are the **in-flow acceptance gate** — run once, here, against the freshly generated code. They deliberately overlap with the bundled `ha-integration-review` agent, which re-runs quality-scale + security *plus* cross-cutting + drift; the split is **temporal, not additive**. A run that clears this in-flow gate **MUST NOT** also dispatch `ha-integration-review` for the same two dimensions in the same pass — the bundled agent is the separate **release / pre-PR whole-picture pass** (see the closing report), pointed at as a follow-up, never run on top of a green in-flow gate.
12. **Deploy-ready is opt-in, behind a second gate.** Generation stays the default and the plan approval (rule 2) remains the single gate for it. Only when `deploy_ready` is set does the deploy→verify→review lifecycle phase run (§5) — and only after a **second explicit human gate** — chaining `ha-dev-instance-provision` (only if no dev-HA pod exists) → `ha-integration-deploy` → `ha-integration-verify` → `ha-integration-review`. On an `ha-integration-verify` FAIL or an `ha-integration-review` NEEDS-WORK, **route the finding back to the owning authoring/remediation skill** (the rule-11 pattern), re-dispatch the fix, then re-deploy and re-verify — a closed feedback loop, not a terminal report. The `ha-integration-review` executed here is exactly the release/pre-PR whole-picture pass of rule 11, legitimately run at this separate post-gate time and never on top of the in-flow gate in the generation pass. Never `kubectl delete pod`; a code refresh is `kill 1` (the `ha-integration-deploy` agent owns that).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `requirement` | yes | — | The desired device/cloud/API result, in prose |
| `domain` | no | derived from scaffold | the integration domain; threaded into every step |
| `target_dir` | no | working dir | repo root; passed through to dispatched skills |
| `protocol` / `auth` | no | asked when needed | REST/MQTT/Bluetooth; API key/OAuth2 |
| `target_tier` | no | `silver` | `bronze`/`silver`/`gold`/`platinum`; drives the included building blocks (cumulative) |
| `release_ready` | no | inferred | also scaffold CI validation + HACS-release readiness |
| `deploy_ready` | no | `false` | opt-in: after a **second** explicit gate, run the deploy→verify→review lifecycle phase (§5) with a fix feedback loop; default keeps the run generation-only |

## Runtime skill resolution

Resolve the owning skill for each building block **at runtime**, by matching the requirement against the live inventory of this plugin's integration/backend `ha-*` skills — read each candidate's stated responsibility from your available-skills registry, or, when running inside the plugin source tree, `Glob skills/ha-*/SKILL.md` and read its `description:`. Match on responsibility, not on a remembered name. The decomposition heuristic below is an **illustrative anchor** of the typical mappings, **not** an authoritative or exhaustive list: re-resolve against the current inventory on every run, so a skill newly added to (or renamed within) the family is dispatchable immediately and a removed one is not — without editing this skill (the runtime-lookup pattern of `issue-orchestrate`). If you genuinely cannot enumerate the live inventory, fall back to the anchor table and note the degraded resolution.

## Decomposition heuristic (requirement shape → building block → owning skill)

| The requirement needs… | Building block | Owning skill |
|---|---|---|
| a new integration skeleton (manifest, `__init__`, config entry, RuntimeData) | greenfield hub | `ha-integration-scaffold` |
| user setup, multi-step/tenant, reauth, reconfigure, or zeroconf config step | config flow | `ha-config-flow-augment` |
| a post-setup config option retrofitted into the options flow | options flow | `ha-options-flow-augment` |
| a stored config-entry schema migration + version bump | config-entry migration | `ha-config-entry-migrate` |
| OAuth2 / Application Credentials cloud auth | OAuth2 flow | `ha-oauth2-credentials-augment` |
| a separate polling role / update interval | DataUpdateCoordinator | `ha-coordinator-add` |
| declarative read-type entities from a datapoint/schema table | EntityDescription lists | `ha-entity-description-mapper` |
| an active command-driven platform (climate/cover/light/fan/lock/media_player/…) | platform entity | `ha-entity-platform-add` |
| device grouping / hub-child `via_device` hierarchy / stale-device removal | device registry | `ha-device-registry-augment` |
| a registered service action | service | `ha-service-definition-generator` |
| firing/listening on the HA event bus | integration events | `ha-integration-events-add` |
| a WebSocket command a frontend card/panel calls (Python-side backend endpoint) | WebSocket command | `ha-websocket-command-add` |
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
| the Platinum code-style / strict-typing / `hassfest` workflow applied + validated | dev-workflow apply | `ha-dev-workflow-apply` |
| a read-only tier check | quality-scale audit | `ha-quality-scale-audit` |
| a read-only security check | security audit | `ha-security-audit` |
| HA-domain CI validation (hassfest / HACS action / pytest matrix) | CI workflow | `ha-integration-ci-scaffold` |
| HACS-release readiness (`hacs.json`, version alignment, ZIP release) | HACS release | `ha-hacs-release` |
| a YAML automation/helper solution (no own protocol, no config flow) | — | **out of scope** → `ha-automation-solution` |

## Target-tier decomposition

The requirement **plus a `target_tier`** drives *which* building blocks the plan includes, so one run reaches a deliberate quality-scale level (cumulative — each tier includes those below):

- **Bronze** (baseline): `ha-integration-scaffold` (config flow, `runtime_data`, `has_entity_name`), the config flow (`ha-config-flow-augment`), and platform tests (`ha-test-harness-augment`).
- **Silver**: + reauth (`ha-config-flow-augment`), coordinator error handling + `PARALLEL_UPDATES` + `entity-unavailable` (`ha-coordinator-add`, `ha-entity-platform-add`), and options where post-setup config is needed (`ha-options-flow-augment`).
- **Gold**: + diagnostics (`ha-diagnostics-augment`), discovery (`ha-discovery-augment`), the device hierarchy (`ha-device-registry-augment`), repairs (`ha-repairs-add`), reconfigure (`ha-config-flow-augment`), and entity/exception translations (`ha-translation-sync`, `ha-service-definition-generator`).
- **Platinum**: strict typing / fully-async — dispatch `ha-dev-workflow-apply` (the owning skill of `ha/dev-workflow`) to apply and validate the code-style + strict-typing + `hassfest` rules against the generated integration; it reports CONFORMANT / NEEDS-WORK and its findings route back like any other building block, instead of surfacing a bare checklist item.
- **Release-ready** (any tier): + CI validation (`ha-integration-ci-scaffold`) and HACS-release readiness (`ha-hacs-release`).

A stored-shape change from a later edit routes through `ha-config-entry-migrate`. The quality-scale + security audits run last and confirm the reached tier; a shortfall routes back to the named remediation skill per finding.

## Workflow

### 1) Clarify

First gauge requirement confidence. When the requirement is clearly specified, use the lightweight path: ask 1–3 targeted questions (which protocol, which auth type, which entity domains, which quality features) before planning. When it is below a confidence threshold (vague target, unnamed device/API, unclear scope), dispatch `requirements-elicit` first and plan against the confirmed requirement artifact — mirroring the `issue-orchestrate` upstream gate — instead of decomposing a fuzzy requirement against weak understanding. Check whether an integration already exists under `custom_components/<domain>/`, and whether the work is actually YAML-automation-shaped. Do not plan on guesses.

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

The typical order is scaffold → (config-flow + coordinator [+ oauth2] [+ options]) → entities [+ device registry] → [Gold surfaces as the tier needs — diagnostics, discovery, repairs, services] → translations → tests → quality-scale + security audit → [release-ready — CI + HACS release]. Include exactly the building blocks the `target_tier` requires (cumulative). State any "this is actually a YAML automation" finding here and point at `ha-automation-solution`. Wait for explicit approval — that approval is the **single human gate for generation**; after it the dispatch, the audits, and the release-ready finish run to completion, stopping only on a NEEDS-WORK. The opt-in `deploy_ready` lifecycle phase (§5) is gated separately, by a **second** explicit approval.

### 3) Dispatch

Invoke each owning skill in plan order, passing the `domain` and the `entity_id`s/file paths resolved in earlier steps as inputs to the dependent steps. After each, check the returned report; stop on NEEDS-WORK rather than building on an unfinished predecessor.

### 4) Aggregate report

List every produced/changed file, its building block, and the wiring (the `domain`, which `entity_id` references which). Relay each dispatched skill's CONFORMANT / NEEDS-WORK report and the read-only review findings verbatim — do not re-judge them. Point at the operator follow-ups (a bundled whole-picture pass via the `ha-integration-review` agent, deploy via the `ha-integration-deploy` agent, runtime verify via the `ha-integration-verify` agent) without executing them. The `ha-integration-review` follow-up is the **release / pre-PR** review — it adds cross-cutting + drift *on top of* quality-scale + security and must **not** re-run this run's in-flow quality+security gate; a caller who cleared the in-flow gate does not run it again for the same two dimensions in the same pass. In the default generation-only run, stop here and do not deploy. When `deploy_ready` is set, continue into §5 after a second explicit gate.

### 5) Deploy-ready lifecycle phase (opt-in)

Runs **only** when `deploy_ready` is set, and **only** after a second explicit human approval distinct from the plan gate — so the generation-only default and its single gate are preserved. This turns the former set of manual agent islands (build → deploy → verify → review with no feedback loop) into one autonomous flow:

1. **Provision (if needed).** If no dev-HA pod exists in the local Kind cluster, dispatch `ha-dev-instance-provision`; otherwise skip.
2. **Deploy.** Dispatch `ha-integration-deploy` (lint pre-flight → `kubectl cp` → bytecode-cache cleanup → `kill 1` restart → wait-on-ready → log tail). Never `kubectl delete pod`.
3. **Verify.** Dispatch `ha-integration-verify` (pod status, log error-pattern scan, installed-files check).
4. **Review.** Dispatch the bundled `ha-integration-review` agent — the release/pre-PR whole-picture pass (quality-scale + security + cross-cutting + drift).

**Feedback loop.** On an `ha-integration-verify` FAIL or an `ha-integration-review` NEEDS-WORK, do not terminate with a descriptive report: route each finding back to the owning authoring/remediation skill (the rule-11 pattern), re-dispatch the fix, then re-run from step 2 (re-deploy → re-verify), until verify passes and review is CONFORMANT or the operator stops the loop. Report the deploy/verify/review outcome and every fix cycle at the end.

## Boundaries

- Single-building-block generation + spec conformance → the owning individual skill
- A YAML automation/helper solution → `ha-automation-solution` (this skill only recognizes and points)
- A Lovelace frontend card → `ha-lovelace-card-scaffold`
- Deploy / runtime verify against a live HA instance → generation-only by default; available only via the opt-in `deploy_ready` lifecycle phase (§5), which drives the `ha-integration-deploy` / `ha-integration-verify` / `ha-integration-review` agents behind a second gate with a fix feedback loop
