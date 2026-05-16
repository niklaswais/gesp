"""End-to-end smoke test against real court portals.

Marked `live` so it's skipped by default — run manually with `pytest -m live`.
Court portals can be slow, rate-limited, or temporarily down; this is a local
sanity-check, not a CI regression gate.
"""

import subprocess
import sys

import pytest


@pytest.mark.live
def test_real_bund_scrape_produces_file(tmp_path):
    """Run `python -m gesp -s bund -c bgh` against the real federal portal.

    Asserts the process exits cleanly and at least one decision file lands in
    the output folder. ~30s on a fast connection.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "gesp", "-s", "bund", "-c", "bgh", "-p", str(tmp_path)],
        input="y\n",
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, f"gesp exited {proc.returncode}\nstderr:\n{proc.stderr}"
    bund_dir = tmp_path / "bund"
    assert bund_dir.is_dir(), f"no bund/ folder under {tmp_path}\nstdout:\n{proc.stdout}"
    files = list(bund_dir.glob("*"))
    assert files, f"no files produced under {bund_dir}\nstdout:\n{proc.stdout}"
