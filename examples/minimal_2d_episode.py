"""Build-only example: approved guy, upper caption, 1080x1920 at 24fps.

Run explicitly inside Blender after ``--`` with a NEW --output .blend path.
This demonstrates reusable helpers, not a finished episode or a render job.
"""
from pathlib import Path
import argparse
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.grease_pencil_toolkit import (DrawingBuilder, commit_drawing, configure_scene,
                                        create_caption, create_gp_object,
                                        start_episode_from_master)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New generated .blend file; never overwritten")
    parser.add_argument("--duration", type=float, default=2)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    import bpy
    start_episode_from_master(args.output)
    scene = bpy.data.scenes.new("EP_DEMO_Approved_2D_Character")
    bpy.context.window.scene = scene
    configure_scene(scene, duration_seconds=args.duration)
    scene.render.filepath = "//renders/EP_DEMO_######"
    obj, indices = create_gp_object(scene, "GP_EP_DEMO_ApprovedGuy")
    drawing = DrawingBuilder(indices)
    for frame in range(1, scene.frame_end + 1):
        drawing.clear()
        drawing.rect(-5, -9, 10, 18, "panel", 0)
        drawing.shape([(-1.5, -3), (-1.5, -.5), (-1, -.1), (1, -.1),
                       (1.5, -.5), (1.5, -3)], "shirt", .035)
        drawing.rect(-.3, -.3, .6, 1.2, "skin", .027)
        bob = .035 * math.sin((frame - 1) / 24 * math.pi * 2)
        drawing.approved_head(0, 1.35 + bob)
        commit_drawing(obj, frame, drawing)
    create_caption(scene, "POV: Your next episode\nstarts here", "CAPTION_EP_DEMO_Main")
    scene["demo_only"] = True
    scene["render_permission"] = "Build only; queue an explicit render separately"
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.output).resolve()), compress=True)
    print("EP_DEMO_BUILD_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
