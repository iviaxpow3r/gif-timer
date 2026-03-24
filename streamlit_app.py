"""
GIF Timer Generator - Streamlit App
Run: streamlit run streamlit_app.py
Deploy: push to GitHub, connect at share.streamlit.io
"""

import base64
import io
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
import streamlit as st
from timer_core import generate_timer_gif, scan_system_fonts, resolve_font

st.set_page_config(page_title="GIF Timer Generator", page_icon="⏱️", layout="wide")
st.title("⏱️ GIF Timer Generator")
st.caption("Build animated countdown timers for slides.")

col_controls, col_preview = st.columns([1, 1], gap="large")

with col_controls:
    # --- Style ---
    st.subheader("Style")
    style = st.radio("Timer style", ["Digital", "Circular"], horizontal=True).lower()

    # --- Duration ---
    st.subheader("Duration")
    c1, c2 = st.columns(2)
    minutes = c1.number_input("Minutes", min_value=0, max_value=60, value=1)
    seconds = c2.number_input("Seconds", min_value=0, max_value=59, value=0)
    duration = int(minutes) * 60 + int(seconds)
    infinite = st.checkbox("Loop")

    # --- Negative Time ---
    st.subheader("Negative Time")
    go_negative = st.checkbox("Continue counting past zero")
    negative_duration = 0
    flash_on_negative = True
    flash_ring_on_negative = True
    ring_flash_color = None
    negative_color = "#FF3333"
    flash_transparent = True
    flash_color = "transparent"

    if go_negative:
        negative_duration = st.number_input(
            "Seconds past zero", min_value=1, max_value=300, value=10
        )

        flash_on_negative = st.checkbox("Flash when negative", value=True)

        nc1, nc2 = st.columns(2)
        negative_color = nc1.color_picker("Negative text color", "#FF3333")

        flash_transparent = nc2.checkbox("Flash to transparent", value=True)
        flash_color = (
            "transparent"
            if flash_transparent
            else nc2.color_picker("Flash alternate color", "#000000")
        )

        if style == "circular" and flash_on_negative:
            flash_ring_on_negative = st.checkbox("Flash ring when negative", value=True)
            if flash_ring_on_negative:
                flash_ring_transparent = st.checkbox(
                    "Ring flash to transparent", value=True
                )
                ring_flash_color = (
                    "transparent"
                    if flash_ring_transparent
                    else st.color_picker("Ring flash color", "#000000")
                )

    # --- Size & Font ---
    st.subheader("Size & Font")
    sc1, sc2 = st.columns(2)
    default_w = 480 if style == "digital" else 400
    default_h = 120 if style == "digital" else 400
    gif_width = sc1.number_input(
        "Width (px)", min_value=100, max_value=2000, value=default_w
    )
    gif_height = sc2.number_input(
        "Height (px)", min_value=100, max_value=2000, value=default_h
    )
    gif_height = sc2.number_input(
        "Height (px)", min_value=100, max_value=2000, value=default_h
    )

    fonts = scan_system_fonts()
    font_options = ["Auto (system default)"] + list(fonts.keys())
    font_choice = st.selectbox("Font", font_options)
    font_path = None if font_choice == "Auto (system default)" else fonts[font_choice]

    if font_path is not None:
        try:
            preview_img = Image.new("RGBA", (300, 60), (30, 30, 30, 255))
            draw = ImageDraw.Draw(preview_img)
            preview_font = resolve_font(font_path, 36)
            draw.text(
                (10, 10), "AaBbCc 1:23", font=preview_font, fill=(255, 255, 255, 255)
            )
            preview_buf = io.BytesIO()
            preview_img.save(preview_buf, format="PNG")
            preview_buf.seek(0)
            st.image(preview_buf, width=300)
        except Exception:
            pass

    font_size_input = st.number_input(
        "Font size (0 = auto)", min_value=0, max_value=500, value=0
    )
    font_size = int(font_size_input) if font_size_input > 0 else None

    auto_trim = st.checkbox(
        "Auto-trim transparent pixels",
        help="Only applies when background is transparent",
    )

    # --- Colors ---
    st.subheader("Colors")
    cc1, cc2 = st.columns(2)
    fg_color = cc1.color_picker("Text / foreground", "#FFFFFF")

    bg_transparent = cc2.checkbox("Transparent background")
    bg_color = (
        "#000000" if bg_transparent else cc2.color_picker("Background", "#000000")
    )

    if style == "circular":
        st.markdown("**Ring colors**")
        rc1, rc2 = st.columns(2)
        ring_fg_color = rc1.color_picker("Remaining ring", "#00CC66")
        ring_bg_transparent = rc2.checkbox("Transparent depleted ring")
        ring_bg_color = (
            "transparent"
            if ring_bg_transparent
            else rc2.color_picker("Depleted ring", "#333333")
        )
    else:
        ring_fg_color = "#00CC66"
        ring_bg_color = "#333333"

    # --- Color Transitions ---
    with st.expander("Color Transitions"):
        ct1, ct2 = st.columns(2)
        warning_at = ct1.number_input(
            "Warning threshold (seconds)",
            min_value=0,
            max_value=duration,
            value=0,
            help="0 = disabled",
        )
        critical_at = ct2.number_input(
            "Critical threshold (seconds)",
            min_value=0,
            max_value=duration,
            value=0,
            help="0 = disabled",
        )

        warning_fg_color = None
        warning_ring_color = None
        critical_fg_color = None
        critical_ring_color = None

        if warning_at > 0:
            st.markdown("**Warning colors**")
            wfg, wring = st.columns(2)
            warning_fg_color = wfg.color_picker("Warning text", "#FFA500")
            warning_ring_color = wring.color_picker("Warning ring", "#FFA500")

        if critical_at > 0:
            st.markdown("**Critical colors**")
            cfg, cring = st.columns(2)
            critical_fg_color = cfg.color_picker("Critical text", "#FF0000")
            critical_ring_color = cring.color_picker("Critical ring", "#FF0000")

        warning_at = warning_at if warning_at > 0 else None
        critical_at = critical_at if critical_at > 0 else None

    # --- Generate ---
    st.write("")
    generate = st.button("Generate Timer GIF", type="primary", use_container_width=True)

