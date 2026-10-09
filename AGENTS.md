# Blender episode production

This is an existing production system, not a blank project. Read `PRODUCTION_GUIDE.md`, `config/production_defaults.json`, and `docs/CLOUD_WORKFLOW.md` before authoring. The user's latest instructions override older episode settings and historical prose.

## Preserve the approved work

- Reuse `00_LIBRARY` and the existing production helpers. Do not rebuild BRIX or the approved 2D character.
- The recurring 2D character is `CHAR_School_Guy_2D` in `00_LIBRARY/Characters/School_Guy_2D/School_Guy_2D_v001.blend`. Preserve the approved angular hair, face, palette and recognizable design. Role-specific age/costume variants are allowed when requested.
- Start future 2D episodes from `01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v005.blend`. Save a new episode copy before editing.
- Do not overwrite canonical library/template files or delivered episodes. Use a new episode directory and numbered project version. Do not re-render completed episodes unless requested.

## Current visual and delivery defaults

- Vertical **1080 x 1920**, **24 fps**, full resolution. Duration comes from each brief; frame count must match duration exactly.
- Use native editable Grease Pencil for requested 2D work; flat colors, bold outlines and the approved recurring character. Use **Eevee on the local GTX 1650 Ti** for animation. A GPU is not a promise about a cloud environment: check actual availability.
- No automatic CPU Cycles fallback. A specifically requested hybrid episode may use static Cycles GPU background plates rendered once, then compose transparent Eevee/GP animation over them. Plate rendering is a separate explicitly requested render stage; preparation-only queue build steps must not render plates or previews. Check Blender/driver compatibility separately for plates; never open a 5.2 GP project with Blender 4.2.
- Main-caption complete glyph/outline bounds: **x=108..918, y=300..480 px**, measured from top-left. Optional tag: **y=500..548 px**, same x bounds. All titles/taglines stay at the top, never bottom. Keep captions fixed during shake and important faces below y=600 when needed. Use `tools/shorts_caption_safe_area.py:place_caption` and the v002 caption-layout JSON; inspect a phone-scale preview. The target resembles a 2–3 cm top gap on the user's reference phone; centimeters vary with device and playback scale.
- Bold white text with a thick black outline; exact supplied text and readable wrapping. Prefer the template's packed Arial Black data or the locally installed font. On a platform without it, use a suitable bold installed font and review the measured layout; record that substitution. Do not add a standalone proprietary system font to Git.
- Produce original or supplied licensed audio, with a frame-aligned cue sheet and synchronized MP4 audio. Do not claim a render, audio sync, visual review or GPU check that was not performed.
- Deliver the editable project and final video. Record actual render elapsed time, video running length, encoding time and material validation limitations separately. For hybrid work, record static-plate and animation render times separately.

## Cloud authoring and local rendering

Cloud tasks prepare portable **`.py` scripts that import `bpy`**, episode metadata, audio generation and queue entries. `.bpy` is not the standard Python script extension; native Blender projects are `.blend` files. Cloud can create a `.blend` only if a suitable Blender runtime and all assets are available. A script syntax check does not establish that it runs correctly in Blender. Optional audio/image/physics authoring dependencies are declared in `requirements-cloud.txt`; install with `python -m pip install -r requirements-cloud.txt` when needed. The repository/queue validators themselves use the standard library.

Use repository-relative paths and derive the root from the script location; do not hard-code a user's drive, home directory, runtime cache, or Windows font path. Keep executable overrides in ignored `config/local.json` or environment variables. Treat legacy episode helpers as reference code and make new entrypoints portable. Support `BLENDER_QUEUE_BUILD_ONLY=1` so a builder creates the project without launching the animation render.

The local PC must be powered on for its GPU or Blender MCP bridge to be usable. Cloud authoring must not rely on reaching the PC while it is off. Do not assume Blender, GPU, NVENC, a display, or local MCP is preinstalled/connected in cloud. Do not install a mismatched `bpy` package to disguise missing Blender validation.

Prepare each new episode's builder and add one item to `queue/pending.queue.json`. Use `queue/example.queue.json` for schema. Declare additional relative asset/helper dependencies in the episode or build step's optional `inputs` list so their changes invalidate cached work. Keep each episode's assets, frame directory and final output distinct. The local runner executes one episode at a time; do not launch concurrent GPU render jobs on the 4 GB laptop.

## Checks

Ordinary Python, without Blender or a GPU:

```sh
python tools/validate_repository.py
python tools/production_queue.py validate queue/pending.queue.json
python tools/production_queue.py dry-run queue/pending.queue.json
python -m unittest discover -s tests -p "test_*.py"
```

The repository validator checks source syntax, production policy, required assets and immutable approved-asset hashes. Do not refresh its approved inventory to conceal asset changes. Also check changed Python files with `ast.parse` or `py_compile`; avoid recursively compiling vendored dependencies or historical generated caches. If Blender exists, build the new episode without rendering and verify scene settings, frame range, dependencies, packed/relative resources and caption bounds. Only mark visually reviewed after inspecting actual rendered representative frames on the destination runtime. Report unavailable checks clearly.

## Source control

Commit production scripts, portable configuration, documentation, required approved assets and new episode source metadata. Exclude render frames, movies, caches, vendor runtimes, machine configuration, credentials, crash files and `.blend1` backups. Read `docs/CLOUD_WORKFLOW.md` for asset transfer and font handling. Never commit local credential/configuration directories or embed credentials in repository URLs.
