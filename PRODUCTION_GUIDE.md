# Blender production system

## Approved defaults for future 2D content

The latest 2026-10-09 instructions replace the earlier recurring School Guy default with **Peter**, based on the user's supplied portrait. Future videos use his **flat modular SVG puppet**, preserving recognizable hair, facial design and palette while simplifying the supplied illustration to flat fills and bold outlines. Reuse `00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_v002.blend` and its versioned SVG/path assets; consult `config/production_defaults.json` for exact current paths and collection names. Do not rebuild Peter for each episode. Costumes can change for an explicitly requested role.

Animate static editable vector body parts with a skeletal rig: head, torso, upper/lower arms, hands and legs have reusable joints. Use bone/object transforms, persistent facial controls and reusable mouth shapes for expressions and lip sync. **Do not use traditional frame-by-frame animation or redraw the body per frame. No gradients or shading.** Native Grease Pencil may represent the editable parts when requested, but its drawings remain persistent while the rig moves them.

For future 2D episodes, start from `01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v005.blend` and immediately save an episode copy before editing. The user's latest defaults supersede the earlier 720p preference: **1080 x 1920 portrait (9:16) at 24 fps**, with fast **Eevee rendering on the GTX 1650 Ti**. Do not use 720p or 60fps for future 2D content unless the user requests it. Completed episodes retain their delivered settings and files.

Use **one static flat background plate** per episode. This latest instruction supersedes EP009's initial realistic two-plate proposal: keep the same backdrop through its setup and reveal. Animate props, characters and UI in foreground layers as needed. Photorealistic Cycles backgrounds are no longer the default; a new explicit hybrid request can authorize a separate plate stage. Final animation uses Eevee on the local GPU, with no automatic CPU Cycles fallback.

**POV titles and nonspoken tags remain at the top:** use **x=108–918px**, title **y=300–480px** and optional tag **y=500–548px**, including outlines. Default title top is y=300px (15.6%). Keep the user's approximate 2–3 cm visual gap on the reference phone; physical centimeters depend on device and playback scale. Use `tools/shorts_caption_safe_area.py:place_caption` and inspect a phone-scale preview for status/cutout overlap.

**Spoken captions appear near the bottom, above app overlays:** full glyph, outline and pop-animation bounds **x=130–870px, y=1340–1470px**, measured from top-left on the 1080 x 1920 export. This user's explicit update supersedes the previous top-only rule for dialogue captions. Use `00_LIBRARY/Caption_Layouts/Peter_Dynamic_Captions_v003.json`; keep channel/page names, subscribe controls and right-side buttons clear. Use **LuckiestGuy-Regular**, white fill and a heavy black outline. Show the actual spoken words one at a time with a brief scale-in pop, keeping the largest pop inside the safe band. Titles and subtitles remain fixed while scene elements shake. Review legibility and overlays at phone scale.

The font asset is `00_LIBRARY/Fonts/Luckiest_Guy/LuckiestGuy-Regular.ttf`, supplied by the user and redistributed with its license. Reuse its packed project data or repository copy; do not silently switch to Arial Black or commit proprietary standalone system fonts. Any unavoidable substitute must be recorded and its full layout reviewed again.

Dialogue requires lip sync. Use the clean dialogue track, actual word timestamps and measured audio amplitude to drive reusable mouth states. The EP009 method combines 24 fps RMS envelopes with word-based vowel/consonant visemes; it is **not phoneme forced alignment**. Mark listening, lip-sync and visual review complete only after those reviews actually happen.

**Peter always uses the same male Gemini `Charon` voice.** Load the locked `tts_character_voices.Peter` configuration for every line and retry. Keep his young-adult male vocal identity, accent and timbre consistent across future content; adjust only emotional delivery and pace. Never substitute a female voice or silently switch voice IDs/providers when rotating keys or handling failures. If Charon is unavailable, stop the speech stage and report it. Change his voice only on the human user's explicit instruction. Google identifies Charon as male in the [official Gemini-TTS voice table](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts#voice_options).

For speech generation, read comma-separated `GEMINI_API_KEYS` and `GROQ_API_KEYS` only from ignored `.env` or environment secret facilities. `tools/speech_api.py` calls providers server-side, rotates normal requests, retries transient failures and honors provider-wide 429 cooldowns/`Retry-After`; never rotate accounts to bypass quotas or expose keys in logs/source. The original EP009 v001 used Gemini `gemini-3.8-flash-tts` with Kore/Puck and Groq `whisper-large-v3` word timestamps; retain that truthful historical metadata. Corrected and future Peter lines use locked Charon. Recheck available models and documented free tiers for future tasks, cache completed lines using the voice ID as part of cache identity, and preserve exact dialogue.

