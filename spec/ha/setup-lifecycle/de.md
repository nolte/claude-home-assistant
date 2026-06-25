# HA-Integration: Setup-Lifecycle

Status: draft

## Kontext

Jede Custom Integration mit Config-Entry-Unterstützung durchläuft einen festen Lifecycle: Home Assistant ruft beim Start (und beim Anlegen eines neuen Entries zur Laufzeit) `async_setup_entry(hass, entry)` auf, leitet das Setup an Plattformen weiter, und ruft beim Entfernen oder Reload `async_unload_entry(hass, entry)` auf. Der Lifecycle kennt explizite Zustände — `not loaded`, `setup in progress`, `loaded`, `setup error`, `setup retry`, `unload in progress`, `failed unload` —, die HA aus dem Rückgabewert bzw. den geraisten Exceptions dieser Funktionen ableitet.

Der Lifecycle entscheidet darüber, ob eine Integration robust mit temporären Ausfällen, abgelaufenen Credentials und Reloads umgeht oder ob sie HA-Neustarts erzwingt und Ressourcen leakt. HA stellt dafür drei distinkte Setup-Fehler-Exceptions bereit (`ConfigEntryNotReady`, `ConfigEntryAuthFailed`, `ConfigEntryError`), ein Teardown-Protokoll (`async_unload_platforms` + `async_on_unload`-Callbacks) und das `PARALLEL_UPDATES`-Modul-Konstrukt zur Last-Begrenzung. Diese Spec überführt die HA-Lifecycle-Dokumentation und die einschlägigen Quality-Scale-Regeln in eine verbindliche Konvention für jede Integration, die Skills aus diesem Plugin scaffolden.

Die Coordinator-internen Update-Fehler (`UpdateFailed`, periodisches Error-Mapping) sind in `ha/coordinator-patterns` geregelt und werden hier bewusst nicht dupliziert; diese Spec deckt ausschließlich den Entry-Lifecycle ab.

Quality-Scale-Marker: **Bronze** (`test-before-setup`), **Silver** (`config-entry-unloading`, `parallel-updates`).

## Ziele

- Den Config-Entry-Setup-Einstieg (`async_setup_entry`) als verbindlichen Vertrag festschreiben: Plattform-Forwarding über `async_forward_entry_setups`, Rückgabe von `True` bei Erfolg
- Die drei Setup-Fehler-Exceptions klar voneinander abgrenzen: `ConfigEntryNotReady` (temporärer Fehler → Retry mit Backoff), `ConfigEntryAuthFailed` (→ Reauth), `ConfigEntryError` (permanenter Fehler, kein Retry)
- Vollständiges Teardown in `async_unload_entry` erzwingen: Plattformen entladen, Listener abmelden, Verbindungen schließen — kein Reststand in `hass.data` oder bei Listenern
- `entry.async_on_unload(...)` als Standard-Mechanismus für Cleanup-Callbacks etablieren
- `PARALLEL_UPDATES` in jedem Plattform-Modul explizit setzen, gemäß der Coordinator-/Nicht-Coordinator-Unterscheidung der Regel
- Reload über `async_reload` (statt manuellem Unload + Setup) als Standardpfad bei Options-Änderungen vorgeben

## Nicht-Ziele

- Coordinator-internes Error-Mapping periodischer Updates (`UpdateFailed`) — geregelt in `ha/coordinator-patterns`
- Der Config-Flow selbst inkl. `async_step_reauth`-Implementierung — geregelt in `ha/config-flow-patterns`; diese Spec verlangt nur, dass `ConfigEntryAuthFailed` korrekt geraised wird
- `async_setup_platform` / YAML-basiertes Setup und `PlatformNotReady` — Legacy-Pfad; diese Spec deckt ausschließlich Config-Entry-basiertes Setup ab
- Config-Entry-Migration (`async_migrate_entry`) und Entry-Removal (`async_remove_entry`) — eigene Folge-Spec, sobald konkret nötig
- Die Struktur von `runtime_data` selbst — geregelt in `ha/runtime-data-pattern`; diese Spec verlangt nur die korrekte Zuweisung und das Teardown

## Anforderungen

### Setup-Einstieg (`async_setup_entry`)

- **MUSS [MUST]** `async_setup_entry(hass, entry)` in `__init__.py` definieren und bei erfolgreichem Setup `True` zurückgeben
- **MUSS [MUST]** den API-Client / das Device während des Setups initialisieren und das Ergebnis `entry.runtime_data` zuweisen, **bevor** Plattformen geforwarded werden (siehe `ha/runtime-data-pattern`)
- **MUSS [MUST]** bei Verwendung eines `DataUpdateCoordinator` das erste Refresh über `await coordinator.async_config_entry_first_refresh()` ausführen — dieser Aufruf raised die korrekten Setup-Exceptions automatisch (siehe `ha/coordinator-patterns`)
- **MUSS NICHT [MUST NOT]** im Erfolgsfall einen anderen Wert als `True` zurückgeben — ein falscher Rückgabewert versetzt den Entry in `setup error`, statt ihn als `loaded` zu markieren

