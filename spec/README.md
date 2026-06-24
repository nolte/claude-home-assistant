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
| [`ha/security-hardening`](ha/security-hardening/de.md) | HA-Integration: Security-Hardening | HA Integration: Security Hardening | draft | unversioned |
| [`ha/test-harness`](ha/test-harness/de.md) | HA-Integration: Test-Harness | HA Integration: Test Harness | draft | unversioned |
| [`ha/dev-environment`](ha/dev-environment/de.md) | HA-Integration: Dev-Environment | HA Integration: Dev Environment | draft | unversioned |
| [`ha/dev-instance-provisioning`](ha/dev-instance-provisioning/de.md) | HA-Integration: Dev-Instanz-Provisioning | HA Integration: Dev Instance Provisioning | draft | unversioned |
| [`claude/ha-integration-scaffold`](claude/ha-integration-scaffold/de.md) | Skill: `ha-integration-scaffold` | Skill: `ha-integration-scaffold` | draft | unversioned |
| [`claude/ha-config-flow-augment`](claude/ha-config-flow-augment/de.md) | Skill: `ha-config-flow-augment` | Skill: `ha-config-flow-augment` | draft | unversioned |
| [`claude/ha-coordinator-add`](claude/ha-coordinator-add/de.md) | Skill: `ha-coordinator-add` | Skill: `ha-coordinator-add` | draft | unversioned |
| [`claude/ha-entity-description-mapper`](claude/ha-entity-description-mapper/de.md) | Skill: `ha-entity-description-mapper` | Skill: `ha-entity-description-mapper` | draft | unversioned |
| [`claude/ha-service-definition-generator`](claude/ha-service-definition-generator/de.md) | Skill: `ha-service-definition-generator` | Skill: `ha-service-definition-generator` | draft | unversioned |
| [`claude/ha-test-harness-augment`](claude/ha-test-harness-augment/de.md) | Skill: `ha-test-harness-augment` | Skill: `ha-test-harness-augment` | draft | unversioned |
| [`claude/ha-lovelace-card-scaffold`](claude/ha-lovelace-card-scaffold/de.md) | Skill: `ha-lovelace-card-scaffold` | Skill: `ha-lovelace-card-scaffold` | draft | unversioned |
| [`claude/ha-translation-sync`](claude/ha-translation-sync/de.md) | Skill: `ha-translation-sync` | Skill: `ha-translation-sync` | draft | unversioned |
| [`claude/ha-security-audit`](claude/ha-security-audit/de.md) | Skill: `ha-security-audit` | Skill: `ha-security-audit` | draft | unversioned |

## Konventionen

- Slugs sind ASCII-kebab-case, abgeleitet aus dem kanonischen DE-Titel.
- Topic-Folder gruppieren verwandte Specs (`ha/`, `claude/`); nur eine Verschachtelungs­ebene erlaubt.
- Jede Spec lebt in genau einem Ordner mit einer Datei pro konfigurierter Sprache.
- Strukturelle Drift zwischen DE und EN wird per `nolte-shared:spec`-Skill (Operation `drift-check`) gefangen.
- RFC-2119-Schlüsselworte stehen in der DE-Fassung als `MUSS [MUST]`, `SOLLTE [SHOULD]`, `KANN [MAY]` und in der EN-Fassung als `MUST`, `SHOULD`, `MAY`.

## Adaptionsquelle

Die HA-Specs unter `spec/ha/` werden aus den Specs in [`nolte/kamerplanter-ha`](https://github.com/nolte/kamerplanter-ha) (`spec/style-guides/HA-INTEGRATION.md` + `spec/ha-integration/`) destilliert. Dabei werden domänen-spezifische Referenzen (Plants, Tanks, Tenants) generisch ersetzt; die Pattern-Substanz bleibt erhalten.
