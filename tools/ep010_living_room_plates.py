"""EP010's explicitly requested hybrid living-room stills.

Build creates a dedicated Blender 4.2 plate project and camera contract without
rendering. Render is a separate, explicit operation and refuses CPU fallback.
The animated Peter/Grease Pencil project is never opened by this older runtime.
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
EP = ROOT / "02_EPISODES/EP010_Binge_Watching"


def paths(version):
    return {
        "source": EP / "plates" / f"EP010_Living_Room_Plates_4_2_{version}.blend",
        "contract": EP / "edit" / f"plate_composition_{version}.json",
        "report": EP / "edit" / f"plate_render_time_{version}.json",
        "night": EP / "plates" / f"Plate_A_Cozy_Night_1080p_{version}.png",
        "dawn": EP / "plates" / f"Plate_B_Sunrise_Regret_1080p_{version}.png",
    }


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def srgb(hex_color):
    values = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
                 for v in values) + (1,)


def build(version="v001"):
    import bpy
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    pth = paths(version)
    if pth["source"].exists() or pth["contract"].exists():
        raise FileExistsError("Protected plate version exists; choose a new numbered version.")
    if bpy.app.version[:2] != (4, 2):
        raise RuntimeError("Build the separate plate source with the compatible Blender 4.2 runtime.")
    pth["source"].parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rng = random.Random(1010)

    def material(name, color, roughness=.6, metallic=0, emission=0):
        m = bpy.data.materials.new(name); m.use_nodes = True
        m.diffuse_color = srgb(color)
        shader = m.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = srgb(color)
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Metallic"].default_value = metallic
        if emission:
            shader.inputs["Emission Color"].default_value = srgb(color)
            shader.inputs["Emission Strength"].default_value = emission
        return m

    def fabric(name, color):
        m = material(name, color, .94)
        n, links = m.node_tree.nodes, m.node_tree.links
        tex = n.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 210
        tex.inputs["Detail"].default_value = 2
        bump = n.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .20
        bump.inputs["Distance"].default_value = .008
        links.new(tex.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], n.get("Principled BSDF").inputs["Normal"])
        shader = n.get("Principled BSDF")
        shader.inputs["Sheen Weight"].default_value = .24
        shader.inputs["Sheen Roughness"].default_value = .8
        return m

    def wood(name, low, high):
        m = material(name, high, .42)
        n, links = m.node_tree.nodes, m.node_tree.links
        coord = n.new("ShaderNodeTexCoord")
        stretch = n.new("ShaderNodeVectorMath"); stretch.operation = "MULTIPLY"
        stretch.inputs[1].default_value = (2, 44, 9)
        noise = n.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 3.5
        noise.inputs["Detail"].default_value = 3
        ramp = n.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = srgb(low)
        ramp.color_ramp.elements[1].color = srgb(high)
        bump = n.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .08
        bump.inputs["Distance"].default_value = .006
        links.new(coord.outputs["Generated"], stretch.inputs[0])
        links.new(stretch.outputs["Vector"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], n.get("Principled BSDF").inputs["Base Color"])
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], n.get("Principled BSDF").inputs["Normal"])
        return m

    def cube(name, xyz, dims, mat, bevel=0, rotation=(0, 0, 0)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=xyz, rotation=rotation)
        ob = bpy.context.object; ob.name = name; ob.dimensions = dims
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        ob.data.materials.append(mat)
        if bevel:
            mod = ob.modifiers.new("Soft physical edge", "BEVEL")
            mod.width = bevel; mod.segments = 5
            ob.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
            for f in ob.data.polygons: f.use_smooth = True
        return ob

    def cylinder(name, xyz, radius, depth, mat, vertices=64, rotation=(0, 0, 0)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                           depth=depth, location=xyz, rotation=rotation)
        ob = bpy.context.object; ob.name = name; ob.data.materials.append(mat)
        mod = ob.modifiers.new("Rounded rim", "BEVEL"); mod.width = .015; mod.segments = 3
        ob.modifiers.new("Weighted normal", "WEIGHTED_NORMAL")
        for f in ob.data.polygons: f.use_smooth = True
        return ob

    def sphere(name, xyz, scale, mat):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=xyz)
        ob = bpy.context.object; ob.name = name; ob.scale = scale
        ob.data.materials.append(mat)
        for f in ob.data.polygons: f.use_smooth = True
        return ob

    def curve(name, points, radius, mat):
        data = bpy.data.curves.new(name, "CURVE")
        data.dimensions = "3D"; data.resolution_u = 12
        data.bevel_depth = radius; data.bevel_resolution = 3
        spline = data.splines.new("BEZIER"); spline.bezier_points.add(len(points) - 1)
        for point, co in zip(spline.bezier_points, points):
            point.co = co; point.handle_left_type = point.handle_right_type = "AUTO"
        ob = bpy.data.objects.new(name, data); bpy.context.scene.collection.objects.link(ob)
        data.materials.append(mat)
        return ob

    def area(name, xyz, target, watts, color, width, height=None):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = watts; data.color = color
        data.shape = "RECTANGLE"; data.size = width; data.size_y = height or width
        ob = bpy.data.objects.new(name, data); bpy.context.scene.collection.objects.link(ob)
        ob.location = xyz
        ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()
        return ob

    def new_scene(name, dawn=False):
        sc = bpy.data.scenes.new(name); bpy.context.window.scene = sc
        sc.render.engine = "CYCLES"; sc.cycles.device = "GPU"
        sc.cycles.samples = 48; sc.cycles.use_adaptive_sampling = True
        sc.cycles.adaptive_threshold = .04
        sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPTIX"
        sc.cycles.denoising_use_gpu = True
        sc.cycles.max_bounces = 5; sc.cycles.diffuse_bounces = 3
        sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 2
        sc.cycles.volume_bounces = 0; sc.cycles.use_light_tree = True
        sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
        sc.render.resolution_percentage = 100; sc.render.fps = 24
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_mode = "RGB"
        sc.render.image_settings.color_depth = "8"
        sc.render.image_settings.compression = 30
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
        sc.world = bpy.data.worlds.new(name + " atmosphere"); sc.world.use_nodes = True
        bg = sc.world.node_tree.nodes.get("Background")
        bg.inputs["Color"].default_value = ((.19, .27, .45, 1) if dawn else (.35, .29, .25, 1))
        bg.inputs["Strength"].default_value = .12 if dawn else .055
        sc["prepare_only"] = True
        sc["explicit_hybrid_request"] = "EP010 brief dated 2026-10-10"
        sc["plate_role"] = "Static Cycles still; animation is separate Eevee skeletal cut-out."
        return sc

    M = {
        "wall": material("Warm eggshell wall", "BEB5A5", .86),
        "trim": material("Ivory painted trim", "D8D5CC", .55),
        "floor": wood("Original procedural oak flooring", "504339", "A98766"),
        "table": wood("Walnut coffee table", "281E18", "70503B"),
        "sofa": fabric("Soft teal woven sofa upholstery", "465C62"),
        "piping": fabric("Teal sofa piping", "35464C"),
        "pillow": fabric("Mustard woven cushion", "B99B58"),
        "blanket": fabric("Dusty cream knitted blanket", "B5ADA0"),
        "metal": material("Graphite powder-coated metal", "20272C", .48, .45),
        "brass": material("Brushed warm brass lamp", "A68B56", .34, .8),
        "lamp": fabric("Warm linen lampshade", "DBCAAA"),
        "bezel": material("TV satin black housing", "10141A", .25, .2),
        "screen": material("Quiet blue streaming screen", "14283D", .19, .1, .6),
        "dawnScreen": material("Bright overnight TV screen", "2E577C", .20, .1, 1.0),
        "windowNight": material("Night-blue window", "17314C", .2, emission=.11),
        "windowDawn": material("Pale dawn window", "CCDDE8", .3, emission=2.8),
        "bowl": material("Warm glazed popcorn bowl", "CFB696", .22),
        "popcorn": material("Fresh butter popcorn", "EBDFC0", .85),
        "rug": fabric("Textured cream rug", "ADA698"),
        "packet": material("Ochre snack packet", "B28147", .4),
        "redPacket": material("Faded red snack packet", "975347", .43),
    }
    A = new_scene("Plate_A_Cozy_Night")
    camera_data = bpy.data.cameras.new("CAM_EP010_Locked_Room")
    camera = bpy.data.objects.new(camera_data.name, camera_data); A.collection.objects.link(camera)
    camera.location = (0, -10, 5.6)
    camera.rotation_euler = (Vector((0, 0, 4.2)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"; camera_data.ortho_scale = 9
    camera_data.dof.use_dof = True
    focus = bpy.data.objects.new("Focus at sofa / same for both plates", None)
    A.collection.objects.link(focus); focus.location = (0, -.15, 2.6)
    camera_data.dof.focus_object = focus; camera_data.dof.aperture_fstop = 8
    camera.lock_location = camera.lock_rotation = camera.lock_scale = (True, True, True)
    A.camera = camera

    # The tall unadorned upper wall is deliberate caption-safe negative space.
    cube("Living room back wall", (0, 2.7, 4.55), (7, .16, 9.1), M["wall"])
    cube("Floor base", (0, -.1, -.07), (7, 8, .14), M["floor"])
    for i in range(12):
        x = -3.3 + i * .58
        cube("Oak floor plank", (x, -.1, .005), (.565, 8, .015), M["floor"], .004)
    cube("Back wall skirting", (0, 2.59, .15), (7, .06, .3), M["trim"], .012)
    cube("Cream living-room rug", (0, -.2, .025), (4.55, 3.8, .032), M["rug"], .024)

    # Sofa is intentionally oversized: a broad physical seat for the flat puppet.
    cube("Sofa upholstered base", (0, .58, .77), (4.45, 1.75, .73), M["sofa"], .15)
    cube("Sofa plush back", (0, 1.26, 2.24), (4.45, .43, 2.07), M["sofa"], .16)
    for x in (-2.12, 2.12):
        cube("Sofa rounded arm", (x, .5, 1.67), (.38, 1.95, 1.5), M["sofa"], .17)
        for y in (-.1, 1.2):
            cube("Sofa hardwood foot", (x, y, .22), (.15, .15, .44), M["table"], .012)
    for i, x in enumerate((-1.31, 0, 1.31)):
        cube("Seat cushion " + str(i), (x, .25, 1.22), (1.275, 1.22, .30), M["sofa"], .12)
        cube("Back cushion " + str(i), (x, .945, 2.3), (1.285, .38, 1.69), M["sofa"], .13)
        curve("Sofa cushion piping " + str(i),
              [(x - .54, -.35, 1.22), (x + .54, -.35, 1.22),
               (x + .58, -.28, 1.22)], .012, M["piping"])
    cube("Night tidy folded blanket", (-1.6, .01, 1.47), (.58, .74, .17), M["blanket"], .075)
    pillow = cube("Night mustard pillow", (1.43, .63, 2.03), (.69, .27, .75), M["pillow"], .12,
                  rotation=(math.radians(8), math.radians(-9), math.radians(-9)))

    # Window/blinds sit to the left of Peter; TV remains over his right shoulder.
    window_center = Vector((-1.71, 2.59, 4.62))
    window_width, window_height = 1.07, 2.26
    window = cube("Night window sky", window_center, (window_width, .035, window_height), M["windowNight"], .006)
    for x in (-2.29, -1.13):
        cube("Window side trim", (x, 2.48, 4.62), (.095, .16, 2.46), M["trim"], .012)
    for z in (3.435, 5.805):
        cube("Window top bottom trim", (-1.71, 2.48, z), (1.25, .18, .095), M["trim"], .012)
    for i in range(11):
        cube("Window half-open blind slat", (-1.71, 2.41, 3.64 + i * .192),
             (1.08, .065, .070), M["trim"], .009,
             rotation=(math.radians(-18), 0, 0))
    for x in (-2.11, -1.31):
        curve("Blind pull cord", [(x, 2.36, 3.48), (x, 2.36, 5.72)], .008, M["trim"])

    tv_center = Vector((1.27, 2.55, 4.65))
    screen_width, screen_height = 1.50, 1.06
    cube("Wall-mounted television black shell", tv_center, (1.61, .12, 1.19), M["bezel"], .027)
    screen = cube("TV clear streaming overlay screen", (1.27, 2.475, 4.65),
                  (screen_width, .009, screen_height), M["screen"], .008)
    cube("TV standby LED", (1.98, 2.468, 4.096), (.012, .010, .012),
         material("Tiny TV standby LED", "799FCD", .4, emission=2), .003)
    cube("Wall console walnut cabinet", (1.40, 2.27, 3.25), (1.40, .58, .34), M["table"], .018)
    for x in (1.02, 1.57):
        cube("Console cabinet door", (x, 1.97, 3.25), (.50, .025, .28), M["table"], .012)
        cube("Console small brass pull", (x + .18, 1.949, 3.26), (.07, .02, .013), M["brass"], .004)
    for i in range(3):
        cube("Book on wall console", (1.52, 2.2, 3.465 + i * .045), (.52 - i * .05, .29, .038),
             M["trim"] if i == 1 else M["sofa"], .005)

    # Tall linen floorlamp with a real shade and hidden warm area emitter.
    cylinder("Floor lamp brass foot", (2.19, .88, .10), .22, .13, M["brass"])
    cylinder("Floor lamp brass stem", (2.19, .88, 1.91), .022, 3.55, M["brass"], 32)
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=.38, radius2=.25,
                                    depth=.55, location=(2.19, .88, 3.84))
    shade = bpy.context.object; shade.name = "Floorlamp linen shade"; shade.data.materials.append(M["lamp"])
    for f in shade.data.polygons: f.use_smooth = True
    for z, radius in ((3.565, .38), (4.115, .25)):
        bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=.008,
                                        major_segments=64, minor_segments=8, location=(2.19, .88, z))
        bpy.context.object.name = "Shade rolled fabric rim"; bpy.context.object.data.materials.append(M["lamp"])

    # Foreground coffee table remains beneath the safe dialogue band.
    cube("Low coffee table walnut top", (0, -2.02, .67), (3.45, 1.38, .12), M["table"], .06)
    for x in (-1.40, 1.40):
        for y in (-2.56, -1.50):
            cube("Coffee table tapered leg", (x, y, .31), (.12, .12, .62), M["metal"], .012)

    def bowl(name, center, full):
        cx, cy, cz = center
        verts, faces = [], []
        rings = ((.17, 0), (.29, .05), (.36, .19), (.365, .23),
                 (.335, .23), (.315, .18), (.24, .07), (.07, .04))
        for rad, z in rings:
            for k in range(64):
                t = math.tau * k / 64
                verts.append((cx + rad * math.cos(t), cy + rad * math.sin(t), cz + z))
        for j in range(len(rings) - 1):
            for k in range(64):
                faces.append((j * 64 + k, j * 64 + (k + 1) % 64,
                              (j + 1) * 64 + (k + 1) % 64, (j + 1) * 64 + k))
        mesh = bpy.data.meshes.new(name + " hollow mesh"); mesh.from_pydata(verts, [], faces)
        mesh.materials.append(M["bowl"])
        ob = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(ob)
        for f in mesh.polygons: f.use_smooth = True
        if full:
            for k in range(48):
                rr = .285 * math.sqrt(rng.random()); angle = rng.random() * math.tau
                sphere("Night popcorn kernel", (cx + rr * math.cos(angle), cy + rr * math.sin(angle),
                       cz + .22 + .055 * rng.random()), (.041, .036, .035), M["popcorn"])
        return ob

    night_bowl = bowl("Night full popcorn bowl", (-1.07, -1.91, .74), True)
    cube("Night tidy remote on table", (.86, -1.99, .755), (.16, .42, .049), M["metal"], .02,
         rotation=(0, 0, .20))
    cube("Night neatly stacked snack packet", (1.22, -1.95, .76), (.33, .39, .05), M["packet"], .025,
         rotation=(0, 0, -.18))

    # Shared geometry guarantees exact camera/furniture continuity. Scene-specific
    # foreground dressing is held in separate objects, never animated in the plate.
    shared = [o for o in A.objects if not o.name.startswith("Night")]
    area("Night warm floorlamp softbox", (2.1, .7, 3.75), (0, .25, 2.3), 125, (1, .68, .38), .48, .48)
    area("Night blue television spill", (1.27, 2.3, 4.65), (.1, .1, 2), 72, (.36, .54, 1), 1.5, .85)
    area("Night soft camera bounce", (-.7, -4, 4.2), (0, .8, 2.5), 95, (.78, .82, 1), 4.5, 5)
    area("Night amber wall bounce", (2.8, .8, 6), (0, 2.6, 5.7), 85, (1, .68, .40), 2.8, 3)

    B = new_scene("Plate_B_Sunrise_Regret", dawn=True)
    for ob in shared:
        if ob not in (window, screen, pillow): B.collection.objects.link(ob)
    B.camera = camera
    for original, mat, name in ((window, M["windowDawn"], "Dawn window same geometry"),
                                 (screen, M["dawnScreen"], "Dawn TV same geometry")):
        copied = original.copy(); copied.data = original.data.copy(); copied.name = name
        copied.data.materials.clear(); copied.data.materials.append(mat); B.collection.objects.link(copied)
    bowl("Dawn empty popcorn bowl", (-1.07, -1.91, .74), False)
    cube("Dawn pillow on floor", (1.66, -1.1, .23), (.70, .67, .25), M["pillow"], .12,
         rotation=(.03, .06, -.5))
    cube("Dawn fallen blanket fold one", (-1.4, -.65, .18), (.86, .70, .28), M["blanket"], .13,
         rotation=(.14, -.11, .28))
    cube("Dawn fallen blanket fold two", (-1.61, -.94, .11), (.70, .64, .18), M["blanket"], .09,
         rotation=(.06, .14, -.32))
    for k, (x, y, z, col) in enumerate(((.70, -2.07, .77, "packet"), (1.17, -1.91, .77, "redPacket"),
                                        (.8, -.85, .10, "packet"), (-.70, -2.2, .77, "redPacket"))):
        ob = cube("Dawn crumpled snack wrapper " + str(k), (x, y, z), (.29, .30, .072), M[col], .025,
                  rotation=(rng.uniform(-.14, .14), rng.uniform(-.18, .18), rng.uniform(-.7, .7)))
        tex = bpy.data.textures.new("Wrapper crinkle " + str(k), "CLOUDS"); tex.noise_scale = .15
        sub = ob.modifiers.new("Wrapper fold subdivision", "SUBSURF"); sub.levels = 2
        disp = ob.modifiers.new("Wrapper mild folds", "DISPLACE"); disp.texture = tex; disp.strength = .034
    for k in range(14):
        x = rng.uniform(-1.4, .6); y = rng.uniform(-2.5, -1.7)
        sphere("Dawn tiny popcorn crumb", (x, y, .746), (.018, .019, .017), M["popcorn"])
    area("Dawn cold window spill", (-1.72, 2.2, 4.6), (.5, -.5, 1.8), 610, (.70, .82, 1), .95, 2.1)
    area("Dawn broad blue fill", (0, -4, 5.7), (0, .5, 2.0), 180, (.79, .88, 1), 4.5, 5)
    area("Dawn faint retained lamp", (2.1, .7, 3.75), (0, .25, 2.3), 30, (1, .70, .42), .48, .48)
    area("Dawn continuing television spill", (1.27, 2.3, 4.65), (.1, .1, 2), 75, (.35, .56, 1), 1.5, .85)
    sun_data = bpy.data.lights.new("Dawn low early sun", "SUN")
    sun_data.energy = .55; sun_data.angle = .10; sun_data.color = (1, .82, .66)
    sun = bpy.data.objects.new(sun_data.name, sun_data); B.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(66), math.radians(-28), math.radians(-50))

    bpy.context.window.scene = A; bpy.context.view_layer.update()
    def project(point):
        result = world_to_camera_view(A, camera, Vector(point))
        return [round(result.x * 1080, 3), round((1 - result.y) * 1920, 3)]

    def quad(cx, y, cz, width, height):
        return [project((cx + dx, y, cz + dz)) for dx, dz in
                ((-width / 2, height / 2), (width / 2, height / 2),
                 (width / 2, -height / 2), (-width / 2, -height / 2))]

    contract = {
        "episode": "EP010_Binge_Watching", "resolution": [1080, 1920],
        "native_source": pth["source"].relative_to(ROOT).as_posix(),
        "native_source_blender_version": bpy.app.version_string,
        "camera_continuity": "Identical linked orthographic camera, wall, sofa and table in both plates",
        "camera": {"location": list(camera.location), "rotation_euler": list(camera.rotation_euler),
                   "ortho_scale": 9, "dof_fstop": 8},
        "tv_screen_quad_px_clockwise_from_top_left": quad(1.27, 2.463, 4.65, screen_width, screen_height),
        "window_quad_px_clockwise_from_top_left": quad(-1.71, 2.565, 4.62, window_width, window_height),
        "character_face_target_px": [520, 980],
        "character_seated_body_target_px": [520, 1300],
        "character_feet_target_y_px": 1700,
        "composition_landmarks_px": {"sofa_back_top": project((0, 1.26, 3.275)),
                                      "sofa_seat_front": project((0, -.36, 1.37)),
                                      "sofa_arm_left": project((-2.12, .5, 2.42)),
                                      "coffee_table_back": project((0, -1.33, .73)),
                                      "coffee_table_front": project((0, -2.71, .73))},
        "title_safe_bounds_px": [108, 300, 918, 480],
        "dialogue_safe_bounds_px": [130, 1340, 870, 1470],
        "plates": [pth["night"].relative_to(ROOT).as_posix(), pth["dawn"].relative_to(ROOT).as_posix()],
        "plate_roles": {"night": pth["night"].relative_to(ROOT).as_posix(),
                        "dawn": pth["dawn"].relative_to(ROOT).as_posix()},
        "tv_screen_quad_px": quad(1.27, 2.463, 4.65, screen_width, screen_height),
        "window_quad_px": quad(-1.71, 2.565, 4.62, window_width, window_height),
        "window_glass_strips_px": [quad(-1.71, 2.565, 3.736 + i * .192, window_width, .108) for i in range(10)],
        "samples": 48, "procedural_original_assets_only": True,
        "render_in_build": False, "background_style_override": "Two realistic still plates explicitly requested in EP010 brief",
        "color_management": "AgX Medium High Contrast baked into display-referred sRGB PNG plates",
        "composition_color_management": "Load baked PNG as sRGB, emission/Alpha Over in Standard; keep Peter flat and unshaded",
    }
    for sc, key in ((A, "night"), (B, "dawn")):
        sc.render.filepath = "//" + pth[key].name
        sc["camera_locked"] = True
    bpy.context.window.scene = A
    bpy.ops.wm.save_as_mainfile(filepath=str(pth["source"]), compress=True)
    write_json(pth["contract"], contract)
    print("EP010_LIVING_ROOM_BUILD_COMPLETE", json.dumps(contract["tv_screen_quad_px_clockwise_from_top_left"]), flush=True)


def render(version="v001"):
    import bpy

    if os.environ.get("BLENDER_QUEUE_BUILD_ONLY") == "1":
        raise RuntimeError("Preparation-only stage is forbidden from rendering static plates.")
    pth = paths(version)
    if not pth["source"].is_file():
        raise FileNotFoundError("Build the dedicated plate source before explicitly rendering it.")
    if bpy.app.version[:2] != (4, 2):
        raise RuntimeError("The configured laptop requires the compatible Blender 4.2 OptiX plate runtime.")
    if any(pth[k].exists() for k in ("night", "dawn", "report")):
        raise FileExistsError("Protected plate output exists; choose a new numbered version.")
    bpy.ops.wm.open_mainfile(filepath=str(pth["source"]))
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    enabled = []
    for device in prefs.devices:
        device.use = device.type == "OPTIX" and "1650" in device.name
        if device.use: enabled.append({"name": device.name, "type": device.type})
    if not enabled:
        raise RuntimeError("GTX 1650 Ti OptiX unavailable; CPU fallback is forbidden.")
    results = []
    for scene_name, key in (("Plate_A_Cozy_Night", "night"), ("Plate_B_Sunrise_Regret", "dawn")):
        sc = bpy.data.scenes[scene_name]; bpy.context.window.scene = sc
        sc.cycles.device = "GPU"; sc.render.filepath = str(pth[key])
        print("EP010_GPU_STATIC_PLATE_START", scene_name, json.dumps(enabled), flush=True)
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        elapsed = time.perf_counter() - started
        output = pth[key]
        results.append({"scene": scene_name, "file": output.relative_to(ROOT).as_posix(),
                        "render_seconds": round(elapsed, 6), "bytes": output.stat().st_size,
                        "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
        write_json(pth["report"], {
            "episode": "EP010_Binge_Watching", "engine": "Cycles", "backend": "OptiX",
            "gpu": enabled, "cpu_render_enabled": False, "blender_version": bpy.app.version_string,
            "resolution": [1080, 1920], "samples": 48, "denoiser": "OptiX GPU", "plates": results,
            "static_plate_render_seconds": round(sum(r["render_seconds"] for r in results), 6),
            "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "validation": "Actual two static GPU renders; animation, audio and phone-overlay review are separate",
        })
        print("EP010_STATIC_PLATE_COMPLETE", output.name, round(elapsed, 3), flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "render"))
    parser.add_argument("--version", default="v001")
    args = parser.parse_args(argv)
    if not args.version.startswith("v") or not args.version[1:].isdigit():
        raise ValueError("Use a numbered version such as v001.")
    if args.mode == "build": build(args.version)
    else: render(args.version)


if __name__ == "__main__":
    main()
