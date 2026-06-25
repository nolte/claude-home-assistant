#!/usr/bin/env python3
"""List resumable Claude Code sessions for the current working copy.

Run via `task resume`. After a notebook crash, terminal close, or session
expiry, Claude Code's own transcript for this directory survives under
~/.claude/projects/<encoded-cwd>/<session-id>.jsonl. This script surfaces those
transcripts — newest first, with their opening prompt — and prints the exact
`claude --resume` command, so getting back to an interrupted run is one copy-paste.

This is the session-level safety net that covers ALL work in a top-level
session, including free-form work that no resumable skill governs. It does NOT
recover subagent runs (those live under <session-id>/subagents/ and cannot be
--resume'd) — which is exactly why long feature work belongs in a top-level
session inside the worktree, not in a dispatched worktree-isolated subagent.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECTS_ROOT = Path.home() / ".claude" / "projects"
MAX_SESSIONS = 12


def encode_cwd(path: Path) -> str:
    # Claude Code encodes the project dir by replacing every "/" and "." with "-".
    return re.sub(r"[/.]", "-", str(path.resolve()))


def first_user_prompt(transcript: Path) -> str:
    """Best-effort first human turn from a .jsonl transcript, for recognition."""
    try:
        with transcript.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "user":
                    continue
                msg = obj.get("message") or {}
                content = msg.get("content")
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text = part.get("text", "")
                            break
                text = " ".join(text.split())
                # Skip command/tool-result envelopes; we want a real prompt.
                if text and not text.startswith("<"):
                    return text[:90]
    except Exception:
        pass
    return "(no readable prompt)"


def main() -> int:
    cwd = Path.cwd()
    session_dir = PROJECTS_ROOT / encode_cwd(cwd)

    print(f"Working copy : {cwd}")
    print(f"Transcripts  : {session_dir}")

    if not session_dir.is_dir():
        print("\nNo Claude Code sessions recorded for this path yet.")
        print("(If you worked here via a dispatched worktree-isolated subagent,")
        print(" the transcript lives under the PARENT session and cannot be --resume'd.")
        print(" Run long feature work as a top-level session inside the worktree instead.)")
        return 0

    sessions = sorted(
        session_dir.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not sessions:
        print("\nNo top-level sessions found (only subagent transcripts, which")
        print("cannot be resumed). Start a fresh session here with `claude`.")
        return 0

    print(f"\nResumable sessions (newest first, showing up to {MAX_SESSIONS}):\n")
    for transcript in sessions[:MAX_SESSIONS]:
        sid = transcript.stem
        ts = datetime.fromtimestamp(transcript.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {ts}  {sid}")
        print(f"             {first_user_prompt(transcript)}")

    newest = sessions[0].stem
    print("\nResume the most recent:   claude --continue")
    print("Pick interactively:       claude --resume")
    print(f"Resume a specific one:    claude --resume {newest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
