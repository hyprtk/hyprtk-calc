# hyprtk-calc — plan

Status: **v0.1.0 published 2026-11-18** — repo `hyprtk/hyprtk-calc` on `main`,
tag `v0.1.0`, installed locally (`~/.local/share/hyprtk-calc`) and wired into
`hyprtk-merged` (installer step, `Super + N` / `XF86Calculator`, window rule,
docs, ISO). What is left is the production publish (`push-all`) and two
optional follow-ups, both listed below.

## Decisions (and why)

Full survey and measurements: [RESEARCH.md](RESEARCH.md).

| Decision | Rationale |
|---|---|
| `decimal.Decimal` core, `math` only for transcendentals | `0.1+0.2 = 0.3`; documented 15-digit limit on `sin`/`ln`, exact everywhere else |
| Hand-written tokenizer + precedence parser | exact literals, no `eval`, implicit multiplication, `!`/`%`/`xor`/`<<` on our terms |
| Display precision + 12 guard digits | `sin(30°)` shows `0.5`, not the double's own noise |
| Expression-first UI with a keypad beside it | the SpeedCrunch lesson: typing and tapping are the same expression |
| `%` = `/100` | one meaning for `+`, documented; no hidden operand-dependent rule |
| Base conversion display-side | programmer readout of HEX/OCT/DEC/BIN; input stays Python-like |
| PySide6 + QML, same palette resolver | one wallpaper repaints the suite; no new runtime dependency |

## Architecture

```
hyprtk_calc/
  number.py      Decimal literals, display formatting, grouping, base conversion
  evaluator.py   tokenizer, parser, function registry, Context (precision/angle/ans)
  history.py     JSONL append-only history, shared with the CLI
  settings.py    ~/.config/hyprtk-calc/config.json, validated on read and write
  palette.py     pywal/bar theme -> UI tokens, keypad surfaces by blending
  bridge.py      QML facade: evaluate/commit/copy/memory/history/config
  cli.py         the shell calculator (-p, -a, -b, --json, --history, stdin)
  app.py         QGuiApplication + QQmlApplicationEngine
  qml/
    Main.qml             window, display, keyboard handling, overlays
    Keypad.qml           per-mode key models (basic / scientific / programmer)
    components/          CalcKey, Segmented, IconButton, HistoryPanel, SettingsSheet
    theme/               Glyph (Symbols Nerd Font), util.js
```

Python owns numbers, storage and the palette; QML owns chrome. The only object
crossing the boundary is `Bridge`, one context property.

## v0.1.0 — what the scaffold does

- [x] Exact decimal arithmetic, 12 significant digits by default (3–60 in
      settings), `0.1+0.2 = 0.3`
- [x] Hand-written parser: `+ - * / ^ ! %`, parentheses, implicit
      multiplication (`2pi`, `3(4+5)`), unary sign, right-associative `^`
- [x] Bitwise layer: `& | xor ~ << >>`, `0x`/`0b`/`0o` literals, `1_000_000`
- [x] 40 functions: trig/hyperbolic (angle-aware), logs, roots, rounding,
      combinatorics, gcd/lcm, min/max/sign
- [x] Constants `pi e tau phi`, `ans`, named variables in the context
- [x] Live result while typing, `Enter` commits, `Esc` clears, `↑`/`↓` walk the
      history, `Ctrl+C` copies the result
- [x] Keypad with Basic / Scientific / Programmer modes, insert-at-cursor,
      `AC` / `DEL` / `±`, hex digits that open a `0x` literal
- [x] Programmer four-base readout (HEX/DEC/OCT/BIN), click to copy
- [x] History drawer, persisted, deduplicated, click to recall, clear
- [x] Memory register (display only so far — see v0.2), `ans` chaining after `=`
- [x] Settings sheet: precision, angle, grouping, keypad, live result,
      always-on-top; all persisted
- [x] pywal palette, Symbols Nerd Font chrome, v09 suite icon (`calc` glyph)
- [x] CLI: `hyprtk-calc "2+2*3"`, `-p/--precision`, `-a/--angle`, `-b/--base`,
      `-g/--grouping`, `--all-bases`, `--json`, `--history`, stdin, exit status
- [x] Installer with `--system` (ISO) and `--uninstall`; desktop entry with an
      absolute `Exec=`/`Icon=`; PyPI-venv fallback for Debian/Ubuntu PySide6
- [x] 60 unit tests, `qmllint`, headless boot check, installer round-trip

Not in v0.1.0, and deliberately: keys for the memory register, units, variables
in the UI, an input-base toggle, plotting, complex numbers.

## v0.2 — memory and variables in the UI

- [x] `MC / MR / M+ / M− / MS` row above the keypad (the Bridge already has
      `memory()`; the keys and a state badge are missing)
- [x] `ans` shown as a clickable token — 0.1.2
- [ ] `x` variables stored in settings (needs an environment in the parser)
- [x] Expression editing: select-all, cut, undo in the entry field — 0.1.2
- [x] Copy-all-as-text (`Ctrl+Shift+C`); paste is the field's native Ctrl+V — 0.1.2
- [ ] `Shift+Enter` to insert a newline-free continuation? (decide: probably no)

