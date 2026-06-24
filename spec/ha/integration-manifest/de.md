# HA-Integration: `manifest.json`

Status: draft

## Kontext

Jede Home-Assistant-Integration besitzt eine Manifest-Datei, die ihre Basis-Informationen beschreibt. Diese Datei liegt als `manifest.json` im Integrations-Verzeichnis (`custom_components/<domain>/manifest.json`) und ist verpflichtend — ohne sie lädt HA die Integration nicht. Das Manifest deklariert Identität (`domain`, `name`), Abhängigkeiten, Klassifizierung (`integration_type`, `iot_class`), Feature-Flags (`config_flow`, `quality_scale`) und optionale Discovery-Matcher (`zeroconf`, `ssdp`, `dhcp`, `bluetooth`, `usb`, `homekit`, `mqtt`).

Diese Spec deckt das Manifest aus Sicht einer **Custom Integration** ab (Distribution typischerweise über HACS), nicht aus Sicht einer Core-Integration. Der wichtigste Unterschied: Der `version`-Key ist für Custom Integrations **verpflichtend**, während er für Core-Integrationen weggelassen werden muss. Mehrere Manifest-Felder verhalten sich für Custom Integrations anders als für Core (`dependencies`/`after_dependencies` dürfen Custom-Integrationen referenzieren; `requirements` sollen nur Pakete enthalten, die Core nicht ohnehin liefert; Virtual Integrations sind ausschließlich Core).

Quality-Scale-Relevanz: Mehrere Manifest-Felder sind direkt an Quality-Scale-Regeln gekoppelt — `codeowners` erfüllt die „integration-owner"-Regel (jede Integration braucht einen Eigentümer), und `requirements` muss die „dependency-transparency"-Regel erfüllen (Dependencies müssen unter OSI-Lizenz auf PyPI verfügbar und exakt gepinnt sein). Querverweise: `ha/config-flow-patterns` (für `config_flow`), `ha/zeroconf-discovery` (für die Discovery-Keys), `ha/quality-scale` (für `quality_scale`), `ha/integration-architecture` (für den Gesamtaufbau einer Integration).

## Ziele

- Pflicht-Keys (`domain`, `name`) und ihre Namensregeln verbindlich festschreiben
- Den für Custom Integrations verpflichtenden `version`-Key absichern und vom Core-Verhalten abgrenzen
- Abhängigkeits-Deklaration (`dependencies`, `after_dependencies`, `requirements`) korrekt und transparent erzwingen
- Klassifizierung (`integration_type`, `iot_class`) explizit setzen, statt sich auf Defaults zu verlassen
- Feature-Flags (`config_flow`, `quality_scale`) konsistent mit den vorhandenen Code-Artefakten halten
- Discovery-Keys nur dann setzen, wenn die Integration die jeweilige Discovery tatsächlich unterstützt
- Identitäts-Metadaten (`codeowners`, `documentation`, `issue_tracker`, `loggers`) so pflegen, dass die zugehörigen Quality-Scale-Regeln erfüllt sind

## Nicht-Ziele

- Virtual Integrations (`integration_type: virtual`, `supported_by`, `iot_standards`) — laut HA-Doku ausschließlich von Home Assistant Core bereitstellbar, nicht von Custom Integrations
- Brand-Images und das `brands`-Repository — eigene Folge-Spec, sobald sie konkret nötig wird
- Die inhaltliche Implementierung des Config-Flows hinter `config_flow: true` — fällt in `ha/config-flow-patterns`
- Die konkreten Anforderungen je Quality-Scale-Stufe hinter `quality_scale` — fällt in `ha/quality-scale`
- Die Matcher-Detailsemantik der Discovery-Keys (Wildcard-Syntax, UUID-Konvertierung) — fällt in `ha/zeroconf-discovery`

## Anforderungen

### Pflicht-Keys

