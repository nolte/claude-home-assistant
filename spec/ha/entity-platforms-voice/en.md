# HA Integration: Entity Platforms (Voice & AI)

Status: draft

## Context

Home Assistant provides dedicated entity platforms for voice and AI capabilities whose base classes differ from the generic entity architecture: speech-to-text, text-to-speech, wake-word detection, Assist satellites, AI tasks, and notifications. Each of these platforms is the **modern, entity-based replacement** for the corresponding legacy platform (`notify`, `stt`, `tts` as platform modules) and is declared through its own base class with a clearly defined set of required properties and required methods. This spec is the **concrete catalog** for exactly these six platforms.

The generic entity pattern — base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, the `EntityDescription` pattern, entity categories, and coordinator binding — is fixed in `ha/entity-architecture` and is **not repeated here**. The typed sensor/actuator platforms (`sensor`, `binary_sensor`, `climate`, `light`, `cover`) with `device_class`, `state_class`, and `supported_features` live in `ha/entity-platform-types`. The **conversation entity and the intent API** live in `ha/intents-conversation`; the **LLM tool API** lives in `ha/llm-api`. This spec references those specs by slug and does not duplicate them.

Each platform is determined by three questions: which capability it models and when it is the right choice, which base class the entity derives from, and which properties/methods the platform docs mark as **Required**. This spec lifts the six platform docs into a generic obligation for skill output.

## Goals

- Bind platform choice to the voice/AI capability — audio→text → `stt`, text→audio → `tts`, wake word → `wake_word`, satellite device → `assist_satellite`, AI generation → `ai_task`, outbound message → `notify`
- Have every voice/AI entity derive from the correct platform base class (`SpeechToTextEntity`, `TextToSpeechEntity`, `WakeWordDetectionEntity`, `AssistSatelliteEntity`, `AITaskEntity`, `NotifyEntity`)
- Fully implement the properties and methods documented as **Required** per platform
- Set feature flags (`AssistSatelliteEntityFeature`, `AITaskEntityFeature`) only when the corresponding method is implemented
- Use the entity-based platforms as the replacement for the legacy `notify`/`stt`/`tts` platform modules
- Wire generated code so it integrates and runs in the Assist pipeline and the notify/AI-task system

## Non-Goals

- Generic entity pattern (base class, `_attr_has_entity_name`, `translation_key`, `unique_id`, `EntityDescription` pattern, entity categories, coordinator binding) — fully in `ha/entity-architecture`; this spec only references it
- Typed sensor/actuator platforms (`sensor`, `binary_sensor`, `climate`, `light`, `cover`) with `device_class`/`state_class`/`supported_features` — separate `ha/entity-platform-types` spec
- The conversation entity and the intent API (intent handling, voice-command resolution) — separate `ha/intents-conversation` spec
- The LLM tool API (tool exposure for language models) — separate `ha/llm-api` spec
- HA translation format (`strings.json` shape, `entity.<platform>.<key>.name`) — separate `ha/translations` spec
- Building the Assist pipeline itself and the VAD configuration in detail — this spec addresses only the entity platforms that plug into the pipeline

## Requirements

### Speech-to-text (`stt`)

- **MUST** use a speech-to-text entity when audio is to be streamed and text returned — the STT docs define this platform as a streaming API for other integrations or applications
- **MUST** derive the entity from `SpeechToTextEntity` (`homeassistant.components.stt.SpeechToTextEntity`)
- **MUST** provide all properties documented as **Required**: `supported_languages` (`list[str]`), `supported_formats` (`list[AudioFormats]`, wav or ogg), `supported_codecs` (`list[AudioCodecs]`, pcm or opus), `supported_bit_rates`, `supported_sample_rates`, and `supported_channels` (1 or 2)
- **MUST** implement `async_process_audio_stream` to send audio to the STT service and return text — the docs allow streaming content only
- **MUST NOT** perform I/O (e.g. network requests) in properties — the STT docs require that properties only return from memory

