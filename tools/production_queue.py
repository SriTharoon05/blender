"""Portable, explicit local build/render queue. No Blender import is required.

Cloud authoring: validate or dry-run; home machine: build, render, or run.
Every render uses one GPU at a time. Runtime state stays in queue/.runs/.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import math
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath


ROOT = Path(__file__).resolve().parent.parent
DEFAULTS = {"resolution": [1080, 1920], "fps": 24, "engine": "BLENDER_EEVEE",
            "gpu_name": "GTX 1650 Ti"}
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
COMMON_BUILD_INPUTS = [
    "config/production_defaults.json", "config/local.json", "PRODUCTION_GUIDE.md",
    "tools/production_paths.py", "tools/grease_pencil_toolkit.py", "tools/shorts_caption_safe_area.py",
    "00_LIBRARY/asset_manifest.json", "00_LIBRARY/Characters/School_Guy_2D/character_manifest.json",
]


class QueueError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise QueueError(message)


def read_json(path, fallback=None):
    if fallback is not None and not path.is_file():
        return fallback
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    for attempt in range(6):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(.05 * (attempt + 1))


def stamp():
    return datetime.now(timezone.utc).isoformat()


def relative_path(root, value, label):
    require(isinstance(value, str) and bool(value), f"{label}: expected a relative path")
    require(not PureWindowsPath(value).is_absolute() and not PureWindowsPath(value).drive
            and not PurePosixPath(value).is_absolute(), f"{label}: absolute paths are not portable")
    require("\\" not in value, f"{label}: use forward slashes in queue paths")
    target = (root / value).resolve()
    require(target.is_relative_to(root.resolve()), f"{label}: path escapes the workspace")
    return target


def validate(queue, root=ROOT):
    require(queue.get("version") == 1, "Queue version must be 1")
    configured = read_json(root / "config/production_defaults.json", {})
    defaults = dict(DEFAULTS)
    defaults.update({k: configured[k] for k in DEFAULTS if k in configured})
    require(isinstance(queue.get("defaults", {}), dict), "defaults must be an object")
    defaults.update(queue.get("defaults", {}))
    episodes = queue.get("episodes")
    require(isinstance(episodes, list), "episodes must be a list")
    seen_ids, seen_outputs, result = set(), set(), []
    for source in episodes:
        require(isinstance(source, dict), "Each episode must be an object")
        job = dict(defaults, **source)
        episode_id = job.get("id", "")
        require(isinstance(episode_id, str) and NAME.fullmatch(episode_id), "Invalid episode id")
        require(episode_id not in seen_ids, f"Duplicate episode id: {episode_id}")
        seen_ids.add(episode_id)
        require(job["resolution"] == [1080, 1920], f"{episode_id}: expected 1080x1920")
        require(job["fps"] == 24, f"{episode_id}: expected 24 fps")
        duration = job.get("duration_seconds")
        require(isinstance(duration, (int, float)) and not isinstance(duration, bool)
                and math.isfinite(duration) and duration > 0, f"{episode_id}: invalid duration")
        count = duration * job["fps"]
        require(abs(count - round(count)) < 1e-7, f"{episode_id}: duration must be a whole number of frames")
        job["frame_count"] = int(round(count))
        job["frame_start"] = job.get("frame_start", 1)
        require(isinstance(job["frame_start"], int) and job["frame_start"] >= 1,
                f"{episode_id}: frame_start must be positive")
        job["frame_end"] = job["frame_start"] + job["frame_count"] - 1
        require(job.get("engine") in {"BLENDER_EEVEE", "CYCLES"}, f"{episode_id}: unsupported engine")
        require(job.get("cycles_backend", "OPTIX") in {"OPTIX", "CUDA"}, f"{episode_id}: cycles_backend must be OPTIX or CUDA")
        if job.get("blender_profile"):
            require(isinstance(job["blender_profile"], str) and NAME.fullmatch(job["blender_profile"]), "Invalid render blender_profile")
        require(isinstance(job.get("gpu_name"), str) and job["gpu_name"].strip(), f"{episode_id}: specify gpu_name")
        prefix = job.get("frame_prefix", episode_id)
        require(isinstance(prefix, str) and NAME.fullmatch(prefix), f"{episode_id}: invalid frame_prefix")
        job["frame_prefix"] = prefix
        build_steps = job.get("build_steps", [])
        require(isinstance(build_steps, list), f"{episode_id}: build_steps must be a list")
        produced = set()
        for index, step in enumerate(build_steps):
            require(isinstance(step, dict), f"{episode_id}: invalid build step {index + 1}")
            path = relative_path(root, step.get("script"), "build script")
            require(path.suffix == ".py" and path.is_file(), f"Missing Python build script: {path}")
            require(step.get("runner", "blender") in {"python", "blender"}, "runner must be python or blender")
            args = step.get("args", [])
            require(isinstance(args, list) and all(isinstance(arg, str) for arg in args), "build args must be strings")
            if step.get("blend"):
                input_path = relative_path(root, step["blend"], "build input blend")
                require(input_path.is_file() or step["blend"] in produced,
                        f"Missing build input blend: {input_path}")
            require(isinstance(step.get("inputs", []), list), "build inputs must be a list")
            for name in step.get("inputs", []):
                input_path = relative_path(root, name, "build input")
                require(input_path.is_file() or name in produced, f"Missing declared build input: {name}")
            require(isinstance(step.get("outputs", []), list), "build outputs must be a list")
            for output in step.get("outputs", []):
                relative_path(root, output, "build output")
                produced.add(output)
            if step.get("blender_profile"):
                require(NAME.fullmatch(step["blender_profile"]), "Invalid blender_profile")
        job["build_steps"] = build_steps
        require(isinstance(job.get("inputs", []), list), "episode inputs must be a list")
        for name in job.get("inputs", []):
            require(relative_path(root, name, "episode input").is_file(), f"Missing declared episode input: {name}")
        blend = relative_path(root, job.get("blend"), "blend")
        require(blend.suffix == ".blend", f"{episode_id}: blend must end in .blend")
        require(blend.is_file() or job["blend"] in produced, f"Missing project, with no declared build output: {blend}")
        for key in ("frames_dir", "video"):
            output = relative_path(root, job.get(key), key)
            require(str(output) not in seen_outputs, f"Two jobs share {key}: {output}")
            seen_outputs.add(str(output))
        require(Path(job["video"]).suffix.lower() == ".mp4", "video must be an MP4 path")
        if job.get("audio") is not None:
            audio = relative_path(root, job["audio"], "audio")
            require(audio.is_file() or job["audio"] in produced,
                    f"Missing audio, with no declared build output: {audio}")
        if job.get("scene") is not None:
            require(isinstance(job["scene"], str) and job["scene"], "scene must be a nonempty string")
        result.append(job)
    return result


def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def fingerprint(job, root, stage):
    """Only skip matching inputs; a changed script/project invalidates old output."""
    values = {"stage": stage, "job": job, "inputs": {}}
    inputs = [step["script"] for step in job["build_steps"]] if stage == "build" else [job["blend"]]
    if stage != "build" and job.get("audio"):
        inputs.append(job["audio"])
    if stage == "build":
        inputs.extend(step["blend"] for step in job["build_steps"] if step.get("blend"))
        inputs.extend(name for step in job["build_steps"] for name in step.get("inputs", []))
        inputs.extend(common_build_inputs(root))
    inputs.extend(job.get("inputs", []))
    for name in inputs:
        path = root / name
        values["inputs"][name] = digest(path) if path.is_file() else None
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def common_build_inputs(root):
    inputs = list(COMMON_BUILD_INPUTS)
    settings = read_json(root / "config/production_defaults.json", {})
    for key, default in {
        "character_library": "00_LIBRARY/Characters/School_Guy_2D/School_Guy_2D_v001.blend",
        "character_reference": "00_LIBRARY/Characters/School_Guy_2D/Approved_Character_Reference.png",
        "template": "01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v005.blend",
        "caption_layout": "00_LIBRARY/Caption_Layouts/Shorts_Reels_Upper_Safe_Area_v002.json",
    }.items():
        value = settings.get(key, default)
        relative_path(root, value, f"production default {key}")
        inputs.append(value)
    return inputs


def step_fingerprint(job, step, root):
    # Other build steps or final video paths must not invalidate successful immutable output.
    settings = {key: job.get(key) for key in ("id", "resolution", "fps", "engine", "duration_seconds",
                                              "frame_start", "frame_end", "gpu_name")}
    inputs = common_build_inputs(root) + job.get("inputs", []) + step.get("inputs", []) + [step["script"]]
    if step.get("blend"):
        inputs.append(step["blend"])
    hashes = {name: digest(root / name) if (root / name).is_file() else None for name in inputs}
    return hashlib.sha256(json.dumps({"settings": settings, "step": step, "inputs": hashes}, sort_keys=True).encode()).hexdigest()


def valid_build_record(record, signature, outputs, root):
    return record.get("fingerprint") == signature and record.get("status") == "complete" and all(
        (root / name).is_file() and record.get("output_hashes", {}).get(name) == digest(root / name) for name in outputs)


def verify_png(path, width, height):
    """Check dimensions, chunk CRCs and IEND, so interrupted PNGs are re-rendered."""
    try:
        with path.open("rb") as stream:
            if stream.read(8) != b"\x89PNG\r\n\x1a\n":
                return False
            first, have_pixels = True, False
            while True:
                header = stream.read(8)
                if len(header) != 8:
                    return False
                length, kind = struct.unpack(">I4s", header)
                if length > 128 * 1024 * 1024:
                    return False
                data, crc = stream.read(length), stream.read(4)
                if len(data) != length or len(crc) != 4:
                    return False
                if (binascii.crc32(kind + data) & 0xffffffff) != struct.unpack(">I", crc)[0]:
                    return False
                if first:
                    if kind != b"IHDR" or length != 13 or struct.unpack(">II", data[:8]) != (width, height):
                        return False
                    first = False
                if kind == b"IDAT":
                    have_pixels = True
                if kind == b"IEND":
                    return length == 0 and have_pixels and stream.read(1) == b""
    except OSError:
        return False


def frame_path(root, job, number):
    return root / job["frames_dir"] / f"{job['frame_prefix']}_{number:06d}.png"


def missing_frames(root, job, hashes=None, require_hashes=False):
    return [number for number in range(job["frame_start"], job["frame_end"] + 1)
            if not verify_png(frame_path(root, job, number), *job["resolution"])
            or (require_hashes and str(number) not in (hashes or {}))
            or (str(number) in (hashes or {}) and hashes[str(number)] != digest(frame_path(root, job, number)))]


def is_process_alive(pid):
    """Avoid os.kill(pid, 0): on Windows that can terminate the target process."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x1000, 0, pid)
        if not handle:
            return ctypes.get_last_error() == 5  # Access denied means potentially alive.
        try:
            code = ctypes.c_ulong()
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class QueueLock:
    def __init__(self, root):
        self.path = root / "queue/.production_lock"

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.mkdir()
        except FileExistsError:
            owner = read_json(self.path / "owner.json", {})
            require(owner.get("pid") and not is_process_alive(owner["pid"]),
                    f"Another queue owns the GPU lock: {self.path}")
            # Remove only our two known state files; never recursively remove a computed path.
            (self.path / "owner.json").unlink(missing_ok=True)
            self.path.rmdir()
            self.path.mkdir()
        atomic_json(self.path / "owner.json", {"pid": os.getpid(), "started_utc": stamp()})
        return self

    def __exit__(self, *_):
        (self.path / "owner.json").unlink(missing_ok=True)
        self.path.rmdir()


