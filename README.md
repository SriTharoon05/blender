# Blender shorts production

An existing Blender production library, episode source scripts and a portable workflow for preparing episodes in Codex Cloud, then rendering them sequentially on the home laptop.

**Current 2D defaults:** native Grease Pencil, the approved recurring character, 1080 x 1920 vertical, 24 fps, Eevee on the GTX 1650 Ti. Captions stay near the top: main lettering and outline inside y=300–480 px, optional tag y=500–548 px. Read [AGENTS.md](AGENTS.md) and [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md) for the complete production rules.

## Prepare remotely, render at home

1. Connect this GitHub repository to a Codex Cloud environment. Use the [setup instructions and task prompt](docs/CLOUD_WORKFLOW.md).
2. Have cloud tasks prepare a new `.py` episode builder using `bpy`, its audio/cue sheet and a queue item. Cloud authoring works independently of a powered-off PC. Creating a `.blend` there additionally requires a compatible Blender installation and the source assets.
3. Review and commit the new work in GitHub. Pull it on the laptop.
4. Validate and inspect the batch, build projects, review representative frames, then render one episode at a time.

```sh
python tools/validate_repository.py
python tools/production_queue.py validate queue/pending.queue.json
python tools/production_queue.py dry-run queue/pending.queue.json
python tools/production_queue.py build queue/pending.queue.json
python tools/production_queue.py render queue/pending.queue.json
```

The initial pending queue is empty; adding 10–20 new episode entries makes a batch. `run` performs build plus render; `build` stops after preparing projects. `--backend mcp` is available for local rendering through an active Blender bridge. The ordinary subprocess backend can render the same queue without MCP. Configure local executables first as described below.

## Portable setup

Use Python 3.11+ for the queue and dependency-free tooling. Scene builders run inside Blender, not an ordinary Python interpreter. Native Grease Pencil authoring targets **Blender 5.2.2**; API/version compatibility matters.

For original sound synthesis, image QA or legacy physics work, install the optional NumPy, Pillow and SciPy dependencies:

```sh
python -m pip install -r requirements-cloud.txt
```

The repository and queue validators do not need those packages. Blender supplies `bpy` when running scene scripts; do not replace that runtime with an unrelated pip package.

Copy `config/local.example.json` to the ignored `config/local.json`, then supply local Blender, FFmpeg, FFprobe and optional font paths. Environment overrides are `BLENDER_EXECUTABLE`, `FFMPEG_EXECUTABLE` and `FFPROBE_EXECUTABLE`; command flags override executable selection too. Nothing in the public configuration contains a user's absolute filesystem paths or credentials.

Existing template/project font data is packed. Reuse that data when possible; newly generated lettering needs a suitable installed bold font. Do not upload a standalone proprietary Windows font. See the cloud guide for font substitutions and the local Cycles plate compatibility note.

To try the portable build-only example with an unused output path:

```sh
blender --background --python examples/minimal_2d_episode.py -- --output 02_EPISODES/EP_DEMO_Portable/blend/EP_DEMO_v001.blend --duration 2
```

This demonstrates the approved character and caption helpers; it creates an editable project without rendering and refuses to overwrite an existing file.

## Repository contents

| Location | Purpose |
| --- | --- |
| `00_LIBRARY/` | Approved reusable characters, props, environments and caption layout |
| `01_TEMPLATES/` | Saved production masters; copy before editing |
| `02_EPISODES/` | Episode source projects, audio, plate assets and production metadata |
| `tools/` | Existing production scripts plus portable paths/toolkit and batch runner |
| `examples/` | Minimal build-only example for future portable episodes |
| `config/` | Committed production defaults and an empty local configuration example |
| `queue/` | Empty pending batch and a reference manifest |
| `docs/` | Cloud authoring, local validation and render workflow |

Generated movie files, render frame sequences, simulation caches, runtime bundles and machine-specific configuration are kept locally rather than in source control. Historical scripts preserve their original behavior and may contain Windows-specific assumptions; use the portable helpers for new work.

Every final delivery records **video duration, actual render elapsed time and encoding time separately**. Hybrid episodes also record the static-plate render time. Cloud syntax/queue checks are useful preparation; final visual and audio review still happens on rendered output.
