"""EP010's static, modular Peter pajamas costume and joint-only performance.

The approved Peter head contours are reused verbatim. Costumes, props and face
presets are authored once; frames animate skeletal transforms and visibility.
This helper has no render call and can be imported by ordinary Python.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

from tools.cutout_puppet_toolkit import (
    bind_part, contour_mesh, ellipse, make_rig, rotate_joint, shape, visibility,
)
from tools.peter_flat_puppet_tools import load_flat_peter

ROOT = Path(__file__).resolve().parents[1]
TOTAL_FRAMES = 528
UNIT = 16 / 1920
SOURCE_SVG = "02_EPISODES/EP010_Binge_Watching/assets/Peter_Binge_Pajamas_v001.svg"
INK = "#111827"
SKIN = "#FFC38A"
BLUE = "#74B8FF"
YELLOW = "#FFD23F"


def rect(x, y, w, h, fill, stroke=INK, width=5):
    return shape([(x, y), (x+w, y), (x+w, y+h), (x, y+h)], fill, stroke, width)


def costume_bones():
    """Rest-pose pivots in the episode's 1080x1920 image coordinates."""
    return {
        "root": {"head": [470, 1380], "tail": [470, 1280], "parent": None},
        "torso": {"head": [470, 1370], "tail": [470, 1110], "parent": "root"},
        "neck": {"head": [470, 1110], "tail": [474, 1032], "parent": "torso"},
        "head": {"head": [474, 1032], "tail": [470, 860], "parent": "neck"},
        "jaw": {"head": [497, 986], "tail": [497, 969], "parent": "head"},
        "upper_arm.L": {"head": [355, 1115], "tail": [326, 1250], "parent": "torso"},
        "lower_arm.L": {"head": [326, 1250], "tail": [407, 1295], "parent": "upper_arm.L"},
        "hand.L": {"head": [407, 1295], "tail": [426, 1295], "parent": "lower_arm.L"},
        "upper_arm.R": {"head": [585, 1115], "tail": [637, 1235], "parent": "torso"},
        "lower_arm.R": {"head": [637, 1235], "tail": [618, 1187], "parent": "upper_arm.R"},
        "hand.R": {"head": [618, 1187], "tail": [618, 1167], "parent": "lower_arm.R"},
        "upper_leg.L": {"head": [416, 1360], "tail": [362, 1470], "parent": "torso"},
        "lower_leg.L": {"head": [362, 1470], "tail": [334, 1615], "parent": "upper_leg.L"},
        "foot.L": {"head": [334, 1615], "tail": [295, 1646], "parent": "lower_leg.L"},
        "upper_leg.R": {"head": [522, 1360], "tail": [577, 1450], "parent": "torso"},
        "lower_leg.R": {"head": [577, 1450], "tail": [612, 1590], "parent": "upper_leg.R"},
        "foot.R": {"head": [612, 1590], "tail": [650, 1618], "parent": "lower_leg.R"},
    }


