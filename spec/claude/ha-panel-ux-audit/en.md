# Skill: `ha-panel-ux-audit`

Status: draft

## Context

The panel family can now build panels (`ha-panel-author` end-to-end, `ha-panel-add` the bare scaffold), but nothing evaluates a finished panel from the **user's** point of view — whether a person can actually use it, and above all whether it works on a phone. Home Assistant is used heavily through the mobile companion app, so a panel that only reads well on a wide desktop viewport fails a large share of its real usage. The existing specs already carry the load-bearing facts — `ha/lovelace-layout-antipatterns` E1 (the `narrow` property and the documented mobile single-column collapse), the delivery-shape and layout guardrails, `ha/lovelace-card-patterns` (theming, entity-change discipline), and `ha/frontend-data-api` (unavailable-guarded state) — but no skill audits a panel against them plus general UX and accessibility heuristics.

This skill is the **UX expert** of the panel family: a read-only, static, panel-level audit that produces a severity-sorted improvement report, with **mobile-device usability as a mandatory first-class dimension**. It never modifies the panel; the report is meant to be read and acted on, and — when the user wants — passed to `ha-panel-author` as a prioritized work-list. It is the panel-scoped UX sibling of the integration-level audit skills `ha-quality-scale-audit` and `ha-security-audit`. Quality-scale marker: custom panels and views are **not part of the HA quality scale**; this audit lives outside the scale.

## Scope

Statically auditing exactly one panel-level artifact per run — a custom sidebar panel element (plus its `panel_custom` registration), a panel-mode view, or a custom view — against the binding spec set plus UX/accessibility heuristics, and emitting a severity-sorted report with concrete, spec-referenced improvement suggestions and a distilled work-list for `ha-panel-author`. The audit reads code and config only; it does not render the panel, drive a live instance, or test on real devices, and it never edits anything.

## Goals

- Evaluate a panel from the user's point of view, with mobile-device usability as a required dimension, and emit an explicit **Mobile usability verdict** (PASS / NEEDS-WORK)
- Audit against the existing specs (`ha/lovelace-views-panels`, `ha/lovelace-layout-antipatterns`, `ha/lovelace-card-patterns`, `ha/frontend-data-api`) and reference the governing rule in every finding
- Keep HA facts and UX heuristics cleanly separated — heuristics are labelled and never asserted as HA facts
- Produce severity-sorted, actionable findings whose improvement suggestions `ha-panel-author` can consume directly as a work-list
- Stay strictly read-only — `git status` is unchanged after the run

## Non-Goals

- Building, developing, or fixing a panel — `ha-panel-author` (which may consume this report as `ux_audit_report`)
- Scaffolding a bare panel — `ha-panel-add`
- A whole-integration review (quality-scale, security, consistency) — `ha-integration-reviewer`
- A single custom card's internals as an artifact — `ha/lovelace-card-patterns` scope
- Auto-fixing findings — this skill is read-only
- Rendering the panel, driving a live HA instance, or on-device testing — static audit only; live verification is a complementary manual step
- Defining a reusable HA UX/mobile domain spec — the rubric lives in this skill spec; extracting a `spec/ha/*` UX spec is a possible follow-up

## Requirements

### Activation triggers

- **MUST** activate on phrasings like:
  - "audit my panel's UX", "is this panel usable on mobile", "review the panel for usability and accessibility"
  - "auditiere die UX meines Panels", "ist das Panel auf dem Handy gut nutzbar", "prüfe das Panel auf Barrierefreiheit"
- **MUST NOT** activate for building/fixing a panel (`ha-panel-author`), scaffolding one (`ha-panel-add`), or a whole-integration review (`ha-integration-reviewer`)

### Inputs

- **MUST** capture: `target_dir` (repo root)
- **MAY** capture: `panel` (path/identifier of the panel artifact; discovered and confirmed otherwise), `target_devices` (mobile is always audited; default `mobile + desktop`), `audience`, and `severity_threshold` (default `low`)

### Pre-flight (in order — abort on first failure)

- **MUST** check that `target_dir` is a git repo
- **MUST** locate the panel artifact (custom panel element + `panel_custom` registration, or the panel-mode/custom-view config); when none exists, point at `ha-panel-author` / `ha-panel-add`
- **MUST** read the binding spec set: `ha/lovelace-views-panels`, `ha/lovelace-layout-antipatterns`, `ha/lovelace-card-patterns`, `ha/frontend-data-api`
- **MUST** confirm `target_devices` (mobile always included) and the severity threshold