### Setup-Fehler & Retry (`ConfigEntryNotReady`/`AuthFailed`/`Error`)

- **MUSS [MUST]** bei temporären Fehlern (Device offline, Netzwerk-Timeout, Service nicht erreichbar) `homeassistant.exceptions.ConfigEntryNotReady` aus `async_setup_entry` raisen — HA versetzt den Entry dann in `setup retry` und wiederholt das Setup automatisch mit wachsendem Backoff (`test-before-setup`-Regel)
- **MUSS [MUST]** bei abgelaufenen oder ungültigen Credentials (falsches Passwort, ungültiger API-Key, abgelaufenes Token) `homeassistant.exceptions.ConfigEntryAuthFailed` raisen — HA versetzt den Entry in einen Fehlerzustand und startet den Reauth-Flow (siehe `ha/config-flow-patterns`)
- **MUSS [MUST]** bei permanenten Fehlern, bei denen ein Funktionieren auf absehbare Zeit nicht zu erwarten ist (z. B. geschlossener Account), `homeassistant.exceptions.ConfigEntryError` raisen — HA wiederholt das Setup dann **nicht**
- **MUSS [MUST]** die Setup-Exceptions ausschließlich aus `async_setup_entry` in `__init__.py` (oder aus dem `DataUpdateCoordinator`) raisen — aus dem `async_setup_entry` einer Plattform geraised, ist `ConfigEntryNotReady` wirkungslos, weil es zu spät kommt, um vom Config-Entry-Setup gefangen zu werden
- **MUSS [MUST]** die Ursprungs-Exception als Cause behalten (`raise ConfigEntryNotReady("...") from ex`) — HA extrahiert daraus die Fehlermeldung für UI und Log
- **SOLLTE [SHOULD]** der Setup-Exception eine Fehlermeldung als erstes Argument mitgeben — HA loggt `ConfigEntryNotReady` auf `debug`-Level und zeigt die Meldung auf der Integrations-Seite an
- **MUSS NICHT [MUST NOT]** eigene Nicht-Debug-Log-Meldungen über den Retry erzeugen — die in `ConfigEntryNotReady` eingebaute Logik verhindert Log-Spam und ist die maßgebliche Stelle dafür

### Plattform-Forwarding

- **MUSS [MUST]** das Setup über `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)` an alle Plattformen weiterleiten, wobei `PLATFORMS` die in `const.py` deklarierte Liste der unterstützten Plattform-Domains ist
- **MUSS [MUST]** das Forwarding erst aufrufen, nachdem `entry.runtime_data` zugewiesen wurde — die Plattform-Setups lesen `runtime_data`, um ihre Entitäten zu erzeugen
- **MUSS [MUST]** in jedem Plattform-Modul eine `async_setup_entry(hass, config_entry, async_add_entities)`-Funktion bereitstellen, damit die Plattform Config-Entries überhaupt unterstützt

### Unload & Cleanup (`async_unload_entry`)

- **MUSS [MUST]** `async_unload_entry(hass, entry)` implementieren — `entry.async_on_unload` allein genügt nicht; die Funktion ist Pflicht für Unload-Unterstützung (`config-entry-unloading`-Regel)
- **MUSS [MUST]** für jede geforwardete Plattform das Entladen über `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` weiterleiten und dessen Ergebnis als Rückgabewert von `async_unload_entry` zurückgeben
- **MUSS [MUST]** beim Entladen alle während des Setups erzeugten Ressourcen aufräumen: Event-Listener abmelden, Sessions / Verbindungen schließen, registrierte Callbacks lösen — gemäß `config-entry-unloading` darf nach dem Unload kein Reststand zurückbleiben
- **MUSS NICHT [MUST NOT]** Reststand in `hass.data` oder bei Listenern hinterlassen — ein leakender Listener führt nach wiederholtem Reload zu Memory-Leaks
- **SOLLTE [SHOULD]** Cleanup-Schritte, die nur bei erfolgreichem Plattform-Unload laufen dürfen, an das Ergebnis von `async_unload_platforms` koppeln (`if unload_ok: ...`), und genau dieses `unload_ok` zurückgeben

### `entry.async_on_unload`

- **SOLLTE [SHOULD]** Cleanup-Callbacks über `entry.async_on_unload(<callback>)` registrieren, statt die Removal-Methoden selbst zu verwalten — HA ruft die registrierten Callbacks automatisch auf
- **MUSS [MUST]** sich darauf einstellen, dass `async_on_unload`-Callbacks in zwei Fällen laufen: wenn `async_setup_entry` `ConfigEntryError`, `ConfigEntryAuthFailed` oder `ConfigEntryNotReady` raised, **und** wenn `async_unload_entry` erfolgreich `True` zurückgibt
- **KANN [MAY]** State-Change-Subscriptions über `entry.async_on_unload(entry.async_on_state_change(<callback>))` an den Entry-Lifecycle binden, sodass sie beim Unload automatisch gelöst werden

