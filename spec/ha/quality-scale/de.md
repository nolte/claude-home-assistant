# HA-Integration: Quality-Scale

Status: draft

## Kontext

Die Integration Quality Scale ist HAs Framework, das Integrationen anhand von vier Achsen bewertet: User Experience, Features, Code-Qualität und Developer Experience. Die Bewertung läuft über ein Tier-System, in dem jede Stufe eine eigene Bedeutung trägt und einen festen Satz von Regeln zusammenfasst.

Es gibt vier gestufte Tiers: 🥉 **Bronze**, 🥈 **Silver**, 🥇 **Gold** und 🏆 **Platinum**. **Bronze** ist der Baseline-Standard und die Mindestanforderung für *alle* neuen Integrationen — eine neue Integration kann nicht ohne Score eingeführt werden. Um ein Tier zu erreichen, muss eine Integration *alle* Regeln dieses Tiers **und** aller darunterliegenden Tiers erfüllen. Daneben existieren die Sonder-Tiers ❓ **No score** (noch nicht bewertet / Legacy-Stand unter Bronze, für neue Integrationen nicht vergebbar), 🏠 **Internal**, 💾 **Legacy** und 📦 **Custom** für Integrationen, die nicht auf der gestuften Skala einsortiert werden.

Die Deklaration erfolgt zweistufig: ein `quality_scale:`-Schlüssel in der `manifest.json` benennt das erreichte Tier, und eine begleitende `quality_scale.yaml`-Datei führt pro Regel den Status (`done` oder `exempt` mit Begründungs-`comment`). Diese Datei dokumentiert den Fortschritt der implementierten Regeln und die Begründung für ausgenommene Regeln.

Die anderen Specs in diesem Repo tragen bereits einen "Quality-Scale-Marker" (z. B. `ha/coordinator-patterns` → **Silver**). Diese Spec ist das Framework, auf das sich diese Marker beziehen: Sie definiert die Tiers, die Deklarations-Artefakte und das Mapping der Schlüssel-Regeln auf die bestehenden Repo-Specs, die sie erfüllen.

## Ziele

- Die vier gestuften Tiers (Bronze / Silver / Gold / Platinum) und die Sonder-Tiers als gemeinsames Vokabular für alle vom Plugin gescaffoldeten Integrationen festschreiben
- Bronze als verbindliche Mindeststufe für jede neu generierte Integration verankern
- Die zweistufige Deklaration erzwingen: `quality_scale:` in `manifest.json` plus eine `quality_scale.yaml` mit Per-Regel-Status (`done` / `exempt` / `todo`)
- Die kumulative Tier-Semantik festhalten: ein Tier verlangt alle eigenen Regeln *und* alle Regeln darunter
- Die Schlüssel-Regeln auf die bestehenden Repo-Specs mappen, die sie erfüllen, damit Quality-Scale-Marker und Anforderungen konsistent bleiben
- Ausgenommene Regeln über einen dokumentierten `comment` rechtfertigen, statt sie still wegzulassen

## Nicht-Ziele

- Die wörtliche Reproduktion aller 45 Regeln samt Beispiel-Implementierung — die kanonische Quelle bleibt die HA-Dokumentation; diese Spec verlinkt und gruppiert, statt zu duplizieren
- Ein automatisierter Regel-Prüfer (Linter / `hassfest`-Äquivalent), der `quality_scale.yaml` gegen den Code validiert — eigene Folge-Spec, sobald ein Tooling-Bedarf konkret wird
- Die Pflege der HA-Checklist-PR für ein Tier-Upgrade gegenüber dem HA-Core-Repo — das ist ein Beitrags-Workflow, kein Plugin-Artefakt
- Tier-Vergaben für Integrationen außerhalb der gestuften Skala (Internal, Legacy) — diese Tiers werden vom HA-Projekt selbst verwaltet
- Die Definition der `manifest.json`-Gesamtstruktur jenseits des `quality_scale`-Schlüssels — das fällt in `ha/integration-architecture`

## Anforderungen

### Tier-Zielsetzung