## v0.3 — units and a manual currency table

- [ ] Unit table (length, mass, volume, temperature, time, data, angle) with
      conversion via `to`/`in` (`5 km in mi`), unit-carrying quantities
- [ ] Constants panel (c, g, h, N_A, …) insertable from the keypad
- [ ] Manual currency rate table in settings (no network, no scraper)
- [ ] Significant-figures mode (as opposed to decimal places)

## v0.4 — paper mode and programmer input

- [ ] Paper/tape view for a running chain of calculations (galculator's idea)
- [ ] Input base follows the selected base (with the print/format rules that
      make it safe), and a bit-field view for 8/16/32/64-bit widths
- [ ] Financial mode (interest, PV/FV, depreciation) — only if it earns a tab
- [ ] Fraction mode (`Fraction` exact display beside the decimal)

## Suite integration — the release order

Steps 1–7 are **done** (2026-11-18); step 8 is the publish, which needs an
explicit go. `hyprtk-merged` is a source tree, not a destination.

- [x] **1. Repo + first tag.** `git init`, push `hyprtk/hyprtk-calc` on `main`,
      tag `v0.1.0`, topics set.
- [x] **2. Vendor into merged.** `hyprtk-merged/installer/hyprtk-calc/`
      (payload only: no tests, scripts, PLAN or RESEARCH).
- [x] **3. `1-install.sh` step** after hyprtk-term.
- [x] **4. Keybinding** `Super + N` and `XF86Calculator`.
- [x] **5. Window rule** float, centered, 480x740.
- [x] **6. Docs in merged** (`README.md`, `cheatsheet.md`, suite `CHANGELOG`).
- [x] **7. ISO**: system install, first-run fallback, `~/.local/bin` link.
- [ ] **8. `push-all`**: gate (T1 matrix, T2 dry-run, audit at zero TODO), suite
      `CHANGELOG` + tag, merged → dotfiles + live, then reinstall the
      calculator from the live tree.

Optional, not done:

- **Bar quick link / launcher item.** A `calc` entry in
  `hyprtk-bar-qt/config.json` (quicklinks and the arc launcher). It only reaches
  fresh installs — the bar seeds `~/.config` once — so it needs a bar version
  bump and a re-vendor to be worth doing, and `Super + N` already covers the
  daily case.
- **Keypad memory keys** (v0.2), units (v0.3).

### The exact edits, for a future port

`hyprtk-merged/1-install.sh`, after the hyprtk-term block:

```sh
_step "Installing hyprtk-calc"
_spin "Installing hyprtk-calc..." "bash $SCRIPT_DIR/installer/hyprtk-calc/install.sh" "$LOG_FILE"
_ok "hyprtk-calc installed (hyprtk-calc; GUI + shell calculator)"
```

`hypr/keybindings.lua` — `Super+N` is free, `Super+C` is hyprpicker:

```lua
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd("sh -c 'p=$HOME/.local/bin/hyprtk-calc; [ -x \"$p\" ] && exec \"$p\"'"))
hl.bind("XF86Calculator", hl.dsp.exec_cmd("sh -c 'p=$HOME/.local/bin/hyprtk-calc; [ -x \"$p\" ] && exec \"$p\"'"))
```

`hypr/windowrules.lua` — without it the window tiles across the work area
(verified: Hyprland ignores the 460x700 it asks for):

```lua
hl.window_rule({
    name = "windowrule-hyprtk-calc",
    match = { class = "hyprtk-calc" },
    float = true,
    center = true,
    size = "480 740",
})
```

The class is the desktop id (`setDesktopFileName`); a live run reports
`hyprtk-calc`, not `python3`. Saved sizes are clamped to 1200x1400 so a tiled
first run cannot become the persisted default.

The ISO touches two files: `customize_airootfs.sh` (a `--system` install beside
the other apps) and `hyprtk-first-run` (a `SYS_BIN` check, a per-user fallback
install and `hyprtk-calc` in the `~/.local/bin` link loop). `packages.hyprtk`
needs no change: PySide6 is already baked in.

## Gate

`./scripts/qa.sh` must stay green, and every check must be able to fail:

| Check | Catches |
|---|---|
| `unittest discover` | arithmetic, parser errors, formatting, history, settings, CLI, docs |
| `compileall` | syntax drift in Python |
| `qmllint` | QML syntax and unqualified-property typos |
| `bootcheck.py` | a QML load failure, a renamed slot, a binding loop, a key that stopped inserting |
| installer round-trip | a broken `--system`/`--uninstall` path or a stale desktop entry |
| CLI smoke | the `__main__` GUI/CLI dispatch |

## Open questions

- Percent semantics: keep `x/100`, or add GNOME's operand-relative rule for
  `+`/`−`? Leaning keep, and let the README be the contract.
- Should `=` replace the expression with its result on the *next* keypress
  (current behaviour: an operator continues from the result, a digit starts
  fresh)? Current behaviour matches GNOME.
- Units in v0.3 will decide whether `5 km` is a first-class quantity in the
  parser or a post-processing step on `to`/`in`.
