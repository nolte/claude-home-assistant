# Skill: `ha-integration-solution`

Status: draft

## Kontext

Die Integration-Skill-Familie zerfällt in über zwanzig eng gefasste Einzel-Skills, die je **einen** Backend-Baustein einer Python-Custom-Integration ergänzen: `ha-integration-scaffold` legt das Skelett an (Manifest, `__init__`, Config-Entry, RuntimeData), `ha-config-flow-augment` und `ha-coordinator-add` bauen das Fundament aus, `ha-entity-description-mapper` und `ha-entity-platform-add` erzeugen Entities, und eine breite Schicht aus `ha-service-definition-generator`, `ha-integration-events-add`, `ha-device-automation-add`, `ha-discovery-augment`, `ha-bluetooth-augment`, `ha-diagnostics-augment`, `ha-repairs-add`, `ha-system-health-add`, `ha-significant-change-add`, `ha-backup-platform-add`, `ha-media-source-add`, `ha-reproduce-state-add` und `ha-conversation-agent-augment` ergänzt Aktionen, Oberflächen, Robustheit und Qualitätsmerkmale. `ha-translation-sync` und `ha-test-harness-augment` schließen i18n und Tests ab; `ha-quality-scale-audit` und `ha-security-audit` prüfen read-only.

Reale Geräte-/Cloud-/API-Anforderungen sind aber fast nie ein einzelner Baustein: „Integriere meinen Acme-Thermostat über seine Cloud-API" ist eine Kette aus Scaffold → OAuth2/Config-Flow → Coordinator → Climate-Entity → Diagnostics → Translations → Tests → Review. Ein Nutzer, der die Skill-Landschaft nicht kennt, müsste diese Zerlegung selbst leisten — welcher Skill, in welcher Reihenfolge, welche `domain` und welche `entity_id` thread sich durch welchen Schritt. Genau diese Mapping-Last soll der Nutzer nicht tragen.

Dieser Skill ist die **vorgelagerte Planungs- und Dispatch-Schicht** für den Integration-Backend-Cluster — das Integration-seitige Gegenstück zu `ha-automation-solution`. Er nimmt eine unscharfe Geräte-/Cloud-/API-Anforderung, zerlegt sie in die minimale abhängigkeits-geordnete Menge von Integration-Skills, legt die Reihenfolge fest, bestätigt den Plan mit dem Nutzer und dispatcht dann die zuständigen Einzel-Skills nacheinander, wobei er die `domain` und die `entity_id`s/Datei-Pfade früherer Schritte als Eingaben der späteren durchreicht. Er generiert **selbst kein** Artefakt — die Generierung und Spec-Konformität bleiben bei den Einzel-Skills.

## Scope

Planung und Orchestrierung über den Integration-Backend-Cluster. Eine Anforderung pro Lauf → ein abhängigkeits-geordneter Skill-Plan → N dispatchte Einzel-Aufrufe → ein Gesamt-Bericht. Der Skill entscheidet die *Kombination* (welche Skills, welche Reihenfolge, welche Verdrahtung über `domain`/`entity_id`), nicht den Inhalt eines einzelnen Bausteins. Die typische Reihenfolge: scaffold → (config-flow + coordinator [+ oauth2]) → entities → [services/events/device-automation/diagnostics/repairs/discovery/bluetooth/system-health/significant-change/backup-platform/media-source/reproduce-state/conversation nach Bedarf] → translations → tests → review.

## Ziele

- Aus einer Prosa-Anforderung die richtige *Kombination* von Integration-Skills ableiten, ohne dass der Nutzer die Skill-Landschaft kennen muss
- Einen abarbeitbaren abhängigkeits-geordneten Plan erstellen (pro Eintrag: Schritt, Baustein, zuständiger Skill, Abhängigkeit, Zweck) und vor jeder Generierung bestätigen lassen
- Die Einzel-Skills in korrekter Reihenfolge dispatchen und die `domain` sowie die `entity_id`s/Datei-Pfade früherer Schritte als Eingaben der späteren durchreichen
- Anforderungen, die in Wahrheit YAML-Automation-förmig sind (kein eigenes Protokoll, keine Config-Flow-Integration), als solche erkennen und an `ha-automation-solution` verweisen statt sie in eine Integration zu pressen
- Einen Gesamt-Bericht liefern, der alle erzeugten/geänderten Dateien und ihre Verdrahtung benennt und die Read-only-Review-Berichte weiterreicht

