#!/usr/bin/env bash
# Create a git worktree under the configurable portfolio worktree root.
#
# Wired in Taskfile.yml as `task worktree:add -- <branch> [slug]`.
#
# Operationalises spec/project/parallel-working-copies/ §Path layout,
# §Lifecycle: Create, and §Lifecycle: Plan before work (it seeds a
# .resume/<slug>/plan.md plan stub so the documentary-only plan gate is
# self-serving). The §Path layout SHOULD places every worktree under a
# single centralized root `<root>/<repo>/<short-slug>/`. That root used to be
# hard-coded as `~/repos/.worktrees`; this helper makes it a per-machine
# choice via the NOLTE_WORKTREE_ROOT environment variable while keeping
# `~/repos/.worktrees` as the default, so the layout stays identical for
# anyone who sets nothing and consistent for anyone who relocates it.
#
# Guarantees, so every worktree lands in the same predictable place:
#   - <root> comes from NOLTE_WORKTREE_ROOT (default ~/repos/.worktrees)
#   - <repo> is derived from the origin remote, never guessed
#   - the branch is created with an explicit base ref (origin/develop) per
#     §Lifecycle: Create, after a fetch, so the worktree starts from the
#     remote tip and the primary checkout's local develop is irrelevant
#   - the branch prefix is validated against spec/project/branching-model/
set -euo pipefail

usage() {
  cat >&2 <<EOF
Usage: task worktree:add -- <branch> [slug]

  <branch>  Full branch name including its prefix, e.g. feat/parser-fix.
            Allowed prefixes: feat/ fix/ chore/ docs/ exp/
  [slug]    Optional kebab-case directory name under the worktree root.
            Defaults to the branch name with its prefix stripped.

The worktree is created at:
  \${NOLTE_WORKTREE_ROOT:-~/repos/.worktrees}/<repo>/<slug>/
based on origin/develop.
EOF
  exit 2
}

branch="${1:-}"
slug="${2:-}"

[ -n "$branch" ] || usage

# Branch-prefix rule from spec/project/branching-model/.
case "$branch" in
  feat/*|fix/*|chore/*|docs/*|exp/*) : ;;
  *)
    echo "✖ Branch '$branch' lacks an allowed prefix (feat/ fix/ chore/ docs/ exp/)." >&2
    echo "  The path slug may drop the prefix, but the branch MUST NOT (branching-model)." >&2
    exit 1
    ;;
esac

# Default slug: branch name minus the prefix segment.
if [ -z "$slug" ]; then
  slug="${branch#*/}"
fi

# A slug MUST be a single path segment — never a traversal or nested path.
case "$slug" in
  */*|*..*|"")
    echo "✖ Slug '$slug' must be a single kebab-case path segment." >&2
    exit 1
    ;;
esac

# Resolve the configurable root. Tilde in the env value is not expanded by the
# shell when it arrives as a variable, so expand a leading ~ ourselves.
root="${NOLTE_WORKTREE_ROOT:-$HOME/repos/.worktrees}"
case "$root" in
  "~") root="$HOME" ;;
  "~/"*) root="$HOME/${root#\~/}" ;;
esac

# Derive <repo> from the origin remote — never inferred from the cwd.
origin_url="$(git remote get-url origin)"
repo="$(basename "$origin_url" .git)"

dest="$root/$repo/$slug"

if [ -e "$dest" ]; then
  echo "✖ Destination already exists: $dest" >&2
  exit 1
fi

echo "→ Worktree root : $root"
echo "→ Repository    : $repo"
echo "→ Branch        : $branch"
echo "→ Destination   : $dest"

git fetch origin develop --quiet
git worktree add -b "$branch" "$dest" origin/develop

# Plan-before-work gate, per spec/project/parallel-working-copies/
# §Lifecycle: Plan before work. Seed a foundational implementation-plan stub
# inside the new worktree so the documentary-only gate is self-serving: the
# contributor fills it in before any substantive work begins. The path lives
# under .resume/ (gitignored), so the stub is a worktree-local working aid,
# never a committed artefact that competes with the feature's deliverables.
plan_dir="$dest/.resume/$slug"
plan="$plan_dir/plan.md"
mkdir -p "$plan_dir"

# Header lines interpolate branch/slug/dest and contain no backticks.
cat > "$plan" <<EOF
# Implementation plan: $slug

> Foundational plan for worktree work on branch '$branch'. Authored BEFORE
> substantive work begins, so a fresh, resumable top-level session started in
> this worktree can pick the work up from a known starting point rather than
> reconstructing intent from a half-finished diff.
>
> - Branch: $branch
> - Worktree: $dest
> - Base: origin/develop
EOF

# Body is literal (quoted heredoc) so its backticks stay verbatim.
cat >> "$plan" <<'EOF'

## 1. Goal

<!-- What outcome does this worktree deliver? One or two sentences. -->

## 2. Current state (researched)

<!-- Relevant specs, files, and prior art — the source of truth for the design. -->

## 3. Design decision

<!-- The load-bearing choice, plus the open questions to confirm with the
     operator BEFORE work starts. -->

## 4. Work steps (ordered)

1. <!-- first concrete step -->

## 5. Invariants / guardrails

<!-- Rules carried over from CLAUDE.md and the governing specs that must hold. -->

## 6. Status / resume anchors

- [ ] <!-- first task; the first unchecked box is where the next session resumes -->

> Resume: cd into this worktree and run `task resume` (or `claude --resume`),
> then continue this plan from the first unchecked box.
EOF

echo
echo "✓ Worktree ready."
echo
echo "→ Plan-before-work gate (spec/project/parallel-working-copies/ §Lifecycle: Plan before work):"
echo "    A plan stub was written to .resume/$slug/plan.md inside the worktree."
echo "    Fill it in BEFORE starting substantive work on this branch."
echo
echo "→ Start the work in a FRESH top-level session scoped to this worktree, so it"
echo "  stays resumable via 'task resume' / 'claude --resume' (subagent and"
echo "  Workflow runs are not independently resumable):"
echo "    cd $dest && claude"