def executable(value, names, root=ROOT):
    if value:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = root / path
        found = str(path.resolve()) if path.is_file() else shutil.which(value)
        require(found, f"Executable not found: {value}")
        return found
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def tool_paths(args, root):
    local = read_json(root / "config/local.json", {})
    blender = executable(args.blender or os.environ.get("BLENDER_EXECUTABLE") or os.environ.get("BLENDER_EXE")
                         or local.get("blender_exe") or local.get("blender"), ["blender"], root)
    if not blender and os.name == "nt":
        candidates = sorted(Path(os.environ.get("ProgramFiles", "C:/Program Files")).glob(
            "Blender Foundation/Blender */blender.exe"), reverse=True)
        blender = str(candidates[0]) if candidates else None
    vendor = root / "tools/vendor/ffmpeg611/ffmpeg-6.1.1-essentials_build/bin"
    extension = ".exe" if os.name == "nt" else ""
    ffmpeg_default = str(vendor / ("ffmpeg" + extension)) if (vendor / ("ffmpeg" + extension)).is_file() else None
    ffmpeg = executable(args.ffmpeg or os.environ.get("FFMPEG_EXECUTABLE") or os.environ.get("FFMPEG_EXE")
                        or local.get("ffmpeg_exe") or local.get("ffmpeg") or ffmpeg_default, ["ffmpeg"], root)
    sibling = Path(ffmpeg).with_name("ffprobe" + extension) if ffmpeg else None
    ffprobe = executable(args.ffprobe or os.environ.get("FFPROBE_EXECUTABLE") or os.environ.get("FFPROBE_EXE")
                         or local.get("ffprobe_exe") or local.get("ffprobe")
                         or (str(sibling) if sibling and sibling.is_file() else None), ["ffprobe"], root)
    return {"blender": blender, "ffmpeg": ffmpeg, "ffprobe": ffprobe, "local": local}


