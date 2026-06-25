# Skill: `ha-conversation-agent-augment`

Status: draft

## Context

`ha/intents-conversation` defines the developer-facing intent/conversation API: an integration registers an `IntentHandler` (derived from `homeassistant.helpers.intent.IntentHandler`, via `intent.async_register(hass, handler)`), sets `intent_type`, optionally declares a `slot_schema`, and implements `async_handle(intent_obj) -> IntentResponse`. Alternatively — or additionally — it provides its own conversation agent as a `conversation.ConversationEntity`, declares `supported_languages`, and processes messages in `_async_handle_message(user_input, chat_log) -> ConversationResult`. `ha/llm-api` defines the second, orthogonal axis: **exposing tools** to LLMs by registering an `llm.API` (derived from `API`) via `llm.async_register_api(hass, api)`, where `async_get_api_instance(llm_context) -> APIInstance` returns a list of `llm.Tool` objects plus an `api_prompt`. No skill augments these Voice & AI surfaces so far.

This skill augments **one existing** integration with one or more of these surfaces: intent handlers, a conversation agent, and/or LLM API tools — conformant to `ha/intents-conversation` **plus** `ha/llm-api`. Because three different surfaces are in play, the skill **first decides together with the user** which surface(s) are in scope, and keeps the axes (intents/conversation from `ha/intents-conversation`, tools from `ha/llm-api`) cleanly separated.

## Scope

Augmenting one or more Voice & AI surfaces into an existing `custom_components/<domain>/` integration: (a) intent handlers (`IntentHandler` subclasses with `intent.async_register`, `slot_schema`, `async_handle`); (b) a conversation platform (`conversation.py` with a `ConversationEntity`, `supported_languages`, `_async_handle_message`); and/or (c) LLM API tools (`llm.Tool` subclasses + an `llm.API` via `llm.async_register_api` with `async_get_api_instance` → `APIInstance`). The skill reads `ha/intents-conversation` and `ha/llm-api` and validates.

## Goals

- Decide with the user which surface(s) are in scope (intents vs. conversation entity vs. LLM tools) before generating anything — keep the two axes explicitly separated
- Augment intent handlers spec-conformantly: derived from `IntentHandler`, registered via `intent.async_register`, `intent_type` set, a `slot_schema` for expected slots, `async_handle` returning an `IntentResponse`
- Implement domain-appropriate built-in intents (`HassTurnOn`/`HassTurnOff`/`HassGetState`) rather than only proprietary intents, and re-implement no deprecated intents
- Provide a conversation agent as a `ConversationEntity` with `supported_languages` and `_async_handle_message(...) -> ConversationResult`, rather than using the deprecated `async_process` pattern
- Declare LLM tools as `llm.Tool` subclasses with `name`, a `parameters` schema, and an async `async_call`, register them via an `llm.API`, unregister on unload, and signal errors as `HomeAssistantError`
- Keep localized sentences and response texts out of handler/tool code and delegate them to the language artefacts

## Non-Goals

- Assist satellite, STT, TTS, or wake-word **entities** (`assist_satellite`/`stt`/`tts`/`wake_word`) — `ha/entity-platforms-voice`
- Registered services with their own schema — `ha-service-definition-generator` / `ha/services` (tools are called by the LLM, services are user-driven)
- Translation of intent sentences (`intents/<lang>.yaml`) and response/prompt texts — `ha/translations`
- End-user Assist configuration (exposing entities in the UI, voice pipeline setup) — user documentation, not developer API
- Greenfield scaffolding of an integration — `ha-integration-scaffold`
- The provider-side LLM wiring (streaming, message formatting, tool serialization) — outside this spec

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "add a conversation agent", "register intents", "expose tools to the assistant via the LLM API"
  - "let my integration respond to Assist sentences", "add a custom intent handler"
  - "füge einen Conversation-Agent / Intents / LLM-Tools hinzu"

### Inputs