## Nicht-Ziele

- Die Generierung eines einzelnen Bausteins samt Spec-Konformität — das bleibt bei den dispatchten Einzel-Skills
- Eine reine YAML-Automation-/Helfer-Lösung — das ist `ha-automation-solution`
- Eine Lovelace-Frontend-Lösung — das ist `ha-lovelace-card-scaffold` (und die zugehörige Lovelace-Skill-Familie)
- Deployment in eine laufende HA-Instanz oder Laufzeit-Verifikation als Teil des Standard-Generierungslaufs — das läuft über die `ha-integration-deploy`- / `ha-integration-verify`-Agenten und nur innerhalb der Opt-in-`deploy_ready`-Lifecycle-Phase hinter einem zweiten Gate (außerhalb des Generierungs-only-Scopes)
- Eine eigene Validierungs- oder Konformitäts-Logik — jeder dispatchte Skill validiert sein eigenes Artefakt; dieser Skill aggregiert nur die Berichte

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf zusammengesetzte, lösungsorientierte Geräte-/Cloud-/API-Anfragen aktivieren, bei denen der Nutzer das Ergebnis, nicht den Baustein beschreibt:
  - „build an integration for device/API X", „scaffold and wire up a full custom integration for …", „integrate my Acme thermostat over its cloud API"
  - „baue mir eine Integration für …", „richte eine Custom-Integration für … ein"
- **SOLLTE NICHT [SHOULD NOT]** aktivieren, wenn die Anforderung klar ein einzelner Augment ist (dann greift direkt der zuständige Einzel-Skill); im Zweifel plant dieser Skill und schlägt einen Ein-Schritt-Plan vor

### Eingaben

- **MUSS [MUST]** erfassen: `requirement` (Prosa, das gewünschte Geräte-/Cloud-/API-Ergebnis)
- **KANN [MAY]** erfassen: `domain` (Integration-Domain, sonst aus dem Scaffold-Schritt abgeleitet), `target_dir` (Repo-Root), bekannte Protokoll-/Auth-Details (REST/MQTT/Bluetooth; API-Key/OAuth2), ein `target_tier` (`bronze`/`silver`/`gold`/`platinum`, Default `silver`), das die enthaltenen Bausteine kumulativ treibt, `release_ready` (auch CI-Validierung + HACS-Release-Reife scaffolden) und `deploy_ready` (Default `false`; Opt-in: die Deploy→Verify→Review-Lifecycle-Phase mit Fix-Feedback-Loop hinter einem zweiten Gate ausführen)

### Pre-Flight

- **MUSS [MUST]** `requirement` als nichtleer prüfen; dann die Anforderungs-Konfidenz einschätzen — eine klar spezifizierte Anforderung nutzt den leichten Pfad (1–3 gezielte Rückfragen: welches Protokoll, welche Auth-Art, welche Entity-Domänen, welche Qualitätsmerkmale), während eine Anforderung unterhalb einer Konfidenzschwelle (vages Ziel, ungenanntes Gerät/API, unklarer Scope) **MUSS [MUST]** zuerst `requirements-elicit` dispatchen und gegen das bestätigte Anforderungs-Artefakt planen, analog zum `issue-orchestrate`-Upstream-Gate — bevor er plant
- **MUSS [MUST]** prüfen, ob die Anforderung in Wahrheit YAML-Automation-förmig ist (kein eigenes Protokoll, keine Config-Flow-Integration); wenn ja, das im Plan ausweisen und an `ha-automation-solution` verweisen statt eine Integration zu erzwingen
- **MUSS [MUST]** prüfen, ob bereits eine Integration unter `target_dir/custom_components/<domain>/` existiert; wenn ja, den Scaffold-Schritt überspringen und auf den Bestand aufsetzen

### Dispatch-/Plan-Regeln

