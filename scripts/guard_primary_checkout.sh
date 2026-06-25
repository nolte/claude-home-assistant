#!/usr/bin/env bash
# Guard: the primary checkout MUST stay on `develop`.
#
# Wired in .pre-commit-config.yaml as the `guard-primary-checkout` hook
# (always_run, pass_filenames: false), so it fires on every `git commit`.
#
# Operationalises spec/project/parallel-working-copies/
# §Branch-to-worktree mapping: "MUST keep the primary checkout on
# `develop` at all times" and "MUST perform every change ... in a
# dedicated worktree; the primary checkout MUST NOT be switched off
# `develop` onto a feature branch". The spec is Implementation:
# documentary-only and its §Open Questions deferred a mechanical guard
# until a drift incident was recorded; that incident happened (the
# primary checkout was found sitting on a `docs/` feature branch), so
# this hook closes the loophole for the most common failure mode:
# committing feature work directly in the primary checkout.
#
# Self-detection: the hook is installed once in the shared hooks dir and
# therefore also fires inside linked worktrees. Worktrees are the
# *correct* place for feature-branch commits, so the guard exits 0 in any
# linked worktree and only enforces the rule in the primary checkout,
# distinguished by git-dir == git-common-dir.
set -euo pipefail

# Skip in CI and other non-interactive automation. CI runners (and
# `pre-commit run --all-files` via `task lint`) check the branch out in a
# detached HEAD inside a normal clone, where git-dir == git-common-dir —
# indistinguishable from a primary checkout sitting on a feature branch, so
# the guard would block the lint job on every feature-branch PR. This guard
# targets a developer's local `git commit`, not CI; `CI` is set by GitHub
# Actions and essentially every other CI provider.
if [ -n "${CI:-}" ]; then
  exit 0
fi

# Resolve both to absolute paths. In the primary checkout the per-worktree
# git-dir and the shared git-common-dir are the same directory; in a linked
# worktree the git-dir is .git/worktrees/<name> and they differ.
git_dir="$(cd "$(git rev-parse --git-dir)" && pwd -P)"
common_dir="$(cd "$(git rev-parse --git-common-dir)" && pwd -P)"

if [ "$git_dir" != "$common_dir" ]; then
  # Linked worktree — feature-branch commits belong here. Nothing to enforce.
  exit 0
fi

# Primary checkout: it MUST be on `develop`.
branch="$(git symbolic-ref --quiet --short HEAD || true)"

if [ "$branch" = "develop" ]; then
  exit 0
fi

if [ -z "$branch" ]; then
  state="a detached HEAD"
else
  state="branch '$branch'"
fi

cat >&2 <<EOF
✖ Primary checkout is on $state, not 'develop' — commit blocked.

  The primary checkout ($(pwd -P)) is for integration only and MUST stay
  on 'develop' at all times (spec/project/parallel-working-copies/
  §Branch-to-worktree mapping). Feature work — feat/ fix/ chore/ docs/
  exp/ — happens in a dedicated worktree that branches off develop.

  Repair the drift instead of committing here:

    # 1. park the current feature work in its own worktree
    git switch develop
    git worktree add "\${NOLTE_WORKTREE_ROOT:-~/repos/.worktrees}/claude-home-assistant/<slug>" $branch
    #    (or, for a fresh branch off develop: task worktree:add -- $branch)

    # 2. restore the primary checkout to the remote tip
    git fetch origin develop && git merge --ff-only origin/develop

  Then re-run your commit from inside the worktree.
EOF
exit 1
