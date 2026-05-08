# HA-Integration: Architektur-Foundation

Status: draft

## Kontext

Eine Home-Assistant Custom Integration ist eine reproduzierbare On-Disk-Form: ein `custom_components/<domain>/`-Ordner mit `manifest.json` als Vertrag, Lifecycle-Eintrittspunkten in `__init__.py`, optionalem `config_flow.py`, `coordinator.py`, `entity.py`, plattform­spezifischen Modulen (`sensor.py`, `binary_sensor.py`, …), `services.yaml`, `strings.json` plus `translations/`, sowie `icons.json`. Skills, die diese Form scaffolden oder einzelne Bestandteile generieren, brauchen einen verbindlichen Bezugsrahmen — sonst entsteht entweder generischer HA-Boilerplate-Code, der die nolte-Konventionen verletzt, oder Skill-spezifische Eigenheiten driften vom Konsumenten-Repo `nolte/kamerplanter-ha` weg, das diese Patterns bereits mit ~5 400 LOC Implementation und ~11 000 LOC eigener Specs validiert hat.

Diese Spec ist die **Foundation-Spec** für alle weiteren HA-Specs in diesem Plugin: sie definiert die Pflicht-Dateien, das Manifest-Schema, die Wahl von `integration_type` und `iot_class`, die Lifecycle-Eintrittspunkte sowie die Konvention zur Quality-Scale-Markierung. Detailspecs für `runtime_data`, Config-Flow, Coordinator, Entity-Architektur, Services, Translations, Icons und Zeroconf-Discovery referenzieren von hier aus zurück.

## Ziele

- Für jede HA Custom Integration ein vorhersagbares On-Disk-Layout vorgeben, an dem Menschen und Skills sich orientieren können
- Die Pflichtfelder von `manifest.json` und ihre erlaubten Werte exakt benennen, damit Skill-Output die hassfest-Validierung besteht
- Die Wahl von `integration_type` und `iot_class` entscheidbar machen statt aus dem Bauch heraus
- Lifecycle-Eintrittspunkte (`async_setup_entry`, `async_unload_entry`) festschreiben, damit die Detail-Specs darauf aufbauen können
- Eine Konvention zur expliziten HA-Quality-Scale-Markierung pro Pattern etablieren, sodass Skill-Konsumenten wissen, auf welcher Stufe (Bronze / Silver / Gold / Platinum) ihr generierter Code landet
- Den Sprung von der `nolte/kamerplanter-ha`-Implementation zu generischen, domänen-agnostischen Skills sauber abbilden, ohne kamerplanter-spezifische Begriffe zu erben

## Nicht-Ziele

- Detail-Vorgaben für `config_flow.py`, `coordinator.py`, `entity.py`, `services.yaml`, `strings.json`/`translations/`, `icons.json`, Zeroconf/DHCP/SSDP/MQTT-Discovery, Diagnostics oder Lovelace-Cards — diese leben in eigenen Folge-Specs
- Test-Harness-Form (pytest, `pytest-homeassistant-custom-component`, Fixtures) — eigene `ha/test-harness`-Spec
- Lokaler Dev-Workflow (Kind-Cluster, `kubectl cp`, `kill 1` statt `delete pod`) — eigene `ha/dev-environment`-Spec
- HA-Add-on-Spezifikation (Supervisor, s6-Init, `config.yaml`) — andere Skill-Achse, andere Spec
- ESPHome-Custom-Components — andere Skill-Achse, andere Spec
- HA-Core-Aufnahme-Prozess (PR-Lifecycle in `home-assistant/core`) — Custom-Integration-Scope, nicht Core-Scope

## Anforderungen

### Repository-Layout

