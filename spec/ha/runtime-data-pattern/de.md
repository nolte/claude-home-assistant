# HA-Integration: `runtime_data`-Pattern

Status: draft

## Kontext

Vor Home Assistant 2024.1 war `hass.data[DOMAIN][entry.entry_id]` der etablierte Speicherort, an dem eine Custom Integration ihren API-Client, ihre `DataUpdateCoordinator` und ihre Cleanup-Listener für die Lebenszeit eines `ConfigEntry` ablegte. Dieses Pattern hat drei harte Schwächen: es ist untypisiert (jeder Lookup ist ein dynamisches Dict-Get mit `cast`-Theater), es muss bei `async_unload_entry` manuell mit `pop()` aufgeräumt werden, und Plattform-Module müssen denselben Lookup-Pfad spiegeln, sonst entsteht Drift zwischen Setup und Konsum.

HA 2024.1 hat dafür `entry.runtime_data` eingeführt — einen typisierten Slot direkt am `ConfigEntry`, der über einen generischen Type-Parameter (`ConfigEntry[YourRuntimeData]`) Typ-Sicherheit liefert und beim Entry-Unload automatisch verworfen wird. Die nolte-Konvention (validiert in `nolte/kamerplanter-ha`, dort als _Runtime Data Pattern (PFLICHT)_ kodifiziert) verlangt diesen Slot ausschließlich; jeder Zugriff auf `hass.data[DOMAIN]` für Setup-Artefakte ist verboten. Diese Spec setzt diese Pflicht für alle Skills in `claude-home-assistant`, die Custom Integrations scaffolden, verbindlich.

Quality-Scale-Marker: **Bronze** (typisiertes `runtime_data` ist eine Bronze-Pflicht laut HA-Quality-Scale).

## Ziele

- Typisiertes `runtime_data` als alleinigen Speicherort für Setup-Artefakte (API-Clients, Coordinators, Cleanup-Listener) festschreiben
- Drift zwischen Setup-Speicher und Plattform-Lookup eliminieren — beide sehen denselben typisierten Slot
- Automatischen Cleanup beim Entry-Unload nutzen, statt manuelle `hass.data.pop()`-Logik zu tragen
- Skill-Output sofort Bronze-Quality-Scale-konform machen, ohne nachträglichen Refactoring-Schritt

## Nicht-Ziele

- Multi-Entry-Sharing (ein API-Client für mehrere Entries gegen denselben Server) — eigene Folge-Spec, falls Bedarf entsteht
- Persistente Storage zwischen HA-Neustarts — `runtime_data` ist explizit nicht persistent; das ist die Aufgabe der `homeassistant.helpers.storage`-Helper
- Migration bestehender `hass.data[DOMAIN]`-Integrationen — Skills in diesem Plugin scaffolden Greenfield-Code; eine Migrations-Spec entsteht erst, wenn ein konkreter Kunde danach fragt
- Schema-Migration zwischen Versionen von `entry.data`/`entry.options` — gehört zu `async_migrate_entry`, nicht hierher

## Anforderungen

### `RuntimeData`-Dataclass

- **MUSS [MUST]** pro Integration genau eine `RuntimeData`-Dataclass definieren, typischerweise in `__init__.py` oder einem dedizierten `runtime.py`-Modul
- **MUSS [MUST]** die Klasse mit `@dataclass` dekorieren (nicht `@dataclass(frozen=True)`, weil Listener-Refs nachträglich ergänzt werden können)
- **MUSS [MUST]** alle Setup-Artefakte als getypte Felder enthalten: API-Client, alle `DataUpdateCoordinator`-Instanzen, Cleanup-Callback-Refs, Cache-Strukturen
- **SOLLTE [SHOULD]** Coordinators als typisiertes Mapping (`dict[str, DataUpdateCoordinator[Any]]`) führen, wenn die Integration mehr als einen Coordinator hat — der Schlüssel matched die Coordinator-Rolle (siehe `ha/coordinator-patterns` für die Topologie)
- **KANN [MAY]** weitere Felder ergänzen (z. B. einen pre-resolved Lookup-Cache wie `_fertilizer_lookup` in `nolte/kamerplanter-ha`), solange sie deterministisch aus dem Setup ableitbar sind

### Typed `ConfigEntry`-Alias

- **MUSS [MUST]** einen Type-Alias der Form `type <Domain>ConfigEntry = ConfigEntry[<Domain>RuntimeData]` exportieren — `<Domain>` in PascalCase
- **MUSS [MUST]** diesen Alias in der Signatur jeder Lifecycle-Funktion (`async_setup_entry`, `async_unload_entry`, `async_migrate_entry`) und jeder Plattform-`async_setup_entry`-Funktion verwenden
- **SOLLTE [SHOULD]** den Alias und die `RuntimeData`-Dataclass aus demselben Modul exportieren, damit Plattform-Module einen einzigen Import-Pfad nutzen können

### `async_setup_entry`-Befüllung

- **MUSS [MUST]** `entry.runtime_data` mit der vollständig befüllten `RuntimeData`-Instanz zuweisen, **bevor** `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)` aufgerufen wird — Plattformen lesen `runtime_data` während ihres eigenen Setups
- **MUSS [MUST]** den API-Client und alle Coordinators vor der `runtime_data`-Zuweisung erzeugen
- **SOLLTE [SHOULD]** für jeden Coordinator `await coordinator.async_config_entry_first_refresh()` vor der `runtime_data`-Zuweisung aufrufen, damit Plattformen direkt mit gefüllten Daten starten und Entitäten nicht initial als `unavailable` registriert werden müssen
- **MUSS NICHT [MUST NOT]** `runtime_data` halb befüllen, falls `async_setup_entry` mit einer Exception bricht — entweder die vollständige Zuweisung passiert oder gar keine; partial state ist verboten

