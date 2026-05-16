"""Refresh tests/fixtures/ from live court portals.

Shells out to ``gesp --probe-only -p tests/fixtures``. After running:

  * ``git diff tests/fixtures/`` shows which portals altered their markup.
  * ``pytest`` verifies that the spiders still parse the new responses.

Usage::

    python tests/refresh_fixtures.py            # refresh all 17 states
    python tests/refresh_fixtures.py be bw      # refresh selected states

Exits non-zero if any probe failed (network error, HTTP error, missing key, ...).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def main(argv: list[str]) -> int:
    cmd = [sys.executable, "-m", "gesp", "--probe-only", "-p", str(FIXTURES_DIR)]
    if argv:
        cmd += ["-s", ",".join(argv)]
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
