"""Reusable native Grease Pencil authoring for new production episodes.

This module imports on ordinary cloud Python without ``bpy``. Blender is needed
only when creating datablocks or saving a build. The approved head drawing is
loaded from the original EP003 function definitions without executing that
script's build/render side effects. No function here starts a render.
"""
from __future__ import annotations

import ast
from functools import lru_cache
import math
from pathlib import Path
from typing import Mapping

try:
    from .production_paths import RuntimePaths, repo_root
except ImportError:  # Also usable when tools/ is directly on sys.path in Blender.
    from production_paths import RuntimePaths, repo_root


INK = "28252D"
MASTER = "01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v005.blend"
APPROVED_CHARACTER = "00_LIBRARY/Characters/School_Guy_2D/School_Guy_2D_v001.blend"


def _bpy():
    try:
        import bpy
    except ImportError as exc:
        raise RuntimeError("Run this build inside Blender; ordinary Python can validate/import the helpers.") from exc
    return bpy


@lru_cache(maxsize=4)
def _approved_definitions(root: str):
    """Compile just the immutable approved helpers, never episode side effects."""
    path = Path(root) / "tools/ep003_gp_laptop.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = {"color", "shape", "line", "ellipse", "rect", "curve", "smooth", "mix", "head"}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != names:
        raise ValueError("The approved EP003 character helper set is incomplete.")
    palette_node = next(node for node in tree.body if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == "palette"
                                for target in node.targets))
    return compile(ast.Module(body=nodes + [palette_node], type_ignores=[]), str(path), "exec")


def approved_palette(root: str | Path | None = None) -> dict[str, str]:
    namespace = {"math": math, "INK": INK}
    exec(_approved_definitions(str(Path(root or repo_root()).resolve())), namespace)
    palette = dict(namespace["palette"])
    palette.update({"line": INK, "redLine": "FF4E4F", "chalk": "F6DEC4", "lightLine": "C48B71"})
    return palette


