# Skill: `ha-device-registry-augment`

Status: draft

## Kontext

`ha/device-registry` und `ha/entity-architecture` beschreiben, wie Entitäten über `DeviceInfo` (Identifiers, Manufacturer, Model, Name) zu physischen **Geräten** gruppieren, wie ein Kindgerät über `via_device` an seinen Hub verlinkt, wie neu entdeckte Geräte zur Laufzeit ergänzt werden und wie verschwundene Geräte entfernt werden. Das sind die Gold-Quality-Scale-Regeln `devices`, `stale-devices` und `dynamic-devices`. Aber kein Skill verdrahtet sie: Der Scaffold und `ha-entity-platform-add` erzeugen Entitäten, `ha-entity-description-map` mappt Datenpunkte, und beide delegieren die Geräte-Hierarchie an `ha/entity-architecture`, ohne dass ein Skill sie besitzt. Die häufigen Fehler sind flache Entitäten ohne Gerät, ein fehlendes `via_device` (sodass Hub und Kinder unverbunden sind) und veraltete Geräte, die hängen bleiben, weil `async_remove_config_entry_device` nie implementiert wurde.

Dieser Skill schließt die Lücke: Er verdrahtet die Device-Registry-Hierarchie einer bestehenden Integration — `DeviceInfo`, `via_device`, dynamisches Hinzufügen, Stale-Removal und optionale Geräte-Diagnostics — non-destruktiv zu den bestehenden Entitäten. Er ist die Geräte-Hierarchie-Schwester von `ha-entity-platform-add` (das die Entität besitzt) und hebt eine Integration Richtung Gold-Geräte-Regeln.

## Scope

Verdrahtung der Device-Registry-Hierarchie genau einer bestehenden `custom_components/<domain>/`-Integration: die `DeviceInfo` an den Entitäten (Identifiers / Manufacturer / Model / Name, `via_device` für eine Hierarchie), das Laufzeit-Hinzufügen neu entdeckter Geräte, der `async_remove_config_entry_device`-Stale-Removal-Hook, und optional `async_get_device_diagnostics`, plus ein Device-Registry-Test. Der Skill liest die Coordinator-/Entity-Form, entscheidet die Topologie und validiert offline; er schreibt keine Entity-Logik um.

## Ziele

- Die Device-Registry-Hierarchie (`DeviceInfo`, `via_device`, dynamisches Add, Stale-Removal) besitzen, die `ha/entity-architecture` beschreibt, aber kein Skill verdrahtet
- Entitäten zu echten Geräten mit voller `DeviceInfo` (Identifiers/Manufacturer/Model/Name) gruppieren, non-destruktiv zu bestehenden `unique_id`s
- Einen Hub und seine Kinder über `via_device` verlinken, den Hub zuerst registrieren und nie außerhalb der Integration zeigen
- Neu entdeckte Geräte zur Laufzeit ergänzen (Gold `dynamic-devices`) und veraltete über `async_remove_config_entry_device` entfernen (Gold `stale-devices`), nie ein bloß-unavailable Gerät auto-löschen
- Optional redactete Geräte-Diagnostics ergänzen; einen Device-Registry-Test liefern

## Nicht-Ziele

- Die Entity-Plattform selbst erzeugen — `ha-entity-platform-add` / `ha-entity-description-map`
- Der Config-Entry-Diagnostics-JSON-Dump — `ha-diagnostics-augment`
- Device-Trigger- / Condition- / Action-Automation-Plattformen — `ha-device-automation-add`
- Greenfield-Scaffold — `ha-integration-scaffold`
- Deployment/Import in eine laufende HA-Instanz — Generierung only

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „group these entities into a device", „add a hub device with child devices via_device", „remove stale devices when they disappear"
  - „gruppiere die Entitäten zu einem Gerät", „füge ein Hub-Gerät mit Kindgeräten hinzu"
