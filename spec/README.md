# Spezifikationen — `claude-home-assistant`

Quelle der Wahrheit hinter den Skills und Agents dieses Plugins. Specs sind zweisprachig: Deutsch ist kanonisch (`de.md`), Englisch ist Übersetzung (`en.md`). Konfiguration siehe `.spec-config.yml`.

## Index

| Slug | Titel (DE) | Titel (EN) | Status | Zuletzt aktualisiert |
|---|---|---|---|---|
| [`ha/integration-architecture`](ha/integration-architecture/de.md) | HA-Integration: Architektur-Foundation | HA Integration: Architecture Foundation | draft | unversioned |
| [`ha/runtime-data-pattern`](ha/runtime-data-pattern/de.md) | HA-Integration: `runtime_data`-Pattern | HA Integration: `runtime_data` Pattern | draft | unversioned |
| [`ha/coordinator-patterns`](ha/coordinator-patterns/de.md) | HA-Integration: Coordinator-Patterns | HA Integration: Coordinator Patterns | draft | unversioned |
| [`ha/config-flow-patterns`](ha/config-flow-patterns/de.md) | HA-Integration: Config-Flow-Patterns | HA Integration: Config Flow Patterns | draft | unversioned |
| [`ha/entity-architecture`](ha/entity-architecture/de.md) | HA-Integration: Entity-Architektur | HA Integration: Entity Architecture | draft | unversioned |
| [`ha/device-registry`](ha/device-registry/de.md) | HA-Integration: Device-Registry und `DeviceInfo`-Hierarchie | HA Integration: Device Registry and `DeviceInfo` Hierarchy | draft | unversioned |
| [`ha/services`](ha/services/de.md) | HA-Integration: Services | HA Integration: Services | draft | unversioned |
| [`ha/translations`](ha/translations/de.md) | HA-Integration: Translations | HA Integration: Translations | draft | unversioned |
| [`ha/icons`](ha/icons/de.md) | HA-Integration: `icons.json` | HA Integration: `icons.json` | draft | unversioned |
| [`ha/zeroconf-discovery`](ha/zeroconf-discovery/de.md) | HA-Integration: Zeroconf-Discovery | HA Integration: Zeroconf Discovery | draft | unversioned |
| [`ha/diagnostics`](ha/diagnostics/de.md) | HA-Integration: Diagnostics | HA Integration: Diagnostics | draft | unversioned |
| [`ha/lovelace-card-patterns`](ha/lovelace-card-patterns/de.md) | HA-Integration: Lovelace-Card-Patterns | HA Integration: Lovelace Card Patterns | draft | unversioned |
| [`ha/lovelace-card-entity-selector`](ha/lovelace-card-entity-selector/de.md) | HA-Integration: Lovelace-Card-Entity-Selector-Filter | HA Integration: Lovelace Card Entity Selector Filtering | draft | unversioned |
| [`ha/blueprint-patterns`](ha/blueprint-patterns/de.md) | HA-Blueprint: Authoring-Patterns | HA Blueprint: Authoring Patterns | draft | unversioned |
| [`ha/quality-scale`](ha/quality-scale/de.md) | HA-Integration: Quality-Scale | HA Integration: Quality Scale | draft | unversioned |
| [`ha/integration-manifest`](ha/integration-manifest/de.md) | HA-Integration: `manifest.json` | HA Integration: `manifest.json` | draft | unversioned |
| [`ha/setup-lifecycle`](ha/setup-lifecycle/de.md) | HA-Integration: Setup-Lifecycle | HA Integration: Setup Lifecycle | draft | unversioned |
| [`ha/exceptions`](ha/exceptions/de.md) | HA-Integration: Exceptions und Fehler-Übersetzungen | HA Integration: Exceptions and Error Translations | draft | unversioned |
| [`ha/repairs`](ha/repairs/de.md) | HA-Integration: Repairs und Issue-Registry | HA Integration: Repairs and Issue Registry | draft | unversioned |
| [`ha/application-credentials`](ha/application-credentials/de.md) | HA-Integration: Application Credentials (OAuth2) | HA Integration: Application Credentials (OAuth2) | draft | unversioned |
| [`ha/async-patterns`](ha/async-patterns/de.md) | HA-Integration: Async-Patterns | HA Integration: Async Patterns | draft | unversioned |
| [`ha/entity-platform-types`](ha/entity-platform-types/de.md) | HA-Integration: Entity-Plattform-Typen | HA Integration: Entity Platform Types | draft | unversioned |
| [`ha/bluetooth`](ha/bluetooth/de.md) | HA-Integration: Bluetooth | HA Integration: Bluetooth | draft | unversioned |
| [`ha/intents-conversation`](ha/intents-conversation/de.md) | HA-Integration: Intents und Conversation | HA Integration: Intents and Conversation | draft | unversioned |
| [`ha/significant-change`](ha/significant-change/de.md) | HA-Integration: Significant-Change | HA Integration: Significant Change | draft | unversioned |
| [`ha/backup-platform`](ha/backup-platform/de.md) | HA-Integration: Backup-Platform | HA Integration: Backup Platform | draft | unversioned |
| [`ha/device-automations`](ha/device-automations/de.md) | HA-Integration: Device-Automations | HA Integration: Device Automations | draft | unversioned |
| [`ha/discovery-mechanisms`](ha/discovery-mechanisms/de.md) | HA-Integration: Discovery-Mechanismen (DHCP/SSDP/USB/HomeKit) | HA Integration: Discovery Mechanisms (DHCP/SSDP/USB/HomeKit) | draft | unversioned |
| [`ha/integration-events`](ha/integration-events/de.md) | HA-Integration: Events (feuern und lauschen) | HA Integration: Events (Firing and Listening) | draft | unversioned |
| [`ha/media-source`](ha/media-source/de.md) | HA-Integration: Media-Source | HA Integration: Media Source | draft | unversioned |
| [`ha/reproduce-state`](ha/reproduce-state/de.md) | HA-Integration: Reproduce-State (Scene-Support) | HA Integration: Reproduce State (Scene Support) | draft | unversioned |
| [`ha/system-health`](ha/system-health/de.md) | HA-Integration: System-Health | HA Integration: System Health | draft | unversioned |
| [`ha/llm-api`](ha/llm-api/de.md) | HA-Integration: LLM-API (Tools für Conversation-Agents) | HA Integration: LLM API (Tools for Conversation Agents) | draft | unversioned |
| [`ha/dev-workflow`](ha/dev-workflow/de.md) | HA-Integration: Dev-Workflow (Guidelines, Typing, Validation) | HA Integration: Dev Workflow (Guidelines, Typing, Validation) | draft | unversioned |
| [`ha/entity-platforms-controls`](ha/entity-platforms-controls/de.md) | HA-Integration: Entity-Plattformen (Controls) | HA Integration: Entity Platforms (Controls) | draft | unversioned |
| [`ha/entity-platforms-climate`](ha/entity-platforms-climate/de.md) | HA-Integration: Entity-Plattformen (Klima-Familie) | HA Integration: Entity Platforms (Climate Family) | draft | unversioned |
| [`ha/entity-platforms-inputs`](ha/entity-platforms-inputs/de.md) | HA-Integration: Entity-Plattformen (Input-Helfer) | HA Integration: Entity Platforms (Input Helpers) | draft | unversioned |
| [`ha/entity-platforms-sensors`](ha/entity-platforms-sensors/de.md) | HA-Integration: Entity-Plattformen (Sensorik) | HA Integration: Entity Platforms (Sensors) | draft | unversioned |
| [`ha/entity-platforms-media`](ha/entity-platforms-media/de.md) | HA-Integration: Entity-Plattformen (Media) | HA Integration: Entity Platforms (Media) | draft | unversioned |
| [`ha/entity-platforms-voice`](ha/entity-platforms-voice/de.md) | HA-Integration: Entity-Plattformen (Voice & AI) | HA Integration: Entity Platforms (Voice & AI) | draft | unversioned |
| [`ha/entity-platforms-devices`](ha/entity-platforms-devices/de.md) | HA-Integration: Entity-Plattformen (Geräte-Domänen) | HA Integration: Entity Platforms (Device Domains) | draft | unversioned |
| [`ha/lovelace-card-editor`](ha/lovelace-card-editor/de.md) | HA-Integration: Lovelace-Card-Editor (`ha-form`) | HA Integration: Lovelace Card Editor (`ha-form`) | draft | unversioned |
| [`ha/lovelace-card-features`](ha/lovelace-card-features/de.md) | HA-Integration: Lovelace-Card-Features (Tile-Features) | HA Integration: Lovelace Card Features (Tile Features) | draft | unversioned |
| [`ha/lovelace-badges`](ha/lovelace-badges/de.md) | HA-Integration: Lovelace-Badges | HA Integration: Lovelace Badges | draft | unversioned |
| [`ha/lovelace-strategies`](ha/lovelace-strategies/de.md) | HA-Integration: Lovelace-Strategies | HA Integration: Lovelace Strategies | draft | unversioned |
| [`ha/lovelace-views-panels`](ha/lovelace-views-panels/de.md) | HA-Integration: Lovelace-Views und Custom-Panels | HA Integration: Lovelace Views and Custom Panels | draft | unversioned |
| [`ha/frontend-data-api`](ha/frontend-data-api/de.md) | HA-Integration: Frontend-Data-API (`hass`-Objekt) | HA Integration: Frontend Data API (`hass` object) | draft | unversioned |
| [`ha/frontend-websocket-commands`](ha/frontend-websocket-commands/de.md) | HA-Integration: Frontend-WebSocket-Commands | HA Integration: Frontend WebSocket Commands | draft | unversioned |
| [`ha/security-hardening`](ha/security-hardening/de.md) | HA-Integration: Security-Hardening | HA Integration: Security Hardening | draft | unversioned |
| [`ha/test-harness`](ha/test-harness/de.md) | HA-Integration: Test-Harness | HA Integration: Test Harness | draft | unversioned |
| [`ha/dev-environment`](ha/dev-environment/de.md) | HA-Integration: Dev-Environment | HA Integration: Dev Environment | draft | unversioned |
| [`ha/dev-instance-provisioning`](ha/dev-instance-provisioning/de.md) | HA-Integration: Dev-Instanz-Provisioning | HA Integration: Dev Instance Provisioning | draft | unversioned |
| [`ha/naming-conventions`](ha/naming-conventions/de.md) | HA-Artefakte: Namenskonventionen | HA Artifacts: Naming Conventions | draft | unversioned |
| [`claude/ha-integration-scaffold`](claude/ha-integration-scaffold/de.md) | Skill: `ha-integration-scaffold` | Skill: `ha-integration-scaffold` | draft | unversioned |
| [`claude/ha-config-flow-augment`](claude/ha-config-flow-augment/de.md) | Skill: `ha-config-flow-augment` | Skill: `ha-config-flow-augment` | draft | unversioned |
| [`claude/ha-coordinator-add`](claude/ha-coordinator-add/de.md) | Skill: `ha-coordinator-add` | Skill: `ha-coordinator-add` | draft | unversioned |
| [`claude/ha-entity-description-mapper`](claude/ha-entity-description-mapper/de.md) | Skill: `ha-entity-description-mapper` | Skill: `ha-entity-description-mapper` | draft | unversioned |
| [`claude/ha-service-definition-generator`](claude/ha-service-definition-generator/de.md) | Skill: `ha-service-definition-generator` | Skill: `ha-service-definition-generator` | draft | unversioned |
| [`claude/ha-test-harness-augment`](claude/ha-test-harness-augment/de.md) | Skill: `ha-test-harness-augment` | Skill: `ha-test-harness-augment` | draft | unversioned |
| [`claude/ha-lovelace-card-scaffold`](claude/ha-lovelace-card-scaffold/de.md) | Skill: `ha-lovelace-card-scaffold` | Skill: `ha-lovelace-card-scaffold` | draft | unversioned |
| [`claude/ha-translation-sync`](claude/ha-translation-sync/de.md) | Skill: `ha-translation-sync` | Skill: `ha-translation-sync` | draft | unversioned |
| [`claude/ha-security-audit`](claude/ha-security-audit/de.md) | Skill: `ha-security-audit` | Skill: `ha-security-audit` | draft | unversioned |
| [`claude/ha-blueprint-scaffold`](claude/ha-blueprint-scaffold/de.md) | Skill: `ha-blueprint-scaffold` | Skill: `ha-blueprint-scaffold` | draft | unversioned |

