"""
Convenience runner for the sanity suite.

Usage:
    python run_sanity.py                 # run all sanity tests
    python run_sanity.py -k login        # run only login-related tests
    python run_sanity.py --headed        # force headed mode
    python run_sanity.py --browser firefox
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoPythone2e sanity runner")
    parser.add_argument("-k", "--keyword", help="pytest -k keyword filter")
    parser.add_argument("-m", "--marker", default="sanity", help="pytest marker (default: sanity)")
    parser.add_argument("--browser", help="Override BROWSER env var (chromium|firefox|webkit)")
    parser.add_argument("--headed", action="store_true", help="Force headed mode")
    parser.add_argument("--headless", action="store_true", help="Force headless mode")
    parser.add_argument("-n", "--workers", help="Run in parallel with N workers (pytest-xdist)")
    args, extra = parser.parse_known_args()

    env = os.environ.copy()
    if args.browser:
        env["BROWSER"] = args.browser
    if args.headed:
        env["HEADLESS"] = "false"
    if args.headless:
        env["HEADLESS"] = "true"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_report = ROOT / "reports" / f"sanity_report_{timestamp}.html"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-m",
        args.marker,
        f"--html={html_report}",
        "--self-contained-html",
    ]
    if args.keyword:
        cmd += ["-k", args.keyword]
    if args.workers:
        cmd += ["-n", str(args.workers)]
    cmd += extra

    print(f"Running: {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(ROOT), env=env)
    print(f"\nReport: {html_report}")
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
