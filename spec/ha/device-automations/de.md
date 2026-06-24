# HA-Integration: Device-Automations

Status: draft

## Kontext

Device-Automations geben Usern eine geräte-zentrierte Schicht über den Kernkonzepten von Home Assistant: Statt mit States und Events zu hantieren, wählen sie ein Device und dann aus einer Liste vordefinierter Trigger, Conditions und Actions. Integrationen klinken sich in dieses System ein, indem sie Funktionen exponieren, die diese vordefinierten Trigger, Conditions und Actions generieren, und Funktionen bereitstellen, die einen Trigger anhängen, eine Condition prüfen und eine Action ausführen. Device-Automations exponieren keine zusätzliche Funktionalität — sie sind eine Übersetzungsschicht, die intern auf den Event-, State- und Service-Action-Helpers aufsetzt, damit User keine neuen Konzepte lernen müssen.

Eine Integration nimmt an Device-Automations teil, indem sie die drei Plattform-Module `device_trigger.py`, `device_condition.py` und/oder `device_action.py` bereitstellt. Trigger, Conditions und Actions können von der Integration kommen, die das Device bereitstellt (z. B. ZHA, deCONZ — typisch für Events, die an kein Entity gebunden sind, etwa Tastendruck auf einer Fernbedienung), oder von den Entity-Integrationen, deren Entities das Device hat (z. B. `light`, `switch` — etwa „Licht eingeschaltet"). Diese Spec überführt die Konvention aus den HA-Developer-Docs in eine generische Verpflichtung für jede Custom Integration, die Skills aus diesem Plugin scaffolden.

Quality-Scale-Marker: **keiner** (Device-Automations sind kein Quality-Scale-Kriterium; HA exploriert aktiv Alternativen und nimmt keine neuen Device-Automations mehr an — bestehende laufen weiter, neue Implementierungen sind eine bewusste Abwägung, kein Standard-Scaffold).

## Ziele

- Die drei Plattform-Module (`device_trigger.py`, `device_condition.py`, `device_action.py`) als kanonische Struktur für Device-Automations festschreiben
- Den Vertrag der `async_get_*`-Funktionen erzwingen: pro `device_id` eine Liste von Dictionaries, die das jeweilige Basis-Schema erfüllen
- Statische Validierung über modulkonstante Schemas (`TRIGGER_SCHEMA` / `CONDITION_SCHEMA` / `ACTION_SCHEMA`) durch den Core, statt manueller Schema-Anwendung
- Korrektes Anhängen, Prüfen und Ausführen über `async_attach_trigger`, `async_condition_from_config`, `async_call_action_from_config`
- Extra-Felder über die `async_get_*_capabilities`-Funktionen exponieren, damit der UI-Editor zusätzliche Eingaben erzeugt
- Human-readable Strings für alle Trigger-, Condition- und Action-Typen in `strings.json` unter `device_automation:` pflegen

## Nicht-Ziele

- Entity-Automations (das State-/Event-basierte Standardmodell ohne Device-Indirektion) — die geräte-zentrierte Schicht ist hier definiert, das darunterliegende Modell in `ha/entity-architecture`
- Service-Actions im klassischen Sinn (registrierte Services mit eigenem Schema) — Device-Actions delegieren intern an Service-Action-Helper, sind aber kein Ersatz für `ha/services`
- Die UI-Editor-Logik des Frontends — diese Spec definiert nur den Backend-Vertrag der Integration
- Migration bestehender Device-Automations oder Bridging zu den von HA explorierten Alternativen — eigene Folge-Spec, sobald die Alternative konkret wird

## Anforderungen

### Device-Trigger

- **MUSS [MUST]** ein `device_trigger.py`-Modul bereitstellen, wenn die Integration Device-Trigger anbietet
- **MUSS [MUST]** `async_get_triggers(hass, device_id)` implementieren und eine Liste von Trigger-Dictionaries zurückgeben, die das Device oder seine assoziierten Entities unterstützen
- **MUSS [MUST]** jedes Trigger-Dictionary mit den Pflichtfeldern des `TRIGGER_BASE_SCHEMA` füllen (`CONF_PLATFORM: "device"`, `CONF_DOMAIN`, `CONF_DEVICE_ID`) plus den Pflichtfeldern des eigenen `TRIGGER_SCHEMA` (mindestens `CONF_TYPE`)
- **MUSS [MUST]** `TRIGGER_SCHEMA` als Modulkonstante definieren, die `TRIGGER_BASE_SCHEMA` aus `device_automation/__init__.py` erweitert; der Core wendet dieses Schema an
- **MUSS [MUST]** `async_attach_trigger(hass, config, action, trigger_info)` implementieren, das die `action` aufruft, wenn der Trigger feuert (z. B. via `event_trigger.async_attach_trigger(..., platform_type="device")`), und eine Detach-Funktion zurückgibt
- **MUSS NICHT [MUST NOT]** das `TRIGGER_SCHEMA` manuell auf die Config anwenden — der Core wendet es an, sofern es als Modulkonstante definiert ist
- **KANN [MAY]** `async_validate_trigger_config(hass, config)` implementieren, wenn der Trigger dynamische Validierung braucht, die das statische `TRIGGER_SCHEMA` nicht leisten kann

### Device-Conditions

- **MUSS [MUST]** ein `device_condition.py`-Modul bereitstellen, wenn die Integration Device-Conditions anbietet
- **MUSS [MUST]** `async_get_conditions(hass, device_id)` implementieren und eine Liste der Conditions zurückgeben, die das Device unterstützt
- **MUSS [MUST]** `CONDITION_SCHEMA` aus `homeassistant.helpers.config_validation.DEVICE_CONDITION_BASE_SCHEMA` ableiten
- **MUSS [MUST]** `async_condition_from_config(config, config_validation)` als `@callback` implementieren, das eine async-freundliche Checker-Funktion zurückgibt, welche die Condition auswertet und einen `bool` liefert
- **MUSS [MUST]** den `config_validation`-Parameter respektieren — der Core nutzt ihn, um die Config-Validierung gegen das `CONDITION_SCHEMA` bedingt anzuwenden
- **KANN [MAY]** `async_validate_condition_config(hass, config)` implementieren, wenn die Condition dynamische Validierung braucht, die das statische `CONDITION_SCHEMA` nicht leisten kann

### Device-Actions

- **MUSS [MUST]** ein `device_action.py`-Modul bereitstellen, wenn die Integration Device-Actions anbietet
- **MUSS [MUST]** `async_get_actions(hass, device_id)` implementieren und eine Liste der Actions zurückgeben, die das Device unterstützt
- **MUSS [MUST]** `ACTION_SCHEMA` aus `homeassistant.helpers.config_validation.DEVICE_ACTION_BASE_SCHEMA` ableiten und als Modulkonstante definieren; der Core wendet es an
- **MUSS [MUST]** `async_call_action_from_config(hass, config, variables, context)` implementieren, das die übergebene Action ausführt
- **MUSS NICHT [MUST NOT]** das `ACTION_SCHEMA` manuell auf die Config anwenden — der Core wendet es an, sofern es als Modulkonstante definiert ist
- **KANN [MAY]** `async_validate_action_config(hass, config)` implementieren, wenn die Action dynamische Validierung braucht, die das statische `ACTION_SCHEMA` nicht leisten kann

### Capabilities (Extra-Felder)

- **KANN [MAY]** `async_get_trigger_capabilities`, `async_get_condition_capabilities` bzw. `async_get_action_capabilities` implementieren, um pro Eintrag zusätzliche Eingabefelder zu deklarieren (z. B. eine `for`-Dauer oder einen Zielwert), die der UI-Editor rendert
- **SOLLTE [SHOULD]** die Capability-Felder so eng wie möglich am tatsächlich benötigten Eingabesatz halten, damit der UI-Editor nicht mit irrelevanten Feldern überladen wird
- **KANN [MAY]** eine Device-Automation per `"metadata": {"secondary": True}` als sekundär markieren, damit Devices mit vielen Automations den User nicht überfordern; sekundäre Einträge werden nachrangig oder hinter „mehr anzeigen" dargestellt
- **MUSS [MUST]** bei einem `entity_id`-bezogenen Eintrag akzeptieren, dass der Core das `secondary`-Flag automatisch auf `True` setzt, wenn das referenzierte Entity versteckt ist oder eine Entity-Category ungleich `None` hat (siehe `ha/device-registry` für die Entity-zu-Device-Zuordnung)

### Übersetzungen

- **MUSS [MUST]** für jeden Trigger-, Condition- und Action-Typ einen human-readable String in `strings.json` unter dem Schlüssel `device_automation:` pflegen (z. B. `trigger_type`, `condition_type`, `action_type`)
- **MUSS [MUST]** jeden in den `async_get_*`-Listen verwendeten `CONF_TYPE`-Wert (und ggf. Subtyp) in `strings.json` abdecken — fehlende Strings zeigen dem User einen Roh-Key statt eines Namens
- **SOLLTE [SHOULD]** die Übersetzungen lokal mit `python3 -m script.translations develop` gegenprüfen und im Übrigen den Übersetzungs-Workflow aus `ha/translations` befolgen

### Abgrenzung zu Entity-Automations

- **MUSS [MUST]** Device-Automations nur dann anbieten, wenn sie dem User echten Mehrwert gegenüber dem darunterliegenden State-/Event-Modell bieten — sie exponieren keine neue Funktionalität, sondern setzen auf Event-, State- und Service-Action-Helpers auf
- **SOLLTE [SHOULD]** Device-Actions klar von registrierten Services (`ha/services`) trennen: eine Device-Action delegiert intern an einen Service-Action-Helper, ist aber keine eigenständige, von außen aufrufbare Service-Definition
- **MUSS NICHT [MUST NOT]** Geschäftslogik in den Device-Automation-Modulen duplizieren, die bereits als Service oder in der Entity-Plattform existiert — die Module bleiben dünne Adapter

## Akzeptanzkriterien

- [ ] Für jede angebotene Automation-Art existiert das passende Modul (`device_trigger.py`, `device_condition.py`, `device_action.py`)
- [ ] `async_get_triggers` / `async_get_conditions` / `async_get_actions` geben pro `device_id` eine Liste von Dictionaries zurück
- [ ] Jedes Trigger-Dictionary enthält `CONF_PLATFORM: "device"`, `CONF_DOMAIN`, `CONF_DEVICE_ID` und `CONF_TYPE`
- [ ] `TRIGGER_SCHEMA` erweitert `TRIGGER_BASE_SCHEMA`; `CONDITION_SCHEMA` / `ACTION_SCHEMA` leiten von den jeweiligen `DEVICE_*_BASE_SCHEMA` ab — alle als Modulkonstanten
- [ ] Kein Modul wendet sein Schema manuell auf die Config an
- [ ] `async_attach_trigger` ruft die `action` beim Feuern auf und gibt eine Detach-Funktion zurück
- [ ] `async_condition_from_config` liefert eine `bool`-Checker-Funktion und respektiert `config_validation`
- [ ] `async_call_action_from_config` führt die übergebene Action aus
- [ ] Falls Extra-Felder gebraucht werden, ist die passende `async_get_*_capabilities`-Funktion implementiert
- [ ] `strings.json` enthält unter `device_automation:` einen Eintrag für jeden verwendeten Typ
- [ ] Quality-Scale-Marker für dieses Pattern ist gesetzt: **keiner**

## Offene Fragen

- **Alternativen-Migration**: HA exploriert aktiv Alternativen zu Device-Automations und nimmt keine neuen mehr an. Soll diese Spec das Scaffolding neuer Device-Automations grundsätzlich abraten und nur einen Wartungs-/Bestandspfad definieren, sobald die Alternative benannt ist?
- **Capabilities-Schema-Form**: Die Docs beschreiben die `async_get_*_capabilities`-Funktionen nur konzeptionell. Welche konkrete Rückgabeform (`extra_fields` als voluptuous-Schema?) soll die Spec als verbindlich festschreiben?
- **Subtyp-Konvention**: Wann verlangt die Spec einen `subtype` zusätzlich zum `CONF_TYPE` (z. B. pro Kanal/Button einer Fernbedienung), und wie wird er in `strings.json` strukturiert?
- **Entity- vs. Device-Quelle**: Soll die Spec eine Heuristik festschreiben, wann ein Trigger/eine Condition/Action von der Device-Integration kommt versus von der Entity-Integration, oder bleibt das eine Fall-zu-Fall-Entscheidung?
