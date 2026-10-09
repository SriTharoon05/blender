"""Build only the v002 Peter flat cutout skeletal asset; never render.

Run using Blender 5.2 --background --factory-startup --python this_file.py.
All part geometry is static, rigidly bone bound; expressions switch visibility.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from cutout_puppet_toolkit import bind_part, contour_mesh, make_rig

SOURCE = ROOT / "00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_Paths_v002.json"
OUTPUT = ROOT / "00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_v002.blend"
SCALE = 16 / 2200


def mapper(x, y):
    return (x - 627) * SCALE, (1100 - y) * SCALE


def switch_driver(ob, property_name, expression):
    for attribute in ("hide_render", "hide_viewport"):
        curve = ob.driver_add(attribute)
        curve.driver.type = "SCRIPTED"
        variable = curve.driver.variables.new()
        variable.name = "state"
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = ob.parent
        variable.targets[0].data_path = '["' + property_name + '"]'
        curve.driver.expression = expression


def build():
    import bpy
    if OUTPUT.exists():
        raise FileExistsError(f"Protected version already exists: {OUTPUT.name}")
    manifest = json.loads(SOURCE.read_text(encoding="utf-8"))
    parts = manifest["parts"]
    collection = bpy.data.collections.new("CHAR_Peter_2D_Flat_Puppet")
    bpy.context.scene.collection.children.link(collection)
    collection.asset_mark()
    collection.asset_data.author = "SriTharoon05"
    collection.asset_data.description = "Peter v002: flat solid colors; modular static SVG cutouts; rigid skeletal puppet and mouth/blink presets."
    bones = {"root": {"head": manifest["root_pivot"], "tail": [627, 1304], "parent": None}}
    for name, part in parts.items():
        children = [child["pivot"] for child in parts.values() if child["parent"] == name]
        tail = children[0] if len(children) == 1 else [part["pivot"][0], part["pivot"][1] - 90]
        bones[name] = {"head": part["pivot"], "tail": tail, "parent": part["parent"]}
    rig = make_rig(collection, bones, mapper, name="RIG_Peter_Flat_Puppet")
    rig["mouth_state"] = 0
    rig["blink"] = 0
    rig["mouth_viseme_map"] = "0=rest,1=MBP,2=AA,3=EE,4=OH,5=FV,6=smile"
    rig.id_properties_ui("mouth_state").update(min=0, max=6, description="Static mouth preset: 0 rest,1 MBP,2 AA,3 EE,4 OH,5 FV,6 smile")
    rig.id_properties_ui("blink").update(min=0, max=1, description="Static eye preset: 0 open,1 closed")
    for index, name in enumerate(manifest["paint_order"]):
        records = parts[name]["paths"]
        if name == "head":
            records = [record for record in records if record["group"] not in {"eyes", "mouth"}]
        ob = contour_mesh("Peter_Part_" + name, records, mapper, collection, z=index * .03, scale=SCALE)
        bind_part(ob, rig, name)
        ob["source_part"] = name
        ob["rest_pivot_px"] = parts[name]["pivot"]
    open_eyes = [record for record in parts["head"]["paths"] if record["group"] == "eyes"]
    for label, records, expression in (("open", open_eyes, "state >= .5"),
                                       ("blink", manifest["expressions"]["eyes"]["blink"], "state < .5")):
        ob = contour_mesh("Peter_Eyes_" + label, records, mapper, collection, z=.65, scale=SCALE)
        bind_part(ob, rig, "head")
        ob["expression_layer"] = "eyes"
        ob["eye_state"] = label
        switch_driver(ob, "blink", expression)
    for index, label in enumerate(("rest", "MBP", "AA", "EE", "OH", "FV", "smile")):
        ob = contour_mesh("Peter_Mouth_" + label, manifest["expressions"]["mouth"][label], mapper, collection, z=.69, scale=SCALE)
        bind_part(ob, rig, "head")
        ob["expression_layer"] = "mouth"
        ob["viseme"] = label
        switch_driver(ob, "mouth_state", f"state != {index}")
    collection["source_svg"] = "00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_v002.svg"
    collection["vector_paths"] = "00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_Paths_v002.json"
    collection["style_policy"] = "Flat 2D, solid bright colors, thick black outlines, zero shading/gradients"
    collection["animation_policy"] = "Static modular cutouts, single-weight skeletal binding, expression visibility; no per-frame drawing"
    collection.use_fake_user = True
    bpy.context.view_layer.update()
    bpy.data.libraries.write(str(OUTPUT), {collection}, fake_user=True, compress=True)
    print(f"Flat Peter rig saved: {len(rig.data.bones)} bones, {len(collection.objects)-1} static meshes; {OUTPUT.name}")


if __name__ == "__main__":
    build()
