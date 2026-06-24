# HA-Integration: Discovery-Mechanismen (DHCP/SSDP/USB/HomeKit)

Status: draft

## Kontext

Eine Integration sollte den User nicht zwingen, IP-Adresse, Host oder Geräte-Identifier manuell einzutippen, wenn HA das Gerät auf dem Netzwerk oder am USB-Bus selbst entdecken kann. Die Quality-Scale-Regel `discovery` (Gold) listet als unterstützte Discovery-Methoden explizit App, Bluetooth, DHCP, HomeKit, mDNS, MQTT, SSDP und USB. Discovery reduziert den Setup-Aufwand erheblich — der User muss nicht nachschlagen, welche Integration zum Gerät passt, und keinen Host eintippen.

`ha/zeroconf-discovery` deckt den mDNS-/Zeroconf-Pfad bereits vollständig ab (Manifest-Key `zeroconf`, `async_step_zeroconf`, TXT-Record-Schema). Diese Spec adressiert ausschließlich die **anderen** Netzwerk- und Bus-Discovery-Mechanismen: **DHCP**, **SSDP/uPnP**, **USB** und **HomeKit** (plus **MQTT-Discovery**). Bluetooth-Discovery hat eine eigene Sibling-Spec (`ha/bluetooth`). Die Manifest-Matcher-Keys gehören in `ha/integration-manifest`; die Multi-Step-Flow-Konvention der Bestätigungs-Steps liegt in `ha/config-flow-patterns`. Diese Spec referenziert diese Siblings per Slug und dupliziert sie nicht.

Jeder Mechanismus folgt demselben Grundmuster: Das Manifest deklariert Matcher; bei einem Treffer lädt HA den passenden `dhcp`/`ssdp`/`usb`/`homekit`-Step des Config-Flows mit typisierter Discovery-Info. Eine netzwerkbasierte Discovery erlaubt zusätzlich, die Konfiguration zu aktualisieren, sobald ein Gerät eine neue IP-Adresse erhält — das ist die Gold-Regel `discovery-update-info`.

Quality-Scale-Marker: **Gold** (`discovery` und `discovery-update-info`).

## Ziele

- DHCP-, SSDP/uPnP-, USB- und HomeKit-Discovery als Standardmuster festschreiben, sobald das Gerät einen dieser Mechanismen anbietet
- Die Manifest-Matcher-Keys pro Mechanismus definieren (`dhcp`, `ssdp`, `usb`, `homekit`, `mqtt`) und was jeder Matcher auslöst
- Die Config-Flow-Discovery-Steps (`async_step_dhcp`, `async_step_ssdp`, `async_step_usb`, `async_step_homekit`) mit ihren typisierten Discovery-Info-Objekten etablieren
- Den Entry-Update-Pfad aus Discovery (`discovery-update-info`) verbindlich machen: `unique_id` setzen, `_abort_if_unique_id_configured(updates=...)` zum Nachziehen von Host/IP
- Die Abgrenzung zu `ha/zeroconf-discovery` und `ha/bluetooth` sauber halten — kein doppeltes mDNS-/Bluetooth-Material

## Nicht-Ziele

- mDNS-/Zeroconf-Discovery — vollständig in `ha/zeroconf-discovery`, nicht hier dupliziert
- Bluetooth-Discovery — eigene Sibling-Spec `ha/bluetooth`
- Die generischen Manifest-Schema-Regeln (Pflichtfelder, `dependencies`, `quality_scale`) — `ha/integration-manifest`
- Die Multi-Step-Flow-Mechanik der Bestätigungs-Steps im Detail — `ha/config-flow-patterns`
- HA-interne Discovery-Cache- und Listener-Implementation — HA-internes Detail; das Plugin verlässt sich auf die HA-Garantien

## Anforderungen

### DHCP

- **MUSS [MUST]** `manifest.json:dhcp` als Liste von Matcher-Dictionaries setzen, wenn die Integration DHCP-Discovery unterstützt — HA lauscht dann passiv und lädt den `dhcp`-Step, sobald ein Gerät matcht
- **MUSS [MUST]** je Matcher mindestens einen der Schlüssel `hostname` (Unix-fnmatch-Pattern), `macaddress` (OUI-Prefix) oder `registered_devices: true` angeben — Discovery passiert, wenn **alle** Items **irgendeines** Matchers in den DHCP-Daten gefunden werden
- **SOLLTE [SHOULD]** `registered_devices: true` setzen, wenn die Integration nur IP-Updates für bereits eingerichtete Geräte empfangen will und ein `hostname`-/OUI-Match zu breit wäre — Voraussetzung ist eine Device-Registry-Eintragung der MAC über `CONNECTION_NETWORK_MAC`
- **SOLLTE [SHOULD]** `zeroconf` oder `ssdp` gegenüber `dhcp` bevorzugen, wenn das Gerät sie anbietet — sie liefern generell die bessere User-Experience
- **MUSS NICHT [MUST NOT]** allein auf einen generischen `hostname`- oder OUI-Matcher setzen, der fremde Geräte mitfängt — der Config-Flow muss Duplikate selbst herausfiltern

