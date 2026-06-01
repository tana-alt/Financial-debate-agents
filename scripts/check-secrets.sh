#!/usr/bin/env sh
set -eu
CDPATH=

ROOT="${FOUNDATION_REPO_ROOT:-$(cd -- "$(dirname -- "$0")/.." && pwd)}"

if ! command -v gitleaks >/dev/null 2>&1; then
  echo "secret scan: missing gitleaks; install Gitleaks and rerun" >&2
  exit 127
fi

WORKTREE_INPUT="$(mktemp)"
CACHED_INPUT="$(mktemp)"
trap 'rm -f "$WORKTREE_INPUT" "$CACHED_INPUT"' EXIT

if git -C "$ROOT" grep -I -n -e . -- . >"$WORKTREE_INPUT"; then
  gitleaks --config "$ROOT/.gitleaks.toml" --redact --no-banner --log-level warn stdin \
    <"$WORKTREE_INPUT"
else
  echo "secret scan: skipped tracked working tree scan (no tracked text content)"
fi

if git -C "$ROOT" grep --cached -I -n -e . -- . >"$CACHED_INPUT"; then
  gitleaks --config "$ROOT/.gitleaks.toml" --redact --no-banner --log-level warn stdin \
    <"$CACHED_INPUT"
else
  echo "secret scan: skipped cached/index scan (no staged text content)"
fi

if git -C "$ROOT" rev-parse --verify HEAD >/dev/null 2>&1; then
  gitleaks git --config "$ROOT/.gitleaks.toml" --redact --no-banner --log-level warn "$ROOT"
else
  echo "secret scan: skipped git history scan (no commits yet)"
fi

echo "secret scan: passed"
