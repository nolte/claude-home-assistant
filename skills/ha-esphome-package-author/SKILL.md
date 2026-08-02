---
name: ha-esphome-package-author
description: "Authors or reshapes exactly one shared ESPHome package under common/ per spec/ha/esphome-project-structure — cutting a concern out of duplicated device blocks, giving it a substitution interface with a defaults fallback, adding the id keys devices need to override a component, resolving a one-device deviation through !extend / !remove instead of a near-duplicate package, promoting a repeated override into a defaulted parameter, and pinning or vendoring a remote package. Reads every consumer first and states the merge consequences before writing. Activate on \"factor this into a package\", \"parameterise the board package\", \"two configs share this block\", or equivalent German requests. Do not activate to lay out the repository (ha-esphome-fleet-scaffold), to add a block to one device (ha-esphome-config-augment), to create a device file (ha-esphome-config-scaffold), or to audit the architecture (ha-esphome-fleet-reviewer)."
tags: [home-assistant, esphome, yaml, refactoring]
phase: build
summary: "Authors or reshapes one shared ESPHome package — concern cut, substitution interface with defaults, id keys, !extend / !remove instead of a fork."
summary_de: "Erstellt oder überarbeitet ein einzelnes gemeinsames ESPHome-Package — Concern-Schnitt, Substitutions-Interface mit defaults, id-Keys, !extend / !remove statt Fork."
use_when:
  - "the same block appears in two or more device files and should become a package"
  - "a package needs a parameter so a device can vary it instead of forking the file"
  - "one device needs a package's component slightly different or not at all"
  - "a remote package must be pinned to an immutable ref or vendored into the repository"
dont_use_when:
  - situation: "You want the repository tree and the initial package set"
    alternative: ha-esphome-fleet-scaffold
  - situation: "You want one more sensor, bus, or component in one device file"
    alternative: ha-esphome-config-augment
  - situation: "You want a new device config file"
    alternative: ha-esphome-config-scaffold
  - situation: "You want a verdict on whether the package architecture conforms"
    alternative: ha-esphome-fleet-reviewer
see_also:
  - ha-esphome-fleet-scaffold
  - ha-esphome-config-augment
  - ha-esphome-fleet-reviewer
  - ha-esphome-solution
---

# HA ESPHome Package Author

Spec: `spec/claude/ha-esphome-package-author/en.md` (EN canonical) / `spec/claude/ha-esphome-package-author/de.md` (DE translation). Grounding spec: `spec/ha/esphome-project-structure/en.md` §Package architecture, §Parameterisation, §Deviating without forking, §Remote packages.

Owns one shared package per invocation: how it is cut, what its parameter interface is, and how a deviating device consumes it without forking it.

## Why this is a skill, not an agent

- **Mid-flow approval is the contract (decisive):** where the concern boundary runs, which variables become the package's public interface, and whether a deviation is an `!extend` or a new parameter are judgement calls the operator confirms — and each one is a breaking change for existing consumers if it is wrong.
- **Quick, targeted change in the current context:** one file under `common/` plus the consuming device files, iterated in conversation.
- **Counter-dimension considered:** reading every consumer of the package before writing is a bounded fan-out that could be isolated (agent bias), but the resulting interface decision must be discussed, not reported; skill wins.

## When this skill activates

The user wants shared ESPHome configuration to become or stay one well-cut package — "das gehört ins gemeinsame Package", "make the board package take a parameter for the update interval", "box-02 needs the base package without `captive_portal`".

## When NOT to activate

- the repository tree, the initial base/board packages → `ha-esphome-fleet-scaffold`
- a block that belongs to exactly one device → `ha-esphome-config-augment`
- a new device file → `ha-esphome-config-scaffold`
- a read-only verdict across the whole package architecture → `ha-esphome-fleet-reviewer`
- compiling, flashing, or rolling out → the ESPHome toolchain / operator

## Hard rules

