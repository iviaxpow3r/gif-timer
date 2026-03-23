"""
GIF Timer Generator - Streamlit App
Run: streamlit run streamlit_app.py
Deploy: push to GitHub, connect at share.streamlit.io
"""

import base64
import io
import tempfile
import streamlit as st
from timer_core import generate_timer_gif, scan_system_fonts

st.set_page_config(page_title="GIF Timer Generator", page_icon="⏱️", layout="wide")
st.title("⏱️ GIF Timer Generator")
st.caption("Build animated countdown timers for slides.")

col_controls, col_preview = st.columns([1, 1], gap="large")

with col_controls:

    # --- Duration ---
    st.subheader("Duration")
    c1, c2 = st.columns(2)
    minutes = c1.number_input("Minutes", min_value=0, max_value=60, value=1)
    seconds = c2.number_input("Seconds", min_value=0, max_value=59, value=0)
    duration = int(minutes) * 60 + int(seconds)

    # --- Style ---
    st.subheader("Style")
    style = st.radio("Timer style", ["Digital", "Circular"], horizontal=True).lower()

    # --- Negative time ---
    st.subheader("Negative Time")
    go_negative = st.checkbox("Continue counting past zero")
    negative_duration = 0
    flash_on_negative = True
    if go_negative:
        infinite = st.checkbox("Loop forever (GIF loops indefinitely)")
        if not infinite:
            negative_duration = st.number_input(
                "Seconds past zero", min_value=1, max_value=300, value=10
            )
        else:
            negative_duration = None
        flash_on_negative = st.checkbox("Flash when negative", value=True)

    # --- Colors ---
    st.subheader("Colors")
    cc1, cc2 = st.columns(2)
    bg_transparent = cc1.checkbox("Transparent background")
    bg_color = "#000000" if bg_transparent else cc1.color_picker("Background", "#000000")
    fg_color = cc2.color_picker("Text / foreground", "#FFFFFF")

    negative_color = st.color_picker("Negative text color", "#FF3333")

    flash_transparent = st.checkbox("Flash to transparent", value=True)
    flash_color = "transparent" if flash_transparent else st.color_picker("Flash alternate color", "#000000")

    if style == "circular":
        st.markdown("**Ring colors**")
        rc1, rc2 = st.columns(2)
        ring_fg_color = rc1.color_picker("Remaining ring", "#00CC66")
        ring_bg_color = rc2.color_picker("Depleted ring", "#333333")
    else:
        ring_fg_color = "#00CC66"
        ring_bg_color = "#333333"

    # --- Font & Size ---
    st.subheader("Font & Size")
    fonts = scan_system_fonts()
    font_options = ["Auto (system default)"] + list(fonts.keys())
    font_choice = st.selectbox("Font", font_options)
    font_path = None if font_choice == "Auto (system default)" else fonts[font_choice]

    font_size_input = st.number_input("Font size (0 = auto)", min_value=0, max_value=500, value=0)
    font_size = int(font_size_input) if font_size_input > 0 else None

    sc1, sc2 = st.columns(2)
    gif_width = sc1.number_input("Width (px)", min_value=100, max_value=2000, value=400)
    gif_height = sc2.number_input("Height (px)", min_value=100, max_value=2000, value=400)

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
                )

                with open(tmp_path, "rb") as f:
                    gif_bytes = f.read()

            # Render animated GIF via HTML so animation plays reliably
            b64 = base64.b64encode(gif_bytes).decode()
            bg_style = (
                "background: repeating-conic-gradient(#ccc 0% 25%, #fff 0% 50%) 0 0 / 20px 20px;"
                if bg_transparent
                else "background: #1a1a1a;"
            )
            st.markdown(
                f"""
                <div style="
                    {bg_style}
                    border-radius: 8px;
                    padding: 16px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 200px;
                ">
                    <img src="data:image/gif;base64,{b64}"
                         style="max-width: 100%; border-radius: 4px;">
                </div>
                """,
                unsafe_allow_html=True,
            )

            size_kb = len(gif_bytes) / 1024
            mins_d = duration // 60
            secs_d = duration % 60
            filename = f"timer_{mins_d}m{secs_d:02d}s_{style}.gif"

            st.download_button(
                label=f"Download GIF ({size_kb:.1f} KB)",
                data=gif_bytes,
                file_name=filename,
                mime="image/gif",
                use_container_width=True,
            )
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
                Configure your timer and click<br><strong>Generate Timer GIF</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
