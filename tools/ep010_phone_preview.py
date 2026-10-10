"""Contact sheet of actual EP010 frames with a representative phone UI overlay.

This read-only review helper never changes source frames or the production
movie. The simulated UI is a conservative inspection aid, not a guarantee for
every device, app version or player state. Pillow is an optional cloud authoring
dependency declared in requirements-cloud.txt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOLUTION = (1080, 1920)
DEFAULT_FRAMES = (25, 65, 201, 302, 391, 461, 528)
SAFE_BANDS = {"title": (108, 300, 918, 480), "dialogue": (130, 1340, 870, 1470)}


def repo_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Review paths must stay inside the repository: {value}")
    return path


def font(size):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Compatibility with the oldest permitted Pillow 10 builds.
        return ImageFont.load_default()


def ui_overlay(image):
    from PIL import Image, ImageDraw
    ui = Image.new("RGBA", RESOLUTION, (0, 0, 0, 0))
    d = ImageDraw.Draw(ui)
    white = (255, 255, 255, 245)
    # Common status/cutout and upper navigation overlap, measured from top-left.
    d.rectangle((0, 0, 1080, 200), fill=(0, 0, 0, 35))
    d.text((80, 56), "9:20", font=font(39), fill=white)
    d.rounded_rectangle((365, 28, 710, 133), radius=51, fill=(0, 0, 0, 255))
    d.ellipse((593, 67, 609, 83), fill=(240, 159, 20, 255))
    for j in range(3):
        d.rounded_rectangle((817 + j * 12, 90 - j * 9, 824 + j * 12, 98), radius=2, fill=white)
    d.arc((869, 61, 924, 111), 218, 322, fill=white, width=6)
    d.arc((879, 75, 914, 103), 220, 320, fill=white, width=5)
    d.ellipse((894, 94, 899, 99), fill=white)
    d.rounded_rectangle((949, 62, 1020, 104), radius=9, outline=white, width=4)
    d.rectangle((1022, 75, 1027, 92), fill=white)
    d.text((961, 66), "87", font=font(27), fill=white)
    d.line(((80, 215), (56, 238), (80, 261)), fill=white, width=7)
    d.text((147, 211), "Shorts  /  Reels", font=font(37), fill=white)
    d.arc((981, 211, 1018, 246), 0, 360, fill=white, width=5)
    d.line(((1009, 242), (1028, 260)), fill=white, width=5)

    # The interaction column occupies the conservative right-side safe exclusion.
    d.rounded_rectangle((960, 980, 1080, 1570), radius=24, fill=(0, 0, 0, 42))
    cx = 1020
    for cy, label in ((1035, "Like"), (1180, "Reply"), (1325, "Save"), (1470, "Share")):
        if label == "Like":
            d.arc((cx - 36, cy - 34, cx + 4, cy + 5), 180, 350, fill=white, width=6)
            d.arc((cx - 4, cy - 34, cx + 36, cy + 5), 190, 360, fill=white, width=6)
            d.line(((cx - 35, cy - 10), (cx, cy + 30), (cx + 35, cy - 10)), fill=white, width=6)
        elif label == "Reply":
            d.rounded_rectangle((cx - 34, cy - 28, cx + 34, cy + 22), radius=12, outline=white, width=6)
            d.line(((cx - 14, cy + 21), (cx - 26, cy + 36), (cx + 3, cy + 22)), fill=white, width=5)
            d.line(((cx - 20, cy - 10), (cx + 20, cy - 10)), fill=white, width=4)
        elif label == "Save":
            d.line(((cx - 27, cy + 31), (cx - 27, cy - 28), (cx + 27, cy - 28),
                    (cx + 27, cy + 31), (cx, cy + 12), (cx - 27, cy + 31)), fill=white, width=6)
        else:
            d.line(((cx - 32, cy + 23), (cx - 8, cy - 1), (cx + 24, cy - 1)), fill=white, width=6)
            d.line(((cx + 7, cy - 22), (cx + 29, cy), (cx + 7, cy + 23)), fill=white, width=6)
        d.text((cx, cy + 48), label, font=font(22), anchor="mt", fill=white)

    # Author/subscription and bottom metadata model the provided screenshots.
    d.rectangle((0, 1530, 960, 1660), fill=(0, 0, 0, 100))
    d.ellipse((47, 1570, 115, 1638), fill=(236, 161, 97, 235), outline=white, width=3)
    d.text((135, 1579), "@dumbboypeter", font=font(35), fill=white)
    d.rounded_rectangle((638, 1569, 902, 1640), radius=33, fill=(255, 255, 255, 235))
    d.text((770, 1591), "Subscribe", font=font(29), anchor="mt", fill=(12, 12, 12, 255))
    d.rectangle((0, 1670, 1080, 1920), fill=(0, 0, 0, 135))
    d.text((52, 1698), "Episode caption / channel information", font=font(29), fill=white)
    d.text((52, 1763), "Original audio  |  @dumbboypeter", font=font(26), fill=white)
    d.line(((0, 1849), (1080, 1849)), fill=(255, 255, 255, 110), width=2)
    for x, label in ((128, "Home"), (380, "Shorts"), (640, "+"), (909, "You")):
        d.text((x, 1880), label, font=font(26), anchor="mm", fill=white)
    return Image.alpha_composite(image.convert("RGBA"), ui)


def make_contact(folder, frames, output, prefix="EP010_Review_", width=270,
                 columns=4, show_bands=False, include_plain=False):
    from PIL import Image, ImageDraw
    if not 180 <= width <= 1080:
        raise ValueError("Phone preview width must be 180..1080 px.")
    if not 1 <= columns <= 8:
        raise ValueError("Columns must be 1..8.")
    if not frames or any(f < 1 or f > 528 for f in frames):
        raise ValueError("Select actual EP010 frame numbers in 1..528.")
    if output.exists():
        raise FileExistsError(f"Protected review output already exists: {output.relative_to(ROOT)}")
    files = [(frame, folder / f"{prefix}{frame:04d}.png") for frame in frames]
    missing = [p.relative_to(ROOT).as_posix() for _, p in files if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing actual rendered/decoded frames: " + ", ".join(missing))
    height = round(width * 1920 / 1080)
    label_height = round(width * .15)
    variants = ("plain", "UI simulation") if include_plain else ("UI simulation",)
    tile_count = len(files) * len(variants)
    row_count = (tile_count + columns - 1) // columns
    sheet = Image.new("RGB", (columns * width, row_count * (height + label_height)), "#172029")
    d = ImageDraw.Draw(sheet)
    for i, (frame, path) in enumerate(files):
        with Image.open(path) as source:
            if source.size != RESOLUTION:
                raise ValueError(f"Expected full-resolution actual frame: {path.name}: {source.size}")
            raw = source.convert("RGBA")
        for v, variant in enumerate(variants):
            tile_index = i * len(variants) + v
            col, row = tile_index % columns, tile_index // columns
            x, y = col * width, row * (height + label_height)
            image = raw if variant == "plain" else ui_overlay(raw)
            thumb = image.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
            if show_bands:
                marks = ImageDraw.Draw(thumb)
                scale = width / 1080
                for box in SAFE_BANDS.values():
                    marks.rectangle(tuple(round(a * scale) for a in box), outline="#00e2eb", width=1)
            sheet.paste(thumb, (x, y + label_height))
            d.text((x + 7, y + 3), f"F{frame}  {(frame - 1) / 24:.2f}s  {variant}",
                   font=font(max(11, round(width * .045))), fill="#ffffff")
            d.text((x + 7, y + label_height // 2), "Actual frame / approximate app UI",
                   font=font(max(10, round(width * .039))), fill="#acbbc8")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return {"contact_sheet": output.relative_to(ROOT).as_posix(), "frames": list(frames),
            "phone_width_px": width, "source_resolution": list(RESOLUTION),
            "ui_simulation": "Representative conservative layout; device/app/playback UI may vary",
            "safe_bands_marked": show_bands, "production_frames_modified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", required=True, help="Repository-relative actual PNG frame directory")
    parser.add_argument("--frames", nargs="+", type=int, default=list(DEFAULT_FRAMES))
    parser.add_argument("--output", required=True, help="New repository-relative contact-sheet PNG")
    parser.add_argument("--prefix", default="EP010_Review_")
    parser.add_argument("--width", type=int, default=270)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--show-bands", action="store_true")
    parser.add_argument("--include-plain", action="store_true")
    args = parser.parse_args()
    result = make_contact(repo_path(args.folder), args.frames, repo_path(args.output),
                          args.prefix, args.width, args.columns, args.show_bands, args.include_plain)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