### Audit dimensions

- **MUST** audit the **mobile usability** dimension on every run and emit a **Mobile usability verdict** (PASS / NEEDS-WORK): the element reads/honours `narrow`; content collapses to a legible single column in a sensible order (`ha/lovelace-layout-antipatterns` E1); no horizontal overflow or fixed-outer-pixel widths that break on small viewports (B4/E1); touch targets are comfortably tappable and there are no hover-only affordances (**[UX heuristic]**); text is legible without pinch-zoom
- **MUST** audit delivery-shape & layout fit (`ha/lovelace-views-panels`; panel-mode view has one card and no badges — A1/A2; no third-party layout tooling — D1; embedded cards sized via `getGridOptions()`/`getCardSize()` — B1/B2/B4)
- **MUST** audit readability/theming/contrast (`ha/lovelace-card-patterns`: HA CSS custom properties, no hard-coded colours; sufficient contrast **[UX heuristic WCAG-AA]**) and state coverage (`ha/frontend-data-api`: loading/empty/error/`unavailable`/stale states render; never blank on a missing entity)
- **MUST** audit information hierarchy & density, interaction affordances & feedback, accessibility (focus order, keyboard operability, labelled icon-only controls, reduced-motion — **[UX heuristic]**), perceived performance (entity-change detection before re-render; no heavy synchronous work in `set hass` — `ha/lovelace-card-patterns`), and navigation/orientation (sidebar `title`/`icon`; `route` handling)
- **MUST** reference the governing spec rule in every HA-fact finding, and tag every general UX/accessibility finding **[UX heuristic]** rather than presenting it as an HA fact

### Report format

- **MUST** emit: a header (panel artifact, `target_devices`, applied spec set); the **Mobile usability verdict** (PASS / NEEDS-WORK) with the deciding findings; severity-sorted findings (critical → high → medium → low), each with dimension, location (`file:line`), the defect, the user impact (called out for mobile), a concrete improvement suggestion, and the spec reference or `[UX heuristic]` tag; a distilled ordered **work-list for `ha-panel-author`**; and a **Limitations** section listing findings that need live on-device verification
- **MUST** phrase each improvement suggestion so `ha-panel-author` can act on it directly; **MUST NOT** emit a vague suggestion with no concrete change

### Prohibitions

- **MUST NOT** modify the panel element, its config, or any file — `git status` is unchanged after the run
- **MUST NOT** render the panel, drive a live HA instance, or claim on-device usability a static audit cannot prove
- **MUST NOT** present a UX/accessibility heuristic as an HA fact, or emit a finding without a spec reference or a `[UX heuristic]` tag

## Acceptance criteria

- [ ] The run is read-only — `git status` is unchanged afterwards
- [ ] The mobile usability dimension is audited and a **Mobile usability verdict** (PASS / NEEDS-WORK) is emitted; a critical mobile finding forces NEEDS-WORK
- [ ] Findings are severity-sorted (critical → high → medium → low), each with location, user impact, and a concrete improvement suggestion
- [ ] Every finding carries a governing-spec reference or a `[UX heuristic]` tag; heuristics are not presented as HA facts
- [ ] The binding spec set is read before auditing, and HA-specific mobile facts rest on `ha/lovelace-layout-antipatterns` E1
- [ ] The report includes a distilled work-list consumable by `ha-panel-author` and a Limitations section for live-verification items
- [ ] Quality-scale marker: not part of the HA quality scale (portfolio audit)

## Open questions

- **Reusable UX domain spec**: the UX/mobile heuristics live in this skill spec. Should they be extracted into a `spec/ha/*` panel-UX/mobile-usability domain spec (like `ha/lovelace-layout-antipatterns`) that both this audit and `ha-panel-author` reference? A follow-up.
- **Static vs live**: the audit is static and cannot prove on-device usability. When does a panel warrant a live-device verification pass, and is that a separate agent/skill?
- **Contrast/touch-target thresholds**: the concrete numbers (WCAG-AA ratios, ≈44–48px targets) are external best practice. Should the skill pin specific thresholds or stay descriptive?
- **Handoff contract with `ha-panel-author`**: the work-list is prose plus an ordered list. Does `ha-panel-author` need a stricter machine-readable schema for the `ux_audit_report` input? Currently prose; a schema is open.
