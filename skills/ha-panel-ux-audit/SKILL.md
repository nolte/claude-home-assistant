---
name: ha-panel-ux-audit
description: "Runs a read-only panel-level UX audit of an existing panel artifact (custom sidebar panel, panel-mode view, or custom view) — with mobile-device usability as a mandatory first-class dimension. Audits against spec/ha/lovelace-views-panels, spec/ha/lovelace-layout-antipatterns, spec/ha/lovelace-card-patterns, and spec/ha/frontend-data-api plus UX/accessibility heuristics, and produces a severity-sorted improvement report — mobile usability, responsive/narrow behaviour, touch targets, information hierarchy, readability, accessibility, perceived performance — that ha-panel-author can consume as a prioritized work-list. Never modifies code. Activate on \"audit my panel's UX\", \"is this panel usable on mobile\", \"review the panel for usability and accessibility\", or equivalent German requests. Do not activate for building or fixing a panel (ha-panel-author), scaffolding one (ha-panel-add), a whole-integration review (ha-integration-review), or deploying to a live HA instance."
tags: [home-assistant, frontend, custom-panel, ux, audit]
phase: quality
summary: "Runs a read-only, mobile-first UX audit of an HA panel artifact against the Lovelace specs and UX heuristics, producing a severity-sorted improvement report ha-panel-author can consume."
summary_de: "Führt ein Read-only-UX-Audit eines HA-Panels mit Mobile-Fokus gegen die Lovelace-Specs und UX-Heuristiken durch und erzeugt einen nach Schweregrad sortierten Verbesserungs-Report."
use_when:
  - "you want to audit a panel's UX"
  - "you want to know whether a panel is usable on mobile"
  - "you want to review a panel for usability and accessibility"
dont_use_when:
  - situation: "You want to build or fix a panel, not audit it"
    alternative: ha-panel-author
  - situation: "You want to scaffold a bare panel"
    alternative: ha-panel-add
  - situation: "You want a whole-integration review, not a panel UX audit"
    alternative: ha-integration-review
see_also:
  - ha-panel-author
  - ha-panel-add
  - ha-panel-config-view-add
  - ha-quality-scale-audit
  - ha-security-audit
  - ha-integration-review
---

# HA Panel UX Audit

Spec: `spec/claude/ha-panel-ux-audit/en.md` (EN canonical) / `spec/claude/ha-panel-ux-audit/de.md` (DE translation).

This skill is the **UX expert** of the panel family. It statically audits an existing panel artifact from the user's point of view — can a person actually use this, especially on a phone — and emits a severity-sorted report of concrete improvements. It never edits code; the report is meant to be read, acted on, and — when the user wants — handed to `ha-panel-author` as a prioritized work-list.

## Why this is a skill, not an agent

- **Human-visible audit surface** — like the sibling audit skills `ha-quality-scale-audit` and `ha-security-audit`, this is an interactive audit the user invokes directly and reads the report from; a skill keeps it on the visible command surface.
- **Mid-flow interactivity** — the target devices (mobile is mandatory, but which else), the audience, and severity threshold are per-run inputs the user confirms before the audit.
- **Orchestrator-leaning** — findings route to `ha-panel-author` for the fix; the skill-orchestrates-fixes default keeps the entry point in skill form.
- Counter-dimension considered: a read-only one-shot review could be an agent (cf. `ha-integration-review`), but the report is meant to be read and acted on interactively and to feed `ha-panel-author`, and consistency with the `ha-*-audit` skills wins.

## When this skill activates

Use this skill to audit an existing **panel-level** artifact — a custom sidebar panel element, a panel-mode view, or a custom view — for UX quality, with **mobile usability as a required dimension**, and emit a severity-sorted improvement report. It is the UX sibling of `ha-quality-scale-audit` / `ha-security-audit`, scoped to panels.

## When NOT to activate

