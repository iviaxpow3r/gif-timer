import tempfile
import sys
from pathlib import Path
from PIL import Image, ImageSequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from timer_core import generate_timer_gif


def _load_frames(path):
    img = Image.open(path)
    raw_frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
    canvas = Image.new("RGBA", img.size, (0, 0, 0, 0))
    composited = []
    for frame in raw_frames:
        disposal = frame.info.get("disposal", 0)
        rgba = frame.convert("RGBA")
        canvas = canvas.copy()
        canvas.alpha_composite(rgba)
        composited.append(canvas)
        if disposal == 2:
            canvas = Image.new("RGBA", img.size, (0, 0, 0, 0))
    return composited


def _has_color(frame, target, tolerance=12, min_pixels=25):
    tr, tg, tb = target
    pixels = frame.getdata()
    count = 0
    for r, g, b, a in pixels:
        if a == 0:
            continue
        if (
            abs(r - tr) <= tolerance
            and abs(g - tg) <= tolerance
            and abs(b - tb) <= tolerance
        ):
            count += 1
            if count >= min_pixels:
                return True
    return False


def _run_negative_frame_presence_test():
    duration = 45
    negative_duration = 60
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
        output_path = tmp.name
    generate_timer_gif(
        duration=duration,
        output_path=output_path,
        negative_duration=negative_duration,
        style="circular",
        width=400,
        height=400,
        bg_color="transparent",
        fg_color="#000000",
        negative_color="#FF3333",
        ring_bg_color="transparent",
        ring_fg_color="#00CC66",
        flash_on_negative=True,
        flash_color="transparent",
        font_path=None,
        font_size=None,
        auto_trim=False,
        warning_at=15,
        warning_fg_color="#FFA500",
        warning_ring_color="#FFA500",
        critical_at=5,
        critical_fg_color="#FF0000",
        critical_ring_color="#FF0000",
        flash_ring_on_negative=True,
        ring_flash_color="#FF3333",
        loop=False,
    )
    frames = _load_frames(output_path)
    expected_total = (duration + 1) + (negative_duration * 2)
    assert len(frames) == expected_total, (
        f"Expected {expected_total} frames, got {len(frames)}"
    )
    negative_frames = frames[duration + 1 :]
    assert any(_has_color(f, (255, 51, 51)) for f in negative_frames), (
        "No negative-color frames found"
    )


def _run_ring_flash_color_test():
    duration = 6
    negative_duration = 2
    ring_flash_color = "#00FFFF"
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
        output_path = tmp.name
    generate_timer_gif(
        duration=duration,
        output_path=output_path,
        negative_duration=negative_duration,
        style="circular",
        width=240,
        height=240,
        bg_color="transparent",
        fg_color="#000000",
        negative_color="#FF3333",
        ring_bg_color="transparent",
        ring_fg_color="#00CC66",
        flash_on_negative=True,
        flash_color="transparent",
        font_path=None,
        font_size=None,
        auto_trim=False,
        warning_at=None,
        warning_fg_color=None,
        warning_ring_color=None,
        critical_at=None,
        critical_fg_color=None,
        critical_ring_color=None,
        flash_ring_on_negative=True,
        ring_flash_color=ring_flash_color,
        loop=False,
    )
    frames = _load_frames(output_path)
    negative_frames = frames[duration + 1 :]
    assert any(_has_color(f, (0, 255, 255)) for f in negative_frames), (
        "Ring flash color not found"
    )


def main():
    _run_negative_frame_presence_test()
    _run_ring_flash_color_test()
    print("All tests passed.")


if __name__ == "__main__":
    main()
