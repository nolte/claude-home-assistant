# ESPHome-Device-Config-Patterns

Status: draft

## Kontext

Eine ESPHome-Device-Config ist eine einzelne YAML-Datei, die genau ein Mikrocontroller-Gerät vollständig beschreibt — Board, Konnektivität und seine Sensor-/Aktor-Plattformen — kompiliert und geflasht von der ESPHome-Toolchain und in Home Assistant über die native API sichtbar. Anders als bei einer Custom Integration gibt es hier keinen Python-Lifecycle: die gesamte Qualität entscheidet sich an YAML-Struktur, Secret-Handling, Naming-Disziplin und daran, wie viel gemeinsame Konfiguration wiederverwendet statt kopiert wird.

Diese Spec kanonisiert die Device-YAML-Patterns für das Portfolio und stützt sich dabei auf das Round-Trip-Fixture [`nolte/esphome-configs`](https://github.com/nolte/esphome-configs) (per-Device-Dateien unter `src/`, geteilte Konfiguration unter `src/common/` über `packages:` eingebunden, substitution-getriebenes Naming), verifiziert gegen die offizielle ESPHome-Dokumentation. Zu beachten: Das Fixture ist eine *Quelle von Patterns, kein Konformitäts-Maßstab* — mehrere Anforderungen unten, insbesondere API-Verschlüsselung und OTA-Passwort, sind Portfolio-Entscheidungen, die das Fixture derzeit **nicht** erfüllt; sie sind entsprechend getiert. Sie ist die **Device-Datei**-Hälfte eines Paars: [`ha/esphome-project-structure`](../esphome-project-structure/de.md) besitzt das Repository um diese Dateien herum — Verzeichnislayout, Package-Architektur, Parametrisierung und Onboarding — und ist die tiefere Autorität, wo beide sich berühren. Die Abschnitte *Datei-Layout* und *Gemeinsame Konfiguration* unten sagen nur, wie eine einzelne Device-Datei auszusehen hat; die Regeln auf Baumebene sind jener Spec zu entnehmen. Sie fundiert den ersten Schnitt der ESPHome-Skill-Achse (`ha-esphome-config-scaffold`, `ha-esphome-config-augment`); ESPHome-Custom-Components (C++/Python) und HA-Add-ons sind bewusst separate, spätere Achsen.

### Quellen-Tiers

Die Evidenz-Tiers werden verwendet wie in [`ha/esp32-s3-box`](../esp32-s3-box/de.md) §„Quellen-Tiers" definiert: `[doc]` für die offizielle ESPHome-Komponenten-Dokumentation unter <https://esphome.io>, `[src]` für Verhalten, das real, aber undokumentiert ist und deshalb aus dem ESPHome-Quellbaum belegt wird, `[fixture]` für ein in `nolte/esphome-configs` beobachtetes Pattern und `[policy]` für eine nolte-Portfolio-Regel, die kein Upstream-Fakt ist. `[fixture]` ist hier der schwächste Tier: Er hält fest, was das Referenz-Repository tut — ein Beleg für ein funktionierendes Pattern und nicht mehr.

Verifiziert 2026-08.

## Ziele

- Eine kanonische Form für eine Device-Config: Dateiort, Pflicht-Kernblöcke, Secret-Handling, Naming
- Gemeinsame Konfiguration wird über `packages:` (bevorzugt) oder Legacy-Include-Snippets wiederverwendet — nie zwischen Device-Dateien kopiert
- Jede generierte Config ist out of the box HA-ready: verschlüsselte native API, OTA, sinnvolles Logging
- Fakten über ESPHome-Interna werden gemäß `spec/ha/upstream-docs-verification` gegen die offiziellen Docs verifiziert, nie aus dem Gedächtnis generiert

## Nicht-Ziele

- ESPHome-**Custom-Components** (`external_components`-Authoring, C++/Python) — spätere Achse; das Konsumieren einer existierenden lokalen Component in einem Device-YAML ist in Scope
- HA-**Add-ons** (Supervisor, s6) — separates Distributions-Thema
- Die Compile-/Flash-Toolchain selbst (`esphome run`, CI-Builds) und Fleet-/OTA-Rollout-Orchestrierung
- Dashboard-/UI-Belange in Home Assistant (gehören der Lovelace-Familie)

## Anforderungen

### Datei-Layout und Naming

- Ein Gerät **MUSS** in genau einer YAML-Datei leben, benannt nach dem Gerät (`<device-name>.yaml`, kebab-case), unter dem Device-Config-Root des Repositories (Fixture: `src/`) `[fixture]` `[policy]`
- Der Gerätename **MUSS** einmal über `substitutions:` (`name`, `friendly_name`) deklariert und überall sonst als `${name}` / `${friendly_name}` referenziert werden — Entity-Namen leiten sich als `${friendly_name}_<platform>_<n>_<measurement>` ab, sodass Umbenennungen Ein-Zeilen-Änderungen bleiben `[doc]` `[fixture]` `[policy]`
- Stillgelegte Geräte **SOLLTEN** in einen `archive/`-Ordner neben den Device-Dateien wandern statt gelöscht zu werden, damit die Config als Pattern-Historie erhalten bleibt. Das Fixture führt zusätzlich eine dritte Kategorie, `src/poc/`, für nie ausgerollte Experimente — eine Config, die weder in `src/` noch in `archive/` liegt, trägt keine Zusage, baubar zu sein `[fixture]` `[policy]`

### Gemeinsame Konfiguration

- Gemeinsame Blöcke (wifi, logger, api, ota, Board-/Plattform-Familien, i2c-Busse) **MÜSSEN** in geteilte Dateien ausgelagert und in Device-Dateien hineingezogen werden — nie pro Gerät dupliziert. Im Fixture liegen sie unter `src/common/` `[fixture]` `[policy]`
- Neue Configs **MÜSSEN** dafür ESPHome-`packages:` nutzen, in der `!include`-Form mit `file:` und optionalem `vars:`, damit eine geteilte Datei pro Gerät parametrisiert statt kopiert wird. Die Legacy-Form `<<: !include ./include-*.yaml.snipped` **DARF NICHT** eingeführt werden und ist im Fixture nicht mehr bloß veraltet: Sämtliche `.snipped`-Dateien liegen inzwischen unter `src/archive/`, während `src/box-01.yaml` weiterhin `./include-base.yaml.snipped` an einem Pfad referenziert, an dem keine solche Datei existiert — eine Config, die nicht auflöst und die die CI des Fixtures nicht bemerkt, weil sie Pre-Commit und Security-Scans fährt, aber nie `esphome config` `[doc]` `[fixture]` `[policy]`
- Eine geteilte Datei **MUSS** board- oder concern-scoped bleiben (`esp32`, `esp8266-i2c`, `base`), damit ein Gerät genau die Concerns komponiert, die es hat. Zu beachten: Ein `<<: !include`-Merge **in einen Listeneintrag** (wie `src/common/base.yaml` es für seine Status-/Uptime-/WiFi-Signal-Blöcke tut) ist ein anderes Konstrukt als ein Dokument-Merge auf oberster Ebene und bleibt idiomatisch `[fixture]` `[policy]`

### Konnektivität und Sicherheit

- `wifi:`-Credentials **MÜSSEN** aus Umgebungsvariablen kommen (`!env_var WIFI_SSID` / `!env_var WIFI_PASSWORD`), nie aus einer Datei im Repository, weil Umgebungsvariablen lokalen wie CI-Build gleichermaßen erreichen. Zwei Dinge über `!env_var` sind vorher zu wissen: Es ist **undokumentiert** — es existiert nur als Loader-Tag, registriert in `esphome/yaml_util.py`, auf keiner Seite von esphome.io — und es akzeptiert einen **Default** als nachgestellte Wörter (`!env_var NAME fallback wert`) und wirft nur dann, wenn die Variable ungesetzt ist *und* kein Default angegeben wurde. Jede gelesene Variable **MUSS** dokumentiert sein, damit ein frischer Checkout baubar ist `[src]` `[fixture]` `[policy]`
- Diese Regel **DARF NICHT** allein mit der Remote-Package-Beschränkung begründet werden. Es stimmt und ist dokumentiert, dass „remote packages cannot have secret lookups in them" — aber Upstreams eigenes Gegenmittel sind *keine* Umgebungsvariablen: Es verordnet „substitutions with an optional default in the packaged YAML, which the local device YAML can set using values from the local secrets". Lokale (nicht-remote) Packages lösen `!secret` normal auf, wie das Beispiel der Dokumentation selbst zeigt. Umgebungsvariablen statt `!secret` zu wählen ist also eine Portfolio-Entscheidung zugunsten von CI-Gleichlauf, keine von Upstream auferlegte Randbedingung `[doc]` `[policy]`
- `wifi:` **SOLLTE** einen `ap:`-Fallback plus `captive_portal:` deklarieren, damit ein unerreichbares Gerät wiederherstellbar bleibt `[doc]` `[fixture]`
- `api:` **MUSS** `encryption:` mit einem **geräteeigenen** Key deklarieren, geliefert als Substitution, die die Device-Datei setzt (`substitutions: {api_key: !env_var <DEVICE>_API_KEY}`) und konsumiert als `key: ${api_key}` — eine unverschlüsselte native API ist ein Finding, keine Variante, und ein flottenweiter Key ließe ein einziges kompromittiertes Gerät die API-Sitzung jedes anderen offenlegen. Das Fixture erfüllt das **nicht**: `src/common/base.yaml` liefert ein nacktes `api:` ganz ohne `encryption:`-Block `[policy]`
- `ota:` **MUSS** vorhanden und via `!env_var OTA_PASSWORD` passwortgeschützt sein. Auch das erfüllt das Fixture **nicht** — es deklariert `ota: - platform: esphome` ohne Passwort `[policy]`
- Kein literales Credential, Token oder Key **DARF** je in einer Device- oder Shared-Datei erscheinen, und eine befüllte `secrets.yaml` **DARF NICHT** committet werden `[policy]`

### Plattformen und Components

- Sensor-/Aktor-Blöcke **MÜSSEN** explizite `name:`-Werte tragen (substitution-abgeleitet) und **SOLLTEN** `update_interval` über eine Substitution pinnen (Fixture: `intervall`), damit die Polling-Kadenz pro Gerät justierbar ist `[fixture]` `[policy]`
- Eine lokal konsumierte Custom Component **MUSS** über `external_components:` mit repository-relativem `source:` und expliziter `components:`-Liste deklariert werden. Components explizit zu listen ist eine Portfolio-Regel, keine Schema-Regel — `components` ist optional und nutzt per Default jede Component, die die Quelle anbietet, also genau das implizite Verhalten, das zu vermeiden lohnt `[doc]` `[policy]`
- Multiplexte I²C-Topologien (Fixture: `tca9548a`) **MÜSSEN** jeden Kanal-Bus benennen (`bus_id`), damit Sensor-Blöcke an einen expliziten Bus binden, nie an einen impliziten Default `[doc]` `[fixture]`
- Jeder genutzte Component-/Plattform-Key **MUSS** in den offiziellen ESPHome-Docs eines aktuellen Releases existieren; deprecated Keys sind Findings `[policy]`

### Verifikation

- Fakten über Schema-Keys, Defaults und Deprecations **MÜSSEN** gemäß `spec/ha/upstream-docs-verification` gegen die offizielle ESPHome-Dokumentation (<https://esphome.io>) verifiziert werden — nie aus dem Gedächtnis behauptet `[policy]`
- Auf den ESPHome-Quellbaum **DARF** zurückgegriffen werden, wo ein Verhalten real, aber undokumentiert ist — `!env_var` ist das durchgearbeitete Beispiel —, die Aussage **MUSS** dann aber `[src]` statt `[doc]` tragen, weil sich ein undokumentiertes Tag ohne Dokumentationsänderung ändern kann `[policy]`
- Eine generierte oder augmentierte Config **SOLLTE** mit `esphome config <file>` validiert werden, wenn die Toolchain verfügbar ist; wenn nicht, meldet der Skill die Validierung als offenen Caller-Schritt. Zu beachten: Das Fixture-Repository fährt das **nicht** in CI — seine Pipeline deckt Pre-Commit, Trivy und Chain-Bench ab —, „steht im Fixture" ist also kein Beleg dafür, dass eine Config auflöst `[fixture]` `[policy]`

## Akzeptanzkriterien

- [ ] Eine gescaffoldete Device-Config enthält die Pflicht-Kernblöcke (substitutions, esphome, Shared-Package/-Include, wifi+ap, api+encryption, ota, logger) mit null literalen Secrets
- [ ] Entity-Namen in generierten Plattform-Blöcken leiten sich per Naming-Regel aus `${friendly_name}` ab
- [ ] Neue Configs nutzen `packages:` für geteilte Blöcke; keine neuen `<<: !include`-Merge-Keys
- [ ] Jeder Schema-Key im generierten Output löst gegen die offiziellen ESPHome-Docs auf
- [ ] Credentials lösen sich aus dokumentierten Umgebungsvariablen auf; keine Credential-Datei ist committet
- [ ] Gemeinsame Konfiguration wird über `packages:` mit `file:`/`vars:` eingebunden; kein `<<: !include`-Dokument-Merge wird eingeführt, und jeder von einer Config referenzierte Include löst tatsächlich auf

## Offene Fragen

- Minimale gepinnte ESPHome-Version für die generierten Patterns (das Fixture pinnt keine explizit) — mit der portfolio-weiten HA-Versions-Frage in `AUDIENCES.md` alignen. Zu beachten: [`ha/esp32-s3-box`](../esp32-s3-box/de.md) hat dieselbe Frage inzwischen pro Generation entschieden, was als Präzedenz taugt: den Floor pinnen, den die Upstream-Referenz für dieses Board pinnt, und eine Anhebung als reviewte Änderung behandeln
- Ob die archive/-Konvention ein MUSS wird, sobald ein zweites Consumer-Repo die Achse adoptiert
- **Fixture-Divergenz** (2026-08 durch den Verifikationsdurchgang zu Einheit 1 eröffnet): Das Fixture erfüllt weder die API-Verschlüsselungs- noch die OTA-Passwort-Anforderung, und `src/box-01.yaml` referenziert einen Include, der an diesem Pfad nicht mehr existiert. Am 2026-08-02 upstream gemeldet als [nolte/esphome-configs#14](https://github.com/nolte/esphome-configs/issues/14) (nicht auflösbarer Include, fehlende CI-Validierung) und [#15](https://github.com/nolte/esphome-configs/issues/15) (unverschlüsselte API, ungeschütztes OTA). Wird gemeinsam mit der Frage *Fixture-Remediation* in [`ha/esphome-project-structure`](../esphome-project-structure/de.md) geführt, die die Re-Flash-Folge ergänzt — als eine Entscheidung auflösen, nicht als zwei