- **MUSS [MUST]** jede vom Plugin gescaffoldete Integration mindestens auf **Bronze** zielen — das ist der Baseline-Standard für alle neuen Integrationen
- **SOLLTE [SHOULD]** für jede verbindungsbasierte Integration (die ein Device oder einen Cloud-Service über das Netzwerk anspricht) auf **Silver** zielen, da Reauthentifizierung und robuste Fehlerbehandlung dann zur Pflicht werden
- **KANN [MAY]** **Gold** oder **Platinum** anstreben, wenn die Integration Discovery, vollständige Übersetzbarkeit, Diagnostics und vollständige Typisierung bietet
- **MUSS NICHT [MUST NOT]** eine neue Integration ohne Score (`No score`) ausliefern — neuen Integrationen kann dieses Tier nicht zugewiesen werden

### Deklaration

- **MUSS [MUST]** das erreichte Tier über einen `quality_scale:`-Schlüssel in der `manifest.json` deklarieren (`bronze` / `silver` / `gold` / `platinum`)
- **MUSS [MUST]** eine `quality_scale.yaml` im Integrations-Verzeichnis führen, die unter `rules:` für jede Regel einen Status hält (`done`, oder `status: exempt` mit `comment`)
- **MUSS [MUST]** für jede `exempt`-Regel einen `comment` mit der Begründung angeben — eine ausgenommene Regel ohne Begründung ist nicht zulässig
- **SOLLTE [SHOULD]** noch offene Regeln auf dem Weg zu einem höheren Tier als `todo` markieren, statt sie aus der Datei auszulassen, damit der Fortschritt nachvollziehbar bleibt
- **MUSS NICHT [MUST NOT]** ein Tier in der `manifest.json` deklarieren, dessen Regeln (inklusive aller darunterliegenden Tiers) nicht vollständig `done` oder begründet `exempt` sind

### Tier-zu-Spec-Mapping

- **MUSS [MUST]** die Regel `runtime-data` über die Spec `ha/runtime-data-pattern` erfüllen (`ConfigEntry.runtime_data` für Laufzeitdaten)
- **MUSS [MUST]** die Regeln `config-flow`, `test-before-configure`, `test-before-setup` und `unique-config-entry` über die Spec `ha/config-flow-patterns` erfüllen
- **MUSS [MUST]** die Regel `parallel-updates` über die Specs `ha/entity-architecture` und `ha/coordinator-patterns` erfüllen (`PARALLEL_UPDATES` pro Plattform, `0` für Read-only-Plattformen bei Coordinator-Nutzung)
- **MUSS [MUST]** die Regeln `entity-translations` und `exception-translations` über die Spec `ha/translations` erfüllen
- **MUSS [MUST]** die Regel `diagnostics` über die Spec `ha/diagnostics` erfüllen
- **MUSS [MUST]** die Regeln `discovery` und `discovery-update-info` über die Spec `ha/zeroconf-discovery` erfüllen
- **SOLLTE [SHOULD]** jeden neuen Quality-Scale-Marker in einer Sibling-Spec gegen die hier gelisteten Tiers prüfen, damit Marker und tatsächliches Tier nicht auseinanderdriften

### Bronze-Pflichtregeln

- **MUSS [MUST]** alle Bronze-Regeln erfüllen: `action-setup`, `appropriate-polling`, `brands`, `common-modules`, `config-flow-test-coverage`, `config-flow`, `dependency-transparency`, `docs-actions`, `docs-high-level-description`, `docs-installation-instructions`, `docs-removal-instructions`, `entity-event-setup`, `entity-unique-id`, `has-entity-name`, `runtime-data`, `test-before-configure`, `test-before-setup`, `unique-config-entry`
- **MUSS [MUST]** für `config-flow` zusätzlich `data_description` zur Kontextualisierung der Felder nutzen und `ConfigEntry.data` bzw. `ConfigEntry.options` korrekt trennen (Subchecks der Regel)
- **MUSS [MUST]** für `has-entity-name` jede Entität mit `_attr_has_entity_name = True` versehen, damit Namen logisch aus Device- und Entity-Name zusammengesetzt werden
- **MUSS [MUST]** automatisierte Tests bereitstellen, die das Setup der Integration absichern (`config-flow-test-coverage`, `test-before-setup`)

### Silver-Pflichtregeln

