# Cloud authoring and local batch rendering

Prepare episode source while the home PC is off, then use its GPU when it is back on. Blender scripts normally end in **`.py`** and import **`bpy`**; the editable Blender output ends in **`.blend`**.

## Set up Codex Cloud

On the web or desktop app, choose **Work in > Cloud > Select environment > Create environment**. Select `SriTharoon05/blender`, connect GitHub if prompted, and select **Get started**. Ask setup to provide Python 3.11+, test the repository's checks and preserve the approved production assets. Review the setup, save changes and **Publish**. Start a task from the published environment. Codex also supports selecting a published environment on mobile. [Official cloud setup](https://learn.chatgpt.com/docs/environments/cloud-environments)

Ask setup to run:

```sh
python --version
python tools/validate_repository.py
python tools/production_queue.py validate queue/pending.queue.json
python tools/production_queue.py dry-run queue/pending.queue.json
python -m unittest discover -s tests -p "test_*.py"
```

Those checks use ordinary Python and do not require a GPU. The repository validator checks syntax, production settings, required files and approved-asset hashes; keep the inventory unchanged unless intentionally updating approved assets. If a check or required asset fails, fix setup before publishing. If large source assets are represented by Git LFS pointers, install Git LFS and retrieve their contents first. Do not mistake a pointer file for a `.blend` asset.

For optional original audio synthesis, image QA and legacy physics scripts, ask setup to install the declared NumPy, Pillow and SciPy dependencies:

```sh
python -m pip install -r requirements-cloud.txt
```

These packages are not required for the standard-library validation checks. Scene execution needs the matching Blender runtime, which supplies `bpy`; do not pip-install `bpy` as a substitute. Installing these dependencies here is a cloud setup instruction, not a claim that the environment has already been configured.

Do not assume Blender, NVIDIA GPU/NVENC, a graphical display or the local Blender MCP bridge is present in a cloud environment. The official setup workflow lets you request and test required tools; it does not promise this repository's renderer or your home hardware. A suitable Blender installation may build `.blend` files in cloud, but a different version can break native GP/compositor APIs. Plain Python can validate syntax and queue data without importing `bpy`. Reserve full rendering for the local GPU workflow unless a different capable render machine is explicitly configured.

