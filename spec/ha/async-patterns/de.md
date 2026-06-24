# HA-Integration: Async-Patterns

Status: draft

## Kontext

Der HA-Core läuft seit `0.29` auf Pythons `asyncio`-Modul: Der Zugriff auf die nicht-threadsicheren Core-API-Objekte (z. B. der State der Entitäten) ist auf einen einzigen Thread beschränkt — die *Event-Loop*. Alle Komponenten schedulen sich selbst als Task in der Event-Loop, sodass garantiert nur ein Task gleichzeitig läuft und keine Locks nötig sind. Das einzige Problem dieses Modells ist, wenn ein Task blockierendes I/O macht: Solange die Event-Loop blockiert ist, kann nichts anderes laufen, und das gesamte System stallt für die Dauer der blockierenden Operation.

HA-Quellen formulieren dafür zwei harte Invarianten: kein blockierendes I/O in der Event-Loop (siehe `asyncio_blocking_operations.md`) und keine nicht-threadsicheren Aufrufe von Core-APIs aus einem fremden Thread (siehe `asyncio_thread_safety.md`). Ab `2024.5.0` erkennt und blockiert HA einige nicht-threadsichere Operationen, ab `2024.7.0` erkennt HA zusätzliche blockierende Aufrufe in der Event-Loop — Verstöße, die früher zu Instabilität oder undefiniertem Verhalten führten, werden heute aktiv gemeldet. Diese Spec überführt die HA-Async-Konventionen (`async_`-Naming, `@callback`-Semantik, Executor-Offloading, Thread-Safety, Funktions-Kategorisierung, blockierende Imports) in eine verbindliche Verpflichtung für jede Custom Integration, die Skills aus diesem Plugin scaffolden.

Quality-Scale-Marker: **Platinum** (`async-dependency` verlangt vollständig asynchrone Abhängigkeiten ohne blockierendes I/O in der Event-Loop; `strict-typing` verlangt durchgängige Typannotation der async-/Callback-Signaturen). Die Regeln dieser Spec sind außerdem Bestandteil der allgemeinen Code-Review-Standards von HA und gelten unabhängig von der angestrebten Quality-Scale-Stufe.

## Ziele

- Die Event-Loop strikt von blockierendem I/O freihalten — blockierende Operationen laufen entweder im Executor oder über async-Bibliotheken
- Die HA-Naming-Konvention durchsetzen: `async_`-Präfix für alles, was aus der Event-Loop laufen muss; `@callback` für nicht-blockierende, in der Loop laufende Funktionen
- Thread-Safety erzwingen: Aufrufe von Loop-only-Core-APIs aus einem fremden Thread laufen ausschließlich über die dokumentierten threadsicheren Brücken
- Jede Funktion einer Kategorie zuordnen (Coroutine, Callback, thread- und loop-sicher, sonstige) und die zugehörigen Constraints einhalten
- Blockierende oder schwere Imports außerhalb des Modul-Levels in den Executor verlagern bzw. über die threadsicheren Import-Helper laden
- Async-Fehler früh sichtbar machen — `asyncio`-Debug-Mode und HAs Debug-Mode während der Entwicklung aktivieren

## Nicht-Ziele

- Coordinator-spezifische Async-Mechanik (`_async_update_data`, `async_config_entry_first_refresh`, Error-Mapping) — gehört in `ha/coordinator-patterns`; diese Spec deckt nur die generischen Async-Regeln darunter
- Auswahl konkreter async-Bibliotheken (`aiohttp` vs. `httpx`) pro Integration — fällt unter `ha/integration-architecture` bzw. die API-Client-Definition in `ha/security-hardening`
- Migration bestehender synchroner Integrationen auf async — eigene Folge-Spec, sobald ein konkreter Migrationsfall auftaucht
- Performance-Tuning der Event-Loop jenseits der Nicht-Blockieren-Regel (Profiling, Task-Priorisierung) — derzeit nicht abgedeckt

## Anforderungen

### Event-Loop nie blockieren

