---
name: ha-conversation-agent-augment
description: Augment an existing Home Assistant Custom Integration with one or more Voice & AI surfaces — intent handlers, a conversation agent, and/or LLM API tools — conforming to spec/ha/intents-conversation plus spec/ha/llm-api. Decides with the user which surface(s) are in scope, then generates intent handlers (intent.IntentHandler subclasses registered via intent.async_register, with slot_schema and async_handle returning an IntentResponse), a conversation platform (conversation.py with a ConversationEntity declaring supported_languages and _async_handle_message returning a ConversationResult), and/or LLM tools (llm.Tool subclasses with async_call plus an llm.API registered via llm.async_register_api whose async_get_api_instance returns an APIInstance). Implements domain-appropriate built-in intents, avoids deprecated ones, and signals tool errors as HomeAssistantError. Activate on "add a conversation agent", "register intents", "expose tools to the assistant via the LLM API", "füge einen Conversation-Agent / Intents / LLM-Tools hinzu". Do not activate for assist_satellite/stt/tts/wake_word entities (ha/entity-platforms-voice), registered services (ha-service-definition-generator), greenfield scaffolding (ha-integration-scaffold), or deploying to a live HA instance.
tags: [home-assistant, custom-integration, voice-ai]
---

# HA Conversation Agent Augment

Spec: <https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-conversation-agent-augment/de.md> (DE canonical) / [`en.md`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/claude/ha-conversation-agent-augment/en.md).

## Why this is a skill, not an agent

- **Human-visible augmentation surface** — the user describes a Voice & AI capability and reads back the generated handlers/entity/tools and the conformance report; a skill keeps this on the visible command surface, like the sibling augment skills (`ha-config-flow-augment`, `ha-coordinator-add`, `ha-device-automation-add`).
- **Scope decision up front** — which of the three surfaces (intents / conversation entity / LLM tools) and, for tools, expose-vs-consume, is a per-run dialogue the user approves before any generation; that belongs in the working context.
- **Bounded, inline generation** — intent handlers, one `conversation.py`, and a small `llm.API` with its tools fit inline; no isolated agent context is needed.
- Counter-dimension considered: the draft→validate loop could be an agent, but the surface-scope decision and the two-axis separation belong in the user's working context; skill wins.

## When this skill activates

Use this skill to add **one or more** Voice & AI surfaces — intent handlers, a conversation agent, and/or LLM API tools — to an existing integration, so its devices respond to Assist sentences and/or it exposes tools to the assistant.

## When NOT to activate

- Assist satellite / STT / TTS / wake-word **entities** → `ha/entity-platforms-voice`
- a registered service with its own schema → `ha-service-definition-generator` / `ha/services`
- translation of intent sentences / response / prompt texts → `ha/translations`
- greenfield integration scaffolding → `ha-integration-scaffold`
- deploying/importing into a running HA instance → out of scope

## Hard rules

