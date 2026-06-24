# HA-Integration: Frontend-WebSocket-Commands

Status: draft

## Kontext

Eine Custom Integration kann Daten besitzen, die sie dem Frontend verfügbar machen will — das HA-Frontend kommuniziert mit dem Backend über die WebSocket-API, und diese API lässt sich um **eigene Commands** erweitern. Das Standardbeispiel aus der HA-Doku ist der Media-Player, der Album-Cover an das Frontend ausliefert; allgemeiner gilt: sobald eine Karte oder ein Panel integrationsspezifische Daten braucht, die kein State-Attribut sind, ist ein eigener WebSocket-Command der passende Transportweg.

Ein Command besteht laut HA-Doku aus drei Teilen: einem Message-Type, einem Message-Schema und einem Message-Handler. Die Integration muss `websocket_api` **nicht** als Dependency im Manifest führen — der Command wird registriert, und falls der User die WebSocket-API nutzt, steht der Command zur Verfügung. Auf der Python-Seite definiert der Decorator `@websocket_api.websocket_command({...})` Type und Daten-Schema, der Handler sendet das Ergebnis über `connection.send_result(msg["id"], result)` oder einen Fehler über `connection.send_error(...)`, und `websocket_api.async_register_command(hass, ws_handler)` macht den Command verfügbar. Auf der JavaScript-Seite ruft eine Karte oder ein Panel den Command über das `hass`-Objekt auf und wartet auf das Ergebnis-Promise.

Diese Spec überführt das HA-Doku-Pattern in eine generische Verpflichtung. Die Abgrenzung gegen Services regelt `ha/services` (Services = benutzergesteuerte Aktionen/Mutationen; WebSocket-Commands = Lese-/Abfrage-Transport ins Frontend); die Frontend-Konsumentenseite (`callWS`-Aufruf, Typisierung der Antwort) regelt `ha/frontend-data-api`; das Karten-Wiring regelt `ha/lovelace-card-patterns`; die Sync/Async-Handler-Disziplin (`@callback` vs. `async_response`) regelt `ha/async-patterns`.

Quality-Scale-Marker: kein direkter Quality-Scale-Regelpunkt — die HA-Doku verortet WebSocket-Commands nicht in einer Quality-Scale-Stufe. Inhaltlich grenzt das Pattern aber an `ha/diagnostics` (welche Integrationsdaten exponiert werden) und an Data-Exposure-Erwägungen: ein Command, der sensible Daten liefert, **MUSS [MUST]** dieselbe Zugriffsbeschränkung erwägen wie ein Diagnostics-Dump.

## Ziele

- Integrationsspezifische Frontend-Daten über einen eigenen WebSocket-Command transportieren, statt sie in State-Attribute oder Services zu pressen
- Command-Type, -Schema und -Handler nach dem HA-Doku-Pattern an einem klar markierten Ort definieren und über `async_register_command` registrieren
- Sync- gegen Async-Handler bewusst wählen: `@callback` für reine In-Memory-Antworten, `@websocket_api.async_response` für I/O, Geräte-Zugriff oder Berechnung
- Antworten und Fehler über `connection.send_result` / `connection.send_error` mit korrekter `msg["id"]`-Korrelation ausliefern
- Admin-pflichtige Commands explizit über `@websocket_api.require_admin` schützen
- Den Command aus dem Frontend über das `hass`-Objekt aufrufen und das Ergebnis-Promise korrekt awaiten

## Nicht-Ziele

- Benutzergesteuerte Aktionen / Backend-Mutationen — das sind Services; siehe `ha/services` (WebSocket-Commands sind primär Lese-/Abfrage-Transport)
- Die Frontend-Konsumentenseite im Detail (TypeScript-Typisierung der Antwort, `callWS`-Fehlerbehandlung in der Karte) — gehört zu `ha/frontend-data-api`
- Das Karten- und Panel-Wiring (Rendering, Editor, Lifecycle) — gehört zu `ha/lovelace-card-patterns`
- Die generische Sync/Async-Disziplin im Event-Loop (Blocking-I/O, Executor-Jobs) — gehört zu `ha/async-patterns`
- Zugriffs-Hardening über `require_admin` hinaus (Token-Gating, Path-Whitelist) — gehört zu `ha/security-hardening`

