# EP009 — You shared the wrong screen

Current delivery is **18 seconds, 432 frames, 1080 × 1920 at 24 fps**, rendered with Eevee on the GTX 1650 Ti. The latest user direction is bright **flat 2D SVG puppet animation**, crisp black outlines, solid colors, and one static office background. No shading, gradients, textures or Cycles backgrounds are used in the final version.

## Current sources and delivery

- Editable animation: `blend/EP009_Wrong_Screen_Cutout_v003.blend`.
- Portable animation builder: `../../tools/ep009_wrong_screen_cutout.py`.
- Recurring character: `../../00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_v002.svg`, its native `.blend`, and contour JSON.
- Single background: `plates/Flat_Office_v002.svg`, `plates/Flat_Office_v002.blend`, and `plates/Flat_Office_v002.png`; builder `../../tools/ep009_flat_office.py`.
- Aligned dialogue/word cues: `edit/speech_cues_v001.json`; final audio `audio/EP009_Final_Mix_18s_v001.wav`.
- Local final video: `../../03_FINAL_OUTPUT/YouTube/EP009_Wrong_Screen_Peter_1080p24_v001.mp4`. Generated videos and animation frames are excluded from Git.
- Final source checks: `edit/project_verification.json`, `edit/delivery_verification.json`, and `edit/flat_plate_qa.json`.

## Measured elapsed times

- Final animation render: **413.570529 seconds** (6 minutes 53.57 seconds).
- Video encoding: **5.293647 seconds**.
- Final single flat background render: **0.938907 seconds**.
- Video running length: **18 seconds**. Running length is distinct from render elapsed time.

These are actual measured stages. Earlier development stills and abandoned Cycles attempts are separate records, not the final background render duration.

## Review scope and superseded work

The actual final-render PNGs at frames **5, 27, 85, 150, 241, 340, 385 and 432** were inspected in a phone-scale contact sheet. Captions were readable, the final top title fit, and no painter-order leaks or missing background were observed in those frames. The local sheet is `previews/EP009_Final_Actual_Frames_Contact_Sheet_v001.jpg`; previews are excluded from Git. This representative-frame review does not establish that every frame or every lip-sync movement was individually inspected. Audio/video verification is recorded separately in the delivery metadata.

`EP009_Wrong_Screen_GP_v001.blend`, the original shaded Peter v001 experiments, all `EP009_Office_Plates_4_2_*` sources, `Plate_A_Warm_Office_*`/`Plate_B_Cold_Panic_*` Cycles images, and their `plate_*` metadata are **superseded, unused work in progress**. Earlier `Cutout_v001`/`Cutout_v002` and `Flat_Office_v001` are retained source versions. The queue targets `Cutout_v003`; only `flat_plate_*` metadata describes the current static background.