def costume_parts():
    """A seated, oversized pajama costume, with complete separate leg joints."""
    return {
        "upper_leg.L": [shape([(386, 1337), (446, 1356), (392, 1497), (336, 1473)], BLUE)],
        "lower_leg.L": [shape([(336, 1460), (388, 1470), (361, 1628), (308, 1615)], BLUE),
                        shape([(307, 1606), (363, 1615)], None, stroke_width=4)],
        "foot.L": [shape([(307, 1604), (360, 1617), (365, 1645), (325, 1672),
                           (273, 1672), (269, 1656), (295, 1633)], YELLOW),
                   shape([(274, 1659), (324, 1659), (358, 1642)], None, stroke_width=3)],
        "upper_leg.R": [shape([(495, 1341), (549, 1333), (605, 1459), (549, 1480)], BLUE)],
        "lower_leg.R": [shape([(550, 1447), (602, 1438), (640, 1599), (584, 1612)], BLUE),
                        shape([(583, 1596), (638, 1586)], None, stroke_width=4)],
        "foot.R": [shape([(585, 1594), (640, 1586), (654, 1606), (685, 1619),
                           (686, 1637), (629, 1645), (581, 1628)], YELLOW),
                   shape([(589, 1623), (627, 1631), (681, 1626)], None, stroke_width=3)],
        "torso": [shape([(431, 1082), (369, 1090), (341, 1126), (361, 1379),
                          (579, 1382), (611, 1122), (575, 1091), (511, 1082),
                          (472, 1116)], BLUE),
                  shape([(431, 1082), (472, 1116), (453, 1146), (407, 1104)], BLUE),
                  shape([(511, 1082), (472, 1116), (493, 1146), (538, 1104)], BLUE),
                  shape([(471, 1118), (471, 1360)], None, stroke_width=3),
                  ellipse(486, 1187, 4, 4, YELLOW, None, 0),
                  ellipse(486, 1245, 4, 4, YELLOW, None, 0),
                  ellipse(486, 1303, 4, 4, YELLOW, None, 0),
                  rect(514, 1170, 50, 42, BLUE, width=3)],
        "neck": [shape([(437, 1014), (504, 1014), (516, 1094), (472, 1116),
                         (425, 1093)], SKIN)],
        "upper_arm.L": [shape([(345, 1102), (377, 1122), (353, 1258), (315, 1272),
                                (299, 1242)], BLUE)],
        "lower_arm.L": [shape([(313, 1237), (342, 1230), (423, 1275), (411, 1316),
                                (322, 1280)], BLUE),
                        shape([(397, 1274), (421, 1287), (409, 1311)], None, stroke_width=3)],
        "hand.L": [ellipse(407, 1295, 28, 20, SKIN),
                   shape([(414, 1281), (423, 1293), (418, 1307)], None, stroke_width=2),
                   shape([(426, 1285), (431, 1294)], None, stroke_width=2)],
        "upper_arm.R": [shape([(574, 1101), (605, 1117), (660, 1227), (643, 1261),
                                (612, 1246)], BLUE)],
        "lower_arm.R": [shape([(617, 1244), (654, 1231), (639, 1178), (611, 1172),
                                (598, 1190)], BLUE),
                        shape([(608, 1187), (638, 1179)], None, stroke_width=3)],
        "hand.R": [ellipse(618, 1187, 22, 28, SKIN),
                   shape([(609, 1171), (613, 1190)], None, stroke_width=2),
                   shape([(620, 1168), (624, 1188)], None, stroke_width=2)],
    }


def prop_parts():
    """Each prop has one parent bone; no unconnected hand or moving plate."""
    return {
        "blanket": ("torso", [
            shape([(345, 1086), (414, 1080), (449, 1114), (428, 1351), (370, 1378),
                   (345, 1230)], "#FFF0B5"),
            shape([(520, 1083), (595, 1088), (618, 1239), (582, 1378), (529, 1349),
                   (499, 1113)], "#FFF0B5"),
            shape([(369, 1139), (405, 1156), (393, 1273)], None, stroke_width=3),
            shape([(566, 1139), (546, 1180), (568, 1293)], None, stroke_width=3),
        ]),
        "bowl": ("torso", [
            ellipse(466, 1303, 87, 24, "#FFFFFF"),
            shape([(379, 1303), (399, 1371), (528, 1371), (553, 1303)], "#FF6475"),
            shape([(398, 1321), (413, 1355)], None, "#FFFFFF", 8),
            shape([(435, 1321), (443, 1359)], None, "#FFFFFF", 8),
            shape([(475, 1321), (474, 1359)], None, "#FFFFFF", 8),
            shape([(515, 1321), (508, 1356)], None, "#FFFFFF", 8),
        ]),
        "remote": ("hand.R", [
            rect(609, 1114, 26, 88, "#243851", width=4),
            ellipse(622, 1126, 4, 4, "#FF6475", None, 0),
            ellipse(622, 1152, 7, 7, "#FFFFFF", None, 0),
            rect(616, 1172, 12, 4, "#FFFFFF", None, 0),
        ]),
    }


def _runs(values):
    result = {}
    for frame, value in enumerate(values, 1):
        intervals = result.setdefault(value, [])
        if intervals and intervals[-1][1] == frame-1:
            intervals[-1][1] = frame
        else:
            intervals.append([frame, frame])
    return result


def _intersection(intervals, allowed):
    return [(max(a, c), min(b, d)) for a, b in intervals for c, d in allowed
            if max(a, c) <= min(b, d)]


def _set_visibility(obj, intervals, total):
    visibility(obj, intervals, total_frames=total)
    # Blender 5.2 actions are layered. Explicit constant state switches also
    # support older action layouts when this helper is imported for inspection.
    action = obj.animation_data.action if obj.animation_data else None
    if not action:
        return
    channels = []
    if hasattr(action, "slots"):
        for slot in action.slots:
            for layer in action.layers:
                for strip in layer.strips:
                    bag = strip.channelbag(slot, ensure=False)
                    if bag:
                        channels.extend(bag.fcurves)
    else:
        channels.extend(action.fcurves)
    for fc in channels:
        for key in fc.keyframe_points:
            key.interpolation = "CONSTANT"