- **MUSS [MUST]** sicherstellen, dass keine blockierende Operation in der Event-Loop läuft — laut HA stallt das gesamte System für die Dauer der blockierenden Operation
- **MUSS [MUST]** die in `asyncio_blocking_operations.md` gelisteten blockierenden Operationen als blockierend behandeln: `open` (blockierendes Disk-I/O), `sleep` (blockierend statt `await asyncio.sleep`), `putrequest`/`urllib` (blockierendes Netzwerk-I/O), `glob.glob`, `glob.iglob`, `os.walk`, `os.listdir`, `os.scandir`, `os.stat`, `pathlib.Path.write_bytes`/`write_text`/`read_bytes`/`read_text`, sowie `SSLContext.load_default_certs`/`load_verify_locations`/`load_cert_chain`/`set_default_verify_paths`
- **MUSS [MUST]** einen blockierenden `time.sleep` durch `await asyncio.sleep(...)` ersetzen und blockierendes HTTP (`urllib`) auf `aiohttp` oder `httpx` umstellen statt es im Executor zu kapseln, wenn eine async-Alternative existiert
- **MUSS [MUST]** beim Fix eines `open`-Aufrufs in der Event-Loop auch alle zugehörigen blockierenden Reads und Writes in den Executor verschieben — HA erkennt nur das `open`, nicht die nachgelagerten I/O-Aufrufe
- **SOLLTE [SHOULD]** während der Entwicklung den `asyncio`-Debug-Mode und HAs eingebauten Debug-Mode aktivieren, da viele blockierende-I/O- und Thread-Safety-Fehler dann automatisch erkannt werden
- **MUSS NICHT [MUST NOT]** I/O in Entity-Properties durchführen — Properties werden aus der Event-Loop gelesen; alle Daten werden in der Update-Methode geholt und auf der Entität gecacht

### Executor-Offloading

- **MUSS [MUST]** blockierenden Code innerhalb von HA über `await hass.async_add_executor_job(blocking_code, arg)` in den Executor verlagern
- **MUSS [MUST]** in Bibliotheks-Code (außerhalb von HA) `await loop.run_in_executor(None, blocking_code, arg)` mit `loop = asyncio.get_running_loop()` verwenden
- **SOLLTE [SHOULD]** Keyword-Argumente über `functools.partial` binden (`hass.async_add_executor_job(partial(blocking_code_with_kwargs, kwarg=True))`), da `async_add_executor_job` nur positionale Argumente durchreicht
- **KANN [MAY]** für die SSL-Context-Erzeugung die blockierungssicheren Helper verwenden — `homeassistant.helpers.aiohttp_client.async_get_clientsession` (aiohttp), `homeassistant.helpers.httpx_client.get_async_client` (httpx) bzw. `homeassistant.util.ssl` für generisches SSL —, die das blockierende I/O bereits im Executor erledigen
- **MUSS NICHT [MUST NOT]** `async_add_executor_job` aus einer Funktion heraus aufrufen, die ihrerseits per `run_coroutine_threadsafe`/`asyncio.run_coroutine_threadsafe` aus einem Thread blockiert wird — laut HA kann diese Kombination zu einem Deadlock führen

### Callback- vs. Coroutine-Konvention (`@callback`)

- **MUSS [MUST]** jede Funktion, die aus der Event-Loop laufen muss, mit dem `async_`-Präfix benennen — HA verwendet diese Konvention, um Loop-pflichtige Funktionen kenntlich zu machen
- **MUSS [MUST]** eine Coroutine über `async def` deklarieren und ihre Loop-pflichtigen Abhängigkeiten `await`-en; das Aufrufen einer Coroutine-Funktion gibt nur ein noch nicht gestartetes Objekt zurück, das erst beim `await` oder beim Schedulen auf der Event-Loop ausgeführt wird
- **MUSS [MUST]** eine nicht-blockierende, in der Loop laufende Funktion mit `@callback` aus `homeassistant.core` dekorieren — ein Callback kann sich nicht suspendieren und darf daher kein I/O machen und keine Coroutine aufrufen oder `await`-en (er darf höchstens einen neuen Task schedulen, ohne auf dessen Ergebnis zu warten)
- **MUSS NICHT [MUST NOT]** eine Funktion gleichzeitig als Coroutine (`async def`) und mit `@callback` deklarieren — `@callback` markiert ausdrücklich eine normale, nicht-suspendierbare Funktion
- **SOLLTE [SHOULD]** einen Callback statt einer Coroutine wählen, wenn keine Suspendierung nötig ist — laut HA spart das einen Loop-Durchlauf (die Loop läuft dann nur `A` statt `A`, `B`, `A`) und verbessert die State-Konsistenz der Core-API-Objekte
- **MUSS [MUST]** beim Registrieren eines Built-in-Helper-Callbacks (z. B. `async_track_state_change_event`) den Handler mit `@callback` dekorieren, wenn er in der Event-Loop laufen soll — fehlt das Dekorator, läuft der Handler im Executor und macht einen nicht-threadsicheren Aufruf von `async_write_ha_state`

