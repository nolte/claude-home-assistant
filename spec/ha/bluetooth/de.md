# HA-Integration: Bluetooth

Status: draft

## Kontext

Home Assistant stellt mit der `bluetooth`-Komponente eine geteilte Infrastruktur für BLE-Discovery, Advertisement-Empfang und Verbindungs-Vermittlung bereit. Eine Custom Integration tritt über `manifest.json`-Matcher in die zentrale Discovery ein, abonniert Advertisements über Callback-APIs und holt sich bei Bedarf `BLEDevice`-Objekte für aktive Verbindungen aus dem geteilten Scanner — statt einen eigenen `BleakScanner` zu betreiben.

Der Kern-Unterschied zur generischen Polling-Welt ist die **advertisement-getriebene** Datenbeschaffung: HA unterstützt remote Bluetooth-Controller, von denen einige nur Advertisements empfangen und keine ausgehenden Verbindungen aufbauen können. Daraus folgt die durchgängige Unterscheidung zwischen `connectable` und non-connectable Devices. Viele Sensoren brauchen ausschließlich Advertisements; eine aktive Verbindung ist die Ausnahme, nicht die Regel.

Für die Datenbeschaffung bietet HA spezialisierte Coordinator-Familien (`PassiveBluetoothProcessorCoordinator`, `ActiveBluetoothProcessorCoordinator`, `PassiveBluetoothDataUpdateCoordinator`, `ActiveBluetoothDataUpdateCoordinator`), die durch eingehende Advertisements statt durch Polling getrieben werden. Diese Spec grenzt sich gegen `ha/coordinator-patterns` ab, das den generischen, polling-basierten `DataUpdateCoordinator` für API-/Device-Endpunkte definiert — die Bluetooth-Coordinators sind eine eigene Familie und werden hier behandelt.

## Ziele

- `manifest.json`-`bluetooth`-Matcher als Eintrittspunkt in die zentrale BLE-Discovery festschreiben
- Advertisement-Empfang über die geteilten Callback-APIs (`async_register_callback`) erzwingen, statt einen eigenen `BleakScanner` zu betreiben
- Die `connectable`-Unterscheidung durchgängig verankern und passive Datenbeschaffung als Default vorgeben
- Device-/Service-Info-Lookups über die `bluetooth`-APIs (`async_ble_device_from_address`, `async_last_service_info`, `async_address_present`, `async_scanner_count`) standardisieren
- Die richtige Bluetooth-Coordinator-Familie pro Anwendungsfall auswählbar machen und gegen den generischen Coordinator abgrenzen
- Robustes Verbindungs-Handling über `bleak` / `bleak-retry-connector` mit dem geteilten Scanner erzwingen

## Nicht-Ziele

- Der generische, polling-basierte `DataUpdateCoordinator` für REST-/Cloud-APIs — gehört zu `ha/coordinator-patterns`
- Das Registrieren eigener externer Scanner (`async_register_scanner`, `async_get_advertisement_callback` als Provider-Seite) — relevant nur für Integrationen, die selbst einen Bluetooth-Adapter bereitstellen; eigene Folge-Spec, falls nötig
- Der vollständige Config-Flow-Aufbau inklusive Bluetooth-Discovery-Step — gehört zu `ha/config-flow-patterns`; diese Spec liefert nur den Matcher und die Discovery-Auslösung
- ESPHome-Bluetooth-Proxy-Konfiguration und Add-on-seitige Adapter-Bereitstellung
- Persistente Caches von Advertisement-Daten über HA-Neustarts hinweg

## Anforderungen

### Discovery via manifest matcher