with col_preview:
    st.subheader("Preview")

    if generate:
        if duration == 0 and not go_negative:
            st.error("Duration must be greater than 0.")
        else:
            with st.spinner("Generating..."):
                with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
                    tmp_path = tmp.name

                generate_timer_gif(
                    duration=duration,
                    output_path=tmp_path,
                    negative_duration=negative_duration,
                    style=style,
                    width=int(gif_width),
                    height=int(gif_height),
                    bg_color="transparent" if bg_transparent else bg_color,
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

                with open(tmp_path, "rb") as f:
                    gif_bytes = f.read()

            size_kb = len(gif_bytes) / 1024
            mins_d = duration // 60
            secs_d = duration % 60
            filename = f"timer_{mins_d}m{secs_d:02d}s_{style}.gif"

            # Persist in session_state so the preview survives widget re-renders.
            # st.button() returns True only on the single run after a click; any
            # subsequent widget interaction (toggling auto_trim, opening Color
            # Transitions, etc.) triggers a re-render where generate=False.
            # Without session_state the preview would silently disappear.
            st.session_state["gif_bytes"] = gif_bytes
            st.session_state["gif_bg_transparent"] = bg_transparent
            st.session_state["gif_filename"] = filename
            st.session_state["gif_size_kb"] = size_kb

    # Render from session_state — persists across all widget interactions
    if "gif_bytes" in st.session_state:
        _b64 = base64.b64encode(st.session_state["gif_bytes"]).decode()
        _bg_style = (
            "background: repeating-conic-gradient(#ccc 0% 25%, #fff 0% 50%) 0 0 / 20px 20px;"
            if st.session_state["gif_bg_transparent"]
            else "background: #1a1a1a;"
        )
        # Render animated GIF via HTML so animation plays reliably
        st.markdown(
            f"""
            <div style="
                {_bg_style}
                border-radius: 8px;
                padding: 16px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 200px;
            ">
                <img src="data:image/gif;base64,{_b64}"
                     style="max-width: 100%; border-radius: 4px;">
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            label=f"Download GIF ({st.session_state['gif_size_kb']:.1f} KB)",
            data=st.session_state["gif_bytes"],
            file_name=st.session_state["gif_filename"],
            mime="image/gif",
            use_container_width=True,
        )
    else:
        example_path = Path("examples") / f"{style}_example.gif"
        if example_path.exists():
            gif_bytes = example_path.read_bytes()
            b64 = base64.b64encode(gif_bytes).decode()
            st.markdown(
                f"""
                <div style="
                    background: #1e1e1e;
                    border-radius: 8px;
                    padding: 16px;
                    text-align: center;
                ">
                    <img src="data:image/gif;base64,{b64}"
                         style="max-width: 100%; border-radius: 4px;">
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Example preview — generate to see your settings applied")
        else:
            st.markdown(
                """
                <div style="
                    background: #1e1e1e;
                    border-radius: 8px;
                    padding: 60px 16px;
                    text-align: center;
                    color: #666;
                    font-size: 1.1em;
                ">
                    Generate to preview your timer with current settings
                </div>
                """,
                unsafe_allow_html=True,
            )