Cloud tasks have separate workspaces. Commit completed episode sources or open a pull request so they reach GitHub; saved cloud task state alone does not transfer work to the laptop. Review and merge parallel tasks before pulling the batch. Assign distinct episode IDs to concurrent tasks and resolve queue-file conflicts when combining them. [Official cloud workflow and saved state](https://learn.chatgpt.com/docs/cloud)

## Prompt for each new episode

Paste a brief after this prompt, replacing the ID and duration:

```text
Prepare EP009_My_Title for local batch rendering. Read AGENTS.md,
PRODUCTION_GUIDE.md, config/production_defaults.json and docs/CLOUD_WORKFLOW.md.
Reuse the approved School Guy character and current v005 Grease Pencil master.
Create a portable .py builder that imports bpy, and a build-only entrypoint
using tools/production_paths.py and tools/grease_pencil_toolkit.py.

Use 1080 x 1920 at 24 fps, [DURATION] seconds, fast Eevee GPU animation.
Keep all captions at the top using the current v002 bounds. Preserve all
existing delivered episodes and canonical library/template files.
Prepare original/supplied audio, a frame-aligned cue sheet and relative assets.
Add this episode to queue/pending.queue.json, using the reference queue schema.
Support BLENDER_QUEUE_BUILD_ONLY=1; do not start a final render in this task.

Run python tools/validate_repository.py, the repository tests, queue validate
and dry-run. If compatible Blender is installed, build and inspect project settings
without rendering. Describe which checks were actually run and any remaining
Blender/font/visual validation. Commit the source or open a PR for review.

Episode brief:
[PASTE STORY, EXACT TEXT, SHOTS, ACTION, AUDIO AND TIMINGS HERE]
```

Create an episode folder under `02_EPISODES/EP009_My_Title/` containing the required input assets, builder output paths, audio and edit metadata. Do not fill the queue with blank placeholders for unrequested stories. `queue/pending.queue.json` starts empty; add the 10–20 episodes you actually prepare. Refer to `queue/example.queue.json` for the precise schema.

## What makes an episode portable

- Derive the repository root from `Path(__file__)` or `RuntimePaths.discover()`; store asset and output references relative to it. Do not use the original author's drive or user directory.
- Use `tools/production_paths.py` for runtime and font discovery. Run scene code with Blender's Python. Declare any extra ordinary-Python dependencies rather than checking copied site-packages into Git.
- Keep source assets available to the cloud task and laptop. Pack allowed external assets into the `.blend` or use relative file paths. Retrieve any Git LFS assets before validation/build.
- Reuse the approved character, master and caption geometry. Maintain a cue sheet with frame numbers for precise audio timing. Duration at 24 fps must give the expected frame count.
- Split building, rendering and video encoding. A builder must not render as a side effect; the queue enforces preparation-only build stages. Refactor a legacy helper before queueing it if it launches previews during a build.
- Give each episode unique project, frame and output paths. Save a numbered version before significant changes and protect completed files.

Declare additional repository-relative dependencies with optional `inputs` lists on an episode or individual build step: include external plate images, imported episode helpers and other source assets used by that stage. This lets content changes invalidate cached work instead of reusing a result from old inputs. Inputs produced by an earlier build step must also appear in that step's declared `outputs`.

Arial Black is generally an installed Windows font rather than a portable source dependency. Existing `.blend` font data is packed. For new captions, reuse that packed font when possible, or configure an installed local font via `font_file`. Cloud authoring can use a suitable available bold substitute, but must record it and measure the full glyph/outline bounds again. Review the phone-scale layout before final rendering. Do not commit a standalone Windows system font file.

Historical scripts are preserved as episode references and may need path/font/runtime adaptation. New code should use the portable toolkit; do not assume every older episode script runs unchanged on Linux.

## Pull and render at home

From a clean or safely saved working tree, pull the reviewed GitHub changes into this checkout. Keep local unfinished changes; resolve conflicts deliberately. Retrieve required large assets if Git LFS is used. Copy `config/local.example.json` to ignored `config/local.json` and fill it on the laptop:

```json
{
  "blender_exe": "ABSOLUTE_PATH_TO_BLENDER_5_2_EXECUTABLE",
  "ffmpeg_exe": "ABSOLUTE_PATH_TO_FFMPEG_EXECUTABLE",
  "ffprobe_exe": "ABSOLUTE_PATH_TO_FFPROBE_EXECUTABLE",
  "font_file": "OPTIONAL_ABSOLUTE_PATH_TO_AN_INSTALLED_BOLD_FONT",
  "blenders": {}
}
```

These are placeholders, not runnable paths. Executable environment overrides are `BLENDER_EXECUTABLE`, `FFMPEG_EXECUTABLE`, `FFPROBE_EXECUTABLE`. The queue also accepts `--blender`, `--ffmpeg` and `--ffprobe`. Keep all machine paths in ignored local configuration rather than episode manifests.

On this production laptop, the existing FFmpeg 6.1.1 build works with its NVIDIA driver for NVENC. A newer FFmpeg binary may require a newer driver. Check the actual chosen binary and encode test rather than assuming any FFmpeg can use the GPU.

```sh
python tools/validate_repository.py
python tools/production_queue.py validate queue/pending.queue.json
python tools/production_queue.py dry-run queue/pending.queue.json
python tools/production_queue.py build queue/pending.queue.json
```

Inspect each prepared scene's settings and dependencies, and render/review representative frames locally. Check the setup, action/contact, peak reaction and ending, caption bounds, frame count and audio cues. A cloud syntax check alone is not visual approval. Once ready, run:

```sh
python tools/production_queue.py render queue/pending.queue.json
```

The runner processes episodes sequentially. For a build-and-render batch in one invocation use `run` instead. The default stops on an error; `--continue-on-error` permits later independent episodes to run. Keep GPU concurrency at one on the 4 GB GTX 1650 Ti and enough free disk space for intermediate PNGs.

Rerunning the same queue resumes only matching work: completed build steps need matching input/output hashes, and reusable render frames need matching job inputs and valid PNGs. Per-PC records live in ignored `queue/.runs/`. A changed source or damaged output invalidates its stage; choose a new numbered output path when a builder must rebuild a protected existing project. Existing final videos are protected unless they match this queue's verified completed result.

## Optional local Blender MCP

Start Blender and its installed MCP bridge on the laptop, confirm the bridge is connected, then use:

```sh
python tools/production_queue.py render queue/pending.queue.json --backend mcp
```

This backend applies to the render stage and uses the local bridge at `127.0.0.1:9876`. Build stages use their declared Python/Blender runners. Save the open Blender project first; the backend refuses a dirty/unsaved scene. A bridge acknowledgment means the job was scheduled; the runner waits for the completion/status file before moving to the next episode, then restores the original clean project/scene/frame. Keep Blender running and do not start another GPU job concurrently.

MCP is useful for scene inspection and interactive fixes; ordinary Blender subprocess rendering can execute the batch independently. The bridge on a powered-off home PC cannot service cloud requests. Local MCP servers and transports are not automatically available in cloud; connectivity and authentication must be checked separately. [Official MCP guidance](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

## Hybrid backgrounds and runtime compatibility

Use the ordinary Eevee pipeline unless the brief explicitly requests hybrid realistic backgrounds. For a hybrid episode, keep three stages separate: build the native plate scene without rendering; explicitly render its static Cycles GPU plates locally once; then build the transparent GP/Eevee animation and composition using those images. Plate rendering must finish before the animation's composition/build step needs the files. It is a separate explicit render stage, not an automatic queue `build_steps` operation: the build-only guard prohibits both preview and plate rendering. Finish the plate stage before starting the animation batch.

EP008's local plates used Blender 4.2 with OptiX because the existing driver 555.97 was incompatible with the installed Blender 5.2 Cycles backend. Keep the plate runtime separate from the **5.2.2 native Grease Pencil animation**. `blender_profile: "cycles42"` selects an alternate configured executable through `config/local.json`'s `blenders` map for an individual build or render step. Selecting a profile does not turn a build step into a render. A Cycles render job must specify `engine: "CYCLES"` and the appropriate `cycles_backend: "OPTIX"` or `"CUDA"`; the default remains Eevee. Never open a 5.2 GP project in the older runtime, render a full Cycles animation for this shortcut, or silently fall back to CPU. A new driver or hardware setup requires a fresh compatibility check.

## Delivery and source control

Final MP4s belong in `03_FINAL_OUTPUT/YouTube/` or the requested platform folder. Save the editable project, audio/cue sheet and verification metadata. Report actual video running length, render elapsed time and encoding elapsed time separately. For hybrid episodes, report plate rendering and animation rendering separately as well. Inspect actual decoded video and audio before calling the result finished.

Commit source code, necessary approved assets, portable configuration and episode source metadata. Generated videos, frame sequences, simulation caches, vendor binaries and local configuration are excluded from Git. They are reproducible/local deliverables, not inputs needed for cloud authoring. Keep credentials out of Git and use environment secret facilities only if a task actually needs authenticated network services.
