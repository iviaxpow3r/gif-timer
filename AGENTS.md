# AGENTS.md — gif-timer

## Project Overview

Python tool that generates animated countdown timer GIFs for use in slides/presentations.
Three interfaces share a single core library:

| File | Purpose |
|---|---|
| `timer_core.py` | Core library — all GIF generation logic lives here |
| `app.py` | Flask web UI at `http://localhost:5555` |
| `cli.py` | CLI interface |
| `streamlit_app.py` | Streamlit UI (deployable to share.streamlit.io) |
| `templates/` | Flask Jinja2 HTML templates |
| `generated/` | Default output directory for generated GIFs |

---

## Setup & Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask web UI
python app.py
# → http://localhost:5555

# Run Streamlit UI
streamlit run streamlit_app.py

# CLI usage
python cli.py --duration 60 --style digital --output timer.gif
python cli.py --duration 60 --negative 30 --style circular --output countdown.gif
python cli.py --duration 300 --style circular --bg transparent --ring-fg "#3B82F6" --output meeting.gif
python cli.py --duration 60 --infinite --style digital --fg "#00FF00" --output break.gif
python cli.py --list-fonts
```

## No Build/Test Commands

No test suite, no linter config, no type-checker config. This is a small greenfield project.
Apply modern Python best practices (see below) when adding code.

---

## Architecture

### Core Library: `timer_core.py`

All GIF generation flows through `generate_timer_gif()`. Surfaces (Flask, CLI, Streamlit)
are thin adapters that call this one function.

**Key functions:**
- `generate_timer_gif(duration, output_path, ...)` — main entry point, returns path
- `render_digital_frame(seconds, width, height, bg_color, fg_color, font_path, font_size)` → PIL Image
- `render_circular_frame(seconds, total_duration, ...)` → PIL Image
- `parse_color(color_value, allow_transparent=True)` → RGBA tuple
- `resolve_font(font_path, font_size)` → ImageFont
- `scan_system_fonts()` → `{display_name: path}` dict
- `format_time(seconds)` → `"MM:SS"` or `"-MM:SS"` string

**Timer styles:** `"digital"` (text only) | `"circular"` (depleting arc + centered text)

**Transparency:** Background can be `"transparent"` — triggers RGBA→P-mode conversion
with palette index 255 as the transparency key.

**Negative time:** `negative_duration=None` means infinite loop; `0` means no negative frames;
positive int means that many seconds past zero (with optional flashing effect).

---

## Code Style Guidelines

### Python Style
- **Python 3.10+** compatible syntax
- **4-space indentation** (no tabs)
- **Double quotes** for strings (consistent with existing code)
- **f-strings** for string formatting (used throughout)
- Line length: ~100 chars (no enforced limit, but keep readable)
- **No type annotations** in existing code — not required, but welcome on new public functions

### Imports
- Standard library first, then third-party (Pillow, Flask, Streamlit), then local (`timer_core`)
- No `from x import *`
- Avoid importing inside functions unless justified (see `cli.py` line 125 — `import os` inside `main()` is a minor exception to clean up if editing that file)

### Naming Conventions
- **Functions/variables:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `SYSTEM_FONT_DIRS`)
- **Private helpers:** prefix with `_` (e.g., `_find_font_by_name`, `_auto_font_size`)
- **No classes** in this codebase — flat function style throughout

### Docstrings
- Module-level docstring on every file (one-liner description + run instructions)
- Function docstrings on all public functions: one-line summary, then Args/Returns if non-trivial
- Section headers using `# --- Section Name ---` comments (matches existing style)

### Error Handling
- Raise `ValueError` for invalid inputs (e.g., `"No frames generated"`)
- Use `parser.error()` in CLI for user-facing argument errors
- Fall back gracefully on font resolution (`ImageFont.load_default()` as last resort)
- No bare `except:` — always catch specific exceptions

### Color Handling
- **All colors go through `parse_color()`** — never manipulate raw color strings directly
- Colors are stored/passed as strings (`"#RRGGBB"`, `"transparent"`, named colors)
- Internal representation after `parse_color()` is always RGBA tuple `(R, G, B, A)`

---

## Key Constraints

1. **`timer_core.py` has no UI dependencies** — keep it pure (Pillow + stdlib only). All Flask/Streamlit imports stay in their respective surface files.

2. **GIF loop behavior:** `loop=0` = infinite loop, `loop=1` = play once. Set based on `is_infinite` flag from `negative_duration is None`.

3. **Transparent GIFs** require P-mode with explicit transparency index. The current approach (palette index 255 as transparent) is intentional — don't simplify it without testing.

4. **Font sizing** uses `_auto_font_size()` with `format_time(0)` (`"0:00"`) as the baseline sample so all frames use consistent sizing regardless of digit count.

5. **Flask port is 5555** (not the default 5000) — don't change without updating `app.py` print statement and any docs.

---

## Adding New Features

### New timer style
1. Add a `render_<style>_frame()` function in `timer_core.py`
2. Add the style name to the `if/elif` block in `generate_timer_gif()`
3. Add it to CLI `--style choices` in `cli.py`
4. Add it to Streamlit radio options in `streamlit_app.py`
5. Add it to Flask form/JS in `templates/`

### New color parameter
1. Add parameter to `generate_timer_gif()` with a sensible default
2. Pass through to the relevant `render_*_frame()` call
3. Wire up in all three surfaces (Flask `api_generate`, CLI args, Streamlit widgets)
