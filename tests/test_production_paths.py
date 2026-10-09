"""Meaningful path-discovery checks; safe on cloud hosts without Blender."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.production_paths import RuntimePaths


class RuntimePathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_discovery_requires_no_installed_blender(self):
        paths = RuntimePaths(self.root, environ={"PATH": ""})
        with patch("pathlib.Path.is_file", return_value=False), patch("shutil.which", return_value=None):
            self.assertIsNone(paths.resolve_tool("blender", required=False))
        self.assertEqual(paths.repo_path("tools/new_episode.py"), self.root / "tools/new_episode.py")

    def test_relative_local_override_survives_checkout_relocation(self):
        (self.root / "config").mkdir()
        executable = self.root / "runtime" / "blender"
        executable.parent.mkdir()
        executable.write_text("placeholder", encoding="utf-8")
        (self.root / "config/local.json").write_text(
            json.dumps({"blender_exe": "runtime/blender"}), encoding="utf-8"
        )
        discovered = RuntimePaths.discover(self.root)
        paths = RuntimePaths(discovered.root, discovered.local, {"PATH": ""})
        self.assertEqual(paths.resolve_tool("blender"), executable)

    def test_environment_has_precedence_over_local_settings(self):
        local_file = self.root / "local-tool"
        env_file = self.root / "env-tool"
        for path in (local_file, env_file):
            path.touch()
        paths = RuntimePaths(self.root, {"ffmpeg_exe": "local-tool"},
                             {"FFMPEG_EXE": "env-tool", "PATH": ""})
        self.assertEqual(paths.resolve_tool("ffmpeg"), env_file)

    def test_bad_explicit_override_does_not_silently_choose_another_tool(self):
        paths = RuntimePaths(self.root, environ={"BLENDER_EXE": "missing", "PATH": ""})
        with self.assertRaisesRegex(FileNotFoundError, "BLENDER_EXECUTABLE"):
            paths.resolve_tool("blender", required=False)

    def test_canonical_environment_override_precedes_legacy_alias(self):
        canonical, legacy = self.root / "canonical", self.root / "legacy"
        canonical.touch()
        legacy.touch()
        paths = RuntimePaths(self.root, environ={"BLENDER_EXECUTABLE": "canonical",
                                                "BLENDER_EXE": "legacy", "PATH": ""})
        self.assertEqual(paths.resolve_tool("blender"), canonical)

    def test_repository_paths_cannot_escape(self):
        paths = RuntimePaths(self.root, environ={})
        with self.assertRaises(ValueError):
            paths.repo_path("../outside.blend")

    def test_invalid_configuration_has_an_actionable_error(self):
        (self.root / "config").mkdir()
        (self.root / "config/local.json").write_text('{"font_file": 3}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "font_file"):
            RuntimePaths.discover(self.root)

    def test_font_override_is_portable(self):
        font = self.root / "my-bold.ttf"
        font.touch()
        paths = RuntimePaths(self.root, {"font_file": "my-bold.ttf"}, {"PATH": ""})
        self.assertEqual(paths.resolve_font_path(), font)


if __name__ == "__main__":
    unittest.main()