1. **Read the grounding spec, the package, and every consumer first.** A package edit reaches every device that includes it; generating one from memory is how a fleet breaks silently.
2. **One concern per package.** A board package, a base package, a feature package — never a grab bag, and never a near-duplicate that differs from an existing package in one key.
3. **Two occurrences make a parameter.** One deviation is an exception resolved with `!extend` / `!remove` on the component's **config id**; the second identical override is promoted into the package as a defaulted variable. `!extend` never targets a package key — package keys are documentation only.
4. **Every variable a package reads that not every consumer sets carries a `defaults:` entry.** Adding a variable without a default is a breaking change for existing consumers, and this skill states that in the report.
5. **`id:` on anything overridable.** A component a device might extend or remove gets an explicit `id:`; otherwise the merge concatenates and the device ends up with two components.
6. **State the merge consequences before writing.** Dictionaries merge key-by-key, component lists merge by id, other lists concatenate, and every other value is replaced by the later one — the last clause is the one that silently lets a device scalar win.
7. **Credentials stay `!env_var`, and no `!secret` enters a package** that is or could become remote. `!env_var` is undocumented API and cannot interpolate substitutions in its name; new variables get documented in the same run.
8. **Remote packages are pinned or vendored.** A tag or commit, never a moving branch without a deliberate, documented `refresh`; prefer vendoring into `common/`.
9. **Keep nesting shallow** (device → board → base) and pass parameters in through substitutions rather than letting a package reach back into a consumer's secrets.
10. **One package per run.** No fleet-wide refactoring batches; validation is reported, never silently skipped.

## Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `operation` | yes | — | `cut` (new package from duplication), `parameterise`, `deviate` (`!extend` / `!remove`), `promote` (deviation → parameter), `remote` (pin / vendor) |
| `package` | conditional | — | target file under `common/`; required for every operation but `cut` |
| `consumers` | no | discovered | device files that include the package |
| `concern` | conditional | — | the single concern a `cut` covers |

## Pre-flight (every run, in order — abort on first failure)

1. Resolve the package and **every** consumer (device files and other packages that include it).
2. On `cut`: prove the duplication — show the identical blocks and the files they live in; a single occurrence is not a package.
3. On `parameterise` / `promote`: list every consumer that does **not** set the new variable, so the `defaults:` entry is derived from evidence rather than assumed.
4. On `deviate`: confirm the component carries an `id:`; when it does not, adding one to the package is part of this run and affects every consumer.
5. Present the planned interface change (new variables, defaults, ids, removals) and the merge consequences per consumer; wait for approval.

## Workflow

1. Verify every schema key against the official ESPHome docs per `spec/ha/upstream-docs-verification` — packages, `!extend`, `!remove`, and `vars:` semantics included.
2. Apply the operation:
   - **cut** — write the new concern-scoped package under `common/` (flat when devices include it directly, in the ESPHome-domain subdirectory when only other packages do), then rewrite each consumer to include it and delete the duplicated blocks.
   - **parameterise** — replace literals with `${var}`, add the `defaults:` block, and pass values from the consumers; where the package is instantiated more than once per device, use `!include` with `vars:`.
   - **deviate** — add `!extend` on the component id in the consuming device file, or `!remove` on the id, section, or attribute; the package itself stays untouched.
   - **promote** — fold the repeated override into the package as a defaulted variable and remove the now-redundant `!extend` from both devices.
   - **remote** — pin `ref` to a tag or commit, or vendor the file into `common/` and rewrite the consumers to the local path.
3. Update the environment-variable documentation when the change adds or removes one.
4. Validate: `esphome config` for **every** consumer, not only the one at hand — a package edit is exactly the change that breaks an untouched device. Where the toolchain is unavailable, report it as the open caller step.
5. **Report:** the package diff, the per-consumer effect, new variables and their defaults, ids added, any consumer left needing a follow-up, and validation status.

## Boundaries

- Repository layout and the initial package set → `ha-esphome-fleet-scaffold`
- A device-only block → `ha-esphome-config-augment`
- Home-Assistant-driven values inside a package → `ha-esphome-binding-add`
- A conformance verdict over the architecture → `ha-esphome-fleet-reviewer`
- Compile, flash, rollout → the ESPHome toolchain / operator
