"""Generate the skill and agent catalog pages at MkDocs build time.

Implements spec/claude/skill-agent-catalog/<lang>.md (shipped by the
nolte-shared plugin). Reads `docs/catalog-sources.yml` to discover plugin
source roots, walks each one for `skills/<name>/SKILL.md` and
`agents/<name>.md`, and emits per-artifact pages, group SUMMARY.md files for
mkdocs-literate-nav, and a tag index.

The build fails loudly if an artifact has invalid frontmatter — never silently
skip, since a hidden gap defeats the catalog's whole purpose.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import shutil

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCES_FILE = REPO_ROOT / "docs" / "catalog-sources.yml"

# The catalog is written as real files into the canonical-language docs tree
# (docs/en/) rather than as mkdocs-gen-files virtual files. mkdocs-static-i18n
# only localizes files that physically live under docs_dir; virtual gen-files
# pages hit its "Unhandled file case" branch and are dropped from every language
# tree (ultrabug/mkdocs-static-i18n#263). Writing real files lets i18n build the
# catalog into the default language and fall other languages back onto it. A
# `hooks:` entry runs main() in on_pre_build, before MkDocs collects the files.
DOCS_LANG = REPO_ROOT / "docs" / "en"

# Generated subtrees, wiped before each run so deleted artifacts don't linger as
# orphan pages. Hand-written prose (docs/en/index.md) is never touched.
_GENERATED = ("skills", "agents", "tags.md")


def _doc_path(*parts: str) -> Path:
    return DOCS_LANG.joinpath(*parts)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


class CatalogError(RuntimeError):
    pass


def _parse_frontmatter(text: str, source: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise CatalogError(f"{source}: missing YAML frontmatter")
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise CatalogError(f"{source}: invalid YAML frontmatter — {exc}") from exc
    if not isinstance(meta, dict):
        raise CatalogError(f"{source}: frontmatter is not a mapping")
    return meta, match.group(2)


def _require(meta: dict, key: str, source: str) -> str:
    value = meta.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{source}: frontmatter is missing required '{key}'")
    return value.strip()


def _load_sources() -> list[dict]:
    if not SOURCES_FILE.exists():
        raise CatalogError(f"{SOURCES_FILE}: catalog sources file not found")
    data = yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8")) or {}
    sources = data.get("sources") or []
    if not isinstance(sources, list) or not sources:
        raise CatalogError(f"{SOURCES_FILE}: 'sources' must be a non-empty list")
    return sources


def _collect_skills(source: dict) -> list[dict]:
    base = (REPO_ROOT / source["local"]).resolve()
    skills_dir = base / source.get("skills_path", "skills")
    if not skills_dir.is_dir():
        return []
    out: list[dict] = []
    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        loc = f"{source['name']}:skills/{skill_dir.name}/SKILL.md"
        meta, body = _parse_frontmatter(skill_md.read_text(encoding="utf-8"), loc)
        name = _require(meta, "name", loc)
        if name != skill_dir.name:
            raise CatalogError(
                f"{loc}: frontmatter 'name' ({name!r}) does not match folder ({skill_dir.name!r})"
            )
        out.append(
            {
                "kind": "skill",
                "name": name,
                "description": _require(meta, "description", loc),
                "tags": meta.get("tags") or [],
                "body": body,
                "source": source,
                "rel_source": f"{source.get('skills_path', 'skills')}/{skill_dir.name}/SKILL.md",
            }
        )
    return out


def _collect_agents(source: dict) -> list[dict]:
    base = (REPO_ROOT / source["local"]).resolve()
    agents_dir = base / source.get("agents_path", "agents")
    if not agents_dir.is_dir():
        return []
    out: list[dict] = []
    for agent_md in sorted(p for p in agents_dir.iterdir() if p.is_file() and p.suffix == ".md"):
        if agent_md.name == "SUMMARY.md":
            continue
        loc = f"{source['name']}:agents/{agent_md.name}"
        meta, body = _parse_frontmatter(agent_md.read_text(encoding="utf-8"), loc)
        name = _require(meta, "name", loc)
        if name != agent_md.stem:
            raise CatalogError(
                f"{loc}: frontmatter 'name' ({name!r}) does not match filename ({agent_md.stem!r})"
            )
        distribution = _require(meta, "distribution", loc)
        if distribution not in {"plugin", "project"}:
            raise CatalogError(
                f"{loc}: 'distribution' must be 'plugin' or 'project', got {distribution!r}"
            )
        out.append(
            {
                "kind": "agent",
                "name": name,
                "description": _require(meta, "description", loc),
                "distribution": distribution,
                "tags": meta.get("tags") or [],
                "body": body,
                "source": source,
                "rel_source": f"{source.get('agents_path', 'agents')}/{agent_md.name}",
            }
        )
    return out


def _source_link(source: dict, rel_source: str) -> str:
    base = source["repo_url"].rstrip("/")
    branch = source.get("branch", "main")
    return f"{base}/blob/{branch}/{rel_source}"


def _render_tags(tags: list[str]) -> str:
    if not tags:
        return ""
    chips = " ".join(f"`#{t}`" for t in tags)
    return f"\n**Tags:** {chips}\n"


def _render_skill_page(entry: dict) -> str:
    src_link = _source_link(entry["source"], entry["rel_source"])
    return (
        f"# {entry['name']}\n\n"
        f"_Plugin: **{entry['source']['name']}**_\n\n"
        f"> {entry['description']}\n"
        f"{_render_tags(entry['tags'])}\n"
        f"[View source]({src_link})\n\n"
        f"---\n\n"
        f"{entry['body'].strip()}\n"
    )


def _render_agent_page(entry: dict) -> str:
    src_link = _source_link(entry["source"], entry["rel_source"])
    return (
        f"# {entry['name']}\n\n"
        f"_Plugin: **{entry['source']['name']}** · Distribution: `{entry['distribution']}`_\n\n"
        f"> {entry['description']}\n"
        f"{_render_tags(entry['tags'])}\n"
        f"[View source]({src_link})\n\n"
        f"---\n\n"
        f"{entry['body'].strip()}\n"
    )


def _render_index(kind: str, entries: list[dict]) -> str:
    title = "Skills" if kind == "skill" else "Agents"
    if not entries:
        return (
            f"# {title}\n\n"
            f"_No {title} in the configured plugin sources yet._\n"
        )
    lines = [f"# {title}\n"]
    by_plugin: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_plugin[e["source"]["name"]].append(e)
    for plugin in sorted(by_plugin):
        lines.append(f"\n## {plugin}\n")
        for e in sorted(by_plugin[plugin], key=lambda x: x["name"]):
            tag_chips = " ".join(f"`#{t}`" for t in e["tags"]) if e["tags"] else ""
            lines.append(
                f"- [{e['name']}]({plugin}/{e['name']}.md) — {e['description']} {tag_chips}".rstrip()
            )
    return "\n".join(lines) + "\n"


def _render_summary(kind: str, entries: list[dict]) -> str:
    out = [f"- [Overview](index.md)"]
    by_plugin: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_plugin[e["source"]["name"]].append(e)
    for plugin in sorted(by_plugin):
        out.append(f"- {plugin}:")
        for e in sorted(by_plugin[plugin], key=lambda x: x["name"]):
            out.append(f"    - [{e['name']}]({plugin}/{e['name']}.md)")
    return "\n".join(out) + "\n"


def _render_tag_index(all_entries: list[dict]) -> str:
    by_tag: dict[str, list[dict]] = defaultdict(list)
    for e in all_entries:
        for t in e["tags"]:
            by_tag[t].append(e)
    if not by_tag:
        return "# Tags\n\n_No tags in the configured plugin sources yet._\n"
    lines = ["# Tags\n"]
    for tag in sorted(by_tag):
        lines.append(f"\n## #{tag}\n")
        for e in sorted(by_tag[tag], key=lambda x: (x["kind"], x["name"])):
            section = "skills" if e["kind"] == "skill" else "agents"
            plugin = e["source"]["name"]
            lines.append(f"- [{e['name']}]({section}/{plugin}/{e['name']}.md) ({e['kind']})")
    return "\n".join(lines) + "\n"


def _clean_generated() -> None:
    for name in _GENERATED:
        target = DOCS_LANG / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def main() -> None:
    sources = _load_sources()
    skills: list[dict] = []
    agents: list[dict] = []
    for source in sources:
        skills.extend(_collect_skills(source))
        agents.extend(_collect_agents(source))

    _clean_generated()

    for entry in skills:
        _write(
            _doc_path("skills", entry["source"]["name"], f"{entry['name']}.md"),
            _render_skill_page(entry),
        )

    for entry in agents:
        _write(
            _doc_path("agents", entry["source"]["name"], f"{entry['name']}.md"),
            _render_agent_page(entry),
        )

    _write(_doc_path("skills", "index.md"), _render_index("skill", skills))
    _write(_doc_path("agents", "index.md"), _render_index("agent", agents))
    _write(_doc_path("skills", "SUMMARY.md"), _render_summary("skill", skills))
    _write(_doc_path("agents", "SUMMARY.md"), _render_summary("agent", agents))
    _write(_doc_path("tags.md"), _render_tag_index(skills + agents))


def on_pre_build(config, **kwargs) -> None:
    """MkDocs hook entry point: regenerate the catalog into docs/de/ before
    MkDocs collects the files, so mkdocs-static-i18n sees real docs_dir files."""
    main()


if __name__ == "__main__":
    main()
