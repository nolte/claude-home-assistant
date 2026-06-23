# HA-Integration: Services

Status: draft

## Kontext

Eine Custom Integration kann benutzergesteuerte Aktionen über **HA-Services** anbieten — User klickt einen Button im Frontend, eine Automation triggert einen Action-Aufruf, oder ein Skript ruft den Service direkt auf. Services werden über zwei Artefakte deklariert: `services.yaml` (UI-Schema mit Selectors, das die HA-UI rendert) und ein async-Handler, der über `hass.services.async_register(DOMAIN, "<service>", handler, schema=...)` registriert ist (oder über das modernere `hass.services.async_register` mit voluptuous-Schema-Validierung).

`nolte/kamerplanter-ha` validiert dieses Pattern mit fünf Services (`refresh_data`, `clear_cache`, `fill_tank`, `water_channel`, `confirm_care`) und hat dabei drei nicht-offensichtliche Verfeinerungen kodifiziert: (1) **Multi-Instance-Disambiguation** — wenn mehrere Config-Entries laufen und der User ruft den Service ohne `entity_id` auf, muss der Handler erkennen, welcher Entry gemeint ist, oder mit einer klaren Fehlermeldung abbrechen; (2) **Selector-Disziplin** — `entity:` mit `integration:`-Filter statt freier Entity-Strings, `select:` mit `options:`-Listen statt freier Strings, `number:` mit `min`/`max`/`step`; (3) **Idempotency-Guards** — derselbe Service-Aufruf darf nicht zwei identische Backend-Mutationen erzeugen, wenn HA den Aufruf wiederholt.

Die Spec überführt diese Konvention in eine generische Verpflichtung. Service-Sicherheit (Path-Whitelist, Token-Gating) gehört in `ha/security-hardening`; Translations für Service-Namen und Field-Labels gehören in `ha/translations`; Icons für Services gehören in `ha/icons`.

Quality-Scale-Marker: **Silver** (Services mit Schema-Validierung und Selectors sind Silver-Pflicht; Idempotency und Multi-Instance-Sicherheit sind über Silver hinausgehende, aber portfolioseitig erwartete Verfeinerungen).

## Ziele

- `services.yaml` als alleinige Quelle der UI-Renderung — keine Service-Definition ohne YAML-Schema
- Handler-Implementation an einem klar markierten Ort (`__init__.py` oder `services.py`) konsolidieren, statt sie über die Plattform-Module zu verstreuen
- Selectors statt freier String-Felder als Default — die HA-UI bekommt typsichere Auswahllisten, der Handler bekommt validierte Eingaben
- Multi-Instance-Disambiguation explizit lösen, sodass User mit mehreren Config-Entries derselben Integration nicht in stille Fehlauflösungen laufen
- Idempotency-Guards als Default für mutierende Services, damit doppelte HA-Calls nicht zu doppelten Backend-Mutationen führen
- Klare Trennung zwischen `ServiceValidationError` (User-Fehler, im Frontend rendern) und `HomeAssistantError` (interne Fehler, ins Log)

## Nicht-Ziele

- Sicherheits-Hardening von Service-Eingaben (Path-Validation, API-Key-Gating, Bearer-Token-Whitelist) — eigene Spec `ha/security-hardening`
- Service-Translations (`services.<name>.name`, `services.<name>.fields.<field>.name`) — gehört zu `ha/translations`
- Service-Icons (`icons.json:services.<name>.service`) — gehört zu `ha/icons`
- Asynchrone Background-Jobs / Long-Running-Tasks — Services sollten kurz und synchron-feel sein; Background-Work ist Coordinator-Job, nicht Service-Job
- HA-Action-Trigger (`event:<service>_<event>`) für Reverse-Notification — eigene Folge-Spec, sobald die erste Integration so etwas braucht

## Anforderungen

### `services.yaml`

- **MUSS [MUST]** für jeden registrierten Service einen Eintrag in `services.yaml` führen — ohne Eintrag rendert die HA-UI das Service-Formular nicht
- **MUSS [MUST]** in jedem Service-Eintrag mindestens einen `target:`-Block oder eine `fields:`-Map deklarieren; ein Service ohne Eingabe ist syntaktisch erlaubt, aber die meisten Services haben mindestens ein Feld
- **MUSS [MUST]** Felder über typisierte Selectors deklarieren (`selector: { entity: { ... } }`, `selector: { select: { ... } }`, `selector: { number: { ... } }`, `selector: { text: ... }`, `selector: { boolean: ... }`)
- **MUSS NICHT [MUST NOT]** freie String-Felder ohne `selector:` deklarieren, wenn ein passender Selector existiert — die HA-UI rendert dann ein generisches Textfeld, was die Eingabe-Qualität senkt

