#!/usr/bin/env python3
"""Generate the Skills and Agents catalog as physical Markdown files.

Operationalises ``spec/claude/skill-agent-catalog/<canonical_language>.md``.

Architecturally this script writes physical files under ``docs/<lang>/`` rather
than emitting through ``mkdocs-gen-files``. The reason: the installed
``mkdocs-static-i18n`` (1.3.x) only classifies files whose ``abs_src_path`` is
under ``mkdocs_config.docs_dir``; ``gen-files`` virtual files live in a temp
directory and are silently dropped from the i18n file set. Writing physical
files satisfies the spec's hard rules just as well — they're gitignored under
``/docs/<lang>/skills/`` etc. so the "no committed generated markdown" rule
still holds.

Sources are configured in ``docs/catalog-sources.yml``. For each configured
plugin source root the script walks ``<local>/<skills_path>/<name>/SKILL.md``
and ``<local>/<agents_path>/<name>.md``, parses the YAML-ish frontmatter, and
emits one catalog page per artifact per configured docs language plus
``SUMMARY.md`` files for ``mkdocs-literate-nav`` and a ``tags.md`` index.

The build fails (non-zero exit, ``CatalogError``) on malformed frontmatter;
the spec forbids silently skipping broken artefacts.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"
SOURCES_FILE = DOCS_DIR / "catalog-sources.yml"
MKDOCS_FILE = REPO_ROOT / "mkdocs.yml"

# Canonical phase order, declared by spec/claude/skill-agent-catalog/ §Phase classification.
# Order matters: every renderer uses this sequence so the navigation stays stable.
PHASE_ORDER: tuple[str, ...] = (
    "vision",
    "plan",
    "design",
    "build",
    "review",
    "quality",
    "close-release",
    "cross-cutting",
)
PHASE_VOCABULARY: frozenset[str] = frozenset(PHASE_ORDER)

# Limits per spec/claude/skill-agent-catalog/ §Per-language short summary and §Use-case metadata.
SUMMARY_MAX_LEN = 200
USE_WHEN_MAX_ENTRIES = 6
USE_WHEN_MAX_LEN = 120
DONT_USE_WHEN_MAX_ENTRIES = 6
DONT_USE_WHEN_SITUATION_MAX_LEN = 120
SEE_ALSO_MAX_ENTRIES = 8
EXAMPLES_MAX_ENTRIES = 4
EXAMPLES_FIELD_MAX_LEN = 200

# Reserved auto-tag emitted by the generator when a non-English page falls back to the English
# summary or the description truncation, per spec §Per-language short summary.
AUTO_TAG_TRANSLATION_PENDING = "_translation-pending"

# The canonical metadata language summary (vs. summary_<lang>) is authored in,
# per spec §Per-language short summary.
SUMMARY_CANONICAL_LANG = "en"

CHROME = {
    "de": {
        "skills_title": "Skills",
        "skills_intro": (
            "Auto-generierter Katalog aller Skills aus den konfigurierten Plugin-Source-Roots. "
            "Inhalt stammt direkt aus den `SKILL.md`-Frontmattern und -Bodies. "
            "Gruppiert nach Phase des Liefer-Lebenszyklus."
        ),
        "agents_title": "Agents",
        "agents_intro": (
            "Auto-generierter Katalog aller Agents aus den konfigurierten Plugin-Source-Roots. "
            "Inhalt stammt direkt aus den Agent-Markdown-Dateien. "
            "Gruppiert nach Phase des Liefer-Lebenszyklus."
        ),
        "tags_title": "Tags",
        "tags_intro": (
            "Querverweise: jeder Tag listet alle Skills und Agents, die ihn deklarieren."
        ),
        "no_tags": "Bisher sind keine Tags vergeben.",
        "source_label": "Quelle",
        "distribution_label": "Distribution",
        "tags_label": "Tags",
        "plugin_label": "Plugin",
        "phase_label": "Phase",
        "use_when_label": "Anwenden wenn",
        "dont_use_when_label": "Nicht anwenden wenn",
        "see_also_label": "Siehe auch",
        "referenced_by_label": "Referenziert von",
        "examples_label": "Beispiele",
        "example_prompt_label": "Prompt",
        "example_outcome_label": "Ergebnis",
        "translation_pending_badge": "🚧 Übersetzung ausstehend",
        "by_task_link_label": "Nach Aufgabe stöbern →",
        "by_task_title": "Nach Aufgabe",
        "by_task_intro": (
            "Aufgaben-orientierte Einstiegs-Seite: gruppiert Skills und Agents nach Nutzer-Absicht "
            "statt nach Phase. Hand-kuratiert; erweitern, sobald neue Use-Case-Muster sichtbar werden."
        ),
        "by_task_skeleton_notice": (
            "_Hinweis: Dieses Skelett wurde vom Katalog-Generator aus `use_when`-Frontmatter-Einträgen "
            "vorbefüllt. Es wird in Folgeläufen NICHT überschrieben — gerne Rubriken ergänzen, "
            "umsortieren oder Einträge mit Disambiguierungs-Notizen versehen._"
        ),
        "by_task_no_use_when": (
            "Noch hat kein Artefakt `use_when`-Einträge deklariert; sobald welche existieren, kann "
            "der Generator hier ein erstes Skelett vorschlagen."
        ),
        "phase_labels": {
            "vision": "1 Vision",
            "plan": "2 Plan",
            "design": "3 Design",
            "build": "4 Build",
            "review": "5 Review",
            "quality": "6 Quality",
            "close-release": "7 Close & Release",
            "cross-cutting": "8 Cross-cutting",
        },
    },
    "en": {
        "skills_title": "Skills",
        "skills_intro": (
            "Auto-generated catalog of every skill discovered across the configured plugin source "
            "roots. Content is taken verbatim from each `SKILL.md` frontmatter and body. "
            "Grouped by delivery-lifecycle phase."
        ),
        "agents_title": "Agents",
        "agents_intro": (
            "Auto-generated catalog of every agent discovered across the configured plugin source "
            "roots. Content is taken verbatim from each agent markdown file. "
            "Grouped by delivery-lifecycle phase."
        ),
        "tags_title": "Tags",
        "tags_intro": (
            "Cross-reference: each tag links to every skill and agent that declares it."
        ),
        "no_tags": "No tags have been declared yet.",
        "source_label": "Source",
        "distribution_label": "Distribution",
        "tags_label": "Tags",
        "plugin_label": "Plugin",
        "phase_label": "Phase",
        "use_when_label": "Use when",
        "dont_use_when_label": "Don't use when",
        "see_also_label": "See also",
        "referenced_by_label": "Referenced by",
        "examples_label": "Examples",
        "example_prompt_label": "Prompt",
        "example_outcome_label": "Outcome",
        "translation_pending_badge": "🚧 Translation pending",
        "by_task_link_label": "Browse by task →",
        "by_task_title": "By task",
        "by_task_intro": (
            "Task-oriented landing page: groups skills and agents by user intent rather than by "
            "phase. Hand-curated; grow as new use-case patterns emerge."
        ),
        "by_task_skeleton_notice": (
            "_Note: This skeleton was pre-populated by the catalog generator from `use_when` "
            "frontmatter entries. It is NOT regenerated on subsequent runs — please add rubrics, "
            "reorganise, or annotate entries with disambiguation hints as needed._"
        ),
        "by_task_no_use_when": (
            "No artifact has declared `use_when` entries yet; once any do, the generator can "
            "propose a first skeleton here."
        ),
        "phase_labels": {
            "vision": "1 Vision",
            "plan": "2 Plan",
            "design": "3 Design",
            "build": "4 Build",
            "review": "5 Review",
            "quality": "6 Quality",
            "close-release": "7 Close & Release",
            "cross-cutting": "8 Cross-cutting",
        },
    },
}


class CatalogError(RuntimeError):
    """Raised when an artefact is malformed; fails the build."""


@dataclass(frozen=True)
class SourceRoot:
    name: str
    local: Path
    skills_path: str
    agents_path: str
    repo_url: str
    branch: str


@dataclass
class Artifact:
    kind: str  # "skill" or "agent"
    plugin: str
    name: str
    description: str
    distribution: str | None
    phase: str
    tags: list[str]
    body: str
    source_relpath: str
    repo_url: str
    branch: str
    # Optional fields per spec §Per-language short summary and §Use-case metadata.
    summary: str | None = None
    summaries: dict[str, str] | None = None  # lang → translated short summary
    use_when: list[str] | None = None
    dont_use_when: list[dict[str, str]] | None = None  # {situation, alternative}
    see_also: list[str] | None = None
    examples: list[dict[str, str]] | None = None  # {prompt, outcome}

    @property
    def source_url(self) -> str:
        return f"{self.repo_url}/blob/{self.branch}/{self.source_relpath}"


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)
FRONTMATTER_LINE_RE = re.compile(r"\A([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)\Z")
TAG_RE = re.compile(r"\A[a-z0-9]+(?:-[a-z0-9]+)*\Z")

# Per spec/project/mkdocs-structure/ §Per-page structure plus
# spec/project/docs-audience-tracks/ §Per-page contract: every page under
# docs/<lang>/ MUST declare these five keys. Catalog pages are generator-fixed
# to track=developer-docs (per skill-agent-catalog Open Question on track
# defaulting) and use last_updated=generated.
CATALOG_TRACK = "developer-docs"
CATALOG_AUDIENCE = "maintainer"


def _render_frontmatter(*, title: str, content_mode: str) -> str:
    """Emit the per-page MUST frontmatter block for a generated catalog page."""

    lines = [
        "---",
        f"title: {title}",
        f"audience: [{CATALOG_AUDIENCE}]",
        f"content_mode: {content_mode}",
        f"track: {CATALOG_TRACK}",
        "last_updated: generated",
        "---",
        "",
    ]
    return "\n".join(lines)


def parse_frontmatter(text: str, file_label: str) -> tuple[dict, str]:
    """Parse the YAML-ish frontmatter block leniently.

    Skill and agent frontmatter is mostly flat (no nested mappings on the legacy
    fields) but ``description`` routinely contains colons followed by spaces —
    for example ``status: planned`` — which PyYAML rejects as ambiguous plain
    scalars. We treat each top-level line as ``key: value`` with the value taken
    verbatim, handling YAML block scalars (``>``, ``>-``, ``|``, ``|-``) via
    continuation collection. Bracketed list values like ``tags: [a, b]`` are
    delegated to PyYAML, and YAML block-style sequences/mappings (introduced by
    a key with no inline value followed by indented lines) are delegated to
    PyYAML as well — this is how ``dont_use_when``/``examples`` (lists of
    mappings) and the wider use-case metadata land.
    """

    match = FRONTMATTER_RE.match(text)
    if not match:
        raise CatalogError(f"{file_label}: missing YAML frontmatter block")
    raw, body = match.group(1), match.group(2)
    lines = raw.split("\n")
    meta: dict[str, object] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = FRONTMATTER_LINE_RE.match(line)
        if not m:
            raise CatalogError(
                f"{file_label}: cannot parse frontmatter line: {line!r}"
            )
        key, raw_value = m.group(1), m.group(2).strip()
        i += 1
        if raw_value in (">", ">-", "|", "|-"):
            block_lines: list[str] = []
            while i < len(lines):
                cont = lines[i]
                if cont and not cont[0].isspace():
                    break
                block_lines.append(cont.strip())
                i += 1
            if raw_value.startswith(">"):
                meta[key] = " ".join(filter(None, block_lines))
            else:
                meta[key] = "\n".join(block_lines).rstrip()
        elif raw_value.startswith("[") and raw_value.endswith("]"):
            try:
                meta[key] = yaml.safe_load(raw_value)
            except yaml.YAMLError as exc:
                raise CatalogError(
                    f"{file_label}: invalid list value for {key!r}: {exc}"
                ) from exc
        elif raw_value == "" and i < len(lines) and lines[i] and lines[i][0].isspace():
            # YAML block-style value follows (sequence of mappings, mapping of
            # mappings, …). Collect all indented continuation lines and hand
            # the whole block to PyYAML; this is what use_when / dont_use_when /
            # see_also / examples ride on per spec §Use-case metadata.
            block_lines = []
            while i < len(lines):
                cont = lines[i]
                if cont and not cont[0].isspace():
                    break
                block_lines.append(cont)
                i += 1
            block_text = "\n".join(block_lines)
            try:
                meta[key] = yaml.safe_load(block_text)
            except yaml.YAMLError as exc:
                raise CatalogError(
                    f"{file_label}: invalid YAML block for {key!r}: {exc}"
                ) from exc
        elif (
            len(raw_value) >= 2
            and raw_value[0] == raw_value[-1]
            and raw_value[0] in ("'", '"')
        ):
            meta[key] = raw_value[1:-1]
        else:
            meta[key] = raw_value
    return meta, body.lstrip("\n")


def load_sources() -> list[SourceRoot]:
    with SOURCES_FILE.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    sources_raw = data.get("sources") or []
    if not sources_raw:
        raise CatalogError(f"{SOURCES_FILE}: no sources configured")
    result: list[SourceRoot] = []
    for idx, entry in enumerate(sources_raw):
        if not isinstance(entry, dict):
            raise CatalogError(f"{SOURCES_FILE}: source #{idx} is not a mapping")
        try:
            local_value = entry["local"]
            name = entry["name"]
            repo_url = entry["repo_url"]
        except KeyError as exc:
            raise CatalogError(f"{SOURCES_FILE}: source #{idx} missing field {exc}") from exc
        local_path = (REPO_ROOT / local_value).resolve()
        result.append(
            SourceRoot(
                name=name,
                local=local_path,
                skills_path=entry.get("skills_path", "skills"),
                agents_path=entry.get("agents_path", "agents"),
                repo_url=repo_url.rstrip("/"),
                branch=entry.get("branch", "main"),
            )
        )
    return result


def load_languages() -> list[str]:
    with MKDOCS_FILE.open("r", encoding="utf-8") as fh:
        raw = fh.read()
    locales = re.findall(r"^\s*-\s*locale:\s*([a-zA-Z][\w-]*)", raw, re.MULTILINE)
    if not locales:
        raise CatalogError(
            f"{MKDOCS_FILE}: no i18n locales found; mkdocs-static-i18n configuration required"
        )
    return locales


def _validate_phase(raw, label: str) -> str:
    if raw is None or raw == "":
        raise CatalogError(
            f"{label}: frontmatter 'phase' is required; "
            f"expected one of {sorted(PHASE_VOCABULARY)}"
        )
    if not isinstance(raw, str):
        raise CatalogError(f"{label}: frontmatter 'phase' must be a string, not a list")
    if raw not in PHASE_VOCABULARY:
        raise CatalogError(
            f"{label}: frontmatter 'phase' value {raw!r} is not in the closed "
            f"vocabulary {sorted(PHASE_VOCABULARY)}"
        )
    return raw


def _normalize_tags(raw, label: str) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise CatalogError(f"{label}: frontmatter 'tags' must be a list")
    if len(raw) > 5:
        raise CatalogError(f"{label}: frontmatter 'tags' must have at most 5 entries")
    tags: list[str] = []
    for tag in raw:
        if not isinstance(tag, str):
            raise CatalogError(f"{label}: tag entries must be strings")
        if tag.startswith("_"):
            raise CatalogError(
                f"{label}: tag '{tag}' begins with '_' which is reserved for "
                f"generator-emitted auto-tags (e.g. '{AUTO_TAG_TRANSLATION_PENDING}'). "
                f"Source frontmatter MUST NOT declare an underscore-prefixed tag."
            )
        if len(tag) > 30 or not TAG_RE.match(tag):
            raise CatalogError(
                f"{label}: tag '{tag}' must be lowercase ASCII kebab-case, ≤30 chars"
            )
        tags.append(tag)
    return tags


def _validate_summary(raw, label: str, field_name: str) -> str | None:
    """Per spec §Per-language short summary.

    Returns the validated summary string, or ``None`` if the field wasn't
    declared. Raises CatalogError for any shape violation (wrong type, empty
    after whitespace stripping, > SUMMARY_MAX_LEN chars).
    """

    if raw is None:
        return None
    if not isinstance(raw, str):
        raise CatalogError(
            f"{label}: frontmatter '{field_name}' must be a plain string, got "
            f"{type(raw).__name__}"
        )
    stripped = raw.strip()
    if not stripped:
        raise CatalogError(
            f"{label}: frontmatter '{field_name}' must be non-empty after "
            f"whitespace stripping"
        )
    if len(stripped) > SUMMARY_MAX_LEN:
        raise CatalogError(
            f"{label}: frontmatter '{field_name}' is {len(stripped)} characters; "
            f"the limit is {SUMMARY_MAX_LEN}"
        )
    return stripped


def _collect_summaries(meta: dict, label: str, languages: list[str]) -> dict[str, str]:
    """Read every ``summary_<lang>`` field for languages configured in the docs
    build and return a ``{lang: summary}`` mapping. The English-canonical
    ``summary`` is collected separately by the caller via ``_validate_summary``.
    """

    out: dict[str, str] = {}
    for lang in languages:
        if lang == SUMMARY_CANONICAL_LANG:
            continue
        field = f"summary_{lang}"
        if field in meta:
            value = _validate_summary(meta[field], label, field)
            if value is not None:
                out[lang] = value
    return out


def _validate_use_when(raw, label: str) -> list[str] | None:
    """Per spec §Use-case metadata: list of plain strings, ≤6 entries, each ≤120 chars."""

    if raw is None:
        return None
    if not isinstance(raw, list):
        raise CatalogError(f"{label}: frontmatter 'use_when' must be a YAML list")
    if len(raw) > USE_WHEN_MAX_ENTRIES:
        raise CatalogError(
            f"{label}: frontmatter 'use_when' has {len(raw)} entries; "
            f"limit is {USE_WHEN_MAX_ENTRIES}"
        )
    out: list[str] = []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, str):
            raise CatalogError(
                f"{label}: frontmatter 'use_when[{idx}]' must be a plain string, "
                f"got {type(entry).__name__}"
            )
        stripped = entry.strip()
        if not stripped:
            raise CatalogError(
                f"{label}: frontmatter 'use_when[{idx}]' is empty after stripping"
            )
        if len(stripped) > USE_WHEN_MAX_LEN:
            raise CatalogError(
                f"{label}: frontmatter 'use_when[{idx}]' is {len(stripped)} "
                f"characters; limit is {USE_WHEN_MAX_LEN}"
            )
        out.append(stripped)
    return out


def _validate_dont_use_when(raw, label: str) -> list[dict[str, str]] | None:
    """Per spec §Use-case metadata: list of {situation, alternative} mappings.

    Resolvability of ``alternative`` against the discovered catalog happens later
    in :func:`_resolve_use_case_references`, after every source root has been
    walked.
    """

    if raw is None:
        return None
    if not isinstance(raw, list):
        raise CatalogError(f"{label}: frontmatter 'dont_use_when' must be a YAML list")
    if len(raw) > DONT_USE_WHEN_MAX_ENTRIES:
        raise CatalogError(
            f"{label}: frontmatter 'dont_use_when' has {len(raw)} entries; "
            f"limit is {DONT_USE_WHEN_MAX_ENTRIES}"
        )
    out: list[dict[str, str]] = []
    allowed_keys = {"situation", "alternative"}
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise CatalogError(
                f"{label}: frontmatter 'dont_use_when[{idx}]' must be a mapping with "
                f"keys 'situation' and 'alternative', got {type(entry).__name__}"
            )
        keys = set(entry.keys())
        if keys != allowed_keys:
            raise CatalogError(
                f"{label}: frontmatter 'dont_use_when[{idx}]' must have exactly the "
                f"keys 'situation' and 'alternative', got {sorted(keys)}"
            )
        situation = entry["situation"]
        alternative = entry["alternative"]
        if not isinstance(situation, str):
            raise CatalogError(
                f"{label}: frontmatter 'dont_use_when[{idx}].situation' must be a "
                f"plain string, got {type(situation).__name__}"
            )
        situation = situation.strip()
        if not situation:
            raise CatalogError(
                f"{label}: frontmatter 'dont_use_when[{idx}].situation' is empty "
                f"after stripping"
            )
        if len(situation) > DONT_USE_WHEN_SITUATION_MAX_LEN:
            raise CatalogError(
                f"{label}: frontmatter 'dont_use_when[{idx}].situation' is "
                f"{len(situation)} characters; limit is "
                f"{DONT_USE_WHEN_SITUATION_MAX_LEN}"
            )
        if not isinstance(alternative, str) or not alternative.strip():
            raise CatalogError(
                f"{label}: frontmatter 'dont_use_when[{idx}].alternative' must be a "
                f"non-empty plain string naming a skill or agent"
            )
        out.append({"situation": situation, "alternative": alternative.strip()})
    return out


def _validate_see_also(raw, label: str) -> list[str] | None:
    """Per spec §Use-case metadata: list of skill/agent names, ≤8 entries.

    Resolvability happens later in :func:`_resolve_use_case_references`.
    """

    if raw is None:
        return None
    if not isinstance(raw, list):
        raise CatalogError(f"{label}: frontmatter 'see_also' must be a YAML list")
    if len(raw) > SEE_ALSO_MAX_ENTRIES:
        raise CatalogError(
            f"{label}: frontmatter 'see_also' has {len(raw)} entries; "
            f"limit is {SEE_ALSO_MAX_ENTRIES}"
        )
    out: list[str] = []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, str) or not entry.strip():
            raise CatalogError(
                f"{label}: frontmatter 'see_also[{idx}]' must be a non-empty plain "
                f"string naming a skill or agent"
            )
        out.append(entry.strip())
    return out


def _validate_examples(raw, label: str) -> list[dict[str, str]] | None:
    """Per spec §Use-case metadata: list of {prompt, outcome} mappings, ≤4 entries."""

    if raw is None:
        return None
    if not isinstance(raw, list):
        raise CatalogError(f"{label}: frontmatter 'examples' must be a YAML list")
    if len(raw) > EXAMPLES_MAX_ENTRIES:
        raise CatalogError(
            f"{label}: frontmatter 'examples' has {len(raw)} entries; "
            f"limit is {EXAMPLES_MAX_ENTRIES}"
        )
    out: list[dict[str, str]] = []
    allowed_keys = {"prompt", "outcome"}
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise CatalogError(
                f"{label}: frontmatter 'examples[{idx}]' must be a mapping with keys "
                f"'prompt' and 'outcome', got {type(entry).__name__}"
            )
        keys = set(entry.keys())
        if keys != allowed_keys:
            raise CatalogError(
                f"{label}: frontmatter 'examples[{idx}]' must have exactly the keys "
                f"'prompt' and 'outcome', got {sorted(keys)}"
            )
        rec: dict[str, str] = {}
        for sub in ("prompt", "outcome"):
            value = entry[sub]
            if not isinstance(value, str):
                raise CatalogError(
                    f"{label}: frontmatter 'examples[{idx}].{sub}' must be a plain "
                    f"string, got {type(value).__name__}"
                )
            value = value.strip()
            if not value:
                raise CatalogError(
                    f"{label}: frontmatter 'examples[{idx}].{sub}' is empty after "
                    f"stripping"
                )
            if len(value) > EXAMPLES_FIELD_MAX_LEN:
                raise CatalogError(
                    f"{label}: frontmatter 'examples[{idx}].{sub}' is {len(value)} "
                    f"characters; limit is {EXAMPLES_FIELD_MAX_LEN}"
                )
            rec[sub] = value
        out.append(rec)
    return out


def discover_skills(source: SourceRoot, languages: list[str]) -> list[Artifact]:
    skills_dir = source.local / source.skills_path
    if not skills_dir.is_dir():
        return []
    artefacts: list[Artifact] = []
    for entry in sorted(skills_dir.iterdir()):
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            continue
        label = f"{source.name}:{source.skills_path}/{entry.name}/SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text, label)
        name = meta.get("name")
        if not name:
            raise CatalogError(f"{label}: frontmatter missing 'name'")
        if name != entry.name:
            raise CatalogError(
                f"{label}: frontmatter name '{name}' must match folder name '{entry.name}'"
            )
        description = meta.get("description")
        if not description:
            raise CatalogError(f"{label}: frontmatter missing 'description'")
        artefacts.append(
            Artifact(
                kind="skill",
                plugin=source.name,
                name=str(name),
                description=str(description),
                distribution=None,
                phase=_validate_phase(meta.get("phase"), label),
                tags=_normalize_tags(meta.get("tags"), label),
                body=body,
                source_relpath=f"{source.skills_path}/{entry.name}/SKILL.md",
                repo_url=source.repo_url,
                branch=source.branch,
                summary=_validate_summary(meta.get("summary"), label, "summary"),
                summaries=_collect_summaries(meta, label, languages),
                use_when=_validate_use_when(meta.get("use_when"), label),
                dont_use_when=_validate_dont_use_when(meta.get("dont_use_when"), label),
                see_also=_validate_see_also(meta.get("see_also"), label),
                examples=_validate_examples(meta.get("examples"), label),
            )
        )
    return artefacts


def discover_agents(source: SourceRoot, languages: list[str]) -> list[Artifact]:
    agents_dir = source.local / source.agents_path
    if not agents_dir.is_dir():
        return []
    artefacts: list[Artifact] = []
    for entry in sorted(agents_dir.iterdir()):
        if entry.suffix != ".md" or not entry.is_file():
            continue
        label = f"{source.name}:{source.agents_path}/{entry.name}"
        text = entry.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text, label)
        name = meta.get("name")
        if not name:
            raise CatalogError(f"{label}: frontmatter missing 'name'")
        if name != entry.stem:
            raise CatalogError(
                f"{label}: frontmatter name '{name}' must match file stem '{entry.stem}'"
            )
        description = meta.get("description")
        if not description:
            raise CatalogError(f"{label}: frontmatter missing 'description'")
        distribution = meta.get("distribution")
        if distribution not in ("plugin", "project"):
            raise CatalogError(
                f"{label}: frontmatter 'distribution' must be 'plugin' or 'project'"
            )
        artefacts.append(
            Artifact(
                kind="agent",
                plugin=source.name,
                name=str(name),
                description=str(description),
                distribution=str(distribution),
                phase=_validate_phase(meta.get("phase"), label),
                tags=_normalize_tags(meta.get("tags"), label),
                body=body,
                source_relpath=f"{source.agents_path}/{entry.name}",
                repo_url=source.repo_url,
                branch=source.branch,
                summary=_validate_summary(meta.get("summary"), label, "summary"),
                summaries=_collect_summaries(meta, label, languages),
                use_when=_validate_use_when(meta.get("use_when"), label),
                dont_use_when=_validate_dont_use_when(meta.get("dont_use_when"), label),
                see_also=_validate_see_also(meta.get("see_also"), label),
                examples=_validate_examples(meta.get("examples"), label),
            )
        )
    return artefacts


_HEADING_RE = re.compile(r"^(#{1,5})(\s)", re.MULTILINE)

# Inline-code span matching the shape of a valid skill or agent name
# (lowercase ASCII kebab-case). The wider RFC-1738-style backtick-rules of
# Markdown allow more, but artifact names are always this shape so this is
# both sufficient and false-positive-safe for the cross-linking pass below.
INLINE_CODE_NAME_RE = re.compile(r"`([a-z][a-z0-9-]*)`")

# Sentence boundary used by _truncate_description as a fallback summary source.
_SENTENCE_END_RE = re.compile(r"(?<=[\.!?])\s+")


def _demote_headings(body: str) -> str:
    """Demote every ATX heading in `body` by one level (H1→H2, H2→H3, …).

    Keeps the catalog page itself owning the single H1 (`# <artifact.name>`),
    so the rendered page has exactly one H1 — required by markdownlint's MD025
    and respected by the mkdocs-material page-title heuristic.
    """

    return _HEADING_RE.sub(lambda m: f"#{m.group(1)}{m.group(2)}", body)


# ---------------------------------------------------------------------------
# Cross-linking
# ---------------------------------------------------------------------------


def _build_link_index(skills: list[Artifact], agents: list[Artifact]) -> dict[str, list[Artifact]]:
    """Return ``{name: [Artifact, ...]}`` for every discovered artifact.

    The same name can map to multiple artifacts when (a) a skill and an agent
    share a name or (b) two plugin source roots ship artifacts of the same
    name. Cross-linking treats those as ambiguous.
    """

    index: dict[str, list[Artifact]] = {}
    for art in [*skills, *agents]:
        index.setdefault(art.name, []).append(art)
    return index


def _build_referenced_by_index(
    skills: list[Artifact], agents: list[Artifact]
) -> dict[str, list[Artifact]]:
    """Return ``{name: [Artifact, ...]}`` mapping each artifact name to every
    artifact whose ``see_also`` lists it — the inverse of the forward cross-link
    index, per spec §Cross-linking "Referenced by" SHOULD.

    Built in a single in-memory pass over the already-parsed artifacts; each
    referencing list is sorted (kind, plugin, name) for stable output. This
    surfaces one-directional ``see_also`` asymmetries authors miss.
    """

    referenced_by: dict[str, list[Artifact]] = {}
    for art in [*skills, *agents]:
        if not art.see_also:
            continue
        for target in art.see_also:
            referenced_by.setdefault(target, []).append(art)
    for target in referenced_by:
        referenced_by[target].sort(key=lambda a: (a.kind, a.plugin, a.name))
    return referenced_by


def _resolve_use_case_references(
    skills: list[Artifact], agents: list[Artifact]
) -> None:
    """Validate every ``dont_use_when[].alternative`` and ``see_also[]`` value
    against the discovered catalog, per spec §Use-case metadata. Fails the
    build on unresolved or ambiguous references.
    """

    index = _build_link_index(skills, agents)
    for art in [*skills, *agents]:
        label = f"{art.plugin}:{art.kind}/{art.name}"
        if art.dont_use_when:
            for i, entry in enumerate(art.dont_use_when):
                _check_ref_resolves(
                    index, entry["alternative"], label, f"dont_use_when[{i}].alternative"
                )
        if art.see_also:
            for i, target in enumerate(art.see_also):
                _check_ref_resolves(
                    index, target, label, f"see_also[{i}]"
                )


def _check_ref_resolves(
    index: dict[str, list[Artifact]], target: str, label: str, field_path: str
) -> None:
    if target not in index:
        raise CatalogError(
            f"{label}: '{field_path}' references '{target}' which is not discoverable "
            f"in any configured plugin source root"
        )
    if len(index[target]) > 1:
        collisions = ", ".join(
            f"{a.plugin}:{a.kind}/{a.name}" for a in index[target]
        )
        raise CatalogError(
            f"{label}: '{field_path}' references '{target}' which is ambiguous "
            f"(found in: {collisions}); rename one of the colliding artifacts"
        )


def _relative_link(
    from_art: Artifact, to_art: Artifact
) -> str:
    """Compute the relative MkDocs link from ``from_art``'s catalog page to
    ``to_art``'s catalog page, working purely from logical path segments so the
    result is the same across docs languages.
    """

    from_section = "skills" if from_art.kind == "skill" else "agents"
    to_section = "skills" if to_art.kind == "skill" else "agents"
    from_dir_parts = [from_section, from_art.plugin]
    to_parts = [to_section, to_art.plugin, f"{to_art.name}.md"]
    # Walk up to the closest common ancestor, then descend.
    common = 0
    while (
        common < len(from_dir_parts)
        and common < len(to_parts) - 1
        and from_dir_parts[common] == to_parts[common]
    ):
        common += 1
    ups = ["..".rstrip()] * (len(from_dir_parts) - common)
    downs = to_parts[common:]
    return "/".join([*ups, *downs])


def _apply_inline_cross_linking(
    text: str,
    from_art: Artifact,
    index: dict[str, list[Artifact]],
    warnings: list[tuple[str, str, list[Artifact]]],
) -> str:
    """Rewrite inline-code mentions ``\\`name\\``` in ``text`` into Markdown
    links when ``name`` resolves to exactly one discovered artifact. Ambiguous
    mentions stay unlinked and are appended to ``warnings`` for a build-time
    diagnostic.
    """

    self_label = f"{from_art.plugin}:{from_art.kind}/{from_art.name}"

    def replace(m: re.Match[str]) -> str:
        name = m.group(1)
        targets = index.get(name)
        if not targets:
            return m.group(0)
        if len(targets) > 1:
            warnings.append((self_label, name, list(targets)))
            return m.group(0)
        target = targets[0]
        if target.name == from_art.name and target.kind == from_art.kind:
            # Self-mention: never link the page to itself.
            return m.group(0)
        url = _relative_link(from_art, target)
        return f"[`{name}`]({url})"

    return INLINE_CODE_NAME_RE.sub(replace, text)


# ---------------------------------------------------------------------------
# Summary resolution + auto-tags
# ---------------------------------------------------------------------------


def _truncate_description(description: str) -> str:
    """Fallback summary: first sentence of ``description``, capped at SUMMARY_MAX_LEN."""

    flat = " ".join(description.split())
    # Split at the first sentence boundary; if none found, the whole text is
    # one sentence.
    first = _SENTENCE_END_RE.split(flat, maxsplit=1)[0]
    if len(first) > SUMMARY_MAX_LEN:
        return first[: SUMMARY_MAX_LEN - 1].rstrip() + "…"
    return first


def _resolve_summary_for_lang(art: Artifact, lang: str) -> tuple[str, bool]:
    """Return ``(displayed_summary, is_translation_pending)`` for ``art`` on the
    catalog page of docs language ``lang``, per spec §Per-language short summary.

    The three-step fallback chain is summary_<lang> → summary (English) →
    first sentence of description truncated to SUMMARY_MAX_LEN. The boolean is
    True whenever the page falls back away from a native-language summary on a
    non-English docs language; that boolean drives both the chrome badge and
    the ``_translation-pending`` auto-tag.
    """

    if lang != SUMMARY_CANONICAL_LANG and art.summaries and lang in art.summaries:
        return art.summaries[lang], False
    if art.summary:
        return art.summary, lang != SUMMARY_CANONICAL_LANG
    return _truncate_description(art.description), lang != SUMMARY_CANONICAL_LANG


def _effective_tags(art: Artifact, lang: str) -> list[str]:
    """Return ``art.tags`` plus any generator-emitted auto-tags applicable to
    the rendered page in docs language ``lang``. Currently the only auto-tag is
    ``_translation-pending`` per spec §Per-language short summary.
    """

    base = list(art.tags)
    _, pending = _resolve_summary_for_lang(art, lang)
    if pending:
        base.append(AUTO_TAG_TRANSLATION_PENDING)
    return base


def render_page(
    artifact: Artifact,
    chrome: dict,
    lang: str,
    link_index: dict[str, list[Artifact]],
    referenced_by_index: dict[str, list[Artifact]],
    warnings: list[tuple[str, str, list[Artifact]]],
) -> str:
    phase_label = chrome["phase_labels"][artifact.phase]
    summary_text, translation_pending = _resolve_summary_for_lang(artifact, lang)
    tags_for_page = _effective_tags(artifact, lang)

    lines: list[str] = []
    lines.append(_render_frontmatter(title=artifact.name, content_mode="reference"))
    lines.append(f"# {artifact.name}")
    lines.append("")

    # Per-language short summary as a callout above the routing description.
    # The translation-pending badge sits on its own line so screen readers and
    # markdown viewers both surface it. Cross-link the summary (the rewrite
    # only touches inline-code spans, so the leading/trailing prose stays put).
    summary_rendered = _apply_inline_cross_linking(
        summary_text, artifact, link_index, warnings
    )
    lines.append(f"> {summary_rendered}")
    if translation_pending:
        lines.append(f">")
        lines.append(f"> _{chrome['translation_pending_badge']}_")
    lines.append("")

    # Routing description (the source-of-truth Claude reads).
    description_rendered = _apply_inline_cross_linking(
        artifact.description, artifact, link_index, warnings
    )
    lines.append(f"_{description_rendered}_")
    lines.append("")

    # Metadata bullets.
    lines.append(f"- **{chrome['plugin_label']}:** `{artifact.plugin}`")
    lines.append(f"- **{chrome['phase_label']}:** {phase_label} (`{artifact.phase}`)")
    if artifact.distribution:
        lines.append(f"- **{chrome['distribution_label']}:** `{artifact.distribution}`")
    if tags_for_page:
        tag_list = ", ".join(f"`{t}`" for t in tags_for_page)
        lines.append(f"- **{chrome['tags_label']}:** {tag_list}")
    lines.append(
        f"- **{chrome['source_label']}:** "
        f"[{artifact.source_relpath}]({artifact.source_url})"
    )
    lines.append("")

    # Use-case metadata sections (each rendered only when the field is declared).
    if artifact.use_when:
        lines.append(f"## {chrome['use_when_label']}")
        lines.append("")
        for entry in artifact.use_when:
            lines.append(f"- {entry}")
        lines.append("")
    if artifact.dont_use_when:
        lines.append(f"## {chrome['dont_use_when_label']}")
        lines.append("")
        for entry in artifact.dont_use_when:
            target_link = _resolve_structured_link(
                entry["alternative"], artifact, link_index
            )
            lines.append(f"- **{entry['situation']}** → {target_link}")
        lines.append("")
    if artifact.see_also:
        lines.append(f"## {chrome['see_also_label']}")
        lines.append("")
        for target in artifact.see_also:
            target_link = _resolve_structured_link(target, artifact, link_index)
            lines.append(f"- {target_link}")
        lines.append("")
    # Inverted cross-link pass per spec §Cross-linking "Referenced by" SHOULD:
    # list every artifact whose see_also points at this one.
    referencing = referenced_by_index.get(artifact.name)
    if referencing:
        lines.append(f"## {chrome['referenced_by_label']}")
        lines.append("")
        for ref in referencing:
            url = _relative_link(artifact, ref)
            lines.append(f"- [`{ref.name}`]({url})")
        lines.append("")
    if artifact.examples:
        lines.append(f"## {chrome['examples_label']}")
        lines.append("")
        # Nested bullets keep the prompt/outcome pair grouped without tripping
        # markdownlint's MD028 (no blank lines inside blockquotes).
        for ex in artifact.examples:
            lines.append(f"- **{chrome['example_prompt_label']}:** {ex['prompt']}")
            lines.append(f"  - **{chrome['example_outcome_label']}:** {ex['outcome']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    body_rendered = _apply_inline_cross_linking(
        artifact.body.rstrip(), artifact, link_index, warnings
    )
    lines.append(_demote_headings(body_rendered))
    return "\n".join(lines) + "\n"


def _resolve_structured_link(
    target_name: str,
    from_art: Artifact,
    index: dict[str, list[Artifact]],
) -> str:
    """Resolve a ``dont_use_when[].alternative`` or ``see_also[]`` reference
    into an inline Markdown link. The caller has already verified resolution
    via :func:`_resolve_use_case_references`, so we can assume exactly one
    target exists here.
    """

    targets = index[target_name]
    target = targets[0]
    url = _relative_link(from_art, target)
    return f"[`{target_name}`]({url})"


def group_by_phase_then_plugin(
    artefacts: Iterable[Artifact],
) -> dict[str, dict[str, list[Artifact]]]:
    """Bucket artefacts into ``{phase: {plugin: [Artifact, ...]}}``.

    Outer dict iterates in :data:`PHASE_ORDER`; only phases with at least one
    artefact appear. Inner dict iterates alphabetically by plugin. Each
    artefact list is sorted alphabetically by ``name``.
    """

    by_phase: dict[str, dict[str, list[Artifact]]] = {}
    for art in artefacts:
        by_phase.setdefault(art.phase, {}).setdefault(art.plugin, []).append(art)
    ordered: dict[str, dict[str, list[Artifact]]] = {}
    for phase in PHASE_ORDER:
        if phase not in by_phase:
            continue
        plugins = by_phase[phase]
        ordered[phase] = {
            plugin: sorted(plugins[plugin], key=lambda a: a.name)
            for plugin in sorted(plugins)
        }
    return ordered


def write_page(path: Path, content: str) -> None:
    """Write ``content`` to ``path``, skipping the write when the file already
    holds identical bytes.

    Preserving the mtime of unchanged pages keeps the generator **idempotent**:
    when the ``on_pre_build`` hook regenerates the catalog inside the watched
    ``docs_dir`` on every build, an unchanged run touches no files, so
    ``mkdocs serve``'s livereload doesn't loop (spec §Generation mechanism;
    requirement R8, mirroring the verified claude-home-assistant#6 pattern).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def _prune_stale(root: Path, kept: set[Path]) -> None:
    """Delete every file under ``root`` not in ``kept``, then remove emptied
    directories (deepest first).

    Replaces a blanket ``rmtree`` + rewrite: pages for removed artefacts or
    plugins still disappear on the next build, but unchanged pages keep their
    mtime so the generator stays idempotent (see :func:`write_page`).
    """
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_file() and path not in kept:
            path.unlink()
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def emit_section(
    lang: str,
    section: str,  # "skills" or "agents"
    artefacts: list[Artifact],
    chrome: dict,
    link_index: dict[str, list[Artifact]],
    referenced_by_index: dict[str, list[Artifact]],
    warnings: list[tuple[str, str, list[Artifact]]],
) -> None:
    section_dir = DOCS_DIR / lang / section
    section_dir.mkdir(parents=True, exist_ok=True)
    written: set[Path] = set()

    by_phase = group_by_phase_then_plugin(artefacts)
    distinct_plugins = {art.plugin for art in artefacts}
    show_plugin_subgroup = len(distinct_plugins) > 1

    for art in artefacts:
        page_path = section_dir / art.plugin / f"{art.name}.md"
        write_page(
            page_path,
            render_page(
                art, chrome, lang, link_index, referenced_by_index, warnings
            ),
        )
        written.add(page_path)

    title_key = f"{section}_title"
    intro_key = f"{section}_intro"

    index_lines: list[str] = []
    index_lines.append(_render_frontmatter(title=chrome[title_key], content_mode="meta"))
    index_lines.append(f"# {chrome[title_key]}")
    index_lines.append("")
    # Prominent by-task link near the top of the section index, per
    # spec §Navigation and layout.
    index_lines.append(f"[**{chrome['by_task_link_label']}**](../by-task.md)")
    index_lines.append("")
    index_lines.append(chrome[intro_key])
    index_lines.append("")
    for phase, plugins in by_phase.items():
        index_lines.append(f"## {chrome['phase_labels'][phase]}")
        index_lines.append("")
        for plugin, items in plugins.items():
            if show_plugin_subgroup:
                index_lines.append(f"### {plugin}")
                index_lines.append("")
            for art in items:
                summary_text, _ = _resolve_summary_for_lang(art, lang)
                index_lines.append(
                    f"- [`{art.name}`]({plugin}/{art.name}.md) — {summary_text}"
                )
            index_lines.append("")
    index_path = section_dir / "index.md"
    write_page(index_path, "\n".join(index_lines).rstrip() + "\n")
    written.add(index_path)

    # mkdocs-literate-nav reads SUMMARY.md as a nav source, but the page is
    # still a file under docs/<lang>/, so the per-page frontmatter contract
    # from spec/project/mkdocs-structure/ §Per-page structure and
    # spec/project/docs-audience-tracks/ §Per-page contract applies. literate-nav
    # parses the bullet list and leaves the YAML frontmatter alone.
    summary_parts: list[str] = [
        _render_frontmatter(title=chrome[title_key], content_mode="meta")
    ]
    summary_parts.append(f"* [{chrome[title_key]}](index.md)")
    for phase, plugins in by_phase.items():
        summary_parts.append(f"* {chrome['phase_labels'][phase]}")
        for plugin, items in plugins.items():
            # mkdocs-literate-nav requires 4-space indent per nesting level;
            # SUMMARY.md is therefore excluded from markdownlint via
            # `.markdownlintignore` (the repo-wide MD007 default stays at 2).
            if show_plugin_subgroup:
                summary_parts.append(f"    * {plugin}")
                for art in items:
                    summary_parts.append(
                        f"        * [{art.name}]({plugin}/{art.name}.md)"
                    )
            else:
                for art in items:
                    summary_parts.append(
                        f"    * [{art.name}]({plugin}/{art.name}.md)"
                    )
    summary_path = section_dir / "SUMMARY.md"
    write_page(summary_path, "\n".join(summary_parts) + "\n")
    written.add(summary_path)

    # Replaces the old blanket rmtree: drop pages for artefacts/plugins that no
    # longer exist without rewriting unchanged pages (keeps regeneration
    # idempotent so `mkdocs serve` doesn't livereload-loop).
    _prune_stale(section_dir, written)


def emit_tag_index(lang: str, all_artefacts: list[Artifact], chrome: dict) -> None:
    """Emit ``docs/<lang>/references/tags.md`` listing every author-declared tag
    and every generator-emitted auto-tag (currently ``_translation-pending``)
    for the docs language ``lang``. Per spec §Navigation and layout the auto-tag
    appears only when at least one artifact carries it.

    The tag index lives under the ``references/`` section (per
    spec/project/mkdocs-structure/ §Top-level navigation; the catalog's tag
    index is reference content), so every href walks up one level
    (``../skills/…``, ``../agents/…``) to reach the catalog trees that sit at
    ``docs/<lang>/{skills,agents}/``.
    """

    by_tag: dict[str, list[Artifact]] = {}
    for art in all_artefacts:
        for tag in _effective_tags(art, lang):
            by_tag.setdefault(tag, []).append(art)
    for tag in by_tag:
        by_tag[tag].sort(key=lambda a: (a.kind, a.plugin, a.name))

    path = DOCS_DIR / lang / "references" / "tags.md"
    lines: list[str] = []
    lines.append(_render_frontmatter(title=chrome["tags_title"], content_mode="meta"))
    lines.append(f"# {chrome['tags_title']}")
    lines.append("")
    lines.append(chrome['tags_intro'])
    lines.append("")
    if not by_tag:
        lines.append(chrome['no_tags'])
    else:
        # Sort: author tags first (alphabetical), auto-tags (underscore-prefixed) last.
        ordered_tags = sorted(by_tag, key=lambda t: (t.startswith("_"), t))
        for tag in ordered_tags:
            lines.append(f"## `{tag}`")
            lines.append("")
            for art in by_tag[tag]:
                section = "skills" if art.kind == "skill" else "agents"
                # tags.md sits under references/, so step up one level to the
                # catalog trees at docs/<lang>/{skills,agents}/.
                href = f"../{section}/{art.plugin}/{art.name}.md"
                lines.append(f"- [{art.name}]({href}) — {art.plugin}")
            lines.append("")
    write_page(path, "\n".join(lines).rstrip() + "\n")


def emit_landing_skeleton(
    lang: str,
    skills: list[Artifact],
    agents: list[Artifact],
    chrome: dict,
) -> None:
    """Per spec §Task-oriented landing pages: emit ``docs/<lang>/by-task.md``
    as a one-shot skeleton populated from artifacts' ``use_when`` entries.
    Does **NOT** overwrite an existing file — the landing page transitions
    from generator-emitted skeleton to hand-curated artifact as soon as a
    human starts editing it.
    """

    path = DOCS_DIR / lang / "by-task.md"
    if path.exists():
        return

    artefacts_with_use_when = [a for a in [*skills, *agents] if a.use_when]

    lines: list[str] = []
    lines.append(_render_frontmatter(title=chrome["by_task_title"], content_mode="meta"))
    lines.append(f"# {chrome['by_task_title']}")
    lines.append("")
    lines.append(chrome["by_task_intro"])
    lines.append("")
    lines.append(chrome["by_task_skeleton_notice"])
    lines.append("")
    if not artefacts_with_use_when:
        lines.append(chrome["by_task_no_use_when"])
    else:
        # Flat list of every `use_when` entry across the catalog, sorted by
        # artifact name. The human author groups them into rubrics on the
        # first hand-edit.
        for art in sorted(artefacts_with_use_when, key=lambda a: a.name):
            section = "skills" if art.kind == "skill" else "agents"
            href = f"{section}/{art.plugin}/{art.name}.md"
            for entry in art.use_when:
                lines.append(f"- [`{art.name}`]({href}) — _{entry}_")
    write_page(path, "\n".join(lines).rstrip() + "\n")


def _generate() -> tuple[list[Artifact], list[Artifact]]:
    """Render the entire catalog to physical files under ``docs/<lang>/``.

    The single rendering core shared by both invocation surfaces — the CLI
    ``main()`` / ``__main__`` entry point and the MkDocs ``on_pre_build`` hook
    (see :func:`on_pre_build`). The form choice concerns the invocation surface
    only; the generator never forks (spec §Generation mechanism — the DRY
    single-generator / multi-surface contract). Raises :class:`CatalogError` on
    any malformed source so the docs build fails loudly rather than publishing a
    partial catalog.
    """
    sources = load_sources()
    languages = load_languages()

    skills: list[Artifact] = []
    agents: list[Artifact] = []
    for source in sources:
        skills.extend(discover_skills(source, languages))
        agents.extend(discover_agents(source, languages))

    # Structured peer references (dont_use_when[].alternative, see_also[])
    # MUST resolve against the discovered catalog; unresolved or ambiguous
    # ones fail the docs build per spec §Use-case metadata.
    _resolve_use_case_references(skills, agents)

    # One cross-link index drives the inline-code rewrite on every rendered
    # page; warnings collected here are flushed to stderr after the run.
    link_index = _build_link_index(skills, agents)
    # Inverted index for the "Referenced by" pass per spec §Cross-linking.
    referenced_by_index = _build_referenced_by_index(skills, agents)
    warnings: list[tuple[str, str, list[Artifact]]] = []

    for lang in languages:
        chrome = CHROME.get(lang, CHROME["en"])
        emit_section(
            lang, "skills", skills, chrome, link_index, referenced_by_index, warnings
        )
        emit_section(
            lang, "agents", agents, chrome, link_index, referenced_by_index, warnings
        )
        emit_tag_index(lang, skills + agents, chrome)
        emit_landing_skeleton(lang, skills, agents, chrome)

    _flush_link_warnings(warnings)
    print(
        f"gen_catalog: wrote {len(skills)} skill(s) and {len(agents)} agent(s) "
        f"for languages {languages}",
        file=sys.stderr,
    )
    return skills, agents


def _flush_link_warnings(
    warnings: list[tuple[str, str, list[Artifact]]],
) -> None:
    """Surface ambiguous inline-code mentions as non-fatal build warnings per
    spec §Cross-linking. De-duplicate so the same collision reported on every
    language doesn't drown the log."""
    seen: set[tuple[str, str]] = set()
    for self_label, mention, collisions in warnings:
        key = (self_label, mention)
        if key in seen:
            continue
        seen.add(key)
        collision_str = ", ".join(
            f"{a.plugin}:{a.kind}/{a.name}" for a in collisions
        )
        print(
            f"gen_catalog: warning: {self_label}: inline-code mention "
            f"`{mention}` is ambiguous (matches: {collision_str}) — left unlinked",
            file=sys.stderr,
        )


def on_pre_build(config, **kwargs):  # noqa: ANN001, ANN003, ARG001 — MkDocs hook signature
    """MkDocs ``on_pre_build`` hook: regenerate the catalog from inside
    ``mkdocs build`` itself.

    Because MkDocs runs file collection *after* ``on_pre_build``, the physical
    pages this writes under ``docs/<lang>/`` are collected and localized by
    ``mkdocs-static-i18n`` exactly like hand-authored pages. The hook fires on
    every build surface — ``mkdocs build``, ``mkdocs serve``, and the
    ``mkdocs gh-deploy`` run by the docs-deploy pipeline — so the catalog stays
    current with no Taskfile or CI wiring. This is the spec's recommended
    pre-build surface for repositories on ``mkdocs-static-i18n`` folder mode.

    Shares the one render core (:func:`_generate`) with the CLI entry point. A
    malformed source aborts the build loudly via ``PluginError``. Registered
    through the ``hooks:`` key in ``mkdocs.yml``.
    """
    try:
        _generate()
    except CatalogError as exc:
        # Imported lazily so the CLI / __main__ surface stays importable
        # without MkDocs installed; on the hook path MkDocs is always present.
        from mkdocs.exceptions import PluginError

        raise PluginError(f"gen_catalog: {exc}") from exc


def main() -> int:
    try:
        _generate()
    except CatalogError as exc:
        print(f"gen_catalog: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
