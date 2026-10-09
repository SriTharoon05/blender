"""Blender-side worker for production_queue.py (also dispatched asynchronously by MCP)."""

import hashlib
import json
import os
import runpy
import sys
import time
import traceback
from pathlib import Path


def write_status(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    for attempt in range(6):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(.05 * (attempt + 1))


class NoRenderOps:
    """Build steps can save projects, but ordinary bpy.ops rendering is prohibited."""
    def __init__(self, original):
        self.original = original

    def __getattr__(self, name):
        if name == "render":
            return NoRenderOperators(self.original.render)
        return getattr(self.original, name)


class NoRenderOperators:
    def __init__(self, original):
        self.original = original

    def __getattr__(self, name):
        if name in {"render", "opengl"}:
            raise RuntimeError("Build-only queue steps cannot render. Move previews/renders to the render stage.")
        return getattr(self.original, name)


def render_gpu(scene, expected, cycles_backend="OPTIX"):
    import bpy
    if scene.render.engine == "CYCLES":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = cycles_backend
        prefs.get_devices()
        selected = []
        for device in prefs.devices:
            device.use = device.type == cycles_backend and expected.lower() in device.name.lower()
            if device.use:
                selected.append(device.name)
        if not selected:
            raise RuntimeError(f"Cycles {cycles_backend} GPU {expected} was not found; CPU fallback is disabled")
        scene.cycles.device = "GPU"
        if any(d.use and d.type == "CPU" for d in prefs.devices):
            raise RuntimeError("CPU Cycles devices must be disabled")
        return f"Cycles {cycles_backend} GPU: " + ", ".join(selected)
    import gpu
    if hasattr(gpu, "init"):
        gpu.init()
    renderer = gpu.platform.renderer_get()
    if not renderer or renderer.lower() in {"unknown", "none"}:
        raise RuntimeError("Blender has no GPU graphics context; run rendering on the local NVIDIA machine")
    if expected.lower() not in renderer.lower():
        raise RuntimeError(f"Expected {expected}, actual graphics renderer is {renderer}")
    return renderer


def main(payload_path):
    import bpy
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    root, job = Path(payload["root"]), payload["job"]
    status_path, cancel_path = Path(payload["status_path"]), Path(payload["cancel_path"])
    started = time.perf_counter()
    status = {"state": "running", "mode": payload["mode"], "pid": os.getpid(),
              "completed_frames": 0, "total_frames": len(payload.get("frames", [])), "elapsed_seconds": 0,
              "frame_hashes": {}}
    write_status(status_path, status)
    original_scene_name = bpy.context.window.scene.name if bpy.context.window else None
    original_filepath = bpy.data.filepath
    original_frame = bpy.context.scene.frame_current if bpy.context.scene else None
    mcp_loaded = False
    try:
        os.environ["PRODUCTION_ROOT"] = str(root)
        sys.path.insert(0, str(root / "tools"))
        sys.path.insert(0, str(root))
        if payload["mode"] == "build":
            step = payload["step"]
            os.environ["BLENDER_QUEUE_BUILD_ONLY"] = "1"
            original_ops, original_argv = bpy.ops, sys.argv
            try:
                bpy.ops = NoRenderOps(original_ops)
                sys.argv = ["blender", "--", *step.get("args", [])]
                runpy.run_path(str(root / step["script"]), run_name="__main__")
            finally:
                bpy.ops, sys.argv = original_ops, original_argv
        else:
            if globals().get("QUEUE_PAYLOAD_PATH"):
                # MCP uses an already-open Blender: load the exact queue project, not an unsaved scene.
                if bpy.data.is_dirty or not bpy.data.filepath:
                    raise RuntimeError("MCP rendering requires a saved, clean current scene. Save your open project first; unsaved work will not be replaced.")
                bpy.ops.wm.open_mainfile(filepath=str(root / job["blend"]))
                mcp_loaded = True
            scene = bpy.data.scenes.get(job.get("scene")) if job.get("scene") else bpy.context.scene
            if not scene:
                raise RuntimeError(f"Missing queued scene: {job.get('scene')}")
            if bpy.context.window:
                bpy.context.window.scene = scene
            scene.render.engine = job["engine"]
            scene.render.resolution_x, scene.render.resolution_y = job["resolution"]
            scene.render.resolution_percentage = 100
            scene.render.fps, scene.render.fps_base = job["fps"], 1
            scene.frame_start, scene.frame_end = job["frame_start"], job["frame_end"]
            scene.render.image_settings.file_format = "PNG"
            scene.render.image_settings.color_mode = "RGBA"
            scene.render.image_settings.color_depth = "8"
            scene.render.image_settings.compression = 50
            scene.render.use_file_extension = True
            scene.render.use_sequencer = False
            if hasattr(scene.render, "compositor_device"):
                scene.render.compositor_device = "GPU"
            status["gpu"] = render_gpu(scene, job["gpu_name"], job.get("cycles_backend", "OPTIX"))
            status.update(engine=scene.render.engine, resolution=job["resolution"], fps=job["fps"],
                          compositor_device=getattr(scene.render, "compositor_device", "not exposed"))
            write_status(status_path, status)
            for index, frame in enumerate(payload["frames"]):
                if cancel_path.is_file():
                    status.update(state="cancelled")
                    return
                scene.frame_set(frame)
                scene.render.filepath = str(root / job["frames_dir"] / f"{job['frame_prefix']}_{frame:06d}.png")
                bpy.ops.render.render(write_still=True, scene=scene.name)
                status["frame_hashes"][str(frame)] = hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest()
                status.update(frame=frame, completed_frames=index + 1, elapsed_seconds=time.perf_counter() - started)
                write_status(status_path, status)
                print(f"PRODUCTION_QUEUE_FRAME {frame} {index + 1}/{len(payload['frames'])}", flush=True)
        status.update(state="complete")
    except BaseException as exc:
        status.update(state="failed", elapsed_seconds=time.perf_counter() - started,
                      error=str(exc), traceback=traceback.format_exc())
        print(status["traceback"], flush=True)
        if not globals().get("QUEUE_PAYLOAD_PATH"):
            raise
    finally:
        try:
            if mcp_loaded:
                bpy.ops.wm.open_mainfile(filepath=original_filepath)
                if original_scene_name in bpy.data.scenes and bpy.context.window:
                    bpy.context.window.scene = bpy.data.scenes[original_scene_name]
                if original_frame is not None:
                    bpy.context.scene.frame_set(original_frame)
            elif not globals().get("QUEUE_PAYLOAD_PATH") and original_scene_name in bpy.data.scenes and bpy.context.window:
                bpy.context.window.scene = bpy.data.scenes[original_scene_name]
        except BaseException as exc:
            status.update(state="failed", error="Could not restore original Blender project: " + str(exc),
                          traceback=traceback.format_exc())
            print(status["traceback"], flush=True)
        status["elapsed_seconds"] = time.perf_counter() - started
        write_status(status_path, status)
        if status["state"] == "complete":
            print("PRODUCTION_QUEUE_COMPLETE " + json.dumps(status), flush=True)


if "QUEUE_PAYLOAD_PATH" in globals():
    main(QUEUE_PAYLOAD_PATH)
elif __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1])