def _eye_variant(paths, mode):
    paths = deepcopy(paths)
    for record in paths:
        points = record["points"]
        cx = sum(p[0] for p in points)/len(points)
        cy = sum(p[1] for p in points)/len(points)
        if mode == "focus":
            factor = .72 if "iris" in record["id"] or "pupil" in record["id"] else 1.05
            record["points"] = [[cx+(x-cx)*factor, cy+(y-cy)*factor] for x, y in points]
        elif mode == "sleepy":
            record["points"] = [[x, cy+(y-cy)*.62] for x, y in points]
    return paths


def build_puppet(collection, mapper, name="Peter", center=(470, 1135), scale=1., *, inner=False):
    """Build a rigid puppet in one collection; return named objects and pivots.

    ``mapper`` converts final pixel coordinates to world XY, normally the main
    builder's 16-unit camera mapper. ``center`` relocates the rest pose uniformly.
    Nothing is generated per frame and canonical assets are never modified.
    """
    source = load_flat_peter(ROOT)

    def local_pixel(x, y):
        return (center[0]+(x-470)*scale, center[1]+(y-1135)*scale)

    def body_map(x, y):
        return mapper(*local_pixel(x, y))

    def head_map(x, y):
        return body_map(470+(x-620)*.54, 870+(y-440)*.54)

    # All helper-created depth values are global foreground depths. The caller
    # can shake the rig as a whole without moving a caption or static plate.
    z = 1.75 if inner else .35
    rig = make_rig(collection, costume_bones(), body_map, name="RIG_EP010_"+name)
    parts, by_bone, props = [], {}, {}
    for index, (bone, paths) in enumerate(costume_parts().items()):
        ob = contour_mesh(name+"_"+bone, paths, body_map, collection,
                          z=z+index*.005, scale=UNIT*scale)
        bind_part(ob, rig, bone)
        parts.append(ob)
        by_bone[bone] = ob

    for label, (bone, paths) in prop_parts().items():
        if inner and label in {"bowl", "remote", "blanket"}:
            continue
        depth = z+.105 if label == "blanket" else z+.18
        ob = contour_mesh(name+"_"+label, paths, body_map, collection, z=depth, scale=UNIT*scale)
        bind_part(ob, rig, bone)
        parts.append(ob)
        props[label] = ob
    # Hands overlap the bowl rim and grip the remote continuously.
    for bone in ("hand.L", "hand.R"):
        for vertex in by_bone[bone].data.vertices:
            vertex.co.z += .19

    head_paths = source["parts"]["head"]["paths"]
    base = [record for record in head_paths if record.get("group") not in {"eyes", "mouth"}]
    head = contour_mesh(name+"_approved_head_identity", base, head_map, collection,
                        z=z+.27, scale=UNIT*.54*scale)
    bind_part(head, rig, "head")
    parts.append(head)
    eye_paths = [record for record in head_paths if record.get("group") == "eyes"]
    eyes = {}
    presets = {"normal": eye_paths, "blink": source["expressions"]["eyes"]["blink"],
               "focus": _eye_variant(eye_paths, "focus"), "sleepy": _eye_variant(eye_paths, "sleepy")}
    for state, paths in presets.items():
        ob = contour_mesh(name+"_eyes_"+state, paths, head_map, collection,
                          z=z+.48, scale=UNIT*.54*scale)
        bind_part(ob, rig, "head")
        eyes[state] = ob
        parts.append(ob)
    mouth = {}
    for state, paths in source["expressions"]["mouth"].items():
        ob = contour_mesh(name+"_mouth_"+state, paths, head_map, collection,
                          z=z+.51, scale=UNIT*.54*scale)
        bind_part(ob, rig, "jaw")
        mouth[state] = ob
        parts.append(ob)

    bags = contour_mesh(name+"_late_night_eye_bags", [
        shape([(489, 536), (521, 548), (555, 545)], None, "#6F3F25", 7, False),
        shape([(704, 512), (740, 521), (776, 515)], None, "#6F3F25", 7, False),
        shape([(499, 487), (512, 479), (506, 468)], None, "#FF6475", 2, False),
        shape([(716, 457), (725, 448), (721, 435)], None, "#FF6475", 2, False),
    ], head_map, collection, z=z+.505, scale=UNIT*.54*scale)
    bind_part(bags, rig, "head")
    parts.append(bags)

    popcorn = []
    if not inner:
        for index, (cx, cy, radius) in enumerate([
            (400,1293,10),(419,1282,13),(440,1291,12),(461,1279,12),
            (483,1292,12),(505,1282,12),(527,1295,11),(430,1267,9),
            (451,1257,11),(473,1260,10),(496,1265,10),
        ]):
            paths = [ellipse(cx, cy, radius, radius*.84, "#FFF0B5", INK, 2),
                     ellipse(cx+radius*.32, cy-radius*.28, radius*.5, radius*.48, "#FFF0B5", None, 0)]
            ob = contour_mesh(name+"_popcorn_kernel_%02d" % index, paths, body_map,
                              collection, z=z+.185+index*.001, scale=UNIT*scale)
            bind_part(ob, rig, "torso")
            popcorn.append(ob)
            parts.append(ob)

    decorations = {}
    if inner:
        decorations["wings"] = contour_mesh(name+"_conscience_wings", [
            shape([(355, 1160), (290, 1116), (263, 1124), (283, 1163), (258, 1171),
                   (286, 1204), (310, 1208), (326, 1243), (366, 1262)], "#FFFFFF"),
            shape([(585, 1160), (650, 1116), (677, 1124), (657, 1163), (682, 1171),
                   (654, 1204), (630, 1208), (614, 1243), (574, 1262)], "#FFFFFF"),
        ], body_map, collection, z=z-.02, scale=UNIT*scale)
        bind_part(decorations["wings"], rig, "torso")
        decorations["horns"] = contour_mesh(name+"_late_night_horns", [
            shape([(332, 735), (317, 643), (385, 696)], "#FF6475"),
            shape([(548, 697), (610, 643), (605, 737)], "#FF6475"),
        ], body_map, collection, z=z+.25, scale=UNIT*scale)
        bind_part(decorations["horns"], rig, "head")
        parts.extend(decorations.values())

    rig["approved_character_contours"] = "00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_Paths_v002.json"
    rig["role_costume_svg"] = SOURCE_SVG
    rig["character"] = "Peter"
    rig["voice_identity"] = "Charon"
    rig["role"] = "inner Peter" if inner else "binge-watching Peter"
    return {"rig": rig, "root_object": rig, "part_objects": parts, "parts_by_bone": by_bone,
            "head_object": head, "head_objects": [head, *eyes.values(), *mouth.values(), bags],
            "mouth_objects": mouth, "eye_objects": eyes, "eye_bags": bags, "popcorn": popcorn,
            "props": props, "decorations": decorations, "inner": inner, "center": list(center),
            "scale": scale, "head_mapper": head_map, "body_mapper": body_map}


