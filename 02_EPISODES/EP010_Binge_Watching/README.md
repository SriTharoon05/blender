# EP010 — Binge Watching: Expectation vs Reality

22 seconds, 528 frames, vertical 1080 x 1920 at 24 fps. The latest brief explicitly
requests two matching static Cycles room plates with an Eevee transparent puppet
foreground. This is an episode-specific hybrid exception; the ordinary production
default remains one static flat background.

Peter reuses the approved flat SVG identity with new modular pajama, slipper and
blanket costume parts. His body is animated by skeletal pivots, with reusable eye
and mouth states. The small inner voice is Peter too. Both use his permanent male
Gemini **Charon** voice; the historical brief's Kore/Puck suggestions do not change
his locked identity. A separate fictional television announcer uses Puck.

The user requests suitable sound design instead of blindly copying the proposed
audio list. The original mix uses a restrained cozy motif, remote/countdown clicks,
accelerating clock touches, then birds and a quiet deadpan ending. Actual fitted
speech is transcribed with Groq word timestamps and supplies the caption and mouth
cues. Word/amplitude-driven mouth states are estimates, not phoneme alignment.

The prepared scene starts from the approved 5.2 master. The separate static room
stage uses the configured `cycles42` runtime with verified OptiX GPU; it never opens
a native 5.2 Grease Pencil project. Builders do not render. Finish the explicit
plate render stage before building or rendering the final animation. The local
queue runs one GPU job at a time.

```
python tools/production_queue.py build queue/pending.queue.json
python tools/production_queue.py render queue/pending.queue.json
```

The new entrypoint is `tools/ep010_binge_watching.py`, with puppet construction in
`tools/ep010_binge_puppet.py` and audio generation in `tools/ep010_audio.py`.
Machine executables and API keys remain in ignored local configuration/environment.
Final movies and both composed/transparent PNG sequences are local render outputs,
excluded from Git. The editable project packs the two background images, font and
mixed audio. Delivery validation records actual plate, animation and encoding
times separately, plus the limited scope of representative frame inspection.

Previous EP009 queue instructions are retained under `queue/completed/`; completed
episodes and canonical assets are preserved.

Delivered project: `blend/EP010_Binge_Watching_v004.blend`. Local final movie:
`03_FINAL_OUTPUT/YouTube/EP010_Binge_Watching_Peter_1080p24_v004.mp4` (repository-root
relative). Actual selected-version elapsed times on the GTX 1650 Ti were **21.496 s
for both static plates**, **719.142 s (11 min 59 s) for animation**, and **7.331 s
for encoding**. Video running length is exactly **22 s**, separate from these
elapsed processing times. Development builds and previews are excluded.

`edit/v004/delivery_verification_v001.json` records full audio/video decoding,
encoded dimensions/frame count, audio timing and source correlation, caption
bounds, voice identity, GPU evidence and protected-source hashes. Ten decoded MP4
representatives were inspected with a 270 px simulated phone interface; two were
also inspected at full resolution. `edit/v004/freeze_verification_v001.json`
establishes identical final PNG pixels for frames 517–528. This is representative
visual inspection, not a full motion or subjective audio listening review. Lip
sync uses measured word/amplitude estimates rather than phoneme forced alignment.
Repository/queue checks and all 77 unit tests passed.