def run_process(command, log_path, root, status_path=None, env=None):
    """Fresh process; poll atomic progress, preserve detailed logs and Ctrl-C cleanup."""
    started, last_frame = time.perf_counter(), None
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print("  " + subprocess.list2cmdline(command), flush=True)
    with log_path.open("w", encoding="utf-8") as log:
        child = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, env=env)
        try:
            while child.poll() is None:
                if status_path and status_path.is_file():
                    status = read_json(status_path)
                    current = status.get("completed_frames")
                    if current is not None and current != last_frame:
                        last_frame = current
                        print(f"  Frames {current}/{status.get('total_frames')} | {status.get('elapsed_seconds', 0):.1f}s", flush=True)
                time.sleep(.25)
            require(child.returncode == 0, f"Process failed ({child.returncode}); see {log_path}")
        except KeyboardInterrupt:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
            raise
    return time.perf_counter() - started


def worker_payload(root, job, folder, mode, **extra):
    payload = {"root": str(root), "mode": mode, "job": job,
               "status_path": str(folder / "worker_status.json"),
               "cancel_path": str(folder / "cancel.request"), **extra}
    atomic_json(folder / "worker_payload.json", payload)
    (folder / "cancel.request").unlink(missing_ok=True)
    return folder / "worker_payload.json"


