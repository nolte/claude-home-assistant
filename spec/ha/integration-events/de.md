# HA-Integration: Events (feuern und lauschen)

Status: draft

## Kontext

Der Kern von Home Assistant wird durch Events getrieben — wer auf etwas reagieren will, reagiert auf Events. Eine Custom Integration kann über den **HA-Event-Bus** (`hass.bus`) zwei Dinge tun: eigene Events **feuern** (z. B. „Bewegung erkannt", „Taster gedrückt") und auf Events **lauschen** (z. B. der Lifecycle-Stop von HA, ein State-Change einer Entität). Der Event-Bus akzeptiert beliebige Event-Typen als String und beliebige JSON-serialisierbare Event-Daten als Dictionary.

Diese Spec überführt die HA-Developer-Doku (`integration_events`, `integration_listen_events`, `dev_101_events`) in eine generische Verpflichtung für Portfolio-Integrationen. Die Doku trägt zwei nicht-offensichtliche Leitplanken, die hier zentral werden: (1) **Event-Naming** — eigene Events tragen zwingend den Integrations-Domain als Präfix (`<domain>_event`), damit der globale Bus kollisionsfrei bleibt; (2) **Event vs. State** — Event-Code gehört nicht in die Entity-Logik, und Entity-State darf keine Events repräsentieren (kein Binary-Sensor, der für 30 Sekunden `on` ist, wenn ein Event passiert).

Beim Lauschen liefern sowohl die Event-Helper (`homeassistant.helpers.event`) als auch der direkte Bus-Zugriff (`async_listen`, `async_listen_once`) ein Callable zurück, das den Listener wieder abmeldet. Dieses Unsubscribe-Callable muss für sauberes Teardown über `entry.async_on_unload(...)` registriert werden — sonst leakt der Listener über den Config-Entry-Reload hinaus. `@callback`-Semantik (nicht-blockierend, läuft im Event-Loop) gehört zu `ha/async-patterns`; das `async_on_unload`-Cleanup-Pattern zu `ha/setup-lifecycle`; die Abgrenzung zu benutzergesteuerten Aktionen zu `ha/services`; die Entity-Modellierung zu `ha/entity-architecture`.

Quality-Scale-Marker: **Bronze** (korrektes Event-Naming, sauberes Listener-Teardown und die Event-vs-State-Trennung sind grundlegende Korrektheits-Anforderungen).

## Ziele

- Eigene Integrations-Events über `hass.bus.async_fire(event_type, event_data)` feuern, statt Events an die Entity-Logik zu koppeln
- Event-Typen zwingend mit dem Integrations-Domain präfixen (`<domain>_event`), damit der globale Bus kollisionsfrei bleibt
- Den `event_data`-Shape dokumentieren und stabil halten, sodass Device-Trigger und Automationen verlässlich darauf bauen können
- Auf Events ausschließlich über `async_listen` / `async_listen_once` (oder die bevorzugten Event-Helper) lauschen und das zurückgegebene Unsubscribe-Callable über `entry.async_on_unload(...)` registrieren
- Listener als `@callback` implementieren, sodass sie nicht blockieren und im Event-Loop laufen
- Die Trennung zwischen Event (flüchtiges Vorkommnis) und State (dauerhafter Zustand) konsequent durchhalten

## Nicht-Ziele

- Benutzergesteuerte Aktionen (Service-Aufrufe aus Frontend, Automation, Skript) — eigene Spec `ha/services`
- `@callback`-Mechanik und Loop-vs-Executor-Regeln im Detail — gehört zu `ha/async-patterns`
- Das `async_on_unload`-Teardown-Pattern und der Setup-Lifecycle insgesamt — gehört zu `ha/setup-lifecycle`
- Entity-Modellierung und die Frage, wann ein Event als `event`-Entity exponiert wird — gehört zu `ha/entity-architecture`
- Die Datenbank-Persistenz von Events (Recorder-Schema, `data.home-assistant.io`) — außerhalb des Integration-Scopes

## Anforderungen

### Events feuern

- **MUSS [MUST]** eigene Events über den Event-Bus feuern: `hass.bus.async_fire("<domain>_event", event_data)` — der Bus ist über `hass.bus` auf der HA-Instanz erreichbar
- **MUSS [MUST]** Event-Daten als JSON-serialisierbares Dictionary übergeben (Zahlen, Strings, Listen, verschachtelte Dicts) — nicht-serialisierbare Objekte sind nicht erlaubt
- **SOLLTE [SHOULD]** den Bus nur dann direkt befeuern, wenn kein passender Helper oder keine `event`-Entity das Vorkommnis bereits sauberer modelliert — die Doku empfiehlt `event`-Entitäten als bevorzugte Darstellung
- **MUSS NICHT [MUST NOT]** Event-Code in die Entity-Logik einer Plattform legen — die Übersetzung von Integrations-Events in HA-Events gehört nach `async_setup_entry` in `__init__.py`

### Event-Naming & Daten-Shape

- **MUSS [MUST]** Event-Typen mit dem Integrations-Domain präfixen — das kanonische Format ist `<domain>_event` (Beispiel: ZHA feuert `zha_event`)
- **MUSS [MUST]** geräte-/service-bezogene Events korrekt zuordnen, indem ein `device_id`-Attribut mit dem Device-Registry-Identifier in die Event-Daten aufgenommen wird
- **SOLLTE [SHOULD]** den `event_data`-Shape dokumentieren (welche Schlüssel mit welchen Typen) und ihn stabil halten, damit Device-Trigger und Automationen verlässlich darauf bauen
- **KANN [MAY]** einen Device-Trigger an das Event hängen (basierend auf dem Payload), damit User alle verfügbaren Events des Geräts sehen und in Automationen nutzen können
- **MUSS NICHT [MUST NOT]** ungepräfixte oder generische Event-Namen verwenden, die mit Core- oder Fremd-Integrations-Events kollidieren können

