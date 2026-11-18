#!/usr/bin/env python3
"""Dev-only: render the window headlessly to a PNG for the README.

    python3 scripts/screenshot.py docs/shot.png [--mode scientific] [--expr "2+2"]

Uses the offscreen platform, so it works over SSH and in CI. The window is
grabbed after its first frame rather than on a timer: grabbing too early
returns an unpolished frame with a pending layout.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

_SANDBOX = tempfile.mkdtemp(prefix="hyprtk-calc-shot-")
os.environ.setdefault("XDG_CONFIG_HOME", os.path.join(_SANDBOX, "config"))
os.environ.setdefault("XDG_CACHE_HOME", os.path.join(_SANDBOX, "cache"))
os.environ.setdefault("HYPRTK_WAL_HOME", _SANDBOX)
os.environ.setdefault("HYPRTK_CALC_CONFIG_DIR", os.path.join(_SANDBOX, "config", "hyprtk-calc"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtQuick import QQuickWindow  # noqa: E402
from shiboken6 import getCppPointer, wrapInstance  # noqa: E402

from hyprtk_calc.app import create  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--mode", default="basic", choices=("basic", "scientific", "programmer"))
    parser.add_argument("--expr", default="(48 * 1.15) + 12^2 / 8")
    parser.add_argument("--precision", type=int, default=None)
    parser.add_argument("--size", default="460x700", help="WIDTHxHEIGHT")
    parser.add_argument("--history", action="store_true", help="open the history drawer")
    parser.add_argument("--settings", action="store_true", help="open the settings sheet")
    args = parser.parse_args()

    width, _, height = args.size.partition("x")
    app, engine, bridge = create(["hyprtk-calc"])
    root = engine.rootObjects()[0]
    root.setProperty("width", int(width))
    root.setProperty("height", int(height))
    if args.precision:
        bridge.setConfig("precision", args.precision)
    root.setProperty("mode", args.mode)
    root.setProperty("expression", args.expr)
    if args.mode == "programmer":
        root.setProperty("expression", args.expr if args.expr != "(48 * 1.15) + 12^2 / 8" else "0x2f1 + 0b1010")
    if args.history or args.settings:
        for expression, value in (
            ("12^2 / 8", "18"),
            ("48 * 1.15", "55.2"),
            ("sqrt(2)", "1.41421356237"),
            ("255", "255"),
        ):
            bridge.history.add(expression, value)
        bridge.historyChanged.emit()
        root.setProperty("historyOpen", args.history)
        root.setProperty("settingsOpen", args.settings)
    # The root object arrives as a plain QWindow wrapper; re-wrap the same
    # pointer as a QQuickWindow, which is what exposes grabWindow().
    window = wrapInstance(getCppPointer(root)[0], QQuickWindow)

    def shoot() -> None:
        # Grab a frame that has actually been composed: grabbing in the same
        # turn as the state change returns the previous frame, and a half-drawn
        # segmented pill is exactly what that looks like.
        window.update()
        window.grabWindow().save(args.output)
        print("wrote", args.output, window.width(), "x", window.height())
        app.quit()

    QTimer.singleShot(120, shoot)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