### SSDP/uPnP

- **MUSS [MUST]** `manifest.json:ssdp` als Liste von Matcher-Dictionaries setzen, wenn die Integration SSDP-Discovery unterstützt — HA lädt dann den `ssdp`-Step
- **MUSS [MUST]** Matcher gegen SSDP-/uPnP-Daten formulieren: SSDP-Header `st`, `usn`, `ext`, `server` (Header-Namen lowercase) oder Felder der uPnP-Device-Description wie `manufacturer` und `deviceType` — Discovery passiert, wenn **alle** Items **irgendeines** Matchers gefunden werden
- **KANN [MAY]** `ssdp.async_register_callback(hass, cb, {"st": ...})` aus `homeassistant.components.ssdp` nutzen, um zur Laufzeit Callbacks auf neue Treffer zu erhalten — dasselbe Matcher-Format wie im Manifest, und die Registrierung wird über `entry.async_on_unload(...)` wieder aufgeräumt
- **MUSS NICHT [MUST NOT]** annehmen, dass HA Duplikate über mehrere uPnP-Services derselben `UDN` auflöst — der Config-Flow filtert Duplikate selbst

### USB

- **MUSS [MUST]** `manifest.json:usb` als Liste von Matcher-Dictionaries setzen, wenn die Integration USB-Discovery unterstützt — HA lädt den `usb`-Step beim Start, beim Öffnen der Integrationsseite und beim Einstecken (sofern `pyudev` verfügbar)
- **MUSS [MUST]** Matcher aus den USB-Deskriptor-Werten bilden: `vid` (Vendor-ID), `pid` (Device-ID), `serial_number`, `manufacturer`, `description` — Discovery passiert, wenn **alle** Items **irgendeines** Matchers in den USB-Daten gefunden werden
- **MUSS [MUST]** bei generischen Bridge-Chips (z. B. `vid: 10C4` / `pid: EA60`, Silicon-Labs-CP2102) zusätzlich auf `description` oder einen weiteren Identifier matchen — sonst löst eine unerwartete Discovery aus
- **KANN [MAY]** `usb.async_is_plugged_in(hass, {...})` aus `homeassistant.components.usb` nutzen, um in `async_setup_entry` zu prüfen, ob der Adapter steckt, und sonst `ConfigEntryNotReady` zu werfen

### HomeKit

- **MUSS [MUST]** `manifest.json:homekit` mit dem Schlüssel `models` als Liste von Modellnamen setzen, wenn die Integration HomeKit-Discovery unterstützt — HA lädt den `homekit`-Step, wenn das `zeroconf`-Integration geladen ist
- **MUSS [MUST]** beachten, dass HomeKit-Discovery per Prefix-Match arbeitet: Sie greift, wenn der entdeckte Modellname mit **irgendeinem** der gelisteten Modellnamen **beginnt**
- **KANN [MAY]** das Gerät mit einem beliebigen Protokoll ansprechen — eine `homekit`-Manifest-Deklaration verpflichtet nicht dazu, das HomeKit-Protokoll zu sprechen
- **MUSS NICHT [MUST NOT]** erwarten, dass dieselbe Discovery-Info zusätzlich an HomeKit-Zeroconf-Listener geht — sobald sie wegen des `homekit`-Manifest-Eintrags an die Integration geroutet wird, erreicht sie diese Listener nicht mehr

### MQTT-Discovery

- **MUSS [MUST]** `manifest.json:mqtt` als Liste von MQTT-Topics setzen, wenn die Integration MQTT-Discovery unterstützt — HA lädt den `mqtt`-Step, wenn das `mqtt`-Integration geladen ist, durch Subscribe auf die gelisteten Topics
- **MUSS [MUST]** `mqtt` zu `dependencies` im Manifest hinzufügen, wenn die Integration MQTT zwingend braucht (siehe `ha/integration-manifest`)
- **SOLLTE [SHOULD]** vor dem Subscribe mit `await mqtt.async_wait_for_mqtt_client(hass)` auf die Verfügbarkeit des MQTT-Clients warten — der Aufruf blockiert und liefert `True`, sobald der Client verfügbar ist

### Config-Flow-Discovery-Steps

- **MUSS [MUST]** für jeden deklarierten Manifest-Matcher den passenden Step in `config_flow.py` implementieren: `async_step_dhcp(self, discovery_info: DhcpServiceInfo)`, `async_step_ssdp(self, discovery_info: SsdpServiceInfo)`, `async_step_usb(self, discovery_info: UsbServiceInfo)`, `async_step_homekit(self, discovery_info: ZeroconfServiceInfo)` — jeder empfängt seine typisierte Discovery-Info
- **MUSS [MUST]** in einen Bestätigungs-Step weiterleiten (typisch `async_step_discovery_confirm` mit `self._set_confirm_only()`), bevor `async_create_entry` aufgerufen wird — niemals einen Entry anlegen, ohne dass der User die Discovery bestätigt hat
- **SOLLTE [SHOULD]** die Backend-/Geräte-Validierung (Test-Connection) im Discovery-Step ausführen und bei Fehlschlag `self.async_abort(reason="cannot_connect")` zurückgeben, bevor in den Bestätigungs-Step verzweigt wird
- **SOLLTE [SHOULD]** die Multi-Step-Flow-Konvention aus `ha/config-flow-patterns` nutzen, wenn Bestätigung plus Auth plus Auswahl nötig sind