### Events empfangen (`async_listen`)

- **MUSS [MUST]** auf Events über `hass.bus.async_listen(event_type, callback)` (bis-abgemeldet) oder `hass.bus.async_listen_once(event_type, callback)` (genau einmal) lauschen
- **SOLLTE [SHOULD]** einen vorhandenen Event-Helper aus `homeassistant.helpers.event` bevorzugen, wenn er den benötigten Event-Typ bereits abdeckt (z. B. State-Change-Tracking, Time-Tracking) — die Helper sind hoch optimiert und minimieren die Zahl der Callbacks
- **SOLLTE [SHOULD]** `async_listen_once` für Lifecycle-Events nutzen, die pro Lauf nur einmal feuern (`EVENT_HOMEASSISTANT_START`, `EVENT_HOMEASSISTANT_STARTED`, `EVENT_HOMEASSISTANT_STOP`)
- **MUSS NICHT [MUST NOT]** Core-Events wie `EVENT_STATE_CHANGED` oder `EVENT_ENTITY_REGISTRY_UPDATED` direkt belauschen, wenn ein dedizierter Helper existiert — der Helper ist die bevorzugte Variante

### Unsubscribe & Cleanup

- **MUSS [MUST]** das von `async_listen` / `async_listen_once` (und von den Event-Helpern) zurückgegebene Unsubscribe-Callable festhalten — beide geben ein Callable zurück, das den Listener abmeldet
- **MUSS [MUST]** dieses Unsubscribe-Callable über `entry.async_on_unload(unsub)` registrieren, sodass HA den Listener beim Config-Entry-Unload/Reload automatisch abmeldet (siehe `ha/setup-lifecycle`)
- **MUSS NICHT [MUST NOT]** ein Unsubscribe-Callable verwerfen oder ungenutzt lassen — ein nicht abgemeldeter Listener leakt über den Reload hinaus und feuert doppelt

### Callback-Semantik

- **MUSS [MUST]** Listener-Funktionen mit `@callback` (`homeassistant.core.callback`) dekorieren, wenn sie nicht-blockierend sind und vollständig im Event-Loop laufen — siehe `ha/async-patterns`
- **MUSS [MUST]** in einem `@callback`-Listener jede blockierende oder I/O-bindende Arbeit vermeiden — der Callback läuft direkt im Loop und darf ihn nicht stallen
- **SOLLTE [SHOULD]** blockierende Folge-Arbeit aus dem Callback heraus als Task abkoppeln (`hass.async_create_task(...)`), statt sie im Callback selbst auszuführen — Details in `ha/async-patterns`

### Event vs. State

- **MUSS [MUST]** flüchtige Vorkommnisse (Bewegung erkannt, Taster gedrückt) als Event feuern und nicht als dauerhaften Entity-State modellieren
- **MUSS NICHT [MUST NOT]** Entity-State Events repräsentieren lassen — z. B. kein Binary-Sensor, der für 30 Sekunden `on` ist, nur weil ein Event passiert ist
- **SOLLTE [SHOULD]** ein Gerät/Service, das ausschließlich Events feuert, manuell im Device-Registry registrieren, damit die Events korrekt einem Gerät zugeordnet sind

## Akzeptanzkriterien

- [ ] Eigene Events werden über `hass.bus.async_fire("<domain>_event", event_data)` gefeuert, mit Domain-Präfix
- [ ] Geräte-bezogene Events tragen ein `device_id`-Attribut aus dem Device-Registry
- [ ] Der `event_data`-Shape ist dokumentiert (Schlüssel + Typen)
- [ ] Event-Feuer-Code liegt in `async_setup_entry` (`__init__.py`), nicht in der Entity-Logik einer Plattform
- [ ] Listener werden über `async_listen` / `async_listen_once` (oder einen Event-Helper) registriert
- [ ] Jedes zurückgegebene Unsubscribe-Callable ist über `entry.async_on_unload(...)` registriert
- [ ] Listener-Funktionen, die im Loop laufen, sind mit `@callback` dekoriert und enthalten keine blockierende I/O
- [ ] Kein Entity-State repräsentiert ein flüchtiges Event (kein „30-Sekunden-on"-Binary-Sensor)
- [ ] Quality-Scale-Marker: **Bronze**

## Offene Fragen

- **`event`-Entity statt Bus-Fire**: Die Doku empfiehlt `event`-Entitäten als bevorzugte Darstellung gegenüber rohem Bus-Feuern. Soll die Spec Bus-Fire nur noch als Ausnahme zulassen und `event`-Entitäten zur Default-Anforderung machen — und wo wird die Grenze gezogen?
- **`device_id`-Pflicht-Schwelle**: Ab wann ist das `device_id`-Attribut Pflicht — bei jedem gerätebezogenen Event oder nur, wenn ein Device-Trigger existiert?
- **Sync- vs. Async-Listen**: Die Doku listet `listen`/`listen_once` (Sync) neben `async_listen`/`async_listen_once`. Soll die Spec Sync-Varianten generell verbieten, oder gibt es Sync-Kontexte (`setup`), in denen sie erlaubt bleiben?
- **Event-Helper-Katalog**: Die Doku führt einen großen Helper-Katalog (State-, Template-, Time-, Sun-Tracking). Soll die Spec einzelne Helper namentlich als bevorzugt vorschreiben oder generisch auf „nutze den Helper, wenn vorhanden" bleiben?
- **Unsubscribe ohne Config-Entry**: `async_on_unload` setzt einen Config-Entry voraus. Wie wird das Listener-Cleanup für YAML-only- oder Setup-Phase-Listener geregelt, die keinen Entry haben?
