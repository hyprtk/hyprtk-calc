# Research: desktop calculators, and what hyprtk-calc borrows

Survey done 2026-11-18, before the first line of the app. The question was not
"can we write a calculator" — it was "what do people actually use a desktop
calculator for, and which of the existing answers is worth copying, given the
suite already owns a palette, a font, an installer and a release chain".

## The field, 2026

| Calculator | Stack | Strength | What we took |
|---|---|---|---|
| **Qalculate! 5.13** | C++, libqalculate, GTK/Qt/CLI | 400+ functions and units, symbolic algebra, interval arithmetic, uncertainty, plotting, currency | The ambition, and the *shape*: one input line, live result, history, and `qalc` as a real CLI beside the GUI |
| **GNOME Calculator 51.1** | GTK4, Vala | Named modes (basic / advanced / financial / programming / conversion / keyboard), keyboard-first, correct through several decades | Mode tabs, the financial/programmer split, and `%` as a first-class key |
| **KCalc** | C++ / KDE Frameworks | Result stack, configurable precision, keypad that stays out of the way | The result *stack* (history as a sidebar), not a scrolling log |
| **SpeedCrunch 1.2** | C++ / Qt | 50 digits, 140+ functions, variables, units, complex numbers, matrices, history rewriting, keypad presets, 40 colour schemes | The single most important one: **the expression is the UI**. Type `sqrt 9`, tap digits, both work. Also per-result precision and a keypad that can be hidden |
| **galculator** | GTK | Paper mode, RPN | Paper mode is a good idea we are not doing yet (see PLAN v0.4) |
| **Extcalc / KAlgebra / KmPlot** | Qt / KDE | Plotting | No plotting in v0.1 — a graph needs axes, zoom and a compositor-sized canvas |
| **rpCalc / Sums / `bc` / `qalc`** | TUI / CLI | Scriptable, instant | A real CLI mode in the same binary (`hyprtk-calc "2+2"`, stdin, `--json`) |
| **Numbat / kalker / Rink** | Rust, CLI | Units and dimensional analysis | Units arrive in v0.2 with an offline table, not a network lookup |

Two conclusions shaped this app:

1. **The winner is decided by input, not features.** Every tool above can do
   `2+2`. What separates them is whether you can type the whole expression
   before seeing a result, whether the keyboard is the primary interface, and
   whether the number you got is the number you can trust. Those three are the
   product; everything else is a feature list.
2. **Nobody in this suite needs a second CAS.** Qalculate! exists, is packaged
   on every family the installer supports, and covers symbolic algebra and
   currency far past anything we would finish. hyprtk-calc should be the app
   that opens in 150 ms from a keybinding, is exact for ordinary arithmetic,
   looks like the rest of the desktop, and never gets in the way. When a
   calculation outgrows it, `qalc` is one `Super+Return` away.

## Decisions (and why)

| Decision | Rationale |
|---|---|
| **`decimal.Decimal`, not `float`** | `0.1 + 0.2` must be `0.3`, and money/percent arithmetic must not grow a `0.00000000000000004` tail. Measured: `0.1+0.2` → `0.3` here, `0.30000000000000004` with floats. |
| **A hand-written parser, not `ast` + `eval`** | `ast` parses literals as Python floats, which throws away the exactness before the calculation starts; `eval` is a security hole in any app that can paste. ~450 lines buys exact literals, implicit multiplication, `!`, `%`, `xor` and `<<` on our terms. |
| **Two precisions, not one** | Display precision is what the user asked for (12 by default). Working precision is `+12` guard digits. Without it, `sin(30°)` — which is `0.49999999999999994` in doubles — would display its own noise instead of `0.5`. |
| **Transcendentals through `math`, arithmetic through `Decimal`** | The stdlib has no Decimal `sin`. The honest consequence is documented: `1/3` is exact to every digit you ask for, `sin(x)` is good to ~15 digits and is then rounded to your display precision. Vendoring `mpmath` for the last three digits is not worth a dependency. |
| **`%` is a unit (`x/100`), not "percent of the left operand"** | `100 + 10%` = `100.1` here, like Qalculate! and SpeedCrunch. The "10% of 100 is 110" rule is a Windows-calculator convention that silently changes what `+` means depending on the right-hand token. Documented in the README instead of being guessed at. |
| **Base conversion is display-side** | The programmer readout shows HEX/OCT/DEC/BIN of the result; input is decimal or `0x`/`0b`/`0o` literals, like Python. Input-base-shifting calculators make `10` mean three different numbers depending on a toggle, which is exactly where such apps get their bug reports. |
| **History in JSONL, newest last** | Append-only: a crash mid-write loses one entry, never the file. The GUI and the CLI share it. |
| **PySide6 + Qt Quick/QML, not Quickshell** | A calculator is a focused window with a text input, not a shell surface. PySide6 6.12 is already installed for the suite's other apps, and QML gives the chrome the same visual language as bar-qt, the editor and the terminal. |
| **`QS_APP_ID`-equivalent via `setDesktopFileName`** | The suite rule: a toplevel must report its desktop id, or the bar's task list draws a generic icon. |
| **Same pywal palette resolver as the other apps** | One wallpaper change repaints the whole suite. The keypad's surface levels are derived by blending the background toward the foreground, because pywal can hand back a `color0` that is identical to `background` — keys would be invisible. |

## Numeric behaviour, measured

On this machine (Python 3.14.10, PySide6 6.12):

| Case | Result |
|---|---|
| `0.1 + 0.2` | `0.3` (float: `0.30000000000000004`) |
| `1/3` at 20 digits | `0.33333333333333333333` |
| `sin(30)` in degrees | `0.5` (raw double: `0.49999999999999994`) |
| `2^0.5` at 12 digits | `1.41421356237` |
| `2^3^2` | `512` (right associative) |
| `-2^2` | `-4` (unary binds looser than `^`) |
| `3!!` | `720` (`(3!)!`) |
| `1/0` | error "division by zero", not `Infinity` |
| one complex expression (`sin·log·sqrt·+−^`) | ~115 µs, parse + evaluate |
| `1/3` at 12 / 30 / 60 digits | ~11.5 µs, flat with precision |

That cost is invisible at typing speed, and a live result is re-evaluated on
every keystroke, so it matters: ~8,000 expressions/s against a 20 ms budget.

## What we deliberately do not build (yet)

- **Symbolic algebra, equation solving, integrals.** Qalculate! does it; a
  half-finished CAS is worse than a link to one.
- **Currency rates.** Requires a network call and a privacy decision; deferred
  to a *manual* rate table in v0.3 at the earliest.
- **Plotting.** Real work (axes, zoom, sampling, compositor-sized canvas) for a
  feature nobody needs on a keybinding calculator.
- **Complex numbers.** `Decimal` has no complex type; a complex mode means a
  second numeric stack, and `sqrt(-1)` should be an honest error until then.
- **Their own icon set.** The v09 suite badge exists; the calculator gets the
  `calc` glyph in `brand-kit/gen/brand.py` and nothing else.

## References

- Qalculate! — <https://qalculate.github.io/> (5.13, 2026-10-05)
- GNOME Calculator — <https://apps.gnome.org/Calculator/> (51.1, 2026-10-10)
- SpeedCrunch — <https://speedcrunch.org/> (1.2)
- KCalc handbook — <https://docs.kde.org/> (KDE Gear 2026)
- LinuxLinks, "Best Free and Open Source Linux Graphical Calculators" (2026-10)
- Python `decimal` module documentation (contexts, traps, significant digits)