def color(hexcode: str) -> tuple[float, float, float, float]:
    """sRGB hex to linear Blender RGBA, matching the approved production asset."""
    rgb = [int(hexcode[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
                 for value in rgb) + (1.0,)


class DrawingBuilder:
    """Accumulate strokes for one drawing; animate poses without redrawing identity.

    ``approved_head`` keeps the original face and angular hair coordinates.
    Its scale/angle parameters transform the complete design as one unit.
    ``strokes`` uses the existing production tuple format
    ``(points, material_index, radius, closed)``.
    """
    def __init__(self, material_indices: Mapping[str, int], root: str | Path | None = None):
        self.strokes = []
        self.namespace = {"math": math, "INK": INK, "indices": dict(material_indices),
                          "strokes": self.strokes}
        exec(_approved_definitions(str(Path(root or repo_root()).resolve())), self.namespace)

    def clear(self):
        self.strokes.clear()

    def shape(self, points, mat="skin", width=.027, closed=True):
        self.namespace["shape"](points, mat, width, closed)

    def line(self, points, mat="line", width=.025):
        self.namespace["line"](points, mat, width)

    def ellipse(self, x, y, rx, ry, mat="skin", width=.027, n=40):
        self.namespace["ellipse"](x, y, rx, ry, mat, width, n)

    def rect(self, x, y, width, height, mat, radius=.027):
        self.namespace["rect"](x, y, width, height, mat, radius)

    def curve(self, points, n=24, mat="line", width=.026):
        self.namespace["curve"](points, n, mat, width)

    def approved_head(self, x, y, expression="calm", turn=0, t=0, *, scale=1, angle=0):
        first = len(self.strokes)
        self.namespace["head"](x, y, expression, turn, t)
        cosine, sine = math.cos(angle), math.sin(angle)
        for index in range(first, len(self.strokes)):
            points, material, width, closed = self.strokes[index]
            transformed = [(x + scale * ((px - x) * cosine - (py - y) * sine),
                            y + scale * ((px - x) * sine + (py - y) * cosine))
                           for px, py in points]
            self.strokes[index] = (transformed, material, width * scale, closed)


def configure_scene(scene, *, duration_seconds: float, transparent: bool = False,
                    camera_height: float = 16):
    """Set the approved fast portrait Eevee defaults on a NEW episode scene."""
    bpy = _bpy()
    frames = round(duration_seconds * 24)
    if duration_seconds <= 0 or abs(frames - duration_seconds * 24) > 1e-6:
        raise ValueError("Duration must be positive and resolve to a whole frame at 24fps.")
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
    scene.render.resolution_percentage = 100
    scene.render.fps, scene.render.fps_base = 24, 1
    scene.frame_start, scene.frame_end = 1, frames
    scene.eevee.taa_render_samples = 8
    scene.eevee.use_raytracing = False
    scene.render.use_motion_blur = False
    scene.render.use_sequencer = False
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 50
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
    if scene.camera is None:
        data = bpy.data.cameras.new(f"CAM_{scene.name}_2D")
        scene.camera = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(scene.camera)
    scene.camera.data.type = "ORTHO"
    scene.camera.data.ortho_scale = camera_height
    scene.camera.location = (0, 0, 30)
    scene.camera.rotation_euler = (0, 0, 0)
    scene["production_defaults"] = "1080x1920; 24fps; fast Eevee; local NVIDIA GPU render verification required"
    scene["approved_character_library"] = APPROVED_CHARACTER
    scene["caption_policy"] = "Shorts_Reels_Upper_Safe_Area_v002; main y300-480; tags y500-548; never bottom"
    return scene.camera


def create_gp_object(scene, name: str, palette: Mapping[str, str] | None = None):
    bpy = _bpy()
    palette = dict(palette or approved_palette())
    gp = bpy.data.grease_pencils.new(name)
    gp.stroke_depth_order = "2D"
    obj = bpy.data.objects.new(name, gp)
    scene.collection.objects.link(obj)
    indices = {}
    for label, hexcode in palette.items():
        material = bpy.data.materials.new(f"{name}_{label}")
        bpy.data.materials.create_gpencil_data(material)
        material.grease_pencil.fill_color = color(hexcode)
        material.grease_pencil.color = color(hexcode if label in {"line", "redLine", "chalk", "lightLine"} else INK)
        gp.materials.append(material)
        indices[label] = len(gp.materials) - 1
    return obj, indices


def commit_drawing(obj, frame: int, drawing: DrawingBuilder, *, layer_name="Animation", z_step=.001):
    """Write a native 5.2 drawing, including explicit fill IDs and zero-width fills."""
    _bpy()
    if obj.type != "GREASEPENCIL" or frame < 1:
        raise ValueError("Expected a Grease Pencil object and a positive frame.")
    layer = obj.data.layers.get(layer_name) or obj.data.layers.new(layer_name, set_active=True)
    layer.use_lights = False
    if any(existing.frame_number == frame for existing in layer.frames):
        raise ValueError(f"Drawing already exists at frame {frame}; do not overwrite approved drawings.")
    data = layer.frames.new(frame).drawing
    strokes = drawing.strokes
    if strokes:
        if any(len(points) < 2 or width < 0 for points, _, width, _ in strokes):
            raise ValueError("Each stroke needs at least two points and a nonnegative radius.")
        data.add_strokes([len(points) for points, _, _, _ in strokes])
    for index, (points, material, width, closed) in enumerate(strokes):
        stroke = data.strokes[index]
        stroke.material_index, stroke.cyclic = material, closed
        stroke.fill_id = index + 1 if closed else 0
        stroke.fill_opacity = 1
        stroke.hide_stroke = width == 0
        for point, (x, y) in zip(stroke.points, points):
            point.position = (x, y, index * z_step)
            point.radius, point.opacity = width, 1
    data.tag_positions_changed()
    return data


def select_caption_font(paths: RuntimePaths | None = None):
    """Return the packed approved font first; disclose a bold fallback in metadata."""
    bpy = _bpy()
    paths = paths or RuntimePaths.discover()
    for font in bpy.data.fonts:
        identity = (font.name + " " + font.filepath).lower().replace(" ", "")
        if ("arialblack" in identity or "ariblk" in identity) and font.packed_file:
            return font, {"font_name": font.name, "font_fallback": False,
                          "font_source": "Packed approved Arial Black from master"}
    path = paths.resolve_font_path()
    if path is None:
        raise FileNotFoundError("No bold caption font is available. Set BLENDER_FONT_FILE or local.json font_file.")
    font = bpy.data.fonts.load(str(path), check_existing=True)
    font.pack()
    approved = "ariblk" in path.name.lower() or "arial black" in path.name.lower()
    return font, {"font_name": font.name, "font_fallback": not approved,
                  "font_source": "Local configured/default bold font", "font_filename": path.name}


def create_caption(scene, body: str, name: str, *, slot="main", size=.53,
                   outline_radius: float | None = None, paths: RuntimePaths | None = None):
    """Static native GP lettering with rounded outlines and the saved upper placement.

    The hidden editable FONT source is retained for regenerating text. Letter
    meshes are converted once per caption, not once per animation frame.
    The caption must stay independent of scene shake and character motion.
    """
    bpy = _bpy()
    if not body.strip():
        raise ValueError("Caption cannot be empty.")
    if slot not in {"main", "tag"}:
        raise ValueError("Captions must use the approved main or tag upper slot.")
    try:
        from .shorts_caption_safe_area import place_caption
    except ImportError:
        from shorts_caption_safe_area import place_caption
    font, metadata = select_caption_font(paths)
    gp = bpy.data.grease_pencils.new(name + "_GP")
    gp.stroke_depth_order = "2D"
    obj = bpy.data.objects.new(name, gp)
    scene.collection.objects.link(obj)
    obj.location.z = 1
    for label, hexcode in (("outline", "000000"), ("white", "FFFFFF")):
        material = bpy.data.materials.new(f"{name}_{label}")
        bpy.data.materials.create_gpencil_data(material)
        material.grease_pencil.fill_color = color(hexcode)
        material.grease_pencil.color = color(hexcode)
        gp.materials.append(material)
    contour = gp.layers.new("Black outline", set_active=True)
    contour.use_lights = False
    contour_drawing = contour.frames.new(1).drawing
    letters = gp.layers.new("White letters", set_active=True)
    letters.use_lights = False
    letter_drawing = letters.frames.new(1).drawing

    curve_data = bpy.data.curves.new(name + "_EditableSource", "FONT")
    curve_data.body, curve_data.font, curve_data.size = body, font, size
    curve_data.align_x, curve_data.space_line = "CENTER", 1.18
    source = bpy.data.objects.new(curve_data.name, curve_data)
    scene.collection.objects.link(source)
    bpy.context.view_layer.update()
    evaluated = source.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        if not mesh.loop_triangles:
            raise ValueError("Caption font produced no visible glyphs.")
        letter_drawing.add_strokes([3] * len(mesh.loop_triangles))
        edge_counts = {}
        for index, triangle in enumerate(mesh.loop_triangles):
            stroke = letter_drawing.strokes[index]
            stroke.cyclic, stroke.material_index = True, 1
            stroke.fill_id, stroke.fill_opacity, stroke.hide_stroke = index + 1, 1, True
            vertices = []
            for point, vertex_index in zip(stroke.points, triangle.vertices):
                vertex = source.matrix_world @ mesh.vertices[vertex_index].co
                point.position = (vertex.x, vertex.y, .01)
                point.radius, point.opacity = 0, 1
                vertices.append((round(vertex.x, 6), round(vertex.y, 6)))
            for a, b in zip(vertices, vertices[1:] + vertices[:1]):
                edge = tuple(sorted((a, b)))
                edge_counts[edge] = edge_counts.get(edge, 0) + 1
        boundary = [edge for edge, count in edge_counts.items() if count == 1]
        contour_drawing.add_strokes([2] * len(boundary))
        radius = outline_radius if outline_radius is not None else (.045 if slot == "tag" else .055)
        for index, (a, b) in enumerate(boundary):
            stroke = contour_drawing.strokes[index]
            stroke.material_index, stroke.fill_id, stroke.cyclic = 0, 0, False
            for point, xy in zip(stroke.points, (a, b)):
                point.position = (*xy, 0)
                point.radius, point.opacity = radius, 1
        letter_drawing.tag_positions_changed()
        contour_drawing.tag_positions_changed()
    finally:
        evaluated.to_mesh_clear()
    source.hide_render, source.hide_viewport = True, True
    obj["exact_text"], obj["editable_font_source"] = body.replace("\n", " "), source.name
    for key, value in metadata.items():
        obj[key] = value
    obj["style"] = "Bold white letters; rounded thick black native GP outline; upper slot"
    bpy.context.view_layer.update()
    bounds = place_caption(obj, slot=slot, camera_height=scene.camera.data.ortho_scale)
    obj["caption_outline_edges"] = len(boundary)
    return obj, bounds


def start_episode_from_master(output: str | Path, *, paths: RuntimePaths | None = None,
                              master: str | Path | None = None):
    """Open the approved master and immediately Save As a NEW file before editing."""
    bpy = _bpy()
    paths = paths or RuntimePaths.discover()
    target = Path(output).expanduser().resolve()
    for protected in (paths.root / "00_LIBRARY", paths.root / "01_TEMPLATES"):
        if target.is_relative_to(protected.resolve()):
            raise ValueError("Episode output cannot overwrite the library or a production master.")
    if target.suffix.lower() != ".blend":
        raise ValueError("Episode output must have a .blend extension.")
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite an existing episode: {target}")
    master_path = Path(master).resolve() if master else paths.repo_path(MASTER, must_exist=True)
    if not master_path.is_file():
        raise FileNotFoundError(master_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(master_path))
    bpy.ops.wm.save_as_mainfile(filepath=str(target), compress=True)
    return bpy.context.scene
