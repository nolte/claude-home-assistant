# Skill: `ha-discovery-augment`

Status: draft

## Kontext

`ha/discovery-mechanisms` definiert die Netzwerk- und Bus-Discovery jenseits von mDNS/Zeroconf: **DHCP**, **SSDP/uPnP**, **USB**, **HomeKit** und **MQTT-Discovery**. Jeder Mechanismus folgt demselben Muster — das Manifest deklariert Matcher (`dhcp`/`ssdp`/`usb`/`homekit`/`mqtt`), bei einem Treffer lädt HA den passenden Config-Flow-Step mit typisierter Discovery-Info, und ein netzwerkbasierter Mechanismus zieht über `unique_id` + `_abort_if_unique_id_configured(updates=...)` neue Host/IP-Daten nach (Gold-Regel `discovery-update-info`). Der `ha-integration-scaffold`-Skill erzeugt nur den **Zeroconf**-Pfad (`ha/zeroconf-discovery`); die übrigen Mechanismen hat bislang kein Skill ergänzt. In der Praxis vergessen Entwickler den Bestätigungs-Step (direkter `async_create_entry` ohne User-Bestätigung), den `unique_id`-Update-Pfad (zweiter Entry bei Re-Discovery) oder matchen zu breit (generische OUI-/Bridge-Chip-Matcher fangen fremde Geräte).

Dieser Skill ergänzt **einen** Discovery-Mechanismus (DHCP/SSDP/USB/HomeKit/MQTT) in einer **bestehenden** Integration: er setzt den Manifest-Matcher, implementiert den `async_step_<mechanismus>`-Step in `config_flow.py`, leitet in einen Bestätigungs-Step und verdrahtet den `unique_id`/`discovery-update-info`-Pfad — spec-konform zu `ha/discovery-mechanisms`. Er ergänzt das Scaffold-Zeroconf um die Gold-Regel `discovery`.

## Scope

Ergänzung genau eines Discovery-Mechanismus pro Lauf (`dhcp`, `ssdp`, `usb`, `homekit`, `mqtt`) in einer bestehenden `custom_components/<domain>/`-Integration: der Manifest-Matcher-Key, der typisierte `async_step_<mechanismus>` in `config_flow.py`, die Weiterleitung in den Bestätigungs-Step und der `unique_id` + `_abort_if_unique_id_configured(updates=...)`-Pfad. Der Skill liest `ha/discovery-mechanisms` und validiert.

## Ziele

- Aus einer beschriebenen Geräte-Discovery-Situation den richtigen Mechanismus wählen und spec-konform ergänzen (Manifest-Matcher + Config-Flow-Step)
- Den Matcher eng genug formulieren, damit keine fremden Geräte mitgefangen werden (OUI-/Bridge-Chip-Schärfung)
- Jeden Discovery-Step in einen Bestätigungs-Step leiten — niemals direkter `async_create_entry` ohne User-Bestätigung
- Den `discovery-update-info`-Pfad verbindlich machen: `unique_id` aus stabilem Identifier, `_abort_if_unique_id_configured(updates=...)` zum Nachziehen von Host/IP
- Scharf gegen `ha/zeroconf-discovery` (mDNS) und `ha/bluetooth` abgrenzen — kein doppeltes Material

## Nicht-Ziele

- mDNS/Zeroconf-Discovery — `ha/zeroconf-discovery` (vom Scaffold erzeugt)
- Bluetooth-Discovery — eigene Schwester-Spec `ha/bluetooth`
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`
- Die generische Config-Flow-Multi-Step-Mechanik (Auth, Auswahl) im Detail — `ha-config-flow-augment` / `ha/config-flow-patterns`
- Die generischen Manifest-Schema-Regeln — `ha/integration-manifest`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add DHCP / SSDP / USB / HomeKit / MQTT discovery to the integration"
  - „discover the device by MAC / vid:pid / model / SSDP service"
  - „update the host when the device gets a new IP"
  - „füge DHCP-/SSDP-/USB-/HomeKit-Discovery hinzu", „entdecke das Gerät über die MAC / vid:pid"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und den Mechanismus bzw. die Discovery-Situation (Prosa), aus der der Skill den Mechanismus ableitet und bestätigt
- **KANN [MAY]** erfassen: die Matcher-Werte je Mechanismus (`hostname`/`macaddress`/`registered_devices`; `st`/`manufacturer`/`deviceType`; `vid`/`pid`/`serial_number`/`description`; `models`; `mqtt`-Topics) und die `unique_id`-Quelle

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` und `config_flow.py` existieren; `domain` lesen
- **MUSS [MUST]** den Mechanismus auflösen und gegen die Abgrenzung prüfen: ist die Situation mDNS/Zeroconf (→ `ha/zeroconf-discovery`/Scaffold) oder Bluetooth (→ `ha/bluetooth`), **MUSS [MUST]** der Skill umlenken statt einen falschen Mechanismus zu ergänzen
- **MUSS [MUST]** die `ha/discovery-mechanisms`-Spec lesen
- **MUSS NICHT [MUST NOT]** einen bereits deklarierten Mechanismus-Matcher/Step überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (pro Mechanismus, aus `ha/discovery-mechanisms`)