- **MUSS [MUST]** jeden zuständigen Skill zur Laufzeit auflösen, indem die Anforderung gegen das aktive Inventar der Integrations-`ha-*`-Skills abgeglichen wird (die formulierte Zuständigkeit jedes Kandidaten), nicht aus einer eingefrorenen Namensliste — die Zuordnungen in diesem Abschnitt sind ein illustrativer Anker, pro Lauf neu aufgelöst, sodass ein zur Familie hinzugefügter oder entfernter Skill dispatchbar ist, ohne den Orchestrator zu editieren (analog zum Runtime-Lookup-Dispatch von `issue-orchestrate`)
- **MUSS [MUST]** vor jeder Generierung einen Plan als Tabelle in Abhängigkeits-Reihenfolge präsentieren: pro Eintrag `#`, Baustein, zuständiger Skill, Abhängigkeit (`depends-on`), Zweck — und explizite Bestätigung abwarten
- **MUSS NICHT [MUST NOT]** einen Baustein selbst inline generieren; jede Generierung läuft über den zuständigen Einzel-Skill
- **MUSS [MUST]** `ha-integration-scaffold` als Schritt 1 dispatchen, sobald eine *neue* Integration angelegt wird (Greenfield-Hub)
- **MUSS [MUST]** das Fundament vor den Entities planen: `ha-config-flow-augment` und `ha-coordinator-add`; `ha-oauth2-credentials-augment` nur bei OAuth2/Cloud-Auth; `ha-options-flow-augment` für eine Post-Setup-Option und `ha-config-entry-migrate` für einen Stored-Shape-Change
- **MUSS [MUST]** deklarative Read-Type-Entities (Datapoint-/Schema-getrieben) auf `ha-entity-description-mapper` abbilden und aktive, befehlsgetriebene Plattformen (climate/cover/light/fan/lock/media_player/…) auf `ha-entity-platform-add`
- **SOLLTE [SHOULD]** Aktionen/Oberflächen/Robustheit nur nach Bedarf der Anforderung planen: `ha-service-definition-generator` (Services), `ha-integration-events-add` (Event-Bus), `ha-websocket-command-add` (ein WebSocket-Command, den eine Frontend-Card/-Panel aufruft — der Python-seitige Backend-Endpoint), `ha-device-automation-add` (Device-Automations), `ha-discovery-augment` (DHCP/SSDP/USB/HomeKit/Zeroconf), `ha-bluetooth-augment` (BLE), `ha-diagnostics-augment`, `ha-repairs-add`, `ha-system-health-add`, `ha-significant-change-add`, `ha-backup-platform-add`, `ha-media-source-add`, `ha-reproduce-state-add`, `ha-conversation-agent-augment`, `ha-device-registry-augment` (Geräte-Gruppierung / `via_device` / stale-devices)
- **MUSS [MUST]** i18n und Tests gegen Ende planen: `ha-translation-sync` nach allen string-erzeugenden Schritten, `ha-test-harness-augment` für die ergänzten Code-Pfade
- **MUSS [MUST]** den Baustein-Satz nach `target_tier` treiben (kumulativ Bronze→Platinum) — Bronze Scaffold + Config-Flow + Tests; Silver + Reauth + `PARALLEL_UPDATES` + `entity-unavailable` + Options; Gold + Diagnostics + Discovery + `ha-device-registry-augment` + Repairs + Reconfigure + Translations; Platinum dispatcht `ha-dev-workflow-apply` (den zuständigen Skill von `ha/dev-workflow`), um den Strict-Typing- / Code-Stil- / `hassfest`-Workflow anzuwenden und zu validieren, statt einen bloßen Checklistenpunkt anzuzeigen
- **MUSS [MUST]** einen `release_ready`-Lauf mit `ha-integration-ci-scaffold` (hassfest/HACS/pytest-CI) und `ha-hacs-release` (HACS-Distributions-Reife) abschließen
- **MUSS [MUST]** den Lauf mit dem Read-only-Audit-Gate abschließen — `ha-quality-scale-audit` und `ha-security-audit` (modifizieren nie Code); ein Defizit routet je Finding zurück an den benannten Remediation-Skill. Dies ist das **In-Flow-Acceptance-Gate**, hier einmal ausgeführt; es überschneidet sich bewusst mit dem gebündelten `ha-integration-review`-Agenten (der Quality-Scale + Security *plus* Cross-Cutting + Drift erneut fährt). Die Trennung ist **zeitlich, nicht additiv**: Ein Lauf, der dieses Gate besteht, **MUSS NICHT [MUST NOT]** zusätzlich `ha-integration-review` für dieselben zwei Dimensionen im selben Durchlauf dispatchen — dieser Agent ist der separate **Release-/Pre-PR-Gesamtblick-Durchlauf**, auf den als Folge-Schritt hingewiesen wird, nie zusätzlich auf ein grünes In-Flow-Gate ausgeführt
- **SOLLTE [SHOULD]** die Plan-Bestätigung als einzelnes menschliches Gate für die Generierung behandeln — danach laufen Dispatch, Audits und der Release-Ready-Abschluss bis zur Fertigstellung, Stopp nur bei NEEDS-WORK
- **KANN [MAY]**, nur wenn `deploy_ready` gesetzt ist und nur nach einem **zweiten expliziten menschlichen Gate**, das vom Plan-Gate verschieden ist, die Deploy→Verify→Review-Lifecycle-Phase ausführen: `ha-dev-instance-provision` (nur falls kein Dev-HA-Pod existiert) → `ha-integration-deploy` → `ha-integration-verify` → `ha-integration-review` (der Release-/Pre-PR-Gesamtblick-Durchlauf, legitim zu diesem separaten Post-Gate-Zeitpunkt ausgeführt, nie zusätzlich zum In-Flow-Gate). Der Generierungs-only-Default und sein einzelnes Gate bleiben erhalten, wenn `deploy_ready` nicht gesetzt ist
- **MUSS [MUST]** in dieser Phase bei einem `ha-integration-verify`-FAIL oder einem `ha-integration-review`-NEEDS-WORK jedes Finding an den zuständigen Authoring-/Remediation-Skill zurückrouten (das Audit-Defizit-Muster), den Fix neu dispatchen und dann neu deployen und neu verifizieren — ein geschlossener Feedback-Loop, kein terminaler beschreibender Bericht; nie `kubectl delete pod` (ein Code-Refresh ist `kill 1`, im Besitz des `ha-integration-deploy`-Agenten)
- **MUSS [MUST]** die Skills in Abhängigkeits-Reihenfolge dispatchen und die `domain` sowie die in einem Schritt erzeugten `entity_id`s/Datei-Pfade als Eingaben der abhängigen Schritte durchreichen
- **MUSS [MUST]** abbrechen und zurückmelden, wenn ein dispatchter Skill einen NEEDS-WORK-Bericht liefert, statt auf einem unfertigen Vorgänger-Baustein weiterzubauen
- **MUSS [MUST]** die Artefakte minimal halten — keinen Baustein planen, den die Anforderung nicht verlangt
- **MUSS [MUST]** alle Bezeichner über die Bausteine hinweg konsistent nach `ha/naming-conventions` halten und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** am Ende jeden erzeugten/geänderten Datei-Pfad, den zugehörigen Baustein und die Verdrahtung (`domain`, welche `entity_id` welche referenziert) auflisten
- **MUSS [MUST]** die aggregierten CONFORMANT / NEEDS-WORK-Berichte der Einzel-Skills sowie die Findings der Read-only-Reviews weiterreichen, ohne sie neu zu bewerten
- **MUSS [MUST]** im Generierungs-only-Default (`deploy_ready` nicht gesetzt) auf die Operator-Folge-Schritte hinweisen (ein gebündelter Gesamtblick-Durchlauf über den `ha-integration-review`-Agenten als **Release-/Pre-PR**-Review, Deploy/Verify über die `ha-integration-deploy`- und `ha-integration-verify`-Agenten), ohne sie auszuführen — der `ha-integration-review`-Folge-Schritt ergänzt Cross-Cutting + Drift *zusätzlich zu* Quality-Scale + Security und **MUSS NICHT [MUST NOT]** das In-Flow-Quality+Security-Gate dieses Laufs erneut fahren. Ist `deploy_ready` gesetzt, werden diese Folge-Schritte stattdessen von der Opt-in-Lifecycle-Phase hinter dem zweiten Gate ausgeführt, und der Bericht enthält das Deploy/Verify/Review-Ergebnis und jeden Fix-Zyklus

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Anforderung pro Lauf orchestrieren
- **MUSS NICHT [MUST NOT]** einen Plan ohne Nutzer-Bestätigung ausführen
- **MUSS NICHT [MUST NOT]** einen dispatchten Skill-Bericht neu bewerten
- **MUSS NICHT [MUST NOT]** im Generierungs-only-Default in eine laufende HA-Instanz deployen oder gegen sie verifizieren — Deploy/Verify geschieht **nur** innerhalb der Opt-in-`deploy_ready`-Lifecycle-Phase, hinter dem zweiten expliziten Gate