def build_episode(job, root, folder, tools, state):
    signature = fingerprint(job, root, "build")
    outputs = [item for step in job["build_steps"] for item in step.get("outputs", [])]
    record = state.get("build", {})
    if valid_build_record(record, signature, outputs, root):
        print("  Build already complete; validated output hashes.", flush=True)
        return
    record.update(status="running", fingerprint=signature)
    records = record.setdefault("steps", {})
    state["build"] = record
    atomic_json(folder / "state.json", state)
    for index, step in enumerate(job["build_steps"]):
        step_signature = step_fingerprint(job, step, root)
        step_record = records.get(str(index + 1), {})
        if valid_build_record(step_record, step_signature, step.get("outputs", []), root):
            print(f"  Build step {index + 1} already complete; validated input/output hashes.", flush=True)
            continue
        step_record = {"status": "running", "fingerprint": step_signature,
                       "seconds": float(step_record.get("seconds", 0)) if step_record.get("fingerprint") == step_signature else 0,
                       "attempts": int(step_record.get("attempts", 0)) + 1}
        records[str(index + 1)] = step_record
        atomic_json(folder / "state.json", state)
        environment = dict(os.environ, BLENDER_QUEUE_BUILD_ONLY="1", PRODUCTION_ROOT=str(root))
        started = time.perf_counter()
        try:
            if step.get("runner", "blender") == "python":
                command = [sys.executable, str(root / step["script"]), *step.get("args", [])]
            else:
                profile = step.get("blender_profile")
                blender = executable(tools["local"].get("blenders", {}).get(profile), [], root) if profile else tools["blender"]
                require(blender, f"Set a Blender executable for build step {index + 1}" + (f" (profile {profile})" if profile else ""))
                payload = worker_payload(root, job, folder, "build", step=step)
                command = [blender, "--background"]
                if step.get("blend"):
                    command.append(str(root / step["blend"]))
                command.extend(["--python-exit-code", "1", "--python", str(root / "tools/blender_queue_worker.py"), "--", str(payload)])
            run_process(command, folder / f"build_{index + 1:02d}_attempt_{step_record['attempts']:02d}.log", root, env=environment)
            for output in step.get("outputs", []):
                require((root / output).is_file(), f"Build did not produce declared output: {output}")
            step_record.update(status="complete", finished_utc=stamp(),
                               output_hashes={name: digest(root / name) for name in step.get("outputs", [])})
        except (Exception, KeyboardInterrupt):
            step_record["status"], record["status"] = "interrupted", "interrupted"
            raise
        finally:
            step_record["seconds"] += time.perf_counter() - started
            record["seconds"] = sum(value.get("seconds", 0) for value in records.values())
            atomic_json(folder / "state.json", state)
    require((root / job["blend"]).is_file(), f"Build project is missing: {job['blend']}")
    record.update(status="complete", fingerprint=fingerprint(job, root, "build"),
                  seconds=sum(value.get("seconds", 0) for value in records.values()), finished_utc=stamp(),
                  output_hashes={name: digest(root / name) for name in outputs})
    atomic_json(folder / "state.json", state)