def animate_puppet(state, cues):
    """Use measured speech cues, reusable face states and connected FK joints."""
    total = int(cues.get("frames", cues.get("frame_count", TOTAL_FRAMES)))
    if total != TOTAL_FRAMES:
        raise ValueError("EP010 must contain exactly 22 seconds / 528 frames")
    speaker = "inner" if state["inner"] else "peter"
    allowed = [(49, 143), (241, 288)] if state["inner"] else [(1, total)]
    rig = state["rig"]
    rows = [row for row in cues["mouth_frames"] if row.get("speaker") == speaker]
    mouth_values = ["rest"]*total
    if not state["inner"]:
        for frame in range(1, 145):
            mouth_values[frame-1] = "smile"
        for frame in range(511, total+1):
            mouth_values[frame-1] = "smile"
    for row in rows:
        frame = int(row["frame"])
        if 1 <= frame <= total:
            mouth_values[frame-1] = {"A": "AA", "E": "EE", "O": "OH"}.get(row["shape"], row["shape"])
    for label, intervals in _runs(mouth_values).items():
        if label not in state["mouth_objects"]:
            raise ValueError("Unknown Peter mouth preset: "+label)
    for label, obj in state["mouth_objects"].items():
        _set_visibility(obj, _intersection(_runs(mouth_values).get(label, []), allowed), total)

    eye_values = ["normal"]*total
    if not state["inner"]:
        for frame in range(193, 361):
            eye_values[frame-1] = "focus"
        for frame in range(361, total+1):
            eye_values[frame-1] = "sleepy"
    for blink in ([63, 270] if state["inner"] else [35, 113, 180, 229, 303, 398, 475]):
        for frame in (blink, blink+1):
            eye_values[frame-1] = "blink"
    for label, obj in state["eye_objects"].items():
        _set_visibility(obj, _intersection(_runs(eye_values).get(label, []), allowed), total)
    _set_visibility(state["eye_bags"], [] if state["inner"] else [(361, total)], total)
    specialized = set(state["mouth_objects"].values()) | set(state["eye_objects"].values())
    specialized.add(state["eye_bags"])
    specialized.update(state["popcorn"])
    specialized.update(state["decorations"].values())
    for obj in state["part_objects"]:
        if obj not in specialized:
            _set_visibility(obj, allowed, total)
    for index, obj in enumerate(state["popcorn"]):
        # A cache of persistent kernels empties in increasingly hurried cuts.
        end = 213+index*8 if index < 6 else 175+(index-6)*5
        _set_visibility(obj, [(1, end)], total)
    if state["inner"]:
        _set_visibility(state["decorations"]["wings"], [(49, 143)], total)
        _set_visibility(state["decorations"]["horns"], [(241, 288)], total)
        rotate_joint(rig, "head", [(1,0),(49,-5),(63,4),(80,-3),(96,0),
                                   (241,7),(256,-7),(272,6),(288,0),(total,0)])
        rotate_joint(rig, "upper_arm.L", [(1,0),(49,-32),(96,-20),(241,-48),(288,-48),(total,-48)])
        rotate_joint(rig, "lower_arm.L", [(1,0),(49,-24),(96,-24),(241,-44),(288,-44),(total,-44)])
        rotate_joint(rig, "hand.L", [(1,0),(49,13),(96,13),(241,-18),(288,-18),(total,-18)])
    else:
        rotate_joint(rig, "torso", [(1,2),(19,-1),(49,0),(145,0),(193,4),(241,5),
                                    (289,7),(324,8),(360,8),(369,-3),(385,-5),(433,-5),
                                    (474,-5),(481,-4),(516,-4),(528,-4)])
        rotate_joint(rig, "head", [(1,-2),(25,2),(49,0),(95,-1),(121,0),(193,-3),
                                   (241,-5),(289,-3),(304,-9),(325,-6),(346,-9),(360,-9),
                                   (361,12),(385,15),(411,10),(433,14),(469,13),(481,-2),
                                   (504,-2),(516,-2),(528,-2)])
        rotate_joint(rig, "upper_arm.L", [(1,0),(25,2),(49,0),(145,0),(193,-3),(241,-4),
                                          (289,-8),(324,-12),(360,-12),(369,6),(433,6),(528,6)])
        rotate_joint(rig, "lower_arm.L", [(1,0),(29,-42),(40,-45),(49,0),(145,0),(193,-2),
                                          (241,2),(289,-15),(324,-18),(360,-18),(369,9),(433,9),(528,9)])
        rotate_joint(rig, "hand.L", [(1,0),(29,-5),(40,-5),(49,0),(289,-4),(369,2),(528,2)])
        rotate_joint(rig, "upper_arm.R", [(1,0),(92,-2),(97,1),(104,0),(145,0),(181,-6),
                                          (193,0),(229,-5),(241,0),(289,-16),(324,-18),(360,-18),
                                          (369,7),(433,7),(481,7),(528,7)])
        rotate_joint(rig, "lower_arm.R", [(1,0),(93,-4),(97,2),(104,0),(145,0),(182,-12),
                                          (193,0),(230,-12),(241,0),(289,-20),(324,-24),(360,-24),
                                          (369,120),(433,120),(481,120),(528,120)])
        rotate_joint(rig, "hand.R", [(1,0),(94,4),(97,-3),(104,0),(180,5),(184,-5),(193,0),
                                     (228,5),(232,-5),(241,0),(289,-6),(324,4),(346,-3),(360,-3),
                                     (369,-120),(433,-120),(477,-123),(479,-117),(481,-123),
                                     (483,-120),(516,-120),(528,-120)])
        # Knees open slightly while shins counter-rotate, reading as a supported
        # seated pose instead of a straight standing silhouette over the couch.
        rotate_joint(rig, "upper_leg.L", [(1,-9),(49,-9),(193,-10),(289,-12),(361,-10),(528,-10)])
        rotate_joint(rig, "upper_leg.R", [(1,9),(49,9),(193,10),(289,12),(361,10),(528,10)])
        rotate_joint(rig, "lower_leg.L", [(1,9),(49,9),(193,10),(289,12),(361,10),(528,10)])
        rotate_joint(rig, "lower_leg.R", [(1,-9),(49,-9),(193,-10),(289,-12),(361,-10),(528,-10)])
    jaw = [(1,0)]
    jaw.extend((int(row["frame"]), 1.6*float(row.get("openness", 0))) for row in rows)
    jaw.append((total,0))
    rotate_joint(rig, "jaw", sorted(jaw))
    # Every joint holds its final state for the exact last half-second tag.
    for bone in rig.pose.bones:
        bone.keyframe_insert(data_path="rotation_euler", frame=517)
        bone.keyframe_insert(data_path="rotation_euler", frame=528)
    state["speech_speaker"] = speaker
    state["lip_sync_method"] = cues.get("lip_sync_method", "Measured word timings and audio RMS; reusable visemes, not phoneme forced alignment")
    return state


