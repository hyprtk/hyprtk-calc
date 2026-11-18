# hyprtk-calc — plan

Status: **v0.1.0 scaffolded 2026-11-18**, not published, not wired into
`hyprtk-merged`. The app runs (GUI + CLI), the gate is green, and the release
steps below are the remaining work.

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

- [ ] `MC / MR / M+ / M− / MS` row above the keypad (the Bridge already has
      `memory()`; the keys and a state badge are missing)
- [ ] `ans` shown as a clickable token, `x` variables stored in settings
- [ ] Expression editing: select-all, cut, undo in the entry field
- [ ] Copy-all-as-text (`Ctrl+Shift+C`) and paste-into-expression
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

Nothing here is done yet. `hyprtk-merged` is a source tree, not a destination:
do these in order, and only when a release is wanted.

1. **Repo + first tag.** `git init` in `~/Projects/AI-Projects/hyprtk-calc`,
   push `hyprtk/hyprtk-calc` on `main`, tag `v0.1.0`.
2. **Vendor into merged.** Copy (excluding `.git`, `spike/`, `venv/`,
   `__pycache__`) to `hyprtk-merged/installer/hyprtk-calc/`.
3. **`1-install.sh`** — add the install step after `hyprtk-term`:

   ```sh
   _spin "Installing hyprtk-calc..." "bash $SCRIPT_DIR/installer/hyprtk-calc/install.sh" "$LOG_FILE"
   _ok "hyprtk-calc installed (hyprtk-calc; GUI + shell calculator)"
   ```

   Note: `install.sh` may call `pip` only on the PySide6-missing fallback, so it
   is safe under `_spin`; no `sudo` anywhere in it.
4. **Keybinding** — `hypr/keybindings.lua`:

   ```lua
   hl.bind("XF86Calculator", hl.dsp.exec_cmd("sh -c 'p=$HOME/.local/bin/hyprtk-calc; [ -x \"$p\" ] && exec \"$p\""))
   hl.bind(mainMod .. " + N", hl.dsp.exec_cmd("sh -c 'p=$HOME/.local/bin/hyprtk-calc; [ -x \"$p\" ] && exec \"$p\""))
   ```

   `Super+N` is free; `Super+C` is hyprpicker, so it is not an option.
5. **Window rule** — `hypr/windowrules.lua`, or the app is tiled full-screen
   (verified on the live session: Hyprland ignores the window's own 460x700 and
   tiles it 1927x1046):

   ```lua
   hl.window_rule({
       name = "windowrule-hyprtk-calc",
       match = { class = "hyprtk-calc" },
       float = true,
       center = true,
       size = "480 740",
   })
   ```

   The class is the desktop id (`setDesktopFileName`), which the live run
   confirmed: `hyprctl clients` reports `hyprtk-calc`, not `python3`. Until this
   rule exists the window tiles and its size is clamped to 1200x1400 when saved,
   so a tiled first run cannot become the persisted default.

6. **Bar quick link + launcher item** — `installer/hyprtk-bar-qt/config.json`:
   a `calc` quicklink (`id: "calc"`, glyph `\uf1ec`, command `hyprtk-calc`) and a
   launcher item next to Terminal. Bar-qt is a shared repo, so the same change
   is made in `hyprtk-bar-qt/config.json` and re-vendored with
   `git archive HEAD`, not rsync.
7. **Docs** — `cheatsheet.md` (shortcut line), `README.md` (apps table, the
   "Terminal"-style feature row, keybinding table, apps list at the top,
   project table).
8. **ISO** — `installer/hyprtk-iso-creator/airootfs/root/customize_airootfs.sh`
   (system install beside the other apps), `airootfs/usr/local/bin/hyprtk-first-run`
   (the `SYS_BIN` check and the per-user fallback loop), `packages.hyprtk` only
   if a new dependency appears (none expected: PySide6 is already baked).
9. **`push-all`** — gate (T1 matrix, T2 dry-run, audit), suite `CHANGELOG` +
   tag, merged → dotfiles + live, then reinstall the bar (which does not carry
   the calculator) and the calculator itself.

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