- **MUSS [MUST]** alle Silver-Regeln erfüllen: `action-exceptions`, `config-entry-unloading`, `docs-configuration-parameters`, `docs-installation-parameters`, `entity-unavailable`, `integration-owner`, `log-when-unavailable`, `parallel-updates`, `reauthentication-flow`, `test-coverage`
- **MUSS [MUST]** bei Action-Fehlern eine Exception werfen (`action-exceptions`): `ServiceValidationError` bei fehlerhafter Eingabe, `HomeAssistantError` bei einem Fehler in der Action selbst
- **MUSS [MUST]** offline gegangene Devices als `entity-unavailable` markieren und beim Recovery sauber zurückkehren, ohne die Logs mit Wiederholungen zu fluten (`log-when-unavailable`)
- **MUSS [MUST]** einen `reauthentication-flow` bereitstellen, der bei Auth-Fehlern automatisch greift (siehe Error-Mapping in `ha/coordinator-patterns`)
- **MUSS [MUST]** mindestens einen aktiven Code-Owner führen (`integration-owner`)

### Gold/Platinum-Ausblick

- **SOLLTE [SHOULD]** für Gold die Regeln um Devices und Discovery erweitern: `devices`, `diagnostics`, `discovery`, `discovery-update-info`, `dynamic-devices`, `stale-devices`, `reconfiguration-flow`, `repair-issues`
- **SOLLTE [SHOULD]** für Gold die volle Übersetzbarkeit und Kategorisierung herstellen: `entity-translations`, `exception-translations`, `icon-translations`, `entity-category`, `entity-device-class`, `entity-disabled-by-default`
- **SOLLTE [SHOULD]** für Gold die End-User-Dokumentation vervollständigen: `docs-data-update`, `docs-examples`, `docs-known-limitations`, `docs-supported-devices`, `docs-supported-functions`, `docs-troubleshooting`, `docs-use-cases`
- **KANN [MAY]** für Platinum die technische Exzellenz nachweisen: `async-dependency`, `inject-websession`, `strict-typing` (vollständig asynchrone, voll typisierte, ressourcen-effiziente Code-Basis)

## Akzeptanzkriterien

- [ ] `quality_scale:` ist in der `manifest.json` deklariert und benennt eines von `bronze` / `silver` / `gold` / `platinum`
- [ ] Eine `quality_scale.yaml` existiert mit einem Per-Regel-Status unter `rules:`
- [ ] Jede `exempt`-Regel trägt einen `comment` mit Begründung
- [ ] Alle Bronze-Pflichtregeln sind `done` oder begründet `exempt`
- [ ] Die `config-flow`-Subchecks (`data_description`, `data`/`options`-Trennung) sind erfüllt
- [ ] Bei Ziel-Tier ≥ Silver sind alle Silver-Regeln zusätzlich `done` oder begründet `exempt`
- [ ] Das deklarierte Tier ist kumulativ erfüllt (alle Regeln darunter ebenfalls)
- [ ] Jede Schlüssel-Regel mit Sibling-Spec ist auf die im Mapping gelistete Spec zurückführbar
- [ ] Keine neue Integration wird mit `No score` ausgeliefert

## Offene Fragen

- **Ziel-Tier-Policy**: Soll das Plugin verbindungsbasierte Integrationen hart auf Silver zwingen, oder bleibt Silver eine `SHOULD`-Empfehlung? Aktuell ist es `SHOULD`.
- **Automatische Regel-Verifikation**: Wie wird `quality_scale.yaml` gegen den tatsächlichen Code verifiziert? HA-Core nutzt `hassfest`; ein plugin-seitiges Äquivalent für Custom Integrations fehlt.
- **Exempt-Begründungs-Standard**: Welche Mindestqualität muss ein `exempt`-`comment` haben? Aktuell ist nur die Existenz, nicht die Aussagekraft erzwungen.
- **`quality_scale.yaml`-Drift**: Wie wird verhindert, dass die Datei nach Code-Änderungen veraltet (z. B. eine `done`-Regel wird durch ein Refactoring gebrochen)? Eine Drift-Prüfung wäre eine Folge-Spec.
- **Marker-Synchronisierung**: Soll der Quality-Scale-Marker jeder Sibling-Spec automatisch gegen tiers.json geprüft werden, oder bleibt das eine manuelle Review-Aufgabe?
