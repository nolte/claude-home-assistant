# HA-Integration: Entity-Plattformen (Sensorik)

Status: draft

## Kontext

Neben den generischen Mess- und Zwei-Zustands-Plattformen `sensor` und `binary_sensor` kennt Home Assistant eine Reihe weiterer read-only- und Status-Plattformen, die jeweils eine eigene Capability typisieren: Luftqualität, Wetter, Anwesenheit (Device-Tracker), physische Ereignisse und Update-Verfügbarkeit. Jede dieser Plattformen leitet von einer eigenen Basisklasse ab und erwartet ein festes Set an Properties, Forecast-Methoden, Feature-Flags oder Device-Classes, damit UI, Forecast-API, DHCP-Discovery, Automatisierungs-Trigger und Update-Verwaltung funktionieren.

Die **generische Entity-Architektur** — Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, das `EntityDescription`-Pattern, Entity-Kategorien und die Coordinator-Anbindung — ist in `ha/entity-architecture` festgeschrieben und wird **hier nicht wiederholt**. Die **plattform-spezifische Typisierung** der generischen Mess-Plattformen — `sensor`/`binary_sensor` mit dem `device_class`/`state_class`/`supported_features`-Muster — ist vollständig in `ha/entity-platform-types` festgeschrieben; auch sie wird **hier nicht wiederholt**. Diese Spec ist der **konkrete Katalog** für die übrigen read-only- und Status-Oberflächen und referenziert die beiden Schwester-Specs per Slug.

Behandelte Plattformen: `air-quality` (deprecated, Migrationshinweis), `weather`, `device-tracker`, `event`, `update`. Für jede gilt: Plattformwahl an die Capability binden, die dokumentierte Basisklasse ableiten, ausschließlich die in der Plattform-Doku genannten Properties/Features/Device-Classes verwenden und jedes beworbene Feature-Flag mit seiner Methode hinterlegen.

## Ziele

- Die Plattformwahl an die abzubildende Capability binden — Luftqualitäts-Messung → getrennte `sensor` (Air-Quality ist deprecated), Wetterzustand+Forecast → `weather`, Anwesenheit → `device_tracker`, physisches Ereignis → `event`, Update-Verfügbarkeit → `update`
- Je Plattform die dokumentierte Basisklasse ableiten (`WeatherEntity`, `TrackerEntity`/`ScannerEntity`/`BaseScannerEntity`, `EventEntity`, `UpdateEntity`)
- Forecast- und Feature-Flags (`WeatherEntityFeature`, `UpdateEntityFeature`) nur setzen, wenn die korrespondierende Methode tatsächlich implementiert ist
- `device_class` aus dem plattform-eigenen geschlossenen Enum setzen, wo ein passendes Member existiert (`EventDeviceClass`, `UpdateDeviceClass`)
- Generierten Code so starten lassen, dass UI, Forecast-API, DHCP-Discovery und Update-Verwaltung ohne Nacharbeit funktionieren

## Nicht-Ziele