def dispatch_mcp(root, payload, folder, timeout_seconds):
    """Bridge reply only acknowledges dispatch. Actual completion comes from disk."""
    status_path, cancel_path = folder / "worker_status.json", folder / "cancel.request"
    worker = str(root / "tools/blender_queue_worker.py")
    code = (
        "import bpy, runpy\n"
        f"_queue_worker={worker!r}\n_queue_payload={str(payload)!r}\n"
        "def _queue_start():\n"
        "    runpy.run_path(_queue_worker, init_globals={'QUEUE_PAYLOAD_PATH':_queue_payload}, run_name='__queue_mcp__')\n"
        "    return None\n"
        "bpy.app.timers.register(_queue_start, first_interval=0.25)\n"
        "print('PRODUCTION_QUEUE_ACCEPTED')\n"
    )
    started, buffer = time.perf_counter(), b""
    with socket.create_connection(("127.0.0.1", 9876), timeout=10) as bridge:
        bridge.settimeout(10)
        bridge.sendall(json.dumps({"type": "execute_code", "params": {"code": code}}).encode())
        try:
            while True:
                chunk = bridge.recv(65536)
                require(chunk, "MCP bridge disconnected before acknowledging the job")
                buffer += chunk
                try:
                    reply = json.loads(buffer)
                    break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    require(len(buffer) < 4 * 1024 * 1024, "Oversized MCP acknowledgment")
            require(reply.get("status") == "success", f"MCP rejected job: {reply}")
        except socket.timeout as exc:
            # A received transport timeout never counts as completion or retries.
            raise QueueError("MCP acknowledgment timed out; inspect worker_status.json before rerunning") from exc
    (folder / "mcp_acknowledgment.json").write_text(json.dumps(reply, indent=2), encoding="utf-8")
    last_frame = None
    try:
        while time.perf_counter() - started < timeout_seconds:
            status = read_json(status_path, {})
            if status.get("state") == "complete":
                return time.perf_counter() - started
            require(status.get("state") not in {"failed", "cancelled"}, f"MCP worker stopped: {status.get('error', status)}")
            current = status.get("completed_frames")
            if current is not None and current != last_frame:
                last_frame = current
                print(f"  MCP frames {current}/{status.get('total_frames')}", flush=True)
            time.sleep(1)
        cancel_path.write_text("timeout\n", encoding="utf-8")
        raise QueueError("MCP job exceeded its explicit deadline; cancellation requested after the current frame")
    except KeyboardInterrupt:
        cancel_path.write_text("interrupted\n", encoding="utf-8")
        print("MCP cancellation requested; it takes effect after the current frame.", flush=True)
        raise


