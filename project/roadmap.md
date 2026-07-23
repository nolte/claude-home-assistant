# Roadmap

This file is the work queue governed by `spec/project/roadmap/`. Each entry is a
level-3 heading followed by a `yaml` code block (`id`, `title`, `detail`,
`outcomes`, `target_sprint`, `mvp`, `status`, in that order) and a free-text
body. `roadmap-plan` and `roadmap-refine` own the detail level and the status
lifecycle; do not hand-edit those fields here.

Entries carry monotonically increasing IDs starting at `R-1`, never reused.
Outcome IDs (`O-n` in `goals.md`) are an independent counter.

`claude-home-assistant` shipped the MVP item below before adopting the planning
suite. This roadmap records it retroactively as `status: done`, mapped to sprint
1, so the mission's minimum viable product resolves.

## Phase 1 — Home Assistant development skill and agent set

### R-1 — Skills and agents for Home Assistant development

```yaml
id: R-1
title: Skills and agents for Home Assistant development
detail: fine
outcomes: [O-1, O-2]
target_sprint: 1
mvp: true
status: done
```

The Claude Code skills and agents that author Home Assistant custom integrations,
Lovelace cards, blueprints and automations, and ESPHome / add-on work against
Home Assistant Core and HACS conventions. Capability
`claude-code-skills-and-agents-for-home-assistant` in `project/portfolio.yml`.

## Phase 2 — Audience-aligned plugin split

### R-2 — Split into three audience-aligned plugins (ha-esphome / ha-automation / ha-dev)

```yaml
id: R-2
title: Split into three audience-aligned plugins (ha-esphome / ha-automation / ha-dev)
detail: fine
outcomes: [O-1, O-2]
target_sprint: null
mvp: false
status: proposed
```

The single `claude-home-assistant` marketplace entry is replaced by three
audience-aligned plugins — `ha-esphome` (ESPHome device-config author),
`ha-automation` (HA power user incl. the Pixoo family), and `ha-dev` (custom
integration + Lovelace/frontend developer) — in one monorepo with lockstep
versioning, one plugin-local router each, and a shared spec base package
referenced via `inherits:`. Requirements:
`project/requirements/three-plugin-split.md` (R1–R9 confirmed); decision record:
`AUDIENCES.md` §"Offene Fragen → Plugin-Schnitt"; work item: issue #90. The
legacy marketplace entry is removed with a documented namespace migration
mapping (hard cut).

Feature checklist:

- [ ] Multi-plugin marketplace schema verified against current Claude Code plugin docs (R9)
- [ ] Directory restructure: per-plugin skills/agents trees + three marketplace entries (R1, R2)
- [ ] Shared spec base package wired via `inherits:` (R5, R7)
- [ ] Router rework: remove `ha-solution`, one plugin-local router per plugin (R3)
- [ ] Cross-reference repair across plugin boundaries (pattern from #86)
- [ ] Docs and artefacts: per-plugin AUDIENCES.md, README/MkDocs/catalog, migration mapping (R6)
- [ ] CI/release adapted: lockstep versioning, green lint/test/docs, per-plugin dogfooding (R4, R8)
