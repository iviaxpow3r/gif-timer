# GIF Timer

Generate animated countdown timer GIFs for presentations, slides, and anywhere you need a self-contained visual timer.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Two visual styles** — digital (segmented display) or circular progress ring
- **Transparent backgrounds** — drop timers directly onto slides or images
- **Negative time support** — timer continues past zero with a configurable flash effect
- **Custom fonts & colors** — use any system font; full hex color control
- **Three interfaces** — Flask web UI, Streamlit app, or CLI
- **No dependencies beyond Pillow, Flask, and Streamlit**

## Installation

```bash
git clone https://github.com/iviaxpow3r/gif-timer.git
cd gif-timer
pip install -r requirements.txt
```

Python 3.10+ required.

## Usage

### Flask Web UI

```bash
python app.py
```

Open [http://localhost:5555](http://localhost:5555) in your browser. Configure your timer visually and download the generated GIF.

### Streamlit App

```bash
streamlit run streamlit_app.py
```

Or deploy to [share.streamlit.io](https://share.streamlit.io) by connecting your forked repo — no server required.

### CLI

```bash
python cli.py --duration 60 --output timer.gif
```

#### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--duration` | `60` | Timer length in seconds |
| `--output` | `timer.gif` | Output file path |
| `--style` | `digital` | Visual style: `digital` or `circular` |
| `--width` | `400` | Frame width in pixels |
| `--height` | `200` | Frame height in pixels |
| `--fps` | `10` | Frames per second |
| `--bg-color` | `#000000` | Background color (hex or `transparent`) |
| `--text-color` | `#ffffff` | Text/digit color (hex) |
| `--accent-color` | `#ff4444` | Accent color for circular ring or flash |
| `--font` | auto | Font name or path |
| `--font-size` | auto | Font size in points |
| `--negative-time` | `30` | Seconds to show after zero (0 to disable) |
| `--flash-interval` | `0.5` | Flash period in seconds for negative time |

#### Examples

```bash
# 5-minute presentation timer, transparent background
python cli.py --duration 300 --bg-color transparent --style circular --output talk.gif

# 30-second quiz timer with custom colors
python cli.py --duration 30 --text-color "#00ff88" --accent-color "#ff6600" --output quiz.gif

# Compact digital timer
python cli.py --duration 120 --width 300 --height 100 --style digital --output compact.gif
```

## API

The core logic lives in `timer_core.py` and exposes a single entry point:

```python
from timer_core import generate_timer_gif

gif_bytes = generate_timer_gif(
    duration=60,
    width=400,
    height=200,
    style="digital",         # "digital" | "circular"
    bg_color="transparent",
    text_color="#ffffff",
    accent_color="#ff4444",
    fps=10,
    negative_time=10,        # seconds past zero to show
    flash_interval=0.5,
)

with open("timer.gif", "wb") as f:
    f.write(gif_bytes)
```

All three UI surfaces (Flask, Streamlit, CLI) are thin adapters over this function.

## Deploying to Streamlit Cloud

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your fork, branch `main`, file `streamlit_app.py`
4. Deploy — no secrets or environment variables needed

## Requirements

- Python 3.10+
- [Pillow](https://pillow.readthedocs.io/) >= 10.0.0
- [Flask](https://flask.palletsprojects.com/) >= 3.0.0 *(web UI only)*
- [Streamlit](https://streamlit.io/) >= 1.30.0 *(Streamlit UI only)*

## License

MIT
