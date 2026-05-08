# CLAUDE.md

Orientation for Claude Code and contributors working inside this repository.

## What this repo is

`claude-home-assistant` is a Claude Code plugin that bundles skills, agents, and specifications for efficient development of [Home Assistant](https://www.home-assistant.io/) artifacts — custom integrations (Python), Lovelace cards (TypeScript / JavaScript), blueprints and automations (YAML), and ESPHome / add-on work.

## Layout

- `.claude-plugin/plugin.json` — plugin manifest (name, version, author)
- `.claude-plugin/marketplace.json` — marketplace catalog (downstream install source)
- `skills/<name>/SKILL.md` — reusable skills; each folder is one skill
- `agents/<name>.md` — reusable sub-agents (when present)
- `spec/` — bilingual specifications (DE canonical, EN translation)
- `docs/` — MkDocs source (bilingual once content lands; DE-first)
- `tests/` — repo-local test harness (placeholder until first runtime check exists)

Plugin skills are namespaced by plugin name — for example `/claude-home-assistant:<skill>`.

## Command entry points

Local automation runs through `Taskfile.yml`:

- `task lint` — pre-commit checks
- `task test` — test suite (placeholder — no runtime tests yet)
- `task docs` — build the MkDocs site
- `task plugin:reload` — launch Claude Code with this repo loaded as a plugin (dogfooding)

## Dogfooding

When developing inside this repository, launch Claude Code with the plugin pointed at the repo root:

```bash
claude --plugin-dir .
```

Use `/reload-plugins` inside the session to pick up changes without restarting.

## Conventions

- New skills are scaffolded via `/nolte-shared:skill-management`.
- Specs are authored and translated via `/nolte-shared:spec`.
- Project-structure drift is checked via `/nolte-shared:project-structure-apply`.
- Pull requests are created via `/nolte-shared:pull-request-create`.

## Authoring rules

- Keep `CLAUDE.md`, `spec/`, and the plugin manifest in sync with what the repo actually ships.
- Never copy plugin-owned skills into a consumer's `.claude/skills/` — distribution happens via the plugin marketplace.
- All generated configuration files (`.github/*.yml`, `Taskfile.yml`, workflow YAML) are written in English for portfolio consistency, regardless of the language used in conversation.
