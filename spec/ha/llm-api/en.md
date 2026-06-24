# HA Integration: LLM API (Tools for Conversation Agents)

Status: draft

## Context

Home Assistant can interact with large language models (LLMs). By exposing a Home Assistant API to an LLM, the LLM can fetch data or control Home Assistant to better assist the user. Home Assistant comes with a built-in LLM API, but custom integrations can register their own to provide additional functionality.

The LLM helper API has **two consumer sides** that an integration must keep cleanly separated: (a) an integration that **exposes tools to LLMs** by registering an `llm.API` via `llm.async_register_api(hass, api)` and implementing an API class that inherits from `API` and returns `async_get_api_instance(...) -> APIInstance` with a list of `Tool` objects; (b) an LLM-providing integration (conversation entity) that **consumes** an API — it stores the selected API IDs in the config entry options under `CONF_LLM_HASS_API`, pulls the selected API's tools from the `ChatLog`, and passes them together with the `api_prompt` to the LLM.

Home Assistant ships a built-in **Assist API** that exposes the Assist capabilities to LLMs. This API lets LLMs interact with Home Assistant via [intents](../intents-conversation) and can be extended by registering intents. The Assist API is equivalent to the capabilities and exposed entities also available to the built-in conversation agent; no administrative tasks can be performed.

This spec lifts the documentation convention into a generic obligation. Conversation agents that consume LLM APIs and intents belong in `ha/intents-conversation`; the delimitation of tools vs services belongs in `ha/services`; translations for API- and tool-related strings belong in `ha/translations`.

## Goals

- Separate the two sides of the LLM helper API (exposing tools vs consuming) explicitly, so an integration does not accidentally mix both roles
- Register a custom `llm.API` correctly and unregister it again when the config entry is unloaded
- Declare `Tool` definitions with name, description, a voluptuous parameter schema, and an async `async_call`, so the LLM knows when and how to call the tool
- Use the built-in `assist` API as the default consume path rather than reinventing intent functionality
- Treat the `LLMContext` as the sole source of call context, rather than smuggling context through side channels
- Signal tool errors via `HomeAssistantError` rather than in-band error codes in the response

## Non-Goals

- Conversation agent implementation, intent handlers, and intent registration — separate `ha/intents-conversation` spec
- Delimitation and implementation of HA services (user-driven actions) — separate `ha/services` spec
- Translations for API names, tool names, and prompt text — owned by `ha/translations`
- The concrete LLM wiring (streaming, message formatting, provider-specific tool serialization) — provider-side and outside this spec
- Administrative tasks via the Assist API — the built-in API allows no administrative tasks

## Requirements

### Purpose & two sides (exposing tools vs consuming)

- **MUST** explicitly decide which of the two roles the integration takes: an integration that **exposes tools** (registers an `llm.API`) or an LLM-providing integration that **consumes** an API (pulls tools from the `ChatLog`)
- **MUST** hold the selected API IDs in the config entry options under `CONF_LLM_HASS_API` when consuming — as a string or list; if no API is selected, the key **MUST NOT** be set
- **SHOULD** offer a selector in the options flow that presents the available APIs for selection via `llm.async_get_apis(hass)`

### Registering a custom `llm.API`

- **MUST** create a class that inherits from `API` for a custom API and implement `async_get_api_instance(self, llm_context: LLMContext) -> APIInstance`, returning an `APIInstance` with `api`, `api_prompt`, `llm_context`, and `tools`
- **MUST** register the API via `llm.async_register_api(hass, MyAPI(...))`, where the `llm.API` carries a unique `id` and a `name`
- **MUST** unregister the API when the config entry is unloaded if it is bound to a config entry — register the return value of `async_register_api` via `entry.async_on_unload(unreg)`
- **MUST** set an `api_prompt` in the `APIInstance` that tells the LLM how to use the tools — `api_prompt` is a required field

### `Tool` definition (`async_call`)

- **MUST** derive every tool from `llm.Tool` and carry a `name` attribute — `name` is required
- **MUST** implement `async_call` as an async method; its arguments are `hass`, an `llm.ToolInput` instance, and the `llm_context`
- **MUST** raise tool errors as `HomeAssistantError` (or subclasses) — the response data **MUST NOT** contain error codes used for error handling
- **SHOULD** set a `description` attribute that helps the LLM understand when and how the tool should be called — optional but recommended
- **SHOULD** declare the input parameters via a voluptuous `parameters` schema; HA converts and validates `tool_args` through this schema (default: `vol.Schema({})`)
- **MUST** return a JSON-serializable result (`JsonObjectType`) as response data

### Consuming the built-in `assist` API

- **SHOULD** use the built-in Assist API as the default consume path rather than reinventing intent functionality — it exposes entities and intents equivalent to the built-in conversation agent
- **MAY** extend the Assist API by registering additional intents
- **MUST NOT** expect or require administrative tasks via the Assist API — the built-in API allows no administrative tasks

### `LLMContext`

- **MUST** pass the `LLMContext` as input to `async_get_api_instance(...)` and `async_call(...)`, rather than transporting call context through globals or side channels
- **MUST** resolve the LLM API via `llm.async_get_api(hass, api_id, llm_context)` with the current `llm_context` when consuming
- **SHOULD** use the fields delivered in `ToolInput` (`tool_name`, `tool_args`, `platform`, `context`, `user_prompt`, `language`, `assistant`, `device_id`) for tool logic, rather than reconstructing these values itself

### Delimitation against conversation/intents

- **MUST NOT** define conversation entity logic, intent handlers, or intent registration in this spec — these belong in `ha/intents-conversation`
- **MUST NOT** mix LLM tools with HA services — tools are called by the LLM, services are user-driven actions; the delimitation belongs in `ha/services`
- **SHOULD** route API names, tool names, and prompt text, where translatable, through the translations mechanism from `ha/translations`

## Acceptance Criteria

- [ ] The integration explicitly fixes one of the two roles (exposing tools or consuming an API)
- [ ] When consuming, the selected API IDs are held under `CONF_LLM_HASS_API` in the options; with no selection the key is omitted
- [ ] A custom API inherits from `API` and implements `async_get_api_instance(...) -> APIInstance`
- [ ] The API is registered via `llm.async_register_api(hass, api)` and unregistered on unload via `entry.async_on_unload(unreg)`
- [ ] Every `Tool` carries a `name` attribute and implements async `async_call(self, hass, tool_input, llm_context)`
- [ ] Tool errors are raised as `HomeAssistantError`; the response contains no error codes
- [ ] `async_call` returns a JSON-serializable `JsonObjectType` result
- [ ] When consuming, the API is resolved via `llm.async_get_api(hass, api_id, llm_context)`
- [ ] Conversation/intent logic and service logic are not defined in this spec but delegated to `ha/intents-conversation` and `ha/services` respectively

## Open Questions

- **`api_prompt` granularity**: The documentation requires an `api_prompt` per `APIInstance`. Should the spec mandate a minimum structure for this prompt (for example "name the available tools explicitly"), or does it stay free?
- **Tool naming convention**: The documentation names `name` as required but gives no naming scheme. Should the spec fix a convention (CamelCase, verb-object) so skill output is deterministic?
- **Multiple API selection**: The selector allows `multiple=True`. Should the spec address how tool name collisions are resolved across multiple selected APIs?
- **Streaming/message formatting**: The documentation shows provider-specific `_format_tool`/`_convert_content` stubs. Should the spec explicitly mark this provider-side wiring as out of scope or recommend a minimum loop structure?
