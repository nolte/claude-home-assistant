# Skill: `ha-service-definition-generator`

Status: draft

## Kontext

`ha/services` definiert das Pattern: `services.yaml` als UI-Schema mit Selectors, Handler in `__init__.py` oder `services.py`, Multi-Instance-Disambiguation, Idempotency-Guards, sauberes Error-Mapping (`ServiceValidationError` für User-Fehler, `HomeAssistantError` für interne Fehler), Coordinator-Refresh nach Mutation. Die initiale Scaffold-Phase liefert keine Services aus, weil sie integration-spezifisch sind. Dieser Skill ergänzt sie: pro Aufruf einen Service mit definierten Feldern, Selectors, Translation-Strings, Icon, Handler-Stub und Test.

## Scope

Der Skill ergänzt einen oder mehrere Services in `services.yaml` plus Handler in `__init__.py` (oder `services.py`, sobald die Service-Anzahl jenseits von ~5 liegt). Er löscht keine Services, mergt keine Service-Definitionen und ändert kein bestehendes Service-Schema — bei Konflikt auf gleichem `service`-Schlüssel wird abgebrochen.

## Ziele

- Service-Definition deterministisch aus einer Felder-Beschreibung generieren — kein freier YAML-Edit, der Selector-Konventionen vergisst
- Multi-Instance-Disambiguation als Default-Pattern einziehen — der Handler-Stub ruft den `_resolve_entry`-Helper, der bei Mehrdeutigkeit `ServiceValidationError` raised
- Idempotency-Guard-Skelett für mutierende Services — der Handler reserviert eine Stelle für den Backend-Acknowledgment-Lookup
- Coordinator-Refresh nach Mutation als Pflicht-Aufruf — `await coordinator.async_request_refresh()` ist Teil des Handler-Stubs für mutierende Services
- Cross-File-Konsistenz: `services.yaml`, `strings.json` (`services.<name>.name/description/fields.<f>.name/description`), `translations/<lang>.json`, `icons.json` (`services.<name>.service`)

## Nicht-Ziele

- Backend-Mutation-Logik selbst (welcher API-Endpoint, welche Payload-Konstruktion, welche Response-Validierung) — Konsumenten-Aufgabe; der Handler-Stub ruft eine Backend-Methode aus `api.py`, deren Existenz vom Skill geprüft wird
- Service-Removal — manuelle Aufgabe
- Service-Response-Pattern (`return_response=True`) — eigene Folge-Spec, sobald die erste Integration es konkret braucht
- Cross-Service-State-Sharing — nicht gewollt; jeder Service-Aufruf ist atomar

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a service `<name>` that does <X>"
  - „add a `refresh_data` service"
  - „add a service to confirm a notification"
  - „füge einen Service `<name>` hinzu"
- **MUSS NICHT [MUST NOT]** aktivieren bei:
  - Service-Removal
  - Service-Schema-Migration
  - Greenfield-Scaffold

### Eingaben

- **MUSS [MUST]** erfassen:
  - `target_dir`
  - `service_name` — lowercase ASCII snake_case (`refresh_data`, `confirm_notification`, …)
  - `description` — 1–2 Sätze, was der Service tut
  - `mutating` — bool; mutierende Services bekommen Idempotency-Guard und Coordinator-Refresh
  - `fields` — Liste von Feld-Dicts mit `name`, `selector_type` (`entity` / `select` / `number` / `text` / `boolean` / `target`), `required` (bool), `default` (optional), Selector-spezifische Optionen (`options` für `select`, `min`/`max`/`step` für `number`, …)
  - `coordinator_role` — bei `mutating=true`: welcher Coordinator-Schlüssel aus `RuntimeData.coordinators` nach Mutation refreshed wird
  - `api_method` — der Name der Backend-API-Methode in `api.py`, die der Handler aufruft

### Pre-Flight

- **MUSS [MUST]** prüfen:
  1. `target_dir` ist git-Repo, sauber
  2. `<target_dir>/custom_components/<domain>/services.yaml` (legt es neu an, falls noch nicht vorhanden — Logik im Generator)
  3. Service-Schlüssel `<service_name>` ist nicht bereits in `services.yaml`
  4. `api.py` enthält die `api_method` (oder User wird darauf hingewiesen)

