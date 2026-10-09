"""Build v002 flat-color modular Peter SVG source; no raster images or bpy.

Preserves v001. Each body part is an independent static vector cutout with a
skeletal parent/pivot contract; expressions are reusable static head overlays.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
INK, SKIN, HAIR, BLUE = "#111827", "#FFC38A", "#6F3F25", "#327BFF"
spec = importlib.util.spec_from_file_location("peter_vector_source", HERE / "build_peter_vector.py")
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)


def rgba(color):
    return None if color is None else [round(int(color[a:a+2], 16)/255, 6) for a in (1,3,5)] + [1.]


def fresh(ident, group, d, fill, width=8, stroke=INK):
    record = {"id": ident, "group": group, "d": d, "fill": fill,
              "stroke": stroke, "stroke_width": width}
    points, closed = source.sample_path(d)
    record.update(points=points, closed=closed or fill is not None,
                  fill_rgba=rgba(fill), stroke_rgba=rgba(stroke))
    return record


def flat(record):
    item = deepcopy(record)
    item.update(source.contour(record))
    ident = item["id"]
    if item["group"] in {"face", "ears", "neck"} and item["fill"]:
        fill = SKIN
    elif "white" in ident or "teeth" in ident:
        fill = "#FFFFFF"
    elif "pupil" in ident or "mole" in ident:
        fill = INK
    elif "tongue" in ident:
        fill = "#FF6677"
    elif item["fill"]:
        fill = HAIR if item["group"] in {"hair", "brows", "eyes"} else INK
    else:
        fill = None
    item["fill"], item["fill_rgba"] = fill, rgba(fill)
    if item["stroke"]:
        item["stroke"], item["stroke_rgba"] = INK, rgba(INK)
        item["stroke_width"] = max(5., item["stroke_width"])
    if item["group"] in {"face", "ears", "hair"} and fill:
        item["stroke_width"] = 8.
    if item["group"] == "brows":
        item["stroke"], item["stroke_rgba"], item["stroke_width"] = INK, rgba(INK), 3.
    return item


head_ids = {"ear_left", "ear_left_inner", "ear_right", "ear_right_inner",
            "face_silhouette", "brow_left", "brow_right", "eye_left_white",
            "eye_left_iris", "eye_left_pupil", "eye_right_white", "eye_right_iris",
            "eye_right_pupil", "left_lid_fold", "right_lid_fold", "nose_bridge",
            "nostril_left", "nostril_right", "cheek_mole", "front_hair_silhouette"}
head = [flat(record) for record in source.PATHS if record["id"] in head_ids]
head.extend([fresh("hair_wisp_crown", "hair", "M500 95 Q576 59 650 75", None, 5),
             fresh("hair_wisp_left", "hair", "M399 184 Q439 117 521 89", None, 5),
             fresh("hair_wisp_mid", "hair", "M321 339 Q405 341 483 247", None, 5),
             fresh("hair_wisp_lower", "hair", "M296 469 Q357 484 399 433", None, 5),
             fresh("hair_wisp_right", "hair", "M760 103 Q780 155 735 210", None, 5),
             fresh("hair_wisp_side", "hair", "M792 229 Q843 229 881 285", None, 5)])
head.extend([flat(record) for record in source.EXPRESSIONS["mouth"]["rest"]])

parts = {
    "torso": {"pivot": [627, 865], "parent": "root", "paths": [fresh("hoodie_torso", "torso", "M478 827 Q625 795 777 827 L819 1405 Q626 1460 433 1405 Z", BLUE), fresh("hoodie_neck_opening", "torso", "M500 830 L623 918 L787 829", None, 8), fresh("hoodie_zipper", "torso", "M624 930 L624 1408", None, 5), fresh("hoodie_pocket", "torso", "M489 1194 L576 1160 L579 1317 L479 1317 Z", BLUE, 5), fresh("hoodie_pocket_right", "torso", "M682 1160 L769 1194 L779 1317 L681 1317 Z", BLUE, 5), fresh("hoodie_drawstring_left", "torso", "M574 886 L573 1072", None, 6, "#FFFFFF"), fresh("hoodie_drawstring_right", "torso", "M671 886 L672 1065", None, 6, "#FFFFFF")]},
    "neck": {"pivot": [627, 826], "parent": "torso", "paths": [fresh("neck", "neck", "M503 734 L786 733 L793 842 L627 918 L504 838 Z", SKIN)]},
    "upper_arm.L": {"pivot": [479, 862], "parent": "torso", "paths": [fresh("upper_arm_left", "upper_arm.L", "M476 824 Q429 817 395 863 L344 1097 Q388 1128 438 1120 L500 916 Z", BLUE)]},
    "lower_arm.L": {"pivot": [389, 1100], "parent": "upper_arm.L", "paths": [fresh("lower_arm_left", "lower_arm.L", "M345 1081 L433 1097 L432 1323 L346 1328 Z", BLUE)]},
    "hand.L": {"pivot": [389, 1317], "parent": "lower_arm.L", "paths": [fresh("hand_left", "hand.L", "M349 1310 L429 1310 L436 1375 Q440 1410 421 1439 L400 1440 L392 1407 L383 1445 L363 1444 L359 1404 L342 1430 L326 1413 L340 1369 Z", SKIN)]},
    "upper_arm.R": {"pivot": [776, 862], "parent": "torso", "paths": [fresh("upper_arm_right", "upper_arm.R", "M777 824 Q825 817 859 863 L910 1097 Q866 1128 816 1120 L754 916 Z", BLUE)]},
    "lower_arm.R": {"pivot": [865, 1100], "parent": "upper_arm.R", "paths": [fresh("lower_arm_right", "lower_arm.R", "M909 1081 L821 1097 L822 1323 L908 1328 Z", BLUE)]},
    "hand.R": {"pivot": [865, 1317], "parent": "lower_arm.R", "paths": [fresh("hand_right", "hand.R", "M905 1310 L825 1310 L818 1375 Q814 1410 833 1439 L854 1440 L862 1407 L871 1445 L891 1444 L895 1404 L912 1430 L928 1413 L914 1369 Z", SKIN)]},
    "upper_leg.L": {"pivot": [550, 1404], "parent": "torso", "paths": [fresh("upper_leg_left", "upper_leg.L", "M451 1374 L622 1393 L617 1722 L474 1722 Z", "#FFD23F")]},
    "lower_leg.L": {"pivot": [548, 1709], "parent": "upper_leg.L", "paths": [fresh("lower_leg_left", "lower_leg.L", "M475 1704 L618 1704 L603 2057 L474 2057 Z", "#FFD23F")]},
    "foot.L": {"pivot": [540, 2046], "parent": "lower_leg.L", "paths": [fresh("shoe_left", "foot.L", "M476 2034 L604 2034 L616 2120 L620 2162 L419 2162 Q409 2132 433 2108 Z", "#FFFFFF"), fresh("shoe_left_sole", "foot.L", "M418 2143 L618 2143", None, 6)]},
    "upper_leg.R": {"pivot": [704, 1404], "parent": "torso", "paths": [fresh("upper_leg_right", "upper_leg.R", "M632 1393 L803 1374 L780 1722 L637 1722 Z", "#FFD23F")]},
    "lower_leg.R": {"pivot": [706, 1709], "parent": "upper_leg.R", "paths": [fresh("lower_leg_right", "lower_leg.R", "M636 1704 L779 1704 L780 2057 L651 2057 Z", "#FFD23F")]},
    "foot.R": {"pivot": [714, 2046], "parent": "lower_leg.R", "paths": [fresh("shoe_right", "foot.R", "M650 2034 L778 2034 L821 2108 Q845 2132 835 2162 L634 2162 L638 2120 Z", "#FFFFFF"), fresh("shoe_right_sole", "foot.R", "M636 2143 L836 2143", None, 6)]},
    "head": {"pivot": [627, 740], "parent": "neck", "paths": head},
}
# The SVG uses painter's order; the declared hierarchy is consumed by the rig.
paint_order = ["upper_leg.L", "lower_leg.L", "foot.L", "upper_leg.R", "lower_leg.R", "foot.R", "upper_arm.L", "lower_arm.L", "hand.L", "upper_arm.R", "lower_arm.R", "hand.R", "torso", "neck", "head"]
expressions = {category: {label: [flat(record) for record in records]
                          for label, records in variants.items()}
               for category, variants in source.EXPRESSIONS.items()}


def write():
    manifest = {"schema_version": 2, "character": "Peter", "style": "flat cutout puppet; solid fills, crisp black outlines; no shading, texture or gradient", "view_box": [0,0,1254,2200], "head_reference_view_box": [0,0,1254,1254], "coordinates": "image-space x right y down; sRGB colors; all parts static vectors", "paint_order": paint_order, "root_pivot": [627,1404], "head_pivot": [627,740], "mouth_pivot": [670,651], "parts": parts, "expressions": expressions, "rig_policy": "Independent static part meshes parented to named skeletal bones; animate bone transforms and expression visibility, never redraw complete poses per frame."}
    (HERE / "Peter_2D_Flat_Puppet_Paths_v002.json").write_text(json.dumps(manifest,indent=2)+"\n", encoding="utf-8")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1254 2200" width="1254" height="2200">', '<title>Peter — flat modular cutout puppet v002</title>']
    for name in paint_order:
        part = parts[name]
        lines.append(f'<g id="part_{name}" data-parent="{part["parent"]}" data-pivot="{part["pivot"][0]},{part["pivot"][1]}">')
        for record in part["paths"]:
            lines.append(source.svg_path(record))
        lines.append('</g>')
    lines.append('</svg>')
    (HERE / "Peter_2D_Flat_Puppet_v002.svg").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(f"Created {len(parts)} modular cutouts; head has {len(head)} flat paths.")


if __name__ == "__main__":
    write()
