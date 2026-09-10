"""
Single place the OpenAQ API key is resolved.

Previously the key was hard-coded in fetch_reference_fem_2022_2023.py and three other
scripts re-read it out of that file with a regex. That key is dead (every request returns
HTTP 401), which is why the 12,243-pair result and the 2024 reference level cannot be
reproduced -- see CANONICAL_NUMBERS.md §4 and §8.

Get a free key at https://explore.openaq.org/register, then either:
    setx OPENAQ_API_KEY "..."            (Windows, new shells)
    export OPENAQ_API_KEY=...            (bash)
or add a line to the repo-root .env:
    OPENAQ_API_KEY=...

.env is gitignored. Never commit the key.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

HELP = (
    "OpenAQ API key not found.\n"
    "  Get one free at https://explore.openaq.org/register, then set OPENAQ_API_KEY\n"
    "  as an environment variable or add OPENAQ_API_KEY=... to the repo-root .env.\n"
    "  The old hard-coded key was revoked and returns HTTP 401."
)


def openaq_key(required: bool = True) -> str | None:
    """Return the OpenAQ API key, or None/SystemExit if absent."""
    key = os.getenv("OPENAQ_API_KEY", "").strip()
    if not key:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                name, _, value = line.partition("=")
                # matches OPENAQ_API_KEY, OPENAQ_KEY and the existing bare `OpenAQ=`
                if name.strip().lower().startswith("openaq"):
                    key = value.strip().strip("'\"")
                    break
    if not key and required:
        raise SystemExit(HELP)
    return key or None


def openaq_headers() -> dict:
    return {"X-API-Key": openaq_key()}
