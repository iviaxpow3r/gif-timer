"""
GIF Timer Generator - Core Library
Generates animated countdown timer GIFs for use in slides.
"""

import io
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageColor


# --- Font utilities ---

SYSTEM_FONT_DIRS = [
    "/System/Library/Fonts/",
    "/System/Library/Fonts/Supplemental/",
    "/Library/Fonts/",
    os.path.expanduser("~/Library/Fonts/"),
]


def scan_system_fonts():
    """Return dict of {display_name: path} for available .ttf/.otf/.ttc fonts."""
    fonts = {}
    for font_dir in SYSTEM_FONT_DIRS:
        if not os.path.isdir(font_dir):
            continue
        for fname in os.listdir(font_dir):
            if fname.lower().endswith((".ttf", ".otf", ".ttc")):
                display = os.path.splitext(fname)[0]
                fonts[display] = os.path.join(font_dir, fname)
    return dict(sorted(fonts.items()))


def resolve_font(font_path, font_size):
    """Resolve a font path/name to an ImageFont object."""
    if font_path is None:
        # Try common defaults
        for name in ["Helvetica", "Arial", "DejaVuSans"]:
            found = _find_font_by_name(name)
            if found:
                return ImageFont.truetype(found, font_size)
        return ImageFont.load_default()

    # Direct path
    if os.path.isfile(font_path):
        return ImageFont.truetype(font_path, font_size)

    # Search by name
    found = _find_font_by_name(font_path)
    if found:
        return ImageFont.truetype(found, font_size)

    return ImageFont.load_default()


def _find_font_by_name(name):
    """Search system font dirs for a font matching the given name."""
    name_lower = name.lower()
    for font_dir in SYSTEM_FONT_DIRS:
        if not os.path.isdir(font_dir):
            continue
        for fname in os.listdir(font_dir):
            if name_lower in fname.lower() and fname.lower().endswith(
                (".ttf", ".otf", ".ttc")
            ):
                return os.path.join(font_dir, fname)
    return None


# --- Color utilities ---