### Thread-Safety

- **MUSS [MUST]** beachten, dass nahezu alle `asyncio`-Objekte nicht thread-sicher sind und Loop-only-Core-APIs niemals direkt aus einem fremden Thread aufgerufen werden
- **MUSS [MUST]** beim Aufruf aus einem fremden Thread die nicht-`async`-Variante einer Core-API verwenden, wo HA eine anbietet — verbatim aus `asyncio_thread_safety.md`: statt `hass.async_create_task` → `hass.create_task`; statt `hass.bus.async_fire` → `hass.bus.fire`; statt `hass.services.async_register` → `hass.services.register`; statt `hass.services.async_remove` → `hass.services.remove`; statt `async_write_ha_state` → `self.schedule_update_ha_state`; statt `async_dispatcher_send` → `dispatcher_send`
- **MUSS [MUST]** für Loop-only-APIs ohne Sync-Variante (`hass.config_entries.async_update_entry`, `async_render_to_info`, sowie sämtliche `area_registry`-, `category_registry`-, `device_registry`-, `entity_registry`-, `floor_registry`-, `issue_registry`- und `label_registry`-Mutationen) `hass.add_job` verwenden, um eine Funktion in der Event-Loop zu schedulen, die die `async_`-API aufruft — bzw. die dokumentierten Sync-Helper `issue_registry.create_issue` / `issue_registry.delete_issue`
- **MUSS [MUST]** beim Aufruf einer ausschließlich async vorhandenen Funktion aus einem Thread `asyncio.run_coroutine_threadsafe(coro, hass.loop).result()` (oder den äquivalenten `run_callback_threadsafe`/`hass.loop.call_soon_threadsafe`-Pfad) verwenden, um die Coroutine threadsicher auf der Loop zu schedulen
- **MUSS NICHT [MUST NOT]** `hass.config_entries.async_update_entry`, `async_render_to_info` oder eine Registry-Mutation direkt aus einem fremden Thread aufrufen — diese Operationen müssen in der Event-Loop-Thread laufen, sonst korrumpieren sie den internen `asyncio`-State

### Funktions-Kategorisierung

- **MUSS [MUST]** jede Funktion einer der vier HA-Kategorien aus `asyncio_categorizing_functions.md` zuordnen: Coroutine (`async def`, Loop-pflichtig, `async_`-Präfix), Callback (`@callback`, in der Loop, nicht-blockierend), event-loop- und thread-sicher (reine In-Memory-Berechnung/Transformation, kein I/O), oder sonstige (nutzt `sleep` oder I/O und ist nicht loop-sicher)
- **MUSS [MUST]** eine Funktion nur dann als event-loop- und thread-sicher behandeln, wenn sie kein I/O macht — laut HA fällt alles, was I/O macht, ausdrücklich nicht in diese Kategorie
- **SOLLTE [SHOULD]** im Zweifel die Implementierung einer aufgerufenen Funktion prüfen, bevor sie aus der Event-Loop heraus genutzt wird — für die thread- und loop-sichere Kategorie gibt es keine Annotation, die Einordnung ist Aufgabe der Aufruferin
- **MUSS [MUST]** Funktionen der Kategorie „sonstige" (mit `sleep` oder I/O) aus der Event-Loop heraus über den Executor aufrufen statt direkt

### Blockierende Imports

- **SOLLTE [SHOULD]** Imports auf Modul-Level (Top-Level) in `__init__.py` halten — HA lädt die Integration dann entweder vor dem Start der Event-Loop oder im Import-Executor, sodass die Imports sicher sind
- **MUSS [MUST]** jeden Import außerhalb des Modul-Levels einzeln prüfen, da die Import-Machinery beim Laden des Moduls blockierendes Disk-I/O macht und CPython-Imports nicht thread-sicher sind
- **MUSS [MUST]** einen bedingten Late-Import, der nur an einer einzigen Stelle passiert, in den Executor verlagern (`hass.async_add_executor_job(_function_that_does_late_import)` innerhalb von HA bzw. `loop.run_in_executor(None, _function_that_does_late_import)` außerhalb)
- **KANN [MAY]** bei potenziell konkurrierenden Imports aus mehreren Pfaden den thread-sicheren Helper `homeassistant.helpers.importlib.import_module` bzw. `async_import_module` verwenden
- **SOLLTE [SHOULD]** ausschließlich für Type-Checking benötigte Imports in einen `if TYPE_CHECKING:`-Block setzen, damit sie zur Laufzeit nicht geladen werden
- **SOLLTE [SHOULD]** selten genutzten, CPU- und I/O-intensiven Code nicht auf Modul-Level importieren, sondern den Import deferren, damit Ressourcen nur bei Bedarf belegt werden

