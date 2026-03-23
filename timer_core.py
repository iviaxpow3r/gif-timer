"""
GIF Timer Generator - Core Library
Generates animated countdown timer GIFs for use in slides.
"""

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


def _auto_font_size(text, width, height, font_path):
    """Find the largest font size that fits text within the given bounds."""
    max_w = int(width * 0.8)
    max_h = int(height * 0.4)
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
    use_alpha = bg[3] < 255

    if use_alpha:
        img = Image.new("RGBA", (width, height), bg)
    else:
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

    # Draw background ring (full circle)
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
        font_size = _auto_font_size(sample, inner_size, inner_size, font_path)

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
    width=400,
    height=400,
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
    frames = []
    frame_durations = []
    frame_ms = int(1000 / fps)

    is_infinite = negative_duration is None

    # Calculate total frames
    # Count down from duration to 1, then show 0:00, then negative
    if is_infinite:
        # For infinite, we generate a reasonable number of negative frames
        # that will loop. Use 60 seconds of negative as the loop content.
        neg_frames = 60
    else:
        neg_frames = negative_duration

    total_seconds = list(range(duration, -1, -1))  # duration down to 0
    if neg_frames > 0:
        total_seconds += list(range(-1, -(neg_frames + 1), -1))  # -1 to -neg

    transparent_bg = is_transparent(bg_color)

    for sec in total_seconds:
        is_neg = sec < 0

        # Determine colors for this frame
        if is_neg and flash_on_negative:
            # Alternate between negative_color and flash_color
            frame_idx = abs(sec)
            if frame_idx % 2 == 0:
                current_fg = negative_color
                current_ring_fg = negative_color
            else:
                current_fg = flash_color
                current_ring_fg = flash_color
        elif is_neg:
            current_fg = negative_color
            current_ring_fg = negative_color
        else:
            current_fg = fg_color
            current_ring_fg = ring_fg_color

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

    # Convert to mode suitable for GIF
    if transparent_bg:
        # For transparent GIFs, we need to handle alpha properly
        gif_frames = []
        for f in frames:
            # Convert RGBA to P mode with transparency
            alpha = f.split()[3]
            p_frame = f.convert("RGB").convert(
                "P", palette=Image.ADAPTIVE, colors=255
            )
            # Find the closest color to transparent and set as transparency
            mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
            p_frame.paste(255, mask)
            gif_frames.append(p_frame)

        gif_frames[0].save(
            output_path,
            save_all=True,
            append_images=gif_frames[1:],
            duration=frame_durations,
            loop=0 if is_infinite else 1,
            transparency=255,
            disposal=2,
        )
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