## Akzeptanzkriterien

- [ ] Zuständige Skills werden pro Lauf gegen das aktive Integrations-`ha-*`-Inventar aufgelöst (ein neu hinzugefügter oder umbenannter Familien-Skill ist dispatchbar, ohne den Orchestrator zu editieren); die Zerlegungs-Zuordnungen sind illustrativ, keine eingefrorene geschlossene Menge
- [ ] Skill erfragt fehlende Eckdaten (Protokoll, Auth-Art, Entity-Domänen, Qualitätsmerkmale), bevor er plant
- [ ] Eine unterspezifizierte Anforderung dispatcht `requirements-elicit` vor der Planung; eine klar spezifizierte nutzt den schnellen 1–3-Fragen-Clarify-Pfad
- [ ] Skill präsentiert einen abhängigkeits-geordneten Skill-Plan und wartet auf Bestätigung
- [ ] Skill dispatcht die zuständigen Einzel-Skills statt selbst zu generieren
- [ ] `ha-integration-scaffold` ist Schritt 1 für eine neue Integration; bei Bestand wird darauf aufgesetzt
- [ ] `domain` und `entity_id`s früherer Schritte werden als Eingaben der abhängigen Schritte durchgereicht
- [ ] Eine YAML-Automation-förmige Anforderung wird erkannt und an `ha-automation-solution` verwiesen
- [ ] Abbruch bei einem NEEDS-WORK-Vorgänger statt Weiterbau
- [ ] Lauf endet mit den Read-only-Reviews (`ha-quality-scale-audit`, `ha-security-audit`)
- [ ] Gesamt-Bericht listet alle Dateien und die Verdrahtung, reicht die Einzel-Berichte weiter und verweist auf die Deploy/Verify-Folge-Schritte
- [ ] Ist `deploy_ready` gesetzt, provisioniert eine Opt-in-Phase (falls nötig), deployt, verifiziert und reviewt hinter einem **zweiten** expliziten Gate, das vom Plan-Gate verschieden ist
- [ ] In dieser Phase routet ein `ha-integration-verify`-FAIL oder `ha-integration-review`-NEEDS-WORK zurück an den zuständigen Skill und treibt Deploy→Verify erneut, statt mit einem beschreibenden Bericht zu terminieren
- [ ] Der Generierungs-only-Default (und sein einzelnes Gate) bleibt erhalten, wenn `deploy_ready` nicht gesetzt ist