## Akzeptanzkriterien

- [ ] Kein blockierendes I/O (Datei, Netzwerk, `sleep`, `requests`/`urllib`) läuft in der Event-Loop; jede der in `asyncio_blocking_operations.md` gelisteten Operationen ist entweder in den Executor verlagert oder durch eine async-Alternative ersetzt
- [ ] Blockierender Code wird über `hass.async_add_executor_job(...)` (innerhalb HA) bzw. `loop.run_in_executor(None, ...)` (Bibliotheks-Code) ausgelagert; Keyword-Argumente sind per `functools.partial` gebunden
- [ ] Jede Loop-pflichtige Funktion trägt das `async_`-Präfix; Coroutinen sind `async def`, nicht-blockierende Loop-Funktionen sind mit `@callback` dekoriert
- [ ] Keine Funktion ist gleichzeitig `async def` und mit `@callback` dekoriert; kein `@callback`-Handler macht I/O oder `await`-et eine Coroutine
- [ ] Built-in-Helper-Handler (z. B. für `async_track_state_change_event`) sind mit `@callback` dekoriert
- [ ] Aufrufe von Core-APIs aus einem fremden Thread laufen über die dokumentierte Sync-Variante, `hass.add_job` oder `asyncio.run_coroutine_threadsafe(...).result()` — kein direkter Aufruf von `async_write_ha_state`, `async_update_entry`, `async_render_to_info` oder einer Registry-Mutation aus einem Thread
- [ ] Jede Funktion ist einer der vier HA-Kategorien (Coroutine / Callback / loop- und thread-sicher / sonstige) eindeutig zuordenbar
- [ ] Imports liegen auf Modul-Level in `__init__.py` oder sind als bedingte Late-Imports in den Executor bzw. den thread-sicheren Import-Helper verlagert
- [ ] Reine Type-Checking-Imports stehen in einem `if TYPE_CHECKING:`-Block
- [ ] Quality-Scale-Marker für dieses Pattern ist gesetzt: **Platinum** (`async-dependency`, `strict-typing`)

## Offene Fragen

- **Executor-vs.-async-Heuristik**: Wann ist Executor-Offloading akzeptabel und wann ist die Migration auf eine async-Bibliothek verpflichtend? Aktuell verlangt die Spec die async-Alternative „wenn sie existiert" — eine messbare Schwelle (Aufruf-Frequenz, Latenz, Thread-Pool-Druck) fehlt.
- **Executor-Pool-Sättigung**: Viele parallele `async_add_executor_job`-Aufrufe können den Default-Thread-Pool sättigen. Soll die Spec ein Limit oder einen dedizierten Executor für I/O-lastige Integrationen verlangen?
- **Debug-Mode in CI**: Sollte die Spec den `asyncio`-Debug-Mode und HAs Debug-Mode auch im Test-Harness (siehe `ha/test-harness`) erzwingen, damit blockierende-I/O- und Thread-Safety-Fehler in CI auffallen statt erst zur Laufzeit?
- **`async_import_module`-Schwelle**: Ab wann verlangt die Spec den thread-sicheren Import-Helper statt eines einfachen Executor-Late-Imports? Die HA-Doku unterscheidet nach „möglicherweise konkurrierend aus mehreren Pfaden" — ein konkretes Kriterium im Repo-Kontext fehlt.
- **`run_callback_threadsafe`-vs.-`hass.add_job`-Abgrenzung**: Wann ist `hass.loop.call_soon_threadsafe`/`run_callback_threadsafe` der richtige Pfad und wann `hass.add_job`? Die HA-Doku nennt überwiegend `hass.add_job`; eine Entscheidungsregel für die low-level-Varianten fehlt.
