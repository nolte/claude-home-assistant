# Skill: `ha-device-automation-add`

Status: draft

## Kontext

`ha/device-automations` definiert die geräte-zentrierte Automations-Schicht: eine Integration nimmt teil, indem sie die Plattform-Module `device_trigger.py`, `device_condition.py` und/oder `device_action.py` bereitstellt — je mit einer `async_get_*`-Funktion, die pro `device_id` eine Liste schema-konformer Dictionaries liefert, einer modulkonstanten `*_SCHEMA` (vom Core angewendet, nie manuell), und der Attach-/Check-/Call-Funktion (`async_attach_trigger`, `async_condition_from_config`, `async_call_action_from_config`). Bislang gibt es keinen Skill, der das ergänzt. Wichtig: Der Quality-Scale-Marker ist **keiner**, und HA nimmt **keine neuen Device-Automations** mehr an (es exploriert aktiv Alternativen) — neue Implementierungen sind eine bewusste Abwägung, kein Standard-Scaffold. Sie lohnen vor allem für geräte-eigene Events, die an kein Entity gebunden sind (z. B. Tastendruck auf einer Fernbedienung).

Dieser Skill ergänzt **eine** Device-Automation-Art (Trigger, Condition oder Action) in einer **bestehenden** Integration: das passende Plattform-Modul, die `async_get_*`-Liste, die modulkonstante `*_SCHEMA`, die Attach-/Check-/Call-Funktion, optionale Capabilities und die `device_automation:`-Strings — spec-konform zu `ha/device-automations`. Vor der Generierung prüft er, ob eine Entity-Automation den Bedarf nicht ohnehin besser deckt.

## Scope

Ergänzung genau einer Device-Automation-Art pro Lauf (`trigger`, `condition` oder `action`) in einer bestehenden `custom_components/<domain>/`-Integration: das Plattform-Modul (`device_trigger.py` / `device_condition.py` / `device_action.py`), die `async_get_*`-Funktion, die modulkonstante `*_SCHEMA`, die Attach-/Check-/Call-Funktion, optionale `async_get_*_capabilities` und die `strings.json`-`device_automation:`-Einträge. Der Skill liest `ha/device-automations` und validiert.

## Ziele

- Aus einer beschriebenen Geräte-Interaktion die richtige Art (Trigger/Condition/Action) wählen und spec-konform ergänzen
- Den `async_get_*`-Vertrag erzwingen: pro `device_id` eine Liste von Dictionaries mit den Basis-Schema-Pflichtfeldern (`CONF_PLATFORM: "device"`, `CONF_DOMAIN`, `CONF_DEVICE_ID`, `CONF_TYPE`)
- Die statische Validierung über modulkonstante `*_SCHEMA` erzwingen — niemals manuelle Schema-Anwendung
- Die Module als dünne Adapter halten, die auf Event-/State-/Service-Action-Helpers aufsetzen — keine duplizierte Geschäftslogik
- Den User vor unnötigen Device-Automations bewahren: bestätigen, dass die geräte-zentrierte Schicht echten Mehrwert gegenüber Entity-Automations bietet, und auf HAs Abwägungs-Stand hinweisen

## Nicht-Ziele

