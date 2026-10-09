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
Prepare EP010_My_Title for local batch rendering. Read AGENTS.md,
PRODUCTION_GUIDE.md, config/production_defaults.json and docs/CLOUD_WORKFLOW.md.
Reuse Peter's current flat modular SVG puppet and the v005 master; save a new
episode copy before editing. Use static editable vector parts driven by the
skeletal rig's head/torso, arm/hand and leg joints. No traditional frame-by-frame
redraw, gradients or shading. Use one static flat background plate.
Create a portable .py builder that imports bpy, and a build-only entrypoint
using the existing production path, vector/rig and caption helpers.

Use 1080 x 1920 at 24 fps, [DURATION] seconds, fast Eevee GPU animation.
Use LuckiestGuy-Regular, white fill and a heavy black outline. Keep POV titles
at the top within x=108..918,y=300..480. Put one-word-at-a-time spoken captions
inside x=130..870,y=1340..1470, including their brief scale-in pop and outline.
Check the phone-scale layout above channel/subscribe UI; captions stay fixed
during camera shake. Preserve historical delivered episodes and library assets.
Prepare original/supplied audio, a frame-aligned cue sheet and relative assets.
Dialogue needs lip sync: measured word timings plus amplitude-driven reusable
visemes. Distinguish that from phoneme forced alignment. If authorized secrets
are available, use tools/speech_api.py for server-side Gemini TTS and Groq STT;
never expose keys or bypass quota cooldowns. Cache generated lines/transcripts.
Peter must use the locked male Gemini Charon voice from
config/production_defaults.json:tts_character_voices.Peter for every line and
retry. Keep the same voice ID and vocal profile; never fall back to a female
voice or a different voice/provider. Only explicit human instruction can change
Peter's permanent voice. Include voice identity in audio cache validation.
Add this episode to queue/pending.queue.json, using the reference queue schema.
Support BLENDER_QUEUE_BUILD_ONLY=1; do not start a final render in this task.

Run python tools/validate_repository.py, the repository tests, queue validate
and dry-run. If compatible Blender is installed, build and inspect project settings
without rendering. Describe which checks were actually run and any remaining
Blender/font/visual validation. Commit the source or open a PR for review.

