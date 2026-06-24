# HA-Integration: Intents und Conversation

Status: draft

## Kontext

Ein **Intent** ist die Beschreibung einer Nutzer-Absicht — eine High-Level-Aktion, die durch Nutzer-Handlungen erzeugt wird, etwa „Amazon Echo bitten, ein Licht einzuschalten". Intents werden von Komponenten **gefeuert**, die sie von externen Quellen/Diensten empfangen (Conversation, Alexa, API.ai, Snips), und können von **jeder** Komponente **gehandhabt** werden. Genau das macht es für eine Custom Integration einfach, mit allen Voice-Assistenten gleichzeitig zu integrieren: Sie registriert einen `IntentHandler`, und sobald ein passender Intent gefeuert wird — egal aus welcher Quelle — antworten ihre Geräte über Assist.

Intents sind über die Klasse `homeassistant.helpers.intent.Intent` implementiert; ein Intent trägt `hass`, `platform`, `intent_type`, `slots`, optional `text_input` und `language`. Eine Integration registriert einen Handler via `intent.async_register(hass, handler)`, deklariert dort `intent_type`, optional ein `slot_schema`, und implementiert `async_handle(intent_obj)`, das eine `IntentResponse` zurückgibt. Intents lassen sich aus eigenem Code via `intent.async_handle(hass, platform, intent_type, slots)` feuern; die Antwort ist eine `IntentResponse` mit `speech`, `reprompt` und `card`.

HA liefert eine Reihe von **Built-in Intents** (`HassTurnOn`, `HassTurnOff`, `HassGetState`, …), die eine Integration implementieren kann, damit ihre Geräte auf Assist-Sätze reagieren. Über die Conversation-Schicht (`/api/conversation/process`) wird ein Eingabesatz zu Text-Erkennung, Intent-Feuerung und einer `conversation response` verarbeitet. Eine Integration kann zusätzlich einen **eigenen Conversation-Agenten** als `ConversationEntity` bereitstellen.

Diese Spec adressiert die **Entwickler-orientierte Intent-/Conversation-API** — Handler, Slots, Built-in-Intent-Implementierung, Conversation-Entity und Sätze. Sie adressiert **nicht** die End-User-Konfiguration von Assist (Exposing von Entitäten im UI, Voice-Pipeline-Setup). Abgrenzung: Intent vs. Service ist in `ha/services` festgehalten; Lokalisierung der Intent-Sätze (`intents/<lang>.yaml`) gehört zu `ha/translations`; dass eine Conversation-Entity eine reguläre Entität ist, folgt aus `ha/entity-architecture`.

## Ziele

- `IntentHandler`-Registrierung als alleinigen Eintrittspunkt für eigene High-Level-Aktionen — eine Quelle pro `intent_type`
- Built-in Intents (`HassTurnOn`/`HassTurnOff`/`HassGetState`) implementieren, damit die Geräte der Integration auf Standard-Assist-Sätze reagieren, statt ausschließlich proprietäre Intents anzubieten
- Slot-Validierung über ein deklariertes `slot_schema` erzwingen, statt im Handler-Code ad-hoc zu prüfen
- Intent-Antworten konsequent über `IntentResponse`/`async_set_speech` formulieren, sodass Assist eine sprechbare Rückmeldung erhält
- Eigene Conversation-Agenten als `ConversationEntity` mit `supported_languages` bereitstellen, statt das veraltete `async_process`-Muster neu zu implementieren
- Intent-Sätze und ihre Lokalisierung von der Handler-Logik trennen, sodass Sprache und Code unabhängig wartbar bleiben

## Nicht-Ziele

- End-User-Konfiguration von Assist (Exposing von Entitäten im UI, Voice-Pipeline-, STT-/TTS-Setup) — Nutzer-Dokumentation, nicht Entwickler-API
- Übersetzung der Intent-Sätze (`intents/<lang>.yaml`, Response-Texte) — gehört zu `ha/translations`
- Service-Definition und `services.yaml`-Schema — eigene Spec `ha/services`; Abgrenzung Intent vs. Service ist dort und unten festgehalten
- Entity-Lifecycle und -Registrierung der Conversation-Entity im Detail — gehört zu `ha/entity-architecture`
- Externe Intent-Quellen (Alexa-, API.ai-, Snips-Bridge-Setup) — die Spec adressiert nur die Handler-Seite, nicht die Quellen-Konfiguration

## Anforderungen

### Intent-Handler registrieren

