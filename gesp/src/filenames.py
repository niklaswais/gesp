import re

_WINDOWS_INVALID_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_REPEATED_DASH_RE = re.compile(r"-{2,}")
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def safe_filename_part(value) -> str:
    """Return one Windows-safe filename segment without changing metadata."""
    cleaned = _WINDOWS_INVALID_RE.sub("-", str(value).strip())
    cleaned = _REPEATED_DASH_RE.sub("-", cleaned).strip(" .-")
    if not cleaned:
        return "_"
    if cleaned.upper() in _WINDOWS_RESERVED_NAMES:
        return f"_{cleaned}"
    return cleaned


def safe_filename(name) -> str:
    """Return a Windows-safe basename while preserving a final extension."""
    raw = str(name).strip()
    if "." in raw and not raw.endswith("."):
        stem, suffix = raw.rsplit(".", 1)
        return safe_filename_part(stem) + "." + safe_filename_part(suffix)
    return safe_filename_part(raw)
