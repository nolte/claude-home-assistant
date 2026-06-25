# Skill: `ha-integration-events-add`

Status: draft

## Kontext

`ha/integration-events` definiert, wie eine Custom Integration über den HA-Event-Bus (`hass.bus`) teilnimmt: eigene Events **feuern** (`hass.bus.async_fire("<domain>_event", event_data)`) und auf Events **lauschen** (`hass.bus.async_listen` bis-abgemeldet / `hass.bus.async_listen_once` genau einmal). Die Spec trägt zwei nicht-offensichtliche Leitplanken: (1) **Event-Naming** — eigene Events tragen zwingend den Integrations-Domain als Präfix (`<domain>_event`), damit der globale Bus kollisionsfrei bleibt; (2) **Event vs. State** — Event-Code gehört nicht in die Entity-Logik, und Entity-State darf keine flüchtigen Events repräsentieren. Beim Lauschen liefern Bus und Event-Helper ein Unsubscribe-Callable zurück, das über `entry.async_on_unload(...)` registriert werden **muss**, sonst leakt der Listener über den Config-Entry-Reload hinaus. Der Quality-Scale-Marker ist **Bronze**. Bislang gibt es keinen Skill, der das ergänzt.

Dieser Skill ergänzt Event-Feuern und/oder Event-Lauschen in einer **bestehenden** Integration: das Bus-Feuern mit dokumentiertem Event-Typ (`<domain>_event`) und Daten-Shape, die Listener-Registrierung über `async_listen` / `async_listen_once`, das Festhalten und Teardown des Unsubscribe-Callables über `entry.async_on_unload`, und die `@callback`-Dekoration nicht-blockierender Listener — spec-konform zu `ha/integration-events`. Vor der Generierung entscheidet er mit dem User explizit **feuern vs. lauschen vs. beides**.

## Scope

Ergänzung von Event-Feuern und/oder -Lauschen in einer bestehenden `custom_components/<domain>/`-Integration: das `async_fire`-Feuern mit Domain-präfixiertem Event-Typ und dokumentiertem `event_data`-Shape (im `__init__.py`-Setup, nicht in der Entity-Logik), die Listener-Registrierung über `async_listen` / `async_listen_once`, das Festhalten des Unsubscribe-Callables und dessen Registrierung über `entry.async_on_unload(...)` (bzw. Teardown in `async_unload_entry`), und die `@callback`-Dekoration. Der Skill liest `ha/integration-events` und validiert.

## Ziele

- Mit dem User explizit die Richtung wählen — **feuern**, **lauschen** oder **beides** — bevor irgendetwas generiert wird
- Beim Feuern den Event-Typ zwingend mit dem Integrations-Domain präfixen (`<domain>_event`) und einen JSON-serialisierbaren `event_data`-Shape dokumentieren und stabil halten
- Das Feuern in `async_setup_entry` (`__init__.py`) ansiedeln und niemals in die Entity-Logik einer Plattform koppeln
- Beim Lauschen ausschließlich `async_listen` / `async_listen_once` (oder einen Event-Helper) nutzen und das zurückgegebene Unsubscribe-Callable über `entry.async_on_unload(...)` registrieren
- Nicht-blockierende Listener mit `@callback` dekorieren und blockierende Folge-Arbeit als Task abkoppeln
- Die Trennung zwischen Event (flüchtiges Vorkommnis) und State (dauerhafter Zustand) konsequent durchhalten

## Nicht-Ziele

- Benutzergesteuerte Aktionen (Service-Aufrufe aus Frontend, Automation, Skript) — `ha-service-definition-generator` / `ha/services`
- Device-Trigger, die auf einem gefeuerten Event aufsetzen — `ha-device-automation-add` / `ha/device-automations`
- `@callback`-Mechanik und Loop-vs-Executor-Regeln im Detail — `ha/async-patterns`
- Das `async_on_unload`-Teardown-Pattern und der Setup-Lifecycle insgesamt — `ha/setup-lifecycle`
- Entity-Modellierung und die Frage, wann ein Event als `event`-Entity exponiert wird — `ha/entity-architecture`
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „fire a custom event", „listen for an event", „emit an event when … happens"
  - „subscribe to the HA stop event", „react to a state change via the bus"
  - „feuere/lausche ein Integration-Event", „feuere ein eigenes Event", „lausche auf ein Event"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die Richtung (`fire` / `listen` / `both`) sowie das Vorkommnis (Prosa), aus dem der Skill Event-Typ und Daten-Shape ableitet
- **KANN [MAY]** erfassen: den `event_data`-Shape (Schlüssel + Typen), ob ein `device_id`-Attribut nötig ist, und für Listener den Event-Typ sowie ob `async_listen_once` (einmalige Lifecycle-Events) passt

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** die Richtung explizit mit dem User klären — **feuern vs. lauschen vs. beides**; ohne diese Entscheidung nicht generieren
- **MUSS [MUST]** den Event-vs-State-Check fahren: flüchtige Vorkommnisse als Event feuern, nicht als dauerhaften Entity-State modellieren; **SOLLTE [SHOULD]** auf eine `event`-Entity hinweisen, wenn sie das Vorkommnis sauberer modelliert (`ha/entity-architecture`)
- **MUSS [MUST]** die `ha/integration-events`-Spec lesen
- **MUSS NICHT [MUST NOT]** einen bestehenden Event-Typ oder Listener überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (aus `ha/integration-events`)