- **MUSS [MUST]** jeden eigenen Intent-Handler von `homeassistant.helpers.intent.IntentHandler` ableiten und via `intent.async_register(hass, handler)` registrieren
- **MUSS [MUST]** auf der Handler-Klasse `intent_type` als String setzen, der den zu handhabenden Intent benennt (z. B. `intent_type = "CountInvocationIntent"`)
- **MUSS [MUST]** `async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse` implementieren und eine `IntentResponse` zurückgeben — niemals `None` oder einen rohen String
- **SOLLTE [SHOULD]** je `intent_type` genau einen Handler registrieren — mehrere Handler für denselben Typ machen die Auflösung mehrdeutig
- **MUSS NICHT [MUST NOT]** Intent-Handler in Plattform-Modulen (`sensor.py`, `light.py`) registrieren; Registrierung gehört in `async_setup`/`async_setup_entry`

### Slots & Slot-Schema

- **MUSS [MUST]** Slot-Werte ausschließlich über `intent_obj.slots` lesen — das Dictionary ist nach Slot-Namen geschlüsselt, der eigentliche Wert liegt unter `slots["<name>"]["value"]`
- **SOLLTE [SHOULD]** ein `slot_schema`-Validierungsschema auf der Handler-Klasse deklarieren (z. B. `slot_schema = {"item": cv.string}`), wenn der Intent Slots erwartet, statt die Eingabe ungeprüft zu verwenden
- **MUSS [MUST]** beim Feuern eines Intents aus eigenem Code die Slots in der dokumentierten Form übergeben — `slots = {"<name>": {"value": <wert>}}` an `intent.async_handle(hass, platform, intent_type, slots)`
- **KANN [MAY]** `intent_obj.text_input` und `intent_obj.language` auswerten, wenn der Handler den Rohtext oder die Eingabesprache benötigt — beide sind optional und können fehlen

### Built-in Intents implementieren

- **SOLLTE [SHOULD]** die unterstützten Built-in Intents implementieren, die zur Domäne der Integration passen (z. B. `HassTurnOn`, `HassTurnOff`, `HassGetState`), damit die Geräte auf Standard-Assist-Sätze reagieren
- **MUSS [MUST]** für `HassTurnOn`/`HassTurnOff` die Slots als **optional** behandeln und die dokumentierten Slot-Kombinationen unterstützen (z. B. `name only`, `area only`, `area and domain`, `device class and domain`)
- **MUSS NICHT [MUST NOT]** **deprecated** Intents neu implementieren (`HassOpenCover`, `HassCloseCover`, `HassToggle`, `HassHumidifierSetpoint`, `HassHumidifierMode`, `HassShoppingListLastItems`) — stattdessen die jeweils empfohlenen Ersatz-Intents verwenden (z. B. `HassTurnOn` statt `HassOpenCover`)
- **SOLLTE [SHOULD]** den Built-in-Intent-Katalog als von der Intents-Repository generiert behandeln und keine lokale Kopie der Intent-Liste pflegen, die driften kann

### Intent-Response & Speech

- **MUSS [MUST]** die Antwort über `intent_obj.create_response()` erzeugen und die gesprochene Rückmeldung via `response.async_set_speech("<text>")` setzen
- **MUSS [MUST]** Speech-Antworten nur in den erlaubten Typen liefern — `plain` (Default) oder `ssml`; andere Speech-Typen sind nicht zulässig
- **KANN [MAY]** über die `reprompt`-Antwort die Session offen halten, wenn eine Nutzer-Antwort erforderlich ist — in diesem Fall ist `speech` üblicherweise eine Rückfrage
- **MUSS [MUST]** den korrekten `response_type` der Conversation-Antwort respektieren — `action_done` (eine Aktion wurde ausgeführt, mit `targets`/`success`/`failed`), `query_answer` (Antwort auf eine Frage), oder `error`
- **MUSS [MUST]** im Fehlerfall einen passenden `data.code` setzen — einen aus `no_intent_match`, `no_valid_targets`, `failed_to_handle`, `unknown` — und die Fehlermeldung über `speech` ausgeben

### Conversation-Agent (`ConversationEntity`)

