#!/usr/bin/env sh
set -eu
CDPATH=

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
STATUS=0

check() {
  if "$@"; then
    printf 'ok: %s\n' "$*"
  else
    printf 'missing: %s\n' "$*" >&2
    STATUS=1
  fi
}

check command -v git
check command -v uv
check command -v python3
check command -v shellcheck
check command -v gitleaks

if command -v git >/dev/null 2>&1; then
  git --version | sed 's/^/ok: /'
fi

if command -v uv >/dev/null 2>&1; then
  uv --version | sed 's/^/ok: /'
fi

if command -v shellcheck >/dev/null 2>&1; then
  shellcheck --version | sed -n 's/^version: /ok: shellcheck /p' | head -n 1
fi

if command -v gitleaks >/dev/null 2>&1; then
  GITLEAKS_VERSION="$(gitleaks version 2>/dev/null || gitleaks --version 2>/dev/null || true)"
  if [ -n "$GITLEAKS_VERSION" ]; then
    printf 'ok: gitleaks %s\n' "$GITLEAKS_VERSION"
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY' || STATUS=1
import sys

version = sys.version_info
if (3, 12) <= version < (3, 15):
    print(f"ok: python3 {version.major}.{version.minor}.{version.micro}")
else:
    print(
        f"missing: python3 >=3.12,<3.15; found {version.major}.{version.minor}.{version.micro}",
        file=sys.stderr,
    )
    raise SystemExit(1)
PY
fi

HOOKS_PATH="$(git -C "$ROOT" config --get core.hooksPath 2>/dev/null || true)"
if [ "$HOOKS_PATH" = "hooks" ]; then
  echo "ok: core.hooksPath=hooks"
else
  echo "missing: core.hooksPath=hooks; run sh scripts/setup-agent-environment.sh" >&2
  STATUS=1
fi

CANONICAL_ROOT="$(git -C "$ROOT" config --get foundation.canonicalRoot 2>/dev/null || true)"
if [ -n "$CANONICAL_ROOT" ] && [ -d "$CANONICAL_ROOT" ]; then
  echo "ok: foundation.canonicalRoot=$CANONICAL_ROOT"
else
  echo "missing: foundation.canonicalRoot; run sh scripts/setup-agent-environment.sh" >&2
  STATUS=1
fi

if git -C "$ROOT" submodule status >/dev/null 2>&1; then
  echo "ok: submodule metadata"
else
  echo "missing: valid submodule metadata" >&2
  STATUS=1
fi

exit "$STATUS"