## Offene Fragen

- **Review-Agent vs. Review-Skills (entschieden)**: Der gebündelte `ha-integration-review`-Agent (ein Aufruf, der Quality-Scale, Security und übergreifende Konsistenz read-only zusammenfasst) existiert bereits, ist aber per Contract eine *fire-and-forget* Operator-Folge-Prüfung (pre-PR/pre-release), die nie von einem Orchestrator dispatcht wird und die Einzel-Audit-Skills nie ersetzt. **Entscheidung (Variante b):** Die zwei Audit-Skills sind das **In-Flow-Acceptance-Gate** (interaktiv, sichtbar, einmal im Lauf ausgeführt); `ha-integration-review` ist der separate **Release-/Pre-PR-Gesamtblick-Durchlauf**. Die Trennung ist **zeitlich, nicht additiv** — ein Lauf, der das In-Flow-Gate besteht, fährt nicht zusätzlich den gebündelten Agenten für dieselben zwei Dimensionen, sodass die Nutzerin die Quality+Security-Bewertung nie doppelt bezahlt. Siehe die Dispatch-/Plan-Regeln und Validierung & Bericht.
- **Agent- vs. Skill-Dispatch**: Sollen die Generierungs-Schritte als Skills (sichtbar, sequentiell) oder über Generierungs-Agenten (isoliert, parallel) ausgeführt werden? Aktuell Skill-Dispatch, weil die Plan-Bestätigung und die `domain`/`entity_id`-Verdrahtung im Nutzer-Kontext sichtbar bleiben sollen.
- **Plan-Persistenz**: Soll der Skill-Plan als Datei persistiert werden, damit ein unterbrochener Lauf fortsetzbar ist? Aktuell in-conversation.
- **Bestehende-Integration-Awareness**: Wie tief soll der Skill eine bestehende `custom_components/<domain>/` einlesen, um schon vorhandene Bausteine (Coordinator, Plattformen) zu erkennen und doppelte Schritte zu vermeiden? Aktuell Pre-Flight-Existenz-Check plus Nutzer-Angabe.
