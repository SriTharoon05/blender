"""Read Peter's current flat modular static-cutout source without bpy."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

ASSET_RELATIVE = "00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_Paths_v002.json"


@lru_cache(maxsize=4)
def load_flat_peter(root: str | Path | None = None):
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    return json.loads((root / ASSET_RELATIVE).read_text(encoding="utf-8"))


def part_paths(name, *, root: str | Path | None = None):
    return deepcopy(load_flat_peter(root)["parts"][name]["paths"])


def expression_paths(category, label, *, root: str | Path | None = None):
    return deepcopy(load_flat_peter(root)["expressions"][category][label])


def head_paths(*, mouth="rest", blink=False, root: str | Path | None = None):
    """Return a copied flat reference head for authoring, preserving paint order.

    Production should construct each expression mesh once and switch visibility.
    This selector never redraws a Blender frame or changes approved geometry.
    """
    source = load_flat_peter(root)
    output = []
    mouth_added = eye_added = False
    for record in source["parts"]["head"]["paths"]:
        if record["group"] == "mouth":
            if not mouth_added:
                output.extend(expression_paths("mouth", mouth, root=root))
                mouth_added = True
        elif blink and record["group"] == "eyes":
            if not eye_added:
                output.extend(expression_paths("eyes", "blink", root=root))
                eye_added = True
        else:
            output.append(deepcopy(record))
    return output