### `async_unload_entry`-Bereinigung

- **MUSS NICHT [MUST NOT]** `hass.data[DOMAIN].pop(entry.entry_id, None)`-Logik enthalten — `runtime_data` wird beim Unload automatisch durch HA verworfen
- **SOLLTE [SHOULD]** Cleanup-Callbacks (Listener, Subscription-Cancellations), die nicht über `entry.async_on_unload(...)` registriert sind, vor dem Plattform-Unload ausführen — typischerweise indem die Callback-Refs in `runtime_data` gespeichert und in `async_unload_entry` aufgerufen werden
- **SOLLTE [SHOULD]** für Listener bevorzugt `entry.async_on_unload(callback)` während des Setups verwenden — HA ruft die Callbacks dann automatisch beim Unload auf, ohne dass `RuntimeData` sie tragen muss
- **MUSS [MUST]** `await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` als Rückgabewert von `async_unload_entry` zurückgeben (siehe `ha/integration-architecture`)

### Plattform-Lookup

- **MUSS [MUST]** in jedem Plattform-Modul (`sensor.py`, `binary_sensor.py`, …) `runtime_data` ausschließlich über `entry.runtime_data` lesen, niemals über `hass.data[DOMAIN]`
- **MUSS [MUST]** den `entry`-Parameter der Plattform-`async_setup_entry`-Funktion mit dem Typed-Alias annotieren: `entry: <Domain>ConfigEntry`
- **SOLLTE [SHOULD]** den Coordinator-Lookup über das Mapping (`entry.runtime_data.coordinators["<role>"]`) führen statt über separate Felder pro Coordinator — das hält die `RuntimeData`-Dataclass stabil, wenn sich die Coordinator-Anzahl ändert

### Verbotene Patterns

- **MUSS NICHT [MUST NOT]** `hass.data[DOMAIN][entry.entry_id]` als Speicherort für API-Clients, Coordinators oder Cleanup-Listener verwenden
- **MUSS NICHT [MUST NOT]** `hass.data` als Cache für Setup-Artefakte einer einzelnen Integration verwenden — der einzige akzeptable Grund ist Cross-Integration-Sharing, und dafür gibt es eine separate offene Frage (siehe Open Questions)
- **MUSS NICHT [MUST NOT]** `runtime_data` als Konfig-Speicher missbrauchen — `entry.data` und `entry.options` bleiben die Quellen für Konfiguration; `runtime_data` ist der Quergeleitete Speicher für **abgeleitete** Setup-Artefakte
- **MUSS NICHT [MUST NOT]** `runtime_data` direkt verändern, um Konfigurations-Updates zu spiegeln — Konfig-Updates triggern `async_unload_entry` + `async_setup_entry`-Reload (oder explizit `entry.async_reload()`); inkrementelle In-Place-Mutation ist nicht vorgesehen

## Akzeptanzkriterien

- [ ] Eine `@dataclass` namens `<Domain>RuntimeData` ist im Code exportiert und enthält alle Setup-Artefakte als typisierte Felder
- [ ] Ein Type-Alias `<Domain>ConfigEntry = ConfigEntry[<Domain>RuntimeData]` ist exportiert
- [ ] `async_setup_entry`, `async_unload_entry` und ggf. `async_migrate_entry` verwenden den Typed-Alias in der Signatur
- [ ] `async_setup_entry` setzt `entry.runtime_data` vor `async_forward_entry_setups`
- [ ] `async_setup_entry` ruft `async_config_entry_first_refresh()` für jeden Coordinator vor der `runtime_data`-Zuweisung auf
- [ ] `async_unload_entry` enthält keinen `hass.data.pop()`-Aufruf
- [ ] Jedes Plattform-Modul verwendet `entry.runtime_data` für Coordinator-/API-Lookups; kein Plattform-Modul referenziert `hass.data[DOMAIN]`
- [ ] Eine `grep`-Suche nach `hass.data[DOMAIN]` im `custom_components/<domain>/`-Ordner liefert keine Treffer (Migrations-Pfade ausgenommen)
- [ ] Quality-Scale-Marker für dieses Pattern ist gesetzt: **Bronze**

## Offene Fragen

- **Multi-Entry-Sharing**: Wie behandeln wir den Fall, dass zwei Config-Entries denselben Server / dieselbe Cloud adressieren und sich einen API-Client teilen sollten? `runtime_data` ist Pro-Entry; der Sharing-Mechanismus müsste auf `hass.data` zurückgreifen oder einen externen Singleton einführen. Eigene Spec, sobald der Bedarf konkret ist.
- **Cleanup-Listener-Stil**: `entry.async_on_unload(...)` (HA-managed) vs. Callback-Refs in `RuntimeData` (selbst-verwaltet) — wann verlangt die Spec welchen Stil? Aktuell als SHOULD für `async_on_unload` formuliert; bei Patterns mit komplexer Cleanup-Logik (z. B. WebSocket mit Backoff-Reconnect) kann selbst-verwaltet sinnvoller sein.
- **`RuntimeData`-Mutation**: Ist es zulässig, `runtime_data` zur Laufzeit um neue Felder zu ergänzen (z. B. einen on-demand registrierten Service-Listener)? Aktuell als „nicht direkt verändern" formuliert; ein definitiver Stil-Entscheid wartet auf den ersten konkreten Use-Case.
- **`@dataclass(slots=True)`**: Soll `RuntimeData` mit `slots=True` deklariert werden? Spart Speicher pro Entry, verhindert aber dynamische Attribut-Ergänzung — was die obige Frage zur Mutation ohnehin verbietet.
