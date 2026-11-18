#!/usr/bin/env python3
"""Dev-only: load the QML tree headlessly, drive it, and fail on warnings.

The point is not to re-test the parser (that is tests/test_evaluator.py) but to
catch the things only a real QML load finds: a renamed slot, a missing property,
a binding loop, a key that no longer inserts, a settings write that never lands.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

# Hermetic: the app reads the pywal palette and the config from the real home,
# which would make the result depend on the current wallpaper.
_SANDBOX = tempfile.mkdtemp(prefix="hyprtk-calc-boot-")
os.environ["XDG_CONFIG_HOME"] = os.path.join(_SANDBOX, "config")
os.environ["XDG_CACHE_HOME"] = os.path.join(_SANDBOX, "cache")
os.environ["HYPRTK_WAL_HOME"] = _SANDBOX
os.environ["HYPRTK_CALC_CONFIG_DIR"] = os.path.join(_SANDBOX, "config", "hyprtk-calc")
os.environ["HYPRTK_CALC_HISTORY"] = os.path.join(_SANDBOX, "history.jsonl")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Q_ARG, QMetaObject, Qt, qInstallMessageHandler  # noqa: E402
from PySide6.QtQuick import QQuickItem  # noqa: E402
from PySide6.QtQuick import QQuickWindow  # noqa: E402
from shiboken6 import getCppPointer, wrapInstance  # noqa: E402

from hyprtk_calc.app import create  # noqa: E402

problems: list[str] = []

# Messages that are not defects in this app.
IGNORED = (
    "QStandardPaths",
    "This plugin does not support",
    "Failed to create",
)


def handler(mode, context, message: str) -> None:
    if any(fragment in message for fragment in IGNORED):
        return
    problems.append(message)


def fail(message: str) -> None:
    problems.append(message)


def result_of(root) -> dict:
    return dict(root.property("result") or {})


def find(root, fragment: str):
    """First item in the tree whose QML type name contains ``fragment``."""
    stack = [wrapInstance(getCppPointer(root)[0], QQuickWindow).contentItem()]
    while stack:
        item = stack.pop()
        if fragment in item.metaObject().className():
            return item
        stack.extend(item.childItems())
    return None


def main() -> int:
    qInstallMessageHandler(handler)
    app, engine, bridge = create(["hyprtk-calc"])
    if not engine.rootObjects():
        print("FAIL: QML did not load")
        for problem in problems:
            print("  ", problem)
        return 1

    root = engine.rootObjects()[0]
    window = wrapInstance(getCppPointer(root)[0], QQuickWindow)
    print("booted:", window.width(), "x", window.height())

    # -- live evaluation
    root.setProperty("expression", "2+2*3")
    row = result_of(root)
    if row.get("display") != "8":
        fail("live evaluation: expected 8, got {0!r}".format(row.get("display")))

    root.setProperty("expression", "1/0")
    if not result_of(root).get("error"):
        fail("division by zero produced no error message")

    root.setProperty("expression", "sqrt(2)")
    if not result_of(root).get("display", "").startswith("1.41421356"):
        fail("sqrt(2) display: {0!r}".format(result_of(root).get("display")))

    # -- the keypad path: emit the signal every key emits and let Main handle it
    keypad = find(root, "Keypad")
    if keypad is None:
        fail("keypad not found in the item tree")
    root.setProperty("expression", "")
    for token in ("7", "*", "6", "="):
        if token == "=":
            QMetaObject.invokeMethod(keypad, "action", Q_ARG(str, "equals"))
        else:
            QMetaObject.invokeMethod(keypad, "token", Q_ARG(str, token))
    if root.property("expression") != "7*6":
        fail("keypad insertion: expression is {0!r}".format(root.property("expression")))
    row = result_of(root)
    if row.get("display") != "42":
        fail("commit: expected 42, got {0!r}".format(row.get("display")))
    if len(bridge.history) != 1:
        fail("commit did not record history ({0} entries)".format(len(bridge.history)))
    if not os.path.exists(os.environ["HYPRTK_CALC_HISTORY"]):
        fail("history file was not written")

    # -- after a commit an operator continues from the result
    QMetaObject.invokeMethod(keypad, "token", Q_ARG(str, "+"))
    if root.property("expression") != "42+":
        fail("operator after '=' should continue from the result, got {0!r}"
             .format(root.property("expression")))

    # -- hex digits open a 0x literal in programmer mode
    root.setProperty("mode", "programmer")
    root.setProperty("expression", "")
    QMetaObject.invokeMethod(keypad, "action", Q_ARG(str, "hex:F"))
    if root.property("expression") != "0xF":
        fail("programmer hex key: {0!r}".format(root.property("expression")))

    # -- the four-base readout
    root.setProperty("expression", "255")
    bases = dict(result_of(root).get("bases") or {})
    if bases.get("16") != "0xFF" or bases.get("2") != "0b11111111":
        fail("base readout: {0!r}".format(bases))

    # -- settings round-trip through the bridge (config file included)
    bridge.setConfig("angle", "rad")
    if bridge.config.get("angle") != "rad":
        fail("setConfig did not update the config property")
    from hyprtk_calc.settings import Settings

    if Settings().get("angle") != "rad":
        fail("setConfig did not persist to disk")
    bridge.setConfig("keypad", "scientific")
    if root.property("mode") != "scientific":
        fail("mode should follow the keypad setting, got {0!r}".format(root.property("mode")))

    # -- history recall (the drawer emits, Main applies)
    panel = find(root, "HistoryPanel")
    if panel is None:
        fail("history drawer not found in the item tree")
    root.setProperty("expression", "")
    QMetaObject.invokeMethod(panel, "recall", Q_ARG(int, 0))
    if root.property("expression") != "7*6":
        fail("history recall: {0!r}".format(root.property("expression")))
    bridge.clearHistory()
    if len(bridge.history) != 0:
        fail("clearHistory left entries behind")

    # -- the overlays must instantiate without warnings
    root.setProperty("historyOpen", True)
    root.setProperty("historyOpen", False)
    root.setProperty("settingsOpen", True)
    root.setProperty("settingsOpen", False)

    window.close()
    if problems:
        print("FAIL: {0} problem(s)".format(len(problems)))
        for problem in problems:
            print("  -", problem)
        return 1
    print("BOOTCHECK OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
