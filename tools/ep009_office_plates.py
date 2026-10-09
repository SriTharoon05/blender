"""Superseded EP009 realistic two-plate proposal; historical WIP only.

The final episode uses one flat plate from ep009_flat_office.py. These Cycles
scenes are retained for provenance and are not part of the current queue.

Run with Blender 4.2's Python: --python tools/ep009_office_plates.py -- build
or -- render. Build never renders; render refuses CPU fallback and older output
replacement. All source/output paths are repository-relative.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / "02_EPISODES/EP009_Wrong_Screen"
SOURCE = EP / "plates/EP009_Office_Plates_4_2_v003.blend"
PLATES = (("Plate_A_Warm_Office", "Plate_A_Warm_Office_1080p_v003.png"),
          ("Plate_B_Cold_Panic", "Plate_B_Cold_Panic_1080p_v003.png"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def srgb(hex_color):
    values = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
                 for v in values) + (1,)


def build():
    import bpy
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    if SOURCE.exists():
        raise FileExistsError(f"Protected version already exists: {SOURCE.relative_to(ROOT)}")
    if bpy.app.version >= (5, 0, 0):
        raise RuntimeError("Build this separate plate source with the compatible Blender 4.2 runtime.")
    EP.joinpath("plates").mkdir(parents=True, exist_ok=True)
    EP.joinpath("edit").mkdir(parents=True, exist_ok=True)
    rng = random.Random(909)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    def material(name, color, roughness=.45, metallic=0, emission=0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.diffuse_color = srgb(color)
        p = m.node_tree.nodes.get("Principled BSDF")
        p.inputs["Base Color"].default_value = srgb(color)
        p.inputs["Roughness"].default_value = roughness
        p.inputs["Metallic"].default_value = metallic
        if emission:
            p.inputs["Emission Color"].default_value = srgb(color)
            p.inputs["Emission Strength"].default_value = emission
        return m

    def wood(name, dark, light):
        m = material(name, light, .34)
        n, links = m.node_tree.nodes, m.node_tree.links
        coord = n.new("ShaderNodeTexCoord")
        scale = n.new("ShaderNodeVectorMath"); scale.operation = "MULTIPLY"
        scale.inputs[1].default_value = (1.2, 35, 7)
        noise = n.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 3.5
        noise.inputs["Detail"].default_value = 3
        noise.inputs["Roughness"].default_value = .67
        ramp = n.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = .13
        ramp.color_ramp.elements[0].color = srgb(dark)
        ramp.color_ramp.elements[1].position = .90
        ramp.color_ramp.elements[1].color = srgb(light)
        fine = n.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 145
        bump = n.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .13
        bump.inputs["Distance"].default_value = .008
        links.new(coord.outputs["Generated"], scale.inputs[0])
        links.new(scale.outputs["Vector"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], n.get("Principled BSDF").inputs["Base Color"])
        links.new(scale.outputs["Vector"], fine.inputs["Vector"])
        links.new(fine.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], n.get("Principled BSDF").inputs["Normal"])
        return m

    def cube(name, location, dimensions, mat, bevel=0, rotation=(0, 0, 0)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rotation)
        ob = bpy.context.object; ob.name = name; ob.dimensions = dimensions
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        ob.data.materials.append(mat)
        if bevel:
            mod = ob.modifiers.new("Manufactured edge radius", "BEVEL")
            mod.width = bevel; mod.segments = 3
            ob.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
            for face in ob.data.polygons: face.use_smooth = True
        return ob

    def cylinder(name, pos, radius, depth, mat, rotation=(0, 0, 0), vertices=64):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                           location=pos, rotation=rotation)
        ob = bpy.context.object; ob.name = name; ob.data.materials.append(mat)
        for face in ob.data.polygons: face.use_smooth = True
        mod = ob.modifiers.new("Rolled rim", "BEVEL"); mod.width = .006; mod.segments = 3
        ob.modifiers.new("Weighted normal", "WEIGHTED_NORMAL")
        return ob

    def curve(name, points, radius, mat):
        data = bpy.data.curves.new(name, "CURVE")
        data.dimensions = "3D"; data.resolution_u = 16
        data.bevel_depth = radius; data.bevel_resolution = 4
        spline = data.splines.new("BEZIER"); spline.bezier_points.add(len(points) - 1)
        for point, co in zip(spline.bezier_points, points):
            point.co = co; point.handle_left_type = point.handle_right_type = "AUTO"
        ob = bpy.data.objects.new(name, data); bpy.context.scene.collection.objects.link(ob)
        data.materials.append(mat)
        return ob

    def area(name, position, target, energy, color, size, size_y=None):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy; data.color = color
        data.shape = "RECTANGLE"; data.size = size; data.size_y = size_y or size
        ob = bpy.data.objects.new(name, data); bpy.context.scene.collection.objects.link(ob)
        ob.location = position
        ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()
        return ob

    def scene(name, cold=False):
        sc = bpy.data.scenes.new(name); bpy.context.window.scene = sc
        sc.render.engine = "CYCLES"; sc.cycles.device = "GPU"
        sc.cycles.samples = 48; sc.cycles.use_adaptive_sampling = True
        sc.cycles.adaptive_threshold = .035
        sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPTIX"
        sc.cycles.denoising_use_gpu = True
        sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3
        sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 3
        sc.cycles.volume_bounces = 0; sc.cycles.use_light_tree = True
        sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
        sc.render.resolution_percentage = 100; sc.render.fps = 24
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_mode = "RGB"
        sc.render.image_settings.color_depth = "8"
        sc.render.image_settings.compression = 50
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
        world = bpy.data.worlds.new(name + " atmosphere"); world.use_nodes = True
        world.node_tree.nodes.get("Background").inputs["Color"].default_value = (
            (.14, .22, .38, 1) if cold else (.62, .51, .36, 1))
        world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .045 if cold else .16
        sc.world = world
        return sc

    M = {
        "oak": wood("Natural oak / fine procedural grain", "663C25", "B9895B"),
        "walnut": wood("Walnut cabinetry / procedural grain", "221B16", "6A503F"),
        "wall": material("Warm eggshell limewash", "C8C1B1", .86),
        "trim": material("Off-white window and skirting", "E4DFD4", .48),
        "aluminum": material("Anodized graphite aluminum", "313B43", .30, .77),
        "bezel": material("Laptop satin charcoal bezel", "080D14", .33),
        "rubber": material("Rubber and matte keys", "202732", .52),
        "screen": material("Screen neutral reflective glass", "091827", .18, .25, .045),
        "screenCold": material("Screen cold emissive bloom source", "A5CEF6", .21, .13, 2.0),
        "ceramic": material("Ivory glazed ceramic", "D6D4C9", .19),
        "coffee": material("Coffee meniscus", "21120D", .15),
        "brass": material("Brushed brass trim", "B29560", .26, .78),
        "curtain": material("Soft linen curtain", "DDD4BE", .98),
        "green": material("Plant foliage", "385644", .67),
        "paper": material("Warm book page edges", "D1C7B1", .82),
        "clock": material("Clock matte black metal", "282C31", .42, .35),
        "clockFace": material("Clock warm white face", "E6DECF", .8),
        "windowWarm": material("Warm diffuse window glass", "E3E3CE", .45, emission=.9),
        "windowCold": material("Dim blue window glass", "374D67", .49, emission=.08),
    }
    A = scene(PLATES[0][0])
    cam_data = bpy.data.cameras.new("CAM_EP009_Locked_Perspective")
    cam = bpy.data.objects.new(cam_data.name, cam_data); A.collection.objects.link(cam)
    cam.location = (0, -6.8, 3.4)
    cam.rotation_euler = (Vector((0, 0, 2.7)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = 65; cam_data.sensor_width = 36; cam_data.sensor_fit = "HORIZONTAL"
    cam_data.dof.use_dof = True
    focus = bpy.data.objects.new("Focus laptop front / identical plates", None)
    A.collection.objects.link(focus); focus.location = (0, -.45, 1.96)
    cam_data.dof.focus_object = focus; cam_data.dof.aperture_fstop = 5.6
    cam_data.dof.aperture_blades = 7
    A.camera = cam
    cam.lock_location = cam.lock_rotation = cam.lock_scale = (True, True, True)

    cube("Office back wall", (0, 3.25, 4.4), (7, .18, 8.8), M["wall"])
    cube("Office floor", (0, -.2, -.05), (7, 9, .12), M["walnut"])
    cube("Back skirting", (0, 3.13, .13), (7, .07, .26), M["trim"], .012)
    cube("Hero oak desk top", (0, -.59, 1.2), (3.9, 1.98, .105), M["oak"], .032)
    cube("Desk front apron", (0, -1.56, 1.015), (3.82, .075, .29), M["walnut"], .018)
    for x in (-1.67, 1.67):
        for y in (-1.35, .20): cube("Desk tapered leg", (x, y, .57), (.10, .10, 1.14), M["clock"], .01)
    # Room margins remain softly out of focus; center wall is an intentional clean stage.
    cube("Bookcase backing", (1.70, 2.96, 2.54), (1.50, .095, 3.35), M["walnut"], .015)
    for x in (.94, 2.46): cube("Bookcase side", (x, 2.61, 2.54), (.10, .75, 3.49), M["walnut"], .014)
    book_mats = [material("Muted cloth book " + str(i), c, .83) for i, c in enumerate(
        ("656C6A", "5A6759", "A28E6F", "516172", "78675B", "B0A48C", "604A45"))]
    for row in range(4):
        zz = .93 + row * .79
        cube("Bookshelf oak shelf", (1.70, 2.60, zz), (1.63, .79, .06), M["walnut"], .01)
        xx = 1.03
        while xx < 2.33:
            width = rng.uniform(.07, .13); height = rng.uniform(.42, .65)
            cube("Book cloth spine", (xx, 2.50, zz + .03 + height / 2),
                 (width, .42, height), rng.choice(book_mats), .006,
                 rotation=(0, rng.choice((0, 0, -.045, .04)), 0))
            cube("Book top page edge", (xx, 2.51, zz + .04 + height),
                 (width * .78, .34, .008), M["paper"], .002)
            xx += width + .015

    window = cube("Warm window diffuse glass", (-1.94, 3.12, 3.20), (1.10, .025, 2.5), M["windowWarm"], .003)
    for x in (-2.55, -1.33): cube("Window upright frame", (x, 3.03, 3.20), (.10, .18, 2.70), M["trim"], .009)
    for z in (1.86, 4.54): cube("Window cross frame", (-1.94, 3.03, z), (1.30, .18, .10), M["trim"], .009)
    cube("Window mullion", (-1.94, 3.02, 3.20), (.037, .15, 2.55), M["trim"], .006)
    cube("Window horizontal divider", (-1.94, 3.02, 3.20), (1.20, .15, .04), M["trim"], .006)
    for j in range(8):
        x = -2.75 + .058 * j
        curtain = cube("Pleated linen curtain", (x, 2.97 + .025 * math.sin(j), 3.18),
                       (.065, .055, 2.77), M["curtain"], .022)

    # Large stylized laptop remains physically rendered and its exact screen quad is
    # exported for separately animated screen-share graphics in the 2D pass.
    cube("Laptop CNC base", (0, -.78, 1.294), (2.19, .85, .062), M["aluminum"], .019)
    cube("Keyboard inset", (0, -.77, 1.328), (1.92, .48, .012), M["bezel"], .012)
    for row in range(5):
        for col in range(15):
            cube("Keyboard sculpted keycap", (-.875 + col * .125, -.60 - row * .09, 1.342),
                 (.107, .067, .011), M["rubber"], .003)
    cube("Wide spacebar", (0, -1.065, 1.343), (.53, .056, .010), M["rubber"], .003)
    cube("Touchpad brushed inset", (0, -1.13, 1.334), (.61, .17, .004), M["aluminum"], .01)
    cylinder("Laptop black hinge left", (-.75, -.369, 1.325), .025, .35, M["bezel"], (0, math.pi / 2, 0))
    cylinder("Laptop black hinge right", (.75, -.369, 1.325), .025, .35, M["bezel"], (0, math.pi / 2, 0))
    tilt = -.17
    lid_center = Vector((0, -.31, 1.985))
    lid = cube("Laptop lid satin shell", lid_center, (2.20, .053, 1.32), M["aluminum"], .023,
               rotation=(tilt, 0, 0))
    def lid_point(x, z, front=-.032):
        return lid_center + Vector((x, front * math.cos(tilt) - z * math.sin(tilt),
                                         front * math.sin(tilt) + z * math.cos(tilt)))
    bezel = cube("Laptop black display bezel", lid_point(0, 0), (2.153, .012, 1.273), M["bezel"], .017,
                 rotation=(tilt, 0, 0))
    screen = cube("Laptop empty overlay screen", lid_point(0, -.010, -.042), (2.017, .007, 1.123), M["screen"], .006,
                  rotation=(tilt, 0, 0))
    cylinder("Laptop camera lens", lid_point(0, .605, -.047), .008, .003, M["clock"], (math.pi / 2 + tilt, 0, 0), 24)
    cube("Laptop status LED", lid_point(.970, -.605, -.047), (.012, .007, .007),
         material("Tiny pale status LED", "A3D1C0", .2, emission=1), .002, (tilt, 0, 0))
    for j in range(3): cube("USB port edge", (-1.099, -.66 - j * .13, 1.294), (.006, .077, .014), M["bezel"], .003)

    # True hollow ceramic mug with coffee meniscus, rolled lip and curved handle.
    mug_x, mug_y = -1.42, -.89
    verts, faces = [], []
    rings = ((.119, 1.261), (.146, 1.282), (.151, 1.572), (.145, 1.592),
             (.128, 1.592), (.126, 1.315), (.002, 1.315))
    for radius, z in rings:
        for k in range(64):
            t = 2 * math.pi * k / 64
            verts.append((mug_x + radius * math.cos(t), mug_y + radius * math.sin(t), z))
    for r in range(len(rings) - 1):
        for k in range(64):
            faces.append((r * 64 + k, r * 64 + (k + 1) % 64,
                          (r + 1) * 64 + (k + 1) % 64, (r + 1) * 64 + k))
    mesh = bpy.data.meshes.new("Ceramic lathed hollow cup mesh"); mesh.from_pydata(verts, [], faces)
    mesh.materials.append(M["ceramic"])
    mug = bpy.data.objects.new("Coffee mug glazed hollow ceramic", mesh); A.collection.objects.link(mug)
    for face in mesh.polygons: face.use_smooth = True
    cylinder("Coffee dark curved surface", (mug_x, mug_y, 1.55), .124, .007, M["coffee"])
    curve("Coffee cup handle", [(mug_x - .136, mug_y, 1.543), (mug_x - .251, mug_y, 1.529),
                                 (mug_x - .266, mug_y, 1.397), (mug_x - .132, mug_y, 1.335)], .025, M["ceramic"])
    cylinder("Cork mug coaster", (mug_x, mug_y, 1.261), .179, .012, material("Natural cork", "8A735A", .96))
    # Slightly asymmetric smooth wireless mouse, correctly seated on desk.
    mouse_x = 1.13
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, location=(mouse_x, -.84, 1.31))
    mouse = bpy.context.object; mouse.name = "Wireless mouse pearl shell"
    mouse.scale = (.124, .192, .070); mouse.data.materials.append(M["ceramic"])
    for face in mouse.data.polygons: face.use_smooth = True
    curve("Mouse center seam", [(mouse_x, -.995, 1.342), (mouse_x, -.945, 1.363), (mouse_x, -.870, 1.376)], .0013, M["aluminum"])
    cylinder("Mouse black scroll wheel", (mouse_x, -.893, 1.375), .014, .036, M["rubber"], (math.pi / 2, 0, 0), 32)

    # Clock is placed at the right margin with an offset hard-light shadow in panic.
    clock_center = (1.30, 3.07, 4.75)
    cylinder("Wall clock rim", clock_center, .34, .085, M["clock"], (math.pi / 2, 0, 0))
    cylinder("Wall clock cream dial", (1.30, 3.018, 4.75), .308, .010, M["clockFace"], (math.pi / 2, 0, 0))
    for k in range(12):
        t = 2 * math.pi * k / 12
        cube("Clock hour index", (1.30 + .270 * math.sin(t), 3.005, 4.75 + .270 * math.cos(t)),
             (.012, .012, .035), M["clock"], .002, rotation=(0, t, 0))
    curve("Clock minute hand", [(1.30, 2.998, 4.75), (1.30 + .19, 2.998, 4.75 + .11)], .008, M["clock"])
    curve("Clock hour hand", [(1.30, 2.996, 4.75), (1.30 - .034, 2.996, 4.75 + .13)], .010, M["clock"])
    cylinder("Clock hand hub", (1.30, 2.989, 4.75), .021, .006, M["brass"], (math.pi / 2, 0, 0), 24)
    # The chair is low enough for the character body to cover it naturally.
    cube("Office chair padded back", (0, .50, 1.86), (1.15, .16, 1.06), M["rubber"], .075)
    cube("Office chair seat", (0, .36, 1.03), (1.20, .75, .14), M["rubber"], .07)

    shared = list(A.objects)
    # Shared original geometry; lighting and screen/window materials differ by plate.
    area("A warm soft window", (-2.05, .35, 4.5), (0, -.3, 1.7), 580, (1, .84, .65), 2.0, 2.8)
    area("A restrained camera fill", (0, -3.3, 4.3), (0, -.3, 1.6), 75, (.86, .90, 1), 3.0)
    area("A bookshelf warm bounce", (1.9, 1.4, 4.4), (1.7, 2.7, 2.2), 55, (1, .78, .54), 1.9)
    sun_data = bpy.data.lights.new("A morning sun", "SUN"); sun_data.energy = .72
    sun_data.angle = .055; sun_data.color = (1, .86, .68)
    sun = bpy.data.objects.new(sun_data.name, sun_data); A.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(28), math.radians(-20), math.radians(-38))

    B = scene(PLATES[1][0], cold=True)
    for ob in shared:
        if ob not in (window, screen): B.collection.objects.link(ob)
    B.camera = cam
    cold_window = window.copy(); cold_window.data = window.data.copy()
    cold_window.name = "Cold window same geometry"
    cold_window.data.materials.clear(); cold_window.data.materials.append(M["windowCold"])
    B.collection.objects.link(cold_window)
    cold_screen = screen.copy(); cold_screen.data = screen.data.copy()
    cold_screen.name = "Cold laptop overlay screen same quad"
    cold_screen.data.materials.clear(); cold_screen.data.materials.append(M["screenCold"])
    B.collection.objects.link(cold_screen)
    area("B strong cold laptop spill", (0, -.43, 2.02), (0, -.98, 1.23), 72, (.28, .48, 1), 1.75, 1.02)
    area("B blue overhead edge", (-1.75, .10, 4.25), (0, -.1, 1.3), 110, (.22, .39, .72), .62, 2.0)
    area("B cold camera bounce", (0, -3.6, 3.8), (0, 0, 1.9), 22, (.22, .43, 1), 2.6)
    area("B red notification reflected edge", (1.12, -1.2, 2.02), (1.0, 1.5, 2.1), 22, (1, .035, .025), .32)
    area("B hard clock shadow", (.4, 1.65, 4.64), (1.3, 3.14, 4.75), 8, (.45, .63, 1), .055)

    bpy.context.window.scene = A
    bpy.context.view_layer.update()
    corners = [lid_point(-1.0085, .5515, -.048), lid_point(1.0085, .5515, -.048),
               lid_point(1.0085, -.5715, -.048), lid_point(-1.0085, -.5715, -.048)]
    def project(point):
        p = world_to_camera_view(A, cam, Vector(point))
        return [round(p.x * 1080, 3), round((1 - p.y) * 1920, 3)]
    # The lid + base convex hull is an accurate lightweight foreground occlusion
    # contract. Its few corner pixels include the manufacturing bevel radius;
    # root can mask the character torso with this polygon without another render.
    laptop_points = [project(lid_point(x, z, front))
                     for x in (-1.10, 1.10) for z in (-.66, .66)
                     for front in (-.027, .027)]
    laptop_points += [project((x, y, z)) for x in (-1.095, 1.095)
                      for y in (-1.205, -.355) for z in (1.263, 1.325)]
    def convex_hull(points):
        pts = sorted(set(tuple(p) for p in points))
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        lower, upper = [], []
        for p in pts:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0: lower.pop()
            lower.append(p)
        for p in reversed(pts):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0: upper.pop()
            upper.append(p)
        return [list(p) for p in lower[:-1] + upper[:-1]]
    contract = {
        "episode": "EP009_Wrong_Screen", "resolution": [1080, 1920],
        "native_source": SOURCE.relative_to(ROOT).as_posix(),
        "blender_source_version": bpy.app.version_string,
        "camera_continuity": "Same linked perspective camera and same shared geometry in both plates",
        "camera": {"location": list(cam.location), "rotation_euler": list(cam.rotation_euler),
                   "lens_mm": 65, "dof_fstop": 5.6},
        "screen_quad_px_clockwise_from_top_left": [project(p) for p in corners],
        "screen_quad_world": [list(p) for p in corners],
        "laptop_foreground_occlusion_polygon_px": convex_hull(laptop_points),
        "character_face_target_px": [540, 780],
        "negative_character_space_px": [290, 580, 715, 980],
        "composition_landmarks_px": {
            "desk_back": project((0, .40, 1.255)),
            "desk_front": project((0, -1.58, 1.255)),
            "mug_center": project((mug_x, mug_y, 1.43)),
            "mouse_center": project((mouse_x, -.84, 1.35)),
            "character_face_world_proxy": project((0, .35, 3.37)),
        },
        "samples": 48, "procedural_original_assets_only": True,
        "render_in_build": False, "plates": [name for _, name in PLATES],
        "color_management": "AgX - Medium High Contrast baked into display-referred 8-bit sRGB PNG plates",
    }
    for sc, (_, filename) in zip((A, B), PLATES):
        sc.render.filepath = "//" + filename
        sc["camera_locked"] = True
        sc["prepare_only"] = True
        sc["plate_role"] = "Static background rendered once; transparent animated character is a separate pass"
    bpy.context.window.scene = A
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE), compress=True)
    write_json(EP / "edit/plate_composition.json", contract)
    print("EP009_OFFICE_BUILD_COMPLETE", json.dumps(contract["screen_quad_px_clockwise_from_top_left"]), flush=True)


def render():
    import bpy
    if os.environ.get("BLENDER_QUEUE_BUILD_ONLY") == "1":
        raise RuntimeError("Preparation-only stage is forbidden from rendering static plates.")
    if not SOURCE.is_file():
        raise FileNotFoundError("Build the native plate source before explicit render.")
    if bpy.app.version >= (5, 0, 0):
        raise RuntimeError("Current laptop driver requires the compatible Blender 4.2 OptiX plate runtime.")
    destinations = [EP / "plates" / name for _, name in PLATES]
    if any(path.exists() for path in destinations):
        raise FileExistsError("A versioned plate output already exists; use a new source/output version.")
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    devices = []
    for device in prefs.devices:
        device.use = device.type == "OPTIX" and "1650" in device.name
        if device.use: devices.append(device.name)
    if not devices:
        raise RuntimeError("GTX 1650 Ti OptiX device unavailable; CPU rendering fallback is forbidden.")
    results = []
    for scene_name, filename in PLATES:
        sc = bpy.data.scenes[scene_name]; bpy.context.window.scene = sc
        sc.cycles.device = "GPU"; sc.render.filepath = str(EP / "plates" / filename)
        print("EP009_GPU_STATIC_PLATE_START", scene_name, devices, flush=True)
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        elapsed = time.perf_counter() - started
        output = EP / "plates" / filename
        results.append({"scene": scene_name, "file": output.relative_to(ROOT).as_posix(),
                        "render_seconds": round(elapsed, 6), "bytes": output.stat().st_size,
                        "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
        report = {"episode": "EP009_Wrong_Screen", "engine": "Cycles", "backend": "OptiX",
                  "gpu": devices, "cpu_render_enabled": False,
                  "blender_version": bpy.app.version_string, "resolution": [1080, 1920],
                  "samples": 48, "denoiser": "OptiX GPU", "plates": results,
                  "static_plate_render_seconds": round(sum(p["render_seconds"] for p in results), 6),
                  "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "validation": "Actual static GPU render completed; animation/audio validation is a separate stage"}
        write_json(EP / "edit/plate_render_time.json", report)
        print("EP009_STATIC_PLATE_COMPLETE", filename, round(elapsed, 3), flush=True)
    print("EP009_OFFICE_PLATES_RENDER_COMPLETE", flush=True)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "render"))
    ns = parser.parse_args(args)
    if ns.mode == "build": build()
    else: render()


if __name__ == "__main__":
    main()