### Text-to-speech (`tts`)

- **MUST** use a text-to-speech entity when Home Assistant is to produce spoken responses — the TTS docs define this platform as "enables Home Assistant to speak to you"
- **MUST** derive the entity from `TextToSpeechEntity` (`homeassistant.components.tts.TextToSpeechEntity`)
- **MUST** provide the properties documented as **Required**: `supported_languages` (`list[str]`) and `default_language` (`str`)
- **MUST** implement the 1-shot method `async_get_tts_audio` (or its synchronous variant `get_tts_audio`) — the TTS docs mark it as "mandatory to implement"
- **MAY** additionally implement `async_stream_tts_audio` to stream text chunks (for example from a language model) into audio chunks — when absent, the service calls the 1-shot method with the final message
- **MAY** set `async_get_supported_voices`, `supported_options`, and `default_options` to offer voices/options per language

### Wake-word detection (`wake_word`)

- **MUST** use a wake-word detection entity when wake words (hotwords) are to be detected in an audio stream
- **MUST** derive the entity from `WakeWordDetectionEntity` (`homeassistant.components.wake_word.WakeWordDetectionEntity`)
- **MUST** provide the property documented as **Required**: `supported_wake_words` (`list[WakeWord]`), each with `ww_id` (unique identifier) and `name` (human-readable)
- **MUST** implement `async_process_audio_stream` and return a `DetectionResult` (or `None` when the stream ends without a detection) — the input is 16-bit mono PCM at 16 kHz
- **MUST** in an Assist pipeline return audio chunks removed during detection via the `queued_audio` of the `DetectionResult`, otherwise speech-to-text cannot process them
- **MUST NOT** perform I/O in properties — the wake-word docs require that properties only return from memory

### Assist satellite (`assist_satellite`)

- **MUST** use an Assist satellite entity when a device represents the Assist-pipeline-powered voice-assistant capabilities (voice control of Home Assistant)
- **MUST** derive the entity from `AssistSatelliteEntity` (`homeassistant.components.assist_satellite.AssistSatelliteEntity`)
- **MUST** run a pipeline only via `async_accept_pipeline_from_satellite` and handle pipeline events via `on_pipeline_event`
- **MUST** call `tts_response_finished` once the TTS response has finished playing so the entity returns to the `IDLE` state — the `RESPONDING` → `IDLE` transition is not triggered automatically
- **MUST** set `supported_features` as a bitwise `|` combination from the `AssistSatelliteEntityFeature` enum and implement `async_announce` for `ANNOUNCE` and `async_start_conversation` for `START_CONVERSATION` — both return only once the announcement has finished playing
- **SHOULD** have `async_get_configuration` return a (cached) `AssistSatelliteConfiguration` and perform any device communication during initialization

### AI task (`ai_task`)

- **MUST** use an AI task entity when AI-powered tasks (data/content from natural-language instructions) are to be executed
- **MUST** derive the entity from `AITaskEntity` (`homeassistant.components.ai_task.AITaskEntity`)
- **MUST** set `supported_features` as a bitwise `|` combination from the `AITaskEntityFeature` enum and implement `_async_generate_data` for `GENERATE_DATA`, returning a `GenDataTaskResult` with `conversation_id` and `data`
- **MUST** implement `_async_generate_image` only when `AITaskEntityFeature.GENERATE_IMAGE` is set — the docs call the method exactly then
- **SHOULD** use the `chat_log` to maintain conversation context; a shared processing path between conversation and AI-task entities (see `ha/intents-conversation`) is the pattern the docs recommend
- **SHOULD** validate the structured output via the selector system when `task.structure` is set, and return the raw text only when no structure is present

### Notify (`notify`)

