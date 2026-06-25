# Skill: `ha-websocket-command-add`

Status: draft

## Kontext

`ha/frontend-websocket-commands` definiert, wie eine Custom Integration die WebSocket-API um einen **eigenen Command** erweitert — den Backend-Endpunkt, den eine Karte oder ein Panel aufruft, um integrationsspezifische Daten zu laden, die kein State-Attribut sind. Laut HA-Doku besteht ein Command aus drei Teilen: Message-Type, Message-Schema und Message-Handler. Auf der Python-Seite deklariert `@websocket_api.websocket_command({...})` Type und Daten-Schema, der Handler sendet das Ergebnis über `connection.send_result(msg["id"], result)` oder einen Fehler über `connection.send_error(...)`, und `websocket_api.async_register_command(hass, ws_handler)` macht den Command verfügbar. Bislang gibt es keinen Skill, der das ergänzt.

Dieser Skill ergänzt **einen** WebSocket-Command in einer **bestehenden** Integration: den dekorierten Handler, sein voluptuous-Schema mit `"<domain>/<name>"`-Type, die korrekte Sync-/Async-Wahl (`@callback` vs. `@websocket_api.async_response`), die `send_result`/`send_error`-Auslieferung mit korrekter `msg["id"]`-Korrelation, optional `@websocket_api.require_admin`, und die `async_register_command`-Verdrahtung in der Setup-Methode — spec-konform zu `ha/frontend-websocket-commands`. Vor der Generierung prüft er, ob die Daten ins Frontend gelesen werden (Command) oder eine Aktion/Mutation ausgelöst wird (Service).

## Scope

Ergänzung genau eines WebSocket-Commands pro Lauf in einer bestehenden `custom_components/<domain>/`-Integration: der mit `@websocket_api.websocket_command({...})` dekorierte Handler, das voluptuous-Schema mit `vol.Required("type"): "<domain>/<name>"`, die Sync-/Async-Form mit `@callback` oder `@websocket_api.async_response`, die `connection.send_result` / `connection.send_error`-Pfade, optional `@websocket_api.require_admin`, und der `async_register_command(hass, ws_handler)`-Aufruf in der Setup-Methode (z. B. `async_setup`). Der Skill liest `ha/frontend-websocket-commands` und validiert offline. Die Frontend-Konsumentenseite wird höchstens als `callWS`-Aufrufbeispiel skizziert, nicht im Detail ausgebaut.

## Ziele

- Aus einem beschriebenen Daten-Bedarf einer Karte/eines Panels einen spec-konformen WebSocket-Command ableiten und ergänzen
- Den Drei-Teile-Vertrag erzwingen: Message-Type als `"<domain>/<name>"`, voluptuous-Schema mit `vol.Required`/`vol.Optional` und Typ-Annotation, Handler mit Signatur `(hass, connection, msg)`
- Sync gegen Async bewusst wählen: `@callback` für reine In-Memory-Antworten, `@websocket_api.async_response` mit `async def` für I/O, Geräte-Zugriff oder Berechnung
- Antworten und Fehler über `connection.send_result(msg["id"], result)` / `connection.send_error(msg["id"], code, message)` mit korrekter `msg["id"]`-Korrelation ausliefern und nach jedem `send_error` zurückkehren
- Admin-pflichtige oder sensible Commands über `@websocket_api.require_admin` schützen
- Den Command über `async_register_command(hass, ws_handler)` in der Setup-Methode registrieren — nicht über Plattform-Module verstreut

## Nicht-Ziele

- Benutzergesteuerte Aktionen / Backend-Mutationen mit eigenem Schema — das sind Services; `ha-service-definition-generator` / `ha/services`
- Die Frontend-Konsumentenseite im Detail (TypeScript-Typisierung der Antwort, `callWS`-Fehlerbehandlung in der Karte) — `ha/frontend-data-api`
- Ein eigenes Panel, das den Command konsumiert — `ha-panel-add`
- Die generische Sync/Async-Disziplin im Event-Loop (Blocking-I/O, Executor-Jobs) — `ha/async-patterns`
- Zugriffs-Hardening über `require_admin` hinaus (Token-Gating, Path-Whitelist) — `ha/security-hardening`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a websocket command", „expose a backend endpoint to my card", „register a custom ws command"
  - „let my card fetch integration data from the backend"
  - „füge ein WebSocket-Command hinzu", „registriere einen eigenen WS-Command"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und den Daten-Bedarf (Prosa), aus dem der Skill Type-Name, Schema-Felder und Handler-Logik ableitet