def build_episode_puppets(scene, cues, mapper):
    import bpy
    collection = bpy.data.collections.new("CHAR_EP010_Peter_Modular_Pajamas")
    scene.collection.children.link(collection)
    main = build_puppet(collection, mapper, center=(470,1225))
    inner = build_puppet(collection, mapper, "Inner_Peter", (245,810), .30, inner=True)
    animate_puppet(main, cues)
    animate_puppet(inner, cues)
    metadata = {
        "character_library": "00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_v002.blend",
        "approved_contours": "00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_Paths_v002.json",
        "costume_svg": SOURCE_SVG, "main_static_parts": len(main["part_objects"]),
        "inner_static_parts": len(inner["part_objects"]), "skeletal_bones_per_character": len(main["rig"].data.bones),
        "character_geometry_redraws_per_frame": 0, "character_mesh_animation": False,
        "parts_rigidly_bound": True, "main_speaker": "peter", "inner_speaker": "inner",
        "peter_voice": "Charon", "inner_voice": "Charon", "costume": "oversized pastel-blue pajamas, yellow slippers, cream blanket",
        "lip_sync_method": main["lip_sync_method"],
        "main_head_pixel_reference": [470,960], "main_head_reference_scale": .54,
        "main_instance_translation_px": [0,90],
        "main_rest_face_bounds_approx_px": [269,738,631,1152],
    }
    return {"main": main, "inner": inner, "metadata": metadata, "collection": collection}


