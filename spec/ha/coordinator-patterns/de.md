# HA-Integration: Coordinator-Patterns

Status: draft

## Kontext

`homeassistant.helpers.update_coordinator.DataUpdateCoordinator` ist HAs etabliertes Pattern, um asynchrones Polling eines API-Endpunkts oder Devices in einer geteilten Update-Schleife zu bündeln. Eine Custom Integration mit nicht-trivialer Datenmenge braucht typischerweise nicht einen einzigen Mega-Coordinator, der bei jedem Tick alles pollt, sondern eine **Multi-Coordinator-Topologie**: pro logischem Datensatz ein Coordinator mit eigenem Update-Intervall, sodass schnelle Daten (Alerts, Status) nicht hinter langsamen Daten (Inventar, Stammdaten) hängen.

`nolte/kamerplanter-ha` validiert dieses Muster mit fünf Coordinators (Plants, Locations, Runs, Alerts, Tasks) — vier mit `300 s` Default und `120 s`-Mindestintervall, einer (Alerts) mit `60 s` Default und `30 s`-Mindestintervall — und mappt API-Auth-Fehler konsequent auf `ConfigEntryAuthFailed`, Verbindungsfehler auf `UpdateFailed`. Diese Spec überführt diese Konvention in eine generische Verpflichtung für jede Custom Integration, die Skills aus diesem Plugin scaffolden.

Quality-Scale-Marker: **Silver** (`DataUpdateCoordinator`-Verwendung mit korrektem Error-Mapping ist eine Silver-Pflicht laut HA-Quality-Scale; die Multi-Coordinator-Topologie ist kein eigenes Quality-Scale-Kriterium, hebt den Wert des Patterns aber praktisch über reine Silver-Konformität hinaus).

## Ziele

- Multi-Coordinator-Topologie als verbindlichen Stil für Integrationen mit unterschiedlichen Update-Frequenzen festschreiben
- Korrektes Error-Mapping erzwingen: API-Auth-Fehler → `ConfigEntryAuthFailed` (triggert Reauth-Flow); Verbindungsfehler → `UpdateFailed` (markiert Entitäten als `unavailable`, bricht aber den Entry nicht)
- Konfigurierbare Polling-Intervalle pro Coordinator als Standard, mit erzwungenem Mindest-Cap, der Server-DDoS durch Fehlkonfiguration verhindert
- `always_update=False` als Default — Entitäten triggern Updates nur bei tatsächlicher Änderung
- Einmaliges Stammdaten-Setup über `_async_setup()` getrennt vom periodischen Update
- Per-Coordinator-Timeout (`async_timeout.timeout(...)`), damit ein hängender API-Call nicht den gesamten Entry blockiert

## Nicht-Ziele

- Push-basierte Updates (WebSocket, MQTT, HTTP-Webhook auf HA) — eigene Folge-Spec, sobald sie konkret nötig wird
- Coordinator-übergreifende Daten-Aggregation (Cross-Coordinator-Lookups) — derzeit als ad-hoc Helper-Functions in den jeweiligen Plattform-Modulen gelöst; eigene Spec, falls ein robustes Pattern entsteht
- Persistente Caches der Coordinator-Daten zwischen HA-Neustarts — `homeassistant.helpers.storage` ist die richtige Stelle dafür
- Throttling / Rate-Limiting jenseits der Update-Intervalle — fällt in die `ha/security-hardening`-Spec, die das API-Client-Verhalten definiert

## Anforderungen

### Coordinator-Topologie

- **MUSS [MUST]** pro logischem Datensatz einen eigenen Coordinator definieren statt einen einzigen Mega-Coordinator, der bei jedem Tick alles pollt
- **MUSS [MUST]** alle Coordinators in `RuntimeData` unter benannten String-Schlüsseln führen (siehe `ha/runtime-data-pattern`); jeder Schlüssel matched die fachliche Rolle (`"plants"`, `"alerts"`, …)
- **SOLLTE [SHOULD]** Update-Intervalle pro Coordinator über den Options-Flow konfigurierbar machen (siehe `ha/config-flow-patterns`); die Konfiguration triggert einen Entry-Reload, der die Coordinators mit den neuen Intervallen neu erzeugt
- **KANN [MAY]** für eng gekoppelte Endpunkte einen Coordinator führen, der mehrere API-Aufrufe parallel ausführt (z. B. ein Coordinator, der pro Tick zwei Endpunkte pollt, weil deren Daten in den Plattformen nur gemeinsam Sinn ergeben), solange das in der Coordinator-`name`-Property dokumentiert ist
- **MUSS NICHT [MUST NOT]** denselben fachlichen Datensatz auf mehrere Coordinators aufteilen — pro Datensatz genau ein Coordinator

### Coordinator-Definition

