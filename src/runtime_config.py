"""Runtime environment configuration helpers."""

from __future__ import annotations

import math
import os
from pathlib import Path


def _env_value(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value


def env_str(name: str, default: str) -> str:
    """Return a string env value, falling back for unset or empty values."""

    value = _env_value(name)
    return default if value is None else value


def env_int(name: str, default: int, *, min_value: int | None = None) -> int:
    """Return an integer env value or raise ``ValueError`` for invalid input."""

    value = _env_value(name)
    if value is None:
        parsed = default
    else:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc
    if min_value is not None and parsed < min_value:
        raise ValueError(f"{name} must be >= {min_value}")
    return parsed


def env_float(name: str, default: float, *, min_value: float | None = None) -> float:
    """Return a finite float env value or raise ``ValueError`` for invalid input."""

    value = _env_value(name)
    if value is None:
        parsed = default
    else:
        try:
            parsed = float(value)
        except ValueError as exc:
            raise ValueError(f"{name} must be a number") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{name} must be finite")
    if min_value is not None and parsed < min_value:
        raise ValueError(f"{name} must be >= {min_value}")
    return parsed


def env_bool(name: str, default: bool) -> bool:
    """Return a boolean env value or raise ``ValueError`` for invalid input."""

    value = _env_value(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def env_path(name: str, default: str | Path) -> Path:
    """Return a path env value or raise ``ValueError`` for invalid path strings."""

    value = _env_value(name)
    if value is None:
        return Path(default)
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL bytes")
    return Path(value)