- building, developing, or fixing a panel → `ha-panel-author` (which may consume this skill's report)
- scaffolding a bare panel → `ha-panel-add`
- a whole-integration review (quality/security/consistency) → `ha-integration-review`
- a single custom card's internals → `ha/lovelace-card-patterns` scope
- auto-fixing findings → this skill is read-only; hand findings to `ha-panel-author`
- deploying/importing into a running HA instance, or live on-device testing → out of scope (static audit only)

## Hard rules

1. **Read-only.** The skill never modifies the panel element, its config, or any file. `git status` must be unchanged after the run.
2. **Mobile usability is mandatory.** Every audit MUST evaluate the mobile-device dimension and emit an explicit **Mobile usability verdict: PASS / NEEDS-WORK**; a critical mobile finding makes the overall verdict NEEDS-WORK. Anchor the HA-specific mobile facts in `spec/ha/lovelace-layout-antipatterns/en.md` E1 (the `narrow` property and the documented single-column collapse).
3. **Audit against the existing specs; reference them per finding.** The binding set: `spec/ha/lovelace-views-panels/en.md`, `spec/ha/lovelace-layout-antipatterns/en.md`, `spec/ha/lovelace-card-patterns/en.md`, and `spec/ha/frontend-data-api/en.md`. Every finding names the spec rule it rests on, or is tagged a **UX heuristic** (see rule 4).
4. **Distinguish HA facts from UX heuristics.** HA-internal facts come from the specs above / the official docs; general UX and accessibility heuristics (touch-target ≈44–48px, WCAG-AA contrast, no hover-only affordances, reduced-motion) are external best practice — label them **[UX heuristic]** and never present them as HA facts.
5. **Severity-sorted, actionable output.** Rank findings critical → high → medium → low. Every finding carries a concrete, spec-referenced improvement suggestion phrased so `ha-panel-author` can act on it; never a vague "improve UX".
6. **Never overstate.** A static audit cannot prove on-device usability; flag findings that need live-device verification as such rather than asserting them as confirmed.
7. **Verify HA internals against the official docs.** Don't reproduce HA API/behaviour from memory — when uncertain consult Developer docs [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant) and [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (see `spec/ha/upstream-docs-verification/en.md`).

## Inputs

| Field | Required | Default | Notes |
|---|---|---|---|
| `target_dir` | yes | — | repo root |
| `panel` | no | discovered + confirmed | path/identifier of the panel artifact (custom panel JS + `panel_custom` config, or the panel-mode/custom view config) |
| `target_devices` | no | `mobile + desktop` | mobile is always audited; add tablet/desktop as needed |
| `audience` | no | asked when relevant | who uses the panel (informs density/affordance judgement) |
| `severity_threshold` | no | `low` | report findings at or above this severity |

## Pre-flight (in order — abort on first failure)

1. `git -C <target_dir> rev-parse --is-inside-work-tree`.
2. Locate the panel artifact (the panel custom element and its `panel_custom` registration, or the panel-mode/custom-view config); if none is found, point at `ha-panel-author` / `ha-panel-add` to create one first.
3. Read the binding spec set (hard rule 3).
4. Confirm `target_devices` (mobile is always included) and the severity threshold.

## Audit dimensions

Audit each dimension and record findings with a spec reference or a `[UX heuristic]` tag.

1. **Mobile usability (mandatory).** The panel element reads and honours `narrow`; content collapses to a legible single column in a sensible order (E1); no horizontal overflow or fixed-outer-pixel widths that break on small viewports (`ha/lovelace-layout-antipatterns` B4/E1); touch targets are comfortably tappable **[UX heuristic ≈44–48px]**; no hover-only affordances **[UX heuristic]**; text stays legible without pinch-zoom; companion-app/safe-area considerations noted.
2. **Delivery-shape & layout fit.** The chosen shape suits the content (`ha/lovelace-views-panels`); a panel-mode view holds exactly one card and no badges (A1/A2); no third-party layout tooling (D1); embedded cards are sized via `getGridOptions()`/`getCardSize()` (B1/B2/B4).
3. **Information hierarchy & density.** Primary information is prominent and scannable; grouping is clear; the panel is not overloaded on a small screen.
4. **Readability, theming & contrast.** HA CSS custom properties (theme-aware, `ha/lovelace-card-patterns`), no hard-coded colours; sufficient contrast **[UX heuristic WCAG-AA]**; sensible, scalable font sizes.
5. **Interaction affordances & feedback.** Controls are discoverable and give feedback on action; disabled/active states are visible; no interaction that only works via hover **[UX heuristic]**.
6. **State coverage.** Loading, empty, error, `unavailable`/`unknown`, and stale states render sensibly (`ha/frontend-data-api`); the panel is never blank on a missing entity.
7. **Accessibility.** Sensible focus order and keyboard operability; icon-only controls are labelled; images/icons have text alternatives; reduced-motion respected **[UX heuristic]**.
8. **Perceived performance.** Entity-change detection before re-render (no blanket re-render on every `hass` tick, `ha/lovelace-card-patterns`); no synchronous heavy work in `set hass`; no layout thrash.
9. **Navigation & orientation.** Sidebar `title`/`icon` set; the full-page panel gives orientation and handles `route` where it drives sub-navigation.

## Report format

- **Header** — the panel artifact, the `target_devices`, and the applied spec set.
- **Mobile usability verdict** — **PASS / NEEDS-WORK**, with the deciding findings.
- **Findings** — severity-sorted (critical → high → medium → low). Each finding: dimension, location (`file:line`), what is wrong, why it matters (user impact, called out for mobile), the concrete improvement suggestion, and the spec reference or `[UX heuristic]` tag.
- **Work-list for `ha-panel-author`** — the actionable improvements distilled into an ordered list the author skill can consume as its input.
- **Limitations** — findings that need live on-device verification.

## Delegation

- Fixing the findings → `ha-panel-author` (pass this report as its `ux_audit_report` input to drive a prioritized rebuild/refinement)
- Creating a panel that does not yet exist → `ha-panel-author` / `ha-panel-add`
