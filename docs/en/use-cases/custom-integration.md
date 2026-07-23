# Build a custom integration (Python)

A complete custom integration under `custom_components/<domain>/`, installable through HACS — from an empty folder to a skeleton with manifest, config flow, coordinator, entities, and a pytest harness, then augmented with the advanced platform features a mature integration needs.

## Use cases

- You want to wrap a REST or WebSocket **cloud API** in a first-class integration: a config flow to capture credentials, a `DataUpdateCoordinator` that polls on one schedule, and sensor/switch entities backed by the fetched data.
- You want to talk to a **local device** — Bluetooth, mDNS/zeroconf, or a LAN HTTP endpoint — and have Home Assistant discover it automatically instead of forcing manual setup.
- You have a working integration and now need to **grow it**: add a second entity platform, expose a registered service, add an options flow so users can retune it without deleting the entry, or migrate a config entry to a new schema version without breaking existing installs.
- You are preparing an integration for **HACS distribution** and want the full skeleton — translations, icons, diagnostics, a repairs flow, and system-health — done correctly the first time rather than bolted on later.
- You are pushing an existing component **up the HA quality scale** and need the bronze-floor-to-platinum plumbing: strict typing, diagnostics redaction, reproduce-state, significant-change, and a test harness that covers the secondary code paths.

## Target audiences

- **Python developers wrapping a device or cloud API.** You know Python but not necessarily every Home Assistant contract (config-entry lifecycle, coordinator semantics, entity registry). This use case gives you an idiomatic skeleton and focused augment skills so you write integration logic, not boilerplate.
- **Contributors aiming for HACS distribution.** You want a repository layout and manifest that HACS accepts, with translations, icons, and diagnostics in place from the start. The scaffold produces a HACS-installable component; `ha-hacs-release` handles the release side.
- **Maintainers climbing the quality scale.** You already ship an integration and want to reach a higher tier. The augment skills add exactly the platforms and features a tier requires (repairs, system-health, reproduce-state, significant-change, backup), and `ha-quality-scale-audit` tells you where you stand.

## How skills and agents work together

The `ha-integration-solution` front door plans the work and dispatches focused skills; each focused skill owns one artifact and its own spec conformance.

```mermaid
flowchart TD
    dev(["Integration developer"]) --> fd["ha-integration-solution<br/>front door"]
    fd --> scaffold["ha-integration-scaffold<br/>skeleton"]
    fd --> aug["Augment skills<br/>config-flow / coordinator / entity platforms<br/>services / diagnostics / discovery / …"]
    fd --> qual["Quality<br/>ha-translation-sync / ha-test-harness-augment"]
    fd --> style["ha-dev-workflow-apply<br/>format / typing / validation"]
    scaffold -.-> devtest["Run and test on a dev HA"]
    style -.-> review["Review and harden"]
```

Describe the integration you want and `ha-integration-solution` decomposes it into a skeleton plus the augment, quality, and code-style steps it needs, then dispatches each. `ha-integration-scaffold` lays down the installable skeleton; the augment skills add one platform feature each; `ha-translation-sync` and `ha-test-harness-augment` keep translations and tests honest; `ha-dev-workflow-apply` enforces format, typing, and validation. From here the natural hand-offs are to [Run and test on a dev HA](dev-testing.md) and then [Review and harden before release](review-hardening.md).

## Skills and agents in play

- **Front door:** `ha-integration-solution`
- **Building blocks:** `ha-integration-scaffold` (skeleton: manifest, lifecycle, config flow, coordinator, entity, platforms, translations, icons, diagnostics, pytest harness); augment skills `ha-config-flow-augment`, `ha-options-flow-augment`, `ha-config-entry-migrate`, `ha-coordinator-add`, `ha-entity-platform-add`, `ha-entity-description-mapper`, `ha-service-definition-generator`, `ha-diagnostics-augment`, `ha-discovery-augment`, `ha-bluetooth-augment`, `ha-oauth2-credentials-augment`, `ha-device-registry-augment`, `ha-repairs-add`, `ha-system-health-add`, `ha-backup-platform-add`, `ha-media-source-add`, `ha-significant-change-add`, `ha-reproduce-state-add`, `ha-integration-events-add`, `ha-conversation-agent-augment`; quality `ha-translation-sync`, `ha-test-harness-augment`; code style and validation `ha-dev-workflow-apply`
- **Related use cases:** [Run and test on a dev HA](dev-testing.md), [Review and harden before release](review-hardening.md)

See the full catalog under [Skills](../skills/index.md) and [Agents](../agents/index.md).

## Specs

- `spec/ha/integration-architecture`
- `spec/ha/config-flow-patterns`
- `spec/ha/coordinator-patterns`
- `spec/ha/entity-architecture`
- `spec/ha/dev-workflow`
- and the other `spec/ha/*` integration topics