- **KANN [MAY]** erfassen: den `"<domain>/<name>"`-Type, die Schema-Felder (`vol.Required`/`vol.Optional`), ob der Handler I/O macht (Sync/Async-Wahl) und ob `require_admin` nötig ist

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** die Command-vs-Service-Wahl klären: ist das Ziel ein Datenabruf ins Frontend, ist ein Command richtig; ist es eine benutzergesteuerte Aktion/Mutation, **MUSS [MUST]** der Skill auf `ha-service-definition-generator` verweisen und abbrechen
- **MUSS [MUST]** die `ha/frontend-websocket-commands`-Spec lesen
- **MUSS NICHT [MUST NOT]** einen bestehenden Command-Type überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/frontend-websocket-commands`)

- **MUSS [MUST]** `from homeassistant.components import websocket_api` importieren und den Handler mit Signatur `(hass, connection, msg)` definieren
- **MUSS [MUST]** Type und Daten-Schema über `@websocket_api.websocket_command({...})` am Handler deklarieren; der Message-Type ist als `vol.Required("type"): "<domain>/<name>"` genamespaced (Doku-Beispiel: `"camera/get_thumbnail"`)
- **MUSS [MUST]** Eingabefelder über `vol.Required(...)` und `vol.Optional(...)` mit Typ-Annotation deklarieren und das Schema minimal halten (nur Felder, die der Handler liest)
- **MUSS [MUST]** einen reinen In-Memory-Handler synchron mit `@callback` deklarieren; einen Handler mit Netzwerk-, Geräte- oder Berechnungs-Arbeit als `async def` schreiben und mit `@websocket_api.async_response` dekorieren
- **MUSS NICHT [MUST NOT]** blockierende I/O in einem `@callback`-Handler ausführen — solche Arbeit gehört in einen `@websocket_api.async_response`-Handler
- **MUSS [MUST]** ein Erfolgsergebnis über `connection.send_result(msg["id"], result)` mit der eingehenden `msg["id"]` ausliefern und Fehler über `connection.send_error(msg["id"], "<error_code>", "<message>")` melden, statt eine Exception propagieren zu lassen; nach jedem `send_error`-Pfad **MUSS [MUST]** der Handler zurückkehren (`return`)
- **MUSS NICHT [MUST NOT]** die `msg["id"]` durch einen anderen Wert ersetzen — ohne korrekte ID kann das Frontend die Antwort nicht zuordnen
- **MUSS [MUST]** Admin-pflichtige Commands mit `@websocket_api.require_admin` dekorieren und **MUSS NICHT [MUST NOT]** Admin-Prüfungen von Hand im Handler-Body nachbauen; bei sensiblen oder integrationsinternen Daten **SOLLTE [SHOULD]** `require_admin` erwogen werden
- **MUSS [MUST]** den Command über `websocket_api.async_register_command(hass, ws_handler)` in der Setup-Methode der Integration (z. B. `async_setup`) registrieren — nicht über Plattform-Module verstreut
- **MUSS NICHT [MUST NOT]** `websocket_api` als Manifest-Dependency verlangen, um den Command zu registrieren
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: der Handler trägt `@websocket_api.websocket_command({...})`; der `type` ist als `"<domain>/<name>"` genamespaced; Eingabefelder nutzen `vol.Required`/`vol.Optional` mit Typ-Annotation; die Sync-/Async-Wahl passt zur Arbeit (`@callback` vs. `@websocket_api.async_response`); Erfolg geht über `send_result(msg["id"], ...)`, Fehler über `send_error(msg["id"], ...)` gefolgt von `return`; `require_admin` ist gesetzt, wo nötig; `async_register_command` steht in der Setup-Methode
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/frontend-websocket-commands` liefern, plus die geänderten Datei-Pfade und die begründete Command-vs-Service-Wahl

### Verbote

- **MUSS NICHT [MUST NOT]** mehr als einen Command pro Lauf ergänzen
- **MUSS NICHT [MUST NOT]** einen Command für eine benutzergesteuerte Aktion/Mutation generieren — das ist ein Service
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill fährt die Command-vs-Service-Wahl und bricht bei Aktion/Mutation zugunsten `ha-service-definition-generator` ab
- [ ] Der Handler trägt `@websocket_api.websocket_command({...})`; der `type` ist als `"<domain>/<name>"` genamespaced
- [ ] Eingabefelder nutzen `vol.Required`/`vol.Optional` mit Typ-Annotation und das Schema ist minimal
- [ ] Die Sync-/Async-Form passt zur Arbeit: `@callback` für In-Memory, `@websocket_api.async_response` mit `async def` für I/O/Geräte/Berechnung
- [ ] Erfolg geht über `connection.send_result(msg["id"], result)`, Fehler über `connection.send_error(msg["id"], code, message)` gefolgt von `return`; die `msg["id"]` bleibt unverändert
- [ ] Admin-pflichtige Commands sind mit `@websocket_api.require_admin` dekoriert
- [ ] Der Command ist über `websocket_api.async_register_command(hass, ws_handler)` in der Setup-Methode registriert (keine Manifest-Dependency)
- [ ] Bericht nennt Datei-Pfade und begründet die Command-vs-Service-Wahl

## Offene Fragen

- **Schema-Validierungs-Fehler**: `ha/frontend-websocket-commands` lässt offen, welcher Error-Code für einen ungültigen Payload gilt. Bis das geklärt ist, übernimmt der Skill nur fachliche `send_error`-Codes aus dem Doku-Muster und fragt im Zweifel nach.
- **Subscription-Commands**: Die Doku-Beispiele sind Request/Response; langlebige Subscriptions sind in der Spec eine offene Frage. Der Skill generiert vorerst nur Einmal-Anfragen.
- **Data-Exposure-Schwelle**: Ab wann `@require_admin` Pflicht statt SOLLTE ist, lässt die Spec offen; der Skill erwägt es bei sensiblen Daten und fragt nach.