- Generisches Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`-Pattern, Entity-Kategorien, Coordinator-Anbindung) — vollständig in `ha/entity-architecture`; diese Spec referenziert es nur
- `sensor`/`binary_sensor` und das `device_class`/`state_class`/`supported_features`-Typisierungsmuster — vollständig in `ha/entity-platform-types`; diese Spec referenziert es nur
- HA-Translation-Format selbst (`strings.json`-Aufbau, `entity.<platform>.<key>.name`, State-Übersetzungen) — eigene Spec `ha/translations`
- Aktor-Plattformen (`climate`, `light`, `cover`, `switch`, `fan`, …) — read-only/Status-Oberflächen sind hier der Fokus; steuerbare Plattformen sind nicht Ziel
- Erschöpfende Listen aller Wetter-Conditions, Einheiten-Varianten oder AwesomeVersion-Strategien — diese Spec verweist auf die jeweilige Plattform-Doku, statt sie zu duplizieren

## Anforderungen

### Air-Quality

- **MUSS NICHT [MUST NOT]** die `air_quality`-Plattform für neue Integrationen verwenden — die Air-Quality-Doku markiert die Entity ausdrücklich als deprecated und verlangt stattdessen getrennte `sensor` für die einzelnen Messwerte
- **MUSS [MUST]** Luftqualitäts-Messwerte (PM2.5, PM10, PM0.1, AQI, Ozon, CO, CO₂, SO₂, NO₂, …) als je eigene `sensor`-Entity nach `ha/entity-platform-types` abbilden statt sie in einer Air-Quality-Entity zu bündeln
- **SOLLTE [SHOULD]** eine bestehende Integration, die noch die Air-Quality-Entity nutzt, auf getrennte Sensoren migrieren — so verlangt es die Air-Quality-Doku
- **MUSS [MUST]**, falls eine Air-Quality-Entity unvermeidbar weiterbetrieben wird, `particulate_matter_2_5` als einzig erforderliche Property liefern und für `nitrogen_dioxide` ausschließlich die dokumentierten Einheiten (`ppb`, `ppm`, `µg/m³`) verwenden
- **MUSS NICHT [MUST NOT]** für die Air-Quality-Entity das Attribut-Shorthand (`_attr_`-Property-Implementierung) verwenden — die Air-Quality-Doku schließt das ausdrücklich aus

### Weather

- **MUSS [MUST]** eine Wetter-Plattform von `homeassistant.components.weather.WeatherEntity` ableiten
- **MUSS [MUST]** `condition`, `native_temperature` und `native_temperature_unit` als erforderliche Properties bereitstellen — die Weather-Doku markiert genau diese drei als **Required**
- **MUSS [MUST]** Messwerte in den nativen `native_*`-Properties (`native_temperature`, `native_pressure`, `native_wind_speed`, `native_visibility`, …) zurückgeben und die zugehörige `native_*_unit`-Property setzen, wenn der Wert gesetzt ist (z. B. `native_pressure_unit` ist Required, sobald `native_pressure` gesetzt ist) — HA übernimmt die nutzer-seitige Einheiten-Konvertierung
- **SOLLTE [SHOULD]** für `condition` ausschließlich die in der Weather-Doku gelisteten empfohlenen Condition-Strings (`sunny`, `cloudy`, `rainy`, `clear-night`, …) verwenden — diese sind in den HA-Übersetzungs- und Icon-Dateien hinterlegt, sodass `weather`-Plattformen keine eigenen Sprachen unterstützen müssen
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus `WeatherEntityFeature` (`FORECAST_DAILY`, `FORECAST_HOURLY`, `FORECAST_TWICE_DAILY`) setzen und je gesetztem Flag genau die korrespondierende async-Methode (`async_forecast_daily`, `async_forecast_hourly`, `async_forecast_twice_daily`) implementieren — die Weather-Doku koppelt Flag und Methode eins-zu-eins
- **MUSS NICHT [MUST NOT]** Forecast-Daten in den Entity-State legen — Forecasts sind laut Weather-Doku nicht Teil des States, sondern werden über eine separate API bereitgestellt, die Konsumenten abonnieren
- **SOLLTE [SHOULD]** gefetchte Forecasts cachen und bei Aktualisierung den Cache invalidieren sowie `WeatherEntity.async_update_listeners` awaiten, um aktive Abonnenten zu benachrichtigen — so empfiehlt es die Weather-Doku
- **MUSS [MUST]** in `async_forecast_twice_daily`-Daten je Eintrag `is_daytime` setzen — die Weather-Doku markiert es dort als verpflichtend (Tag/Nacht-Unterscheidung)

### Device-Tracker

- **MUSS [MUST]** eine Anwesenheits-Plattform von genau einer der drei dokumentierten Basisklassen ableiten — `BaseScannerEntity` (reiner Connection-State), `ScannerEntity` (IP-Netz, per MAC identifizierbar) oder `TrackerEntity` (Positions-Tracking)
- **MUSS [MUST]** für `ScannerEntity`/`BaseScannerEntity` `is_connected` und `source_type` als erforderliche Properties liefern — die Device-Tracker-Doku markiert beide als **Required**
- **MUSS [MUST]** für `TrackerEntity` entweder `in_zones` oder `latitude` **und** `longitude` setzen, um einen State zu melden; sind beide vorhanden, hat `in_zones` Vorrang — so die Device-Tracker-Doku
- **MUSS [MUST]** `source_type` aus dem `SourceType`-Enum setzen (z. B. `SourceType.ROUTER` für `ScannerEntity`, `SourceType.GPS` für `TrackerEntity`) und niemals als frei gewählten String
- **SOLLTE [SHOULD]** für eine `ScannerEntity` mit `source_type` `router` zusätzlich `ip_address`, `mac_address` und `hostname` setzen — die Doku nennt dies als Beschleuniger für DHCP-Discovery
- **MUSS NICHT [MUST NOT]** die `device_tracker`-Plattform als steuerbare Entity behandeln — ein Device-Tracker ist laut Doku eine read-only-Entity, die ausschließlich Anwesenheits-Information liefert

### Event

- **MUSS [MUST]** eine Ereignis-Plattform von `homeassistant.components.event.EventEntity` ableiten
- **MUSS [MUST]** `event_types` als Liste der möglichen Ereignis-Typen bereitstellen — die Event-Doku markiert es als **Required**
- **MUSS [MUST]** ein Ereignis über `_trigger_event(event_type, extra_data=None)` auslösen und im Anschluss `async_write_ha_state()` aufrufen — die Entity ist laut Doku stateless; HA verwaltet den State, die Integration feuert die Ereignisse
- **MUSS NICHT [MUST NOT]** einen Ereignis-Typ feuern, der nicht in `event_types` deklariert ist — die Event-Doku verlangt, dass `_trigger_event` sonst einen `ValueError` wirft
- **SOLLTE [SHOULD]** die `device_class` aus `EventDeviceClass` (`BUTTON`, `DOORBELL`, `MOTION`) setzen, wo ein passendes Member existiert
- **MUSS [MUST]** bei `EventDeviceClass.DOORBELL` den Standard-Ereignis-Typ `DoorbellEventType.RING` in `event_types` führen — die Event-Doku markiert diesen Standard-Typ als verpflichtend
- **SOLLTE [SHOULD]** registrierte Geräte-Callbacks beim Entfernen der Entity wieder deregistrieren — so empfiehlt es die Event-Doku

### Update

- **MUSS [MUST]** eine Update-Plattform von `homeassistant.components.update.UpdateEntity` ableiten
- **MUSS [MUST]** `installed_version` und `latest_version` so liefern, dass HA Verfügbarkeit und Differenz ableiten kann — die Update-Doku stützt die Verfügbarkeits-Anzeige darauf
- **MUSS [MUST]** `supported_features` aus `UpdateEntityFeature` (`INSTALL`, `SPECIFIC_VERSION`, `BACKUP`, `PROGRESS`, `RELEASE_NOTES`) setzen und je Flag genau die geforderte Methode bereitstellen — `INSTALL` verlangt `install`/`async_install`, `RELEASE_NOTES` verlangt `release_notes`/`async_release_notes`
- **MUSS [MUST]** `async_install(version, backup, **kwargs)` so implementieren, dass bei `version=None` die neueste Version installiert wird und der `backup`-Parameter ein Backup vor der Installation auslöst — so die Update-Doku
- **MUSS NICHT [MUST NOT]** `UpdateEntityFeature.SPECIFIC_VERSION` oder `UpdateEntityFeature.BACKUP` setzen, ohne dass `install`/`async_install` die jeweilige Fähigkeit tatsächlich bedient — beide Flags setzen `INSTALL` voraus
- **SOLLTE [SHOULD]** `device_class` auf `UpdateDeviceClass.FIRMWARE` setzen, wenn das Update eine Geräte-Firmware betrifft — das einzige dokumentierte Member dieses Enums
- **MUSS NICHT [MUST NOT]** ein Update überspringbar darstellen, wenn `auto_update=True` gesetzt ist — die Update-Doku stellt fest, dass bei aktiviertem Auto-Update keine Updates übersprungen werden können

## Akzeptanzkriterien

- [ ] Keine neue Integration nutzt die deprecated `air_quality`-Plattform; Luftqualitäts-Messwerte sind getrennte `sensor`
- [ ] Jede `weather`-Entity leitet von `WeatherEntity` ab und liefert `condition`, `native_temperature`, `native_temperature_unit`
- [ ] Jedes gesetzte `WeatherEntityFeature`-Forecast-Flag hat seine `async_forecast_*`-Methode; Forecasts liegen nicht im Entity-State
- [ ] `async_forecast_twice_daily`-Einträge setzen `is_daytime`
- [ ] Jede `device_tracker`-Entity leitet von `BaseScannerEntity`/`ScannerEntity`/`TrackerEntity` ab und setzt `source_type` aus dem `SourceType`-Enum
- [ ] `ScannerEntity`/`BaseScannerEntity` liefern `is_connected`; `TrackerEntity` setzt `in_zones` oder `latitude`+`longitude`
- [ ] `router`-`ScannerEntity` setzen `ip_address`, `mac_address`, `hostname` zur DHCP-Beschleunigung
- [ ] Jede `event`-Entity leitet von `EventEntity` ab, liefert `event_types` und feuert nur deklarierte Typen über `_trigger_event`
- [ ] `EventDeviceClass.DOORBELL`-Entitäten führen `DoorbellEventType.RING` in `event_types`
- [ ] Jede `update`-Entity leitet von `UpdateEntity` ab, liefert `installed_version`/`latest_version` und hat zu jedem `UpdateEntityFeature`-Flag die geforderte Methode
- [ ] `device_class` ist aus dem plattform-eigenen Enum gesetzt, wo ein Member existiert (`EventDeviceClass`, `UpdateDeviceClass.FIRMWARE`)

## Offene Fragen

- **Air-Quality-Migrationspfad**: Soll diese Spec eine konkrete Mapping-Tabelle Air-Quality-Property → Sensor-`device_class` vorschreiben, oder genügt der Verweis auf `ha/entity-platform-types`?
- **Forecast-Cache-Konvention**: Die Weather-Doku empfiehlt Caching, schreibt aber keine konkrete Strategie vor. Gehört eine Cache-Invalidierungs-Konvention in diese Spec oder in `ha/entity-architecture` (Coordinator)?
- **Device-Tracker-Basisklassen-Wahl**: Soll der Skill die Wahl zwischen `ScannerEntity` und `TrackerEntity` automatisch aus den verfügbaren Daten (MAC vs. GPS) ableiten oder immer rückfragen?
- **Event-Translation-Keys**: Nicht-Standard-Event-Typen brauchen Übersetzungen. Soll die Spec eine Konvention für deren Translation-Keys vorschreiben (Schnittstelle zu `ha/translations`)?
- **Version-Vergleichs-Strategie**: Die Update-Doku erlaubt ein `version_is_newer`-Override via AwesomeVersion. Soll der Skill dieses Override standardmäßig generieren oder nur auf Anforderung?
