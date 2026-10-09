"""Portable, standard-library-only discovery for cloud authoring and home renders.

Importing this module never requires Blender, creates files, or starts a process.
Machine-specific overrides belong in ignored ``config/local.json`` or environment
variables. Relative overrides are resolved against the repository root.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import shutil
from typing import Mapping


_ENV_KEYS = {
    "blender": "BLENDER_EXECUTABLE",
    "ffmpeg": "FFMPEG_EXECUTABLE",
    "ffprobe": "FFPROBE_EXECUTABLE",
}


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    local: Mapping[str, str] = field(default_factory=dict)
    environ: Mapping[str, str] = field(default_factory=lambda: dict(os.environ), repr=False)

    @classmethod
    def discover(cls, root: str | Path | None = None) -> "RuntimePaths":
        root_path = Path(root or Path(__file__).resolve().parents[1]).resolve()
        config_path = root_path / "config" / "local.json"
        local = json.loads(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {}
        if not isinstance(local, dict):
            raise ValueError(f"Expected a JSON object in {config_path}")
        for key in (*[f"{tool}_exe" for tool in _ENV_KEYS], "font_file"):
            if key in local and not isinstance(local[key], str):
                raise ValueError(f"{key} must be a path string in {config_path}")
        return cls(root_path, local)

    def repo_path(self, relative: str | Path, *, must_exist: bool = False) -> Path:
        """Resolve a repository path and reject traversal outside the checkout."""
        result = (self.root / relative).resolve()
        if not result.is_relative_to(self.root):
            raise ValueError(f"Path is outside the repository: {relative}")
        if must_exist and not result.exists():
            raise FileNotFoundError(result)
        return result

    def _override(self, value: str, label: str, *, executable: bool) -> Path:
        expanded = Path(os.path.expandvars(value)).expanduser()
        candidate = expanded if expanded.is_absolute() else self.root / expanded
        if candidate.is_file():
            return candidate.resolve()
        if executable and len(expanded.parts) == 1:
            found = shutil.which(value, path=self.environ.get("PATH", ""))
            if found:
                return Path(found).resolve()
        raise FileNotFoundError(f"{label} points to an unavailable file: {value}")

    def resolve_tool(self, tool: str, *, required: bool = True) -> Path | None:
        """Find a tool without running it; explicit invalid overrides fail loudly."""
        if tool not in _ENV_KEYS:
            raise ValueError(f"Unknown production tool: {tool}")
        env_key = _ENV_KEYS[tool]
        configured = (self.environ.get(env_key) or self.environ.get(f"{tool.upper()}_EXE")
                      or self.local.get(f"{tool}_exe"))
        if configured:
            return self._override(configured, env_key, executable=True)

        suffix = ".exe" if os.name == "nt" else ""
        candidates = []
        if tool == "blender" and os.name == "nt":
            program_files = Path(self.environ.get("ProgramFiles", "C:/Program Files"))
            candidates.extend(program_files / "Blender Foundation" / f"Blender {v}" / "blender.exe"
                              for v in ("5.2", "5.1", "5.0", "4.5", "4.2"))
        elif tool in ("ffmpeg", "ffprobe"):
            # Retain compatibility with the installed GTX 1650 Ti driver.
            candidates.append(self.root / "tools/vendor/ffmpeg611/ffmpeg-6.1.1-essentials_build/bin"
                              / f"{tool}{suffix}")
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        found = shutil.which(tool, path=self.environ.get("PATH", ""))
        if found:
            return Path(found).resolve()
        if required:
            raise FileNotFoundError(
                f"{tool} is not installed here. Set {env_key} or config/local.json "
                f"{tool}_exe. Cloud authoring does not require a render runtime."
            )
        return None

    def resolve_font_path(self) -> Path | None:
        """Find a bold font; Blender helpers prefer an already packed Arial Black."""
        configured = self.environ.get("BLENDER_FONT_FILE") or self.local.get("font_file")
        if configured:
            return self._override(configured, "BLENDER_FONT_FILE", executable=False)
        candidates = (
            Path("C:/Windows/Fonts/ariblk.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Black.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        )
        return next((path.resolve() for path in candidates if path.is_file()), None)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