- **MUSS [MUST]** den Integrations-Code unter `custom_components/<domain>/` ablegen, wobei `<domain>` den Wert von `manifest.json:domain` trägt
- **MUSS [MUST]** mindestens diese zwei Dateien im Domain-Ordner enthalten: `manifest.json` und `__init__.py`
- **SOLLTE [SHOULD]** zusätzlich enthalten, sobald die jeweilige Funktionalität existiert:
  - `const.py` (Domain-Konstanten — `DOMAIN`, `CONF_*`, `DEFAULT_*`, `MIN_*`, `EVENT_*`, `SERVICE_*`)
  - `config_flow.py` (siehe `ha/config-flow-patterns`)
  - `coordinator.py` (siehe `ha/coordinator-patterns`)
  - `entity.py` (siehe `ha/entity-architecture`)
  - `services.yaml` und Service-Handler in `__init__.py` oder `services.py` (siehe `ha/services`), sobald die Integration HA-Services anbietet
  - `strings.json` plus `translations/<lang>.json` für jede ausgelieferte Sprache (siehe `ha/translations`)
  - `icons.json` (siehe `ha/icons`)
- **KANN [MAY]** zusätzlich enthalten:
  - Plattform-Module wie `sensor.py`, `binary_sensor.py`, `button.py`, `switch.py`, `number.py`, `select.py`, `calendar.py`, `todo.py` — eines pro genutzter HA-Plattform
  - `diagnostics.py` (siehe `ha/diagnostics`)
  - `repairs.py`
  - `system_health.py`
  - `api.py` oder ein API-Client-Subpackage
  - `www/` mit Custom Lovelace Cards (auto-registriert in `__init__.py`; siehe `ha/lovelace-card-patterns`)
- **MUSS NICHT [MUST NOT]** primären Integrations-Code außerhalb von `custom_components/<domain>/` ablegen; lose Module im Repository-Wurzelverzeichnis sind nur für Tooling, Tests und Doku zulässig

### HACS-Integration (optional)

- **KANN [MAY]** ein `hacs.json` im Repository-Wurzelverzeichnis enthalten, wenn die Integration über HACS distribuiert werden soll
- **MUSS [MUST]** in `hacs.json` mindestens `name` setzen, wenn die Datei vorhanden ist
- **SOLLTE [SHOULD]** in `hacs.json` `render_readme: true` setzen, damit HACS die Repo-`README.md` als Beschreibung rendert
- **SOLLTE [SHOULD]** in `hacs.json` einen `homeassistant`-Mindest-Versions-Pin setzen (siehe Open Questions zur portfolioweiten Pin-Strategie)
- **MUSS NICHT [MUST NOT]** `content_in_root: true` für ein klassisches `custom_components/<domain>/`-Layout setzen — das bricht die HACS-Erkennung

### `manifest.json` — Pflichtfelder

- **MUSS [MUST]** `domain` als kleingeschriebenen ASCII-Slug enthalten (`a–z`, `0–9`, `_`); Bindestriche und Großbuchstaben sind nicht erlaubt
- **MUSS [MUST]** `name` als menschenlesbaren Anzeigenamen enthalten
- **MUSS [MUST]** `codeowners` als nicht-leere Liste enthalten, mit `@`-präfigierten GitHub-Handles (mindestens ein Codeowner)
- **MUSS [MUST]** `documentation` als HTTPS-URL auf eine reachbare Doku-Seite enthalten (typischerweise das Repo oder die MkDocs-Seite)
- **MUSS [MUST]** `issue_tracker` als HTTPS-URL auf den Bug-Tracker enthalten (typischerweise `https://github.com/<owner>/<repo>/issues`)
- **MUSS [MUST]** `iot_class` enthalten — siehe Abschnitt _`iot_class`-Wahl_ unten
- **MUSS [MUST]** `integration_type` enthalten — siehe Abschnitt _`integration_type`-Wahl_ unten
- **MUSS [MUST]** `version` als SemVer-konforme Versionsnummer enthalten (`MAJOR.MINOR.PATCH`); HA verlangt diesen Schlüssel für jede Custom Integration
- **MUSS [MUST]** `loggers` als Liste der vom Code verwendeten Logger-Namen enthalten — typisch `["custom_components.<domain>"]` plus jede externe Library, die geloggt wird
- **MUSS [MUST]** `requirements` als Liste enthalten (auch wenn leer), gepinnt an explizite Versionen, wenn externe PyPI-Pakete genutzt werden (z. B. `["aiohttp==3.9.5"]`)
- **SOLLTE [SHOULD]** `config_flow: true` setzen, sobald die Integration UI-konfigurierbar ist; reine YAML-Konfiguration ist für Custom Integrations stark veraltet und sollte vermieden werden
- **KANN [MAY]** Discovery-Hinweise als Top-Level-Schlüssel ergänzen (`zeroconf`, `dhcp`, `ssdp`, `mqtt`, `bluetooth`, `usb`) — siehe `ha/zeroconf-discovery` und Folge-Specs für die jeweilige Form
- **KANN [MAY]** `dependencies` ergänzen, wenn die Integration auf andere HA-Komponenten angewiesen ist (z. B. `["frontend"]` für Lovelace-Card-Auto-Registrierung)
- **KANN [MAY]** `preload_platforms: false` setzen, um das Vorab-Laden zu deaktivieren

