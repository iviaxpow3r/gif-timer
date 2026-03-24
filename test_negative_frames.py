"""
Tests for negative frame generation in GIF timer.
Run: python -m pytest test_negative_frames.py -v
"""

import os
import tempfile
import pytest
from PIL import Image
from timer_core import generate_timer_gif


def test_negative_frames_are_generated():
    """GIF with negative_duration=5 should have duration+1+(negative*2) frames with flash."""
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
        out = f.name
    try:
        generate_timer_gif(
            duration=3, output_path=out, negative_duration=5, style="digital"
        )
        im = Image.open(out)
        # 4 non-negative (3,2,1,0) + 10 flashed negative (5*2) = 14 frames
        assert im.n_frames == 14, f"Expected 14 frames, got {im.n_frames}"
    finally:
        os.unlink(out)


def test_no_negative_frames_when_zero():
    """GIF with negative_duration=0 should only have duration+1 frames."""
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
        out = f.name
    try:
        generate_timer_gif(
            duration=3, output_path=out, negative_duration=0, style="digital"
        )
        im = Image.open(out)
        assert im.n_frames == 4, f"Expected 4 frames, got {im.n_frames}"
    finally:
        os.unlink(out)


def test_negative_frames_no_flash():
    """negative_duration > 0 with flash disabled should produce duration+1+negative frames."""
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
        out = f.name
    try:
        generate_timer_gif(
            duration=2,
            output_path=out,
            negative_duration=3,
            flash_on_negative=False,
            style="digital",
        )
        im = Image.open(out)
        # 3 non-negative (2,1,0) + 3 negative = 6 frames
        assert im.n_frames == 6, f"Expected 6 frames (2+1+3), got {im.n_frames}"
    finally:
        os.unlink(out)


def test_circular_style_negative_frames():
    """Circular style should also generate correct negative frame count."""
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
        out = f.name
    try:
        generate_timer_gif(
            duration=2, output_path=out, negative_duration=3, style="circular"
        )
        im = Image.open(out)
        # 3 non-negative + 6 flashed negative = 9 frames
        assert im.n_frames == 9, f"Expected 9 frames, got {im.n_frames}"
    finally:
        os.unlink(out)


def test_negative_frames_contain_negative_text():
    """Negative frames should contain text with negative sign."""
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
        out = f.name
    try:
        generate_timer_gif(
            duration=1,
            output_path=out,
            negative_duration=2,
            style="digital",
            flash_on_negative=False,
        )
        im = Image.open(out)
        # 2 non-negative (1,0) + 2 negative = 4 frames
        assert im.n_frames == 4, f"Expected 4 frames, got {im.n_frames}"
        # Verify we can seek to negative frames without error
        im.seek(2)
        im.seek(3)
    finally:
        os.unlink(out)