def _interpolate_color(c1, c2, t):
    """Linearly interpolate between two RGBA tuples at ratio t (0.0-1.0)."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))


def parse_color(color_value, allow_transparent=True):
    """Parse a color value into an RGBA tuple.

    Accepts:
      - "transparent" -> (0, 0, 0, 0)
      - "#RRGGBB" or "#RRGGBBAA" hex strings
      - (R, G, B) or (R, G, B, A) tuples
      - Named colors like "red", "white", etc.
    """
    if isinstance(color_value, str):
        if color_value.lower() == "transparent":
            if allow_transparent:
                return (0, 0, 0, 0)
            return (0, 0, 0, 255)
        try:
            rgb = ImageColor.getrgb(color_value)
            if len(rgb) == 3:
                return rgb + (255,)
            return rgb
        except ValueError:
            return (255, 255, 255, 255)

    if isinstance(color_value, (list, tuple)):
        if len(color_value) == 3:
            return tuple(color_value) + (255,)
        if len(color_value) == 4:
            return tuple(color_value)

    return (255, 255, 255, 255)


def is_transparent(color):
    """Check if a parsed color is fully transparent."""
    rgba = parse_color(color)
    return rgba[3] == 0


# --- Time formatting ---


def format_time(seconds):
    """Format seconds into MM:SS or -MM:SS display string."""
    negative = seconds < 0
    abs_sec = abs(seconds)
    mins = abs_sec // 60
    secs = abs_sec % 60
    prefix = "-" if negative else ""
    return f"{prefix}{mins}:{secs:02d}"


# --- Frame rendering ---


def _auto_font_size(text, width, height, font_path, max_h_ratio=0.4):
    """Find the largest font size that fits text within the given bounds.

    Args:
        text: Sample text to measure.
        width: Available width in pixels.
        height: Available height in pixels.
        font_path: Font to use.
        max_h_ratio: Maximum height as fraction of available height (default 0.4).
    """
    max_w = int(width * 0.8)
    max_h = int(height * max_h_ratio)
    size = 10
    best = 10
    while size < 500:
        font = resolve_font(font_path, size)
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw > max_w or th > max_h:
            break
        best = size
        size += 2
    return best


def render_digital_frame(
    seconds, width, height, bg_color, fg_color, font_path, font_size
):
    """Render a single digital-style timer frame."""
    bg = parse_color(bg_color)
    fg = parse_color(fg_color)

    img = Image.new("RGBA", (width, height), bg)

    draw = ImageDraw.Draw(img)
    text = format_time(seconds)

    if font_size is None:
        # Use a sample text to get consistent sizing across all frames
        sample = format_time(0)  # "0:00" as baseline
        font_size = _auto_font_size(sample, width, height, font_path)

    font = resolve_font(font_path, font_size)
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (width - tw) / 2 - bbox[0]
    y = (height - th) / 2 - bbox[1]
    draw.text((x, y), text, fill=fg, font=font)

    return img


def render_circular_frame(
    seconds,
    total_duration,
    width,
    height,
    bg_color,
    fg_color,
    ring_bg_color,
    ring_fg_color,
    font_path,
    font_size,
):
    """Render a single circular-style timer frame with a depleting arc."""
    bg = parse_color(bg_color)
    fg = parse_color(fg_color)
    ring_bg = parse_color(ring_bg_color)
    ring_fg = parse_color(ring_fg_color)

    img = Image.new("RGBA", (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Ring dimensions
    ring_width = max(int(min(width, height) * 0.08), 6)
    margin = int(min(width, height) * 0.08)
    bbox_ring = [margin, margin, width - margin, height - margin]

    # Draw background ring (full circle) - skip if fully transparent
    if ring_bg[3] > 0:
        draw.arc(bbox_ring, 0, 360, fill=ring_bg, width=ring_width)

    # Draw foreground arc (remaining time)
    if seconds > 0 and total_duration > 0:
        fraction = seconds / total_duration
        sweep = fraction * 360
        # Start from top (-90 degrees), go clockwise
        start_angle = -90
        end_angle = start_angle + sweep
        draw.arc(bbox_ring, start_angle, end_angle, fill=ring_fg, width=ring_width)
    elif seconds <= 0:
        # No remaining arc when negative
        pass

    # Draw time text in center
    text = format_time(seconds)
    if font_size is None:
        inner_size = min(width, height) - 2 * margin - 2 * ring_width
        sample = format_time(0)
        font_size = _auto_font_size(
            sample, inner_size, inner_size, font_path, max_h_ratio=0.3
        )

    font = resolve_font(font_path, font_size)
    bbox_text = font.getbbox(text)
    tw = bbox_text[2] - bbox_text[0]
    th = bbox_text[3] - bbox_text[1]
    x = (width - tw) / 2 - bbox_text[0]
    y = (height - th) / 2 - bbox_text[1]
    draw.text((x, y), text, fill=fg, font=font)

    return img


# --- GIF generation ---


def generate_timer_gif(
    duration,
    output_path,
    negative_duration=0,
    style="digital",
    width=None,
    height=None,
    fps=1,
    bg_color="#000000",
    fg_color="#FFFFFF",
    negative_color="#FF3333",
    ring_bg_color="#333333",
    ring_fg_color="#00CC66",
    flash_on_negative=True,
    flash_color="transparent",
    font_path=None,
    font_size=None,
    auto_trim=True,
    warning_at=None,
    warning_fg_color=None,
    warning_ring_color=None,
    critical_at=None,
    critical_fg_color=None,
    critical_ring_color=None,
    flash_ring_on_negative=True,
    ring_flash_color=None,
    loop=False,
):
    """Generate a countdown timer GIF.

    Args:
        duration: Countdown duration in seconds.
        output_path: Where to save the GIF.
        negative_duration: Seconds to count past zero. None = infinite loop.
        style: "digital" or "circular".
        width, height: Output dimensions.
        fps: Frames per second (1 = one frame per second).
        bg_color: Background color (hex, tuple, "transparent").
        fg_color: Text/ring color during countdown.
        negative_color: Text/ring color when past zero.
        ring_bg_color: Circular style depleted ring color.
        ring_fg_color: Circular style remaining ring color.
        flash_on_negative: Flash text when negative.
        flash_color: Alternate color during flash ("transparent" for blink effect).
        font_path: Path to font file or font name.
        font_size: Font size (None = auto).

    Returns:
        Path to the generated GIF.
    """
    # Resolve style-aware defaults for width/height
    if width is None:
        width = 480 if style == "digital" else 400
    if height is None:
        height = 120 if style == "digital" else 400

    frames = []
    frame_durations = []
    frame_ms = int(1000 / fps)

    is_infinite = (negative_duration is None) or loop

    # Calculate total frames
    # Count down from duration to 1, then show 0:00, then negative
    neg_frames = negative_duration if isinstance(negative_duration, int) else 0

    total_seconds = list(range(duration, -1, -1))  # duration down to 0
    if neg_frames > 0:
        total_seconds += list(range(-1, -(neg_frames + 1), -1))  # -1 to -neg

    transparent_bg = is_transparent(bg_color)

    # Pre-parse warning/critical colors if thresholds are set
    warning_fg = parse_color(warning_fg_color) if warning_fg_color else None
    warning_ring = parse_color(warning_ring_color) if warning_ring_color else None
    critical_fg = parse_color(critical_fg_color) if critical_fg_color else None
    critical_ring = parse_color(critical_ring_color) if critical_ring_color else None

    for sec in total_seconds:
        is_neg = sec < 0

        # Determine colors for this frame
        if is_neg and flash_on_negative:
            # Flash at 0.5s intervals: 2 sub-frames per negative second
            half_ms = frame_ms // 2
            if flash_ring_on_negative:
                sub_ring_alt = ring_flash_color if ring_flash_color else flash_color
            else:
                sub_ring_alt = ring_fg_color
            for sub_fg, sub_ring in [
                (flash_color, sub_ring_alt),
                (negative_color, negative_color),
            ]:
                if style == "circular":
                    frame = render_circular_frame(
                        seconds=sec,
                        total_duration=duration,
                        width=width,
                        height=height,
                        bg_color=bg_color,
                        fg_color=sub_fg,
                        ring_bg_color=ring_bg_color,
                        ring_fg_color=sub_ring,
                        font_path=font_path,
                        font_size=font_size,
                    )
                else:
                    frame = render_digital_frame(
                        seconds=sec,
                        width=width,
                        height=height,
                        bg_color=bg_color,
                        fg_color=sub_fg,
                        font_path=font_path,
                        font_size=font_size,
                    )
                frames.append(frame)
                frame_durations.append(half_ms)
            continue

        elif is_neg:
            current_fg = negative_color
            current_ring_fg = negative_color
        else:
            # Non-negative: apply warning/critical color transitions
            current_fg = fg_color
            current_ring_fg = ring_fg_color

            if (
                critical_at is not None
                and sec <= critical_at
                and critical_fg is not None
            ):
                current_fg = critical_fg_color
                if critical_ring is not None:
                    current_ring_fg = critical_ring_color
            elif (
                warning_at is not None and sec <= warning_at and warning_fg is not None
            ):
                current_fg = warning_fg_color
                if warning_ring is not None:
                    current_ring_fg = warning_ring_color

        if style == "circular":
            frame = render_circular_frame(
                seconds=sec,
                total_duration=duration,
                width=width,
                height=height,
                bg_color=bg_color,
                fg_color=current_fg,
                ring_bg_color=ring_bg_color,
                ring_fg_color=current_ring_fg,
                font_path=font_path,
                font_size=font_size,
            )
        else:
            frame = render_digital_frame(
                seconds=sec,
                width=width,
                height=height,
                bg_color=bg_color,
                fg_color=current_fg,
                font_path=font_path,
                font_size=font_size,
            )

        frames.append(frame)
        frame_durations.append(frame_ms)

    if not frames:
        raise ValueError("No frames generated")

    # Auto-trim: compute bounding box of non-transparent pixels across all frames
    if auto_trim and transparent_bg:
        bbox = None
        for f in frames:
            f_bbox = f.getbbox()
            if f_bbox:
                if bbox is None:
                    bbox = list(f_bbox)
                else:
                    bbox[0] = min(bbox[0], f_bbox[0])
                    bbox[1] = min(bbox[1], f_bbox[1])
                    bbox[2] = max(bbox[2], f_bbox[2])
                    bbox[3] = max(bbox[3], f_bbox[3])

        if bbox and bbox[2] > bbox[0] and bbox[3] > bbox[1]:
            frames = [f.crop(bbox) for f in frames]

    # Convert to mode suitable for GIF
    if transparent_bg:
        # For transparent GIFs we need P-mode with a designated transparent palette index.
        #
        # Why not index 255?
        #   quantize(colors=255) produces valid indices 0–254.  Writing index 255 via
        #   putdata() is out-of-range and causes Pillow's GIF encoder to misbehave
        #   (it remaps the palette and the transparency GCE no longer matches the pixels).
        #
        # Strategy: reserve index 0 for transparency.
        #   1. Quantize RGB content to 255 colors  → internal indices 0–254
        #   2. Prepend a transparent placeholder entry, shifting content to indices 1–255
        #   3. Map transparent pixels to index 0
        #   4. Save with transparency=0
        #   5. Read back the actual transparency index Pillow settled on (it may still
        #      remap during encoding) and patch the GIF Logical Screen Descriptor byte 11
        #      (background color index) so disposal=2 correctly restores transparency.
        gif_frames = []
        for f in frames:
            alpha = f.split()[3]

            # Quantize RGB to 255 content colors (yields pixel values 0–254)
            p_img = f.convert("RGB").quantize(colors=255)
            old_palette = (
                p_img.getpalette()
            )  # always 256 entries × 3 bytes = 768 values

            # New 256-entry palette: slot 0 = transparent placeholder (0,0,0),
            # slots 1–255 = the 255 original content colors shifted up by one.
            new_palette = [0, 0, 0] + old_palette[: 255 * 3]
            p_img.putpalette(new_palette)

            # Remap pixels: transparent areas → 0, content → original_index + 1
            p_data = list(p_img.getdata())
            a_data = list(alpha.getdata())
            p_img.putdata([0 if a <= 128 else p + 1 for p, a in zip(p_data, a_data)])

            gif_frames.append(p_img)

        buf = io.BytesIO()
        gif_frames[0].save(
            buf,
            format="GIF",
            save_all=True,
            append_images=gif_frames[1:],
            duration=frame_durations,
            loop=0 if is_infinite else 1,
            transparency=0,
            disposal=2,
        )
        gif_data = bytearray(buf.getvalue())

        # Pillow may remap palette indices during encoding; read back the transparency
        # index it actually wrote to the GCE, then patch LSD byte 11 to match so
        # disposal=2 restores to the correct (transparent) background color.
        saved_check = Image.open(io.BytesIO(bytes(gif_data)))
        actual_trans_idx = saved_check.info.get("transparency", 0)
        gif_data[11] = actual_trans_idx

        with open(output_path, "wb") as gif_out:
            gif_out.write(gif_data)
    else:
        # Non-transparent: simpler path
        rgb_frames = [f.convert("RGB") for f in frames]
        rgb_frames[0].save(
            output_path,
            save_all=True,
            append_images=rgb_frames[1:],
            duration=frame_durations,
            loop=0 if is_infinite else 1,
        )

    return output_path