def render_episode(job, root, folder, tools, state, args):
    require((root / job["blend"]).is_file(), "Render requires the built .blend; run build first")
    signature = fingerprint(job, root, "render")
    record = state.get("render", {})
    status = read_json(folder / "worker_status.json", {})
    require(status.get("state") != "running" or not is_process_alive(status.get("pid")),
            f"An existing Blender worker is still active (PID {status.get('pid')}); do not start another GPU job")
    # Existing images belong to this exact input only when the stage fingerprint matches.
    missing = missing_frames(root, job, record.get("frame_hashes"), record.get("status") == "complete") if record.get("fingerprint") == signature else list(range(
        job["frame_start"], job["frame_end"] + 1))
    if not missing:
        require(record.get("gpu") and job["gpu_name"].lower() in record["gpu"].lower(),
                "Completed frame record is missing the required GPU evidence")
        print("  Render already complete; validated every PNG.", flush=True)
        return
    previous_hashes = record.get("frame_hashes", {}) if record.get("fingerprint") == signature else {}
    record = {"status": "running", "fingerprint": signature, "frame_hashes": previous_hashes,
              "seconds": float(record.get("seconds", 0)) if record.get("fingerprint") == signature else 0,
              "attempts": int(record.get("attempts", 0)) + 1,
              "started_utc": stamp()}
    state["render"] = record
    atomic_json(folder / "state.json", state)
    (root / job["frames_dir"]).mkdir(parents=True, exist_ok=True)
    (folder / "worker_status.json").unlink(missing_ok=True)
    payload = worker_payload(root, job, folder, "render", frames=missing)
    attempt_started = time.perf_counter()
    try:
        if args.backend == "mcp":
            dispatch_mcp(root, payload, folder, args.mcp_timeout)
        else:
            profile = job.get("blender_profile")
            blender = executable(tools["local"].get("blenders", {}).get(profile), [], root) if profile else tools["blender"]
            require(blender, "Set --blender, BLENDER_EXECUTABLE, or config/local.json" + (f" profile {profile}" if profile else ""))
            run_process([blender, "--background", str(root / job["blend"]),
                         "--python-exit-code", "1", "--python", str(root / "tools/blender_queue_worker.py"),
                         "--", str(payload)], folder / f"render_{record['attempts']:02d}.log", root,
                        status_path=folder / "worker_status.json")
        status = read_json(folder / "worker_status.json")
        require(status.get("state") == "complete", f"Blender did not report completion: {status}")
        require(not missing_frames(root, job), "Rendered frame sequence failed integrity verification")
        require(job["gpu_name"].lower() in status.get("gpu", "").lower(), "Wrong GPU renderer")
        record.update(status="complete", gpu=status["gpu"], finished_utc=stamp(),
                      seconds=record["seconds"] + status["elapsed_seconds"],
                      frame_hashes={str(number): digest(frame_path(root, job, number)) for number in range(
                          job["frame_start"], job["frame_end"] + 1)})
    except (Exception, KeyboardInterrupt):
        status = read_json(folder / "worker_status.json", {})
        record["frame_hashes"].update(status.get("frame_hashes", {}))
        record.update(status="interrupted", seconds=record["seconds"] + time.perf_counter() - attempt_started)
        raise
    finally:
        atomic_json(folder / "state.json", state)


