#!/usr/bin/env bash
# Create a git worktree under the configurable portfolio worktree root.
#
# Wired in Taskfile.yml as `task worktree:add -- <branch> [slug]`.
#
# Operationalises spec/project/parallel-working-copies/ §Path layout and
# §Lifecycle: Create. The §Path layout SHOULD places every worktree under a
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

echo
echo "✓ Worktree ready. Start a session scoped to it with:"
echo "    cd $dest && claude"
