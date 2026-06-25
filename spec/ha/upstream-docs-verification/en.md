# HA Artifacts: Verification Against Official Docs

Status: draft

## Context

This plugin's skills, agents, and specs produce Home Assistant artifacts — Custom Integrations (Python), Lovelace cards (TypeScript/JavaScript), blueprints and automations (YAML), and ESPHome / add-on work. HA-internal APIs, naming conventions, quality-scale criteria, and frontend contracts change across releases; assumptions reproduced from memory go stale silently and then propagate into generated code, specs, and answers.

Home Assistant maintains two authoritative, publicly versioned documentation sources:

- **Developer docs** — [`home-assistant/developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant) (rendered at `developers.home-assistant.io`): integration internals, config flow, entities, coordinators, quality scale, frontend/WebSocket contracts.
- **User / architecture docs** — [`home-assistant/home-assistant.io`](https://github.com/home-assistant/home-assistant.io) (rendered at `www.home-assistant.io`): architecture, blueprints, YAML schemas, end-user-facing behaviour.

This spec lifts verification against these two sources from an ad-hoc habit to a cross-cutting obligation for every HA artifact this plugin produces. It complements the existing `Adaptionsquelle` (adaptation-source) convention in `spec/README.md`, which records that every `ha/` spec is anchored to a concrete doc file.

## Goals

- Verify every uncertain claim about HA internals against the official docs before it is asserted, committed to code, or written into a spec
- Name the two authoritative sources unambiguously and delimit their respective scope
- Anchor verified claims to a concrete doc file so drift remains traceable later
- Phrase the obligation so it covers both answers to the user and generated artifacts

## Non-Goals

- Mirror or summarise the doc content here — this spec mandates the lookup, it does not replace it
- Maintain an exhaustive per-topic source list — the `Adaptionsquelle` convention in `spec/README.md` covers the topic-to-doc mapping
- Elevate external third-party sources (forums, blog posts, third-party integrations) to authoritative status — they are at most supplementary, never a substitute
- Define an automated drift check against upstream — that is reserved for a later spec

## Requirements

### Scope

- **MUST** apply to every HA artifact this plugin creates or modifies: integration code, Lovelace cards, blueprints, automations, service definitions, translations, tests, and the `ha/` specs themselves
- **MUST** apply both to answers directed at the user and to content written to disk

### Verification obligation

- **MUST** verify any uncertain claim about HA internals (API signatures, lifecycle hooks, conventions, quality-scale criteria, frontend/WebSocket contracts, YAML schemas) against the official docs before the claim enters an answer, generated code, or a spec
- **MUST** consult the source rather than answer from memory when in doubt — uncertainty is the trigger, not a later correction
- **SHOULD** fetch the `raw.githubusercontent.com` version of the relevant file when the exact wording or revision matters

### Source selection

- **MUST** verify integration internals, config flow, entities, coordinators, quality scale, and frontend/WebSocket contracts against [`developers.home-assistant`](https://github.com/home-assistant/developers.home-assistant)
- **MUST** verify architecture, blueprints, YAML schemas, and end-user-facing behaviour against [`home-assistant.io`](https://github.com/home-assistant/home-assistant.io)
- **MUST NOT** treat forums, blog posts, or third-party repos as the authoritative source — they supplement the official docs, never replace them

### Anchoring

- **SHOULD** anchor a verified, non-obvious claim to the concrete doc file (path relative to the respective repo) so later drift stays traceable
- **SHOULD** note the revision (year/release) when a claim is version-dependent

## Acceptance Criteria

- [ ] The two authoritative sources are named and their scope is delimited
- [ ] The obligation explicitly applies to answers to the user **and** to generated artifacts
- [ ] Uncertainty about HA internals triggers a doc consultation before the claim is used
- [ ] Integration internals are verified against `developers.home-assistant`, architecture/blueprints/YAML against `home-assistant.io`
- [ ] Forum/blog/third-party sources are explicitly marked non-authoritative
- [ ] Non-obvious verified claims are anchored to a concrete doc file

## Open Questions

- **Automated drift check**: Should a later spec define a mechanical reconciliation of generated assumptions against the upstream HEAD (analogous to the DE↔EN spec-drift check)?
- **Pinning to release revisions**: Should anchoring pin to a concrete HA release, or does pointing at the doc repos' `dev` branch suffice?
- **Verification cache**: Is a reusable cache of frequently looked-up doc facts worthwhile, or does it undercut the freshness guarantee of live consultation?