- **MUSS [MUST]** den `bluetooth`-Schlüssel in der `manifest.json` setzen, um die zentrale Discovery für die Devices der Integration auszulösen (siehe `ha/integration-manifest`)
- **MUSS [MUST]** den Matcher aus den dokumentierten Feldern bilden — gültig sind advertised `service_uuid`(s), `local_name`, `manufacturer_id`, `service_data_uuid` und `connectable`
- **SOLLTE [SHOULD]** `connectable` im Matcher passend zum Device setzen: `False`, wenn das Device keine ausgehende Verbindung braucht, damit auch non-connectable Controller die Daten liefern; Default ist `True`
- **KANN [MAY]** für HomeKit-artige Filter zusätzliche Felder wie `manufacturer_data_first_byte` neben `manufacturer_id` verwenden
- **MUSS [MUST]** `bluetooth_adapters` in `dependencies` der `manifest.json` aufnehmen, wenn die Integration einen Bluetooth-Adapter nutzt — das stellt sicher, dass alle unterstützten remote Adapter verbunden sind, bevor die Integration sie verwendet
- **MUSS NICHT [MUST NOT]** einen Matcher bauen, der ähnliche, aber unterschiedlich verbindungsbedürftige Devices nicht trennen kann, ohne im Config-Flow das `connectable`-Property der `BluetoothServiceInfoBleak` zu prüfen und Flows für nicht erreichbare Devices abzulehnen (siehe `ha/config-flow-patterns`)

### Advertisement-Callbacks

- **MUSS [MUST]** Advertisements über `bluetooth.async_register_callback(hass, callback, matcher, mode)` abonnieren, wenn die Integration sofort über neue Advertisements informiert werden muss — statt einen eigenen Scanner zu betreiben
- **MUSS [MUST]** den Callback als `@callback` (synchron, nicht-blockierend) mit der Signatur `(service_info: BluetoothServiceInfoBleak, change: BluetoothChange) -> None` implementieren
- **MUSS [MUST]** den Matcher im selben Format wie der `manifest.json`-`bluetooth`-Eintrag angeben; zusätzlich ist `address` als Matcher-Feld erlaubt
- **MUSS [MUST]** den Scanning-Modus explizit über `bluetooth.BluetoothScanningMode` (`ACTIVE` / `PASSIVE`) übergeben
- **MUSS [MUST]** den von `async_register_callback` zurückgegebenen Cancel-Callback an den Entry-Lifecycle binden (`entry.async_on_unload(...)`) — sonst bleibt die Registrierung nach Entry-Unload bestehen
- **KANN [MAY]** bei einem `address`-spezifischen Matcher mit nicht-`PASSIVE`-Modus über die optionalen Keyword-Argumente `scan_interval` und `scan_duration` periodische aktive Scan-Fenster für genau diese Adresse anfragen; ohne `address` im Matcher wird die Active-Scan-Anfrage übersprungen

### Device-/Service-Info-Lookup

- **MUSS [MUST]** ein `BLEDevice` über `bluetooth.async_ble_device_from_address(hass, address, connectable)` beziehen, statt einen zusätzlichen Scanner zur Adress-Auflösung zu starten; die API liefert das `BLEDevice` des nächsten erreichbaren Adapters oder `None`, wenn kein Adapter das Device erreicht
- **MUSS [MUST]** den `None`-Rückgabewert von `async_ble_device_from_address` behandeln — er bedeutet, dass aktuell kein Adapter in Reichweite ist
- **SOLLTE [SHOULD]** die jüngste Advertisement-/Device-Info über `bluetooth.async_last_service_info(hass, address, connectable)` lesen — sie liefert die `BluetoothServiceInfoBleak` vom Scanner mit dem besten RSSI des angefragten `connectable`-Typs
- **KANN [MAY]** über `bluetooth.async_address_present(hass, address, connectable)` prüfen, ob das Device noch präsent ist, wenn die Integration die Präsenz für die Verfügbarkeit braucht
- **SOLLTE [SHOULD]** beim Setup über `bluetooth.async_scanner_count(hass, connectable=True)` prüfen, ob überhaupt ein passender Scanner läuft, und einen hilfreichen Fehler erheben, wenn kein connectable-fähiger Scanner verfügbar ist