All production assets, scripts, previews, versions and episodes live in this folder. The earlier School Guy asset `CHAR_School_Guy_2D` in `00_LIBRARY/Characters/School_Guy_2D/School_Guy_2D_v001.blend` remains preserved for historical episodes. Keep BRIX, old Peter versions and delivered episodes unchanged. The BRIX sections below describe the existing 3D library rather than future Peter animation defaults.

For every future video delivery, measure and report the actual animation render elapsed time. Report video running length separately from render time; also record encoding time in the episode delivery verification.

## Start an episode

1. For a new 2D episode, open `01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v005.blend` and append the current Peter puppet. For explicitly requested BRIX 3D work, use `01_TEMPLATES/BRIX_Shorts_Master.blend`.
2. Immediately **Save As** a new numbered project in its own `02_EPISODES/EP_Number_Name/` directory before editing.
3. Keep scene changes and animation in that episode copy. Check `00_LIBRARY` before making a new asset.
4. Before a significant change, save a new numbered version. Never overwrite the character master, template master, or an approved episode.
5. Episode caches belong in `02_EPISODES/EP_001_Name/cache/`, never in the library. Render approved outputs into the appropriate `03_FINAL_OUTPUT` platform folder.

## Historical BRIX controls

Select `RIG_BRIX`. Pose Mode exposes root, pelvis, spine, head and separate FK upper arm, forearm, hand, thigh, shin and foot bones on each side. Meshes have rigid bone weights and an Armature modifier. This is a lightweight FK rig; there is no automatic IK or cloth simulation.

Object custom properties provide ten expression weights: NEUTRAL, CONFIDENT, CURIOUS, SUSPICIOUS, SURPRISED, SCARED, DISGUSTED, IMPRESSED, RELIEVED, EXCITED. Set one to 1 and the others to 0 for a clean preset. Keyframe properties for transitions. Mouth shape keys, eye shape keys and eyebrow drivers respond to these weights.

Manual controls blend on top: `blink`, `squint`, `wide_open`, `look_x`, `look_y`, `smile`, `nervous_smile`, `open_surprise`, `frown`, `worried`, `impressed_O`. `look_x` and `look_y` range from -1 to 1. Other controls range from 0 to 1. Use manual mouth controls with expression weights at zero to avoid additive overshoot.

## Experiment station and UI

Select `CTRL_Experiment_Press` and keyframe `travel_m` from 0 to 2.2 for a downward press motion. This moves the piston and press head without a physics simulation. The shield is a separate thick glass side panel and can be moved vertically. The sample is a reusable material demonstration block.

Select `CTRL_UI`, then set or keyframe `selected_material`: 0 SLIME, 1 GLASS, 2 CLOTH, 3 WATER, 4 HONEY, 5 SAND, 6 LAVA. Each tile has a driven cyan selected state. Selection is a visual indicator; assign the matching library material to the experiment object yourself. SLIME uses the Jelly material family. UI_Title and UI_Parameter are native editable Blender text. UI objects follow CAM_MainVertical. Keep words short and preview on a phone before approving an episode.

## Library and reuse

Canonical collections are stored in separate blend libraries. Use File > Append > collection to reuse BRIX, laboratory, station, lighting, camera and UI. Materials are marked as assets and have fake users. Collections are marked as assets too. Existing template assets were assembled from the same original datablocks; do not rebuild them per episode.

The template uses local editable assets so character drivers, poses and UI can be animated within an episode without editing library files. Library changes are intentionally not pushed into completed episodes. To update a reusable asset, create a versioned library file and review it first. The camera and UI are a matched assembly: append them together or relink the UI parents to the episode camera. Text font data is packed.

## Historical BRIX laptop and transfer settings

The older BRIX master uses EEVEE at 1080 x 1920, 30 fps. Its resolution percentage 50 preview is 540 x 960; set 100 for a full-size still or approved output. **New Peter 2D episodes use 1080 x 1920 at 24 fps and full resolution.** BRIX subdivision is capped at 1. Its geometry has small bevels and lightweight procedural materials, with no image textures or volumetrics. No BRIX simulation or animation has been baked.

Transfer the whole Blender folder to the final machine. Packed font and procedural materials avoid external asset dependencies. Render and library references use relative paths. Validate EEVEE shaders and reflections on the destination machine before rendering. Final Cycles animation and expensive simulations require explicit approval.

## Tools and versions

`tools/blender_bridge.py` connects to the installed Blender MCP bridge at localhost:9876. `tools/build_foundation.py` builds the original foundation only when canonical masters do not exist. It is not an episode tool. Work-in-progress files and QA previews are kept under `01_TEMPLATES/Versions` and `01_TEMPLATES/Previews`. Save the full folder as a backup before upgrading Blender.
