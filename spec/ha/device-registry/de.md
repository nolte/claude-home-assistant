# HA-Integration: Device-Registry und `DeviceInfo`-Hierarchie

Status: draft

## Kontext

Home Assistant pflegt zwei getrennte Register: das **Entity-Registry** (siehe `ha/entity-architecture` für die Entity-Identifikation) und das **Device-Registry**. Eine Custom Integration meldet ihre Devices über `homeassistant.helpers.device_registry.DeviceInfo`-Instanzen an, die jede Entity beim Setup über `_attr_device_info` mit­bringt. HA fügt die DeviceInfos pro `(integration, identifiers)`-Paar zu einem Device-Eintrag im Registry zusammen — unterschiedliche `identifiers` ergeben unterschiedliche Devices, gleiche `identifiers` mit unterschiedlicher `DeviceInfo` werden gemerged.

Eine echte Integration besteht selten aus einem flachen Device — typisch ist eine **Hub-Hierarchie**: Ein zentrales „Hub"-Device repräsentiert den Server / die Bridge / den API-Endpunkt; alle untergeordneten Resources (verwaltete Geräte, Standorte, Tanks, Räume, …) sind Sub-Devices, die per `via_device=(DOMAIN, hub_identifier)` auf das Hub zeigen. HA rendert die Hierarchie dann in der UI als Baum, was die Übersicht in größeren Setups massiv verbessert.

`nolte/kamerplanter-ha` validiert dieses Hub-Pattern mit einer zentralen `server_device_info(entry)`-Factory-Funktion plus drei Sub-Device-Factories (`plant_device_info`, `location_device_info`, `tank_device_info`), die alle `via_device=(DOMAIN, entry.entry_id)` setzen. Jede Sub-`identifiers`-Instanz präfigiert `entry.entry_id`, sodass zwei Entries (Multi-Instance) kollisionsfrei nebeneinander existieren. Diese Spec überführt das Pattern in eine generische Verpflichtung.

Quality-Scale-Marker: **Silver** (Device-Hierarchie über `via_device` und Multi-Instance-fähige `identifiers` ist eine Silver-Pflicht laut HA-Quality-Scale).

## Ziele

- Hub-und-Sub-Device-Hierarchie als Standardform für Custom Integrations etablieren, die mehr als ein Device anlegen
- `DeviceInfo`-Factory-Funktionen in `entity.py` zentralisieren, sodass Plattform-Module sie referenzieren statt sie zu duplizieren
- `identifiers`-Konstruktion mit `entry.entry_id`-Präfix verbindlich machen — Multi-Instance-Setups (zwei Entries gegen unterschiedliche Server) bleiben dadurch kollisions­frei
- `via_device`-Setzung auf jedem Sub-Device pflichten, damit HA die Hierarchie korrekt in der UI rendert
- Stabile, sprach- und installations­unabhängige `identifiers` über die Lebenszeit eines Resources hinweg garantieren

## Nicht-Ziele

- Entity-Identifikation (`unique_id`, `translation_key`, `_attr_has_entity_name`) — eigene Spec `ha/entity-architecture`
- HA-Area-Registry-Verwaltung (Area-Zuweisung) — Areas werden vom User in der UI gesetzt; Skills setzen sie nicht programmatisch
- Device-Discovery-Mechanik (Zeroconf-Detection, DHCP-Match) — eigene Folge-Specs
- Connections-Feld (`connections={(CONNECTION_NETWORK_MAC, "...")}`) für MAC-/IP-basierte Identifikation — relevant nur für Discovery-driven Integrationen; eine eigene Folge-Spec nimmt sich des Themas an, sobald die erste Discovery-Spec landet

## Anforderungen

### `DeviceInfo`-Factory-Funktionen