- **MUST** use a notify entity when a message is sent to a device or service (SMS, email, chat message, LCD display) — the platform is the entity-based replacement for the legacy `notify` platform
- **MUST** derive the entity from `NotifyEntity` (`homeassistant.components.notify.NotifyEntity`)
- **MUST** implement `async_send_message` (or the synchronous variant `send_message`) with the signature `(message: str, title: str | None = None)`
- **MUST NOT** assume a settable state for a notify entity — its state is the timestamp of the last message sent; for a changeable text value use a `text` entity
- **MUST NOT** record externally generated notifications via `_async_record_notification` — only notifications originating from within Home Assistant may be recorded; for external ones use an `event` entity

### Platform base class ↔ required-contract consistency

- **MUST** choose the correct base class for each of the six platforms and fulfill exactly its required contract (properties + methods) — the platform docs couple base class and mandatory members one-to-one
- **MUST** provide the corresponding method for every set feature flag (`AssistSatelliteEntityFeature`, `AITaskEntityFeature`) — an advertised but unimplemented feature breaks the pipeline or AI-task integration
- **MUST NOT** copy generic entity pattern, conversation/intent logic, or LLM tool exposure into these platform entities — those belong in `ha/entity-architecture`, `ha/intents-conversation`, and `ha/llm-api` respectively
- **SHOULD** prefer the entity-based platform over the legacy platform (`notify`/`stt`/`tts` as a platform module), since these specs describe the modern replacement

## Acceptance Criteria

- [ ] Every voice/AI capability is modeled on the semantically appropriate platform (audio→text → `stt`, text→audio → `tts`, wake word → `wake_word`, satellite → `assist_satellite`, AI generation → `ai_task`, message → `notify`)
- [ ] Every entity derives from the correct base class (`SpeechToTextEntity`, `TextToSpeechEntity`, `WakeWordDetectionEntity`, `AssistSatelliteEntity`, `AITaskEntity`, `NotifyEntity`)
- [ ] `stt` sets `supported_languages`, `supported_formats`/`supported_codecs` (plus bit-rates/sample-rates/channels) and implements `async_process_audio_stream`
- [ ] `tts` sets `supported_languages` + `default_language` and implements `async_get_tts_audio`; `async_stream_tts_audio` is optionally added
- [ ] `wake_word` sets `supported_wake_words` and implements `async_process_audio_stream` returning `DetectionResult`/`queued_audio`
- [ ] `assist_satellite` sets `AssistSatelliteEntityFeature` correctly, implements `async_announce`/`async_start_conversation` for the set flags, and calls `tts_response_finished`
- [ ] `ai_task` sets `AITaskEntityFeature.GENERATE_DATA` and implements `_async_generate_data` (image method only with `GENERATE_IMAGE`)
- [ ] `notify` implements `async_send_message`; no settable state; no externally generated notifications recorded
- [ ] For every set feature flag the corresponding method exists; no flags set "on spec"
- [ ] Generic entity pattern, conversation/intent logic, and LLM tool exposure are not duplicated but delegated to `ha/entity-architecture`, `ha/intents-conversation`, `ha/llm-api`
- [ ] Properties perform no I/O (explicitly for `stt` and `wake_word`)

## Open Questions

- **Pipeline wiring**: This spec addresses the entity platforms, not building the Assist pipeline itself. Does a pipeline/VAD wiring convention belong in a separate follow-up spec (`ha/assist-pipeline`), or does it stay outside the plugin scope?
- **AI-task ↔ conversation shared path**: The docs recommend a shared `chat_log` processing path between conversation and AI-task entities. Should the skill generate this shared path, or does the coupling to `ha/intents-conversation` stay purely referential?
- **Legacy migration**: Should the spec prescribe a migration convention from the legacy `notify`/`stt`/`tts` platform modules to the entity-based platforms, or does recommending an entity-based start suffice?
- **Voice/options translations**: `tts` offers `supported_options`/`default_options` and `async_get_supported_voices`. Does a translation-key convention for their labels belong in this spec or in `ha/translations`?
- **Satellite select entities**: `assist_satellite` references `pipeline_entity_id` and `vad_sensitivity_entity_id` on `select` entities. Should the spec prescribe providing them, or does that stay device-specific and optional?