def probe_video(path, job, ffprobe):
    require(path.is_file() and path.stat().st_size > 0, f"Missing video: {path}")
    data = json.loads(subprocess.check_output([ffprobe, "-v", "error", "-count_frames", "-show_streams",
                                              "-show_format", "-of", "json", str(path)], text=True))
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    require(video and [video["width"], video["height"]] == job["resolution"], "Wrong video resolution")
    numerator, denominator = map(int, video["avg_frame_rate"].split("/"))
    require(denominator and abs(numerator / denominator - job["fps"]) < 1e-7, "Wrong video fps")
    require(int(video.get("nb_read_frames", video.get("nb_frames", 0))) == job["frame_count"], "Wrong video frame count")
    require(video["codec_name"] == "h264" and video["pix_fmt"] == "yuv420p", "Expected H.264/yuv420p")
    require(abs(float(data["format"]["duration"]) - job["duration_seconds"]) < .08, "Wrong video duration")
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    require(bool(audio) == bool(job.get("audio")), "Unexpected audio presence/absence")
    if audio:
        require(audio["codec_name"] == "aac" and int(audio["sample_rate"]) == 48000, "Expected AAC/48kHz audio")
    return data


def encode_episode(job, root, folder, tools, state):
    require(tools["ffmpeg"] and tools["ffprobe"], "Encoding needs FFmpeg and FFprobe with h264_nvenc support")
    require(not missing_frames(root, job), "Encode requires a complete valid PNG sequence")
    target = root / job["video"]
    signature = fingerprint(job, root, "encode")
    record = state.get("encode", {})
    if record.get("status") == "complete" and record.get("fingerprint") == signature and target.is_file() and record.get("sha256") == digest(target):
        probe_video(target, job, tools["ffprobe"])
        print("  Encode already complete; validated MP4 and hash.", flush=True)
        return
    require(not target.exists(), f"Existing video does not match this queue's completed fingerprint: {target}; choose a new version path")
    encoders = subprocess.check_output([tools["ffmpeg"], "-hide_banner", "-encoders"], stderr=subprocess.STDOUT, text=True)
    require("h264_nvenc" in encoders, "This FFmpeg lacks h264_nvenc; install/configure a compatible build")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.stem + ".partial.mp4")
    command = [tools["ffmpeg"], "-hide_banner", "-y", "-framerate", str(job["fps"]),
               "-start_number", str(job["frame_start"]), "-i",
               str(root / job["frames_dir"] / f"{job['frame_prefix']}_%06d.png")]
    if job.get("audio"):
        command.extend(["-i", str(root / job["audio"]), "-map", "0:v:0", "-map", "1:a:0"])
    command.extend(["-frames:v", str(job["frame_count"]), "-t", str(job["duration_seconds"]),
                    "-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "18", "-b:v", "0",
                    "-pix_fmt", "yuv420p"])
    if job.get("audio"):
        command.extend(["-af", "apad", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2"])
    else:
        command.append("-an")
    command.extend(["-movflags", "+faststart", str(temporary)])
    elapsed = run_process(command, folder / "encode.log", root)
    probe = probe_video(temporary, job, tools["ffprobe"])
    run_process([tools["ffmpeg"], "-v", "error", "-xerror", "-i", str(temporary), "-f", "null", "-"],
                folder / "decode_check.log", root)
    temporary.replace(target)
    state["encode"] = {"status": "complete", "fingerprint": signature, "seconds": elapsed,
                       "sha256": digest(target), "finished_utc": stamp(), "video": job["video"]}
    atomic_json(folder / "probe.json", probe)
    atomic_json(folder / "state.json", state)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "dry-run", "build", "render", "run"])
    parser.add_argument("queue", nargs="?", default="queue/pending.queue.json")
    parser.add_argument("--blender")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    parser.add_argument("--backend", choices=["subprocess", "mcp"], default="subprocess")
    parser.add_argument("--mcp-timeout", type=float, default=24 * 3600, help="Explicit MCP job deadline in seconds")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args(argv)
    root = ROOT.resolve()
    path = relative_path(root, args.queue, "queue")
    jobs = validate(read_json(path), root)
    print(f"Validated {len(jobs)} episode(s): 1080x1920, 24fps; captions require visual QA.", flush=True)
    if args.command in {"validate", "dry-run"}:
        if args.command == "dry-run":
            for job in jobs:
                print(f"{job['id']}: {len(job['build_steps'])} build step(s), {job['frame_count']} frames, "
                      f"{job['engine']} on {job['gpu_name']} -> {job['video']}")
                for step in job["build_steps"]:
                    print(f"  Build {step.get('runner', 'blender')}: {step['script']} {step.get('args', [])}")
        return 0
    if not jobs:
        print("Queue is empty; no work started.")
        return 0
    tools = tool_paths(args, root)
    failed, reports = [], []
    with QueueLock(root):
        # A restarted controller must not collide with an orphaned/live MCP job from any queue.
        for previous in (root / "queue/.runs").glob("*/*/worker_status.json"):
            status = read_json(previous, {})
            require(status.get("state") != "running" or not is_process_alive(status.get("pid")),
                    f"GPU worker still active; inspect {previous} before restarting")
        for job in jobs:
            folder = root / "queue/.runs" / path.stem / job["id"]
            folder.mkdir(parents=True, exist_ok=True)
            state = read_json(folder / "state.json", {})
            print(f"\n{job['id']} ({job['duration_seconds']}s video)", flush=True)
            try:
                if args.command in {"build", "run"}:
                    build_episode(job, root, folder, tools, state)
                if args.command in {"render", "run"}:
                    target, encoded = root / job["video"], state.get("encode", {})
                    require(not target.exists() or (encoded.get("status") == "complete"
                            and encoded.get("fingerprint") == fingerprint(job, root, "encode")
                            and encoded.get("sha256") == digest(target)),
                            f"Existing video is protected: {job['video']}; choose a new version path")
                    render_episode(job, root, folder, tools, state, args)
                    encode_episode(job, root, folder, tools, state)
                report = {"id": job["id"], "status": "build_ready" if args.command == "build" else "complete",
                          "stage": args.command, "video_seconds": job["duration_seconds"],
                          "build_seconds": state.get("build", {}).get("seconds", 0),
                          "render_seconds": state.get("render", {}).get("seconds", 0),
                          "encode_seconds": state.get("encode", {}).get("seconds", 0),
                          "gpu": state.get("render", {}).get("gpu"), "video": job["video"] if args.command != "build" else None,
                          "video_exists": (root / job["video"]).is_file() if args.command != "build" else False,
                          "finished_utc": stamp()}
                atomic_json(folder / "delivery.json", report)
                reports.append(report)
                print(f"  Build {report['build_seconds']:.1f}s | render {report['render_seconds']:.1f}s | "
                      f"encode {report['encode_seconds']:.1f}s", flush=True)
            except Exception as exc:
                failed.append(job["id"])
                atomic_json(folder / "failure.json", {"id": job["id"], "error": str(exc), "failed_utc": stamp()})
                print(f"ERROR {job['id']}: {exc}", file=sys.stderr, flush=True)
                if not args.continue_on_error:
                    break
    atomic_json(root / "queue/.runs" / path.stem / "summary.json", {"episodes": reports, "failed": failed})
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except QueueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("Queue interrupted. Re-run the same command to resume validated frames.", file=sys.stderr)
        raise SystemExit(130)
