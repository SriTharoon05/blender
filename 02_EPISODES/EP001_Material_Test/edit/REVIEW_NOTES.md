# EP001 — BRIX'S MATERIAL TEST

Review checkpoint: `blend/EP001_v009.blend`. Open this file, not an earlier bake checkpoint. Production timeline is 1–1290 at 30 fps: 43 seconds, 1080 x 1920, EEVEE. Normal development resolution is 25%.

The existing master character, laboratory, lighting, CAM_MainVertical, UI and material library were reused. Original master blend hashes were checked and remain unchanged.

## Review media

- `previews/review_v009/`: ten representative 540 x 960 EEVEE stills, including the establishing shot, button click, all seven materials, containment climax and final reaction.
- `previews/EP001_Review_v009.mp4`: full-story silent EEVEE timing preview, 324 x 576 at 7.5 fps. It samples every fourth production frame and retains the approximately 43-second duration. This deliberately lightweight review animation is not final output.

## Story and timing

| Frames | Beat |
| --- | --- |
| 1–90 | Confident entrance, console approach, button press, machine retracts |
| 91–240 | Slime falls, compresses and jiggles; BRIX is surprised then amused |
| 241–390 | Fourteen glass shards release at impact; BRIX raises his hands and ducks |
| 391–540 | Cloth drops and drapes over the platform; suspicion becomes relief/impressed interest |
| 541–690 | Water splashes; BRIX leans in, recoils and becomes annoyed |
| 691–840 | Viscous amber honey drops slowly; curiosity, disgust and impressed reaction |
| 841–990 | Sand block collapses to a mound with instanced grains; BRIX waves it away |
| 991–1170 | LAVA selection, widened eyes, camera glance, retreat/panic; containment locks before impact |
| 1171–1290 | Relief, then an exhausted/annoyed look at the camera |

AMUSED and CONCERNED blend existing expression controls; the master rig was not rebuilt. Camera lens pushes and very small impact shakes are animated on the existing camera. Title and parameter text use the established camera-mounted UI.

## Lightweight simulation limits

- Slime: **98 vertices**, guided soft-body springs, collision response and jiggle. Actual deformation results are stored in `cache/softbody/EP001_Slime.mdd`; the source solver remains disabled in the review file.
- Glass: **14 volumetric Voronoi cells**, convex-hull rigid-body simulation sampled into transform keyframes. The portable record is `cache/rigidbody/EP001_Glass_Transforms.json`. The review playback does not rerun rigid-body physics.
- Cloth: **25 x 25 grid**, 625 vertices, small cloth simulation without self-collision. The corrected fabric drapes over the support and platform. Actual deformation is in `cache/cloth/EP001_Cloth_Drape_v002.mdd`, followed by a thin Solidify modifier. The source solver remains disabled.
- Water and honey: **32 divisions**, small 2.22 x 2.22 x 2.20 m liquid domains, 110 cached frames each, mesh scale 1. Honey uses low-resolution viscosity and slower simulation time. Caches stay in `cache/fluid/water` and `cache/fluid/honey`.
- Sand: an animated mound collapse plus **96 instances** of one low-poly grain mesh. This is a granular proxy, not a large granular physics simulation.
- Lava: animated viscous proxy with procedural emissive crust and a small warm point light. The safety shield geometry is reused for episode containment panels. There is no lava fluid bake, smoke or volumetric simulation.

EEVEE clarity variants are used for glass, water and containment so dark screen-space transmission does not hide the action. They do not replace the original canonical material files.

## Crash recovery

Blender 5.2.2 crashed while changing a point-cache disk setting after a bake. Recovery began from saved v005. The completed deformation caches were exported to portable MDD files, and the glass simulation was sampled in a separate Blender process without toggling disk caching. The recovered v006 and polished v007/v008 are retained. V009 fixes the cloth support collision and its drape in an isolated simulation pass.

Earlier numbered checkpoints preserve development history. Some early point-cache files under `blend/blendcache_*` are diagnostic history and are not required by the current review checkpoint. The current file uses explicit relative cache paths under `cache/`.

No final high-resolution fluid bake, large fracture or sand simulation, Cycles rendering, copyrighted music, or finished video was produced. Sound-effect markers are provided; the review animation is silent. Await user review before final production.
