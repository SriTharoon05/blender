"""Create the standalone approved Peter native Grease Pencil collection.

Run in Blender 5.2 with --background --factory-startup --python this_file.py.
Build only: no scene rendering; the versioned asset refuses existing output.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from peter_svg_tools import linear_rgba, map_points, pose_paths

OUTPUT = ROOT / "00_LIBRARY/Characters/Peter_2D/Peter_2D_v001.blend"


def build():
    import bpy
    if OUTPUT.exists():
        raise FileExistsError(f"Protected asset already exists: {OUTPUT.name}")
    collection = bpy.data.collections.new("CHAR_Peter_2D")
    collection.asset_mark()
    collection.asset_data.description = "Peter: user-approved portrait; editable native vector Grease Pencil; neutral mouth."
    collection.asset_data.author = "SriTharoon05"
    collection["source_svg"] = "00_LIBRARY/Characters/Peter_2D/Peter_2D_v001.svg"
    collection["expression_contours"] = "00_LIBRARY/Characters/Peter_2D/Peter_2D_Paths_v001.json"
    collection["mouth_states"] = "rest, MBP, AA, EE, OH, FV, smile"
    collection["source_coordinates"] = "1254 x 1254; native drawing scale .01 world units per pixel"
    gp = bpy.data.grease_pencils.new("Peter_2D_Vector")
    gp.stroke_depth_order = "2D"
    obj = bpy.data.objects.new("GP_Peter_2D", gp)
    collection.objects.link(obj)
    records = pose_paths(mouth="rest", include_body=True)
    material_indices = {}
    for record in records:
        key = (record["fill"], record["stroke"])
        if key in material_indices:
            continue
        material = bpy.data.materials.new(f"Peter_Vector_{len(material_indices):02d}")
        bpy.data.materials.create_gpencil_data(material)
        style = material.grease_pencil
        style.show_fill = record["fill"] is not None
        style.show_stroke = record["stroke"] is not None
        style.fill_color = linear_rgba(record["fill_rgba"]) or (0, 0, 0, 0)
        style.color = linear_rgba(record["stroke_rgba"]) or (0, 0, 0, 0)
        material_indices[key] = len(gp.materials)
        gp.materials.append(material)
    layer = gp.layers.new("Peter — editable vector contours", set_active=True)
    layer.use_lights = False
    drawing = layer.frames.new(1).drawing
    drawing.add_strokes([len(record["points"]) for record in records])
    for index, record in enumerate(records):
        stroke = drawing.strokes[index]
        stroke.material_index = material_indices[(record["fill"], record["stroke"])]
        stroke.cyclic = record["closed"]
        stroke.fill_id = index + 1 if record["fill"] is not None and record["closed"] else 0
        stroke.fill_opacity = 1.0
        stroke.hide_stroke = not record["stroke"] or record["stroke_width"] <= 0
        radius = record["stroke_width"] * .005
        for point, (x, y) in zip(stroke.points, map_points(record, image_anchor=(627, 627), scale=.01)):
            point.position = (x, y, index * .001)
            point.radius = radius
            point.opacity = 1.0
    drawing.tag_positions_changed()
    obj["approved_character"] = "Peter"
    obj["expression"] = "rest"
    obj["editable_contours"] = len(records)
    gp.use_fake_user = True
    collection.use_fake_user = True
    bpy.data.libraries.write(str(OUTPUT), {collection}, fake_user=True, compress=True)
    print(f"Peter native library created: {len(records)} strokes; {len(gp.materials)} materials; {OUTPUT.name}")


if __name__ == "__main__":
    build()
