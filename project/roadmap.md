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
