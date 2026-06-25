# Spezifikationen — `claude-home-assistant`

Quelle der Wahrheit hinter den Skills und Agents dieses Plugins. Specs sind zweisprachig: Englisch ist kanonisch (`en.md`), Deutsch ist Übersetzung (`de.md`). Konfiguration siehe `.spec-config.yml`.

## Index

| Slug | Titel (EN) | Titel (DE) | Status | Zuletzt aktualisiert |
|---|---|---|---|---|
| [`ha/integration-architecture`](ha/integration-architecture/en.md) | HA Integration: Architecture Foundation | HA-Integration: Architektur-Foundation | draft | unversioned |
| [`ha/runtime-data-pattern`](ha/runtime-data-pattern/en.md) | HA Integration: `runtime_data` Pattern | HA-Integration: `runtime_data`-Pattern | draft | unversioned |
| [`ha/coordinator-patterns`](ha/coordinator-patterns/en.md) | HA Integration: Coordinator Patterns | HA-Integration: Coordinator-Patterns | draft | unversioned |
| [`ha/config-flow-patterns`](ha/config-flow-patterns/en.md) | HA Integration: Config Flow Patterns | HA-Integration: Config-Flow-Patterns | draft | unversioned |
| [`ha/entity-architecture`](ha/entity-architecture/en.md) | HA Integration: Entity Architecture | HA-Integration: Entity-Architektur | draft | unversioned |
| [`ha/device-registry`](ha/device-registry/en.md) | HA Integration: Device Registry and `DeviceInfo` Hierarchy | HA-Integration: Device-Registry und `DeviceInfo`-Hierarchie | draft | unversioned |
| [`ha/services`](ha/services/en.md) | HA Integration: Services | HA-Integration: Services | draft | unversioned |
| [`ha/translations`](ha/translations/en.md) | HA Integration: Translations | HA-Integration: Translations | draft | unversioned |
| [`ha/icons`](ha/icons/en.md) | HA Integration: `icons.json` | HA-Integration: `icons.json` | draft | unversioned |
| [`ha/zeroconf-discovery`](ha/zeroconf-discovery/en.md) | HA Integration: Zeroconf Discovery | HA-Integration: Zeroconf-Discovery | draft | unversioned |
| [`ha/diagnostics`](ha/diagnostics/en.md) | HA Integration: Diagnostics | HA-Integration: Diagnostics | draft | unversioned |
| [`ha/lovelace-card-patterns`](ha/lovelace-card-patterns/en.md) | HA Integration: Lovelace Card Patterns | HA-Integration: Lovelace-Card-Patterns | draft | unversioned |
| [`ha/lovelace-card-entity-selector`](ha/lovelace-card-entity-selector/en.md) | HA Integration: Lovelace Card Entity Selector Filtering | HA-Integration: Lovelace-Card-Entity-Selector-Filter | draft | unversioned |
| [`ha/blueprint-patterns`](ha/blueprint-patterns/en.md) | HA Blueprint: Authoring Patterns | HA-Blueprint: Authoring-Patterns | draft | unversioned |
| [`ha/quality-scale`](ha/quality-scale/en.md) | HA Integration: Quality Scale | HA-Integration: Quality-Scale | draft | unversioned |
| [`ha/integration-manifest`](ha/integration-manifest/en.md) | HA Integration: `manifest.json` | HA-Integration: `manifest.json` | draft | unversioned |
| [`ha/setup-lifecycle`](ha/setup-lifecycle/en.md) | HA Integration: Setup Lifecycle | HA-Integration: Setup-Lifecycle | draft | unversioned |
| [`ha/exceptions`](ha/exceptions/en.md) | HA Integration: Exceptions and Error Translations | HA-Integration: Exceptions und Fehler-Übersetzungen | draft | unversioned |
| [`ha/repairs`](ha/repairs/en.md) | HA Integration: Repairs and Issue Registry | HA-Integration: Repairs und Issue-Registry | draft | unversioned |
| [`ha/application-credentials`](ha/application-credentials/en.md) | HA Integration: Application Credentials (OAuth2) | HA-Integration: Application Credentials (OAuth2) | draft | unversioned |
| [`ha/async-patterns`](ha/async-patterns/en.md) | HA Integration: Async Patterns | HA-Integration: Async-Patterns | draft | unversioned |
| [`ha/entity-platform-types`](ha/entity-platform-types/en.md) | HA Integration: Entity Platform Types | HA-Integration: Entity-Plattform-Typen | draft | unversioned |
| [`ha/bluetooth`](ha/bluetooth/en.md) | HA Integration: Bluetooth | HA-Integration: Bluetooth | draft | unversioned |
| [`ha/intents-conversation`](ha/intents-conversation/en.md) | HA Integration: Intents and Conversation | HA-Integration: Intents und Conversation | draft | unversioned |
| [`ha/significant-change`](ha/significant-change/en.md) | HA Integration: Significant Change | HA-Integration: Significant-Change | draft | unversioned |
| [`ha/backup-platform`](ha/backup-platform/en.md) | HA Integration: Backup Platform | HA-Integration: Backup-Platform | draft | unversioned |
| [`ha/device-automations`](ha/device-automations/en.md) | HA Integration: Device Automations | HA-Integration: Device-Automations | draft | unversioned |
| [`ha/discovery-mechanisms`](ha/discovery-mechanisms/en.md) | HA Integration: Discovery Mechanisms (DHCP/SSDP/USB/HomeKit) | HA-Integration: Discovery-Mechanismen (DHCP/SSDP/USB/HomeKit) | draft | unversioned |
| [`ha/integration-events`](ha/integration-events/en.md) | HA Integration: Events (Firing and Listening) | HA-Integration: Events (feuern und lauschen) | draft | unversioned |
| [`ha/media-source`](ha/media-source/en.md) | HA Integration: Media Source | HA-Integration: Media-Source | draft | unversioned |
| [`ha/reproduce-state`](ha/reproduce-state/en.md) | HA Integration: Reproduce State (Scene Support) | HA-Integration: Reproduce-State (Scene-Support) | draft | unversioned |
| [`ha/system-health`](ha/system-health/en.md) | HA Integration: System Health | HA-Integration: System-Health | draft | unversioned |
| [`ha/llm-api`](ha/llm-api/en.md) | HA Integration: LLM API (Tools for Conversation Agents) | HA-Integration: LLM-API (Tools für Conversation-Agents) | draft | unversioned |
| [`ha/dev-workflow`](ha/dev-workflow/en.md) | HA Integration: Dev Workflow (Guidelines, Typing, Validation) | HA-Integration: Dev-Workflow (Guidelines, Typing, Validation) | draft | unversioned |
| [`ha/entity-platforms-controls`](ha/entity-platforms-controls/en.md) | HA Integration: Entity Platforms (Controls) | HA-Integration: Entity-Plattformen (Controls) | draft | unversioned |
| [`ha/entity-platforms-climate`](ha/entity-platforms-climate/en.md) | HA Integration: Entity Platforms (Climate Family) | HA-Integration: Entity-Plattformen (Klima-Familie) | draft | unversioned |
| [`ha/entity-platforms-inputs`](ha/entity-platforms-inputs/en.md) | HA Integration: Entity Platforms (Input Helpers) | HA-Integration: Entity-Plattformen (Input-Helfer) | draft | unversioned |
| [`ha/entity-platforms-sensors`](ha/entity-platforms-sensors/en.md) | HA Integration: Entity Platforms (Sensors) | HA-Integration: Entity-Plattformen (Sensorik) | draft | unversioned |
| [`ha/entity-platforms-media`](ha/entity-platforms-media/en.md) | HA Integration: Entity Platforms (Media) | HA-Integration: Entity-Plattformen (Media) | draft | unversioned |
| [`ha/entity-platforms-voice`](ha/entity-platforms-voice/en.md) | HA Integration: Entity Platforms (Voice & AI) | HA-Integration: Entity-Plattformen (Voice & AI) | draft | unversioned |
| [`ha/entity-platforms-devices`](ha/entity-platforms-devices/en.md) | HA Integration: Entity Platforms (Device Domains) | HA-Integration: Entity-Plattformen (Geräte-Domänen) | draft | unversioned |
| [`ha/lovelace-card-editor`](ha/lovelace-card-editor/en.md) | HA Integration: Lovelace Card Editor (`ha-form`) | HA-Integration: Lovelace-Card-Editor (`ha-form`) | draft | unversioned |
| [`ha/lovelace-card-features`](ha/lovelace-card-features/en.md) | HA Integration: Lovelace Card Features (Tile Features) | HA-Integration: Lovelace-Card-Features (Tile-Features) | draft | unversioned |
| [`ha/lovelace-badges`](ha/lovelace-badges/en.md) | HA Integration: Lovelace Badges | HA-Integration: Lovelace-Badges | draft | unversioned |
| [`ha/lovelace-strategies`](ha/lovelace-strategies/en.md) | HA Integration: Lovelace Strategies | HA-Integration: Lovelace-Strategies | draft | unversioned |
| [`ha/lovelace-views-panels`](ha/lovelace-views-panels/en.md) | HA Integration: Lovelace Views and Custom Panels | HA-Integration: Lovelace-Views und Custom-Panels | draft | unversioned |
| [`ha/frontend-data-api`](ha/frontend-data-api/en.md) | HA Integration: Frontend Data API (`hass` object) | HA-Integration: Frontend-Data-API (`hass`-Objekt) | draft | unversioned |
| [`ha/frontend-websocket-commands`](ha/frontend-websocket-commands/en.md) | HA Integration: Frontend WebSocket Commands | HA-Integration: Frontend-WebSocket-Commands | draft | unversioned |
| [`ha/security-hardening`](ha/security-hardening/en.md) | HA Integration: Security Hardening | HA-Integration: Security-Hardening | draft | unversioned |
| [`ha/test-harness`](ha/test-harness/en.md) | HA Integration: Test Harness | HA-Integration: Test-Harness | draft | unversioned |
| [`ha/dev-environment`](ha/dev-environment/en.md) | HA Integration: Dev Environment | HA-Integration: Dev-Environment | draft | unversioned |
| [`ha/dev-instance-provisioning`](ha/dev-instance-provisioning/en.md) | HA Integration: Dev Instance Provisioning | HA-Integration: Dev-Instanz-Provisioning | draft | unversioned |
| [`ha/naming-conventions`](ha/naming-conventions/en.md) | HA Artifacts: Naming Conventions | HA-Artefakte: Namenskonventionen | draft | unversioned |
| [`ha/hacs-release`](ha/hacs-release/en.md) | HA Integration: HACS Release and Distribution | HA-Integration: HACS-Release und Distribution | draft | unversioned |
| [`ha/upstream-docs-verification`](ha/upstream-docs-verification/en.md) | HA Artifacts: Verification Against Official Docs | HA-Artefakte: Verifikation gegen offizielle Docs | draft | unversioned |
| [`ha/divoom-pixoo`](ha/divoom-pixoo/en.md) | HA Device: Divoom Pixoo 64 (gickowtf integration) | HA-Gerät: Divoom Pixoo 64 (gickowtf-Integration) | draft | unversioned |
| [`ha/pixoo-pixel-art`](ha/pixoo-pixel-art/en.md) | HA Device: Pixel Art on the 64×64 Matrix (Shading & Contours) | HA-Gerät: Pixel-Art auf der 64×64-Matrix (Schattierung & Konturen) | draft | unversioned |
| [`ha/pixoo-pixel-art-animation`](ha/pixoo-pixel-art-animation/en.md) | HA Device: Pixel Art Animation on the 64×64 Matrix | HA-Gerät: Pixel-Art-Animation auf der 64×64-Matrix | draft | unversioned |
| [`ha-automation/automation`](ha-automation/automation/en.md) | HA Automation: Using Automation | HA-Automation: Automation nutzen | draft | unversioned |
| [`ha-automation/script`](ha-automation/script/en.md) | HA Automation: Using Script | HA-Automation: Script nutzen | draft | unversioned |
| [`ha-automation/scene`](ha-automation/scene/en.md) | HA Automation: Using Scene | HA-Automation: Scene nutzen | draft | unversioned |
| [`ha-automation/template`](ha-automation/template/en.md) | HA Automation: Using the Template Integration | HA-Automation: Template-Integration nutzen | draft | unversioned |
| [`ha-automation/group`](ha-automation/group/en.md) | HA Automation: Using Group | HA-Automation: Group nutzen | draft | unversioned |
| [`ha-automation/input-boolean`](ha-automation/input-boolean/en.md) | HA Automation: Using input_boolean | HA-Automation: input_boolean nutzen | draft | unversioned |
| [`ha-automation/input-button`](ha-automation/input-button/en.md) | HA Automation: Using input_button | HA-Automation: input_button nutzen | draft | unversioned |
| [`ha-automation/input-datetime`](ha-automation/input-datetime/en.md) | HA Automation: Using input_datetime | HA-Automation: input_datetime nutzen | draft | unversioned |
| [`ha-automation/input-number`](ha-automation/input-number/en.md) | HA Automation: Using input_number | HA-Automation: input_number nutzen | draft | unversioned |
| [`ha-automation/input-select`](ha-automation/input-select/en.md) | HA Automation: Using input_select | HA-Automation: input_select nutzen | draft | unversioned |
| [`ha-automation/input-text`](ha-automation/input-text/en.md) | HA Automation: Using input_text | HA-Automation: input_text nutzen | draft | unversioned |
| [`ha-automation/timer`](ha-automation/timer/en.md) | HA Automation: Using Timer | HA-Automation: Timer nutzen | draft | unversioned |
| [`ha-automation/counter`](ha-automation/counter/en.md) | HA Automation: Using Counter | HA-Automation: Counter nutzen | draft | unversioned |
| [`ha-automation/schedule`](ha-automation/schedule/en.md) | HA Automation: Using Schedule | HA-Automation: Schedule nutzen | draft | unversioned |
| [`ha-automation/python-script`](ha-automation/python-script/en.md) | HA Automation: Using Python Script | HA-Automation: Python Script nutzen | draft | unversioned |
| [`ha-automation/shell-command`](ha-automation/shell-command/en.md) | HA Automation: Using Shell Command | HA-Automation: Shell Command nutzen | draft | unversioned |
| [`ha-automation/rest-command`](ha-automation/rest-command/en.md) | HA Automation: Using REST Command | HA-Automation: REST Command nutzen | draft | unversioned |
| [`ha-automation/derivative`](ha-automation/derivative/en.md) | HA Automation: Using Derivative | HA-Automation: Derivative nutzen | draft | unversioned |
| [`ha-automation/integration-riemann`](ha-automation/integration-riemann/en.md) | HA Automation: Using Integration (Riemann Sum) | HA-Automation: Integration (Riemann-Summe) nutzen | draft | unversioned |
| [`ha-automation/utility-meter`](ha-automation/utility-meter/en.md) | HA Automation: Using Utility Meter | HA-Automation: Utility Meter nutzen | draft | unversioned |
| [`ha-automation/statistics`](ha-automation/statistics/en.md) | HA Automation: Using the Statistics Sensor | HA-Automation: Statistics-Sensor nutzen | draft | unversioned |
| [`ha-automation/threshold`](ha-automation/threshold/en.md) | HA Automation: Using Threshold | HA-Automation: Threshold nutzen | draft | unversioned |
| [`ha-automation/trend`](ha-automation/trend/en.md) | HA Automation: Using Trend | HA-Automation: Trend nutzen | draft | unversioned |
| [`ha-automation/history-stats`](ha-automation/history-stats/en.md) | HA Automation: Using history_stats | HA-Automation: history_stats nutzen | draft | unversioned |
| [`ha-automation/min-max`](ha-automation/min-max/en.md) | HA Automation: Using min_max | HA-Automation: min_max nutzen | draft | unversioned |
| [`ha-automation/bayesian`](ha-automation/bayesian/en.md) | HA Automation: Using the Bayesian Sensor | HA-Automation: Bayesian-Sensor nutzen | draft | unversioned |
| [`ha-automation/filter`](ha-automation/filter/en.md) | HA Automation: Using the Filter Sensor | HA-Automation: Filter-Sensor nutzen | draft | unversioned |
| [`ha-automation/legacy-trigger-helpers`](ha-automation/legacy-trigger-helpers/en.md) | HA Automation: Avoiding Legacy Trigger Helpers | HA-Automation: Legacy-Trigger-Helfer vermeiden | draft | unversioned |
| [`claude/ha-integration-scaffold`](claude/ha-integration-scaffold/en.md) | Skill: `ha-integration-scaffold` | Skill: `ha-integration-scaffold` | draft | unversioned |
| [`claude/ha-config-flow-augment`](claude/ha-config-flow-augment/en.md) | Skill: `ha-config-flow-augment` | Skill: `ha-config-flow-augment` | draft | unversioned |
| [`claude/ha-coordinator-add`](claude/ha-coordinator-add/en.md) | Skill: `ha-coordinator-add` | Skill: `ha-coordinator-add` | draft | unversioned |
| [`claude/ha-entity-description-mapper`](claude/ha-entity-description-mapper/en.md) | Skill: `ha-entity-description-mapper` | Skill: `ha-entity-description-mapper` | draft | unversioned |
| [`claude/ha-service-definition-generator`](claude/ha-service-definition-generator/en.md) | Skill: `ha-service-definition-generator` | Skill: `ha-service-definition-generator` | draft | unversioned |
| [`claude/ha-test-harness-augment`](claude/ha-test-harness-augment/en.md) | Skill: `ha-test-harness-augment` | Skill: `ha-test-harness-augment` | draft | unversioned |
| [`claude/ha-lovelace-card-scaffold`](claude/ha-lovelace-card-scaffold/en.md) | Skill: `ha-lovelace-card-scaffold` | Skill: `ha-lovelace-card-scaffold` | draft | unversioned |
| [`claude/ha-translation-sync`](claude/ha-translation-sync/en.md) | Skill: `ha-translation-sync` | Skill: `ha-translation-sync` | draft | unversioned |
| [`claude/ha-security-audit`](claude/ha-security-audit/en.md) | Skill: `ha-security-audit` | Skill: `ha-security-audit` | draft | unversioned |
| [`claude/ha-quality-scale-audit`](claude/ha-quality-scale-audit/en.md) | Skill: `ha-quality-scale-audit` | Skill: `ha-quality-scale-audit` | draft | unversioned |
| [`claude/ha-blueprint-scaffold`](claude/ha-blueprint-scaffold/en.md) | Skill: `ha-blueprint-scaffold` | Skill: `ha-blueprint-scaffold` | draft | unversioned |
| [`claude/ha-automation-solution`](claude/ha-automation-solution/en.md) | Skill: `ha-automation-solution` | Skill: `ha-automation-solution` | draft | unversioned |
| [`claude/ha-automation-author`](claude/ha-automation-author/en.md) | Skill: `ha-automation-author` | Skill: `ha-automation-author` | draft | unversioned |
| [`claude/ha-helper-scaffold`](claude/ha-helper-scaffold/en.md) | Skill: `ha-helper-scaffold` | Skill: `ha-helper-scaffold` | draft | unversioned |
| [`claude/ha-derived-sensor-author`](claude/ha-derived-sensor-author/en.md) | Skill: `ha-derived-sensor-author` | Skill: `ha-derived-sensor-author` | draft | unversioned |
| [`claude/ha-repairs-add`](claude/ha-repairs-add/en.md) | Skill: `ha-repairs-add` | Skill: `ha-repairs-add` | draft | unversioned |
| [`claude/ha-discovery-augment`](claude/ha-discovery-augment/en.md) | Skill: `ha-discovery-augment` | Skill: `ha-discovery-augment` | draft | unversioned |
| [`claude/ha-device-automation-add`](claude/ha-device-automation-add/en.md) | Skill: `ha-device-automation-add` | Skill: `ha-device-automation-add` | draft | unversioned |
| [`claude/ha-oauth2-credentials-augment`](claude/ha-oauth2-credentials-augment/en.md) | Skill: `ha-oauth2-credentials-augment` | Skill: `ha-oauth2-credentials-augment` | draft | unversioned |
| [`claude/ha-bluetooth-augment`](claude/ha-bluetooth-augment/en.md) | Skill: `ha-bluetooth-augment` | Skill: `ha-bluetooth-augment` | draft | unversioned |
| [`claude/ha-conversation-agent-augment`](claude/ha-conversation-agent-augment/en.md) | Skill: `ha-conversation-agent-augment` | Skill: `ha-conversation-agent-augment` | draft | unversioned |
| [`claude/ha-diagnostics-augment`](claude/ha-diagnostics-augment/en.md) | Skill: `ha-diagnostics-augment` | Skill: `ha-diagnostics-augment` | draft | unversioned |
| [`claude/ha-integration-events-add`](claude/ha-integration-events-add/en.md) | Skill: `ha-integration-events-add` | Skill: `ha-integration-events-add` | draft | unversioned |
| [`claude/ha-system-health-add`](claude/ha-system-health-add/en.md) | Skill: `ha-system-health-add` | Skill: `ha-system-health-add` | draft | unversioned |
| [`claude/ha-media-source-add`](claude/ha-media-source-add/en.md) | Skill: `ha-media-source-add` | Skill: `ha-media-source-add` | draft | unversioned |
| [`claude/ha-reproduce-state-add`](claude/ha-reproduce-state-add/en.md) | Skill: `ha-reproduce-state-add` | Skill: `ha-reproduce-state-add` | draft | unversioned |
| [`claude/ha-significant-change-add`](claude/ha-significant-change-add/en.md) | Skill: `ha-significant-change-add` | Skill: `ha-significant-change-add` | draft | unversioned |
| [`claude/ha-backup-platform-add`](claude/ha-backup-platform-add/en.md) | Skill: `ha-backup-platform-add` | Skill: `ha-backup-platform-add` | draft | unversioned |
| [`claude/ha-entity-platform-add`](claude/ha-entity-platform-add/en.md) | Skill: `ha-entity-platform-add` | Skill: `ha-entity-platform-add` | draft | unversioned |
| [`claude/ha-card-editor-add`](claude/ha-card-editor-add/en.md) | Skill: `ha-card-editor-add` | Skill: `ha-card-editor-add` | draft | unversioned |
| [`claude/ha-card-features-add`](claude/ha-card-features-add/en.md) | Skill: `ha-card-features-add` | Skill: `ha-card-features-add` | draft | unversioned |
| [`claude/ha-badge-add`](claude/ha-badge-add/en.md) | Skill: `ha-badge-add` | Skill: `ha-badge-add` | draft | unversioned |
| [`claude/ha-strategy-add`](claude/ha-strategy-add/en.md) | Skill: `ha-strategy-add` | Skill: `ha-strategy-add` | draft | unversioned |
| [`claude/ha-panel-add`](claude/ha-panel-add/en.md) | Skill: `ha-panel-add` | Skill: `ha-panel-add` | draft | unversioned |
| [`claude/ha-websocket-command-add`](claude/ha-websocket-command-add/en.md) | Skill: `ha-websocket-command-add` | Skill: `ha-websocket-command-add` | draft | unversioned |
| [`claude/ha-integration-solution`](claude/ha-integration-solution/en.md) | Skill: `ha-integration-solution` | Skill: `ha-integration-solution` | draft | unversioned |
| [`claude/ha-lovelace-solution`](claude/ha-lovelace-solution/en.md) | Skill: `ha-lovelace-solution` | Skill: `ha-lovelace-solution` | draft | unversioned |

