# HA Artifacts: Naming Conventions

Status: draft

## Context

The skills and agents in this plugin produce artifacts across four very different worlds: custom-integration code (Python), blueprints and automations (YAML), Lovelace cards (TypeScript/JavaScript), and the file/directory layout that holds all of it. Each world has its own Home-Assistant-mandated naming mechanics — a `unique_id` follows different rules than a custom-element tag, a `translation_key` different rules than a blueprint filename. Without a shared, binding convention the skill outputs drift apart: `snake_case` here, `camelCase` there, German display names in one place, English in another, with an area prefix here, without it there.

This spec is the **single authoritative source for the naming dimension** across all generated artifacts. It fixes which casing, which language, and which structure an identifier carries — based on its role, not on the mood of the individual skill. The underlying *mechanics* (how a `unique_id` is technically built, how the `EntityDescription` pattern works, how a card is registered) remain in their respective domain specs and are **not repeated here** but referenced: `ha/entity-architecture`, `ha/entity-platform-types`, `ha/device-registry`, `ha/integration-manifest`, `ha/services`, `ha/translations`, `ha/blueprint-patterns`, `ha/lovelace-card-patterns`.

The two guiding decisions of this spec: **(1)** Human-readable display names are uniformly **English**; localization happens cleanly via `translation_key`/`translations`, never via hard-wired foreign-language names. **(2)** Entity and device names follow the **HA convention** (`_attr_has_entity_name = True` + `translation_key`, with the `entity_id` derived by HA at runtime) — **no** forced prefix pattern such as `<area>_<device>_<function>` is prescribed.

Quality-Scale marker: **Bronze** — a stable, non-random `unique_id` is a Bronze requirement; this spec consolidates the naming rule whose mechanics live in `ha/entity-architecture`.

## Goals

- Fix a closed casing matrix: which identifier role carries `snake_case`, `kebab-case`, or `PascalCase`
- Establish English as the binding language for all human-readable display names and bind localization to `translation_key`/`translations`
- Declare the HA convention for entity/device names (`has_entity_name` + `translation_key`, derived `entity_id`) binding and forbid manual `entity_id` setting
- Make the naming rules per artifact world (integration code, blueprint/automation, Lovelace card, file layout) atomic and checkable
- Secure identifier stability: no volatile data (IP, hostname, token, timestamp) in `unique_id`, `identifiers`, or file/element names
- Delimit clearly against the domain specs: this spec defines *names*, the domain specs define *mechanics*

## Non-Goals

- Mechanics of `unique_id` construction, the `EntityDescription` pattern, or coordinator wiring — covered by `ha/entity-architecture` and `ha/entity-platform-types`
- Structure of the `DeviceInfo`/hub hierarchy and `via_device` chaining — covered by `ha/device-registry`
- Manifest field semantics beyond the `domain` name — covered by `ha/integration-manifest`
- Translation workflow and `strings.json` structure — covered by `ha/translations`
- Blueprint schema, selectors, and the templating bridge — covered by `ha/blueprint-patterns`
- Card registration, lifecycle callbacks, and rendering — covered by `ha/lovelace-card-patterns`
- Prescribing an area-/room-based prefix scheme for entity IDs (deliberately left to HA derivation)
- Naming of artifacts in the user's private HA config (`home-assistant-config`) — this spec binds only the plugin-generated artifacts

## Requirements

### Cross-Cutting Rules

- **MUST** use `snake_case` from `[a-z0-9_]`, with no leading digit, for all technical identifiers (domain, `object_id`, `translation_key`, service name, input key, automation `id`, blueprint filename)
- **MUST** use `kebab-case` from `[a-z0-9-]` for web custom-element tags and card source filenames
- **MUST** use `PascalCase` for TypeScript/JavaScript class names
- **MUST** write all human-readable display names (friendly name, `blueprint.name`, automation `alias`, card `name`/label) in **English**
- **MUST** limit human-readable display names to at most **50 characters**, so UI lists and pickers stay lean
- **MUST** restrict every identifier to ASCII — no umlauts, accents, or non-ASCII characters in identifiers
- **MUST NOT** embed volatile or environment-dependent data (IP address, hostname, port, token, raw serial number without a stability guarantee, timestamp) in `unique_id`, device `identifiers`, file names, or element names
- **MUST NOT** include personal data or secrets (username, email, API key) in any identifier or display name
- **SHOULD** keep display names short and device-scoped and leave localization to the `translation_key` path instead of hard-coding multilingual names

### Custom-Integration Code

