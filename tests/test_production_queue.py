"""Stdlib orchestration tests; no GPU, Blender install, or media render is required."""

import binascii
import importlib.util
import json
import os
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import production_queue as queue

spec = importlib.util.spec_from_file_location("queue_worker", ROOT / "tools/blender_queue_worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def png(path, width=1080, height=1920):
    def chunk(kind, value):
        return struct.pack(">I", len(value)) + kind + value + struct.pack(">I", binascii.crc32(kind + value) & 0xffffffff)
    value = b"\x89PNG\r\n\x1a\n"
    value += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    value += chunk(b"IDAT", zlib.compress((b"\x00" + b"\x00" * width * 3) * height))
    value += chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "input.blend").write_bytes(b"BLENDER test fixture")
        self.source = {"id": "EP009_Test", "blend": "input.blend", "duration_seconds": 1 / 12,
                       "frames_dir": "episode/frames", "frame_prefix": "EP009",
                       "video": "outputs/test.mp4", "audio": None, "build_steps": []}
        self.job = queue.validate({"version": 1, "episodes": [self.source]}, self.root)[0]
        self.folder = self.root / "queue/.runs/test/EP009_Test"
        self.folder.mkdir(parents=True)
        self.args = SimpleNamespace(backend="subprocess", mcp_timeout=60)
        self.tools = {"blender": "fake-blender", "local": {}}

    def tearDown(self):
        self.temporary.cleanup()

    def fake_render(self, command, log_path, root, status_path=None, env=None):
        payload = queue.read_json(self.folder / "worker_payload.json")
        for number in payload["frames"]:
            png(queue.frame_path(root, self.job, number))
        queue.atomic_json(status_path, {"state": "complete", "pid": os.getpid(),
                                        "gpu": "NVIDIA GeForce GTX 1650 Ti", "elapsed_seconds": 1.25,
                                        "completed_frames": len(payload["frames"]), "total_frames": len(payload["frames"])})
        return 1.5

    def test_paths_and_settings_are_portable_and_current(self):
        for bad in ("../outside.blend", "/tmp/outside.blend", "C:/outside.blend", "C:outside.blend", "some\\file.blend"):
            with self.subTest(path=bad), self.assertRaises(queue.QueueError):
                queue.relative_path(self.root, bad, "fixture")
        for overrides in ({"fps": 60}, {"resolution": [720, 1080]}, {"duration_seconds": .01}):
            source = dict(self.source, **overrides)
            with self.subTest(overrides=overrides), self.assertRaises(queue.QueueError):
                queue.validate({"version": 1, "episodes": [source]}, self.root)

    def test_future_project_can_be_declared_build_output(self):
        (self.root / "builder.py").write_text("print('build-only')", encoding="utf-8")
        source = dict(self.source, blend="future.blend", build_steps=[{
            "script": "builder.py", "outputs": ["future.blend"], "blender_profile": "cycles42"}])
        job = queue.validate({"version": 1, "episodes": [source]}, self.root)[0]
        self.assertEqual(job["build_steps"][0]["blender_profile"], "cycles42")

    def test_png_integrity_detects_incomplete_and_corrupt_frames(self):
        path = self.root / "frame.png"
        png(path)
        self.assertTrue(queue.verify_png(path, 1080, 1920))
        self.assertFalse(queue.verify_png(path, 1920, 1080))
        complete = path.read_bytes()
        path.write_bytes(complete[:-1])
        self.assertFalse(queue.verify_png(path, 1080, 1920))
        damaged = bytearray(complete)
        damaged[45] ^= 1
        path.write_bytes(damaged)
        self.assertFalse(queue.verify_png(path, 1080, 1920))

    def test_fresh_build_process_per_step_and_hash_checked_resume(self):
        steps = []
        for index in (1, 2):
            script = f"step{index}.py"
            body = "import os\nfrom pathlib import Path\nassert os.environ['BLENDER_QUEUE_BUILD_ONLY']=='1'\n"
            body += f"Path('pid{index}.txt').write_text(str(os.getpid()))\n"
            (self.root / script).write_text(body, encoding="utf-8")
            steps.append({"script": script, "runner": "python", "outputs": [f"pid{index}.txt"]})
        job, state = dict(self.job, build_steps=steps), {}
        queue.build_episode(job, self.root, self.folder, self.tools, state)
        self.assertNotEqual((self.root / "pid1.txt").read_text(), (self.root / "pid2.txt").read_text())
        with patch.object(queue, "run_process", side_effect=AssertionError("should resume")):
            queue.build_episode(job, self.root, self.folder, self.tools, state)
        (self.root / "pid1.txt").write_text("corrupt", encoding="utf-8")
        with patch.object(queue, "run_process", wraps=queue.run_process) as calls:
            queue.build_episode(job, self.root, self.folder, self.tools, state)
            self.assertEqual(calls.call_count, 1)

    def test_retry_skips_successful_immutable_step_after_later_failure(self):
        (self.root / "first.py").write_text(
            "from pathlib import Path\nwith Path('immutable.txt').open('x') as output: output.write('first build')\n",
            encoding="utf-8")
        (self.root / "second.py").write_text(
            "from pathlib import Path\nimport sys\n"
            "if not Path('failed_once').exists():\n"
            "    Path('failed_once').write_text('yes')\n    sys.exit(1)\n"
            "Path('second.txt').write_text(Path('immutable.txt').read_text())\n", encoding="utf-8")
        steps = [{"script": "first.py", "runner": "python", "outputs": ["immutable.txt"]},
                 {"script": "second.py", "runner": "python", "inputs": ["immutable.txt"], "outputs": ["second.txt"]}]
        job, state = dict(self.job, build_steps=steps), {}
        with self.assertRaises(queue.QueueError):
            queue.build_episode(job, self.root, self.folder, self.tools, state)
        persisted = queue.read_json(self.folder / "state.json")
        self.assertEqual(persisted["build"]["steps"]["1"]["status"], "complete")
        self.assertEqual(persisted["build"]["steps"]["2"]["status"], "interrupted")
        with patch.object(queue, "run_process", wraps=queue.run_process) as calls:
            queue.build_episode(job, self.root, self.folder, self.tools, persisted)
        self.assertEqual(calls.call_count, 1)
        self.assertEqual((self.root / "second.txt").read_text(), "first build")
        self.assertEqual(persisted["build"]["steps"]["1"]["attempts"], 1)
        self.assertEqual(persisted["build"]["steps"]["2"]["attempts"], 2)

    def test_shared_helper_change_invalidates_build_cache(self):
        helper = self.root / "tools/grease_pencil_toolkit.py"
        helper.parent.mkdir()
        helper.write_text("VERSION=1\n", encoding="utf-8")
        (self.root / "builder.py").write_text("from pathlib import Path\nPath('built.txt').write_text('built')\n", encoding="utf-8")
        job, state = dict(self.job, build_steps=[{"script": "builder.py", "runner": "python", "outputs": ["built.txt"]}]), {}
        queue.build_episode(job, self.root, self.folder, self.tools, state)
        helper.write_text("VERSION=2\n", encoding="utf-8")
        with patch.object(queue, "run_process", wraps=queue.run_process) as calls:
            queue.build_episode(job, self.root, self.folder, self.tools, state)
        self.assertEqual(calls.call_count, 1)

    def test_declared_input_change_invalidates_only_dependent_step(self):
        (self.root / "notes.txt").write_text("old", encoding="utf-8")
        (self.root / "builder.py").write_text(
            "from pathlib import Path\nPath('built.txt').write_text(Path('notes.txt').read_text())\n", encoding="utf-8")
        job, state = dict(self.job, build_steps=[{"script": "builder.py", "runner": "python", "inputs": ["notes.txt"], "outputs": ["built.txt"]}]), {}
        queue.build_episode(job, self.root, self.folder, self.tools, state)
        (self.root / "notes.txt").write_text("new", encoding="utf-8")
        with patch.object(queue, "run_process", wraps=queue.run_process) as calls:
            queue.build_episode(job, self.root, self.folder, self.tools, state)
        self.assertEqual(calls.call_count, 1)
        self.assertEqual((self.root / "built.txt").read_text(), "new")

    def test_atomic_json_retries_transient_windows_sharing_error(self):
        original, attempts = Path.replace, []
        def intermittent(path, target):
            attempts.append(target)
            if len(attempts) == 1:
                raise PermissionError("file briefly open in another reader")
            return original(path, target)
        target = self.root / "state.json"
        with patch.object(Path, "replace", intermittent), patch.object(queue.time, "sleep"):
            queue.atomic_json(target, {"status": "complete"})
        self.assertEqual(len(attempts), 2)
        self.assertEqual(queue.read_json(target)["status"], "complete")

    def test_resume_renders_only_missing_or_corrupt_images(self):
        state = {}
        with patch.object(queue, "run_process", side_effect=self.fake_render) as render:
            queue.render_episode(self.job, self.root, self.folder, self.tools, state, self.args)
            self.assertEqual(render.call_count, 1)
            queue.render_episode(self.job, self.root, self.folder, self.tools, state, self.args)
            self.assertEqual(render.call_count, 1)
            queue.frame_path(self.root, self.job, 2).write_bytes(b"interrupted PNG")
            queue.render_episode(self.job, self.root, self.folder, self.tools, state, self.args)
            self.assertEqual(queue.read_json(self.folder / "worker_payload.json")["frames"], [2])
            self.assertEqual(render.call_count, 2)
            self.assertEqual(state["render"]["seconds"], 2.5)

    def test_changed_blend_invalidates_cached_frames(self):
        state = {}
        with patch.object(queue, "run_process", side_effect=self.fake_render):
            queue.render_episode(self.job, self.root, self.folder, self.tools, state, self.args)
            (self.root / "input.blend").write_bytes(b"modified scene")
            queue.render_episode(self.job, self.root, self.folder, self.tools, state, self.args)
        self.assertEqual(queue.read_json(self.folder / "worker_payload.json")["frames"], [1, 2])

    def test_valid_png_replacement_is_detected_by_hash(self):
        state = {}
        with patch.object(queue, "run_process", side_effect=self.fake_render):
            queue.render_episode(self.job, self.root, self.folder, self.tools, state, self.args)
            path = queue.frame_path(self.root, self.job, 1)
            # A valid ancillary chunk changes the image file without breaking its PNG CRCs.
            complete = path.read_bytes()
            kind, value = b"tEXt", b"changed\x00outside renderer"
            chunk = struct.pack(">I", len(value)) + kind + value + struct.pack(">I", binascii.crc32(kind + value) & 0xffffffff)
            path.write_bytes(complete[:-12] + chunk + complete[-12:])
            self.assertTrue(queue.verify_png(path, 1080, 1920))
            queue.render_episode(self.job, self.root, self.folder, self.tools, state, self.args)
        self.assertEqual(queue.read_json(self.folder / "worker_payload.json")["frames"], [1])

    def test_live_worker_prevents_duplicate_gpu_process(self):
        queue.atomic_json(self.folder / "worker_status.json", {"state": "running", "pid": os.getpid()})
        with self.assertRaisesRegex(queue.QueueError, "still active"):
            queue.render_episode(self.job, self.root, self.folder, self.tools, {}, self.args)

    def test_gpu_checks_reject_software_renderer_and_disable_cycles_cpu(self):
        scene = SimpleNamespace(render=SimpleNamespace(engine="BLENDER_EEVEE"), cycles=SimpleNamespace(device="CPU"))
        cpu = SimpleNamespace(type="CPU", name="CPU", use=True)
        cuda = SimpleNamespace(type="CUDA", name="GeForce GTX 1650 Ti", use=False)
        prefs = SimpleNamespace(compute_device_type="NONE", devices=[cpu, cuda], get_devices=lambda: None)
        bpy = SimpleNamespace(context=SimpleNamespace(preferences=SimpleNamespace(addons={"cycles": SimpleNamespace(preferences=prefs)})))
        gpu = SimpleNamespace(platform=SimpleNamespace(renderer_get=lambda: "llvmpipe"))
        with patch.dict(sys.modules, bpy=bpy, gpu=gpu):
            with self.assertRaisesRegex(RuntimeError, "actual graphics renderer"):
                worker.render_gpu(scene, "GTX 1650 Ti")
            gpu.platform.renderer_get = lambda: "NVIDIA GeForce GTX 1650 Ti"
            scene.render.engine = "CYCLES"
            actual = worker.render_gpu(scene, "GTX 1650 Ti", "CUDA")
        self.assertIn("Cycles CUDA", actual)
        self.assertFalse(cpu.use)
        self.assertTrue(cuda.use)
        self.assertEqual(scene.cycles.device, "GPU")

    def test_build_guard_blocks_render_but_preserves_save_operator(self):
        original = SimpleNamespace(render=SimpleNamespace(render=lambda: "rendered"), wm="save operators")
        guard = worker.NoRenderOps(original)
        self.assertEqual(guard.wm, "save operators")
        with self.assertRaisesRegex(RuntimeError, "Build-only"):
            guard.render.render()

    def test_cli_dry_run_does_not_load_tools_or_start_blender(self):
        queue.atomic_json(self.root / "queue/pending.queue.json", {"version": 1, "episodes": [self.source]})
        with patch.object(queue, "ROOT", self.root), patch.object(queue, "tool_paths", side_effect=AssertionError("tools not needed")):
            self.assertEqual(queue.main(["validate"]), 0)
            self.assertEqual(queue.main(["dry-run"]), 0)

    def test_fail_stop_and_explicit_continue(self):
        second = dict(self.source, id="EP010_Test", frames_dir="second/frames", video="outputs/second.mp4")
        queue.atomic_json(self.root / "queue/pending.queue.json", {"version": 1, "episodes": [self.source, second]})
        for flags, expected in (([], 1), (["--continue-on-error"], 2)):
            with patch.object(queue, "ROOT", self.root), patch.object(queue, "tool_paths", return_value=self.tools), \
                    patch.object(queue, "render_episode", side_effect=queue.QueueError("GPU unavailable")) as render:
                self.assertEqual(queue.main(["render", *flags]), 1)
                self.assertEqual(render.call_count, expected)

    def test_existing_video_is_protected_before_render(self):
        target = self.root / self.job["video"]
        target.parent.mkdir(parents=True)
        target.write_bytes(b"approved output")
        queue.atomic_json(self.root / "queue/pending.queue.json", {"version": 1, "episodes": [self.source]})
        with patch.object(queue, "ROOT", self.root), patch.object(queue, "tool_paths", return_value=self.tools), \
                patch.object(queue, "render_episode", side_effect=AssertionError("must not render")) as render:
            self.assertEqual(queue.main(["render"]), 1)
            self.assertFalse(render.called)
        self.assertEqual(target.read_bytes(), b"approved output")

    def test_build_only_report_does_not_claim_video_delivery(self):
        queue.atomic_json(self.root / "queue/pending.queue.json", {"version": 1, "episodes": [self.source]})
        with patch.object(queue, "ROOT", self.root), patch.object(queue, "tool_paths", return_value=self.tools):
            self.assertEqual(queue.main(["build"]), 0)
        report = queue.read_json(self.root / "queue/.runs/pending.queue/EP009_Test/delivery.json")
        self.assertEqual(report["status"], "build_ready")
        self.assertIsNone(report["video"])
        self.assertFalse(report["video_exists"])

    def test_local_executable_paths_resolve_from_repository_root(self):
        executable = self.root / "runtime/blender.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"executable fixture")
        self.assertEqual(queue.executable("runtime/blender.exe", [], self.root), str(executable))

    def test_mcp_waits_for_status_after_timer_dispatch(self):
        queue.atomic_json(self.folder / "worker_status.json", {"state": "complete"})
        bridge = SimpleNamespace(settimeout=lambda *_: None, sendall=lambda value: sent.append(json.loads(value)),
                                 recv=lambda *_: b'{"status":"success","result":"accepted"}')
        sent = []
        class Connection:
            def __enter__(self):
                return bridge
            def __exit__(self, *_):
                pass
        with patch.object(queue.socket, "create_connection", return_value=Connection()):
            queue.dispatch_mcp(self.root, self.folder / "payload.json", self.folder, 60)
        self.assertIn("bpy.app.timers.register", sent[0]["params"]["code"])
        self.assertNotIn("bpy.ops.render.render", sent[0]["params"]["code"])

    def test_cycles_optix_gpu_is_selected_without_cpu_fallback(self):
        scene = SimpleNamespace(render=SimpleNamespace(engine="CYCLES"), cycles=SimpleNamespace(device="CPU"))
        cpu = SimpleNamespace(type="CPU", name="CPU", use=True)
        optix = SimpleNamespace(type="OPTIX", name="GeForce GTX 1650 Ti", use=False)
        prefs = SimpleNamespace(compute_device_type="NONE", devices=[cpu, optix], get_devices=lambda: None)
        bpy = SimpleNamespace(context=SimpleNamespace(preferences=SimpleNamespace(addons={"cycles": SimpleNamespace(preferences=prefs)})))
        with patch.dict(sys.modules, bpy=bpy):
            self.assertIn("OPTIX", worker.render_gpu(scene, "GTX 1650 Ti", "OPTIX"))
        self.assertFalse(cpu.use)
        self.assertTrue(optix.use)


if __name__ == "__main__":
    unittest.main()
