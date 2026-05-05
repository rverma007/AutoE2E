"""
open_latest_trace.py — open the most recent Playwright trace in the
official trace viewer.

Usage:
    python open_latest_trace.py            # opens newest trace in traces/
    python open_latest_trace.py --failed   # newest trace for a FAILED test
    python open_latest_trace.py <path>     # explicit file
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TRACES_DIR = Path(__file__).resolve().parent / "traces"


def _newest(pattern: str = "*.zip") -> Path | None:
    candidates = sorted(TRACES_DIR.glob(pattern), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def main() -> int:
    args = sys.argv[1:]

    if args and args[0] not in {"--failed"}:
        target = Path(args[0]).expanduser().resolve()
    elif args and args[0] == "--failed":
        # Trace file names include the test name — skip session-scoped prefixes
        # so we only get actual per-test traces.
        target = _newest("*.zip")
    else:
        target = _newest("*.zip")

    if target is None or not target.exists():
        print(f"No trace files found under {TRACES_DIR}")
        return 1

    print(f"Opening trace -> {target}")
    try:
        return subprocess.call(["playwright", "show-trace", str(target)])
    except FileNotFoundError:
        # Fallback: try `python -m playwright`
        return subprocess.call(
            [sys.executable, "-m", "playwright", "show-trace", str(target)]
        )


if __name__ == "__main__":
    raise SystemExit(main())
