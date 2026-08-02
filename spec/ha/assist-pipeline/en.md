# HA Voice: Assist Pipeline (Configuration and Operation)

Status: draft

## Context

The **Assist pipeline** is the Home Assistant side of voice control: the ordered chain that turns a spoken utterance into an executed action and a spoken reply. It runs in four stages — **wake word → speech-to-text → intent → text-to-speech** — and is provided by the internal `assist_pipeline` integration, introduced in Home Assistant **2023.5** and part of `default_config` `[doc:user]` `[doc:dev]`.

The pipeline is where voice control actually succeeds or fails. A voice satellite such as the ESP32-S3-BOX contributes microphones, a wake-word model, and a speaker; everything that determines whether a command is *understood* — which speech-to-text engine runs, which entities the agent may touch, which sentences match, how the answer is spoken — lives in Home Assistant. A perfectly configured satellite in front of an unconfigured pipeline is a mute device.

This spec is deliberately the **operator's** view of that machinery: how a pipeline is composed, which engine choices exist and what they cost, how entities are exposed to it, how satellites bind to it, and how a failing pipeline is debugged. It complements three existing developer-facing specs and overlaps none of them:

- [`ha/intents-conversation`](../intents-conversation/en.md) — the developer API (`IntentHandler`, slots, `ConversationEntity`). That spec explicitly excludes "end-user Assist configuration (exposing entities in the UI, voice pipeline setup)" — precisely the gap this one fills.
- [`ha/entity-platforms-voice`](../entity-platforms-voice/en.md) — the entity base classes an integration implements to *become* an STT, TTS, wake-word, or satellite provider.
- [`ha/llm-api`](../llm-api/en.md) — registering and consuming LLM tool APIs for conversation agents.

The device side of a satellite — microphones, codecs, wake-word component, display feedback — belongs to [`ha/esp32-s3-box`](../esp32-s3-box/en.md) and is referenced here, not restated.

### Source tiers

Every non-obvious claim carries an evidence tier:

- `[doc:user]` — the official user documentation, [`home-assistant/home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (`/voice_control/*`, `/integrations/*`): authoritative for setup procedures, UI paths, and end-user behaviour.
- `[doc:dev]` — the official developer documentation, [`home-assistant/developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant) (`/docs/voice/*`): authoritative for pipeline stages, events, and the WebSocket contract.
- `[policy]` — a nolte-portfolio rule, not an upstream fact.

Verified 2026-08.

## Goals

- Describe the pipeline as an ordered, observable contract — stages, events, and the parameters that select a subset of them — instead of as an opaque UI toggle
- Make the engine choices (speech-to-text, text-to-speech, wake word, conversation agent) explicit decisions with their documented costs, rather than defaults nobody revisited
- Fix where wake-word detection runs and what that placement implies for hardware load, language coverage, and offline behaviour
- Treat entity exposure as a security boundary with a stated minimum, not as a convenience switch
- Bind satellites to pipelines through the current entity model (`assist_satellite`) and name the deprecation that older configurations must migrate off
- Give a failing pipeline a deterministic debugging path — which tool answers which question — instead of trial and error
- Name the privacy consequences of the pipeline's own diagnostics, especially audio recording

## Non-Goals

- The developer API for intents, conversation agents, and voice entity platforms — owned by `ha/intents-conversation`, `ha/entity-platforms-voice`, and `ha/llm-api`
- Satellite hardware and its ESPHome binding — owned by `ha/esp32-s3-box`; this spec treats a satellite as a pipeline client
- Add-on installation mechanics and Home Assistant OS administration beyond stating where a Supervisor requirement exists
- Choosing or operating a specific LLM provider (model selection, prompt engineering, cost) — the spec covers *that* an agent is selected and what changes, not which vendor
- Speech-model training beyond noting that custom wake-word training exists
- Home Assistant Cloud subscription and billing questions — Cloud appears only as one documented engine option
- Multi-room audio, media routing, and announcement scheduling beyond the actions the satellite exposes

## Requirements

### Pipeline anatomy

- **MUST** treat a pipeline as an ordered chain of exactly four stages — **wake word**, **speech-to-text**, **intent recognition**, **text-to-speech** — executed in that order `[doc:dev]` `[doc:user]`
- **MUST** understand that a run may cover a **subset** of the chain: the WebSocket API's `start_stage` and `end_stage` parameters select the range, so a text-only run (`intent` → `intent`) and a full voice run share the same pipeline definition `[doc:dev]`
- **SHOULD** treat the run's **events** as the observable contract when integrating or debugging: `run-start`, `wake_word-start`/`wake_word-end`, `stt-start`, `stt-vad-start`/`stt-vad-end`, `stt-end`, `intent-start`/`intent-progress`/`intent-end`, `tts-start`/`tts-end`, `run-end`, and `error` with a specific error code `[doc:dev]`
- **SHOULD** know that a run accepts optional `pipeline` (id), `conversation_id`, `device_id`, and timeout parameters — the `conversation_id` is what makes a follow-up turn part of the same conversation `[doc:dev]`
- **MAY** rely on `assist_pipeline` being present via `default_config`; adding `assist_pipeline:` to `configuration.yaml` is only needed where the default configuration was stripped `[doc:user]`
- **MUST NOT** assume a pipeline is device-specific: pipelines are named configurations that many satellites can share, and one satellite is assigned one pipeline `[doc:user]`

### Engine selection

- **MUST** decide **local versus cloud** deliberately and record the decision — Home Assistant Cloud provides speech-to-text and text-to-speech as a subscription service, while a fully local pipeline is assembled from add-ons `[doc:user]`
- **MUST** choose a speech-to-text engine against the host's actual capacity **and against the features the assistant needs**: **Speech-to-Phrase** delivers "extremely fast transcription even on a Home Assistant Green or Raspberry Pi 4 (under one second)" but "only supports a subset of Assist's voice commands" — the documentation names shopping lists, **naming a timer**, and broadcasts as "*not* usable out of the box". **Whisper** handles freer speech at a documented ~8 seconds on a Pi 4 versus under 1 second on an Intel NUC. Note the consequence for this portfolio: a satellite built on [`ha/esp32-s3-box`](../esp32-s3-box/en.md) leans on the timer intents, so Speech-to-Phrase constrains that device's headline feature `[doc:user]` `[policy]`
- **SHOULD** use **Piper** as the local text-to-speech engine; it is the documented local option, "optimized for the Raspberry Pi 4", generating "1.6s of voice in a second" on a Raspberry Pi with medium-quality models — a throughput figure worth holding against the length of the responses a device actually speaks `[doc:user]`
- **MUST** understand that these engines attach through the **Wyoming** protocol integration, which connects external speech-to-text, text-to-speech, and wake-word services and auto-discovers running instances (manual host/port entry remains available) `[doc:user]`
- **MUST** account for the **Supervisor requirement**: the engines ship as Home Assistant apps (formerly add-ons), which presupposes Home Assistant OS or Supervised — Home Assistant Core cannot install them and needs externally hosted Wyoming services instead. The documented escape hatch is concrete rather than theoretical: openWakeWord is published as a Docker container, and the Wyoming integration is then pointed at its address and port (typically 10400) `[doc:user]` `[policy]`
- **SHOULD** assemble the pipeline in the documented order — install and start the speech-to-text and text-to-speech services, integrate them under *Settings → Devices & Services*, then create the assistant under *Settings → Voice assistants → Add assistant* and select language and engines `[doc:user]`
- **MUST** create **one pipeline per language** rather than overloading a single pipeline, since language and engine selection are per-pipeline settings; each satellite is then assigned the pipeline of the language actually spoken in its room `[doc:user]` `[policy]`

### Wake-word placement

- **MUST** decide **where** wake-word detection runs, because the two placements have different costs — this is an architectural decision, not a preference `[doc:user]`
- **SHOULD** prefer **on-device** detection (`microWakeWord`) for battery- or network-constrained satellites: only post-detection audio is sent, it works without network connectivity, and it ships exactly three pre-trained models — "okay nabu", "hey jarvis", and "alexa" — at the cost of smaller models with less accuracy headroom. The reason the choice exists at all is stated outright: openWakeWord "is too large to run on low-power devices like the S3-BOX-3". Note also that Home Assistant's documentation describes the S3-BOX and S3-BOX-Lite as "now discontinued", which [`ha/esp32-s3-box`](../esp32-s3-box/en.md) should reflect when it calls all three generations current `[doc:user]`
- **SHOULD** choose **server-side** detection (`openWakeWord`) when any audio-streaming device must become a satellite regardless of its compute — accepting that satellites then stream continuously `[doc:user]`
- **MUST** budget server-side detection against the host: the documentation states a Raspberry Pi 4 handles about **five simultaneous** audio streams before being overwhelmed `[doc:user]`
- **MUST** account for language coverage before choosing server-side detection: openWakeWord currently supports **English only**, owing to limited multi-speaker models elsewhere; the alternative **Porcupine (v1)** engine offers 29 wake words across English, French, Spanish, and German `[doc:user]`
- **MUST** meet the stated prerequisites when running wake word in Home Assistant: version **2023.10 or later** on Home Assistant OS, plus Cloud or a configured local pipeline; the wake word is then attached to the assistant via *Add streaming wake word* `[doc:user]`
- **MAY** train a custom wake word — the openWakeWord tooling synthesises training data with text-to-speech across speaker, room-acoustic, and noise variations, so no manual recording campaign is required `[doc:user]`

### Entity exposure

- **MUST** treat exposure as a **security boundary**: entities are opted in under *Settings → Voice assistants → Expose*, explicitly "to avoid that sensitive devices, such as locks and garage doors, can inadvertently be controlled by voice commands" `[doc:user]`
- **MUST** expose the **minimum** set an assistant genuinely needs, and re-review it whenever new devices are added — an exposed entity is reachable by anyone within earshot of a satellite `[doc:user]` `[policy]`
- **MUST NOT** expose locks, garage doors, alarm control panels, or other consequential actuators to a voice assistant without an explicit, recorded decision `[policy]`
- **SHOULD** assign **aliases** to entities whose registered name is not what a person would say aloud, instead of renaming the entity and breaking existing automations `[doc:user]` `[policy]`
- **SHOULD** keep exposure per-assistant deliberate: the expose UI selects which assistants (Assist, Google Assistant, Alexa) receive each entity, and these are independent decisions `[doc:user]`
- **SHOULD** verify exposure changes with the sentence parser rather than by voice, so a missing match is distinguished from a misheard word `[doc:user]` `[policy]`

### Conversation agent and sentences

- **MUST** know that the **default agent** matches community-contributed sentences across dozens of languages and needs no configuration for common commands — turning devices on and off by name or area works out of the box `[doc:user]`
- **SHOULD** cover built-in capability before writing custom sentences: lights (on/off, brightness, colour), covers, scenes and scripts, media players, vacuums, generic on/off, shopping and to-do lists, and date/time and state questions are all handled by built-in intents `[doc:user]`
- **SHOULD** rely on the built-in **timer intents** rather than modelling timers separately — creating ("set a timer for 5 minutes"), cancelling, adding or removing time, querying remaining time, and delayed actions ("turn off the lights in 5 minutes") are covered `[doc:user]`
- **SHOULD** add a custom phrase through the **sentence trigger** in an automation (*Settings → Automations & Scenes → Create automation*, trigger type *Sentence*, phrases entered without punctuation) when the goal is one phrase driving one automation — this is the documented easiest path `[doc:user]`
- **MAY** define reusable custom intents as YAML under `custom_sentences/<language>/` in the config directory, declaring `language:` and an `intents:` mapping of intent name → `data:` → `sentences:`, and handle them with `intent_script` `[doc:user]`
- **MAY** extend an **existing** intent with additional sentence variations rather than creating a new intent, and customise the spoken response of an existing intent `[doc:user]`
- **SHOULD** capture variable parts with wildcards (`{album}`) and consume them in the response or action via `trigger.slots` templating, instead of enumerating every phrasing `[doc:user]`
- **MAY** replace the default agent with a custom or LLM-backed conversation agent; when doing so, the tool surface exposed to the model is governed by [`ha/llm-api`](../llm-api/en.md) and the exposure rules above still apply `[doc:user]` `[policy]`
- **MAY** drive the pipeline from automations with the `conversation.process` action, and reload sentence configuration with `conversation.reload` `[doc:user]`

### Speech output

- **SHOULD** speak text outside a pipeline run with the `tts.speak` action, targeting a `media_player_entity_id` with `message`, and optionally `language`, `cache`, and `options` `[doc:user]`
- **MAY** constrain the generated audio through `options` — `preferred_format` (`wav`, `mp3`, `ogg`), `preferred_sample_rate`, `preferred_sample_channels`, and `preferred_sample_bytes` (`2` for 16-bit) — when the target device is picky about what it can play `[doc:user]`
- **SHOULD** leave `cache` at its default (`True`) for repeated phrases: Home Assistant keeps a long-lived filesystem cache plus a short-lived in-memory cache that is auto-cleaned `[doc:user]`
- **SHOULD** prefer `tts.speak` over the legacy `tts.<platform>_say` services in new configurations `[doc:user]` `[policy]`
- **MUST NOT** route a satellite's pipeline response through a manual `tts.speak` call — the pipeline's text-to-speech stage already delivers the reply to the satellite, and a second path produces doubled or overlapping audio `[doc:dev]` `[policy]`

### Satellite binding

- **MUST** represent a voice satellite through the **`assist_satellite` entity**, the building-block integration introduced in Home Assistant **2024.10** `[doc:user]`
- **MUST** migrate configurations that still consume the older ESPHome voice binary sensors: they are deprecated as of 2024.10 and Home Assistant raises a repair issue pointing at the corresponding `assist_satellite` entity `[doc:user]`
- **SHOULD** automate against the satellite's documented state model — the triggers *became idle*, *started listening*, *started processing*, and *started responding*, plus the matching conditions — rather than inferring pipeline state from media-player or microphone entities `[doc:user]`
- **MAY** push speech to a satellite with the documented actions: **announce**, **ask a question**, and **start a conversation** `[doc:user]`
- **MUST** assign each satellite a pipeline explicitly and verify the assignment after adding the device, rather than assuming the default assistant applies `[doc:user]` `[policy]`
- **SHOULD** take the device-side contract of an ESPHome satellite — microphone, wake word, media player, mute control, screen feedback — from [`ha/esp32-s3-box`](../esp32-s3-box/en.md) `[policy]`

### Audio quality

- **SHOULD** treat poor recognition as an **audio** problem before it is treated as an engine problem: recognition quality depends on the captured signal, and devices with a single microphone need compensating post-processing in Home Assistant `[doc:user]`
- **SHOULD** apply the documented starting values for quiet microphones — `noise_suppression_level: 2`, `auto_gain: 31dBFS`, `volume_multiplier: 2.0` — which are exactly the values the ESPHome reference configuration ships `[doc:dev]`
- **MUST** feed the pipeline audio at the rate it expects (the documented run input uses `sample_rate: 16000`) and keep the satellite's capture rate aligned with it `[doc:dev]`
- **SHOULD** tune gain **once** in the chain — on the device's audio ADC or through the pipeline's gain settings, not both — so a quiet speaker is not compensated twice into clipping `[policy]`

### Debugging

- **MUST** debug in this order — each tool answers a different question, and running them out of order wastes the most time `[doc:user]` `[policy]`:
  1. **Sentence parser** (*Developer tools*) — does the phrase match an intent at all? It reports the triggered intent, the targeted entities, and which of them matched, **without executing** the command
  2. **Pipeline debug** (*Settings → Voice assistants → \<assistant\> → Debug*) — run a phrase for real and inspect past runs from the dropdown
  3. **Debug recording** — set `assist_pipeline: {debug_recording_dir: /share/assist_pipeline}` in `configuration.yaml` to capture a `.wav` per command and judge the audio itself
- **SHOULD** map the symptom to the stage before changing anything: no reaction at all points at wake word, a wrong transcript at speech-to-text, "sorry, I don't understand" at intent matching or exposure, and a silent reply at text-to-speech `[doc:user]` `[policy]`
- **SHOULD** check **exposure** first when a device is not found — the documented failure mode for unanswered questions is an entity that was never exposed, not a misparsed sentence `[doc:user]`
- **MUST NOT** leave `debug_recording_dir` enabled beyond a time-boxed investigation, and **MUST** delete the captured `.wav` files along with the config key when it ends: it writes every spoken command to disk as audio, the most sensitive artefact the pipeline produces `[doc:user]` `[policy]`
- **SHOULD** record what was investigated and over which period whenever debug recording is enabled, so an audio capture is never found later without an explanation `[policy]`

### Privacy and operational constraints

- **MUST** state, per pipeline, whether audio leaves the network: a Cloud-backed speech-to-text or text-to-speech stage sends speech off-site, while a Wyoming-based local pipeline processes it locally `[doc:user]` `[policy]`
- **MUST** treat continuous streaming as the privacy-relevant consequence of server-side wake word: with `openWakeWord`, satellites stream audio to Home Assistant at all times, whereas on-device detection streams only after the wake word `[doc:user]` `[policy]`
- **SHOULD** size the host against the number of streaming satellites before adding more, using the documented five-stream guidance for a Raspberry Pi 4 as the reference point `[doc:user]`
- **SHOULD** provide a discoverable **mute** on every satellite and treat its absence as a defect — the device-side requirement lives in [`ha/esp32-s3-box`](../esp32-s3-box/en.md) `[policy]`
- **MUST** keep the exposed entity set and the pipeline's engine choices under review as part of normal maintenance, since both silently widen over time as devices and add-ons are added `[policy]`

### Verification

- **MUST** verify pipeline stages, run events, and the WebSocket contract against the developer documentation, and setup procedures, UI paths, and engine behaviour against the user documentation, per [`ha/upstream-docs-verification`](../upstream-docs-verification/en.md) `[policy]`
- **MUST** anchor version-dependent claims to the stated release — `assist_pipeline` from 2023.5, wake word in Home Assistant from 2023.10, the browser-based satellite installer from 2023.12, `assist_satellite` from 2024.10 — because each is a hard gate for a given setup `[doc:user]` `[policy]`
- **SHOULD** re-verify engine performance claims (transcription latency, simultaneous streams) when the host hardware differs from the documented reference devices, treating the published numbers as calibration points rather than guarantees `[doc:user]` `[policy]`
- **MUST NOT** treat community forum posts as authoritative for pipeline behaviour; they supplement the two official sources, never replace them `[policy]`

## Acceptance Criteria

- [ ] The pipeline's four stages and their order are understood, and a run's stage range is chosen deliberately where a subset is used
- [ ] Local-versus-cloud is a recorded decision, and the speech-to-text engine matches the host's documented capacity
- [ ] Where local engines are used, the Supervisor requirement is met or externally hosted Wyoming services are provided instead
- [ ] Wake-word placement (on-device versus server-side) is decided against language coverage, offline behaviour, and host load, with the five-stream guidance applied for streaming satellites
- [ ] Exposure is minimal and reviewed; no lock, garage door, or alarm entity is exposed without a recorded decision; aliases are used instead of renaming entities
- [ ] Built-in intents (including timers) are used before custom sentences are written; custom phrases use the sentence trigger or `custom_sentences/<language>/` with `intent_script`
- [ ] Each satellite is bound to an explicit pipeline, represented by an `assist_satellite` entity, with any deprecated voice binary sensors migrated
- [ ] Automations key off the satellite's documented state triggers rather than inferred entity states
- [ ] Speech output uses `tts.speak` with a deliberate `cache` and, where needed, `options`; no manual TTS call duplicates a pipeline response
- [ ] Audio tuning is applied once in the chain, with the documented starting values used for quiet microphones and a capture rate matching the pipeline input
- [ ] A failing pipeline is diagnosed with the sentence parser, then pipeline debug, then debug recording — in that order — and the symptom is mapped to a stage first
- [ ] `debug_recording_dir` is removed after the investigation and is not left enabled in a running configuration
- [ ] For each pipeline it is stated whether audio leaves the network, and every satellite offers a discoverable mute
- [ ] Version gates (2023.5 / 2023.10 / 2023.12 / 2024.10) are checked against the running Home Assistant version before a capability is promised

## Open Questions

- **Agent fallback**: when an LLM-backed conversation agent is configured, is there a local-first or fallback behaviour for commands the built-in intents already handle? Re-checked 2026-08 against the `conversation` integration page and a representative LLM agent page (`openai_conversation`) — **neither documents such an option**, so the question stays open by absence of documentation rather than by lack of looking. Settle it empirically (observe whether a built-in intent still fires with an LLM agent selected) before adopting an LLM agent portfolio-wide.
- **Engine sizing on the real host**: both the speech-to-text choice (Speech-to-Phrase versus Whisper) and the satellite count at which the host needs re-sizing depend on hardware this spec cannot see. The documented figures — ~8 s versus <1 s transcription, ~5 simultaneous streams on a Raspberry Pi 4 — are calibration points; **measure on the actual host** before fixing either as a portfolio rule.

Settled by decision (kept here so the rationale stays findable, not as open work): one pipeline **per language** with per-satellite assignment; **no** custom wake word, so detection stays on-device and audio leaves a satellite only after the wake word; `debug_recording_dir` is permitted **only** for a time-boxed investigation and its recordings are deleted afterwards; and entity exposure is re-reviewed **at every device onboarding** rather than on a calendar cadence, because onboarding is when exposure actually widens.