def write_costume_svg(target=None):
    """Save the episode's editable costume source, with explicit parent pivots."""
    target = Path(target) if target is not None else ROOT/SOURCE_SVG
    if target.exists():
        raise FileExistsError("Choose a new costume version instead of overwriting an existing source")
    bones = costume_bones()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920">',
             '<title>EP010 Peter pajamas — static modular puppet costume v001</title>',
             '<desc>Peter head identity reuses approved v002 contours. All fills are solid; each modular part has a skeletal pivot.</desc>']
    sources = [(name, name, paths) for name, paths in costume_parts().items()]
    sources.extend((name, bone, paths) for name, (bone, paths) in prop_parts().items())
    source = load_flat_peter(ROOT)
    mapped_head = deepcopy(source["parts"]["head"]["paths"])
    for record in mapped_head:
        record["points"] = [[470+(x-620)*.54,870+(y-440)*.54] for x,y in record["points"]]
        record["stroke_width"] = record.get("stroke_width", 0)*.54
    sources.append(("approved_head", "head", mapped_head))
    for name, bone, paths in sources:
        pivot = bones[bone]["head"]
        lines.append('<g id="part_%s" data-bone="%s" data-parent="%s" data-pivot="%s,%s">' %
                     (escape(name), escape(bone), escape(bones[bone].get("parent") or ""), *pivot))
        for index, record in enumerate(paths):
            command = "M"+" L".join("%.3f %.3f" % tuple(p) for p in record["points"])
            if record.get("closed"):
                command += " Z"
            lines.append('<path id="%s_%d" d="%s" fill="%s" stroke="%s" stroke-width="%.3f" stroke-linecap="round" stroke-linejoin="round"/>' %
                         (escape(name), index, command, record.get("fill") or "none", record.get("stroke") or "none", record.get("stroke_width",0)))
        lines.append("</g>")
    lines.append("</svg>")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines)+"\n", encoding="utf-8")
    return {"svg": target.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "parts": len(sources), "approved_head_reused": True}


if __name__ == "__main__":
    print(json.dumps(write_costume_svg(), indent=2))