- **MUSS NICHT [MUST NOT]** für Entity-Plattform-Erzeugung (`ha-entity-platform-add`), Config-Entry-Diagnostics (`ha-diagnostics-augment`) oder Device-Automations (`ha-device-automation-add`) aktivieren

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root), `topology` (`single` / `hub-and-children` / `per-device`) und `identifier_source` (die stabile Pro-Gerät-ID)
- **KANN [MAY]** erfassen: `stale_removal` (sonst abgeleitet und bestätigt) und `device_diagnostics` (Default `false`)

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir` ein Git-Repo mit sauberem Working-Tree ist und `custom_components/<domain>/` mindestens eine Entity-Plattform trägt; `domain` und die Coordinator-/Entity-Form lesen
- **MUSS [MUST]** die `topology`, die `identifier_source` und ob `stale_removal` gilt auflösen

### Generierungs-Regeln

- **MUSS [MUST]** `_attr_device_info = DeviceInfo(...)` mit `identifiers={(DOMAIN, <stabile_geräte_id>)}`, `manufacturer`, `model`, `name` (und `sw_version`/`hw_version`, wenn bekannt) setzen; Entitäten hängen über ihre eigene `device_info` an, nie durch manuelles Erzeugen eines unreferenzierten Geräts; bestehende `unique_id`s bleiben unverändert
- **MUSS [MUST]** `via_device=(DOMAIN, <hub_geräte_id>)` für ein Kind in einer Hub-Hierarchie setzen, den Hub zuerst registrieren und `via_device` nie außerhalb dieser Integration zeigen
- **MUSS [MUST]** neu entdeckte Geräte aus dem Coordinator-Update zur Laufzeit ergänzen, wenn das Backend Geräte gewinnen kann (Gold `dynamic-devices`)
- **MUSS [MUST]** `async_remove_config_entry_device(hass, config_entry, device_entry) -> bool` implementieren, das nur `True` zurückgibt, wenn das Gerät wirklich aus den Integrations-Daten verschwunden ist (Gold `stale-devices`); ein temporär-unavailable Gerät wird nicht entfernt
- **MUSS [MUST]** alle `async_get_device_diagnostics`-Daten über `async_redact_data` gemäß `ha/diagnostics` / `ha/security-hardening` leiten, wenn `device_diagnostics`
- **MUSS [MUST]** `ha/device-registry` + `ha/entity-architecture` folgen, Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: `DeviceInfo` trägt Identifiers/Manufacturer/Model/Name; `via_device` zeigt in die Integration; `async_remove_config_entry_device` ist vorhanden, wenn `stale_removal`; Geräte-Diagnostics sind redactet, wenn vorhanden; ein Device-Registry-Test existiert
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht liefern, der an diese Akzeptanzkriterien plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**Gold** — `devices`, `stale-devices`, `dynamic-devices`) anknüpft

### Verbote

- **MUSS NICHT [MUST NOT]** Entity-Logik umschreiben oder bestehende `unique_id`s ändern
- **MUSS NICHT [MUST NOT]** `via_device` auf ein Gerät außerhalb dieser Integration zeigen oder ein bloß-unavailable Gerät auto-löschen
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen oder importieren

## Akzeptanzkriterien

- [ ] Entitäten tragen `DeviceInfo` mit Identifiers, Manufacturer, Model und Name; bestehende `unique_id`s sind unverändert
- [ ] Eine Hub-Hierarchie verlinkt Kinder über `via_device`, mit dem Hub zuerst registriert und innerhalb der Integration
- [ ] Neu entdeckte Geräte werden zur Laufzeit ergänzt, wenn das Backend Geräte gewinnen kann
- [ ] `async_remove_config_entry_device` entfernt nur wirklich-verschwundene Geräte (Gold `stale-devices`)
- [ ] Geräte-Diagnostics sind, wenn ergänzt, redactet
- [ ] Ein Device-Registry-Test und die geänderten Datei-Pfade sind berichtet; Quality-Scale-Marker **Gold**

## Offene Fragen

- **Device-only vs. Entity-attached**: Ein Hub ohne eigene Entität braucht ein `device_registry.async_get_or_create`. Wann wird ein Gerät device-only registriert vs. immer über die `device_info` einer Entität?
- **Stale-Removal-Signal**: `async_remove_config_entry_device` entscheidet die Entfernbarkeit aus aktuellen Daten. Braucht es einen stärkeren „seen at"-Zeitstempel, oder reicht Presence-in-Data?
- **Migrations-Überschneidung**: Zuvor-flache Entitäten zu Geräten zu gruppieren, kann alte Registry-Einträge stranden lassen. Übergibt dieser Skill an `ha-config-entry-migrate`, wenn eine Geräte-Umstrukturierung einen Version-Bump braucht?
