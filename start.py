#!/usr/bin/env python3
"""Zero-friction launcher for CyberPulse terminal and Web Cyberdeck."""

import sys
from pathlib import Path

# Ensure local cyberpulse package is importable when executed directly
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from cyberpulse import cli  # noqa: E402


def start(argv=None) -> int:
    """Launch the Web Cyberdeck by default, or forward custom CLI arguments."""
    if argv is not None:
        args = list(argv)
    else:
        args = sys.argv[1:]
    if not args:
        # Default zero-friction startup: launch Web Cyberdeck in browser
        args = ["--web"]
    return cli.main(args)


if __name__ == "__main__":
    sys.exit(start())