### `manifest.json` — Pflicht-Auslegungen

- **MUSS NICHT [MUST NOT]** ungetaggte Git-URLs in `requirements` referenzieren (`git+https://...`); die Liste muss aus PyPI-installierbaren, versionsgepinnten Einträgen bestehen
- **MUSS NICHT [MUST NOT]** `domain` über die Lebensdauer der Integration ändern — `domain` ist gleichzeitig Ordnername, Translation-Schlüssel-Präfix, Service-Namespace und Config-Entry-Lookup-Key; ein Wechsel zerschießt alle bestehenden Installationen
- **MUSS NICHT [MUST NOT]** persönliche Mail-Adressen oder echte Namen in `codeowners` listen — nur GitHub-Handles
- **SOLLTE [SHOULD]** `documentation` und `issue_tracker` denselben Repository-Stamm referenzieren, damit hassfest die Konsistenz prüfen kann

### `integration_type`-Wahl

- **MUSS [MUST]** genau einen der folgenden Werte setzen, basierend auf der Beziehung zwischen Integration und ihrer Welt:
  - `hub` — die Integration verwaltet **mehrere Devices oder Entities**, die unter einem zentralen Server / einer Bridge / einem API-Endpunkt zusammenhängen (typisch für die meisten Server-basierten Custom Integrations)
  - `device` — die Integration repräsentiert **genau ein einzelnes physisches oder logisches Device** (typisch für direkt angesprochene IoT-Geräte ohne Bridge)
  - `service` — die Integration spricht einen **Online-Service ohne physisches Device** an (typisch für rein cloudbasierte APIs)
  - `system` — interne System-Komponenten; in Custom Integrations praktisch nie zutreffend
  - `helper` — UI-only Helper ohne Datenquelle; in Custom Integrations praktisch nie zutreffend
- **SOLLTE [SHOULD]** `hub` wählen, sobald die Integration mehr als ein Sub-Device anlegt (auch wenn das Top-Level-Device eigentlich nur ein Server ist) — sonst verliert das Device-Registry die Hierarchie

### `iot_class`-Wahl

- **MUSS [MUST]** genau einen der folgenden Werte setzen:
  - `local_polling` — die Integration pollt einen Endpunkt im lokalen Netzwerk (häufigster Fall für Server-basierte Custom Integrations)
  - `local_push` — das Device / der lokale Endpunkt schickt Updates aktiv (mDNS-Broadcast, MQTT, HTTP-Webhook auf HA)
  - `cloud_polling` — die Integration pollt einen Cloud-Service über das Internet
  - `cloud_push` — der Cloud-Service schickt Updates über einen Webhook oder eine WebSocket-Verbindung
  - `assumed_state` — die Integration setzt Zustände ohne Read-Back vom Device
  - `calculated` — die Integration leitet ihren Zustand aus anderen Entities ab (typisch für Helper-Integrationen)