- **MUSS [MUST]** beim Feuern `hass.bus.async_fire("<domain>_event", event_data)` verwenden — der Event-Typ trägt zwingend den Domain-Präfix (kanonisch `<domain>_event`)
- **MUSS [MUST]** `event_data` als JSON-serialisierbares Dictionary übergeben (Zahlen, Strings, Listen, verschachtelte Dicts) — keine nicht-serialisierbaren Objekte
- **MUSS [MUST]** den Feuer-Code in `async_setup_entry` (`__init__.py`) ansiedeln, nicht in der Entity-Logik einer Plattform
- **MUSS [MUST]** für geräte-/service-bezogene Events ein `device_id`-Attribut mit dem Device-Registry-Identifier in die Event-Daten aufnehmen
- **SOLLTE [SHOULD]** den `event_data`-Shape dokumentieren (Schlüssel mit Typen) und stabil halten, damit Device-Trigger und Automationen verlässlich darauf bauen
- **MUSS [MUST]** beim Lauschen `hass.bus.async_listen(event_type, callback)` (bis-abgemeldet) oder `hass.bus.async_listen_once(event_type, callback)` (genau einmal) verwenden; für einmalige Lifecycle-Events (`EVENT_HOMEASSISTANT_START` / `_STARTED` / `_STOP`) **SOLLTE [SHOULD]** `async_listen_once` genutzt werden
- **SOLLTE [SHOULD]** einen vorhandenen Helper aus `homeassistant.helpers.event` bevorzugen, wenn er den benötigten Event-Typ abdeckt; **MUSS NICHT [MUST NOT]** Core-Events wie `EVENT_STATE_CHANGED` direkt belauschen, wenn ein dedizierter Helper existiert
- **MUSS [MUST]** das von `async_listen` / `async_listen_once` (bzw. dem Helper) zurückgegebene Unsubscribe-Callable festhalten und über `entry.async_on_unload(unsub)` registrieren — bzw. in `async_unload_entry` abbauen; ein verworfenes Callable leakt über den Reload hinaus und feuert doppelt
- **MUSS [MUST]** nicht-blockierende, im Loop laufende Listener mit `@callback` (`homeassistant.core.callback`) dekorieren und in ihnen jede blockierende oder I/O-bindende Arbeit vermeiden; **SOLLTE [SHOULD]** blockierende Folge-Arbeit als Task abkoppeln (`hass.async_create_task(...)`) — Details in `ha/async-patterns`
- **MUSS [MUST]** Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren: gefeuerte Events nutzen `async_fire` mit Domain-Präfix; geräte-bezogene Events tragen `device_id`; der `event_data`-Shape ist dokumentiert; Feuer-Code liegt in `async_setup_entry`; Listener nutzen `async_listen` / `async_listen_once` (oder Helper); jedes Unsubscribe-Callable ist über `entry.async_on_unload(...)` registriert; Loop-Listener sind `@callback` ohne blockierende I/O; kein Entity-State repräsentiert ein flüchtiges Event
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/integration-events` liefern, plus die geänderten Datei-Pfade und den Quality-Scale-Marker (**Bronze**)

### Verbote

- **MUSS NICHT [MUST NOT]** ungepräfixte oder generische Event-Namen verwenden, die mit Core- oder Fremd-Integrations-Events kollidieren können
- **MUSS NICHT [MUST NOT]** ein Unsubscribe-Callable verwerfen oder ungenutzt lassen
- **MUSS NICHT [MUST NOT]** Entity-State ein flüchtiges Event repräsentieren lassen (kein „30-Sekunden-on"-Binary-Sensor)
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill klärt explizit die Richtung (feuern / lauschen / beides) und fährt den Event-vs-State-Check
- [ ] Gefeuerte Events nutzen `hass.bus.async_fire("<domain>_event", event_data)` mit Domain-Präfix
- [ ] Geräte-bezogene Events tragen ein `device_id`-Attribut aus dem Device-Registry; der `event_data`-Shape ist dokumentiert
- [ ] Feuer-Code liegt in `async_setup_entry` (`__init__.py`), nicht in der Entity-Logik einer Plattform
- [ ] Listener werden über `async_listen` / `async_listen_once` (oder einen Event-Helper) registriert
- [ ] Jedes zurückgegebene Unsubscribe-Callable ist über `entry.async_on_unload(...)` registriert / in `async_unload_entry` abgebaut
- [ ] Loop-Listener sind mit `@callback` dekoriert und enthalten keine blockierende I/O
- [ ] Kein Entity-State repräsentiert ein flüchtiges Event
- [ ] Bericht nennt Datei-Pfade und den Quality-Scale-Marker **Bronze**

## Offene Fragen

- **`event`-Entity statt Bus-Fire**: Die Doku empfiehlt `event`-Entitäten als bevorzugte Darstellung gegenüber rohem Bus-Feuern. Soll der Skill Bus-Fire nur noch als Ausnahme zulassen und auf `event`-Entitäten verweisen? Aktuell weist er hin und feuert nach User-Entscheid.
- **`device_id`-Pflicht-Schwelle**: Ab wann ist das `device_id`-Attribut Pflicht — bei jedem gerätebezogenen Event oder nur, wenn ein Device-Trigger existiert? Aktuell fall-zu-fall.
- **Unsubscribe ohne Config-Entry**: `async_on_unload` setzt einen Config-Entry voraus. Wie regelt der Skill das Listener-Cleanup für YAML-only- oder Setup-Phase-Listener ohne Entry? Aktuell außerhalb des Standard-Pfads.