## Anforderungen

### Command registrieren (Python, `async_register_command`)

- **MUSS [MUST]** jeden eigenen Command über `websocket_api.async_register_command(hass, ws_handler)` registrieren — ohne Registrierung steht der Command der WebSocket-API nicht zur Verfügung
- **MUSS [MUST]** die Registrierung in der Setup-Methode der Integration vornehmen (z. B. `async_setup`), wie im HA-Doku-Beispiel — nicht verstreut über Plattform-Module
- **MUSS [MUST]** `from homeassistant.components import websocket_api` importieren und den Handler als Callback-Funktion definieren, der im Event-Loop läuft
- **MUSS NICHT [MUST NOT]** `websocket_api` als Dependency im Manifest verlangen, um den Command zu registrieren — laut HA-Doku ist das nicht nötig; der Command wird verfügbar, falls der User die WebSocket-API nutzt

### Command-Schema & `type`

- **MUSS [MUST]** Type und Daten-Schema über den Decorator `@websocket_api.websocket_command({...})` am Handler deklarieren
- **MUSS [MUST]** den Message-Type als `vol.Required("type"): "<domain>/<name>"` namespacen — der Doku-konforme Aufbau ist `"<domain>/<name>"` (z. B. `"camera/get_thumbnail"`)
- **MUSS [MUST]** Eingabefelder über `vol.Required(...)` und `vol.Optional(...)` mit Typ-Annotation im Schema deklarieren (z. B. `vol.Optional("entity_id"): str`)
- **SOLLTE [SHOULD]** das Schema minimal halten und nur die Felder aufnehmen, die der Handler tatsächlich liest

### Antworten (`send_result`/`send_error`)

- **MUSS [MUST]** ein Erfolgsergebnis über `connection.send_result(msg["id"], result)` mit der `msg["id"]` aus der eingehenden Nachricht ausliefern — die `msg["id"]` korreliert Anfrage und Antwort
- **MUSS [MUST]** Fehler über `connection.send_error(msg["id"], "<error_code>", "<message>")` melden, statt eine Exception aus dem Handler propagieren zu lassen (Doku-Beispiel: `"entity_not_found"`, `"thumbnail_fetch_failed"`)
- **MUSS [MUST]** nach jedem `send_error`-Pfad den Handler verlassen (`return`), damit nicht zusätzlich ein `send_result` für dieselbe `msg["id"]` gesendet wird
- **MUSS NICHT [MUST NOT]** die `msg["id"]` durch einen anderen Wert ersetzen — ohne die korrekte ID kann das Frontend die Antwort nicht dem Aufruf zuordnen

### Sync vs. async (`@callback`/`async_response`)

- **MUSS [MUST]** einen Handler, der nur In-Memory-Daten zurückgibt (keine Netzwerk-, Geräte- oder Berechnungs-Arbeit), als synchrone Funktion mit `@callback` deklarieren — wie das `ws_get_panels`-Beispiel der HA-Doku
- **MUSS [MUST]** einen Handler, der mit dem Netzwerk oder einem Gerät interagiert oder Informationen berechnen muss, als `async def` schreiben und mit `@websocket_api.async_response` dekorieren — laut HA-Doku ist das der Weg, um Arbeit zu queuen und eine verzögerte Antwort zu senden
- **MUSS NICHT [MUST NOT]** blockierende I/O in einem `@callback`-Handler ausführen — solche Arbeit gehört in einen `@websocket_api.async_response`-Handler

### Admin-Beschränkung (`require_admin`)