- **MUSS [MUST]** einen eigenen Conversation-Agenten von `homeassistant.components.conversation.ConversationEntity` ableiten — nicht direkt von `AbstractConversationAgent`, wenn die Entity-Variante verfügbar ist
- **MUSS [MUST]** auf der Conversation-Entity `supported_languages` deklarieren (`list[str]` oder `"*"` für alle Sprachen) — die Property ist Pflicht
- **MUSS [MUST]** eingehende Nachrichten in `_async_handle_message(self, user_input, chat_log) -> ConversationResult` verarbeiten und das Ergebnis als `ConversationResult` mit `response` und `conversation_id` zurückgeben
- **SOLLTE [SHOULD]** `_async_handle_message` statt des veralteten `async_process` implementieren — der neue Hook bindet den `chat_log` automatisch ein und ist rückwärtskompatibel
- **SOLLTE [SHOULD]** das `CONTROL`-Feature (`ConversationEntityFeature.CONTROL`) nur dann setzen, wenn der Agent tatsächlich in der Lage ist, Home Assistant zu steuern
- **KANN [MAY]** `async_prepare(self, language)` implementieren, um Ressourcen (Sprachmodell o. Ä.) vorzuladen, sobald eine Anfrage angekündigt ist — die Methode ist optional
- **MUSS NICHT [MUST NOT]** in Property-Gettern I/O (Netzwerk-Requests o. Ä.) ausführen — Properties geben ausschließlich Informationen aus dem Speicher zurück

### Sätze & Lokalisierung

- **SOLLTE [SHOULD]** Intent-Sätze in `intents/<lang>.yaml` pflegen und damit von der Handler-Logik trennen, sodass Sprache und Code unabhängig wartbar bleiben
- **MUSS [MUST]** beim Verarbeiten eines Conversation-Eingabesatzes die Eingabesprache respektieren — `language` ist optional und fällt sonst auf die konfigurierte HA-Sprache zurück
- **KANN [MAY]** Sätze einer Sprache über die WebSocket-API (`conversation/prepare`) vorladen, wenn Latenz beim ersten Satz reduziert werden soll
- **MUSS NICHT [MUST NOT]** lokalisierte Sätze oder Response-Texte fest im Handler-Code verdrahten — die Lokalisierung gehört in die Sprach-Artefakte (`ha/translations`)

## Akzeptanzkriterien

- [ ] Jeder Intent-Handler leitet von `IntentHandler` ab, ist via `intent.async_register(hass, handler)` registriert und setzt `intent_type`
- [ ] `async_handle(intent_obj)` gibt eine `IntentResponse` zurück, die über `create_response()`/`async_set_speech()` erzeugt wurde
- [ ] Slot-Werte werden über `intent_obj.slots["<name>"]["value"]` gelesen; bei erwarteten Slots ist ein `slot_schema` deklariert
- [ ] Zur Domäne passende Built-in Intents (`HassTurnOn`/`HassTurnOff`/`HassGetState`) sind implementiert; `HassTurnOn`/`HassTurnOff` behandeln Slots als optional
- [ ] Keine deprecated Intents (`HassToggle`, `HassOpenCover`, …) sind neu implementiert
- [ ] Speech wird nur als `plain` oder `ssml` geliefert; Fehler tragen einen gültigen `data.code`
- [ ] Der eigene Conversation-Agent leitet von `ConversationEntity` ab, deklariert `supported_languages` und implementiert `_async_handle_message(...) -> ConversationResult`
- [ ] `ConversationEntityFeature.CONTROL` ist nur gesetzt, wenn der Agent HA tatsächlich steuern kann
- [ ] Intent-Sätze liegen in `intents/<lang>.yaml`; keine lokalisierten Texte sind im Handler-Code verdrahtet

## Offene Fragen

- **`AbstractConversationAgent` vs. `ConversationEntity`**: Die Docs zeigen beide Wege. Soll die Spec `ConversationEntity` strikt vorschreiben, oder bleibt `AbstractConversationAgent` für Agenten ohne Entity-Repräsentation eine zulässige Alternative?
- **Custom vs. Built-in Intents**: Ab wann SOLLTE eine Integration einen eigenen `intent_type` definieren statt einen Built-in Intent zu erweitern? Eine Schwelle (z. B. „nur wenn kein Built-in die Aktion abdeckt") würde Skill-Output deterministisch machen.
- **`continue_conversation`-Semantik**: Wann SOLLTE ein Handler die Session offen halten (`continue_conversation: true` / `reprompt`)? Aktuell nur als Möglichkeit beschrieben — eine konkrete Leitlinie fehlt.
- **Conversation-Id-Tracking**: Soll die Spec vorschreiben, dass jeder Agent Multi-Turn über `conversation_id` unterstützt, oder bleibt das optional (Rückgabe `None`, wenn nicht unterstützt)?
- **Chat-Log-Nutzung**: Welche Verpflichtungen gelten für das Lesen/Schreiben des `chat_log` (Tool-Calls, History)? Die getypte Python-Schnittstelle ist verlinkt, aber die Spec abstrahiert sie hier noch nicht.
