# ESPHome-Device-Config-Patterns

Status: draft

## Kontext

Eine ESPHome-Device-Config ist eine einzelne YAML-Datei, die genau ein Mikrocontroller-Gerät vollständig beschreibt — Board, Konnektivität und seine Sensor-/Aktor-Plattformen — kompiliert und geflasht von der ESPHome-Toolchain und in Home Assistant über die native API sichtbar. Anders als bei einer Custom Integration gibt es hier keinen Python-Lifecycle: die gesamte Qualität entscheidet sich an YAML-Struktur, Secret-Handling, Naming-Disziplin und daran, wie viel gemeinsame Konfiguration wiederverwendet statt kopiert wird.

Diese Spec kanonisiert die Device-YAML-Patterns für das Portfolio, destilliert aus dem Round-Trip-Fixture [`nolte/esphome-configs`](https://github.com/nolte/esphome-configs) (per-Device-Dateien unter `src/`, geteilte Include-Snippets, substitution-getriebenes Naming) und verifiziert gegen die offizielle ESPHome-Dokumentation. Sie fundiert den ersten Schnitt der ESPHome-Skill-Achse (`ha-esphome-config-scaffold`, `ha-esphome-config-augment`); ESPHome-Custom-Components (C++/Python) und HA-Add-ons sind bewusst separate, spätere Achsen.

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

- Ein Gerät **MUSS** in genau einer YAML-Datei leben, benannt nach dem Gerät (`<device-name>.yaml`, kebab-case), unter dem Device-Config-Root des Repositories (Fixture: `src/`)
- Der Gerätename **MUSS** einmal über `substitutions:` (`name`, `friendly_name`) deklariert und überall sonst als `${name}` / `${friendly_name}` referenziert werden — Entity-Namen leiten sich als `${friendly_name}_<platform>_<n>_<measurement>` ab, sodass Umbenennungen Ein-Zeilen-Änderungen bleiben
- Stillgelegte Geräte **SOLLTEN** in einen `archive/`-Nachbarordner wandern statt gelöscht zu werden, damit die Config als Pattern-Historie erhalten bleibt

### Gemeinsame Konfiguration

- Gemeinsame Blöcke (wifi, logger, api, ota, Board-/Plattform-Familien, i2c-Busse) **MÜSSEN** in geteilte Dateien ausgelagert und in Device-Dateien hineingezogen werden — nie pro Gerät dupliziert
- Neue Configs **SOLLTEN** dafür ESPHome-`packages:` nutzen; die Legacy-Form `<<: !include ./include-*.yaml.snipped` des Fixtures **DARF** in Bestandsdateien bleiben, **DARF ABER NICHT** in neuen eingeführt werden (Merge-Keys deep-mergen keine Listen, und das Pattern stammt aus der Zeit vor packages)
- Eine geteilte Datei **MUSS** board- oder concern-scoped bleiben (`esp32`, `esp8266-i2c`, `base`), damit ein Gerät genau die Concerns komponiert, die es hat

### Konnektivität und Sicherheit

- `wifi:`-Credentials **MÜSSEN** aus Umgebungsvariablen kommen (`!env_var WIFI_SSID` / `!env_var WIFI_PASSWORD`), nie aus einer Datei im Repository: Remote-Packages können `!secret` nachweislich nicht auflösen, und Umgebungsvariablen erreichen lokalen wie CI-Build gleichermaßen. Jede gelesene Variable **MUSS** dokumentiert sein, damit ein frischer Checkout baubar ist
- `wifi:` **SOLLTE** einen `ap:`-Fallback plus `captive_portal:` deklarieren, damit ein unerreichbares Gerät wiederherstellbar bleibt
- `api:` **MUSS** `encryption:` mit einem **geräteeigenen** Key deklarieren, geliefert als Substitution, die die Device-Datei setzt (`substitutions: {api_key: !env_var <DEVICE>_API_KEY}`) und konsumiert als `key: ${api_key}` — eine unverschlüsselte native API ist ein Finding, keine Variante
- `ota:` **MUSS** vorhanden und via `!env_var OTA_PASSWORD` passwortgeschützt sein
- Kein literales Credential, Token oder Key **DARF** je in einer Device- oder Shared-Datei erscheinen, und eine befüllte `secrets.yaml` **DARF NICHT** committet werden

### Plattformen und Components

- Sensor-/Aktor-Blöcke **MÜSSEN** explizite `name:`-Werte tragen (substitution-abgeleitet) und **SOLLTEN** `update_interval` über eine Substitution pinnen (Fixture: `intervall`), damit die Polling-Kadenz pro Gerät justierbar ist
- Eine lokal konsumierte Custom Component **MUSS** über `external_components:` mit repository-relativem `source:` und expliziter `components:`-Liste deklariert werden
- Multiplexte I²C-Topologien (Fixture: `tca9548a`) **MÜSSEN** jeden Kanal-Bus benennen (`bus_id`), damit Sensor-Blöcke an einen expliziten Bus binden, nie an einen impliziten Default
- Jeder genutzte Component-/Plattform-Key **MUSS** in den offiziellen ESPHome-Docs eines aktuellen Releases existieren; deprecated Keys sind Findings

### Verifikation

- Fakten über Schema-Keys, Defaults und Deprecations **MÜSSEN** gemäß `spec/ha/upstream-docs-verification` gegen die offizielle ESPHome-Dokumentation (<https://esphome.io>) verifiziert werden — nie aus dem Gedächtnis behauptet
- Eine generierte oder augmentierte Config **SOLLTE** mit `esphome config <file>` validiert werden, wenn die Toolchain verfügbar ist; wenn nicht, meldet der Skill die Validierung als offenen Caller-Schritt

## Akzeptanzkriterien

- [ ] Eine gescaffoldete Device-Config enthält die Pflicht-Kernblöcke (substitutions, esphome, Shared-Package/-Include, wifi+ap, api+encryption, ota, logger) mit null literalen Secrets
- [ ] Entity-Namen in generierten Plattform-Blöcken leiten sich per Naming-Regel aus `${friendly_name}` ab
- [ ] Neue Configs nutzen `packages:` für geteilte Blöcke; keine neuen `<<: !include`-Merge-Keys
- [ ] Jeder Schema-Key im generierten Output löst gegen die offiziellen ESPHome-Docs auf
- [ ] Credentials lösen sich aus dokumentierten Umgebungsvariablen auf; keine Credential-Datei ist committet

## Offene Fragen

- Minimale gepinnte ESPHome-Version für die generierten Patterns (das Fixture pinnt keine explizit) — mit der portfolio-weiten HA-Versions-Frage in `AUDIENCES.md` alignen
- Ob die archive/-Konvention ein MUSS wird, sobald ein zweites Consumer-Repo die Achse adoptiert