- **MUST** carry the integration `domain` as `snake_case`, globally unique, identical to the folder name `custom_components/<domain>/` and to the `domain` key in `manifest.json` (mechanics: `ha/integration-manifest`)
- **MUST** name every entity via `_attr_has_entity_name = True` plus `translation_key` and let HA derive the `entity_id` (mechanics: `ha/entity-architecture`)
- **MUST NOT** set `self.entity_id` manually or hard-code a fixed display name where a `translation_key` applies — this bypasses the HA slug logic and freezes a language-/installation-dependent ID
- **MUST** carry the `translation_key` as `snake_case`, matching a key under `entity.<platform>.<translation_key>.name` in the translations (mechanics: `ha/translations`)
- **MUST** build the `unique_id` stable and collision-free within the integration and never equate it with the `entity_id` (mechanics: `ha/entity-architecture`)
- **MUST** build device `identifiers` as `{(DOMAIN, <stable_string>)}` and prefix with `entry.entry_id` for multi-instance capability (mechanics: `ha/device-registry`)
- **SHOULD** choose the device display name (`DeviceInfo.name`) English and device-scoped, or omit it when manufacturer/model carry the name more sensibly
- **SHOULD** choose the config-entry title English and instance-identifying (e.g., account name or location), not a repeat of the domain name
- **MUST** register service names as `snake_case`, under the integration `domain`, with a matching key in `services.yaml`/translations (mechanics: `ha/services`)
- **SHOULD** name platform, coordinator, and entity-description identifiers in code (`snake_case` variables, `PascalCase` classes) descriptively by their role (e.g., `<Domain>DataUpdateCoordinator`, `<Platform>EntityDescription`)

### Blueprints and Automations

- **MUST** carry the blueprint filename as `snake_case` with a `.yaml` extension, descriptive of its purpose (e.g., `motion_light.yaml`), placed under `blueprints/<domain>/<author>/<file>.yaml` (mechanics: `ha/blueprint-patterns`)
- **MUST** carry `blueprint.name` as a short, English, human-readable title
- **MUST** carry every input key (the label referenced via `!input <key>`) as `snake_case` and write the input's human-readable `name:` label in English
- **MUST NOT** assign the same input key twice or use a key that collides with the HA `!input` tag syntax
- **MUST** carry the `id` of a generated automation/script as a stable `snake_case` slug (not a re-creation of the volatile UI timestamp) and the `alias` English and human-readable
- **SHOULD** choose the `alias` so it uniquely identifies the automation in the UI list without carrying internal identifiers or entity IDs in plain text

### Lovelace Cards

- **MUST** carry the custom-element tag as `kebab-case` and — per the Web Components requirement — contain **at least one hyphen** (e.g., `<domain>-card`)
- **SHOULD** namespace the element tag with the integration `domain` (e.g., `<domain>-card`) to avoid collisions with other cards; an additional portfolio-wide vendor prefix is not required
- **MUST** reference the card type in the Lovelace configuration as `custom:<tag>`, where `<tag>` matches the registered element tag exactly
- **MUST**, *when* the card provides a config editor element, carry that element's tag as `<tag>-editor` (mechanics: `ha/lovelace-card-editor`) — a card without an editor is exempt from this rule
- **MUST** carry the card class name as `PascalCase`, ending in `Card` or `CardEditor` (e.g., `FooCard`, `FooCardEditor`)
- **MUST** write the card `name` (picker label) and `description` English and human-readable
- **SHOULD** name the card source file `kebab-case` and matching the element tag (e.g., `foo-card.ts`)

### File and Directory Layout

- **MUST** place integration code under `custom_components/<domain>/`, where `<domain>` matches the integration `domain` exactly
- **MUST** place card assets shipped with the integration under `custom_components/<domain>/www/` (mechanics: `ha/lovelace-card-patterns`)
- **MUST** place blueprints under `blueprints/<domain>/<author>/<file>.yaml`, where `<domain>` is exactly one of `automation`, `script`, `template` (mechanics: `ha/blueprint-patterns`)
- **MUST** carry Python module and package names as `snake_case` (HA/PEP-8 convention)
- **SHOULD** name files and folders descriptively by their role and not by area/room/instance, so the same artifact stays reusable across installations

## Acceptance Criteria

- [ ] Every plugin-generated technical identifier is `snake_case` (code/YAML), `kebab-case` (web element/card file), or `PascalCase` (TS class) per the casing matrix
- [ ] No human-readable display name in a generated artifact is foreign-language; all are English
- [ ] No display name in a generated artifact exceeds 50 characters
- [ ] No generated entity sets `self.entity_id` manually; each names itself via `has_entity_name` + `translation_key`
- [ ] No `unique_id`, device `identifiers` entry, or file/element name contains IP, hostname, token, timestamp, or personal data
- [ ] The integration `domain` is identical across the folder name, `manifest.json`, and all service/entity registrations
- [ ] Every custom-element tag contains at least one hyphen; the card type is referenced as `custom:<tag>`; any config editor tag is `<tag>-editor`
- [ ] Every blueprint lives under `blueprints/<domain>/<author>/<file>.yaml` with a `snake_case` filename; every input key is `snake_case`
- [ ] The spec repeats no mechanics but references the responsible domain spec for each rule

## Open Questions

The original three questions are decided and folded into the requirements:

- Custom-element tags use the integration `domain` as namespace; a portfolio-wide vendor prefix is not required.
- Display names are limited to at most 50 characters.
- The blueprint `author` folder remains freely configurable per project.

No open questions at this time.