### Entry-Update aus Discovery

- **MUSS [MUST]** im Discovery-Step die `unique_id` aus einem stabilen Geräte-Identifier setzen — `await self.async_set_unique_id(<stable_id>)` — und unmittelbar danach `self._abort_if_unique_id_configured(updates={CONF_HOST: host})` aufrufen (Gold-Regel `discovery-update-info`)
- **MUSS [MUST]** die IP-/Host-Aktualisierung nur durchführen, wenn die Integration sicher ist, dass es sich um dasselbe zuvor eingerichtete Gerät handelt — die `unique_id`-Gleichheit ist genau dieser Beweis
- **MUSS [MUST]** bei DHCP für IP-Update-Flows die MAC-Adresse in der Device-Info registrieren und `registered_devices: true` im Manifest setzen — sonst entstehen keine Discovery-Flows für IP-Updates bereits eingerichteter Geräte
- **MUSS NICHT [MUST NOT]** bei Re-Discovery desselben Geräts einen zweiten Entry anlegen — `_abort_if_unique_id_configured` bricht den Flow ab und zieht stattdessen die neuen Endpoint-Daten nach

## Akzeptanzkriterien

- [ ] `manifest.json:dhcp` ist eine Liste von Matcher-Dictionaries mit `hostname`/`macaddress`/`registered_devices`, und `config_flow.py` enthält `async_step_dhcp(self, discovery_info: DhcpServiceInfo)`
- [ ] `manifest.json:ssdp` ist eine Liste von Matcher-Dictionaries (`st`/`manufacturer`/`deviceType` …), und `config_flow.py` enthält `async_step_ssdp(self, discovery_info: SsdpServiceInfo)`
- [ ] `manifest.json:usb` ist eine Liste von Matcher-Dictionaries (`vid`/`pid`/`serial_number`/`manufacturer`/`description`), und `config_flow.py` enthält `async_step_usb(self, discovery_info: UsbServiceInfo)`
- [ ] `manifest.json:homekit` setzt `models` als Liste von Modellname-Prefixen, und `config_flow.py` enthält `async_step_homekit(self, discovery_info)`
- [ ] `manifest.json:mqtt` ist eine Liste von Topics, `mqtt` steht bei Bedarf in `dependencies`, und es wird mit `async_wait_for_mqtt_client` gewartet
- [ ] Jeder Discovery-Step leitet in einen Bestätigungs-Step weiter — niemals direkter `async_create_entry` ohne User-Bestätigung
- [ ] Jeder Discovery-Step setzt `unique_id` und ruft `_abort_if_unique_id_configured(updates={...})` zum Nachziehen von Host/IP
- [ ] Für DHCP-IP-Updates ist die MAC in der Device-Info registriert und `registered_devices: true` im Manifest gesetzt
- [ ] Quality-Scale-Marker: **Gold** (`discovery`, `discovery-update-info`)

## Offene Fragen

- **MQTT-Abgrenzung**: MQTT-Discovery teilt das Matcher-/Step-Muster, ist aber Topic- statt Netzwerk-basiert. Bleibt sie in dieser Spec, oder verdient sie eine eigene `ha/mqtt-discovery`, sobald der erste MQTT-Skill anlegt?
- **`registered_devices`-Pflicht**: Soll `registered_devices: true` für IP-Update-Flows von SOLLTE auf MUSS hochgezogen werden, sobald die Integration `discovery-update-info` (Gold) anstrebt?
- **Stabiler Identifier pro Mechanismus**: Zeroconf nutzt einen TXT-`instance_id`. Welcher Identifier ist pro Mechanismus die kanonische `unique_id`-Quelle (DHCP-MAC, SSDP-`udn`, USB-`serial_number`, HomeKit-Modell + ID)? Aktuell als „stabiler Geräte-Identifier" generisch gehalten.
- **HomeKit-vs-Zeroconf-Routing**: Der `homekit`-Eintrag entzieht die Discovery-Info den HomeKit-Zeroconf-Listenern. Braucht es eine Cross-Reference-Regel mit `ha/zeroconf-discovery`, um Doppel-Deklarationen zu vermeiden?
- **Combined-Discovery**: Sollten Integrationen, die mehrere Mechanismen gleichzeitig deklarieren (z. B. SSDP + DHCP für IP-Updates), ein gemeinsames Bestätigungs-Step-Pattern teilen, oder bleibt jeder Step eigenständig?
