# HA-Integration: Entity-Plattformen (Voice & AI)

Status: draft

## Kontext

Home Assistant stellt für Voice- und AI-Capabilities eigene Entity-Plattformen bereit, deren Basisklassen sich von der generischen Entity-Architektur unterscheiden: Sprache-zu-Text, Text-zu-Sprache, Wake-Word-Erkennung, Assist-Satelliten, AI-Tasks und Notifications. Jede dieser Plattformen ist die **moderne, entity-basierte Ablösung** der jeweiligen Legacy-Plattform (`notify`, `stt`, `tts` als Plattform-Module) und wird über eine eigene Basisklasse mit einem klar definierten Satz an Pflicht-Properties und Pflicht-Methoden deklariert. Diese Spec ist der **konkrete Katalog** für genau diese sechs Plattformen.

Das generische Entity-Pattern — Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, das `EntityDescription`-Pattern, Entity-Kategorien und die Coordinator-Anbindung — ist in `ha/entity-architecture` festgeschrieben und wird **hier nicht wiederholt**. Die typisierten Sensor-/Aktor-Plattformen (`sensor`, `binary_sensor`, `climate`, `light`, `cover`) mit `device_class`, `state_class` und `supported_features` liegen in `ha/entity-platform-types`. Die **Conversation-Entity und die Intent-API** liegen in `ha/intents-conversation`; die **LLM-Tool-API** liegt in `ha/llm-api`. Diese Spec referenziert jene Specs per Slug und dupliziert sie nicht.

Jede Plattform bestimmt sich über drei Fragen: Welche Capability bildet sie ab und wann ist sie die richtige Wahl, von welcher Basisklasse erbt die Entity, und welche Properties/Methoden sind laut Plattform-Doku **Required**. Diese Spec überführt die sechs Plattform-Dokus in eine generische Verpflichtung für den Skill-Output.

## Ziele

- Die Plattformwahl an die Voice-/AI-Capability binden — Audio→Text → `stt`, Text→Audio → `tts`, Wake-Word → `wake_word`, Satelliten-Gerät → `assist_satellite`, AI-Generierung → `ai_task`, ausgehende Nachricht → `notify`
- Jede Voice-/AI-Entity von der korrekten Plattform-Basisklasse erben lassen (`SpeechToTextEntity`, `TextToSpeechEntity`, `WakeWordDetectionEntity`, `AssistSatelliteEntity`, `AITaskEntity`, `NotifyEntity`)
- Die je Plattform als **Required** dokumentierten Properties und Methoden vollständig implementieren
- Feature-Flags (`AssistSatelliteEntityFeature`, `AITaskEntityFeature`) nur setzen, wenn die zugehörige Methode implementiert ist
- Die entity-basierten Plattformen als Ablösung der Legacy-`notify`/`stt`/`tts`-Plattform-Module verwenden
- Generierten Code lauffähig in die Assist-Pipeline und das Notify-/AI-Task-System einbinden

## Nicht-Ziele