- **SOLLTE [SHOULD]** `local_*` gegenüber `cloud_*` bevorzugen, wenn beide Wege technisch möglich sind — `local_*` ist offline-resilient und datenschutzfreundlicher

### Lifecycle-Eintrittspunkte

- **MUSS [MUST]** `__init__.py` mit `async_setup_entry(hass, entry) -> bool` exportieren — wird von HA pro Config-Entry einmal aufgerufen
- **MUSS [MUST]** `__init__.py` mit `async_unload_entry(hass, entry) -> bool` exportieren — wird beim Entfernen eines Config-Entry aufgerufen
- **SOLLTE [SHOULD]** alle Plattform-Aufnahmen über `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)` in `async_setup_entry` durchführen statt einzelner Plattform-Forwards
- **SOLLTE [SHOULD]** beim Unload `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` als Rückgabewert von `async_unload_entry` zurückgeben — alle Plattform-spezifischen Cleanup-Hooks laufen damit automatisch
- **KANN [MAY]** `async_migrate_entry(hass, entry) -> bool` exportieren, sobald sich das Schema von `entry.data` oder `entry.options` über Versionen ändert — `manifest.json:version` ist dann gleichzeitig die `entry.version`-Quelle
- **MUSS NICHT [MUST NOT]** `hass.data[DOMAIN][entry.entry_id]` als Speicherort für Coordinators / API-Clients / Listener verwenden; siehe `ha/runtime-data-pattern` für die verbindliche Alternative (`entry.runtime_data`)

### Quality-Scale-Markierung

- **SOLLTE [SHOULD]** in jeder Detail-Spec dieses Plugins (`ha/runtime-data-pattern`, `ha/config-flow-patterns`, `ha/coordinator-patterns`, `ha/entity-architecture`, …) pro Pattern explizit eine HA-Quality-Scale-Stufe markieren (`bronze` / `silver` / `gold` / `platinum`), damit Skill-Konsumenten wissen, auf welcher Stufe der generierte Code landet
- **KANN [MAY]** Patterns ohne klare Quality-Scale-Zuordnung als `unscaled` markieren, statt eine Stufe zu erfinden
- **MUSS [MUST]** beim Markieren die jeweils geltende HA-Quality-Scale-Definition referenzieren (Verweis auf `home-assistant/developers.home-assistant.io`), damit der Marker später überprüfbar bleibt

### Cross-Referenzen zu Folge-Specs

- `runtime_data`-Pattern, `KamerplanterRuntimeData`-Analogon, typisierte `ConfigEntry` → `ha/runtime-data-pattern`
- Config-Flow (User / Reauth / Reconfigure / Options) → `ha/config-flow-patterns`
- Discovery-Mechanismen (Zeroconf, DHCP, SSDP, MQTT, Bluetooth, USB) → `ha/zeroconf-discovery` plus Folge-Specs pro Mechanismus
- `DataUpdateCoordinator`-Topologie, Error-Mapping, Update-Intervalle → `ha/coordinator-patterns`
- Base-Entity, `has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`, `DeviceInfo`, `via_device` → `ha/entity-architecture` und `ha/device-registry`
- `services.yaml`, Selectors, Multi-Instance-Disambiguation → `ha/services`
- `strings.json`, `translations/<lang>.json`, Sync-Strategie → `ha/translations`
- `icons.json` → `ha/icons`
- Diagnostics + `async_redact_data` → `ha/diagnostics`
- Lovelace-Card-Auto-Registrierung in `__init__.py` → `ha/lovelace-card-patterns`
- Lokaler Dev-Loop (`kubectl cp`, `kill 1`) → `ha/dev-environment`
- Test-Harness → `ha/test-harness`
- Sicherheits-Hardening (Path-Whitelist, Bearer-Gating) → `ha/security-hardening`

