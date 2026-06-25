# Skill: `ha-conversation-agent-augment`

Status: draft

## Kontext

`ha/intents-conversation` definiert die entwickler-orientierte Intent-/Conversation-API: Eine Integration registriert einen `IntentHandler` (abgeleitet von `homeassistant.helpers.intent.IntentHandler`, via `intent.async_register(hass, handler)`), setzt `intent_type`, deklariert optional ein `slot_schema` und implementiert `async_handle(intent_obj) -> IntentResponse`. Alternativ — oder zusätzlich — stellt sie einen eigenen Conversation-Agenten als `conversation.ConversationEntity` bereit, deklariert `supported_languages` und verarbeitet Nachrichten in `_async_handle_message(user_input, chat_log) -> ConversationResult`. `ha/llm-api` definiert die zweite, orthogonale Achse: das **Anbieten von Tools** für LLMs, indem eine `llm.API` (von `API` abgeleitet) über `llm.async_register_api(hass, api)` registriert wird und `async_get_api_instance(llm_context) -> APIInstance` eine Liste von `llm.Tool`-Objekten plus `api_prompt` liefert. Bislang gibt es keinen Skill, der diese Voice-&-AI-Oberflächen ergänzt.

Dieser Skill ergänzt **eine bestehende** Integration um eine oder mehrere dieser Oberflächen: Intent-Handler, einen Conversation-Agenten und/oder LLM-API-Tools — spec-konform zu `ha/intents-conversation` **plus** `ha/llm-api`. Weil drei verschiedene Oberflächen im Spiel sind, entscheidet der Skill **zuerst gemeinsam mit dem User**, welche Oberfläche(n) im Scope liegen, und hält die Achsen (Intents/Conversation aus `ha/intents-conversation`, Tools aus `ha/llm-api`) sauber getrennt.

## Scope

Ergänzung einer oder mehrerer Voice-&-AI-Oberflächen in einer bestehenden `custom_components/<domain>/`-Integration: (a) Intent-Handler (`IntentHandler`-Subklassen mit `intent.async_register`, `slot_schema`, `async_handle`); (b) eine Conversation-Plattform (`conversation.py` mit einer `ConversationEntity`, `supported_languages`, `_async_handle_message`); und/oder (c) LLM-API-Tools (`llm.Tool`-Subklassen + eine `llm.API` über `llm.async_register_api` mit `async_get_api_instance` → `APIInstance`). Der Skill liest `ha/intents-conversation` und `ha/llm-api` und validiert.

## Ziele

- Mit dem User entscheiden, welche Oberfläche(n) im Scope liegen (Intents vs. Conversation-Entity vs. LLM-Tools), bevor irgendetwas generiert wird — die zwei Achsen explizit getrennt halten
- Intent-Handler spec-konform ergänzen: von `IntentHandler` abgeleitet, via `intent.async_register` registriert, `intent_type` gesetzt, `slot_schema` bei erwarteten Slots, `async_handle` liefert eine `IntentResponse`
- Passende Built-in Intents (`HassTurnOn`/`HassTurnOff`/`HassGetState`) implementieren statt nur proprietäre Intents, und keine deprecated Intents neu implementieren
- Einen Conversation-Agenten als `ConversationEntity` mit `supported_languages` und `_async_handle_message(...) -> ConversationResult` bereitstellen, statt das veraltete `async_process`-Muster zu nutzen
- LLM-Tools als `llm.Tool`-Subklassen mit `name`, `parameters`-Schema und async `async_call` deklarieren, über eine `llm.API` registrieren, beim Unload deregistrieren und Fehler als `HomeAssistantError` signalisieren
- Lokalisierte Sätze und Response-Texte aus dem Handler-/Tool-Code heraushalten und an die Sprach-Artefakte delegieren

## Nicht-Ziele

- Assist-Satelliten-, STT-, TTS- oder Wake-Word-**Entitäten** (`assist_satellite`/`stt`/`tts`/`wake_word`) — `ha/entity-platforms-voice`
- Registrierte Services mit eigenem Schema — `ha-service-definition-generator` / `ha/services` (Tools werden vom LLM aufgerufen, Services sind benutzergesteuert)
- Übersetzung der Intent-Sätze (`intents/<lang>.yaml`) und Response-/Prompt-Texte — `ha/translations`
- End-User-Konfiguration von Assist (Exposing von Entitäten im UI, Voice-Pipeline-Setup) — Nutzer-Dokumentation, nicht Entwickler-API
- Greenfield-Scaffolding einer Integration — `ha-integration-scaffold`
- Die provider-seitige LLM-Anbindung (Streaming, Message-Formatierung, Tool-Serialisierung) — außerhalb dieser Spec

## Anforderungen

### Aktivierungs-Trigger

