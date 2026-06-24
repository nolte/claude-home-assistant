# HA Integration: Dev Workflow (Guidelines, Typing, Validation)

Status: draft

## Context

A Custom Integration for Home Assistant is Python code that must align with the HA Core code style: HA enforces strict [PEP8](https://peps.python.org/pep-0008/) and [PEP 257](https://peps.python.org/pep-0257/) compliance on any submitted code, formatted with [Ruff](https://docs.astral.sh/ruff/), and checks type annotations statically in CI. The HA documentation (`development_guidelines.md`, `development_typing.md`, `development_validation.md`, `development_checklist.md`) defines these coding conventions — but they are spread across several pages and not phrased as an operationalizable obligation.

This spec bundles the **coding workflow** of a Custom Integration into an enforceable form: code style (line length, import order, f-strings, Ruff/Pylint), strict typing (`from __future__ import annotations`, the `.strict-typing` opt-in, mypy), and validation (`hassfest`, manifest/strings/services validation). It pins the HA original rules so a skill can apply them automatically and a reviewer can check them off.

The delineation is strict: the devcontainer / Kind setup belongs to `ha/dev-environment`, the pytest harness to `ha/test-harness`. This spec addresses exclusively **how the code is written, typed, and validated** before it is submitted.

Quality scale marker: **bronze→platinum** (code style and `hassfest` are a bronze floor; strict typing via `.strict-typing` is the platinum `strict-typing` rule, see `ha/quality-scale`).

## Goals

- Establish HA code style (PEP8/PEP257, Ruff formatting, ordered imports, alphabetical constants/lists, f-strings) as an enforceable obligation
- Establish strict typing — full annotations, `from __future__ import annotations`, inclusion in `.strict-typing`, mypy run — as the bridge to the platinum `strict-typing` rule
- Mandate `hassfest` (`python3 -m script.hassfest`) as the required validation before submission — manifest, strings, services
- Mandate voluptuous-based config validation (`config_validation.py` helper, `const.py` constants, required-before-optional) for YAML-configurable platforms
- Convert the pre-submit checklist from `development_checklist.md` into a checkable list
- Delineate clearly against `ha/dev-environment` (setup) and `ha/test-harness` (pytest) without duplicating them

## Non-Goals

- Devcontainer / Kind-cluster setup, `script/setup`, venv bootstrap — belongs to `ha/dev-environment`
- Pytest harness, snapshot tests, fixtures, coverage reports — belongs to `ha/test-harness`
- Async / event-loop patterns (`async def`, executor jobs, blocking I/O) — belongs to `ha/async-patterns`
- Manifest-schema authoring in detail (`manifest.json` fields, versioning) — belongs to `ha/integration-manifest`; this spec only requires that `hassfest` validates it
- The quality-scale rule catalog itself — belongs to `ha/quality-scale`; this spec only references the `strict-typing` rule
- MonkeyType-assisted migration workflows for legacy code — optional, not a mandatory part of skill output

## Requirements

### Code style & guidelines

- **MUST** produce PEP8- and PEP257-compliant code and format it with Ruff (`ruff format`) — HA never merges submissions that diverge
- **MUST** order imports ([PEP8 imports](https://peps.python.org/pep-0008/#imports)) and sort constants as well as the content of lists and dictionaries alphabetically
- **MUST** prefer [f-strings](https://docs.python.org/3/reference/lexical_analysis.html#f-strings) over `%` or `str.format` formatting — the only exception is logging, which uses percentage formatting to render the message only when needed (`_LOGGER.info("... %s ...", value)`)
- **MUST** carry a file-header docstring describing what the file is about (for example `"""Support for MQTT lights."""`)
- **SHOULD** write comments as full sentences ending with a period
- **SHOULD** omit platform/component names and trailing periods in log messages (added automatically), never log API keys, tokens, usernames, or passwords, and use `_LOGGER.info` restrictively — anything not targeting the user goes through `_LOGGER.debug`
- **MAY** use [Google-style](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods) docstrings for extended parameter/return/raises documentation; type information belongs in the annotations and is omitted from the docstring

### Typing (strict)

- **MUST** fully type-annotate the code — HA checks type annotations statically in CI and assumes everything is type checked unless explicitly excluded
- **MUST** add the module to the `.strict-typing` file at the root of the HA Core project once it is fully typed — this enables the strict checks and at the same time satisfies the platinum `strict-typing` rule (see `ha/quality-scale`)
- **SHOULD** carry `from __future__ import annotations` at the module top so annotations are evaluated as strings and forward references work without quote strings
- **SHOULD** run mypy against the module before submitting it — the CI type check mirrors this run
- **MAY** use `assert` statements for type narrowing, but **only** inside an `if TYPE_CHECKING:` block, so they exist solely for the type checker and do not affect runtime behavior
- **MAY** use [MonkeyType](https://pypi.org/project/MonkeyType/) (`script/monkeytype`) for the initial instrumentation of fully untyped modules; the generated stub is always corrected manually afterward

### Validation (`hassfest`)

- **MUST** run `python3 -m script.hassfest` before submission — the run validates the integration and updates generated artifacts (including `CODEOWNERS`)
- **MUST** shape the integration so `hassfest` passes without errors — this covers validation of the manifest (see `ha/integration-manifest`), the translation/strings files, and the service definitions
- **MUST** use voluptuous to validate any YAML configuration the user provides, when the platform is YAML-configurable
- **SHOULD** use the constants from `const.py` when building schemas, import and extend the target integration's `PLATFORM_SCHEMA`, order `required` keys before `optional` keys, and set valid defaults for optional keys (no `default=None` for `cv.string`; use `default=''` instead)
- **MAY** use the HA custom validators from [`config_validation.py`](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/config_validation.py) (`cv.port`, `cv.ensure_list`, `vol.In([...])`, `entity_id`, `slug`, …) instead of raw voluptuous types

### Pre-submit checklist

- **MUST** wrap any communication with external devices or services in an external Python library hosted on [PyPI](https://pypi.org/) — with a source distribution available (no binary-only distributions) and issue tracker enabled
- **MUST** add new dependencies to `requirements_all.txt` via `python3 -m script.gen_requirements_all` (if applicable)
- **MUST** add new codeowners to `CODEOWNERS` via `python3 -m script.hassfest` (if applicable)
- **MUST** format the code with Ruff (`ruff format`) and update the `.strict-typing` file when the code is fully type-annotated
- **SHOULD** develop documentation for [home-assistant.io](https://home-assistant.io/) when the integration introduces user-visible behavior
- **MAY** suppress unavoidable Pylint warnings line by line with `# pylint: disable=YOUR-ERROR-NAME` — only when the warning is provably wrong (for example a mis-reported missing member)

### Delineation (dev environment / test harness)

- **MUST NOT** define setup mechanics (devcontainer, Kind cluster, `script/setup`, venv, `kubectl cp` / `kill 1`) here — that belongs to `ha/dev-environment`
- **MUST NOT** define the pytest harness (fixtures, `MockConfigEntry`, snapshot tests, coverage) here — that belongs to `ha/test-harness`; this spec covers only style/typing/validation of the code to be submitted
- **SHOULD** reference sibling specs by slug instead of duplicating them: `ha/dev-environment`, `ha/test-harness`, `ha/async-patterns`, `ha/quality-scale`, `ha/integration-manifest`

## Acceptance Criteria

- [ ] Code is PEP8/PEP257-compliant and formatted with `ruff format`
- [ ] Imports are ordered; constants, list, and dictionary contents are sorted alphabetically
- [ ] String formatting uses f-strings (exception: logging via percentage formatting)
- [ ] Code is fully type-annotated and the module is added to `.strict-typing`
- [ ] `from __future__ import annotations` is at the module top; mypy passes without errors
- [ ] `assert` type narrowing appears exclusively inside `if TYPE_CHECKING:` blocks
- [ ] `python3 -m script.hassfest` passes without errors (manifest, strings, services)
- [ ] YAML-configurable platforms validate input via voluptuous with `const.py` constants
- [ ] External communication is wrapped in a PyPI library with a source distribution and an active issue tracker
- [ ] New dependencies added via `python3 -m script.gen_requirements_all`, new codeowners via `hassfest`
- [ ] Quality scale marker: **bronze→platinum** (`hassfest`/style = bronze floor, `.strict-typing` = platinum rule)

## Open Questions

- **`.strict-typing` applicability for Custom Integrations**: The `.strict-typing` file lives in the HA Core repo. A standalone Custom Integration (outside Core) needs an equivalent local mypy strict profile. Should the spec pin a `pyproject.toml` `[tool.mypy]` strict snippet as the Custom-Integration counterpart?
- **`hassfest` outside Core**: `python3 -m script.hassfest` requires the Core `script` package. Custom Integrations need either a vendored `hassfest` or a pre-commit hook (`home-assistant/actions`). Which variant is preferred portfolio-wide?
- **Ruff-vs-Pylint configuration**: HA Core ships a curated Ruff/Pylint config. Should the spec pin a concrete `ruff.toml`/`.pylintrc` baseline for Custom Integrations or reference the Core config?
- **Voluptuous relevance for config-flow-only integrations**: Modern integrations are config-flow-based and not YAML-configurable. Should the voluptuous requirement stay marked "applicable only with YAML configuration" or be extended to config-flow voluptuous schemas?