Der Index listet nur **lokale** Specs. Portfolioweite `project/`-Specs (u. a. `project/branching-model`, `project/parallel-working-copies`) werden nicht mehr lokal geführt, sondern aus dem nolte-shared-Hub vererbt — siehe [Vererbte Specs](#vererbte-specs).

## Konventionen

- Slugs sind ASCII-kebab-case, abgeleitet aus dem kanonischen EN-Titel.
- Topic-Folder gruppieren verwandte Specs (`ha/`, `ha-automation/`, `claude/`); nur eine Verschachtelungs­ebene erlaubt.
- Jede Spec lebt in genau einem Ordner mit einer Datei pro konfigurierter Sprache.
- Strukturelle Drift zwischen DE und EN wird per `nolte-shared:spec`-Skill (Operation `drift-check`) gefangen.
- RFC-2119-Schlüsselworte stehen in der DE-Fassung als `MUSS [MUST]`, `SOLLTE [SHOULD]`, `KANN [MAY]` und in der EN-Fassung als `MUST`, `SHOULD`, `MAY`.
- Unklarheiten über HA-Internals werden gegen die offizielle HA-Doku geprüft, bevor sie in eine Spec eingehen — die querschnittliche Pflicht definiert [`ha/upstream-docs-verification`](ha/upstream-docs-verification/de.md).

## Vererbte Specs

Portfolioweite Specs werden gemäß `spec/project/portfolio-inherited-spec-layer/` (nolte/claude-shared#339) **referenziert statt kopiert**: Sie leben kanonisch einmal im `nolte-shared`-Hub und werden über den `inherits:`-Block in [`.spec-config.yml`](.spec-config.yml) eingebunden, gepinnt auf einen Hub-Release-`ref`. Eine verbatim kopierte Hub-Spec im lokalen `spec/`-Baum ist laut dieser Spec ein Critical-Befund.

Vererbt (sobald der gepinnte Hub-Release sie als `Portfolio-Scope: portfolio` ausliefert): `project/branching-model`, `project/parallel-working-copies` samt des von ihnen referenzierten Schwester-Spec-Clusters. Abweichungen würden als deklarierte `overrides:` in `.spec-config.yml` geführt; aktuell sind keine nötig.

## Adaptionsquelle

Die HA-Integration-Specs unter `spec/ha/` werden aus den Specs in [`nolte/kamerplanter-ha`](https://github.com/nolte/kamerplanter-ha) (`spec/style-guides/HA-INTEGRATION.md` + `spec/ha-integration/`) destilliert. Dabei werden domänen-spezifische Referenzen (Plants, Tanks, Tenants) generisch ersetzt; die Pattern-Substanz bleibt erhalten.

Ausnahme: `ha/blueprint-patterns` betrifft YAML-Blueprints statt Python-Integrationen und hat keine `kamerplanter-ha`-Vorlage. Diese Spec ist direkt aus der offiziellen HA-Blueprint-Doku (`home-assistant.io/docs/blueprint/`, Stand 2024–2026) plus den „Share your Blueprints"-Forum-Konventionen destilliert.

Ausnahme: Die mit der Developer-Doku-Auswertung hinzugekommenen Specs (Integration-Core wie `ha/quality-scale`/`ha/integration-manifest`/`ha/setup-lifecycle`, die `ha/entity-platform-types`- und `ha/entity-platforms-*`-Kataloge sowie die `ha/lovelace-*`- und `ha/frontend-*`-Cluster) sind aus der offiziellen HA-Developer-Doku ([`developers.home-assistant.io`](https://github.com/home-assistant/developers.home-assistant), Stand 2024–2026) destilliert statt aus `kamerplanter-ha` — primär `core/integration-quality-scale/`, `creating_integration_manifest.md`, `config_entries_index.md`, `integration_setup_failures.md`, `core/platform/*`, `core/integration/*`, `core/entity/*` (Plattform-Docs), `core/bluetooth/`, `core/llm/`, `device_automation_*`, `network_discovery.md`, `integration_*events*.md`, die `intent_*`-, `asyncio_*`- und `development_*`-Guides sowie der `frontend/`-Baum (`custom-ui/*`, `data.md`, `extending/websocket-api.md`) für die Lovelace-/Frontend-Specs. Jede Anforderung ist an einer konkreten Doc-Datei verankert.

Eigener Topic `spec/ha-automation/`: Anders als der `ha/`-Korpus (Integrations-**Entwicklung** in Python) beschreibt `ha-automation/` die **Nutzung** der eingebauten Automatisierungs-/Helfer-Integrationen auf Konfigurationsebene (YAML/UI) — die Grundlage für hochwertige Automationen und Dashboards. Scope ist ziel-orientiert kuratiert (Kern-Bausteine `automation`/`script`/`scene`/`template`/`group`, die `input_*`-/`timer`/`counter`/`schedule`-Helfer, die Command-Runner `python_script`/`shell_command`/`rest_command` und die berechneten Helfer-Sensoren `derivative`/`integration`/`utility_meter`/`statistics`/`threshold`/`trend`/`history_stats`/`min_max`/`bayesian`/`filter`), nicht die wörtliche HA-Kategorie „Automation" (der die Kern-Bausteine fehlen und die echte Legacy enthält). Jede Spec trägt eine verpflichtende Abgrenzung „Wann NICHT verwenden" mit Begründung und benannter Alternative, nennt ihre reale `ha_category` ehrlich und referenziert die Namens-Dimension `ha/naming-conventions`. Die Specs sind direkt aus der offiziellen HA-Nutzer-Doku ([`home-assistant.io`](https://github.com/home-assistant/home-assistant.io), `/integrations/<domain>/` + `/docs/automation/`, `/docs/scripts/`, `/docs/configuration/templating/`, Stand 2026) destilliert; jede Anforderung ist an einer konkreten Doc-Seite verankert.