- **MUSS [MUST]** auf folgende Phrasen aktivieren:
  - „add a conversation agent", „register intents", „expose tools to the assistant via the LLM API"
  - „let my integration respond to Assist sentences", „add a custom intent handler"
  - „füge einen Conversation-Agent / Intents / LLM-Tools hinzu"

### Eingaben

- **MUSS [MUST]** erfassen: `target_dir` (Repo-Root) und die gewünschte Voice-&-AI-Fähigkeit (Prosa), aus der der Skill die Oberfläche(n) und ihre Verträge ableitet
- **MUSS [MUST]** die Scope-Entscheidung erfassen: welche Oberfläche(n) — Intents, Conversation-Entity und/oder LLM-Tools
- **KANN [MAY]** erfassen: die konkreten `intent_type`-Namen und Slots, `supported_languages`, sowie Tool-Namen, `description` und `parameters`-Schema

### Pre-Flight (in Reihenfolge, Abbruch beim ersten Fehler)

- **MUSS [MUST]** prüfen, dass `target_dir/custom_components/<domain>/manifest.json` existiert; `domain` lesen
- **MUSS [MUST]** die Scope-Entscheidung mit dem User treffen: welche der drei Oberflächen (Intents / Conversation-Entity / LLM-Tools) im Scope liegen; bei LLM-Tools **MUSS [MUST]** zusätzlich die Rolle festgelegt werden — Tools **anbieten** (`llm.API` registrieren) vs. eine API **konsumieren** (Tools aus dem `ChatLog` ziehen)
- **MUSS [MUST]** die Specs `ha/intents-conversation` und `ha/llm-api` lesen (je nach Scope mindestens die zutreffende)
- **MUSS NICHT [MUST NOT]** einen bestehenden `intent_type`, eine bestehende Conversation-Entity oder eine registrierte `llm.API`-`id` überschreiben; bei Kollision abbrechen

### Generierungs-Regeln (pro Oberfläche)

- **MUSS [MUST]** für Intent-Handler jede Handler-Klasse von `homeassistant.helpers.intent.IntentHandler` ableiten, `intent_type` als String setzen, via `intent.async_register(hass, handler)` in `async_setup`/`async_setup_entry` (nicht in Plattform-Modulen) registrieren und `async_handle(self, intent_obj) -> IntentResponse` implementieren — niemals `None` oder einen rohen String zurückgeben
- **MUSS [MUST]** Slot-Werte über `intent_obj.slots["<name>"]["value"]` lesen und bei erwarteten Slots ein `slot_schema` deklarieren
- **SOLLTE [SHOULD]** die zur Domäne passenden Built-in Intents (`HassTurnOn`/`HassTurnOff`/`HassGetState`) implementieren und für `HassTurnOn`/`HassTurnOff` die Slots als optional behandeln; **MUSS NICHT [MUST NOT]** deprecated Intents (`HassToggle`, `HassOpenCover`, …) neu implementieren
- **MUSS [MUST]** die Antwort über `intent_obj.create_response()` + `response.async_set_speech(...)` erzeugen, Speech nur als `plain` oder `ssml` liefern, den korrekten `response_type` (`action_done`/`query_answer`/`error`) setzen und im Fehlerfall einen gültigen `data.code` (`no_intent_match`/`no_valid_targets`/`failed_to_handle`/`unknown`) vergeben
- **MUSS [MUST]** für einen Conversation-Agenten `conversation.py` mit einer von `conversation.ConversationEntity` abgeleiteten Entity erzeugen, `supported_languages` (`list[str]` oder `"*"`) deklarieren und `_async_handle_message(self, user_input, chat_log) -> ConversationResult` implementieren (statt des veralteten `async_process`); `ConversationEntityFeature.CONTROL` nur setzen, wenn der Agent HA tatsächlich steuert; **MUSS NICHT [MUST NOT]** I/O in Property-Gettern ausführen
- **MUSS [MUST]** für angebotene LLM-Tools eine Klasse anlegen, die von `API` erbt, und `async_get_api_instance(self, llm_context) -> APIInstance` implementieren (mit `api`, `api_prompt` (Pflicht), `llm_context`, `tools`); die API via `llm.async_register_api(hass, api)` mit eindeutigem `id`/`name` registrieren und den Rückgabewert über `entry.async_on_unload(unreg)` deregistrieren
- **MUSS [MUST]** jedes Tool von `llm.Tool` ableiten, ein `name`-Attribut tragen, async `async_call(self, hass, tool_input, llm_context)` implementieren, ein JSON-serialisierbares `JsonObjectType`-Resultat liefern und Fehler als `HomeAssistantError` raisen — keine In-Band-Error-Codes in der Response
- **SOLLTE [SHOULD]** für Tools ein `description`-Attribut und ein voluptuous-`parameters`-Schema setzen, und beim Konsumieren die ausgewählten API-IDs unter `CONF_LLM_HASS_API` in den Options halten sowie die API über `llm.async_get_api(hass, api_id, llm_context)` auflösen
- **MUSS [MUST]** lokalisierte Sätze/Response-/Prompt-Texte aus dem Handler-/Tool-Code heraushalten (Sätze in `intents/<lang>.yaml`, `ha/translations`), Bezeichner nach `ha/naming-conventions` benennen und HA-Interna gegen die offizielle Doku verifizieren (`ha/upstream-docs-verification`)