### Passive vs. connectable

- **MUSS [MUST]** passiv arbeiten (`connectable=False`), wann immer das Device seine Daten ausschließlich über Advertisements liefert — das opt-in auf non-connectable Controller liefert dann Daten von connectable und non-connectable Controllern
- **MUSS [MUST]** `connectable=True` nur dort verwenden, wo eine ausgehende Verbindung tatsächlich nötig ist; der Default für `connectable` ist `True`
- **SOLLTE [SHOULD]** bei gemischten Devices den `connectable`-Flag pro Device in der `manifest.json` passend setzen, statt die gesamte Integration auf `connectable=True` zu zwingen
- **KANN [MAY]** ein non-connectable bezogenes `BLEDevice` gegen ein connectable eintauschen, wenn eine Verbindung nötig wird — sofern mindestens ein connectable Controller in Reichweite ist (`async_ble_device_from_address(..., connectable=True)`)

### Bluetooth-Coordinators (Passive/Active)

- **MUSS [MUST]** die Coordinator-Familie nach Anwendungsfall wählen: `PassiveBluetoothProcessorCoordinator` für Sensoren/Binary-Sensoren/Events, deren Daten vollständig aus Advertisements stammen; `ActiveBluetoothProcessorCoordinator`, wenn für einige Sensoren eine aktive Verbindung nötig ist
- **MUSS [MUST]** für Nicht-Sensor-Entitäten den passenden non-Processor-Variant wählen: `PassiveBluetoothDataUpdateCoordinator` (rein advertisement-getrieben) bzw. `ActiveBluetoothDataUpdateCoordinator` (mit `needs_poll_method` / `poll_method` für aktive Verbindungen)
- **MUSS [MUST]** den generischen polling-basierten `DataUpdateCoordinator` (siehe `ha/coordinator-patterns`) nur dann verwenden, wenn das Device ausschließlich über eine aktive Verbindung kommuniziert und gar keine Advertisements nutzt
- **MUSS [MUST]** bei den Processor-Coordinators die Library-Daten in ein `PassiveBluetoothDataUpdate`-Objekt (mit `devices`, `entity_descriptions`, `entity_names`, `entity_data`, indiziert über `PassiveBluetoothEntityKey`) formatieren, damit das Framework Entitäten on-demand erzeugt
- **MUSS [MUST]** den Coordinator mit `address`, `mode` (`BluetoothScanningMode`) und `update_method` konstruieren und `coordinator.async_start()` erst nach `async_forward_entry_setups` an `entry.async_on_unload(...)` binden, damit alle Plattformen vorher abonnieren konnten
- **MUSS [MUST]** bei `ActiveBluetoothProcessorCoordinator` / `ActiveBluetoothDataUpdateCoordinator` im `needs_poll_method` prüfen, dass HA läuft (`CoreState.running`) und ein connectable `BLEDevice` erreichbar ist, bevor `poll_method` eine Verbindung aufbaut
- **KANN [MAY]** über die optionalen `scan_interval` / `scan_duration`-Argumente der Processor-Coordinators ein periodisches aktives Scan-Fenster für die Adresse anfragen; nur `AUTO`-Modus-Scanner honorieren die Anfrage, `PASSIVE`/`ACTIVE`-Scanner bleiben unberührt

### Verbindungs-Handling (bleak/retry-connector)