Episode brief:
[PASTE STORY, EXACT TEXT, SHOTS, ACTION, AUDIO AND TIMINGS HERE]
```

Create an episode folder under `02_EPISODES/EP010_My_Title/` containing the required input assets, builder output paths, audio and edit metadata. Do not fill the queue with blank placeholders for unrequested stories; add the 10–20 episodes you actually prepare. Refer to `queue/example.queue.json` for the precise schema.

## What makes an episode portable

- Derive the repository root from `Path(__file__)` or `RuntimePaths.discover()`; store asset and output references relative to it. Do not use the original author's drive or user directory.
- Use `tools/production_paths.py` for runtime and font discovery. Run scene code with Blender's Python. Declare any extra ordinary-Python dependencies rather than checking copied site-packages into Git.
- Keep source assets available to the cloud task and laptop. Pack allowed external assets into the `.blend` or use relative file paths. Retrieve any Git LFS assets before validation/build.
- Reuse the Peter flat puppet, master, rig joints and current caption layout. Keep vector drawings/parts static while animating transforms and facial controls, and use one static flat backdrop. Maintain real measured word/audio cues with frame numbers. Duration at 24 fps must give the expected frame count.
- Split building, rendering and video encoding. A builder must not render as a side effect; the queue enforces preparation-only build stages. Refactor a legacy helper before queueing it if it launches previews during a build.
- Give each episode unique project, frame and output paths. Save a numbered version before significant changes and protect completed files.

Declare additional repository-relative dependencies with optional `inputs` lists on an episode or individual build step: include external plate images, imported episode helpers and other source assets used by that stage. This lets content changes invalidate cached work instead of reusing a result from old inputs. Inputs produced by an earlier build step must also appear in that step's declared `outputs`.

The current font is the user-supplied **LuckiestGuy-Regular** at `00_LIBRARY/Fonts/Luckiest_Guy/LuckiestGuy-Regular.ttf`, distributed with its license. Load that repository-relative asset and pack it into the new `.blend`. Preserve historical packed Arial Black data in older episodes; it no longer defines future captions. If the requested font is unavailable, record the substitution and review the full glyph/outline/pop bounds again. Do not upload proprietary standalone system fonts. Spoken captions occupy x=130–870,y=1340–1470, above channel/subscribe UI; POV titles remain x=108–918,y=300–480. Use the current `Peter_Dynamic_Captions_v003.json` layout and review at phone scale.

Historical scripts are preserved as episode references and may need path/font/runtime adaptation. New code should use the portable toolkit; do not assume every older episode script runs unchanged on Linux.

## Server-side speech, word timing and lip sync

Read comma-separated `GEMINI_API_KEYS` and `GROQ_API_KEYS` through `tools/speech_api.py`. Local values live in ignored `.env`; a cloud task needs its own authorized environment secrets because the local `.env` is deliberately absent from Git. Never print values, embed them in a URL/client bundle or copy them into source/audio metadata. A cloud authoring task without those secrets can prepare dialogue/audio scripts, but must report that actual provider generation/alignment was unavailable.

**Peter's permanent voice is male Gemini `Charon`.** Read `config/production_defaults.json:tts_character_voices.Peter` before generating narration, thoughts or dialogue. The voice ID and young-adult male vocal profile stay fixed across episodes and retries. Emotion and pacing may vary. Never switch voices/providers or use a female fallback when handling key failures; if Charon is unavailable, report the incomplete speech stage. Only an explicit instruction from the human user may change the lock. Cache identity must include the configured voice so old Kore clips cannot silently satisfy a Charon job. Google explicitly lists Charon as male and Kore as female in its [official Gemini-TTS voice table](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#voice_options).

The current implemented Gemini TTS interface uses REST server-side calls. The original EP009 v001 successfully used **`gemini-3.8-flash-tts`**, employee voice **Kore** and meeting-host voice **Puck**; retain that historical metadata. Corrected and future Peter clips use locked Charon. Its official pricing documents a free tier; availability, quota and account eligibility still need to be checked before future generation. [Gemini TTS documentation](https://ai.google.dev/gemini-api/docs/speech-generation), [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing).

Generate dialogue lines separately, retain original audio, and fit only as needed with pitch-preserving timing. Transcribe the actual fitted clean speech through **Groq `whisper-large-v3`**, `response_format=verbose_json` and word timestamp granularity. Validate exact scripted words, preserve measured word times and clamp any ASR boundary padding to the real audio boundary with a recorded flag. Use the same cue sheet for word-caption onsets and mouth animation. [Groq STT documentation](https://console.groq.com/docs/speech-to-text).

The pool rotates starting keys for normal requests, retries transient failures and temporarily skips failed keys. A 429 applies a provider-wide cooldown honoring `Retry-After`; long/daily account quota exhaustion stops rather than cycling accounts to evade quotas. Groq limits are organization-wide. [Groq rate-limit documentation](https://console.groq.com/docs/rate-limits).

EP009's lip-sync cues combine measured 24 fps RMS amplitude with word-based vowel/consonant viseme estimates and reusable mouth states. This is not phoneme forced alignment. API transcription success and objective sample/peak checks do not establish listening quality or rendered lip-sync quality; report those reviews separately and inspect actual output before claiming completion.

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

## Flat backgrounds and optional hybrid compatibility

Current Peter videos use one static flat background and Eevee puppet animation, without gradients or shading. The user's latest EP009 correction supersedes that brief's initial photorealistic two-plate proposal. Keep its backdrop static and put animated characters/props/UI in foreground layers. Do not launch Cycles plate rendering for ordinary flat episodes.

Only a later explicit hybrid request can authorize realistic backgrounds. For that request, keep three stages separate: build the native plate scene without rendering; explicitly render its static Cycles GPU plate locally once; then build the transparent GP/Eevee animation and composition using that image. Plate rendering must finish before the animation's composition/build step needs the file. It is a separate explicit render stage, not an automatic queue `build_steps` operation: the build-only guard prohibits both preview and plate rendering. Finish the plate stage before starting the animation batch.

EP008's local plates used Blender 4.2 with OptiX because the existing driver 555.97 was incompatible with the installed Blender 5.2 Cycles backend. Keep the plate runtime separate from the **5.2.2 native Grease Pencil animation**. `blender_profile: "cycles42"` selects an alternate configured executable through `config/local.json`'s `blenders` map for an individual build or render step. Selecting a profile does not turn a build step into a render. A Cycles render job must specify `engine: "CYCLES"` and the appropriate `cycles_backend: "OPTIX"` or `"CUDA"`; the default remains Eevee. Never open a 5.2 GP project in the older runtime, render a full Cycles animation for this shortcut, or silently fall back to CPU. A new driver or hardware setup requires a fresh compatibility check.

## Delivery and source control

Final MP4s belong in `03_FINAL_OUTPUT/YouTube/` or the requested platform folder. Save the editable project, audio/cue sheet and verification metadata. Report actual video running length, render elapsed time and encoding elapsed time separately. For hybrid episodes, report plate rendering and animation rendering separately as well. Inspect actual decoded video and audio before calling the result finished.

Commit source code, necessary approved assets, portable configuration and episode source metadata. Generated videos, frame sequences, simulation caches, vendor binaries and local configuration are excluded from Git. They are reproducible/local deliverables, not inputs needed for cloud authoring. Keep credentials out of Git and use environment secret facilities only if a task actually needs authenticated network services.
