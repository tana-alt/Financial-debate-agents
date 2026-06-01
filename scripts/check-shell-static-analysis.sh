#!/usr/bin/env sh
set -eu
CDPATH=

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"

if ! command -v shellcheck >/dev/null 2>&1; then
  echo "shell static analysis: missing shellcheck; install ShellCheck and rerun" >&2
  exit 127
fi

FILES="
hooks/pre-commit
hooks/pre-push
scripts/check-agent-worktree-policy.sh
scripts/check-dev-environment.sh
scripts/check-repo-hygiene.sh
scripts/check-secrets.sh
scripts/check-shell-static-analysis.sh
scripts/setup-agent-environment.sh
"

existing_files=""
for file in $FILES; do
  if [ -f "$ROOT/$file" ]; then
    existing_files="${existing_files}${ROOT}/${file}
"
  fi
done

if [ -z "$existing_files" ]; then
  echo "shell static analysis: no shell files found"
  exit 0
fi

printf '%s' "$existing_files" | xargs shellcheck -s sh
echo "shell static analysis: passed"