### Validierung & Bericht

- **MUSS [MUST]** offline validieren — je nach Scope: Intent-Handler leiten von `IntentHandler` ab, sind registriert, setzen `intent_type` und liefern eine über `create_response()`/`async_set_speech()` erzeugte `IntentResponse`; die Conversation-Entity leitet von `ConversationEntity` ab, deklariert `supported_languages` und implementiert `_async_handle_message`; jedes Tool trägt `name`, implementiert `async_call`, raised `HomeAssistantError` und liefert `JsonObjectType`; die `llm.API` ist registriert und wird beim Unload deregistriert
- **MUSS [MUST]** einen CONFORMANT / NEEDS-WORK-Bericht gegen die Akzeptanzkriterien aus `ha/intents-conversation` und/oder `ha/llm-api` (je nach Scope) liefern, plus die geänderten Datei-Pfade und die gewählte(n) Oberfläche(n)

### Verbote

- **MUSS NICHT [MUST NOT]** Intent-/Conversation-Logik mit LLM-Tool-Logik vermischen — die zwei Achsen bleiben getrennt
- **MUSS NICHT [MUST NOT]** deprecated Intents neu implementieren oder das veraltete `async_process`-Muster für neue Conversation-Agenten nutzen
- **MUSS NICHT [MUST NOT]** Assist-Satelliten-/STT-/TTS-/Wake-Word-Entitäten erzeugen — diese gehören in `ha/entity-platforms-voice`
- **MUSS NICHT [MUST NOT]** in eine laufende HA-Instanz deployen

## Akzeptanzkriterien

- [ ] Skill trifft mit dem User die Scope-Entscheidung (Intents / Conversation-Entity / LLM-Tools) und legt bei Tools die Rolle (anbieten vs. konsumieren) fest
- [ ] Jeder Intent-Handler leitet von `IntentHandler` ab, ist via `intent.async_register` registriert, setzt `intent_type` und liest Slots über `intent_obj.slots["<name>"]["value"]`
- [ ] Zur Domäne passende Built-in Intents sind implementiert; keine deprecated Intents neu implementiert; Speech nur `plain`/`ssml` und Fehler mit gültigem `data.code`
- [ ] Der Conversation-Agent leitet von `ConversationEntity` ab, deklariert `supported_languages` und implementiert `_async_handle_message(...) -> ConversationResult`
- [ ] `ConversationEntityFeature.CONTROL` ist nur gesetzt, wenn der Agent HA tatsächlich steuert
- [ ] Jedes LLM-Tool trägt `name`, implementiert async `async_call(...)`, liefert `JsonObjectType` und raised `HomeAssistantError`
- [ ] Eine eigene `llm.API` erbt von `API`, implementiert `async_get_api_instance(...) -> APIInstance` mit `api_prompt`, ist über `llm.async_register_api` registriert und über `entry.async_on_unload(unreg)` deregistriert
- [ ] Lokalisierte Sätze/Texte sind nicht im Code verdrahtet; Bericht nennt Datei-Pfade und die gewählte(n) Oberfläche(n)

## Offene Fragen

- **Scope-Default**: Wenn der User unspezifisch „add a conversation agent" sagt — soll der Skill standardmäßig zur `ConversationEntity` greifen, oder zuerst klären, ob Built-in-Intents den Bedarf schon decken? Aktuell klärt er erst die Scope-Entscheidung.
- **`AbstractConversationAgent` vs. `ConversationEntity`**: `ha/intents-conversation` lässt beide Wege zu. Der Skill bevorzugt `ConversationEntity`; ob `AbstractConversationAgent` je generiert werden darf, bleibt offen.
- **Tool-Naming-Konvention**: `ha/llm-api` schreibt kein Naming-Schema vor. Der Skill folgt dem Doc-Muster und fragt im Zweifel nach.
- **Mehrere Oberflächen pro Lauf**: Der Skill erlaubt mehrere Oberflächen, sofern der User sie explizit in den Scope nimmt. Ob ein Limit (eine Oberfläche pro Lauf, wie bei `ha-device-automation-add`) sinnvoller wäre, bleibt offen.