## Konventionen

- Slugs sind ASCII-kebab-case, abgeleitet aus dem kanonischen DE-Titel.
- Topic-Folder gruppieren verwandte Specs (`ha/`, `claude/`); nur eine Verschachtelungs­ebene erlaubt.
- Jede Spec lebt in genau einem Ordner mit einer Datei pro konfigurierter Sprache.
- Strukturelle Drift zwischen DE und EN wird per `nolte-shared:spec`-Skill (Operation `drift-check`) gefangen.
- RFC-2119-Schlüsselworte stehen in der DE-Fassung als `MUSS [MUST]`, `SOLLTE [SHOULD]`, `KANN [MAY]` und in der EN-Fassung als `MUST`, `SHOULD`, `MAY`.

## Adaptionsquelle

Die HA-Integration-Specs unter `spec/ha/` werden aus den Specs in [`nolte/kamerplanter-ha`](https://github.com/nolte/kamerplanter-ha) (`spec/style-guides/HA-INTEGRATION.md` + `spec/ha-integration/`) destilliert. Dabei werden domänen-spezifische Referenzen (Plants, Tanks, Tenants) generisch ersetzt; die Pattern-Substanz bleibt erhalten.

Ausnahme: `ha/blueprint-patterns` betrifft YAML-Blueprints statt Python-Integrationen und hat keine `kamerplanter-ha`-Vorlage. Diese Spec ist direkt aus der offiziellen HA-Blueprint-Doku (`home-assistant.io/docs/blueprint/`, Stand 2024–2026) plus den „Share your Blueprints"-Forum-Konventionen destilliert.

Ausnahme: Die mit der Developer-Doku-Auswertung hinzugekommenen Specs (Integration-Core wie `ha/quality-scale`/`ha/integration-manifest`/`ha/setup-lifecycle`, die `ha/entity-platform-types`- und `ha/entity-platforms-*`-Kataloge sowie die `ha/lovelace-*`- und `ha/frontend-*`-Cluster) sind aus der offiziellen HA-Developer-Doku ([`developers.home-assistant.io`](https://github.com/home-assistant/developers.home-assistant), Stand 2024–2026) destilliert statt aus `kamerplanter-ha` — primär `core/integration-quality-scale/`, `creating_integration_manifest.md`, `config_entries_index.md`, `integration_setup_failures.md`, `core/platform/*`, `core/integration/*`, `core/entity/*` (Plattform-Docs), `core/bluetooth/`, `core/llm/`, `device_automation_*`, `network_discovery.md`, `integration_*events*.md`, die `intent_*`-, `asyncio_*`- und `development_*`-Guides sowie der `frontend/`-Baum (`custom-ui/*`, `data.md`, `extending/websocket-api.md`) für die Lovelace-/Frontend-Specs. Jede Anforderung ist an einer konkreten Doc-Datei verankert.
