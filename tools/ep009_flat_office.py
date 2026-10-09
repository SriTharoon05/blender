"""One crisp flat SVG office for EP009; separate source build and Eevee render.

Ordinary Python can write the SVG with ``python tools/ep009_flat_office.py svg``.
Blender 5.2 runs --python tools/ep009_flat_office.py -- build or -- render.
The SVG and native source share identical vector contours and solid colors.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / "02_EPISODES/EP009_Wrong_Screen"
SVG = EP / "plates/Flat_Office_v002.svg"
NATIVE = EP / "plates/Flat_Office_v002.blend"
PNG = EP / "plates/Flat_Office_v002.png"
CONTRACT = EP / "edit/flat_plate_composition.json"
UNIT = 16 / 1920
INK = "000000"
SCREEN_QUAD = [[241.584, 1016.075], [838.416, 1016.075],
               [841.882, 1352.118], [238.118, 1352.118]]


def contours():
    """Painter-ordered, editable plain polygons: no gradients or raster data."""
    shapes = []

    def shape(name, points, fill=None, width=5, closed=True):
        shapes.append({"id": name, "points": points, "fill": fill,
                       "stroke": INK if width else None, "stroke_width": width,
                       "closed": closed})

    def rect(name, x, y, w, h, fill, width=5):
        shape(name, [[x, y], [x + w, y], [x + w, y + h], [x, y + h]], fill, width)

    def ellipse(name, cx, cy, rx, ry, fill, width=5, n=64):
        shape(name, [[cx + rx * math.cos(2 * math.pi * k / n),
                      cy + ry * math.sin(2 * math.pi * k / n)] for k in range(n)], fill, width)

    def line(name, points, width=5):
        shape(name, points, None, width, False)

    # Bright wall and uncluttered central character stage.
    rect("cream-office-wall", -4, -4, 1088, 1930, "FFF1DA", 0)
    rect("wall-baseboard", -4, 1257, 1088, 51, "FFFFFF", 5)
    # Window left: all flat fills. The cloud is a single editable white contour.
    rect("window-outer-frame", 25, 440, 240, 490, "FFFFFF", 6)
    rect("window-blue-sky", 44, 459, 202, 452, "9DDDFF", 4)
    cloud = [[68, 553], [69, 536], [80, 522], [101, 519], [113, 502],
             [137, 496], [157, 505], [168, 520], [190, 519], [205, 531],
             [210, 550], [208, 557], [69, 557]]
    shape("one-flat-cloud", cloud, "FFFFFF", 0)
    rect("window-center-mullion", 141, 459, 8, 452, "FFFFFF", 4)
    rect("window-cross-mullion", 44, 684, 202, 8, "FFFFFF", 4)
    rect("window-sill", 11, 930, 270, 20, "FFD68D", 5)
    # Clean small bookshelf with six chunky books instead of busy fine detail.
    rect("bookcase-back", 869, 509, 182, 500, "F2AE66", 6)
    rect("bookcase-left-post", 862, 505, 15, 518, "C8793A", 5)
    rect("bookcase-right-post", 1043, 505, 15, 518, "C8793A", 5)
    for y in (671, 841, 1010):
        rect("shelf-" + str(y), 861, y, 198, 17, "C8793A", 5)
    for i, (x, y, w, h, c) in enumerate([
            (887, 557, 30, 111, "59B9A2"), (921, 537, 39, 131, "FF746D"),
            (965, 570, 27, 98, "79AAEA"), (997, 549, 30, 119, "FFD15A"),
            (887, 730, 41, 108, "FFB1C4"), (933, 719, 28, 119, "79AAEA"),
            (966, 747, 28, 91, "FFD15A"), (999, 715, 28, 123, "59B9A2"),
            (887, 922, 44, 84, "FFD15A"), (936, 897, 30, 109, "FF746D"),
            (971, 912, 26, 94, "59B9A2"), (1002, 900, 27, 106, "FFB1C4")]):
        rect("book-" + str(i), x, y, w, h, c, 4)
        line("book-spine-" + str(i), [[x + 7, y + h - 20], [x + w - 7, y + h - 20]], 3)
    # Clock: one black outline, no cast shadow, and sparse hour ticks.
    ellipse("clock-white-face", 945, 360, 73, 73, "FFFFFF", 6)
    for i in (0, 3, 6, 9):
        a = math.pi * i / 6
        line("clock-tick-" + str(i), [[945 + 58 * math.sin(a), 360 - 58 * math.cos(a)],
             [945 + 49 * math.sin(a), 360 - 49 * math.cos(a)]], 5)
    line("clock-hands", [[941, 323], [945, 360], [971, 377]], 6)
    ellipse("clock-center", 945, 360, 4, 4, INK, 0, 24)
    # Desk is flat wood-colored geometry, deliberately no wood texture or shading.
    rect("desk-top", -8, 1305, 1096, 289, "FFC575", 6)
    rect("desk-front", -8, 1594, 1096, 153, "F4A959", 6)
    rect("desk-front-rail", -8, 1582, 1096, 20, "C87C40", 5)
    rect("office-floor", -8, 1747, 1096, 185, "BFE8F5", 5)
    rect("left-desk-leg", 73, 1747, 55, 178, "C87C40", 5)
    rect("right-desk-leg", 960, 1747, 55, 178, "C87C40", 5)
    # Low chair silhouette sits behind the desk and behind Peter's white-shirt body.
    shape("chair-shoulder-silhouette", [[368, 1213], [368, 1030], [399, 988],
         [681, 988], [712, 1030], [712, 1213]], "6D8CA4", 6)
    # Laptop matches the previous screen contract precisely for animated screen UI.
    laptop_hull = [[215.899, 984.356], [864.101, 984.356], [870, 1375],
                   [909.138, 1483.481], [170.862, 1483.481], [210, 1375]]
    shape("laptop-flat-graphite-lid", [[215.899, 984.356], [864.101, 984.356],
          [870, 1375], [210, 1375]], "293347", 7)
    shape("laptop-empty-screen", SCREEN_QUAD, "C3EAFB", 4)
    ellipse("laptop-webcam", 540, 999, 3.7, 3.7, INK, 0, 24)
    shape("laptop-flat-keyboard-base", [[210, 1375], [870, 1375],
          [909.138, 1483.481], [170.862, 1483.481]], "BACBDD", 6)
    # Uncluttered but recognizable keyboard: three rows and one spacebar.
    for row in range(3):
        y = 1390 + row * 20
        for col in range(12):
            x = 238 + col * 48
            rect("key-" + str(row) + "-" + str(col), x, y, 41, 13, "FFFFFF", 2.3)
    rect("spacebar", 418, 1455, 244, 12, "FFFFFF", 2.3)
    # Cup and mouse use bold simple paths without highlights, shadows or texture.
    shape("coffee-mug-handle", [[59, 1377], [32, 1372], [16, 1383], [15, 1414],
          [33, 1429], [58, 1426]], "FFFFFF", 6)
    shape("coffee-mug-body", [[58, 1366], [124, 1366], [120, 1451],
          [111, 1459], [71, 1459], [60, 1450]], "FFFFFF", 6)
    ellipse("coffee-mug-rim", 91, 1366, 33, 9, "FFFFFF", 5, 48)
    ellipse("coffee-solid-surface", 91, 1366, 24, 4.5, "6C4031", 0, 40)
    ellipse("wireless-mouse-flat", 899, 1414, 21, 33, "FFFFFF", 5, 56)
    line("wireless-mouse-seam", [[899, 1383], [899, 1407]], 3)
    rect("wireless-mouse-scroll", 895.5, 1392, 7, 11, INK, 0)
    return shapes, laptop_hull


def save_svg():
    SVG.parent.mkdir(parents=True, exist_ok=True)
    shapes, hull = contours()
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920">',
             '<title>EP009 bright flat cartoon office, genuine editable vector paths</title>',
             '<desc>Solid colors and crisp black outlines only. No gradients, shadows, textures or embedded images.</desc>',
             '<g stroke-linecap="round" stroke-linejoin="round">']
    for item in shapes:
        points = item["points"]
        path = "M " + " L ".join(f"{x:.4f} {y:.4f}" for x, y in points)
        if item["closed"]: path += " Z"
        fill = "#" + item["fill"] if item["fill"] else "none"
        stroke = "#" + item["stroke"] if item["stroke"] else "none"
        lines.append(f'<path id="{item["id"]}" d="{path}" fill="{fill}" stroke="{stroke}" stroke-width="{item["stroke_width"]}"/>')
    lines.extend(("</g>", "</svg>"))
    SVG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return shapes, hull


def linear(hexcolor):
    c = [int(hexcolor[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c) + (1,)


def build():
    import bpy
    from mathutils import Vector
    from mathutils.geometry import tessellate_polygon

    if NATIVE.exists(): raise FileExistsError("Flat Office source version already exists; protect versions.")
    if bpy.app.version < (5, 2, 0): raise RuntimeError("Use the episode's Blender 5.2 runtime.")
    shapes, hull = save_svg()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene; scene.name = "EP009_One_Static_Flat_Office"
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 16
    scene.render.resolution_x = 1080; scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100; scene.render.fps = 24
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 50
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0; scene.view_settings.gamma = 1
    scene.render.film_transparent = False
    collection = bpy.data.collections.new("BG_EP009_Flat_Office")
    scene.collection.children.link(collection)
    palette = {}

    def mat(h):
        if h in palette: return palette[h]
        material = bpy.data.materials.new("FLAT_" + h); material.use_nodes = True
        n = material.node_tree.nodes; n.clear()
        emission = n.new("ShaderNodeEmission"); emission.inputs["Color"].default_value = linear(h)
        emission.inputs["Strength"].default_value = 1
        out = n.new("ShaderNodeOutputMaterial")
        material.node_tree.links.new(emission.outputs["Emission"], out.inputs["Surface"])
        material.diffuse_color = linear(h); palette[h] = material
        return material

    def xy(point, z):
        return ((point[0] - 540) * UNIT, (960 - point[1]) * UNIT, z)

    for index, item in enumerate(shapes):
        # The outline curves have a geometric half-stroke depth. A generous
        # painter-layer spacing prevents earlier outlines piercing newer fills.
        z = .10 * index
        if item["fill"]:
            vertices = [Vector(xy(p, z)) for p in item["points"]]
            faces = tessellate_polygon([vertices])
            lookup = {tuple(v): i for i, v in enumerate(vertices)}
            face_indices = [[int(v) if isinstance(v, int) else lookup[tuple(v)]
                             for v in triangle] for triangle in faces]
            mesh = bpy.data.meshes.new(item["id"] + " contour")
            mesh.from_pydata([tuple(v) for v in vertices], [],
                             face_indices)
            mesh.materials.append(mat(item["fill"]))
            ob = bpy.data.objects.new(item["id"], mesh); collection.objects.link(ob)
            ob["flat_vector_path"] = item["id"]
        if item["stroke"]:
            data = bpy.data.curves.new(item["id"] + " black outline", "CURVE")
            data.dimensions = "3D"; data.resolution_u = 1
            data.bevel_depth = item["stroke_width"] * UNIT / 2
            data.bevel_resolution = 2; data.resolution_u = 1
            spline = data.splines.new("POLY"); spline.points.add(len(item["points"]) - 1)
            for p, original in zip(spline.points, item["points"]):
                p.co = (*xy(original, z + .0001), 1)
            spline.use_cyclic_u = item["closed"]
            data.materials.append(mat(item["stroke"]))
            ob = bpy.data.objects.new(item["id"] + " outline", data); collection.objects.link(ob)
    data = bpy.data.cameras.new("CAM_Flat_Pixel_Exact")
    data.type = "ORTHO"; data.ortho_scale = 16
    cam = bpy.data.objects.new(data.name, data); scene.collection.objects.link(cam)
    cam.location = (0, 0, 20); scene.camera = cam
    scene.render.filepath = "//" + PNG.name
    scene["visual_style"] = "Flat 2D vector puppet stage: bright solid colors, black outlines, zero shading/gradients"
    scene["static_background_count"] = 1
    scene["svg_source"] = "//" + SVG.name
    scene["build_rendered"] = False
    bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE), compress=True)
    contract = {
        "episode": "EP009_Wrong_Screen", "background_count": 1,
        "svg": SVG.relative_to(ROOT).as_posix(), "native": NATIVE.relative_to(ROOT).as_posix(),
        "plate_png": PNG.relative_to(ROOT).as_posix(), "resolution": [1080, 1920], "fps": 24,
        "screen_quad_px_clockwise_from_top_left": SCREEN_QUAD,
        "laptop_foreground_occlusion_polygon_px": hull,
        "character_face_target_px": [540, 740],
        "composition_landmarks_px": {"mouse_center": [899, 1414], "mug_center": [91, 1414]},
        "spoken_caption_bounds_px": [108, 1340, 900, 1470],
        "svg_shape_count": len(shapes), "solid_colors_only": True,
        "shadows": False, "gradients": False, "textures": False,
        "color_management": "Standard display transform over linearized solid sRGB emission colors",
        "source_runtime": bpy.app.version_string, "build_rendered": False,
        "supersedes": "Earlier unused Cycles background WIP; this single flat office is the final background",
    }
    CONTRACT.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    print("EP009_FLAT_OFFICE_BUILT", len(shapes), flush=True)


def render():
    import bpy
    import gpu
    if os.environ.get("BLENDER_QUEUE_BUILD_ONLY") == "1":
        raise RuntimeError("Build-only stages must never render the plate.")
    if PNG.exists(): raise FileExistsError("The flat plate already exists; do not re-render completed output.")
    bpy.ops.wm.open_mainfile(filepath=str(NATIVE))
    gpu.init()
    renderer = gpu.platform.renderer_get()
    if "1650" not in renderer: raise RuntimeError(f"Expected GTX 1650 Ti GPU; actual renderer {renderer}")
    scene = bpy.context.scene; scene.render.engine = "BLENDER_EEVEE"
    scene.render.filepath = str(PNG)
    started = time.perf_counter(); bpy.ops.render.render(write_still=True)
    elapsed = time.perf_counter() - started
    data = {"episode": "EP009_Wrong_Screen", "background_count": 1,
            "renderer": renderer, "engine": "Eevee GPU", "cpu_cycles_fallback": False,
            "resolution": [1080, 1920], "actual_static_plate_render_seconds": round(elapsed, 6),
            "plate_png": PNG.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(PNG.read_bytes()).hexdigest(),
            "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "blender_version": bpy.app.version_string,
            "validation": "Actual GPU still rendered; visual inspection recorded separately"}
    (EP / "edit/flat_plate_render_time.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("EP009_FLAT_OFFICE_GPU_RENDERED", renderer, elapsed, flush=True)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("svg", "build", "render"))
    mode = parser.parse_args(args).mode
    if mode == "svg": save_svg()
    elif mode == "build": build()
    else: render()


if __name__ == "__main__": main()
