# HA-Integration: Frontend-Data-API (`hass`-Objekt)

Status: draft

## Kontext

Das HA-Frontend reicht ein einziges `hass`-Objekt durch alle Frontend-Erweiterungen. Dieses Objekt trägt den aktuellen State aller Entities, erlaubt Kommandos zurück an den Server und liefert Helper, um Entity-State lokalisiert und einheitenkorrekt zu formatieren. Custom Cards, Custom Panels, Dialoge und Selektoren konsumieren alle dieselbe Daten-Oberfläche — diese Spec kodifiziert genau diese Oberfläche.

Wann immer sich ein State ändert, erzeugt HA eine neue Version der geänderten Objekte. Eine strikte Gleichheitsprüfung (`const changed = newVal !== oldVal;`) genügt damit, um Änderungen zu erkennen — der Grund, warum Entity-Change-Detection im Frontend überhaupt funktioniert. Die empfohlene Art, an Daten zu kommen, ist das Konsumieren der verfügbaren Contexts; `hass.states` und Direktzugriffe bleiben für einfache Cards die pragmatische Variante.

`hass`-Direktzugriff über die Browser-Devtools (`$0.hass` auf dem `<home-assistant>`-Element) ist ausschließlich Referenz-Hilfe zum Inspizieren — im produktiven Code muss `hass` korrekt an die Erweiterung durchgereicht werden. Diese Spec grenzt sich vom Card-Lifecycle ab: `ha/lovelace-card-patterns` deckt den `set hass`-Setter und das Re-Render-Verhalten ab; hier geht es um die Daten- und Methoden-Oberfläche des `hass`-Objekts selbst, die jede Frontend-Erweiterung konsumiert.

Quality-Scale-Marker: **Kein** Bestandteil der HA-Quality-Scale — die Frontend-Daten-Oberfläche ist eine Frontend-Liefer-Achse und steht außerhalb der Integration-Skala.

## Ziele

- Context-Konsum als empfohlenen Standard-Weg festschreiben, um an Frontend-Daten zu kommen (`states`, `entities`, `extendedEntities`, `connection`, `user`)
- Das `@consume({ context, subscribe: true })`-Pattern als Lit-Default für initiale Daten plus abonnierte Updates etablieren
- `hass.callService(domain, service, data)` als Standard-Weg für Backend-Service-Aufrufe festschreiben
- `hass.callWS(message)` als empfohlenen modernen Pfad für WebSocket-Kommandos etablieren — weg von `callApi`
- Entity-State-Formatierung über die `formatEntity*`-Helper verpflichten, statt rohe State-Strings anzuzeigen
- Die Abgrenzung zum Card-Lifecycle (`ha/lovelace-card-patterns`) sauber halten

## Nicht-Ziele

- Der Card-Lifecycle und der `set hass`-Setter — abgedeckt in `ha/lovelace-card-patterns`
- Das visuelle Card-Editor-UI und die Selektor-Form — abgedeckt in `ha/lovelace-card-editor`
- Die Backend-Seite eigener WebSocket-Kommandos — abgedeckt in `ha/frontend-websocket-commands`
- Die Integration-Seite von `callService` (Service-Registrierung, Schema) — abgedeckt in `ha/services`
- Eigene lokale Contexts definieren und als Provider auftreten — hier nur als KANN-Erwähnung, kein Detail-Pattern

## Anforderungen

### Contexts konsumieren (`states`/`entities`/`connection`/`user`)

- **MUSS [MUST]** Frontend-Daten primär über die verfügbaren Contexts konsumieren — der `states`-Context (States aller Entities) ist der häufigste
- **SOLLTE [SHOULD]** `entities` bzw. `extendedEntities` konsumieren, wenn die Erweiterung Entity-Registry-Daten braucht, statt diese aus `states` zu rekonstruieren
- **SOLLTE [SHOULD]** `connection` konsumieren, um an das HA-Connection-Objekt zu kommen, und `user` für den eingeloggten User
- **KANN [MAY]** eigene lokale Contexts erstellen, um Daten innerhalb der eigenen Komponenten-Hierarchie weiterzureichen

### `@consume`-Pattern & Subscriptions

- **MUSS [MUST]** in Lit-Komponenten einen Context über `@consume({ context: <ctx>, subscribe: true })` konsumieren, wenn die Erweiterung auf Daten-Updates reagieren muss
- **MUSS [MUST]** zum Registrieren am Context-Provider ein Custom-Event mit Callback feuern — der Provider liefert daraufhin initiale Daten
- **SOLLTE [SHOULD]** `subscribe: true` setzen, damit der Provider bei jeder Daten-Änderung auch Updates schickt — ohne Subscription bleibt es bei den initialen Daten
- **MUSS NICHT [MUST NOT]** Context-Daten als statischen Snapshot behandeln, wenn `subscribe: true` aktiv ist — die Komponente erhält fortlaufend neue Werte

### Service-Aufrufe (`callService`)

