#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

echo "== unit tests =="
PYTHONPATH=. python3 -m unittest discover -s tests

echo "== python syntax =="
python3 -m compileall -q hyprtk_calc tests scripts

echo "== qml lint =="
if command -v qmllint >/dev/null 2>&1; then
    while IFS= read -r f; do qmllint "$f"; done < <(find hyprtk_calc/qml -name '*.qml')
else
    echo "qmllint not installed — skipped"
fi

echo "== shell syntax =="
bash -n install.sh
sh -n bin/hyprtk-calc

echo "== headless boot =="
timeout 60 python3 scripts/bootcheck.py

echo "== cli =="
PYTHONPATH=. python3 -m hyprtk_calc --version | grep -q '^hyprtk-calc '
PYTHONPATH=. python3 -m hyprtk_calc "2+2*3" | grep -qx '8'
if PYTHONPATH=. python3 -m hyprtk_calc "1/0" >/dev/null 2>&1; then
    echo "1/0 should have exited non-zero" >&2
    exit 1
fi

echo "== installer round-trip =="
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
HOME="$TMP" XDG_DATA_HOME="$TMP/.local/share" ./install.sh >/dev/null
test -x "$TMP/.local/bin/hyprtk-calc"
test -f "$TMP/.local/share/applications/hyprtk-calc.desktop"
test -f "$TMP/.local/share/hyprtk-calc/hyprtk-calc.svg"
grep -q "Exec=$TMP/.local/share/hyprtk-calc/bin/hyprtk-calc" "$TMP/.local/share/applications/hyprtk-calc.desktop"
HOME="$TMP" XDG_DATA_HOME="$TMP/.local/share" "$TMP/.local/share/hyprtk-calc/bin/hyprtk-calc" --version >/dev/null
HYPRTK_DRYRUN=1 ./install.sh --system | grep -q 'would install'
HOME="$TMP" XDG_DATA_HOME="$TMP/.local/share" ./install.sh --uninstall >/dev/null
test ! -e "$TMP/.local/share/hyprtk-calc"

echo "QA PASS"