- Generisches Entity-Pattern (Base-Klasse, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription`-Pattern, Entity-Kategorien, Coordinator-Anbindung) — vollständig in `ha/entity-architecture`; diese Spec referenziert es nur
- Typisierte Sensor-/Aktor-Plattformen (`sensor`, `binary_sensor`, `climate`, `light`, `cover`) mit `device_class`/`state_class`/`supported_features` — eigene Spec `ha/entity-platform-types`
- Die Conversation-Entity und die Intent-API (Intent-Handling, Sprachbefehl-Auflösung) — eigene Spec `ha/intents-conversation`
- Die LLM-Tool-API (Tool-Exposition für Sprachmodelle) — eigene Spec `ha/llm-api`
- HA-Translation-Format (`strings.json`-Aufbau, `entity.<platform>.<key>.name`) — eigene Spec `ha/translations`
- Aufbau der Assist-Pipeline selbst und die VAD-Konfiguration im Detail — diese Spec adressiert nur die Entity-Plattformen, die in die Pipeline einklinken

## Anforderungen

### Sprache-zu-Text (`stt`)

- **MUSS [MUST]** eine Sprache-zu-Text-Entity verwenden, wenn Audio gestreamt und Text zurückgegeben werden soll — die STT-Doku definiert diese Plattform als Streaming-API für andere Integrationen oder Anwendungen
- **MUSS [MUST]** die Entity von `SpeechToTextEntity` (`homeassistant.components.stt.SpeechToTextEntity`) ableiten
- **MUSS [MUST]** alle als **Required** dokumentierten Properties bereitstellen: `supported_languages` (`list[str]`), `supported_formats` (`list[AudioFormats]`, wav oder ogg), `supported_codecs` (`list[AudioCodecs]`, pcm oder opus), `supported_bit_rates`, `supported_sample_rates` und `supported_channels` (1 oder 2)
- **MUSS [MUST]** `async_process_audio_stream` implementieren, um Audio an den STT-Dienst zu senden und Text zurückzugeben — die Doku lässt ausschließlich Streaming-Content zu
- **MUSS NICHT [MUST NOT]** in Properties I/O (z. B. Netzwerk-Requests) ausführen — die STT-Doku verlangt, dass Properties nur aus dem Speicher liefern

### Text-zu-Sprache (`tts`)

- **MUSS [MUST]** eine Text-zu-Sprache-Entity verwenden, wenn Home Assistant gesprochene Antworten erzeugen soll — die TTS-Doku definiert diese Plattform als „enables Home Assistant to speak to you"
- **MUSS [MUST]** die Entity von `TextToSpeechEntity` (`homeassistant.components.tts.TextToSpeechEntity`) ableiten
- **MUSS [MUST]** die als **Required** dokumentierten Properties `supported_languages` (`list[str]`) und `default_language` (`str`) bereitstellen
- **MUSS [MUST]** die 1-Shot-Methode `async_get_tts_audio` (oder ihre synchrone Variante `get_tts_audio`) implementieren — die TTS-Doku markiert sie als „mandatory to implement"
- **KANN [MAY]** zusätzlich `async_stream_tts_audio` implementieren, um Text-Chunks (etwa von einem Sprachmodell) zu Audio-Chunks zu streamen — fehlt sie, ruft der Dienst die 1-Shot-Methode mit der finalen Nachricht auf
- **KANN [MAY]** `async_get_supported_voices`, `supported_options` und `default_options` setzen, um Stimmen/Optionen je Sprache anzubieten

### Wake-Word-Erkennung (`wake_word`)

- **MUSS [MUST]** eine Wake-Word-Erkennungs-Entity verwenden, wenn Wake-Words (Hotwords) in einem Audio-Stream erkannt werden sollen
- **MUSS [MUST]** die Entity von `WakeWordDetectionEntity` (`homeassistant.components.wake_word.WakeWordDetectionEntity`) ableiten
- **MUSS [MUST]** die als **Required** dokumentierte Property `supported_wake_words` (`list[WakeWord]`) bereitstellen, jeweils mit `ww_id` (eindeutige Kennung) und `name` (menschenlesbar)
- **MUSS [MUST]** `async_process_audio_stream` implementieren und ein `DetectionResult` (bzw. `None`, wenn der Stream ohne Erkennung endet) zurückgeben — die Eingabe ist 16-bit Mono-PCM bei 16 kHz
- **MUSS [MUST]** in einer Assist-Pipeline während der Erkennung entfernte Audio-Chunks über `queued_audio` des `DetectionResult` zurückgeben, sonst kann Sprache-zu-Text sie nicht verarbeiten
- **MUSS NICHT [MUST NOT]** in Properties I/O ausführen — die Wake-Word-Doku verlangt, dass Properties nur aus dem Speicher liefern

### Assist-Satellit (`assist_satellite`)

- **MUSS [MUST]** eine Assist-Satellite-Entity verwenden, wenn ein Gerät die Assist-Pipeline-gestützten Voice-Assistant-Fähigkeiten repräsentiert (Sprachsteuerung von Home Assistant)
- **MUSS [MUST]** die Entity von `AssistSatelliteEntity` (`homeassistant.components.assist_satellite.AssistSatelliteEntity`) ableiten
- **MUSS [MUST]** eine Pipeline ausschließlich über `async_accept_pipeline_from_satellite` ausführen und Pipeline-Events über `on_pipeline_event` behandeln
- **MUSS [MUST]** `tts_response_finished` aufrufen, sobald die TTS-Antwort fertig abgespielt ist, damit die Entity in den `IDLE`-State zurückkehrt — der Übergang `RESPONDING` → `IDLE` wird nicht automatisch ausgelöst
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus dem `AssistSatelliteEntityFeature`-Enum setzen und für `ANNOUNCE` die Methode `async_announce`, für `START_CONVERSATION` die Methode `async_start_conversation` implementieren — beide kehren erst zurück, wenn die Ansage fertig abgespielt ist
- **SOLLTE [SHOULD]** `async_get_configuration` eine (gecachte) `AssistSatelliteConfiguration` liefern lassen und für die Geräte-Kommunikation während der Initialisierung sorgen

### AI-Task (`ai_task`)

- **MUSS [MUST]** eine AI-Task-Entity verwenden, wenn AI-gestützte Aufgaben (Daten/Inhalte aus natürlichsprachlichen Anweisungen) ausgeführt werden sollen
- **MUSS [MUST]** die Entity von `AITaskEntity` (`homeassistant.components.ai_task.AITaskEntity`) ableiten
- **MUSS [MUST]** `supported_features` als bitweise-`|`-Kombination aus dem `AITaskEntityFeature`-Enum setzen und für `GENERATE_DATA` die Methode `_async_generate_data` implementieren, die ein `GenDataTaskResult` mit `conversation_id` und `data` zurückgibt
- **MUSS [MUST]** `_async_generate_image` nur implementieren, wenn `AITaskEntityFeature.GENERATE_IMAGE` gesetzt ist — die Doku ruft die Methode genau dann auf
- **SOLLTE [SHOULD]** den `chat_log` zur Erhaltung des Gesprächskontexts nutzen; ein gemeinsamer Verarbeitungspfad zwischen Conversation- und AI-Task-Entity (siehe `ha/intents-conversation`) ist das von der Doku empfohlene Muster
- **SOLLTE [SHOULD]** bei gesetztem `task.structure` die strukturierte Ausgabe über das Selector-System validieren und nur bei fehlender Struktur den rohen Text zurückgeben

### Notify (`notify`)

- **MUSS [MUST]** eine Notify-Entity verwenden, wenn eine Nachricht an ein Gerät oder einen Dienst gesendet wird (SMS, E-Mail, Chat-Nachricht, LCD-Anzeige) — die Plattform ist die entity-basierte Ablösung der Legacy-`notify`-Plattform
- **MUSS [MUST]** die Entity von `NotifyEntity` (`homeassistant.components.notify.NotifyEntity`) ableiten
- **MUSS [MUST]** `async_send_message` (oder die synchrone Variante `send_message`) mit der Signatur `(message: str, title: str | None = None)` implementieren
- **MUSS NICHT [MUST NOT]** für eine Notify-Entity einen setzbaren State annehmen — ihr State ist der Zeitstempel der letzten gesendeten Nachricht; für einen änderbaren Textwert ist eine `text`-Entity zu verwenden
- **MUSS NICHT [MUST NOT]** extern erzeugte Notifications über `_async_record_notification` aufzeichnen — nur aus Home Assistant stammende Notifications dürfen aufgezeichnet werden; für externe ist eine `event`-Entity zu verwenden

### Konsistenz Plattform-Basisklasse ↔ Required-Vertrag

- **MUSS [MUST]** für jede der sechs Plattformen die korrekte Basisklasse wählen und genau ihren Required-Vertrag (Properties + Methoden) erfüllen — die Plattform-Docs koppeln Basisklasse und Pflicht-Member eins-zu-eins
- **MUSS [MUST]** für jedes gesetzte Feature-Flag (`AssistSatelliteEntityFeature`, `AITaskEntityFeature`) die korrespondierende Methode bereitstellen — ein beworbenes, aber nicht implementiertes Feature bricht die Pipeline- bzw. AI-Task-Anbindung
- **MUSS NICHT [MUST NOT]** generisches Entity-Pattern, Conversation-/Intent-Logik oder LLM-Tool-Exposition in diese Plattform-Entitäten kopieren — diese gehören in `ha/entity-architecture`, `ha/intents-conversation` bzw. `ha/llm-api`
- **SOLLTE [SHOULD]** die entity-basierte Plattform der Legacy-Plattform (`notify`/`stt`/`tts` als Plattform-Modul) vorziehen, da diese Specs den modernen Ersatz beschreiben

## Akzeptanzkriterien

- [ ] Jede Voice-/AI-Capability ist auf der semantisch passenden Plattform abgebildet (Audio→Text → `stt`, Text→Audio → `tts`, Wake-Word → `wake_word`, Satellit → `assist_satellite`, AI-Generierung → `ai_task`, Nachricht → `notify`)
- [ ] Jede Entity erbt von der korrekten Basisklasse (`SpeechToTextEntity`, `TextToSpeechEntity`, `WakeWordDetectionEntity`, `AssistSatelliteEntity`, `AITaskEntity`, `NotifyEntity`)
- [ ] `stt` setzt `supported_languages`, `supported_formats`/`supported_codecs` (plus bit-rates/sample-rates/channels) und implementiert `async_process_audio_stream`
- [ ] `tts` setzt `supported_languages` + `default_language` und implementiert `async_get_tts_audio`; `async_stream_tts_audio` ist optional ergänzt
- [ ] `wake_word` setzt `supported_wake_words` und implementiert `async_process_audio_stream` mit `DetectionResult`/`queued_audio`-Rückgabe
- [ ] `assist_satellite` setzt `AssistSatelliteEntityFeature` korrekt, implementiert `async_announce`/`async_start_conversation` zu den gesetzten Flags und ruft `tts_response_finished` auf
- [ ] `ai_task` setzt `AITaskEntityFeature.GENERATE_DATA` und implementiert `_async_generate_data` (Bild-Methode nur bei `GENERATE_IMAGE`)
- [ ] `notify` implementiert `async_send_message`; kein setzbarer State; keine extern erzeugten Notifications aufgezeichnet
- [ ] Für jedes gesetzte Feature-Flag existiert die korrespondierende Methode; keine „auf Vorrat" gesetzten Flags
- [ ] Generisches Entity-Pattern, Conversation-/Intent-Logik und LLM-Tool-Exposition sind nicht dupliziert, sondern an `ha/entity-architecture`, `ha/intents-conversation`, `ha/llm-api` delegiert
- [ ] Properties führen kein I/O aus (gilt für `stt` und `wake_word` ausdrücklich)

## Offene Fragen

- **Pipeline-Verdrahtung**: Diese Spec adressiert die Entity-Plattformen, nicht den Aufbau der Assist-Pipeline selbst. Gehört eine Pipeline-/VAD-Verdrahtungs-Konvention in eine eigene Folge-Spec (`ha/assist-pipeline`) oder bleibt sie außerhalb des Plugin-Scopes?
- **AI-Task ↔ Conversation gemeinsamer Pfad**: Die Doku empfiehlt einen geteilten `chat_log`-Verarbeitungspfad zwischen Conversation- und AI-Task-Entity. Soll der Skill diesen geteilten Pfad generieren, oder bleibt die Kopplung an `ha/intents-conversation` rein referenziell?
- **Legacy-Migration**: Soll die Spec eine Migrations-Konvention von den Legacy-`notify`/`stt`/`tts`-Plattform-Modulen zu den entity-basierten Plattformen vorschreiben, oder genügt die Empfehlung, neu entity-basiert zu starten?
- **Stimmen-/Optionen-Translations**: `tts` bietet `supported_options`/`default_options` und `async_get_supported_voices`. Gehört eine Translation-Key-Konvention für deren Beschriftung in diese Spec oder nach `ha/translations`?
- **Satelliten-Select-Entitäten**: `assist_satellite` referenziert `pipeline_entity_id` und `vad_sensitivity_entity_id` auf `select`-Entitäten. Soll die Spec deren Bereitstellung vorschreiben, oder bleibt das gerätespezifisch und optional?