### Selectors

- **MUSS [MUST]** für `entity_id`-Felder den `entity:`-Selector verwenden, mit `integration: <DOMAIN>` als Filter — der User sieht dann nur Entitäten der eigenen Integration
- **MUSS [MUST]** für Auswahl-Felder mit fester Optionsliste den `select:`-Selector mit `options:`-Liste verwenden, wobei jedes Option-Element `label`/`value` trägt; freie Enum-Strings ohne Liste sind nicht erlaubt
- **MUSS [MUST]** für numerische Felder den `number:`-Selector mit `min`, `max` und `step` verwenden — Schutz vor Tippfehlern und Eingaben jenseits des sinnvollen Bereichs
- **SOLLTE [SHOULD]** für Volumen-, Zeit- und Energie-Felder zusätzlich `unit_of_measurement` setzen, damit die UI die Einheit anzeigt
- **KANN [MAY]** den `target:`-Block statt eines `entity:`-Felds verwenden, wenn der Service mehrere Targets unterstützt (Entitäten, Devices, Areas) — das ist HA-konform und erlaubt Bulk-Aufrufe

### Handler-Platzierung

- **MUSS [MUST]** alle Service-Handler an genau einem Ort im Code anlegen — entweder in `__init__.py` (klein, bis ~5 Services) oder in einem dedizierten `services.py`-Modul
- **MUSS [MUST]** Service-Handler in `async_setup_entry` (oder einem dedizierten Setup-Hook) registrieren: `hass.services.async_register(DOMAIN, "<service>", handler, schema=<SCHEMA>)`
- **SOLLTE [SHOULD]** Service-Schemas mit `voluptuous` deklarieren und die `schema=`-Option an `async_register` übergeben — HA validiert dann die Eingabe vor dem Handler-Call
- **MUSS NICHT [MUST NOT]** Service-Handler in Plattform-Modulen (`sensor.py`, `binary_sensor.py`) registrieren — Service-Registry ist global, Plattformen sind Per-Plattform-Setup

### Multi-Instance-Disambiguation

- **MUSS [MUST]** bei Services, die `entity_id` (oder `target:`-Entitäten) entgegennehmen, den Config-Entry über das Entity-Registry auflösen, statt globale `hass.data`/`runtime_data`-Lookups zu raten
- **MUSS [MUST]** bei Services, die einen Backend-Resource-Schlüssel statt `entity_id` erlauben (z. B. `tank_key="xy"`), den Config-Entry zwingend aus einem **expliziten** Parameter ableiten (`entry_id` als zusätzliches Feld) **oder** den Service nur dann erfolgreich auflösen, wenn genau ein Config-Entry existiert
- **MUSS [MUST]** bei mehreren Config-Entries und nicht-disambiguiertem Aufruf einen `ServiceValidationError` mit klarer Fehlermeldung (`"Multiple config entries — please specify entry_id"`) raisen — niemals stille Auswahl auf den ersten Entry zurückfallen
- **SOLLTE [SHOULD]** Disambiguation-Logik in einem Helper bündeln (`_resolve_entry(hass, call) -> ConfigEntry`), damit alle Service-Handler denselben Resolver verwenden
- **MUSS NICHT [MUST NOT]** auf `async def async_setup_entry`-übergreifende globale Variablen oder Module-Level-Caches zurückgreifen, um den Entry zu raten

### Idempotency-Guards

- **MUSS [MUST]** für Services, die **mutierende** Backend-Calls auslösen (z. B. `fill_tank`, `water_channel`, `confirm_care`), das Mutations-Resultat nach dem Call lokal cachen oder eine Backend-Acknowledgment-ID festhalten
- **SOLLTE [SHOULD]** doppelte Aufrufe erkennen, wenn das Backend einen idempotency-Key oder eine Request-ID akzeptiert — den Key aus den Eingaben deterministisch ableiten (z. B. Hash aus `entity_id + payload + timestamp_within_window`)
- **MUSS NICHT [MUST NOT]** doppelte Aufrufe stillschweigend zweimal ausführen, wenn das Backend keinen idempotency-Schutz bietet — in dem Fall den User mit einer klaren Fehlermeldung warnen oder den Aufruf in einem kurzen Window deduplizieren

