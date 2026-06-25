# HA Automation: Using REST Command

Status: draft

## Context

The `rest_command` integration turns named HTTP requests into callable actions. In `configuration.yaml`, under the `rest_command:` key, a service name maps to a request definition; each name is exposed as the action `rest_command.<service_name>` and is callable from automations and scripts. So `rest_command` is the declarative tool for firing **one-shot** HTTP calls (webhooks, trigger endpoints, push APIs) from within an automation.

The request is described through documented configuration variables: `url` is required (template), with optional `method` (default `get`; allowed `get`/`patch`/`post`/`put`/`delete`), `payload` (template), `headers` (map), `content_type`, `username`/`password` with `authentication` (default `basic`, alternatively `digest`), `timeout` (default `10` seconds), `verify_ssl` (default `true`), plus `insecure_cipher` and `skip_url_encoding`. `url`, `payload`, and `headers` support templates. Callers can collect a dictionary with `status` (HTTP code), `content` (body), and `headers` (response headers) via `response_variable`.

Real classification: `rest_command` is a **command/integration integration** with a card under `/integrations/rest_command/`, but no connectable device. It sends, it does not poll: within the `ha-automation` corpus it is the outbound, one-shot HTTP call — the counterpart to the inbound `rest`/`restful` sensor.

Verified source: [`/integrations/rest_command/`](https://www.home-assistant.io/integrations/rest_command/) (configuration mapping, invocation `rest_command.<service_name>`, variables `url`/`method`/`payload`/`headers`/`content_type`/`authentication`/`username`/`password`/`timeout`/`verify_ssl`/`insecure_cipher`/`skip_url_encoding` with defaults, template support in `url`/`payload`/`headers`, `response_variable` with `status`/`content`/`headers`).

## When to Use

Use `rest_command` for a **one-shot, outbound HTTP call** from within an automation — declaratively via `url`/`method`/`payload`/`headers`, with no state and no polling. Typical use cases:

- **Trigger a webhook** — call an external service's push/trigger endpoint via `post` as soon as an automation fires
- **Send state to a foreign API** — pass a value from an entity state to an API with `method` (`put`/`patch`/`post`) and a templated `payload`
- **Dynamic request from entity data** — assemble `url`, `payload`, and `headers` via templates from current states
- **Status-dependent branching** — collect the response via `response_variable` and react to `status`/`content`/`headers` instead of ignoring an error status
- **Authenticated one-off call** — fire a request with `username`/`password` and `authentication` (`basic`/`digest`), plus a deliberate `timeout` and `verify_ssl: true`

A `rest_command` is the right tool only for the **one-shot outbound call**. For periodic reading as a sensor, a multi-step auth flow, a service already covered natively, or a local system interaction, another building block is right (see `### Delimitation: When NOT to Use`).

## Goals

- Fix the configuration mapping (`rest_command:` name → request) and invocation contract (`rest_command.<name>`) as binding
- Fix the documented variables and their **defaults** (`method=get`, `timeout=10`, `verify_ssl=true`, `authentication=basic`) as a binding baseline
- Anchor the template model in `url`/`payload`/`headers` and the correct `content_type`
- Fix the response path via `response_variable` (`status`/`content`/`headers`) and clean status handling
- Clearly delimit that `rest_command` is a **one-shot outbound** call and **when NOT** to choose it

## Non-Goals

- **Reading** a REST API as a sensor (polling) — the `rest`/`restful` sensor integration (its own specs), only referenced here for delimitation
- The declarative script/action syntax the call is embedded in — `ha-automation/script`
- The trigger/condition model of the rule engine — `ha-automation/automation`
- Local subprocess/shell interaction — `ha-automation/shell-command`
- The naming dimension (service name, snake_case, English, ≤50 chars) — `ha/naming-conventions`, only referenced here

## Requirements

### Configuration and Invocation

- **MUST** define each request under `rest_command:` as a mapping `<service_name>: { url: …, … }`; the name becomes the action `rest_command.<service_name>`
- **MUST** set `url` as a required field (template allowed); without it the definition is incomplete
- **MUST** give the service name as a snake_case slug; naming mechanics in `ha/naming-conventions`
- **MUST** choose `method` deliberately from `{get, patch, post, put, delete}` when the default `get` does not match the operation — a state-changing call must not accidentally run as `get`
- **SHOULD** set `timeout` deliberately when the default `10` (seconds) is too short or too long for the target endpoint
- **MUST NOT** set `verify_ssl: false` without documenting why — the default `true` is security-critical; `false`/`insecure_cipher: true` only as a deliberate exception for legacy devices

### Templating, Payload, and Response

- **MAY** use templates in `url`, `payload`, and `headers` to insert dynamic values from entity states
- **SHOULD** set an appropriate `content_type` for a structured `payload` (e.g. `application/json`) so the target service interprets the body correctly
- **SHOULD** pass credentials via `username`/`password` with the matching `authentication` (`basic`/`digest`) instead of encoding them into the `url`
- **SHOULD** collect the response via `response_variable` and branch on `status` (HTTP code); `content` (body) and `headers` (response headers) are also available — an error status must not be silently ignored
- **MAY** set `skip_url_encoding: true` when the endpoint expects an already encoded/canonicalized URL — otherwise leave the default

### Delimitation: When NOT to Use

- **MUST NOT** use `rest_command` to **poll a REST API periodically** and expose its value as a state — the **`rest`/`restful` sensor** is for that, because it offers a poll interval, value templates, and an entity with history/availability; `rest_command` is a one-shot, outbound fire call with no state
- **SHOULD NOT** use `rest_command` for **multi-step auth flows** (fetch OAuth token, refresh, manage session cookies) — that belongs in a **custom integration** with `application_credentials`/config flow (`ha/config-flow-patterns`, `ha/application-credentials`), which stores and renews tokens securely; `rest_command` knows only `basic`/`digest` and holds no session state
- **SHOULD NOT** use `rest_command` as a permanent solution for a service that already has a **native integration** — the integration is typed, more error- and auth-robust, and delivers entities instead of raw `content` that has to be parsed in a template
- **SHOULD NOT** disguise local system commands as HTTP — when no network endpoint is involved, `shell_command` (`ha-automation/shell-command`) or a native action is the right tool, not a REST call to `localhost`
- **MUST NOT** use `verify_ssl: false` as a default to work around a certificate problem — it opens man-in-the-middle; the root cause (CA/hostname) should be fixed, and `verify_ssl: false`/`insecure_cipher` remains the documented, justified exception

## Acceptance Criteria

- [ ] Each request is set as a `rest_command:` service name (snake_case) → definition with a required `url`
- [ ] `method` is chosen deliberately (not accidentally `get` for state-changing calls)
- [ ] `timeout` is set deliberately when the default `10`s does not fit
- [ ] `verify_ssl` stays `true` unless a documented exception justifies `false`/`insecure_cipher`
- [ ] A structured `payload` carries an appropriate `content_type`; auth goes through `username`/`password`/`authentication`, not the URL
- [ ] The response is evaluated via `response_variable` (`status`/`content`/`headers`); an error status is not ignored
- [ ] No `rest_command` polls an API as a sensor (use the `rest`/`restful` sensor) and none implements a multi-step auth flow (use a custom integration)
- [ ] The spec repeats no naming mechanics but references `ha/naming-conventions`

## Open Questions

- **Retry/error strategy**: The fetched doc page describes `timeout` but no built-in retry or backoff mechanism. Should this spec anchor its own rule for how callers react to an error status (retry via the script syntax `repeat`/`until` vs. simply discarding), or is that left to the calling script?
