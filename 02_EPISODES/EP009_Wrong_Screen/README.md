# EP009 — You shared the wrong screen

Current corrected **v002** delivery is **18 seconds, 432 frames, 1080 × 1920 at 24 fps**, rendered with Eevee on the GTX 1650 Ti. Peter uses the permanently configured **Gemini Charon male voice**, with the identity locked and voice fallback disabled. The original v001 used the wrong voice and is preserved as a superseded delivery. The visual direction remains bright **flat 2D SVG puppet animation**, crisp black outlines, solid colors, and one static office background. No shading, gradients, textures or Cycles backgrounds are used in the final version.

## Current sources and delivery

- Editable corrected animation: `blend/EP009_Wrong_Screen_Cutout_v004.blend`.
- Portable animation builder: `../../tools/ep009_wrong_screen_cutout.py`.
- Recurring character: `../../00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_v002.svg`, its native `.blend`, and contour JSON.
- Single background: `plates/Flat_Office_v002.svg`, `plates/Flat_Office_v002.blend`, and `plates/Flat_Office_v002.png`; builder `../../tools/ep009_flat_office.py`.
- Corrected aligned dialogue/word cues: `edit/v002/speech_cues_v002.json`; final audio `audio/v002/EP009_Final_Mix_18s_v002.wav`. Charon generation voice/model and raw/fitted audio hash evidence are in `audio/v002/speech_generation_v002.json`.
- Local corrected final video: `../../03_FINAL_OUTPUT/YouTube/EP009_Wrong_Screen_Peter_1080p24_v002.mp4`. Generated videos and animation frames are excluded from Git.
- Corrected source checks: `edit/v002/project_verification_v002.json`, `edit/v002/delivery_verification.json`, and `edit/v002/audio_validation_v002.json`. The reused background retains `edit/flat_plate_qa.json`.

## Measured elapsed times

- Corrected v002 animation render: **407.306009 seconds** (6 minutes 47.31 seconds).
- Corrected v002 video encoding: **5.297532 seconds**.
- Additional background rendering for this correction: **0 seconds**; the same completed flat plate was reused. Its original source render took **0.938907 seconds**.
- Additional GPU review rendering for this correction: **0 seconds**; review used existing full-render/decoded video frames. The earlier v003 reference preview took **2.312 seconds**, separately from this correction.
- Video running length: **18 seconds**. Running length is distinct from render elapsed time.

These are actual measured stages. The superseded v001 movie took **413.570529 seconds** to render and **5.293647 seconds** to encode; its files and original reports remain unchanged. Earlier development stills and abandoned Cycles attempts are separate records, not part of the corrected v002 render elapsed.

## Review scope and superseded work

The corrected v002 movie's actual decoded frames **5, 27, 150, 241, 340 and 432** were inspected at **270px width** in `previews/Final_Encoded_Male_v002_Contact_Sheet.png`. Luckiest Guy words were readable, distinct mouth states matched the caption onsets in these samples, flat fills/painter order were intact, and the final head occlusion/top title were clean. Previews are excluded from Git. This representative encoded-frame review does not establish complete motion or individual phoneme-sync review; no audio listening review is claimed. Media decoding, zero-delay source-audio correlation, configured male voice/catalog evidence and generation-file hashes are checked separately in the corrected delivery report.

`EP009_Wrong_Screen_GP_v001.blend`, the original shaded Peter v001 experiments, all `EP009_Office_Plates_4_2_*` sources, `Plate_A_Warm_Office_*`/`Plate_B_Cold_Panic_*` Cycles images, and their `plate_*` metadata are **superseded, unused work in progress**. Earlier `Cutout_v001`–`Cutout_v003`, the original v001 audio/cues/movie and `Flat_Office_v001` are retained source versions. The corrected queue targets `Cutout_v004`; only `flat_plate_*` metadata describes the current static background. Previously committed EP009 sources are checked against Git, allowing only the repository's declared text line-ending normalization; this README is an authorized current-source-index update.
