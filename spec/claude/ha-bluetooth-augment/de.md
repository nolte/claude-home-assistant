# Skill: `ha-bluetooth-augment`

Status: draft

## Kontext

`ha/bluetooth` definiert, wie eine Custom Integration in Home Assistants geteilte `bluetooth`-Infrastruktur eintritt: über `manifest.json`-Matcher in die zentrale BLE-Discovery, über die Callback-APIs (`bluetooth.async_register_callback`) für advertisement-getriebenen Empfang, über die `bluetooth`-Lookup-APIs (`async_ble_device_from_address`, `async_last_service_info`, `async_address_present`, `async_scanner_count`) und über die spezialisierten Bluetooth-Coordinator-Familien — statt einen eigenen `BleakScanner` zu betreiben. Der Kern-Unterschied zur Polling-Welt ist die durchgängige `connectable`-Unterscheidung: viele Devices liefern ihre Daten ausschließlich über Advertisements; eine aktive Verbindung ist die Ausnahme. Bislang gibt es keinen Skill, der das ergänzt. Bluetooth ist Teil der Gold-Discovery-Familie (Quality-Scale-Marker: `discovery`), Schwester von `ha-discovery-augment`.

Dieser Skill ergänzt **eine bestehende** Integration um Bluetooth-Unterstützung — spec-konform zu `ha/bluetooth`: den `manifest.json`-`bluetooth`-Matcher (und `bluetooth_adapters` in `dependencies` bei Adapter-Nutzung), Advertisement-Callbacks mit `BluetoothCallbackMatcher` und `BluetoothScanningMode`, die passive bzw. aktive Coordinator-Familie und die Device-/Service-Info-Lookups. Der Skill liest `ha/bluetooth`, hält passive Datenbeschaffung als Default und validiert offline.

## Scope

Ergänzung von Bluetooth-Discovery und -Datenbeschaffung in einer bestehenden `custom_components/<domain>/`-Integration: der `bluetooth`-Matcher (`connectable`, `service_uuid`, `service_data_uuid`, `manufacturer_id`, `local_name`) in `manifest.json` (plus `bluetooth_adapters` in `dependencies` bei Adapter-Nutzung); die Advertisement-Registrierung über `bluetooth.async_register_callback(hass, callback, matcher, mode)` mit `@callback`-Signatur und Lifecycle-Bindung; die anwendungsfall-korrekte Bluetooth-Coordinator-Familie (`PassiveBluetoothProcessorCoordinator` / `ActiveBluetoothProcessorCoordinator` bzw. die DataUpdate-Varianten); die Lookups `async_ble_device_from_address` / `async_last_service_info` und das `bleak`/`bleak-retry-connector`-Verbindungs-Handling über den geteilten Scanner.

## Ziele

- Den `manifest.json`-`bluetooth`-Matcher aus den dokumentierten Feldern bilden, als Eintrittspunkt in die zentrale BLE-Discovery, und `bluetooth_adapters` in `dependencies` aufnehmen, wenn die Integration einen Adapter nutzt
- Advertisement-Empfang über `bluetooth.async_register_callback` mit `BluetoothCallbackMatcher` und explizitem `BluetoothScanningMode` erzwingen — statt einen eigenen `BleakScanner` zu betreiben
- Die `connectable`-Unterscheidung durchgängig verankern und passive Datenbeschaffung (`connectable=False`) als Default vorgeben
- Die richtige Bluetooth-Coordinator-Familie pro Anwendungsfall auswählen (Passive/Active Processor vs. DataUpdate) und gegen den generischen `DataUpdateCoordinator` abgrenzen
- Device-/Service-Info-Lookups über `async_ble_device_from_address` (inkl. `None`-Behandlung) und `async_last_service_info` standardisieren und robustes Verbindungs-Handling über den geteilten Scanner erzwingen

## Nicht-Ziele