- **MUSS [MUST]** den geteilten Scanner über `bluetooth.async_get_scanner(hass)` beziehen und an die Library übergeben, statt einen eigenen `BleakScanner` zu instanziieren — das vermeidet den erheblichen Overhead mehrerer Scanner und übersteht Adapter-Änderungen des Nutzers
- **MUSS [MUST]** einen `BleakClient` nicht zwischen Verbindungen wiederverwenden — das macht das Verbinden unzuverlässiger
- **MUSS [MUST]** einen Verbindungs-Timeout von mindestens zehn (10) Sekunden verwenden, da `BlueZ` beim erstmaligen Verbinden zu einem neuen oder aktualisierten Device die Services auflösen muss
- **SOLLTE [SHOULD]** das PyPI-Paket `bleak-retry-connector` einsetzen, um Verbindungen zuverlässig aufzubauen — transiente Verbindungsfehler sind häufig und der erste Versuch gelingt nicht immer
- **MUSS NICHT [MUST NOT]** für die laufende Datenbeschaffung eine permanente Verbindung halten, wenn die Daten aus Advertisements verfügbar sind — die aktive Verbindung ist nur der Poll-Pfad bei den Active-Coordinators

## Akzeptanzkriterien

- [ ] `manifest.json` enthält einen `bluetooth`-Matcher aus den dokumentierten Feldern (`service_uuid`, `local_name`, `manufacturer_id`, `service_data_uuid`, `connectable`)
- [ ] Advertisement-Abonnements laufen über `bluetooth.async_register_callback(hass, callback, matcher, mode)` mit `@callback`-Signatur `(BluetoothServiceInfoBleak, BluetoothChange)`
- [ ] Der Cancel-Callback von `async_register_callback` ist via `entry.async_on_unload(...)` an den Lifecycle gebunden
- [ ] Device-Lookups verwenden `async_ble_device_from_address` und behandeln den `None`-Fall
- [ ] Service-Info-/Präsenz-Lookups verwenden `async_last_service_info` bzw. `async_address_present`
- [ ] `async_scanner_count` wird im Setup geprüft, wenn die Integration einen connectable Scanner braucht
- [ ] Passive Datenbeschaffung (`connectable=False`) ist Default; `connectable=True` nur bei tatsächlichem Verbindungsbedarf
- [ ] Die Coordinator-Familie ist anwendungsfall-korrekt gewählt (Passive/Active Processor vs. DataUpdate vs. generischer `DataUpdateCoordinator`)
- [ ] Processor-Coordinators formatieren Library-Daten in `PassiveBluetoothDataUpdate` und starten via `async_start()` nach `async_forward_entry_setups`
- [ ] Verbindungen nutzen `async_get_scanner`, einen frischen `BleakClient` pro Verbindung, einen Timeout ≥ 10 s und `bleak-retry-connector`

## Offene Fragen

- **Coordinator-Auswahl-Heuristik**: Die HA-Doku unterscheidet Processor- von DataUpdate-Coordinators primär danach, ob die Hauptfunktion „Sensor/Binary-Sensor/Event" ist. Braucht diese Spec eine schärfere, messbare Heuristik für den Grenzfall (z. B. Devices mit gemischten Entity-Typen)?
- **`scan_interval` / `scan_duration`-Default**: Sollen die Skills dieses Plugins die periodischen Active-Scan-Fenster aktiv setzen, oder den habluetooth-Default (5 min Intervall, 10 s Dauer) übernehmen? Eine Empfehlung pro Device-Klasse fehlt.
- **macOS-Unavailable-Verhalten**: Auf macOS cached CoreBluetooth Advertisement-Daten, sodass `_async_handle_unavailable` ggf. nie feuert. Soll die Spec ein Fallback-Verfügbarkeits-Pattern (z. B. `async_track_unavailable` plus Zeitstempel-Prüfung) für diese Plattform verlangen?
- **Abgrenzung externer Scanner**: Das Registrieren eigener Scanner (`async_register_scanner`) ist hier ein Nicht-Ziel. Ab wann braucht das Portfolio dafür eine eigene `ha/bluetooth-scanner-provider`-Spec?
- **Rediscovery nach Entry-Removal**: Die Doku verlangt `async_rediscover_address` beim Entfernen eines Entries/Devices. Soll diese Spec das als harte Anforderung aufnehmen oder bleibt es Teil der `ha/setup-lifecycle`-Spec?