- Entity-Automations (das State-/Event-Modell ohne Device-Indirektion) — `ha/entity-architecture`
- Registrierte Services mit eigenem Schema — `ha-service-definition-generator` / `ha/services` (Device-Actions delegieren intern, sind aber kein Service-Ersatz)
- Die UI-Editor-Logik des Frontends — nur der Backend-Vertrag ist hier definiert
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`
- Migration zu den von HA explorierten Device-Automation-Alternativen — eigene Folge-Spec

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a device trigger / condition / action for …", „expose a remote button press as a device trigger"
  - „let the user pick this device in the automation editor"
  - „füge einen Device-Trigger / eine Device-Condition / Device-Action für … hinzu"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die Geräte-Interaktion (Prosa), aus der der Skill Art und `CONF_TYPE` ableitet
- **KANN [MAY]** erfassen: `kind` (`trigger`/`condition`/`action`), die `CONF_TYPE`-Werte (und ggf. `subtype`), und ob Capabilities-Extra-Felder nötig sind

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** den Mehrwert-Check fahren: deckt eine Entity-Automation (State-/Event-Trigger) den Bedarf, **SOLLTE [SHOULD]** der Skill darauf hinweisen; nur ein echter Device-zentrierter Bedarf (geräte-eigenes Event ohne Entity-Bindung) rechtfertigt die Device-Automation. Der Skill **MUSS [MUST]** auf HAs Stand hinweisen (keine neuen Device-Automations; bewusste Abwägung)
- **MUSS [MUST]** die `ha/device-automations`-Spec lesen
- **MUSS NICHT [MUST NOT]** ein bestehendes Modul/`CONF_TYPE` überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (pro Art, aus `ha/device-automations`)

- **MUSS [MUST]** das passende Plattform-Modul erzeugen: `device_trigger.py`, `device_condition.py` oder `device_action.py`
- **MUSS [MUST]** für Trigger `async_get_triggers(hass, device_id)` implementieren; jedes Dictionary trägt `CONF_PLATFORM: "device"`, `CONF_DOMAIN`, `CONF_DEVICE_ID` und mindestens `CONF_TYPE`; `TRIGGER_SCHEMA` erweitert `TRIGGER_BASE_SCHEMA` (Modulkonstante); `async_attach_trigger(hass, config, action, trigger_info)` ruft die `action` beim Feuern auf und gibt eine Detach-Funktion zurück
- **MUSS [MUST]** für Conditions `async_get_conditions(hass, device_id)` implementieren; `CONDITION_SCHEMA` leitet von `DEVICE_CONDITION_BASE_SCHEMA` ab; `async_condition_from_config(config, config_validation)` ist `@callback`, liefert eine `bool`-Checker-Funktion und respektiert `config_validation`
- **MUSS [MUST]** für Actions `async_get_actions(hass, device_id)` implementieren; `ACTION_SCHEMA` leitet von `DEVICE_ACTION_BASE_SCHEMA` ab (Modulkonstante); `async_call_action_from_config(hass, config, variables, context)` führt die Action aus
- **MUSS NICHT [MUST NOT]** das jeweilige `*_SCHEMA` manuell auf die Config anwenden — der Core wendet es an, sofern es Modulkonstante ist
- **KANN [MAY]** `async_get_*_capabilities` implementieren, um Extra-Eingabefelder (z. B. `for`-Dauer, Zielwert) für den UI-Editor zu deklarieren, so eng wie möglich gehalten; und einen Eintrag per `"metadata": {"secondary": True}` als sekundär markieren
- **KANN [MAY]** `async_validate_*_config(hass, config)` ergänzen, wenn dynamische Validierung über das statische Schema hinaus nötig ist
- **MUSS [MUST]** für jeden verwendeten `CONF_TYPE` (und ggf. Subtyp) einen human-readable String in `strings.json` unter `device_automation:` pflegen — fehlende Strings zeigen dem User einen Roh-Key
- **MUSS [MUST]** die Module als dünne Adapter halten (auf Event-/State-/Service-Action-Helpers aufsetzen, keine duplizierte Geschäftslogik), Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: das passende Modul existiert; die `async_get_*`-Funktion liefert eine Liste von Dictionaries mit den Pflichtfeldern; `*_SCHEMA` ist Modulkonstante und wird nicht manuell angewendet; die Attach-/Check-/Call-Funktion ist implementiert; jeder `CONF_TYPE` ist in `strings.json` unter `device_automation:` aufgelöst
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/device-automations` liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**keiner**) samt Abwägungs-Hinweis

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als eine Art pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** Geschäftslogik duplizieren, die bereits als Service oder in der Entity-Plattform existiert
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill leitet die Art ab (oder erfragt sie) und fährt den Entity-vs-Device-Mehrwert-Check inkl. HA-Abwägungs-Hinweis
- [ ] Das passende Modul (`device_trigger.py`/`device_condition.py`/`device_action.py`) existiert
- [ ] Die `async_get_*`-Funktion liefert pro `device_id` eine Liste von Dictionaries mit `CONF_PLATFORM`/`CONF_DOMAIN`/`CONF_DEVICE_ID`/`CONF_TYPE`
- [ ] `*_SCHEMA` ist Modulkonstante (erweitert das jeweilige Basis-Schema) und wird nicht manuell angewendet
- [ ] Die Attach-/Check-/Call-Funktion ist korrekt implementiert (Detach-Funktion / `bool`-Checker / Action-Ausführung)
- [ ] Jeder `CONF_TYPE` ist in `strings.json` unter `device_automation:` aufgelöst
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker **keiner** plus Abwägungs-Hinweis

## Offene Fragen

- **Neu-vs-Bestand**: HA nimmt keine neuen Device-Automations mehr an. Soll der Skill grundsätzlich abraten und nur einen Bestands-/Wartungspfad anbieten, sobald die HA-Alternative benannt ist? Aktuell ergänzt er mit explizitem Abwägungs-Hinweis.
- **Capabilities-Rückgabeform**: Welche konkrete Form (`extra_fields` als voluptuous-Schema) schreibt der Skill verbindlich vor? `ha/device-automations` lässt es offen; der Skill folgt dem Doc-Muster und fragt im Zweifel nach.
- **Subtyp-Konvention**: Wann ein `subtype` zusätzlich zum `CONF_TYPE` (z. B. pro Button einer Fernbedienung), und wie in `strings.json` strukturiert? Aktuell fall-zu-fall.