### Fehlerbehandlung

- **MUSS [MUST]** User-Fehler (ungültige Eingabe, Validation-Fehlschlag, fehlende Disambiguation) als `homeassistant.exceptions.ServiceValidationError` raisen — HA rendert sie im Frontend als rote Fehlermeldung
- **MUSS [MUST]** interne Fehler (Backend-Verbindung tot, Bug im Handler, unerwartete Exception) als `homeassistant.exceptions.HomeAssistantError` raisen — landet im HA-Log mit Stack-Trace
- **MUSS [MUST]** API-Auth-Fehler innerhalb eines Service-Handlers nicht ins HA-Service-Error-Log dumpen, sondern in `ServiceValidationError("invalid_auth")` umwandeln — der User sieht eine bedeutungsvolle Meldung, der Coordinator triggert den Reauth-Flow beim nächsten regulären Tick
- **MUSS NICHT [MUST NOT]** generische `Exception`-Catches im Handler verwenden — nur konkret bekannte Fehler abfangen, alles andere propagiert

### Coordinator-Refresh nach Mutation

- **SOLLTE [SHOULD]** nach jedem mutierenden Service-Call den zugehörigen Coordinator über `await coordinator.async_request_refresh()` zur erneuten Datenladung anstoßen, sodass die Entitäten den neuen Backend-Stand widerspiegeln
- **MUSS NICHT [MUST NOT]** `coordinator.async_refresh()` (synchron-blocking) aus dem Service-Handler aufrufen — `async_request_refresh()` ist die korrekte Variante; sie debouncet und blockt den Handler nicht

## Akzeptanzkriterien

- [ ] `services.yaml` enthält für jeden registrierten Service einen Eintrag mit `description`, `fields:` (oder `target:`)
- [ ] Alle `fields:` verwenden typisierte Selectors (`entity`, `select`, `number`, `text`, `boolean`)
- [ ] `entity:`-Selectors filtern auf `integration: <DOMAIN>`
- [ ] Service-Handler sind an genau einem Ort registriert (`__init__.py` oder `services.py`)
- [ ] Service-Schemas sind mit `voluptuous` deklariert und an `async_register(..., schema=...)` übergeben
- [ ] Bei mehreren Config-Entries: ein zentraler `_resolve_entry(hass, call)`-Helper bricht mit `ServiceValidationError` ab, wenn der Entry nicht eindeutig auflösbar ist
- [ ] Mutierende Services rufen am Ende `await coordinator.async_request_refresh()` auf
- [ ] User-Fehler werden als `ServiceValidationError` geraised; interne Fehler als `HomeAssistantError`
- [ ] Auth-Fehler im Handler werden in `ServiceValidationError("invalid_auth")` übersetzt, nicht roh propagiert
- [ ] Quality-Scale-Marker: **Silver**

## Offene Fragen

- **`hass.services.async_register` vs. moderner Decorator-API**: HA hat experimentelle Decorator-basierte Service-Registrierung. Soll die Spec auf den klassischen Aufruf bestehen oder den modernen Decorator zulassen, sobald er stabil ist?
- **Idempotency-Window-Default**: Welches Zeitfenster für Deduplikation gilt (5 s, 30 s, gar keines)? Aktuell als „kurz" formuliert — eine konkrete Vorgabe würde Skill-Output deterministisch machen.
- **Multi-Target-Services**: `target:`-Block erlaubt Entity-, Device- und Area-Targets. Soll die Spec den Resolver-Helper für alle drei Target-Typen vorsehen oder bleibt er Entity-zentriert?
- **`response`-feld**: HA unterstützt seit 2024.x Service-Antworten (`return_response`). Soll die Spec response-fähige Services explizit adressieren — wann SOLLTE ein Service Response zurückgeben?
- **Service-Sicherheits-Schwelle**: Ab welcher Service-Klasse wird `ha/security-hardening` Pflicht? Aktuell als Cross-Reference auf eine Folge-Spec; eine konkrete Schwelle (z. B. „Services, die Backend-State mutieren") fehlt hier.