### `PARALLEL_UPDATES`

- **MUSS [MUST]** in jedem Plattform-Modul das Modul-Konstrukt `PARALLEL_UPDATES` explizit setzen — das gilt laut Regel als Good Practice und begrenzt die Zahl gleichzeitiger Entity-Updates und Action-Calls
- **MUSS [MUST]** bei Coordinator-basierten read-only-Plattformen (`binary_sensor`, `sensor`, `device_tracker`, `event`) `PARALLEL_UPDATES = 0` setzen — laut Regel zentralisiert der Coordinator die Daten-Updates bereits, sodass nur noch Action-Calls für eine Begrenzung relevant wären
- **MUSS [MUST]** ohne Coordinator (oder für Plattformen mit Action-Calls) `PARALLEL_UPDATES` auf eine positive Ganzzahl setzen — `PARALLEL_UPDATES = 1` aktualisiert die Entitäten einer Plattform nacheinander (laut Regel: „if there are more entities on the sensor platform, they will be updated one by one")
- **SOLLTE [SHOULD]** den Wert daran ausrichten, wie viele gleichzeitige Requests das Device oder der Service verträgt — manche Devices „don't like receiving a lot of requests at the same time"

### Reload

- **SOLLTE [SHOULD]** den Entry-Reload über `await hass.config_entries.async_reload(entry.entry_id)` auslösen, statt manuell Unload und Setup zu verketten — `async_reload` durchläuft den vollständigen Unload-/Setup-Lifecycle inklusive Zustandsübergänge
- **SOLLTE [SHOULD]** einen Reload bei Options-Änderungen registrieren (typisch über einen Update-Listener, der per `entry.async_on_unload` an den Lifecycle gebunden ist), damit geänderte Intervalle / Optionen wirksam werden (siehe `ha/coordinator-patterns`, `ha/config-flow-patterns`)
- **MUSS NICHT [MUST NOT]** den `ConfigEntry` (Daten oder Optionen) direkt mutieren — Änderungen laufen ausschließlich über `hass.config_entries.async_update_entry`

## Akzeptanzkriterien

- [ ] `async_setup_entry` ist in `__init__.py` definiert und gibt im Erfolgsfall `True` zurück
- [ ] `entry.runtime_data` wird zugewiesen, bevor Plattformen geforwarded werden
- [ ] Plattformen werden über `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)` geforwarded
- [ ] Temporäre Setup-Fehler raisen `ConfigEntryNotReady`; abgelaufene Credentials raisen `ConfigEntryAuthFailed`; permanente Fehler raisen `ConfigEntryError`
- [ ] Setup-Exceptions werden mit `from ex` chained und tragen eine Fehlermeldung als erstes Argument
- [ ] `async_unload_entry` ist implementiert und gibt das Ergebnis von `async_unload_platforms(entry, PLATFORMS)` zurück
- [ ] `async_unload_entry` meldet alle Listener ab und schließt alle im Setup geöffneten Verbindungen — kein Reststand in `hass.data` oder bei Listenern
- [ ] Cleanup-Callbacks sind über `entry.async_on_unload(...)` registriert
- [ ] Jedes Plattform-Modul setzt `PARALLEL_UPDATES` explizit: `0` für Coordinator-basierte read-only-Plattformen, sonst eine positive Ganzzahl
- [ ] Reloads laufen über `async_reload(entry.entry_id)`, nicht über manuelles Unload + Setup
- [ ] Quality-Scale-Marker für diesen Lifecycle sind gesetzt: **Bronze** (`test-before-setup`), **Silver** (`config-entry-unloading`, `parallel-updates`)

## Offene Fragen

- **`ConfigEntryError`-vs.-`ConfigEntryNotReady`-Heuristik**: Wann gilt ein Fehler als „permanent" genug für `ConfigEntryError` statt für einen Retry über `ConfigEntryNotReady`? Die HA-Doku nennt nur Beispiele (geschlossener Account); eine trennscharfe Klassifikation der API-Fehler-Klassen fehlt.
- **`PARALLEL_UPDATES` für gemischte Plattformen**: Wie wird der Wert für eine Plattform gesetzt, die zugleich read-only-Entitäten und Action-Calls bereitstellt (z. B. `switch` mit Coordinator)? Die Regel adressiert read-only-Plattformen und Action-Calls getrennt; der Mischfall ist nicht spezifiziert.
- **Migration & Removal**: Diese Spec klammert `async_migrate_entry` und `async_remove_entry` aus. Ab welcher Komplexität rechtfertigt sich eine eigene `ha/entry-migration`-Spec?
- **Reload-Debounce**: Wenn mehrere Options-Änderungen schnell hintereinander erfolgen, kann jeder Change einen Reload auslösen. Soll die Spec ein Debounce des Reload-Listeners verlangen?
- **Teardown-Verifikation in Tests**: Soll die Spec einen expliziten Test verlangen, der nach `async_unload_entry` prüft, dass keine Listener / `hass.data`-Einträge übrig sind (siehe `ha/test-harness`)?