- DHCP/SSDP/USB/HomeKit/Zeroconf-Netzwerk-Discovery — `ha-discovery-augment` / `ha/discovery-mechanisms`
- Der vollständige Config-Flow-Aufbau inkl. Bluetooth-Discovery-Step — `ha-config-flow-augment` / `ha/config-flow-patterns` (dieser Skill liefert nur Matcher und Auslösung)
- Der generische, polling-basierte `DataUpdateCoordinator` für REST-/Cloud-APIs — `ha/coordinator-patterns`
- Das Registrieren eigener externer Scanner (`async_register_scanner`) für Integrationen, die selbst einen Adapter bereitstellen — eigene Folge-Spec
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`; ESPHome-Bluetooth-Proxy-Konfiguration

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add bluetooth discovery / support", „listen for BLE advertisements", „discover this device over Bluetooth"
  - „use a passive/active bluetooth coordinator for this sensor"
  - „füge Bluetooth-Unterstützung hinzu", „höre auf BLE-Advertisements"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die Beschreibung, wie das Device sich ankündigt und ob es Daten nur über Advertisements liefert oder eine aktive Verbindung braucht
- **KANN [MAY]** erfassen: die Matcher-Felder (`service_uuid`, `service_data_uuid`, `manufacturer_id`, `local_name`, `connectable`), den `BluetoothScanningMode` (`PASSIVE`/`ACTIVE`) und die Coordinator-Familie

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** den Mechanismus abgrenzen: bei DHCP/SSDP/USB/HomeKit/Zeroconf nach `ha-discovery-augment` umleiten und stoppen; den Config-Flow-Discovery-Step an `ha-config-flow-augment` verweisen
- **MUSS [MUST]** die `ha/bluetooth`-Spec lesen
- **MUSS NICHT [MUST NOT]** einen bestehenden `bluetooth`-Matcher oder eine bestehende Callback-/Coordinator-Registrierung überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/bluetooth`)

