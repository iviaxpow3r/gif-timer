"""
Generate watermarked example GIFs for the Streamlit preview column.
Run: python3 generate_examples.py
"""

import io
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from timer_core import generate_timer_gif


def add_watermark(gif_path):
    """Add a diagonal 'EXAMPLE' watermark to all frames of a GIF."""
    # Open the GIF and extract frames
    gif = Image.open(gif_path)
    frames = []
    durations = []

    try:
        while True:
            # Copy frame and convert to RGBA for compositing
            frame = gif.copy()
            if frame.mode != "RGBA":
                frame = frame.convert("RGBA")

            # Create watermark layer
            width, height = frame.size
            watermark_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark_layer)

            # Try to load a nice font, fallback to default
            font = ImageFont.load_default()
            for font_path in [
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Arial.ttf",
            ]:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 52)
                    break

            # Draw "EXAMPLE" text
            text = "EXAMPLE"
            # Get text bbox for centering
            try:
                bbox = font.getbbox(text)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except Exception:
                # Fallback for default font
                text_width = len(text) * 30
                text_height = 40

            # Create rotated text
            # First create text on transparent background
            text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_layer)

            # Center the text
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            text_draw.text((x, y), text, fill=(255, 255, 255, 100), font=font)

            # Rotate the text 45 degrees
            rotated = text_layer.rotate(-45, expand=True)

            # Center the rotated text
            rw, rh = rotated.size
            offset_x = (width - rw) // 2
            offset_y = (height - rh) // 2

            # Composite onto watermark layer
            watermark_layer.paste(rotated, (offset_x, offset_y), rotated)

            # Composite watermark onto frame
            result = Image.alpha_composite(frame, watermark_layer)

            # Convert back to RGB for GIF saving
            rgb_frame = result.convert("RGB")

            # Quantize to palette mode
            pal_frame = rgb_frame.quantize(colors=255)

            frames.append(pal_frame)
            durations.append(gif.info.get("duration", 100))

            # Move to next frame
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass

    # Save the watermarked GIF
    # Get loop count from original
    loop = gif.info.get("loop", 0)

    output = io.BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=loop,
    )

    # Write back to original path
    with open(gif_path, "wb") as f:
        f.write(output.getvalue())


def main():
    # Create examples directory
    examples_dir = Path("examples")
    examples_dir.mkdir(exist_ok=True)

    # Generate digital example
    print("Generating digital example...")
    generate_timer_gif(
        duration=5,
        output_path="examples/digital_example.gif",
        style="digital",
        bg_color="#000000",
        fg_color="#ffffff",
        width=300,
        height=300,
        negative_duration=0,
    )
    add_watermark("examples/digital_example.gif")
    print("Generated examples/digital_example.gif")

    # Generate circular example
    print("Generating circular example...")
    generate_timer_gif(
        duration=5,
        output_path="examples/circular_example.gif",
        style="circular",
        bg_color="#000000",
        fg_color="#ffffff",
        width=300,
        height=300,
        negative_duration=0,
        ring_fg_color="#22c55e",
    )
    add_watermark("examples/circular_example.gif")
    print("Generated examples/circular_example.gif")


if __name__ == "__main__":
    main()
