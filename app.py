#!/usr/bin/env python3
"""
GIF Timer Generator - Web UI
Run: python app.py
Then open http://localhost:5555
"""

import io
import os
import tempfile
from PIL import Image, ImageDraw
from flask import Flask, render_template, request, send_file, jsonify
from timer_core import generate_timer_gif, scan_system_fonts, resolve_font

app = Flask(__name__)


@app.route("/")
def index():
    fonts = scan_system_fonts()
    return render_template("index.html", fonts=fonts)


@app.route("/api/fonts")
def api_fonts():
    return jsonify(scan_system_fonts())


@app.route("/font-preview")
def font_preview():
    font_path = request.args.get("font") or None
    try:
        preview_font = resolve_font(font_path, 36)
        img = Image.new("RGBA", (300, 60), (30, 30, 30, 255))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "AaBbCc 1:23", font=preview_font, fill=(255, 255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png")
    except Exception:
        img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json

    duration = int(data.get("duration", 60))
    style = data.get("style", "digital")
    default_width = 480 if style == "digital" else 400
    default_height = 120 if style == "digital" else 400
    width = int(data.get("width", default_width))
    height = int(data.get("height", default_height))
    fps = int(data.get("fps", 1))

    # Negative time
    go_negative = data.get("go_negative", False)
    infinite = data.get("infinite", False)
    if go_negative:
        negative_duration = int(data.get("negative_duration", 10))
    else:
        negative_duration = 0

    # Colors
    bg_color = data.get("bg_color", "#000000")
    if data.get("bg_transparent", False):
        bg_color = "transparent"
    fg_color = data.get("fg_color", "#FFFFFF")
    negative_color = data.get("negative_color", "#FF3333")
    ring_bg_color = data.get("ring_bg_color", "#333333")
    ring_fg_color = data.get("ring_fg_color", "#00CC66")
    flash_on_negative = data.get("flash_on_negative", True)
    flash_color = data.get("flash_color", "transparent")
    if data.get("flash_transparent", True):
        flash_color = "transparent"

    # New features
    auto_trim = data.get("auto_trim", False)
    warning_at = data.get("warning_at") or None
    warning_fg_color = data.get("warning_fg_color") or None
    warning_ring_color = data.get("warning_ring_color") or None
    critical_at = data.get("critical_at") or None
    critical_fg_color = data.get("critical_fg_color") or None
    critical_ring_color = data.get("critical_ring_color") or None
    flash_ring_on_negative = data.get("flash_ring_on_negative", True)
    ring_flash_color = data.get("ring_flash_color") or None

    # Font
    font_path = data.get("font_path") or None
    font_size = data.get("font_size")
    if font_size:
        font_size = int(font_size)
    else:
        font_size = None

    # Generate to temp file
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
        tmp_path = tmp.name

    generate_timer_gif(
        duration=duration,
        output_path=tmp_path,
        negative_duration=negative_duration,
        style=style,
        width=width,
        height=height,
        fps=fps,
        bg_color=bg_color,
        fg_color=fg_color,
        negative_color=negative_color,
        ring_bg_color=ring_bg_color,
        ring_fg_color=ring_fg_color,
        flash_on_negative=flash_on_negative,
        flash_color=flash_color,
        font_path=font_path,
        font_size=font_size,
        auto_trim=auto_trim,
        warning_at=warning_at,
        warning_fg_color=warning_fg_color,
        warning_ring_color=warning_ring_color,
        critical_at=critical_at,
        critical_fg_color=critical_fg_color,
        critical_ring_color=critical_ring_color,
        flash_ring_on_negative=flash_ring_on_negative,
        ring_flash_color=ring_flash_color,
        loop=infinite,
    )

    return send_file(
        tmp_path,
        mimetype="image/gif",
        as_attachment=False,
        download_name=f"timer_{duration}s_{style}.gif",
    )


if __name__ == "__main__":
    print("GIF Timer Generator running at http://localhost:5555")
    app.run(host="0.0.0.0", port=5555, debug=True)