- **MUSS [MUST]** den `bluetooth`-Schlüssel in `manifest.json` als Liste von Matcher-Dicts aus den dokumentierten Feldern setzen (`service_uuid`, `local_name`, `manufacturer_id`, `service_data_uuid`, `connectable`); **MUSS [MUST]** `bluetooth_adapters` in `dependencies` aufnehmen, wenn die Integration einen Adapter nutzt
- **SOLLTE [SHOULD]** `connectable` im Matcher passend zum Device setzen: `False`, wenn keine ausgehende Verbindung nötig ist, damit auch non-connectable Controller die Daten liefern; Default ist `True`
- **MUSS [MUST]** Advertisements über `bluetooth.async_register_callback(hass, callback, matcher, mode)` mit einem `BluetoothCallbackMatcher` (Format wie der Manifest-Eintrag, zusätzlich `address` erlaubt) und explizitem `bluetooth.BluetoothScanningMode` (`ACTIVE`/`PASSIVE`) abonnieren, wenn die Integration sofort über Advertisements informiert werden muss
- **MUSS [MUST]** den Callback als `@callback` (synchron, nicht-blockierend) mit der Signatur `(service_info: BluetoothServiceInfoBleak, change: BluetoothChange) -> None` implementieren und den zurückgegebenen Cancel-Callback via `entry.async_on_unload(...)` an den Entry-Lifecycle binden
- **MUSS [MUST]** Device-Lookups über `bluetooth.async_ble_device_from_address(hass, address, connectable)` beziehen und den `None`-Rückgabewert (kein Adapter in Reichweite) behandeln, statt einen zusätzlichen Scanner zu starten; **SOLLTE [SHOULD]** die jüngste Info über `bluetooth.async_last_service_info(hass, address, connectable)` lesen und beim Setup über `bluetooth.async_scanner_count(hass, connectable=True)` einen connectable Scanner prüfen, wenn die Integration verbinden muss
- **MUSS [MUST]** die Coordinator-Familie anwendungsfall-korrekt wählen: `PassiveBluetoothProcessorCoordinator` für Sensoren/Binary-Sensoren/Events aus Advertisements, `ActiveBluetoothProcessorCoordinator` bei Verbindungsbedarf, die DataUpdate-Varianten für Nicht-Sensor-Entitäten; den generischen `DataUpdateCoordinator` nur bei reiner Verbindungs-Kommunikation ohne Advertisements
- **MUSS [MUST]** bei Processor-Coordinators die Library-Daten in ein `PassiveBluetoothDataUpdate` (mit `devices`, `entity_descriptions`, `entity_names`, `entity_data`, indiziert über `PassiveBluetoothEntityKey`) formatieren, den Coordinator mit `address`, `mode` und `update_method` konstruieren und `coordinator.async_start()` erst nach `async_forward_entry_setups` an `entry.async_on_unload(...)` binden; bei den Active-Varianten im `needs_poll_method` `CoreState.running` und ein erreichbares connectable `BLEDevice` prüfen, bevor `poll_method` verbindet
- **MUSS [MUST]** für aktive Verbindungen den geteilten Scanner über `bluetooth.async_get_scanner(hass)` beziehen, pro Verbindung einen frischen `BleakClient` verwenden, einen Timeout ≥ 10 s setzen und `bleak-retry-connector` einsetzen; **MUSS NICHT [MUST NOT]** eine permanente Verbindung halten, wenn die Daten aus Advertisements verfügbar sind
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `manifest.json` trägt einen `bluetooth`-Matcher aus den dokumentierten Feldern (und `bluetooth_adapters` in `dependencies` bei Adapter-Nutzung); Advertisement-Abonnements laufen über `async_register_callback` mit `@callback`-Signatur und sind via `entry.async_on_unload(...)` gebunden; Device-Lookups nutzen `async_ble_device_from_address` mit `None`-Behandlung; passive Beschaffung (`connectable=False`) ist Default; die Coordinator-Familie ist anwendungsfall-korrekt; Processor-Coordinators formatieren `PassiveBluetoothDataUpdate` und starten nach `async_forward_entry_setups`; Verbindungen nutzen `async_get_scanner`, einen frischen `BleakClient`, Timeout ≥ 10 s und `bleak-retry-connector`
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/bluetooth` liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**Gold**: `discovery`)

### Verbote

- **MUSS NICHT [MUST NOT]** einen eigenen `BleakScanner` instanziieren — der geteilte Scanner ist verbindlich
- **MUSS NICHT [MUST NOT]** Netzwerk-Discovery (DHCP/SSDP/USB/HomeKit/Zeroconf) oder den Config-Flow-Discovery-Step in diesem Skill behandeln
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] `manifest.json` enthält einen `bluetooth`-Matcher aus den dokumentierten Feldern (`service_uuid`, `local_name`, `manufacturer_id`, `service_data_uuid`, `connectable`); `bluetooth_adapters` steht in `dependencies`, wenn die Integration einen Adapter nutzt
- [ ] Advertisement-Abonnements laufen über `bluetooth.async_register_callback` mit `BluetoothCallbackMatcher`, explizitem `BluetoothScanningMode` und `@callback`-Signatur `(BluetoothServiceInfoBleak, BluetoothChange)`
- [ ] Der Cancel-Callback ist via `entry.async_on_unload(...)` an den Lifecycle gebunden
- [ ] Device-Lookups nutzen `async_ble_device_from_address` und behandeln den `None`-Fall; Service-Info via `async_last_service_info`
- [ ] Passive Datenbeschaffung (`connectable=False`) ist Default; `connectable=True` nur bei tatsächlichem Verbindungsbedarf
- [ ] Die Coordinator-Familie ist anwendungsfall-korrekt gewählt (Passive/Active Processor vs. DataUpdate vs. generischer `DataUpdateCoordinator`)
- [ ] Processor-Coordinators formatieren `PassiveBluetoothDataUpdate` und starten via `async_start()` nach `async_forward_entry_setups`; Verbindungen nutzen `async_get_scanner`, frischen `BleakClient`, Timeout ≥ 10 s und `bleak-retry-connector`
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker **Gold** (`discovery`)

## Offene Fragen

- **Coordinator-Auswahl-Heuristik**: `ha/bluetooth` unterscheidet Processor- von DataUpdate-Coordinators primär nach „Sensor/Binary-Sensor/Event". Braucht der Skill eine schärfere Heuristik für Devices mit gemischten Entity-Typen, oder fragt er im Grenzfall nach?
- **`scan_interval`/`scan_duration`-Default**: Soll der Skill periodische Active-Scan-Fenster aktiv setzen oder den habluetooth-Default übernehmen? `ha/bluetooth` lässt eine Empfehlung pro Device-Klasse offen.
- **macOS-Unavailable-Verhalten**: CoreBluetooth cached Advertisements, sodass `_async_handle_unavailable` ggf. nie feuert. Soll der Skill ein Fallback-Verfügbarkeits-Pattern verlangen? Aktuell folgt er `ha/bluetooth` und weist nur hin.