### Generator-Choreographie

- **MUSS [MUST]** in `services.yaml` einen neuen Service-Eintrag anlegen — falls die Datei noch nicht existiert, sie neu erzeugen mit YAML-Header und initialem Service
- **MUSS [MUST]** das Service-Schema (Feld-Validation) als `voluptuous`-Schema in `__init__.py` (oder `services.py`, falls existent) anhängen — typisch `<SERVICE>_SCHEMA = vol.Schema({...})`
- **MUSS [MUST]** den Handler-Stub als `async def _async_handle_<service_name>(call: ServiceCall) -> None` in `__init__.py` (oder `services.py`) anlegen, der:
  1. den `_resolve_entry(hass, call)`-Helper aufruft (anlegen, falls noch nicht vorhanden)
  2. die Eingaben aus `call.data` über das Schema validiert (HA macht das vor dem Handler-Aufruf, aber der Stub dokumentiert die Felder)
  3. die Backend-API-Methode aufruft, mit Try-Except auf API-spezifische Auth-/Connection-Exceptions
  4. bei `mutating=true`: `await entry.runtime_data.coordinators[<coordinator_role>].async_request_refresh()`
  5. Auth-Fehler in `ServiceValidationError("invalid_auth")` umwandelt
- **MUSS [MUST]** in `async_setup_entry` (oder einer dedizierten Service-Setup-Funktion) `hass.services.async_register(DOMAIN, "<service_name>", _async_handle_<service_name>, schema=<SERVICE>_SCHEMA)` aufrufen
- **MUSS [MUST]** in `strings.json` und allen `translations/<lang>.json` die Translation-Keys für `services.<service_name>.name`, `services.<service_name>.description`, `services.<service_name>.fields.<field>.name`, `services.<service_name>.fields.<field>.description` anlegen
- **MUSS [MUST]** in `icons.json` `services.<service_name>.service` mit einem passenden Material-Design-Icon ergänzen
- **MUSS [MUST]** in `tests/` einen Test-Block für den Service ergänzen — typisch in `tests/test_services.py` (anlegen falls noch nicht da) — mit Tests für: erfolgreichen Aufruf, fehlende Disambiguation, Auth-Fehler

### Verbote

- **MUSS NICHT [MUST NOT]** existierende Services überschreiben
- **MUSS NICHT [MUST NOT]** generische `Exception`-Catches im Handler-Stub einbauen
- **MUSS NICHT [MUST NOT]** Background-Tasks oder Long-Running-Logik im Handler einbauen — Services sind kurz und synchron-feel; Background gehört in Coordinator

## Akzeptanzkriterien

- [ ] `services.yaml` enthält den neuen Service-Eintrag mit allen Feldern und Selectors
- [ ] `__init__.py` (oder `services.py`) enthält das `<SERVICE>_SCHEMA` und den Handler-Stub
- [ ] `_resolve_entry`-Helper ist verfügbar (anlegen, falls noch nicht vorhanden)
- [ ] `hass.services.async_register(...)` ist aufgerufen
- [ ] Translation-Keys sind in `strings.json` und allen `translations/<lang>.json`
- [ ] `services.<service>.service`-Icon ist in `icons.json`
- [ ] Tests für den Service laufen fehlerfrei
- [ ] `ruff check custom_components/<domain>/` läuft fehlerfrei

## Offene Fragen

- **`services.py` vs. Inline in `__init__.py`-Schwelle**: Aktuell als „bis ~5 Services in `__init__.py`, danach `services.py`" formuliert; eine konkrete Schwelle fehlt.
- **Default-Icon-Auswahl**: Soll der Skill das Icon aus dem Service-Namen heuristisch auswählen oder muss der User es angeben? Aktuell als „passendes mdi:" formuliert ohne klare Logik.
- **Backend-Methoden-Lookup**: Soll der Skill `api.py` lesen und Methoden-Vorschläge generieren?
- **`return_response`-Variant**: Wann verlangt eine Folge-Spec den Response-Pattern?
