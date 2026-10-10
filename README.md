# Blender shorts production

An existing Blender production library, episode source scripts and a portable workflow for preparing episodes in Codex Cloud, then rendering them sequentially on the home laptop.

**Current 2D defaults:** Peter's flat modular SVG puppet, animated through reusable skeletal joints and static editable vector parts; one static flat backdrop, no gradients or shading and no traditional frame-by-frame redraw. Deliver 1080 x 1920 vertical at 24 fps, with Eevee on the GTX 1650 Ti. Use LuckiestGuy-Regular: POV titles stay at the top (y=300–480 px), while word-by-word spoken captions pop inside the lower safe band (x=130–870px, y=1340–1470px), above channel/subscribe UI. Dialogue requires measured audio-driven lip sync. Read [AGENTS.md](AGENTS.md) and [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md) for the complete production rules.

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

Add prepared episodes to the pending queue; 10–20 entries make a sequential batch. `run` performs build plus render; `build` stops after preparing projects. `--backend mcp` is available for local rendering through an active Blender bridge. The ordinary subprocess backend can render the same queue without MCP. Configure local executables first as described below.

## Portable setup

Use Python 3.11+ for the queue and dependency-free tooling. Scene builders run inside Blender, not an ordinary Python interpreter. Editable puppet/Grease Pencil authoring targets **Blender 5.2.2**; API/version compatibility matters. Reuse `00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_v002.blend` and the current versioned SVG/path assets named in the production configuration. Copy the v005 master before editing an episode.

For original sound synthesis, image QA or legacy physics work, install the optional NumPy, Pillow and SciPy dependencies:

```sh
python -m pip install -r requirements-cloud.txt
```

The repository and queue validators do not need those packages. Blender supplies `bpy` when running scene scripts; do not replace that runtime with an unrelated pip package.

Copy `config/local.example.json` to the ignored `config/local.json`, then supply local Blender, FFmpeg, FFprobe and optional font paths. Environment overrides are `BLENDER_EXECUTABLE`, `FFMPEG_EXECUTABLE` and `FFPROBE_EXECUTABLE`; command flags override executable selection too. Nothing in the public configuration contains a user's absolute filesystem paths or credentials.

The current caption font is the user-supplied `00_LIBRARY/Fonts/Luckiest_Guy/LuckiestGuy-Regular.ttf`, distributed with its license. Pack it into new editable projects. Historical projects retain their packed fonts; do not upload standalone proprietary Windows fonts. See the cloud guide for font substitutions and optional explicitly requested hybrid plate handling.

To try the portable build-only example with an unused output path:

```sh
blender --background --python examples/minimal_2d_episode.py -- --output 02_EPISODES/EP_DEMO_Portable/blend/EP_DEMO_v001.blend --duration 2
```

This older example demonstrates the preserved School Guy and caption helpers; it creates an editable project without rendering and refuses to overwrite an existing file. New content must follow the current Peter puppet, Luckiest Guy and dialogue-caption defaults rather than copy the example's historical character/style.

## Speech and synchronized captions

**Peter's permanent voice is male Gemini `Charon`.** Its locked identity and vocal profile are saved in `config/production_defaults.json` under `tts_character_voices.Peter`. Reuse it for all future Peter speech and retries. Key rotation must keep the voice unchanged; unavailable Charon stops speech generation instead of triggering another voice/provider. Only the user's explicit instruction can change it. Google lists Charon as male in its [official voice table](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#voice_options).

`tools/speech_api.py` calls Gemini and Groq server-side. Read comma-separated `GEMINI_API_KEYS` and `GROQ_API_KEYS` from the ignored `.env` or environment secrets. Never commit or print keys. The pool rotates normal requests, retries transient failures and honors provider-wide 429 cooldowns/`Retry-After`, without bypassing project/organization quotas.

The original EP009 v001 used Gemini `gemini-3.8-flash-tts` with Kore/Puck voices and Groq `whisper-large-v3` word timestamps. Its metadata remains historical; corrected and future Peter speech uses locked Charon. Model availability and documented free-tier eligibility must be checked for new generation. Each line is cached with its voice ID and aligned on its actual fitted audio. Caption wording must match the script; the cue sheet supplies word times and 24 fps mouth states. Current lip sync combines measured amplitude with word-based viseme estimates, not phoneme forced alignment. Do not imply a listening or rendered lip-sync review from API success alone.

## Repository contents

| Location | Purpose |
| --- | --- |
| `00_LIBRARY/` | Approved reusable characters, props, environments and caption layout |
| `01_TEMPLATES/` | Saved production masters; copy before editing |
| `02_EPISODES/` | Episode source projects, audio, plate assets and production metadata |
| `tools/` | Existing production scripts plus portable paths/toolkit and batch runner |
| `examples/` | Minimal build-only example for future portable episodes |
| `config/` | Committed production defaults and an empty local configuration example |
| `queue/` | Pending sequential batch, reference manifest and completed episode plans |
| `docs/` | Cloud authoring, local validation and render workflow |

Generated movie files, render frame sequences, simulation caches, runtime bundles and machine-specific configuration are kept locally rather than in source control. Historical scripts preserve their original behavior and may contain Windows-specific assumptions; use the portable helpers for new work.

Every final delivery records **video duration, actual render elapsed time and encoding time separately**. Hybrid episodes also record the static-plate render time. Cloud syntax/queue checks are useful preparation; final visual and audio review still happens on rendered output.

## EP010 production example

[Binge Watching — Expectation vs Reality](02_EPISODES/EP010_Binge_Watching/README.md)
uses Peter's approved flat skeletal puppet and locked Charon voice for both the
main character and his small inner voice. Its current brief explicitly requests
two matching realistic night/dawn room plates; this episode-specific hybrid
exception does not change the ordinary flat-background default. Its portable
builders, original audio/cue generator, phone-preview helper and read-only delivery
verifier are under `tools/ep010_*.py`. Preparation builders never render.