- **MUSS [MUST]** Backend-Service-Aktionen über `hass.callService(domain, service, data)` aufrufen (z. B. `hass.callService('light', 'turn_on', { entity_id: 'light.kitchen' })`)
- **MUSS [MUST]** das von `callService` zurückgegebene `Promise` behandeln — alle mit `call` beginnenden Methoden sind async und resolven mit dem Ergebnis
- **MUSS NICHT [MUST NOT]** State serverseitig über rohe API-Pfade mutieren, wenn ein registrierter Service existiert — `callService` ist der kanonische Mutations-Weg

### WebSocket (`callWS`) & Legacy (`callApi`)

- **SOLLTE [SHOULD]** WebSocket-Kommandos über `hass.callWS(message)` aufrufen (z. B. `hass.callWS({ type: 'config/auth/create', name: 'Paulus' })`) — der empfohlene moderne Pfad
- **MUSS NICHT [MUST NOT]** `hass.callApi(method, path, data)` als Default für neue Erweiterungen verwenden — HA migriert weg von API-Calls hin zu `callWS(message)`
- **KANN [MAY]** `hass.callApi('get', 'hassio/backups')` nur dann nutzen, wenn noch kein WebSocket-Äquivalent existiert (Legacy-Fallback)
- **MUSS [MUST]** das `Promise` von `callWS` bzw. `callApi` behandeln — beide sind async

### Entity-State-Formatierung (`formatEntity*`)

- **MUSS [MUST]** den anzuzeigenden Entity-State über `hass.formatEntityState(stateObj, state)` formatieren, statt den rohen `state`-String darzustellen — der Wert wird über die User-Profil-Einstellungen (Sprache, Zahlen-/Datumsformat, Zeitzone) und die Maßeinheit lokalisiert
- **MUSS [MUST]** Attribut-Werte über `hass.formatEntityAttributeValue(stateObj, attribute, value)` formatieren (z. B. `"20.5 °C"`), statt rohe Attribut-Werte anzuzeigen
- **SOLLTE [SHOULD]** Attribut-Namen über `hass.formatEntityAttributeName(stateObj, attribute)` lokalisieren (z. B. `"Current temperature"`)
- **SOLLTE [SHOULD]** Anzeige-Namen über `hass.formatEntityName(stateObj, name, options)` aus dem Registry-Context (Entity, Device, Area, Floor) bilden — derselbe Helper, den die Built-in-Cards nutzen; `undefined` fällt auf den Friendly-Name zurück, ein String wird als User-Override unverändert übernommen

## Akzeptanzkriterien

- [ ] Daten werden primär über Contexts konsumiert (`states`/`entities`/`extendedEntities`/`connection`/`user`)
- [ ] Lit-Komponenten konsumieren Contexts via `@consume({ context, subscribe: true })`
- [ ] Bei Bedarf an Updates ist `subscribe: true` gesetzt; ein Custom-Event registriert am Provider
- [ ] Backend-Service-Aktionen laufen über `hass.callService(domain, service, data)`
- [ ] WebSocket-Kommandos laufen über `hass.callWS(message)`; `callApi` nur als Legacy-Fallback
- [ ] Jeder `call*`-Aufruf behandelt das zurückgegebene `Promise`
- [ ] Entity-State wird via `hass.formatEntityState` formatiert, nicht roh dargestellt
- [ ] Attribut-Werte und -Namen werden via `formatEntityAttributeValue` / `formatEntityAttributeName` formatiert
- [ ] Anzeige-Namen werden via `hass.formatEntityName` aus dem Registry-Context gebildet
- [ ] Quality-Scale-Marker: **Kein** Bestandteil der HA-Quality-Scale (Frontend-Oberfläche)

## Offene Fragen

- **Context vs. Direktzugriff**: Wann ist `hass.states[id]`-Direktzugriff für eine simple Card noch ok, und ab wann muss auf Context-Konsum umgestellt werden? Aktuell pragmatisch gemischt.
- **`formatEntityName`-Verfügbarkeit**: Der Helper ist erst ab HA 2026.4 verfügbar. Wie wird eine Mindest-HA-Version pro Erweiterung deklariert und gegen fehlenden Helper abgesichert?
- **Eigene WebSocket-Kommandos**: Die Backend-Seite eigener WS-Kommandos liegt in `ha/frontend-websocket-commands` — wie sauber ist die Schnittstelle zwischen `callWS`-Konsum (hier) und der Kommando-Registrierung (dort) abgegrenzt?
- **`callApi`-Restbestände**: HA migriert weg von `callApi`. Wann existiert für jeden heute noch nötigen API-Pfad ein WebSocket-Äquivalent, sodass `callApi` ganz entfallen kann?
- **Lokale Context-Provider**: Eigene Contexts definieren ist hier nur KANN. Braucht es eine Folge-Spec für das Provider-Pattern, sobald eine Erweiterung Daten über mehrere Komponenten-Ebenen reicht?
