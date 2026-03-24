"""
GIF Timer Generator - Streamlit App
Run: streamlit run streamlit_app.py
Deploy: push to GitHub, connect at share.streamlit.io
"""

import base64
import io
import json
import math
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageSequence
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
    negative_ring_color = None
    negative_color = "#FF3333"
    flash_color = "transparent"

    if go_negative:
        negative_duration = int(
            st.number_input("Seconds past zero", min_value=1, max_value=300, value=10)
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

    # Base colors
    st.markdown("**Base colors**")
    c1, c2, c3, c4 = st.columns(4)
    fg_transparent = c2.checkbox("Transparent foreground")
    bg_transparent = c4.checkbox("Transparent background")
    if fg_transparent:
        c1.color_picker(
            "Text / foreground", "#FFFFFF", disabled=True, key="fg_disabled"
        )
        fg_color = "transparent"
    else:
        fg_color = c1.color_picker("Text / foreground", "#FFFFFF")
    if bg_transparent:
        c3.color_picker("Background", "#000000", disabled=True, key="bg_disabled")
        bg_color = "transparent"
    else:
        bg_color = c3.color_picker("Background", "#000000")

    if style == "circular":
        st.markdown("**Ring colors**")
        r1, r2, r3, r4 = st.columns(4)
        ring_fg_transparent = r2.checkbox("Transparent remaining ring")
        ring_bg_transparent = r4.checkbox("Transparent depleted ring")
        if ring_fg_transparent:
            r1.color_picker(
                "Remaining ring", "#00CC66", disabled=True, key="ring_fg_disabled"
            )
            ring_fg_color = "transparent"
        else:
            ring_fg_color = r1.color_picker("Remaining ring", "#00CC66")
        if ring_bg_transparent:
            r3.color_picker(
                "Depleted ring", "#333333", disabled=True, key="ring_bg_disabled"
            )
            ring_bg_color = "transparent"
        else:
            ring_bg_color = r3.color_picker("Depleted ring", "#333333")
    else:
        ring_fg_color = "#00CC66"
        ring_bg_color = "#333333"

    # --- Color Transitions ---
    with st.expander("Color Transitions"):
        # Compute percentage-based defaults: warning ~33%, critical ~10%
        default_warning = max(1, math.ceil(duration * 0.33)) if duration > 0 else 0
        default_critical = max(1, math.ceil(duration * 0.10)) if duration > 0 else 0

        warning_fg_color = None
        warning_ring_color = None
        critical_fg_color = None
        critical_ring_color = None

        warn_col, crit_col = st.columns(2)

        with warn_col:
            enable_warning = st.checkbox("Enable warning transition", value=True)
            warning_at = st.number_input(
                "Warning threshold (seconds)",
                min_value=0,
                max_value=duration if duration > 0 else 1,
                value=default_warning if enable_warning else 0,
                help="Seconds remaining when warning colors activate",
                disabled=not enable_warning,
            )
            if enable_warning and warning_at > 0:
                wfg, wring = st.columns(2)
                warning_fg_color = wfg.color_picker("Warning text", "#FFA500")
                warning_ring_color = wring.color_picker("Warning ring", "#FFA500")

        with crit_col:
            enable_critical = st.checkbox("Enable critical transition", value=True)
            critical_at = st.number_input(
                "Critical threshold (seconds)",
                min_value=0,
                max_value=duration if duration > 0 else 1,
                value=default_critical if enable_critical else 0,
                help="Seconds remaining when critical colors activate",
                disabled=not enable_critical,
            )
            if enable_critical and critical_at > 0:
                cfg, cring = st.columns(2)
                critical_fg_color = cfg.color_picker("Critical text", "#FF0000")
                critical_ring_color = cring.color_picker("Critical ring", "#FF0000")

        warning_at = warning_at if (enable_warning and warning_at > 0) else None
        critical_at = critical_at if (enable_critical and critical_at > 0) else None

    if go_negative:
        st.markdown("**Negative time**")
        flash_on_negative = st.checkbox("Flash when negative", value=True)

        st.markdown("**Negative text**")
        nt1, nt2, nt3, nt4 = st.columns(4)
        neg_transparent = nt2.checkbox("Transparent text (primary)")
        flash_transparent = nt4.checkbox("Transparent text (flash)", value=True)
        if neg_transparent:
            nt1.color_picker(
                "Text (primary)", "#FF3333", disabled=True, key="neg_disabled"
            )
            negative_color = "transparent"
        else:
            negative_color = nt1.color_picker("Text (primary)", "#FF3333")
        if flash_transparent:
            nt3.color_picker(
                "Text (flash)", "#000000", disabled=True, key="flash_disabled"
            )
            flash_color = "transparent"
        else:
            flash_color = nt3.color_picker("Text (flash)", "#000000")
        if flash_on_negative and not flash_transparent:
            if (negative_color or "").lower() == (flash_color or "").lower():
                st.warning(
                    "Text flash color matches primary text; flash may look static."
                )

        if style == "circular":
            st.markdown("**Negative ring**")
            flash_ring_on_negative = st.checkbox("Flash ring when negative", value=True)
            nr1, nr2, nr3, nr4 = st.columns(4)
            neg_ring_transparent = nr2.checkbox("Transparent ring (primary)")
            ring_flash_transparent = nr4.checkbox(
                "Transparent ring (flash)", value=True
            )
            if neg_ring_transparent:
                nr1.color_picker(
                    "Ring (primary)", "#FF3333", disabled=True, key="neg_ring_disabled"
                )
                negative_ring_color = "transparent"
            else:
                negative_ring_color = nr1.color_picker("Ring (primary)", "#FF3333")
            if not flash_ring_on_negative:
                nr3.color_picker(
                    "Ring (flash)",
                    "#000000",
                    disabled=True,
                    key="ring_flash_disabled",
                )
                ring_flash_color = None
            elif ring_flash_transparent:
                nr3.color_picker(
                    "Ring (flash)",
                    "#000000",
                    disabled=True,
                    key="ring_flash_disabled",
                )
                ring_flash_color = "transparent"
            else:
                ring_flash_color = nr3.color_picker("Ring (flash)", "#000000")
            if flash_ring_on_negative and not ring_flash_transparent:
                if (negative_ring_color or "").lower() == (
                    ring_flash_color or ""
                ).lower():
                    st.warning(
                        "Ring flash color matches primary ring; flash may look static."
                    )

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
                    negative_ring_color=negative_ring_color,
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
            expected_negative_frames = (
                negative_duration * (2 if flash_on_negative else 1)
                if go_negative
                else 0
            )
            expected_total_frames = duration + 1 + expected_negative_frames
            frames = list(ImageSequence.Iterator(Image.open(io.BytesIO(gif_bytes))))
            frame_count = len(frames)
            negative_diff_pixels = None
            last_negative_has_color = None
            last_negative_preview = None
            expected_last_label = None
            if frame_count > duration:
                canvas = Image.new("RGBA", frames[0].size, (0, 0, 0, 0))
                composited = []
                for f in frames:
                    disposal = f.info.get("disposal", 0)
                    rgba = f.convert("RGBA")
                    canvas = canvas.copy()
                    canvas.alpha_composite(rgba)
                    composited.append(canvas)
                    if disposal == 2:
                        canvas = Image.new("RGBA", frames[0].size, (0, 0, 0, 0))
                base_frame = composited[duration]
                last_frame = composited[-1]
                if go_negative and negative_duration > 0:
                    expected_last_label = (
                        f"-{negative_duration // 60}:{negative_duration % 60:02d}"
                    )
                    preview_buf = io.BytesIO()
                    last_frame.save(preview_buf, format="PNG")
                    last_negative_preview = preview_buf.getvalue()
                diff_count = 0
                for (r1, g1, b1, a1), (r2, g2, b2, a2) in zip(
                    base_frame.getdata(), last_frame.getdata()
                ):
                    if abs(r1 - r2) > 8 or abs(g1 - g2) > 8 or abs(b1 - b2) > 8:
                        diff_count += 1
                negative_diff_pixels = diff_count
                last_negative_has_color = False
                for r, g, b, a in last_frame.getdata():
                    if a == 0:
                        continue
                    if abs(r - 255) <= 12 and abs(g - 51) <= 12 and abs(b - 51) <= 12:
                        last_negative_has_color = True
                        break
            st.session_state["gif_settings"] = {
                "duration": duration,
                "go_negative": go_negative,
                "negative_duration": negative_duration,
                "style": style,
                "width": int(gif_width),
                "height": int(gif_height),
                "bg_color": "transparent" if bg_transparent else bg_color,
                "fg_color": fg_color,
                "negative_color": negative_color,
                "negative_ring_color": negative_ring_color,
                "ring_bg_color": ring_bg_color,
                "ring_fg_color": ring_fg_color,
                "flash_on_negative": flash_on_negative,
                "flash_color": flash_color,
                "font_path": font_path,
                "font_size": font_size,
                "auto_trim": auto_trim,
                "warning_at": warning_at,
                "warning_fg_color": warning_fg_color,
                "warning_ring_color": warning_ring_color,
                "critical_at": critical_at,
                "critical_fg_color": critical_fg_color,
                "critical_ring_color": critical_ring_color,
                "flash_ring_on_negative": flash_ring_on_negative,
                "ring_flash_color": ring_flash_color,
                "loop": infinite,
                "expected_frames": expected_total_frames,
                "actual_frames": frame_count,
                "negative_diff_pixels": negative_diff_pixels,
                "last_negative_has_color": last_negative_has_color,
                "expected_last_label": expected_last_label,
            }
            if last_negative_preview:
                st.session_state["last_negative_preview"] = last_negative_preview

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

        if "gif_settings" in st.session_state:
            with st.expander("Settings"):
                st.code(
                    json.dumps(st.session_state["gif_settings"], indent=2),
                    language="json",
                )
        if "last_negative_preview" in st.session_state:
            with st.expander("Verification"):
                st.caption(
                    f"Expected last label: {st.session_state['gif_settings'].get('expected_last_label')}"
                )
                st.image(
                    st.session_state["last_negative_preview"], caption="Last frame"
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
