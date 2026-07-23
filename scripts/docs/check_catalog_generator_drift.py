#!/usr/bin/env python3
"""Catalog-generator drift check.

The skill/agent catalog generator (`scripts/docs/gen_catalog.py`) is *vendored*
into this repository: it is a byte-for-byte copy of the canonical generator
shipped by the `nolte-shared` hub (`nolte/claude-shared`). The hub owns the
implementation per `spec/claude/skill-agent-catalog/<lang>.md`; this repo only
carries a pinned copy plus the per-repo *data* file `docs/catalog-sources.yml`.

Vendored copies drift. This gate makes divergence a build error: it fetches the
canonical generator at the pinned hub ref and byte-compares it against the local
copy. When they differ, the fix is never to hand-edit the local copy — it is to
re-sync from the hub (re-run `nolte-shared:skill-agent-catalog-apply`, or copy
the pinned canonical file) and bump `CANONICAL_REF` in lockstep.

Resolution order for the canonical source:
  1. ``--source-file PATH``  — read the canonical bytes from a local file
     (used by tests and offline runs; e.g. a local hub checkout).
  2. network fetch of ``CANONICAL_PATH`` from ``CANONICAL_REPO`` at
     ``CANONICAL_REF`` via ``raw.githubusercontent.com``.

Network policy. A drift gate must never silently pass on divergence, but it also
must not block a local commit just because the developer is offline. So a network
failure is a *skip* (exit 0 + Warning) by default. Pass ``--require-network`` in
CI — where connectivity is guaranteed — to turn a fetch failure into a hard error
so the gate cannot be bypassed by a transient outage on the enforcing runner.

Exit codes:
  0  local copy matches the canonical generator (or network-skipped locally)
  1  drift detected — local copy differs from the pinned canonical generator
  2  internal error (local copy missing, network required but unreachable, …)

Usage:
  python3 scripts/docs/check_catalog_generator_drift.py
  python3 scripts/docs/check_catalog_generator_drift.py --require-network
  python3 scripts/docs/check_catalog_generator_drift.py --source-file ../claude-shared/scripts/docs/gen_catalog.py
"""
from __future__ import annotations

import argparse
import difflib
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOCAL_GENERATOR = REPO / "scripts" / "docs" / "gen_catalog.py"

# The hub that owns the canonical generator implementation.
CANONICAL_REPO = "nolte/claude-shared"
CANONICAL_PATH = "scripts/docs/gen_catalog.py"
# Pinned hub release the local copy was last synced from. Bump this ONLY together
# with re-copying the canonical generator (the two must move as one commit), so
# the gate always compares against the exact upstream the local copy mirrors.
CANONICAL_REF = "v0.1.11"

RAW_URL = (
    f"https://raw.githubusercontent.com/{CANONICAL_REPO}/{CANONICAL_REF}/{CANONICAL_PATH}"
)


def _normalize(text: str) -> str:
    """Compare on logical content: ignore a trailing-newline delta between the
    GitHub raw payload and the on-disk file, but nothing else."""
    return text.replace("\r\n", "\n").rstrip("\n") + "\n"


def _fetch_canonical() -> str:
    with urllib.request.urlopen(RAW_URL, timeout=30) as resp:  # noqa: S310 (fixed https host)
        return resp.read().decode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-file",
        type=Path,
        default=None,
        help="Read canonical generator bytes from this local file instead of the network.",
    )
    parser.add_argument(
        "--require-network",
        action="store_true",
        help="Treat a network failure as a hard error (use in CI, where the network is guaranteed).",
    )
    args = parser.parse_args(argv)

    if not LOCAL_GENERATOR.is_file():
        print(
            f"Critical    {LOCAL_GENERATOR.relative_to(REPO)}  local catalog generator is missing",
            file=sys.stderr,
        )
        return 2
    local_text = LOCAL_GENERATOR.read_text(encoding="utf-8")

    if args.source_file is not None:
        if not args.source_file.is_file():
            print(
                f"Critical    {args.source_file}  --source-file does not exist",
                file=sys.stderr,
            )
            return 2
        canonical_text = args.source_file.read_text(encoding="utf-8")
        source_label = str(args.source_file)
    else:
        try:
            canonical_text = _fetch_canonical()
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            msg = (
                f"could not fetch canonical generator from {RAW_URL}: {exc}"
            )
            if args.require_network:
                print(f"Critical    {CANONICAL_PATH}  [network] {msg}", file=sys.stderr)
                return 2
            print(
                f"Warning     {CANONICAL_PATH}  [network] {msg} — drift check skipped "
                f"(offline). It runs enforced in CI.",
                file=sys.stderr,
            )
            return 0
        source_label = RAW_URL

    if _normalize(local_text) == _normalize(canonical_text):
        print(
            f"OK          scripts/docs/gen_catalog.py matches canonical "
            f"{CANONICAL_REPO}@{CANONICAL_REF}"
        )
        return 0

    diff = "".join(
        difflib.unified_diff(
            _normalize(canonical_text).splitlines(keepends=True),
            _normalize(local_text).splitlines(keepends=True),
            fromfile=f"canonical ({CANONICAL_REPO}@{CANONICAL_REF})",
            tofile="local (scripts/docs/gen_catalog.py)",
            n=2,
        )
    )
    print(
        f"Critical    scripts/docs/gen_catalog.py  drifted from canonical "
        f"{CANONICAL_REPO}@{CANONICAL_REF} (source: {source_label}).\n"
        f"            Do NOT hand-edit the vendored copy. Re-sync from the hub "
        f"(re-run nolte-shared:skill-agent-catalog-apply or copy the pinned\n"
        f"            canonical file) and bump CANONICAL_REF in this script in the "
        f"same commit. Divergence below (canonical → local):",
        file=sys.stderr,
    )
    print(diff, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
