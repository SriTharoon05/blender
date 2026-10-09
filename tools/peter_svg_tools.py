"""Portable Peter contour selection for native editable 2D episode builders.

No bpy dependency: usable for SVG previews, cloud authoring, and Blender scene
generation. Image coordinates are x-right/y-down; scene builders own placement.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path


ASSET_RELATIVE = "00_LIBRARY/Characters/Peter_2D/Peter_2D_Paths_v001.json"
HEAD_GROUPS = frozenset({"ears", "face", "hair", "brows", "eyes", "nose", "mouth", "face_detail"})


@lru_cache(maxsize=4)
def load_peter(root: str | Path | None = None):
    """Read immutable source contours; use pose_paths() before editing a pose."""
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    return json.loads((root / ASSET_RELATIVE).read_text(encoding="utf-8"))


def pose_paths(*, mouth="rest", blink=False, include_body=True,
               gaze=(0., 0.), root: str | Path | None = None):
    """Return painter-ordered copied paths with a viseme, blink and small gaze.

    mouth: rest, smile, MBP, AA, EE, OH or FV. A head-only drawing excludes the
    hoodie and neck, so the supplied office body can replace the casual outfit.
    gaze is an image-space shift in pixels, clamped to +/- 7; it moves only iris
    and pupil paths, retaining eye whites and eyelid outlines.
    """
    source = load_peter(root)
    if mouth not in source["expressions"]["mouth"]:
        raise ValueError(f"Unsupported Peter viseme: {mouth}")
    paths = []
    inserted_mouth = inserted_eyes = False
    dx, dy = (max(-7., min(7., float(value))) for value in gaze)
    for original in source["paths"]:
        group = original["group"]
        if not include_body and group not in HEAD_GROUPS:
            continue
        if group == "mouth":
            if not inserted_mouth:
                paths.extend(deepcopy(source["expressions"]["mouth"][mouth]))
                inserted_mouth = True
            continue
        if blink and group == "eyes":
            if not inserted_eyes:
                paths.extend(deepcopy(source["expressions"]["eyes"]["blink"]))
                inserted_eyes = True
            continue
        record = deepcopy(original)
        if group == "eyes" and ("iris" in record["id"] or "pupil" in record["id"]):
            record["points"] = [[x + dx, y + dy] for x, y in record["points"]]
        paths.append(record)
    return paths


def linear_rgba(srgb):
    """Convert JSON sRGB RGBA into Blender material linear RGBA."""
    if srgb is None:
        return None
    return tuple(value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
                 for value in srgb[:3]) + (srgb[3],)


def map_points(record, *, image_anchor=(627., 495.), target=(0., 0.), scale=1.,
               y_up=True):
    """Map one contour; scale is scene units per reference image pixel."""
    direction = -1 if y_up else 1
    return [(target[0] + (x - image_anchor[0]) * scale,
             target[1] + direction * (y - image_anchor[1]) * scale)
            for x, y in record["points"]]