- **MUSS [MUST]** alle `DeviceInfo`-Konstruktionen in `entity.py` als freie Factory-Funktionen definieren, eine pro Resource-Typ — typische Funktions-Namen: `<role>_device_info(entry, <resource>) -> DeviceInfo`
- **MUSS [MUST]** Factory-Funktionen pure halten — keine Coordinator-Reads, keine I/O, keine Mutationen; sie nehmen `entry` plus optional ein Resource-Dict entgegen und liefern eine `DeviceInfo`
- **MUSS NICHT [MUST NOT]** `DeviceInfo`-Konstruktionen direkt in Plattform-Modulen (`sensor.py`, `binary_sensor.py`, …) inline ausführen — sonst driften die Felder zwischen Plattformen, und HA mergt nicht mehr
- **SOLLTE [SHOULD]** `manufacturer`, `model` und `name` in jeder Factory-Funktion setzen — `name` wird in der HA-UI angezeigt, `manufacturer`/`model` landen in der Device-Detail-Ansicht
- **KANN [MAY]** `model_id`, `sw_version`, `hw_version`, `configuration_url` setzen, wenn die Daten verfügbar sind; insbesondere `configuration_url` ist nützlich, weil HA es als Direkt-Link zur Web-Oberfläche des Backends rendert

### Hub-Device

- **MUSS [MUST]** wenn die Integration `integration_type: "hub"` hat (siehe `ha/integration-architecture`) ein Hub-`DeviceInfo` mit eindeutigem `identifiers` und **ohne** `via_device` definieren
- **MUSS [MUST]** das Hub-`identifiers` als `{(DOMAIN, entry.entry_id)}` setzen — der `entry.entry_id`-Präfix garantiert Multi-Instance-Kollisions­freiheit
- **SOLLTE [SHOULD]** das Hub-`name` aus dem Entry-Title oder einem Backend-Server-Identifier ableiten, sodass zwei Hubs derselben Integration in der UI unterscheidbar bleiben
- **MUSS [MUST]** mindestens eine Entity am Hub-Device hängen lassen — sonst rendert HA das Hub-Device nicht; typisch ist eine Status-Sensor-Entity oder ein Refresh-Button (siehe `ha/entity-architecture`)

### Sub-Devices

- **MUSS [MUST]** für jeden Resource-Typ (verwaltetes Gerät, Standort, Tank, Raum, ...) eine eigene `<role>_device_info(entry, resource)`-Factory-Funktion definieren
- **MUSS [MUST]** das Sub-`identifiers` als `{(DOMAIN, f"{entry.entry_id}_<role>_<resource_slug>")}` setzen — der `entry.entry_id`-Präfix bleibt zwingend, der `<role>`-Marker macht den Identifier menschlesbar im Device-Registry, der `<resource_slug>` ist stabil über die Lebenszeit der Resource
- **MUSS [MUST]** das Sub-Device per `via_device=(DOMAIN, entry.entry_id)` an das Hub binden (das Tupel ist die Hub-`identifiers`-Repräsentation)
- **SOLLTE [SHOULD]** den Resource-Slug deterministisch aus einem stabilen Backend-Schlüssel ableiten (Resource-ID, Ressource-Key, Backend-UUID) — niemals aus einem User-änderbaren Display-Namen, sonst wandert der Slug bei Umbenennung
- **MUSS NICHT [MUST NOT]** zwei Sub-Devices mit identischer `identifiers`-Tupel-Menge erzeugen — HA mergt sie zu einem einzigen Device, das beide Entity-Sätze trägt; das ist nur dann erwünscht, wenn die zwei Sub-Devices logisch ein einziges Device sind

### Sub-Sub-Hierarchien

- **KANN [MAY]** mehrstufige Hierarchien führen (z. B. `tank_device_info` mit `via_device` zu einem `location_device_info`, das wiederum auf das Hub zeigt) — HA unterstützt beliebig tiefe Schachtelung über `via_device`
- **SOLLTE [SHOULD]** die Hierarchie-Tiefe minimal halten; jede zusätzliche Ebene erschwert das mentale Modell für End-User, ohne dass HA-seitig ein technischer Vorteil entsteht
- **MUSS [MUST]** bei mehrstufigen Hierarchien dokumentieren (in der Folge-Skill-Output-Doku), warum die Tiefe gerechtfertigt ist

