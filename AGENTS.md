# Blender episode production

This is an existing production system, not a blank project. Read `PRODUCTION_GUIDE.md`, `config/production_defaults.json`, and `docs/CLOUD_WORKFLOW.md` before authoring. The user's latest instructions override older episode settings and historical prose.

## Preserve the approved work

- Reuse `00_LIBRARY` and the existing production helpers. Preserve BRIX, School Guy and all historical character assets.
- The user's 2026-10-09 replacement for future 2D content is **Peter**, derived from the supplied portrait. Reuse the flat modular puppet in `00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_v002.blend` and its versioned SVG/path assets. Read the current exact asset/collection names from `config/production_defaults.json`. Preserve recognizable hair, face and palette; role-specific costumes may change when requested.
- Start future 2D episodes from `01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v005.blend`. Save a new episode copy before editing.
- Do not overwrite canonical library/template files or delivered episodes. Use a new episode directory and numbered project version. Do not re-render completed episodes unless requested.

## Current visual and delivery defaults

- Vertical **1080 x 1920**, **24 fps**, full resolution. Duration comes from each brief; frame count must match duration exactly.
- Use **flat modular SVG puppet animation**: static editable vector parts driven by a skeletal rig, with joints for head/torso, upper/lower arms, hands and legs. Animate bone/object transforms and reusable mouth/eye states. Do not redraw a character for every frame or create traditional frame-by-frame animation. Use flat fills and bold outlines, **no gradients, shading or moving background**. Use one static flat background plate per episode. Keep native editable Grease Pencil where requested, using persistent rigged parts rather than per-frame drawing copies.
- Use **Eevee on the local GTX 1650 Ti** for animation. A GPU is not a promise about a cloud environment: check actual availability. No automatic CPU Cycles fallback. The flat static-background default supersedes EP009's original photorealistic two-plate brief. A future explicit request can authorize a separate hybrid Cycles GPU plate stage; preparation-only queue build steps must not render plates or previews. Never open a 5.2 GP project with Blender 4.2.
- **POV titles and nonspoken tags stay at the top:** complete glyph/outline bounds **x=108..918, y=300..480 px**, optional tag **y=500..548 px**. Use `tools/shorts_caption_safe_area.py:place_caption`; preserve the requested visual 2–3 cm top gap on the reference phone, without claiming device-independent centimeters.
- **Spoken captions use the lower safe band:** complete glyph/outline/pop bounds **x=130..870, y=1340..1470 px**, measured from top-left on 1080 x 1920. Use the current `Peter_Dynamic_Captions_v003.json` layout and inspect a phone-scale preview with channel/page name, subscribe and side-button overlays. Keep titles and dialogue captions fixed during camera shake; keep important faces clear of both bands. This explicit dialogue-caption update supersedes the old top-only rule for spoken words.
- Use **LuckiestGuy-Regular** from `00_LIBRARY/Fonts/Luckiest_Guy/LuckiestGuy-Regular.ttf`, white fill and a heavy black outline. Spoken captions appear one word at a time, timed to actual speech, with a brief scale-in pop; keep the maximum popped word inside its safe bounds. Preserve exact scripted wording. Include the font's redistribution license when committing it. Do not add proprietary standalone system fonts. Record and review any unavoidable font substitution.
- Produce original or supplied licensed audio, with a frame-aligned cue sheet and synchronized MP4 audio. Do not claim a render, audio sync, visual review or GPU check that was not performed.
- Dialogue requires lip sync. Use measured word timings and audio amplitude to animate reusable visemes; distinguish this from phoneme forced alignment. Do not claim phoneme accuracy or a listening review unless actually performed.
- Deliver the editable project and final video. Record actual render elapsed time, video running length, encoding time and material validation limitations separately. For hybrid work, record static-plate and animation render times separately.

## Cloud authoring and local rendering

Cloud tasks prepare portable **`.py` scripts that import `bpy`**, episode metadata, audio generation and queue entries. `.bpy` is not the standard Python script extension; native Blender projects are `.blend` files. Cloud can create a `.blend` only if a suitable Blender runtime and all assets are available. A script syntax check does not establish that it runs correctly in Blender. Optional audio/image/physics authoring dependencies are declared in `requirements-cloud.txt`; install with `python -m pip install -r requirements-cloud.txt` when needed. The repository/queue validators themselves use the standard library.

Use repository-relative paths and derive the root from the script location; do not hard-code a user's drive, home directory, runtime cache, or Windows font path. Keep executable overrides in ignored `config/local.json` or environment variables. Treat legacy episode helpers as reference code and make new entrypoints portable. Support `BLENDER_QUEUE_BUILD_ONLY=1` so a builder creates the project without launching the animation render.

The local PC must be powered on for its GPU or Blender MCP bridge to be usable. Cloud authoring must not rely on reaching the PC while it is off. Do not assume Blender, GPU, NVENC, a display, or local MCP is preinstalled/connected in cloud. Do not install a mismatched `bpy` package to disguise missing Blender validation.

Prepare each new episode's builder and add one item to `queue/pending.queue.json`. Use `queue/example.queue.json` for schema. Declare additional relative asset/helper dependencies in the episode or build step's optional `inputs` list so their changes invalidate cached work. Keep each episode's assets, frame directory and final output distinct. The local runner executes one episode at a time; do not launch concurrent GPU render jobs on the 4 GB laptop.

## Speech services and secrets

**Peter's permanent voice is male Gemini `Charon`.** Read `tts_character_voices.Peter` from `config/production_defaults.json` for every Peter line, including narration, thoughts, dialogue and retries. Keep the same voice ID and vocal profile across future episodes; emotion and pace may change. Never substitute a female voice, rotate voice IDs with API keys, or fall back to another voice/provider. If Charon is unavailable, leave the speech stage incomplete and report the failure. Only an explicit human instruction can change this locked voice identity. Google lists Charon as male in its [official Gemini-TTS voice table](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#voice_options).

Use `tools/speech_api.py` for direct server-side provider calls. Read comma-separated pools from `GEMINI_API_KEYS` and `GROQ_API_KEYS` in the ignored local `.env` or environment secret settings. Never print, store in source metadata or commit credential values; never put provider keys in URLs or client-side code.

The original EP009 v001 used the available, documented free-tier **Gemini `gemini-3.8-flash-tts`**, with Kore/Puck, and **Groq `whisper-large-v3`** with `verbose_json` word timestamps. Preserve that historical metadata; corrected/new Peter speech uses locked Charon. Recheck official model availability and free-tier eligibility before new generation. Cache generated lines and their real transcripts, including the voice ID in cache identity. Rotate normal requests' starting keys, retry transient failures and temporarily skip failed keys. Honor `Retry-After` and provider-wide cooldowns on 429 responses; key rotation must not bypass project/organization or daily quotas.

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