- **MUSS [MUST]** den Manifest-Matcher als Liste von Matcher-Dictionaries unter dem passenden Schlüssel setzen — Discovery passiert, wenn **alle** Items **irgendeines** Matchers in den Discovery-Daten gefunden werden:
  - `dhcp`: mindestens einer von `hostname` (fnmatch), `macaddress` (OUI-Prefix), `registered_devices: true`
  - `ssdp`: SSDP-Header (`st`/`usn`/`server`, lowercase) oder uPnP-Felder (`manufacturer`/`deviceType`)
  - `usb`: `vid`/`pid`/`serial_number`/`manufacturer`/`description`
  - `homekit`: `models` als Liste von Modellname-**Prefixen** (Prefix-Match)
  - `mqtt`: Liste von Topics; `mqtt` zu `dependencies` ergänzen
- **MUSS [MUST]** bei generischen USB-Bridge-Chips (z. B. `vid: 10C4`/`pid: EA60`) zusätzlich auf `description` o. Ä. matchen, damit keine unerwartete Discovery auslöst
- **MUSS [MUST]** den passenden typisierten Step in `config_flow.py` implementieren: `async_step_dhcp(self, discovery_info: DhcpServiceInfo)`, `async_step_ssdp(self, discovery_info: SsdpServiceInfo)`, `async_step_usb(self, discovery_info: UsbServiceInfo)`, `async_step_homekit(self, discovery_info: ZeroconfServiceInfo)` bzw. der `mqtt`-Step
- **MUSS [MUST]** in einen Bestätigungs-Step weiterleiten (typisch `async_step_discovery_confirm` mit `self._set_confirm_only()`), bevor `async_create_entry` aufgerufen wird — nie ein Entry ohne User-Bestätigung
- **MUSS [MUST]** im Discovery-Step `await self.async_set_unique_id(<stabiler_id>)` setzen und unmittelbar `self._abort_if_unique_id_configured(updates={CONF_HOST: host})` aufrufen; ein zweiter Entry bei Re-Discovery ist verboten
- **MUSS [MUST]** für DHCP-IP-Update-Flows die MAC über `CONNECTION_NETWORK_MAC` in der Device-Info registrieren und `registered_devices: true` setzen
- **SOLLTE [SHOULD]** die Backend-Validierung (Test-Connection) im Discovery-Step ausführen und bei Fehlschlag `self.async_abort(reason="cannot_connect")` zurückgeben; für MQTT vor dem Subscribe `await mqtt.async_wait_for_mqtt_client(hass)` nutzen
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: Manifest-Matcher ist eine Liste von Dicts; der zugehörige `async_step_<mechanismus>` existiert in `config_flow.py`; jeder Step leitet in einen Bestätigungs-Step; jeder Step setzt `unique_id` + `_abort_if_unique_id_configured(updates=...)`; bei DHCP-Updates `registered_devices: true`
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/discovery-mechanisms` liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**Gold**: `discovery`, `discovery-update-info`)

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als einen Mechanismus pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** einen Discovery-Step einen Entry anlegen lassen, ohne dass der User die Discovery bestätigt
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill leitet den Mechanismus ab (oder erfragt ihn) und prüft die Abgrenzung zu Zeroconf/Bluetooth im Pre-Flight
- [ ] Der Manifest-Matcher ist eine Liste von Matcher-Dictionaries unter dem korrekten Schlüssel
- [ ] Der passende typisierte `async_step_<mechanismus>` existiert in `config_flow.py`
- [ ] Jeder Discovery-Step leitet in einen Bestätigungs-Step — kein direkter `async_create_entry`
- [ ] Jeder Discovery-Step setzt `unique_id` und ruft `_abort_if_unique_id_configured(updates={...})`
- [ ] Generische USB-Bridge-Chips tragen einen zusätzlichen `description`-Matcher
- [ ] Für DHCP-IP-Updates ist die MAC registriert und `registered_devices: true` gesetzt
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker **Gold**

## Offene Fragen

- **Stabiler Identifier pro Mechanismus**: Welche `unique_id`-Quelle ist kanonisch je Mechanismus (DHCP-MAC, SSDP-`udn`, USB-`serial_number`, HomeKit-Modell+ID)? Aktuell generisch als „stabiler Identifier"; der Skill fragt im Zweifel nach.
- **Combined-Discovery**: Wenn eine Integration mehrere Mechanismen anbietet (SSDP + DHCP für IP-Updates) — ein geteilter Bestätigungs-Step oder ein Mechanismus pro Lauf? Aktuell ein Mechanismus pro Lauf.
- **MQTT-Sonderfall**: MQTT-Discovery ist Topic- statt Netzwerk-basiert. Bleibt sie in diesem Skill oder verdient sie einen eigenen, sobald MQTT-Integrationen häufiger werden?