## Akzeptanzkriterien

- [ ] `custom_components/<domain>/` existiert und enthält `manifest.json` plus `__init__.py`
- [ ] `manifest.json` enthält alle Pflichtfelder: `domain`, `name`, `codeowners`, `documentation`, `issue_tracker`, `iot_class`, `integration_type`, `version`, `loggers`, `requirements`
- [ ] `manifest.json:domain` matched den Ordnernamen unter `custom_components/`
- [ ] `manifest.json:domain` ist lowercase ASCII (`[a-z0-9_]+`), keine Bindestriche, keine Großbuchstaben
- [ ] `manifest.json:codeowners` ist eine nicht-leere Liste mit `@`-präfigierten GitHub-Handles
- [ ] `manifest.json:version` ist SemVer-konform
- [ ] `manifest.json:integration_type` ist genau einer aus `hub`, `device`, `service`, `system`, `helper`
- [ ] `manifest.json:iot_class` ist genau einer aus `local_polling`, `local_push`, `cloud_polling`, `cloud_push`, `assumed_state`, `calculated`
- [ ] `manifest.json:requirements` enthält keine ungetaggten Git-URLs; jeder Eintrag ist PyPI-installierbar und versionsgepinnt
- [ ] `__init__.py` exportiert `async_setup_entry` und `async_unload_entry`
- [ ] Es existiert kein primärer Integrations-Code außerhalb von `custom_components/<domain>/`
- [ ] Wenn `hacs.json` vorhanden ist: `name` ist gesetzt; `content_in_root: true` ist nicht gesetzt
- [ ] Folge-Specs unter `spec/ha/` markieren ihre Patterns mit einer HA-Quality-Scale-Stufe oder explizit als `unscaled`
- [ ] hassfest (`hacs/action@main` mit Category `Integration`) läuft im CI dieses Konsumenten-Repos fehlerfrei durch

## Offene Fragen

- **HA-Mindest-Version**: Welche Version pinnen wir portfolioweit in `hacs.json:homeassistant`? `nolte/kamerplanter-ha` nutzt `2024.1.0` — ist das der portfolioweite Anker oder pinnen wir aggressiver? Diese Frage stand bereits in `AUDIENCES.md` und wird hier referenziert.
- **`requirements`-Pinning-Stil**: `==1.2.3` (strikt) oder `~=1.2.3` (kompatibel) — gibt es eine Konvention oder bleibt das pro Integration entscheidbar?
- **Quality-Scale-Erst-Anwendung**: Welche Folge-Spec ist die erste, die diese Markierung tatsächlich anwendet? Bauen wir parallel zu jeder Folge-Spec einen Quality-Scale-Anhang oder konsolidieren wir alle Markierungen in einer dedizierten `ha/quality-scale-mapping`-Spec?
- **Discovery-Specs-Reihenfolge**: Reicht `ha/zeroconf-discovery` als erste Discovery-Spec (kamerplanter-ha verwendet Zeroconf) oder ziehen wir DHCP/SSDP/MQTT/Bluetooth/USB sofort mit?
- **`dependencies` vs. `after_dependencies`**: HA bietet beide Schlüssel — wann verlangt die Spec den einen vs. den anderen? Aktuell nicht differenziert; klärt sich, sobald die erste Integration mit echter HA-Komponent-Abhängigkeit auftaucht.
- **Sprach-Konvention für Custom-Integration-Code**: `nolte/kamerplanter-ha` verlangt englischen Source-Code (Variable, Class, Function, Strings); Doku-Kommentare dürfen Deutsch sein. Soll diese Regel hier in der Foundation-Spec stehen oder gehört sie in `ha/translations`?
- **HACS-Pflicht-vs.-Kür**: Sollen Skills standardmäßig HACS-konformes Layout erzeugen oder ist HACS optional? `AUDIENCES.md` markiert das als offene Frage gegenüber dem HACS-Steward.
