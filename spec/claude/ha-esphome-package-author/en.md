# Skill: `ha-esphome-package-author`

Status: draft

## Context

`spec/ha/esphome-project-structure` makes `packages:` the single reuse mechanism of an ESPHome fleet and spends most of its requirements on how that one feature is used well — concern cuts, substitution interfaces with defaults, `id:` coverage, `!extend` / `!remove` instead of forks, remote pinning. Those are per-package decisions taken repeatedly over a repository's life, not once at scaffold time. This skill owns them: it is where a duplicated block becomes a package, where a package grows a parameter, and where a deviating device is resolved without a near-duplicate file appearing.

## Scope

One package per invocation, plus the consumers the change reaches. Five operations: `cut`, `parameterise`, `deviate`, `promote`, `remote`. Ends at the written package, the updated consumers, and a fleet-wide validation report.

## Goals

- Make the "two occurrences make a parameter" rule operational instead of aspirational
- Keep every package interface explicit: which variables it reads, which carry defaults, which components can be overridden
- Resolve deviation without forking, and detect when a deviation has earned promotion
- Make the merge consequences of a package change visible before the change is written
- Ensure a package edit is validated against **every** consumer, not only the device that prompted it

## Non-Goals

- The repository tree and the initial package set (owned by `ha-esphome-fleet-scaffold`)
- Device-only blocks (owned by `ha-esphome-config-augment`)
- Home-Assistant-driven bindings inside a package (owned by `ha-esphome-binding-add`)
- A conformance verdict over the package architecture (owned by the read-only `ha-esphome-fleet-reviewer`)
- Compile, flash, and rollout

## Requirements

- **MUST** read `spec/ha/esphome-project-structure/en.md` §Package architecture, §Parameterisation, §Deviating without forking and §Remote packages, plus the package and **every** consumer, before writing
- **MUST** prove duplication before a `cut`: a single occurrence is not a package
- **MUST** keep one concern per package and **MUST NOT** create a package that differs from an existing one in a single key
- **MUST** resolve a first deviation through `!extend` / `!remove` on the component's config id — never on a package key, which the documentation states has no significance — and **MUST** promote the override into a defaulted variable once a second device needs it
- **MUST** declare a `defaults:` entry for every variable a package reads that not all consumers set, and **MUST** report an added variable without a default as a breaking change for existing consumers
- **MUST** add an explicit `id:` to any component that becomes overridable, and state that the addition reaches every consumer
- **MUST** state the merge consequences — dictionaries key-by-key, component lists by id, other lists concatenated, all other values replaced by the later one — for the change at hand before writing
- **MUST** keep credentials as `!env_var`, **MUST NOT** place a `!secret` lookup in a package that is or could become remote, and **MUST** document any new variable in the same run
- **MUST** pin a remote package to a tag or commit, or vendor it into `common/`; a moving branch requires a documented, deliberate `refresh`
- **MUST** validate **every** consumer with `esphome config` where the toolchain is available, and report it as the caller's open step where it is not
- **MUST** verify package, substitution, `!extend`, `!remove`, and `vars:` semantics against the official ESPHome docs per `spec/ha/upstream-docs-verification`
- **MUST NOT** change more than one package per run

## Acceptance Criteria

- [ ] A `cut` run produces a concern-scoped package and rewrites every consumer, leaving no duplicated block behind
- [ ] A `parameterise` or `promote` run leaves every existing consumer building unchanged, because the new variable carries a default derived from those consumers
- [ ] A `deviate` run changes only the consuming device file; the package stays untouched
- [ ] The report states the per-consumer effect and the validation result for each consumer, not only for the device that prompted the change

## Open Questions

_None at this time._
