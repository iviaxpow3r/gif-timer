#!/usr/bin/env python3
"""
GIF Timer Generator - CLI
Usage: python cli.py --duration 60 --style digital --output timer.gif
"""

import argparse
import sys
from timer_core import generate_timer_gif, scan_system_fonts


def main():
    parser = argparse.ArgumentParser(
        description="Generate countdown timer GIFs for slides",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --duration 120 --output timer.gif
  %(prog)s --duration 60 --negative 30 --style circular --output countdown.gif
  %(prog)s --duration 60 --infinite --style digital --fg "#00FF00" --bg "#000" --output break.gif
  %(prog)s --duration 300 --style circular --bg transparent --ring-fg "#3B82F6" --output meeting.gif
  %(prog)s --list-fonts
        """,
    )

    parser.add_argument(
        "--duration",
        type=int,
        help="Countdown duration in seconds",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="timer.gif",
        help="Output file path (default: timer.gif)",
    )
    parser.add_argument(
        "--style",
        choices=["digital", "circular"],
        default="digital",
        help="Visual style (default: digital)",
    )
    parser.add_argument(
        "--negative",
        type=int,
        default=0,
        help="Seconds to count past zero (default: 0, no negative)",
    )
    parser.add_argument(
        "--infinite",
        action="store_true",
        help="Count negative indefinitely (GIF loops forever)",
    )
    parser.add_argument(
        "--size",
        type=str,
        default="400x400",
        help="Output size as WIDTHxHEIGHT (default: 400x400)",
    )
    parser.add_argument("--fps", type=int, default=1, help="Frames per second (default: 1)")

    # Colors
    parser.add_argument("--bg", type=str, default="#000000", help="Background color (hex, name, or 'transparent')")
    parser.add_argument("--fg", type=str, default="#FFFFFF", help="Foreground/text color")
    parser.add_argument("--negative-color", type=str, default="#FF3333", help="Color when timer is negative")
    parser.add_argument("--ring-bg", type=str, default="#333333", help="Circular: depleted ring color")
    parser.add_argument("--ring-fg", type=str, default="#00CC66", help="Circular: remaining ring color")
    parser.add_argument("--no-flash", action="store_true", help="Disable flashing when negative")
    parser.add_argument("--flash-color", type=str, default="transparent", help="Flash alternate color")

    # Font
    parser.add_argument("--font", type=str, default=None, help="Font path or name")
    parser.add_argument("--font-size", type=int, default=None, help="Font size (auto if not set)")

    # Utility
    parser.add_argument("--list-fonts", action="store_true", help="List available system fonts and exit")

    args = parser.parse_args()

    if args.list_fonts:
        fonts = scan_system_fonts()
        print(f"Found {len(fonts)} fonts:\n")
        for name, path in fonts.items():
            print(f"  {name:40s} {path}")
        return

    if args.duration is None:
        parser.error("--duration is required")

    # Parse size
    try:
        w, h = args.size.lower().split("x")
        width, height = int(w), int(h)
    except ValueError:
        parser.error(f"Invalid size format: {args.size}. Use WIDTHxHEIGHT (e.g., 400x400)")

    negative_duration = None if args.infinite else args.negative

    print(f"Generating {args.style} timer: {args.duration}s countdown", end="")
    if args.infinite:
        print(" + infinite negative", end="")
    elif args.negative > 0:
        print(f" + {args.negative}s negative", end="")
    print(f" → {args.output}")

    output = generate_timer_gif(
        duration=args.duration,
        output_path=args.output,
        negative_duration=negative_duration,
        style=args.style,
        width=width,
        height=height,
        fps=args.fps,
        bg_color=args.bg,
        fg_color=args.fg,
        negative_color=args.negative_color,
        ring_bg_color=args.ring_bg,
        ring_fg_color=args.ring_fg,
        flash_on_negative=not args.no_flash,
        flash_color=args.flash_color,
        font_path=args.font,
        font_size=args.font_size,
    )

    import os
    size_kb = os.path.getsize(output) / 1024
    print(f"Done! Saved to {output} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
