# Eine Custom Integration bauen (Python)

Eine vollständige Custom Integration unter `custom_components/<domain>/`, über HACS installierbar — vom leeren Ordner zu einem Skeleton mit Manifest, Config-Flow, Coordinator, Entities und pytest-Harness, danach erweitert um die fortgeschrittenen Plattform-Features, die eine ausgereifte Integration braucht.

## Anwendungsfälle

- Du willst eine REST- oder WebSocket-**Cloud-API** als vollwertige Integration kapseln: einen Config-Flow für die Zugangsdaten, einen `DataUpdateCoordinator`, der nach einem Zeitplan pollt, und Sensor-/Switch-Entities auf Basis der abgerufenen Daten.
- Du willst mit einem **lokalen Gerät** sprechen — Bluetooth, mDNS/Zeroconf oder ein LAN-HTTP-Endpunkt — und möchtest, dass Home Assistant es automatisch erkennt, statt manuelle Einrichtung zu erzwingen.
- Du hast eine laufende Integration und willst sie jetzt **ausbauen**: eine zweite Entity-Plattform ergänzen, einen registrierten Service anbieten, einen Options-Flow hinzufügen, damit Nutzer sie ohne Löschen des Entrys neu einstellen können, oder einen Config-Entry auf eine neue Schema-Version migrieren, ohne bestehende Installationen zu zerstören.
- Du bereitest eine Integration für die **HACS-Distribution** vor und willst das vollständige Skeleton — Übersetzungen, Icons, Diagnostics, einen Repairs-Flow und System-Health — von Anfang an korrekt haben, statt es später nachzurüsten.
- Du treibst eine bestehende Komponente auf der **HA-Quality-Scale** nach oben und brauchst die Feinarbeit vom Bronze-Boden bis Platinum. Dazu zählen striktes Typing, Diagnostics-Redaction, Reproduce-State, Significant-Change und ein Test-Harness, der die sekundären Code-Pfade abdeckt.

## Zielgruppen

- **Python-Entwickler, die ein Gerät oder eine Cloud-API kapseln.** Du kannst Python, aber nicht zwangsläufig jeden Home-Assistant-Vertrag (Config-Entry-Lifecycle, Coordinator-Semantik, Entity-Registry). Dieser Anwendungsfall gibt Dir ein idiomatisches Skeleton und fokussierte Augment-Skills, damit Du Integrationslogik schreibst statt Boilerplate.
- **Contributor mit Ziel HACS-Distribution.** Du willst ein Repository-Layout und ein Manifest, die HACS akzeptiert, mit Übersetzungen, Icons und Diagnostics von Anfang an. Das Scaffold erzeugt eine HACS-installierbare Komponente; `ha-hacs-release` übernimmt die Release-Seite.
- **Maintainer, die die Quality-Scale hochklettern.** Du lieferst bereits eine Integration aus und willst eine höhere Stufe erreichen. Die Augment-Skills ergänzen genau die Plattformen und Features, die eine Stufe verlangt (Repairs, System-Health, Reproduce-State, Significant-Change, Backup), und `ha-quality-scale-audit` sagt Dir, wo Du stehst.

## Zusammenspiel von Skills und Agents

Die Front-Door `ha-integration-solution` plant die Arbeit und dispatcht fokussierte Skills; jeder fokussierte Skill besitzt genau ein Artefakt und seine eigene Spec-Konformität.

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

Beschreibe die gewünschte Integration, und `ha-integration-solution` zerlegt sie in ein Skeleton plus die nötigen Augment-, Quality- und Code-Style-Schritte und dispatcht jeden davon. `ha-integration-scaffold` legt das installierbare Skeleton an; die Augment-Skills ergänzen je ein Plattform-Feature; `ha-translation-sync` und `ha-test-harness-augment` halten Übersetzungen und Tests ehrlich; `ha-dev-workflow-apply` erzwingt Format, Typing und Validierung. Von hier führen die natürlichen Übergaben zu [Auf einer Dev-HA ausführen und testen](dev-testing.md) und danach zu [Review und Härtung vor dem Release](review-hardening.md).

## Eingesetzte Skills und Agents

- **Front-Door:** `ha-integration-solution`
- **Bausteine:** `ha-integration-scaffold` (Skeleton: Manifest, Lifecycle, Config-Flow, Coordinator, Entity, Plattformen, Übersetzungen, Icons, Diagnostics, pytest-Harness); Augment-Skills `ha-config-flow-augment`, `ha-options-flow-augment`, `ha-config-entry-migrate`, `ha-coordinator-add`, `ha-entity-platform-add`, `ha-entity-description-map`, `ha-service-definition-add`, `ha-diagnostics-augment`, `ha-discovery-augment`, `ha-bluetooth-augment`, `ha-oauth2-credentials-augment`, `ha-device-registry-augment`, `ha-repairs-add`, `ha-system-health-add`, `ha-backup-platform-add`, `ha-media-source-add`, `ha-significant-change-add`, `ha-reproduce-state-add`, `ha-integration-events-add`, `ha-conversation-agent-augment`; Quality `ha-translation-sync`, `ha-test-harness-augment`; Code-Style und Validierung `ha-dev-workflow-apply`
- **Verwandte Anwendungsfälle:** [Auf einer Dev-HA ausführen und testen](dev-testing.md), [Review und Härtung vor dem Release](review-hardening.md)

Den vollständigen Katalog findest Du unter [Skills](../skills/index.md) und [Agents](../agents/index.md).

## Specs

- `spec/ha/integration-architecture`
- `spec/ha/config-flow-patterns`
- `spec/ha/coordinator-patterns`
- `spec/ha/entity-architecture`
- `spec/ha/dev-workflow`
- und die weiteren `spec/ha/*` Integration-Themen