- **MUSS [MUST]** `DataUpdateCoordinator` (oder `TimestampDataUpdateCoordinator`, wenn angemessen) als Basisklasse verwenden
- **MUSS [MUST]** den Datentyp generisch annotieren: `class <Domain><Role>Coordinator(DataUpdateCoordinator[<DataType>])` — `<DataType>` ist der konkrete Typ, den `_async_update_data` zurückgibt
- **MUSS [MUST]** `config_entry=entry` an `super().__init__()` übergeben — HA verlangt diesen Parameter für die ConfigEntry-Lifecycle-Bindung
- **MUSS [MUST]** `name=f"{DOMAIN}_<role>"` setzen — der Name erscheint in HA-Logs und unterscheidet die Coordinators eines Entries
- **MUSS [MUST]** `update_interval=timedelta(seconds=<interval>)` setzen, wobei `<interval>` aus `entry.options` (mit Default und Mindest-Cap, siehe nächster Abschnitt) abgeleitet ist
- **SOLLTE [SHOULD]** `always_update=False` setzen — die Coordinator-Listener (also alle Entitäten) triggern dann ihr `_handle_coordinator_update` nur, wenn sich die Daten gegenüber dem letzten Tick ändern; das spart pro Tick und Entität einen unnötigen Re-Render
- **KANN [MAY]** `update_method=<async-callable>` als Alternative zu einem überschriebenen `_async_update_data` angeben — beide Wege sind gleichwertig

### Default- und Mindest-Intervalle

- **MUSS [MUST]** Default- und Mindest-Intervalle in `const.py` definieren — typisch als `DEFAULT_POLL_<ROLE>` und `MIN_POLL_<ROLE>` in Sekunden
- **MUSS [MUST]** den Mindest-Cap im Coordinator-Constructor erzwingen (`max(MIN_POLL_<ROLE>, entry.options.get(CONF_POLL_<ROLE>, DEFAULT_POLL_<ROLE>))`); fehlerhafte oder bösartige Options-Werte dürfen die API niemals mit Sub-Sekunden-Polling überfluten
- **SOLLTE [SHOULD]** für Coordinators mit deutlich kürzerem Intervall (z. B. Alerts mit `60 s`) die Last-Implikation in der Spec-Doku oder im Code-Kommentar sichtbar machen, damit das Intervall nicht versehentlich auf andere Coordinators kopiert wird

### Stammdaten-Setup

- **KANN [MAY]** `_async_setup()` als async-Methode ohne Parameter überschreiben, um Stammdaten einmalig beim ersten Refresh zu laden (z. B. eine Lookup-Tabelle für Fremdschlüssel-Resolution)
- **MUSS [MUST]** `_async_setup()` so implementieren, dass es bei wiederholtem Aufruf idempotent bleibt — HA garantiert zwar Einmaligkeit innerhalb eines Entry-Lifecycles, ein Re-Setup nach Reload ist aber zu erwarten
- **KANN [MAY]** Lookup-Caches als Instanz-Attribute auf dem Coordinator speichern (z. B. `self._fertilizer_lookup`); diese werden in `_async_update_data` zur Daten-Anreicherung verwendet
- **MUSS NICHT [MUST NOT]** Stammdaten in jeder `_async_update_data`-Iteration neu laden, wenn sie nicht aktualisierbar sind — das verschiebt langsame I/O in den Polling-Pfad

### Update-Methode

- **MUSS [MUST]** `_async_update_data()` als async-Methode ohne Parameter überschreiben (oder ein equivalentes `update_method` angeben)
- **MUSS [MUST]** den API-Aufruf mit einem expliziten Timeout absichern (`async with async_timeout.timeout(<seconds>): ...`) — typischer Wert: `30 s`; der Timeout darf das Update-Intervall nicht überschreiten
- **MUSS [MUST]** generische Exception-Catches vermeiden — nur die API-spezifischen Exception-Klassen abfangen und auf HA-Exceptions mappen (siehe nächster Abschnitt); jeder andere Fehler propagiert nach oben
- **MUSS NICHT [MUST NOT]** den Datentyp zwischen Iterationen wechseln — der Generic-Parameter ist eine Vertrags­erklärung gegenüber Plattformen

### Error-Mapping

- **MUSS [MUST]** API-spezifische Auth-Exceptions (HTTP 401 / 403, abgelaufenes Token, ungültiger API-Key) auf `homeassistant.exceptions.ConfigEntryAuthFailed` mappen — HA triggert daraufhin den `async_step_reauth`-Flow (siehe `ha/config-flow-patterns`)
- **MUSS [MUST]** API-spezifische Verbindungsfehler (Netzwerk-Timeout, HTTP 5xx, DNS-Fehler) auf `homeassistant.helpers.update_coordinator.UpdateFailed` mappen — HA markiert die assoziierten Entitäten dann als `unavailable`, behält aber den Entry am Leben
- **MUSS [MUST]** die ursprüngliche Exception als Cause behalten: `raise ConfigEntryAuthFailed(str(err)) from err` bzw. `raise UpdateFailed(str(err)) from err` — sonst geht der Stack-Trace im HA-Log verloren
- **KANN [MAY]** spezifischere HA-Exceptions verwenden, wenn die Situation es erfordert (z. B. `ConfigEntryNotReady`, wenn das initiale Setup an einer Verbindungsstörung scheitert) — der Coordinator-Constructor kann dafür ein eigenes Try/Except außerhalb von `_async_update_data` führen