- **MUSS [MUST]** einen `domain`-Key setzen, der nur aus Kleinbuchstaben und Unterstrichen besteht, projektweit eindeutig ist und exakt dem Verzeichnisnamen entspricht, in dem die `manifest.json` liegt
- **MUSS NICHT [MUST NOT]** die `domain` nach dem ersten Release ändern — sie ist als unveränderlich dokumentiert
- **MUSS [MUST]** einen `name`-Key mit dem menschenlesbaren Integrations-Namen setzen
- **SOLLTE [SHOULD]** die Namensregeln befolgen: bei reinen Cloud-Integrationen das Suffix „Cloud" anhängen (z. B. „LIFX Cloud"), bei lokalen oder hybriden Varianten den reinen Produktnamen ohne Suffix verwenden (kein „Local"), bei inhärent cloud-basierten Produkten den Namen unverändert lassen (z. B. „iCloud", nicht „iCloud Cloud")

### Identität & Metadaten (codeowners, documentation, issue_tracker, version)

- **MUSS [MUST]** `codeowners` als Array von GitHub-Usernamen oder Team-Namen setzen und mindestens den eigenen GitHub-Usernamen aufnehmen — dies erfüllt die Quality-Scale-Regel „integration-owner", nach der jede Integration einen Eigentümer braucht
- **MUSS [MUST]** `documentation` als URL zur Nutzungs-Dokumentation der Integration setzen
- **SOLLTE [SHOULD]** `issue_tracker` als URL zum Issue-Tracker setzen, damit Nutzer Fehler an der richtigen Stelle melden — bei einer Einreichung in Core wird dieser Key weggelassen, weil Core den Link automatisch generiert
- **MUSS [MUST]** für eine Custom Integration den `version`-Key setzen; der Wert muss eine von [AwesomeVersion](https://github.com/ludeeus/awesomeversion) akzeptierte Version sein (CalVer oder SemVer) — dies weicht bewusst vom Core-Verhalten ab, wo `version` weggelassen werden muss
- **KANN [MAY]** `loggers` als Array der Logger-Namen setzen, die die Requirements der Integration in ihren `getLogger`-Aufrufen verwenden

### Abhängigkeiten (dependencies, after_dependencies, requirements)

- **MUSS [MUST]** in `dependencies` nur Integrationen aufführen, die vor dieser Integration **erfolgreich aufgesetzt** sein müssen (harte Abhängigkeit); eine Custom Integration darf sowohl Built-in- als auch Custom-Integrationen referenzieren
- **SOLLTE [SHOULD]** `after_dependencies` statt `dependencies` verwenden, wenn eine Abhängigkeit optional, aber nicht kritisch ist — HA wartet dann auf die gelisteten Integrationen, sofern sie konfiguriert sind, und installiert deren Requirements, ohne das Setup zu erzwingen, wenn sie nicht konfiguriert sind
- **MUSS [MUST]** `requirements` als Array `pip`-kompatibler Strings setzen, in denen jede Python-Library mit `==` exakt gepinnt ist (z. B. `"aiohue==1.9.1"`) — dies erfüllt die Quality-Scale-Regel „dependency-transparency" (OSI-Lizenz, PyPI-Verfügbarkeit, getaggtes Release)
- **MUSS NICHT [MUST NOT]** in `requirements` Pakete aufführen, die bereits von Cores [requirements.txt](https://github.com/home-assistant/core/blob/dev/requirements.txt) bereitgestellt werden — eine Custom Integration listet nur ihre zusätzlichen Requirements

### Klassifizierung (integration_type, iot_class)

- **MUSS [MUST]** `integration_type` explizit setzen, statt sich auf den Default `hub` zu verlassen — gültige Werte sind `device`, `entity`, `hardware`, `helper`, `hub`, `service`, `system`, `virtual`; `hub` ist ein Gateway zu mehreren Geräten/Services, `device`/`service` versorgen pro Config-Entry genau ein Gerät bzw. einen Service
- **MUSS [MUST]** `iot_class` setzen, und zwar auf genau einen der akzeptierten Werte: `assumed_state`, `cloud_polling`, `cloud_push`, `local_polling`, `local_push` oder `calculated`
- **MUSS NICHT [MUST NOT]** für eine Custom Integration `integration_type: virtual` setzen — Virtual Integrations sind laut HA-Doku ausschließlich Core vorbehalten

### Feature-Flags (config_flow, quality_scale)

- **MUSS [MUST]** `config_flow: true` setzen, sobald die Integration einen Config-Flow bereitstellt; in diesem Fall **muss** die Datei `config_flow.py` existieren (siehe `ha/config-flow-patterns`)
- **KANN [MAY]** `single_config_entry: true` setzen, wenn die Integration nur genau einen Config-Entry unterstützt — HA verhindert dann das Anlegen weiterer Entries
- **SOLLTE [SHOULD]** `quality_scale` auf die erreichte Stufe setzen (`bronze`, `silver`, `gold`, `platinum`); neue Integrationen müssen mindestens Bronze erfüllen (siehe `ha/quality-scale`)

### Discovery-Keys

- **MUSS [MUST]** einen Discovery-Key (`zeroconf`, `ssdp`, `dhcp`, `bluetooth`, `usb`, `homekit`, `mqtt`) nur setzen, wenn die Integration die jeweilige Discovery tatsächlich unterstützt und der zugehörige Config-Flow-Step existiert — die Matcher-Detailsemantik regelt `ha/zeroconf-discovery`
- **SOLLTE [SHOULD]** generische `zeroconf`-Typen (`_http._tcp.local.`, `_printer._tcp.local.` etc.) mit einem `name`- oder `properties`-Filter einschränken, damit fremde Geräte nicht fälschlich diese Integration triggern
- **KANN [MAY]** in einem `dhcp`-Matcher `registered_devices: true` setzen, um IP-Adress-Updates für bereits per MAC registrierte Geräte zu empfangen, wenn ein `hostname`- oder `oui`-Match zu breit wäre
- **MUSS [MUST]** bei einer Integration, die `mqtt`-Discovery nutzt oder MQTT benötigt, `mqtt` zusätzlich in `dependencies` aufnehmen und vor dem Subscribe mit `await mqtt.async_wait_for_mqtt_client(hass)` auf den Client warten

### Custom-Integration-Besonderheiten

- **MUSS [MUST]** den `version`-Key gesetzt haben — für eine Custom Integration (und damit für jede HACS-distribuierte Integration) ist er verpflichtend, andernfalls verweigert HA das Laden; beim Überschreiben einer Core-Integration im `custom_components`-Verzeichnis ist `version` ebenfalls verpflichtend
- **SOLLTE [SHOULD]** eine HACS-distribuierte Integration den `version`-Wert bei jedem Release erhöhen, damit HACS Updates erkennt und ausspielt
- **MUSS [MUST]** das Manifest so halten, dass `domain` und Verzeichnisname unter `custom_components/<domain>/` übereinstimmen — dies ist die einzige Stelle, an der HA die Integration findet (`<config>/custom_components/<domain>`)

## Akzeptanzkriterien

- [ ] `domain` ist gesetzt, nur Kleinbuchstaben/Unterstriche, eindeutig und gleich dem Verzeichnisnamen
- [ ] `name` ist gesetzt und folgt den Cloud-/Local-Namensregeln
- [ ] `codeowners` enthält mindestens einen GitHub-Usernamen (integration-owner-Regel erfüllt)
- [ ] `documentation` ist als URL gesetzt
- [ ] `version` ist gesetzt und eine gültige AwesomeVersion (CalVer/SemVer)
- [ ] `requirements` pinnt jede Library exakt mit `==` und enthält keine bereits von Core gelieferten Pakete (dependency-transparency-Regel erfüllt)
- [ ] `dependencies` / `after_dependencies` sind korrekt nach hart/optional getrennt
- [ ] `integration_type` ist explizit gesetzt und nicht `virtual`
- [ ] `iot_class` ist auf genau einen der sechs akzeptierten Werte gesetzt
- [ ] `config_flow: true` ist genau dann gesetzt, wenn `config_flow.py` existiert
- [ ] Jeder gesetzte Discovery-Key entspricht einem real unterstützten Discovery-Pfad mit zugehörigem Config-Flow-Step
- [ ] Bei MQTT-Discovery ist `mqtt` zusätzlich in `dependencies` aufgeführt
- [ ] `manifest.json` ist valides JSON und liegt unter `custom_components/<domain>/`

## Offene Fragen

- **`quality_scale`-Pflichtgrad**: Verlangt diese Spec für jede gescaffoldete Custom Integration mindestens `bronze`, oder bleibt das Setzen von `quality_scale` optional, solange die Integration nicht in Core eingereicht wird? Die HA-Doku verlangt Bronze nur für neue Core-Integrationen.
- **`loggers`-Verbindlichkeit**: Sollte `loggers` zur Pflicht werden, sobald die Integration externe Libraries mit eigenem Logging einbindet, oder bleibt es `KANN`? Die Doku beschreibt nur den Zweck, nicht die Pflicht.
- **Discovery-Matcher-Validierung**: Soll diese Spec eine Validierung der Discovery-Matcher (z. B. Lowercase-Properties bei `zeroconf`, Byte-Range bei `bluetooth.manufacturer_data_start`) erzwingen, oder delegiert sie das vollständig an `ha/zeroconf-discovery`?
- **`single_config_entry`-Heuristik**: Wann verlangt die Spec `single_config_entry: true`? Aktuell ist es `KANN` — eine Heuristik (genau ein Account/Gateway pro Installation) fehlt.
- **Version-Bump-Automatisierung**: Soll der Skill-Scaffold den `version`-Bump bei HACS-Releases automatisieren oder dem Release-Workflow überlassen?