- **MUSS [MUST]** Commands, die nur Administratoren ausführen dürfen, mit `@websocket_api.require_admin` dekorieren
- **SOLLTE [SHOULD]** `require_admin` für jeden Command erwägen, der sensible oder integrationsinterne Daten liefert — die Voreinstellung ist „nicht exponieren, wenn nicht nötig"
- **MUSS NICHT [MUST NOT]** Admin-Prüfungen von Hand im Handler-Body nachbauen, wenn `@websocket_api.require_admin` den Zweck erfüllt

### Aufruf aus dem Frontend (`hass.callWS`)

- **MUSS [MUST]** den Command aus dem Frontend über das `hass`-Objekt aufrufen, das die WebSocket-Verbindung zum Backend hält — `await hass.callWS({ type: "<domain>/<name>", ... })`
- **MUSS [MUST]** im `callWS`-Aufruf denselben `type`-String und dieselben Feldnamen verwenden, die das Python-Schema deklariert
- **MUSS [MUST]** das von `callWS` zurückgegebene Promise awaiten und das Ergebnis verarbeiten — eine Karte oder ein Panel konsumiert den Command, um integrationsspezifische Daten zu laden
- **SOLLTE [SHOULD]** einen eigenen WebSocket-Command (statt eines Services) wählen, wenn das Ziel ist, integrationsspezifische Daten in eine Karte zu holen; ein Service ist die Wahl für benutzergesteuerte Aktionen/Mutationen

## Akzeptanzkriterien

- [ ] Jeder Command ist über `websocket_api.async_register_command(hass, ws_handler)` in der Setup-Methode registriert
- [ ] Type und Schema sind über `@websocket_api.websocket_command({...})` deklariert; `type` ist als `"<domain>/<name>"` genamespaced
- [ ] Eingabefelder nutzen `vol.Required`/`vol.Optional` mit Typ-Annotation
- [ ] Erfolg wird über `connection.send_result(msg["id"], result)` mit korrekter `msg["id"]` ausgeliefert
- [ ] Fehler werden über `connection.send_error(msg["id"], code, message)` gemeldet, gefolgt von `return`
- [ ] In-Memory-Handler nutzen `@callback`; I/O-/Geräte-/Berechnungs-Handler nutzen `@websocket_api.async_response` mit `async def`
- [ ] Admin-pflichtige Commands sind mit `@websocket_api.require_admin` dekoriert
- [ ] Der Frontend-Aufruf nutzt `hass.callWS({ type: "<domain>/<name>", ... })` mit demselben `type` und denselben Feldnamen wie das Python-Schema und awaitet das Ergebnis
- [ ] Die Wahl Command vs. Service ist begründet: Datenabruf ins Frontend → Command, Aktion/Mutation → Service (`ha/services`)

## Offene Fragen

- **Schema-Validierungs-Fehler**: Die HA-Doku zeigt fachliche Fehler über `send_error`, sagt aber nichts über Schema-Validierungs-Fehler (ungültiger Payload). Soll die Spec einen Standard-Error-Code für Schema-Verstöße vorgeben?
- **Subscription-Commands**: Manche WebSocket-Commands sind langlebige Subscriptions (Stream von Events), nicht Einmal-Anfragen. Die Doku-Beispiele sind Request/Response. Soll die Spec Subscription-Commands als eigene Unterklasse adressieren?
- **`callWS` vs. `sendMessagePromise`**: Die HA-Doku zeigt den Frontend-Aufruf über `hass.connection.sendMessagePromise`; das gängigere High-Level-API ist `hass.callWS`. Soll die Spec ausschließlich `callWS` vorschreiben und `sendMessagePromise` nur als Low-Level-Fallback nennen?
- **Data-Exposure-Schwelle**: Ab wann wird `@require_admin` Pflicht statt SOLLTE? Aktuell als Erwägung formuliert — eine konkrete Schwelle (z. B. „liefert personenbezogene oder Backend-interne Daten") würde Skill-Output deterministisch machen.
- **Versionierung des `type`**: Wenn sich das Antwort-Schema eines Commands ändert, fehlt ein Versionierungs-Mechanismus im `type`-String. Soll die Spec eine Konvention (`"<domain>/<name>/v2"`) vorgeben?