1. **Decide scope first.** Resolve with the user which surface(s) are in scope — intents, a conversation entity, and/or LLM tools — and, for tools, the role: **expose** an `llm.API` vs. **consume** an API. Keep the two axes (intents/conversation vs. tools) separated.
2. **Read [`ha/intents-conversation`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/intents-conversation/de.md) and [`ha/llm-api`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/llm-api/de.md) first** (at least the in-scope one). Do not generate from memory.
3. **Intent handler contract.** Every handler derives from `homeassistant.helpers.intent.IntentHandler`, sets `intent_type`, is registered via `intent.async_register(hass, handler)` in `async_setup`/`async_setup_entry` (never in platform modules), and `async_handle(self, intent_obj) -> IntentResponse` returns an `IntentResponse` — never `None` or a raw string. Read slots via `intent_obj.slots["<name>"]["value"]`; declare a `slot_schema` for expected slots.
4. **Built-in intents, no deprecated ones.** Implement domain-appropriate built-in intents (`HassTurnOn`/`HassTurnOff`/`HassGetState`), treating `HassTurnOn`/`HassTurnOff` slots as optional; **never** re-implement deprecated intents (`HassToggle`, `HassOpenCover`, …).
5. **Speech & response type.** Create the response via `intent_obj.create_response()` + `response.async_set_speech(...)`; speech is only `plain` or `ssml`; set the correct `response_type` (`action_done`/`query_answer`/`error`) and a valid `data.code` (`no_intent_match`/`no_valid_targets`/`failed_to_handle`/`unknown`) on error.
6. **Conversation entity.** A conversation agent lives in `conversation.py`, derives from `conversation.ConversationEntity`, declares `supported_languages` (`list[str]` or `"*"`), and implements `_async_handle_message(self, user_input, chat_log) -> ConversationResult` — **not** the deprecated `async_process`. Set `ConversationEntityFeature.CONTROL` only when the agent actually controls HA; perform no I/O in property getters.
7. **LLM tool contract.** Every tool derives from `llm.Tool`, carries a `name`, implements async `async_call(self, hass, tool_input, llm_context)`, returns a JSON-serializable `JsonObjectType`, and raises errors as `HomeAssistantError` — no in-band error codes. A custom API inherits from `API`, implements `async_get_api_instance(self, llm_context) -> APIInstance` (with the required `api_prompt`), is registered via `llm.async_register_api(hass, api)` with a unique `id`/`name`, and is unregistered via `entry.async_on_unload(unreg)`.
8. **Localization out of code.** Keep localized sentences/response/prompt texts out of handler/tool code — sentences in `intents/<lang>.yaml` (see [`ha/translations`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/translations/de.md)).
9. **Name per [`ha/naming-conventions`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/naming-conventions/de.md)** and **verify HA internals against the official docs** (see [`ha/upstream-docs-verification`](https://github.com/nolte/claude-home-assistant/blob/develop/spec/ha/upstream-docs-verification/de.md)).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root; `custom_components/<domain>/manifest.json` must exist |
| `capability` | yes | — | the Voice & AI capability, in prose |
| `surfaces` | yes | resolved in pre-flight | which of intents / conversation entity / LLM tools |
| `tool_role` | when tools in scope | asked | expose an `llm.API` vs. consume an API |
| `intent_types` / slots | no | derived | `intent_type` names and expected slots |
| `supported_languages` | no | asked when needed | `list[str]` or `"*"` for the conversation entity |
| tool `name` / `description` / `parameters` | no | derived | per `llm.Tool` |

If the user is silent on an optional field, use the default but state it explicitly.

## Pre-flight (in order — abort on first failure)

1. `target_dir/custom_components/<domain>/manifest.json` exists; read `domain`.
2. Make the scope decision: which surface(s) are in scope; for LLM tools fix the role (expose vs. consume).
3. Read `ha/intents-conversation` and/or `ha/llm-api` (at least the in-scope one).
4. The targeted `intent_type` / conversation entity / `llm.API` `id` is not already declared. If it is, abort.

## Workflow

### 1) Resolve and confirm

State `domain`, the in-scope surface(s), for tools the role (expose/consume), and the concrete `intent_type`(s) / `supported_languages` / tool names in one paragraph. Wait for confirmation.

### 2) Generate

| Surface | Artefacts | Key contract |
|---|---|---|
| intents | `IntentHandler` subclass(es) + `intent.async_register` in setup | `intent_type`, `slot_schema`, `async_handle -> IntentResponse`, built-in intents, no deprecated ones |
| conversation entity | `conversation.py` with a `ConversationEntity` | `supported_languages`, `_async_handle_message -> ConversationResult`, no I/O in getters |
| LLM tools | `llm.Tool` subclass(es) + an `API` subclass | `async_call -> JsonObjectType`, `HomeAssistantError`; `async_register_api` + `entry.async_on_unload(unreg)`; `api_prompt` |

Keep localized sentences in `intents/<lang>.yaml`; never wire localized text into code.

### 3) Validate and report

Validate offline per scope (handlers derive from `IntentHandler`, registered, `intent_type`, `IntentResponse` via `create_response()`/`async_set_speech()`; the entity derives from `ConversationEntity`, declares `supported_languages`, implements `_async_handle_message`; every tool carries `name`, implements `async_call`, raises `HomeAssistantError`, returns `JsonObjectType`; the `llm.API` is registered and unregistered on unload). Emit a CONFORMANT / NEEDS-WORK report keyed to the `ha/intents-conversation` and/or `ha/llm-api` acceptance criteria, plus the changed file paths and the chosen surface(s).

### 4) No deploy

The skill never deploys to a live HA instance. Surface the report and stop.

## Boundaries

- Assist satellite / STT / TTS / wake-word entities → `ha/entity-platforms-voice`
- Registered services → `ha-service-definition-generator`
- Intent sentence / prompt translations → `ha/translations`
- Greenfield scaffold → `ha-integration-scaffold`
- Deploy to live HA → out of scope