- **MUST** capture: `target_dir` (repo root) and the desired Voice & AI capability (prose), from which the skill derives the surface(s) and their contracts
- **MUST** capture the scope decision: which surface(s) — intents, conversation entity, and/or LLM tools
- **MAY** capture: the concrete `intent_type` names and slots, `supported_languages`, plus tool names, `description`, and the `parameters` schema

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`
- **MUST** make the scope decision with the user: which of the three surfaces (intents / conversation entity / LLM tools) are in scope; for LLM tools the role **MUST** additionally be fixed — **exposing** tools (register an `llm.API`) vs. **consuming** an API (pull tools from the `ChatLog`)
- **MUST** read the `ha/intents-conversation` and `ha/llm-api` specs (at least the applicable one per scope)
- **MUST NOT** overwrite an existing `intent_type`, an existing conversation entity, or a registered `llm.API` `id`; on collision abort

### Generation rules (per surface)

- **MUST** for intent handlers derive every handler class from `homeassistant.helpers.intent.IntentHandler`, set `intent_type` as a string, register it via `intent.async_register(hass, handler)` in `async_setup`/`async_setup_entry` (not in platform modules), and implement `async_handle(self, intent_obj) -> IntentResponse` — never return `None` or a raw string
- **MUST** read slot values through `intent_obj.slots["<name>"]["value"]` and declare a `slot_schema` for expected slots
- **SHOULD** implement the domain-appropriate built-in intents (`HassTurnOn`/`HassTurnOff`/`HassGetState`) and treat the slots for `HassTurnOn`/`HassTurnOff` as optional; **MUST NOT** re-implement deprecated intents (`HassToggle`, `HassOpenCover`, …)
- **MUST** create the response through `intent_obj.create_response()` + `response.async_set_speech(...)`, deliver speech only as `plain` or `ssml`, set the correct `response_type` (`action_done`/`query_answer`/`error`), and assign a valid `data.code` (`no_intent_match`/`no_valid_targets`/`failed_to_handle`/`unknown`) in the error case
- **MUST** for a conversation agent create `conversation.py` with an entity derived from `conversation.ConversationEntity`, declare `supported_languages` (`list[str]` or `"*"`), and implement `_async_handle_message(self, user_input, chat_log) -> ConversationResult` (instead of the deprecated `async_process`); set `ConversationEntityFeature.CONTROL` only when the agent actually controls HA; **MUST NOT** perform I/O in property getters
- **MUST** for exposed LLM tools create a class inheriting from `API` and implement `async_get_api_instance(self, llm_context) -> APIInstance` (with `api`, `api_prompt` (required), `llm_context`, `tools`); register the API via `llm.async_register_api(hass, api)` with a unique `id`/`name` and unregister the return value via `entry.async_on_unload(unreg)`
- **MUST** derive every tool from `llm.Tool`, carry a `name` attribute, implement async `async_call(self, hass, tool_input, llm_context)`, return a JSON-serializable `JsonObjectType` result, and raise errors as `HomeAssistantError` — no in-band error codes in the response
- **SHOULD** set a `description` attribute and a voluptuous `parameters` schema for tools, and when consuming hold the selected API IDs under `CONF_LLM_HASS_API` in the options and resolve the API via `llm.async_get_api(hass, api_id, llm_context)`
- **MUST** keep localized sentences/response/prompt texts out of handler/tool code (sentences in `intents/<lang>.yaml`, `ha/translations`), name identifiers per `ha/naming-conventions`, and verify HA internals against the official docs (`ha/upstream-docs-verification`)

### Validation & report

- **MUST** validate offline — depending on scope: intent handlers derive from `IntentHandler`, are registered, set `intent_type`, and return an `IntentResponse` created through `create_response()`/`async_set_speech()`; the conversation entity derives from `ConversationEntity`, declares `supported_languages`, and implements `_async_handle_message`; every tool carries `name`, implements `async_call`, raises `HomeAssistantError`, and returns `JsonObjectType`; the `llm.API` is registered and unregistered on unload
- **MUST** deliver a CONFORMANT / NEEDS-WORK report against the acceptance criteria from `ha/intents-conversation` and/or `ha/llm-api` (per scope), plus the changed file paths and the chosen surface(s)

### Prohibitions

- **MUST NOT** mix intent/conversation logic with LLM-tool logic — the two axes stay separated
- **MUST NOT** re-implement deprecated intents or use the deprecated `async_process` pattern for new conversation agents
- **MUST NOT** create Assist satellite/STT/TTS/wake-word entities — these belong in `ha/entity-platforms-voice`
- **MUST NOT** deploy to a running HA instance

## Acceptance criteria

- [ ] Skill makes the scope decision with the user (intents / conversation entity / LLM tools) and fixes the role (exposing vs. consuming) for tools
- [ ] Every intent handler derives from `IntentHandler`, is registered via `intent.async_register`, sets `intent_type`, and reads slots through `intent_obj.slots["<name>"]["value"]`
- [ ] Domain-appropriate built-in intents are implemented; no deprecated intents re-implemented; speech only `plain`/`ssml` and errors with a valid `data.code`
- [ ] The conversation agent derives from `ConversationEntity`, declares `supported_languages`, and implements `_async_handle_message(...) -> ConversationResult`
- [ ] `ConversationEntityFeature.CONTROL` is set only when the agent actually controls HA
- [ ] Every LLM tool carries `name`, implements async `async_call(...)`, returns `JsonObjectType`, and raises `HomeAssistantError`
- [ ] A custom `llm.API` inherits from `API`, implements `async_get_api_instance(...) -> APIInstance` with `api_prompt`, is registered via `llm.async_register_api`, and unregistered via `entry.async_on_unload(unreg)`
- [ ] Localized sentences/texts are not wired into code; report names the file paths and the chosen surface(s)

## Open questions

- **Scope default**: When the user vaguely says "add a conversation agent" — should the skill default to the `ConversationEntity`, or first clarify whether built-in intents already cover the need? Currently it clarifies the scope decision first.
- **`AbstractConversationAgent` vs. `ConversationEntity`**: `ha/intents-conversation` permits both paths. The skill prefers `ConversationEntity`; whether `AbstractConversationAgent` may ever be generated stays open.
- **Tool naming convention**: `ha/llm-api` fixes no naming scheme. The skill follows the doc pattern and asks when in doubt.
- **Multiple surfaces per run**: The skill permits multiple surfaces as long as the user explicitly scopes them. Whether a limit (one surface per run, as in `ha-device-automation-add`) would be cleaner stays open.