### Stabilität von `identifiers`

- **MUSS [MUST]** `identifiers` über die Lebenszeit einer Resource stabil halten — eine Änderung des Identifier-Strings führt aus Sicht des Device-Registry zu einem **neuen** Device; die Entitäten am alten Device bleiben verwaist
- **MUSS NICHT [MUST NOT]** Display-Namen, User-änderbare Slugs oder zufällige UUIDs in den `identifiers`-String aufnehmen
- **SOLLTE [SHOULD]** Backend-IDs / -Schlüssel verwenden, die das Backend selbst als stabil garantiert (Datenbank-Primary-Key, Backend-UUID, hardware-MAC, …)

### Multi-Instance-Verhalten

- **MUSS [MUST]** sicherstellen, dass zwei Config-Entries derselben Integration (gegen unterschiedliche Backends) kollisions­freie `identifiers` produzieren — das wird durch den `entry.entry_id`-Präfix automatisch erreicht
- **MUSS NICHT [MUST NOT]** den Backend-Identifier ohne Entry-Präfix verwenden — zwei Server mit derselben Backend-internen Resource-ID würden sonst zum selben Device-Eintrag mergen, was die Entitäten beider Entries durcheinander bringt

### Lifecycle

- **MUSS [MUST]** Sub-Device-Factory-Calls in `async_setup_entry` (oder in der Plattform-`async_setup_entry`) durchführen, basierend auf den frischen Coordinator-Daten — nicht aus zwischengespeicherten oder hartkodierten Listen
- **MUSS NICHT [MUST NOT]** `async_remove_device(...)` direkt aufrufen, um Sub-Devices manuell zu entfernen — HA räumt verwaiste Devices auf, wenn die letzte Entity am Device entfernt wird; ein expliziter Remove-Call ist nur in seltenen Sonderfällen nötig

## Akzeptanzkriterien

- [ ] Alle `DeviceInfo`-Konstruktionen liegen als freie Factory-Funktionen in `entity.py`
- [ ] Wenn `manifest.json:integration_type` `hub` ist: ein Hub-Device mit `identifiers={(DOMAIN, entry.entry_id)}` und ohne `via_device` ist definiert
- [ ] Mindestens eine Entity ist am Hub-Device verankert
- [ ] Jedes Sub-Device hat `identifiers` mit `entry.entry_id`-Präfix und `via_device=(DOMAIN, entry.entry_id)`
- [ ] Plattform-Module setzen `_attr_device_info` über die Factory-Funktionen aus `entity.py`, nicht inline
- [ ] Eine `grep`-Suche nach `DeviceInfo(` in den Plattform-Modulen liefert keine Treffer
- [ ] Sub-Device-Slugs leiten sich aus stabilen Backend-Schlüsseln ab, nicht aus Display-Namen oder UUIDs
- [ ] Quality-Scale-Marker: **Silver**

## Offene Fragen

- **`connections`-Feld**: Soll die Spec MAC-/IP-Connections für Discovery-fähige Integrationen verlangen, sobald die erste Discovery-Spec landet?
- **Mehrstufige Hierarchien**: Heuristik für sinnvolle Tiefe? Aktuell als „minimal halten" formuliert; eine messbare Schwelle (z. B. „nicht tiefer als 2") fehlt.
- **`async_remove_device`-Use-Case**: Gibt es legitime Fälle, in denen die Integration ein Device explizit entfernen sollte (z. B. Resource im Backend gelöscht)? Aktuell verboten/SOLLTE-NICHT; die Erfahrung mit kamerplanter-ha zeigt, dass HA das automatisch löst, sobald die letzte Entity weg ist — gilt das immer?
- **Hub-Device-Pflicht für `integration_type: "device"`**: Bei `integration_type: "device"` gibt es konventionell kein Hub. Sollten Sub-Device-Factories für solche Integrationen verboten sein, oder gibt es Mischformen?
