# ESPHome Project Structure (Repository Layout and Reuse)

Status: draft

## Context

An ESPHome fleet is not one config — it is dozens. The portfolio fixture [`nolte/esphome-configs`](https://github.com/nolte/esphome-configs) currently carries around two dozen device files: seven cameras, seven smart plugs of one model, several grow boxes, two ESP32-S3-BOX-3 units. At that scale the interesting question stops being "what does a device file contain" and becomes "**what do twenty-five device files share, and how**".

This spec answers the second question. It is the repository-level sibling of [`ha/esphome-config-patterns`](../esphome-config-patterns/en.md), which governs a single device YAML — its required blocks, secret handling, and naming. Here the subject is the tree those files live in: which directories exist, how shared configuration is factored into packages, how a device parameterises what it reuses, and how a new device is onboarded without copying anything.

The load-bearing mechanism is ESPHome's **`packages:`** feature. It merges non-destructively — "dictionaries are merged key-by-key, lists of components are merged by component ID (if specified), other lists are merged by concatenation" — and it supports parameterised includes, defaults, remote sources, and surgical `!extend` / `!remove` overrides `[doc]`. Almost every reuse decision in this spec is a decision about how to use that one feature well.

Two structural models exist upstream and this spec takes a position between them: ESPHome's own [`wake-word-voice-assistants`](https://github.com/esphome/wake-word-voice-assistants) gives **each device its own directory** (`esp32-s3-box-3/`, `m5stack-atom-echo/`) with shared assets beside them, while the portfolio fixture keeps **flat device files** over a shared `common/` package directory. The fixture's model scales better for a fleet of similar devices; the upstream model suits a handful of unrelated reference builds.

### Source tiers

- `[doc]` — the official ESPHome documentation at <https://esphome.io>: authoritative for `packages:`, substitution, and merge semantics.
- `[fixture]` — the portfolio's real repository [`nolte/esphome-configs`](https://github.com/nolte/esphome-configs), inspected 2026-08: authoritative for what this portfolio actually does today, **not** automatically for what it should do.
- `[upstream]` — ESPHome's own multi-device repositories (`esphome/firmware`, `esphome/wake-word-voice-assistants`): a comparison point, not a mandate.
- `[policy]` — a nolte-portfolio rule, not an upstream fact.

Verified 2026-08.

## Goals

- Fix one repository layout for an ESPHome fleet, so a reader finds any device, any shared block, and any C++ helper without searching
- Make `packages:` the single reuse mechanism, and say concretely how packages are cut, named, parameterised, and composed
- Define the parameter contract between a device file and the packages it consumes, so a device file stays a short, declarative statement of identity plus deltas
- Give surgical overrides (`!extend`, `!remove`) a place, so a device that deviates does not fork a package
- Fix a credential strategy that survives shared and remote packages, where `!secret` provably does not work
- Make onboarding a new device and retiring an old one mechanical steps rather than copy-paste archaeology
- Record honestly where the fixture and the existing spec currently disagree, instead of papering over it

## Non-Goals

- The content of a single device YAML — required core blocks, per-device platform configuration, and the device-level naming rule belong to [`ha/esphome-config-patterns`](../esphome-config-patterns/en.md)
- Device-specific hardware knowledge — that lives in per-device specs such as [`ha/esp32-s3-box`](../esp32-s3-box/en.md)
- ESPHome custom components in C++/Python (`external_components` authoring) — consuming one is in scope, writing one is a separate axis
- The compile/flash toolchain itself and OTA rollout orchestration across a fleet
- Home Assistant-side concerns (entity exposure, dashboards, the Assist pipeline)
- Repository scaffolding that is not ESPHome-specific — Taskfile, pre-commit, Renovate, release automation, and docs are governed portfolio-wide by the inherited `project/` specs

## Requirements

### Repository layout

- **MUST** keep every device configuration under one config root (fixture: `src/`), with **one file per device named after the device** (`<device-name>.yaml`, kebab-case) `[fixture]` `[policy]`
- **MUST** place reusable YAML under a `common/` directory inside that root, and **MUST NOT** place device files there — the distinction "is this flashed to a device, or included by one" is what makes the tree readable `[fixture]` `[policy]`
- **SHOULD** keep device files **flat** in the config root rather than giving each device its own directory: the fleet is many similar devices, and a directory per device buries the one file that matters. (ESPHome's own reference repos use a directory per device, which fits a handful of unrelated builds rather than a fleet) `[fixture]` `[upstream]` `[policy]`
- **SHOULD** group `common/` **by consumer, not by count**: packages a device includes directly — the base, board packages, feature packages — stay flat, while building blocks that only other packages include move into an ESPHome-domain subdirectory (`common/sensor/`, `common/binary_sensor/`, `common/text_sensor/`, as the fixture already carries). The flat level is then exactly the set of entry points `[fixture]` `[policy]`
- **SHOULD** keep per-device assets (images, sounds) in their own tree keyed by device or device type (`images/<device-type>/`), beside `common/` and `include/`, rather than giving a device its own directory — ESPHome's reference repo does the same with `casita/` and `sounds/` next to its device folders `[upstream]` `[policy]`
- **MUST** keep C++ helper headers consumed by lambdas in a separate `include/` directory, not mixed into `common/`: they are `#include`d by the compiler, not merged by ESPHome, and conflating them hides that difference `[fixture]` `[policy]`
- **SHOULD** move a retired device's file into an `archive/` sibling instead of deleting it, so the configuration survives as pattern history `[fixture]` `[policy]`
- **MUST NOT** let generated or tool-owned state (`.esphome/`, build directories, `secrets.yaml`) enter version control `[policy]`

### Package architecture

- **MUST** use `packages:` as the only reuse mechanism for YAML; the legacy merge-key form (`<<: !include`) **MUST NOT** be introduced in new files, because it does not deep-merge lists and predates packages `[doc]` `[policy]`
- **MUST** declare packages in the **mapping** form with a meaningful key (`packages: {plug: !include …, duration: !include …}`) rather than as an anonymous list: the key names the concern, appears in errors, and is what a later `!extend` targets `[fixture]` `[doc]` `[policy]`
- **MUST** cut packages along **one concern each** — a board package (`common/gosund-sp111.yaml`, `common/esp32-s3-box-3.yaml`), a base package (`common/base.yaml`), and feature packages (`common/time.yaml`, `common/active-duration.yaml`, `common/timer-cancelable.yaml`) — so a device composes exactly the concerns it has `[fixture]` `[policy]`
- **SHOULD** let the **board package** pull in the base package rather than making every device include both: a device then states one board and its extras, and a change to the base reaches the whole fleet through one edge `[fixture]` `[policy]`
- **MUST** understand the merge semantics before relying on them — dictionaries merge key-by-key, **component lists merge by component ID** when an `id:` is given, and all other lists **concatenate** `[doc]`
- **MUST** give an `id:` to any component in a package that a device might later need to extend or remove; without an ID the merge falls back to concatenation and the device gets two components instead of one modified one `[doc]` `[policy]`
- **SHOULD** keep package nesting shallow (device → board → base). Deeper chains make the effective configuration hard to predict, and `esphome config` output is then the only way to know what a device actually has `[policy]`

### Parameterisation

- **MUST** open every device file with a `substitutions:` block declaring the device's identity, using the fixture's three-part convention: `name` (kebab-case, matches the filename), `id` (snake_case, valid as a C++ identifier), and `comment` (human-readable) `[fixture]` `[policy]`
- **MUST** consume those substitutions in packages as `${name}` / `${id}` / `${comment}` rather than repeating literals, so a rename is a one-line change `[fixture]` `[doc]`
- **MUST** know the override direction: substitutions in the consuming configuration **override** same-named substitutions from a package, which is what makes a package parameterisable at all `[doc]`
- **SHOULD** parameterise a package that is instantiated more than once per device through `!include` with `vars:`, passing the device's substitutions in — the fixture does exactly this for its scheduling package (`file: common/active-duration.yaml`, `vars: {time_start: ${time_start}, time_end: ${time_end}}`) `[fixture]` `[doc]`
- **MUST** declare a `defaults:` block in any package that reads a variable which not every consumer sets, so a missing value produces a documented fallback rather than a substitution error — the fixture's base package defaults `project_name` and `project_version` this way `[doc]` `[fixture]`
- **MAY** select a package file by substitution (`!include device-${platform}.yaml`), but **MUST NOT** combine that with the YAML merge key, where filename substitution does not work `[doc]`
- **SHOULD** treat every `${var}` a package reads as part of its public interface: adding one is a breaking change for existing consumers unless it carries a default `[policy]`

### Deviating without forking

- **MUST** resolve a device that needs a package's component *slightly different* through `!extend` on the component's ID, never by copying the package into a device-specific variant `[doc]` `[policy]`
- **MUST** resolve a device that must not have a package-provided component through `!remove` — either on an ID, on a whole section (`captive_portal: !remove`), or on a single attribute `[doc]`
- **MAY** drive `!extend` / `!remove` conditionally from substitutions where a package serves variants of one device family `[doc]`
- **MUST NOT** answer a one-device deviation by creating a near-duplicate package: two packages that differ in one key are the drift this spec exists to prevent `[policy]`
- **SHOULD** promote a deviation into the package as a defaulted variable once a **second** device needs the same override — one deviation is an exception, two are a parameter `[policy]`

### Credentials

- **MUST NOT** place `!secret` lookups in any package that is, or might become, a **remote** package: the documentation states remote packages cannot resolve secrets and directs configurations to substitutions with defaults instead `[doc]`
- **MUST** keep every credential out of version control regardless of mechanism, and **MUST NOT** commit a populated `secrets.yaml` `[policy]`
- **MUST** use `!env_var` for credentials, as the fixture does for Wi-Fi SSID, password, domain, and fallback-hotspot password: environment variables reach both a local build and a CI build without a file that must never be committed, and they work in packages where `!secret` provably cannot. This is the portfolio's credential mechanism; [`ha/esphome-config-patterns`](../esphome-config-patterns/en.md) carries the same rule `[fixture]` `[doc]` `[policy]`
- **MUST** document every environment variable a package reads, so a fresh checkout can be built without reverse-engineering the failure messages `[policy]`
- **MUST** keep the API-encryption requirement from [`ha/esphome-config-patterns`](../esphome-config-patterns/en.md) intact across packages: a base package that declares a bare `api:` leaves every device consuming it unencrypted at once, which is exactly the blast radius shared packages create. The fixture's base package currently does this and is a defect to fix, not a variant to codify `[fixture]` `[policy]`

### Remote packages

- **MAY** consume a package from a Git repository through the shorthand (`github://user/repo/file.yml@ref`) or the extended form with `url`, `files`, `ref`, `refresh`, and optional credentials `[doc]`
- **MUST** pin a remote package to an immutable-enough `ref` (a tag or a commit, not a moving branch) — an unpinned remote package means a build's content changes without a commit in this repository `[doc]` `[policy]`
- **MUST** set `refresh` deliberately when a `ref` is a branch, and treat the resulting non-reproducibility as the cost being accepted `[doc]` `[policy]`
- **SHOULD** prefer **vendoring** a third-party package into `common/` over referencing it remotely, consistent with the decision recorded in [`ha/esp32-s3-box`](../esp32-s3-box/en.md): a vendored package is reviewable in the diff, builds offline, and changes only when someone changes it `[policy]`
- **MUST** pass parameters into a remote package through substitutions with defaults rather than expecting it to reach back into the consumer's secrets `[doc]`

### Naming and fleet conventions

- **MUST** name a device file after the device, and the device after what it is plus an ordinal when several of a kind exist — the fixture's `gosund-sp111-01` … `gosund-sp111-07` and `cam-01` … `cam-07` are the pattern `[fixture]` `[policy]`
- **MUST** keep `name` (kebab-case) and `id` (snake_case) derived from the same string, so the mapping between filename, network name, and C++ identifier stays mechanical `[fixture]` `[policy]`
- **SHOULD** name a board package after the board (`gosund-sp111.yaml`, `nous-a1t.yaml`, `ulanzi-tc001.yaml`) and a feature package after the capability (`time.yaml`, `active-duration.yaml`, `pixel_art.yaml`), so the import list reads as a sentence about the device `[fixture]` `[policy]`
- **SHOULD** declare `esphome.project.name` / `.version` in the base or board package so a flashed device reports what it is, as the fixture does `[fixture]` `[doc]`
- **MUST NOT** encode a device's location or purpose in its `name` when that can change — the fixture keeps location in `comment` and identity in `name`, which is why a moved device needs no rename `[fixture]` `[policy]`

### Lifecycle

- **MUST** onboard a new device of an existing kind by creating **only** a device file: substitutions plus the board package plus any feature packages. If onboarding requires touching a package, the package was cut wrong `[fixture]` `[policy]`
- **MUST** onboard a new *kind* of device by adding one board package and then the device file, rather than by writing a self-contained device config `[policy]`
- **SHOULD** retire a device by moving its file to `archive/`, keeping it out of the build while preserving the pattern `[fixture]` `[policy]`
- **SHOULD** treat legacy artefacts in `archive/` (the fixture keeps `include-*.yaml.snipped` merge-key snippets there) as read-only history, never as a template for new work `[fixture]` `[policy]`

### Validation

- **MUST** validate every device configuration with `esphome config <file>` before it is committed; the resolved output is also the only reliable answer to "what does this device actually have after all packages merged" `[doc]` `[policy]`
- **MUST** run `esphome config` for **every** device file on every change in CI, not only for the files in the diff: a package edit can break a device whose file nobody touched, which is the characteristic failure mode of a shared-package repository, and schema validation is fast enough to afford fleet-wide `[policy]`
- **SHOULD** reserve the full `esphome compile` for a nightly or pre-release run rather than every pull request — compile time grows with the fleet, while the fleet-wide `config` pass already catches the package-breaks-untouched-device case `[policy]`
- **SHOULD** keep the repository's static checks (YAML lint, spelling, pre-commit) as a gate alongside the ESPHome validation — the fixture ships `build-static-tests.yaml` plus a yamllint and spelling setup `[fixture]` `[policy]`
- **MUST** report validation as an open caller step when the ESPHome toolchain is unavailable, rather than silently skipping it `[policy]`

### Verification

- **MUST** verify `packages:`, substitution, and merge behaviour against the official ESPHome documentation before relying on it, per [`ha/upstream-docs-verification`](../upstream-docs-verification/en.md) `[policy]`
- **MUST NOT** treat the fixture as normative on its own: it is evidence of current practice and carries known deviations from the portfolio's own specs (see Credentials and Open Questions) `[policy]`
- **SHOULD** re-verify the merge and override rules when ESPHome introduces new package features, since `!extend`, `!remove`, and conditional inclusion each changed what "reuse" can mean `[policy]`

## Acceptance Criteria

- [ ] Every device has exactly one file, named after it, flat in the config root; nothing under `common/` is flashable
- [ ] Shared YAML lives in `common/`, C++ helpers in `include/`, retired devices in `archive/`
- [ ] Reuse happens through `packages:` in mapping form with meaningful keys; no new `<<: !include` merge keys exist
- [ ] Each package covers one concern; a device composes a board package plus feature packages, and the board package pulls in the base
- [ ] Every device file opens with `name` / `id` / `comment` substitutions, and packages reference them instead of literals
- [ ] Any package reading a variable not every consumer sets declares a `defaults:` fallback
- [ ] Components that devices may need to override carry an explicit `id:`
- [ ] Deviations use `!extend` / `!remove`; no near-duplicate package exists that differs from another in one key
- [ ] No credential is committed, and no package that could become remote contains a `!secret` lookup
- [ ] Any remote package is pinned to a tag or commit, or a deliberate `refresh` is documented
- [ ] Onboarding a device of an existing kind touched only one new file
- [ ] `esphome config` passes for every device file, and CI validates all of them rather than only the changed ones

## Open Questions

- **Fixture remediation**: this spec and the amended [`ha/esphome-config-patterns`](../esphome-config-patterns/en.md) now describe a state the fixture does not yet meet — its base package declares a bare `api:` without `encryption:`. Who fixes that, and does the fleet need a coordinated re-flash once the key is introduced (every device loses its Home Assistant connection until the key is entered on the HA side)?

Settled by decision (kept here so the rationale stays findable, not as open work): credentials use **`!env_var`**, and `ha/esphome-config-patterns` was amended to match rather than the other way round, because remote packages provably cannot resolve `!secret`. API encryption stays a **requirement**, so the fixture's bare `api:` is a defect rather than an accepted variant. Device files stay **flat** with per-device assets in their own keyed tree. `common/` groups **by consumer** — entry points flat, building blocks in domain subdirectories. CI runs `esphome config` **fleet-wide** on every change with `compile` reserved for nightly. Board packages carry **no version substitution**; fleet-wide validation catches an incompatible change in the same pull request.