### Enrichment-Fehler

- **KANN [MAY]** in `_async_update_data` per-Item-Anreicherung durchführen (z. B. Lookup-Resolution für Fremdschlüssel)
- **MUSS [MUST]** bei einem einzelnen Anreicherungs-Fehler den gesamten Update nicht abbrechen; der betroffene Eintrag wird mit dem Original-Wert (oder `None`) belassen, der Fehler geloggt
- **SOLLTE [SHOULD]** Anreicherungs-Fehler in Diagnostik sichtbar machen (siehe `ha/diagnostics`), damit sie ohne Log-Tail-Sucherei auffallen
- **MUSS NICHT [MUST NOT]** Anreicherungs-Fehler still verschlucken — jeder geloggte Fehler enthält genug Kontext (`entry_id`, Coordinator-Rolle, betroffener Eintrags-Schlüssel), um ihn lokalisierbar zu machen

### Erstes Refresh

- **MUSS [MUST]** für jeden Coordinator `await coordinator.async_config_entry_first_refresh()` in `async_setup_entry` aufrufen, **bevor** `entry.runtime_data` zugewiesen wird (siehe `ha/runtime-data-pattern`)
- **MUSS [MUST]** das erste Refresh sequentiell oder mit `asyncio.gather(...)` parallelisieren, je nach API-Verträglichkeit; `gather` ist erlaubt, wenn das Backend mehrere parallele Calls verträgt
- **MUSS NICHT [MUST NOT]** `coordinator.async_refresh()` direkt im Setup aufrufen — `async_config_entry_first_refresh` enthält die korrekte Fehlerbehandlung für das Setup-Stadium

## Akzeptanzkriterien

- [ ] Pro logischem Datensatz existiert genau ein Coordinator; kein Mega-Coordinator
- [ ] Alle Coordinators sind in `RuntimeData` unter benannten Schlüsseln referenziert
- [ ] Jede Coordinator-Klasse erbt von `DataUpdateCoordinator[<DataType>]` mit explizitem Generic-Parameter
- [ ] `super().__init__(...)` enthält `config_entry`, `name`, `update_interval`, `always_update=False`
- [ ] Default- und Mindest-Intervalle existieren in `const.py` als `DEFAULT_POLL_<ROLE>` und `MIN_POLL_<ROLE>`
- [ ] Der Mindest-Cap wird im Constructor mit `max(min, requested)` durchgesetzt
- [ ] `_async_update_data` ist mit `async with async_timeout.timeout(<seconds>)` umschlossen
- [ ] `_async_update_data` raised `ConfigEntryAuthFailed` für Auth-Fehler und `UpdateFailed` für Verbindungsfehler — beide mit `from err` chained
- [ ] `_async_update_data` enthält keinen generischen `except Exception:`-Catch
- [ ] `async_setup_entry` ruft `async_config_entry_first_refresh()` für jeden Coordinator vor `runtime_data` auf
- [ ] Quality-Scale-Marker für dieses Pattern ist gesetzt: **Silver**

## Offene Fragen

- **Coordinator-Konsolidierungs-Heuristik**: Wann ist ein Multi-Coordinator besser als ein Mega-Coordinator? Aktuell wird der Multi-Coordinator-Stil verlangt, sobald mehrere logische Datensätze existieren — eine messbare Heuristik (Anzahl Endpunkte, Datenvolumen, Update-Frequenz-Spread) fehlt.
- **Push-Coordinator**: Wie behandelt die Spec push-basierte Updates (Webhook, MQTT, WebSocket)? Eigene `ha/coordinator-push`-Spec, sobald die erste push-fähige Integration auftaucht.
- **Initial-Refresh-Spread**: Wenn alle Coordinators eines Entries gleichzeitig ihr erstes Refresh starten, kann das Backend serialisieren oder rate-limiten. Soll die Spec ein gestaffelt­es Initial-Refresh (z. B. mit kleinen `asyncio.sleep`-Versätzen) verlangen?
- **Per-Rolle-Timeout**: Sollte der `async_timeout.timeout(...)` pro Coordinator-Rolle konfigurierbar sein (z. B. längerer Timeout für Stammdaten-Coordinators), oder reicht der globale Default `30 s`?
- **`TimestampDataUpdateCoordinator`-Schwelle**: Wann verlangt die Spec den `Timestamp`-Variant statt der Basis-Klasse? `kamerplanter-ha` verwendet die Basis; ein konkreter Use-Case für die Timestamp-Variante ist im Repo noch nicht aufgetaucht.
