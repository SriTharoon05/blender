# EP002 — Impossible Blankets

The original BRIX episode is ready for preview review. Its new walnut and terracotta bed, sky-blue set, material tokens, camera composition and protective shield take the supplied images as visual references. The character, styling and geometry are original to the BRIX production library.

1. **Episode:** `02_EPISODES/EP002_Impossible_Blankets/blend/EP002_v009.blend`. Blender is open with this version. The project is configured for 1080 × 1920 at 30 FPS, with EEVEE preview settings active.
2. **Reusable stage:** `00_LIBRARY/Environments/BRIX_TestStage.blend`. One scene containing the set, bed, camera, soft lights and seven-item top selector. No character, episode animation or simulations.
3. **New template:** `01_TEMPLATES/BRIX_Shorts_Master_v002.blend`. Includes the existing BRIX character, bed stage and empty material-test collections. The previous template is preserved.
4. **Reused assets:** BRIX_Master character geometry, RIG_BRIX, facial drivers and expression shapes; shared procedural material library; studio light datablocks; the packed UI font. Camera and top selector layout are newly designed for this episode.
5. **New assets:** bed frame, mattress and pillow; seamless sky-blue stage; seven original material tokens and selector highlight; animated blankets; twelve glass fragments; cloth collision proxies; sand instances; sliding transparent safety shield and cyan edges; warm lava light; episode markers and facial/body animation.
6. **Material methods:**

   | Material | Method |
   | --- | --- |
   | Slime | Lightweight green volume with keyed wrap, impact squash and jiggle deformation. |
   | Glass | Twelve thin Voronoi fragments, actual rigid-body simulation, sampled into portable transform keyframes and JSON. A clear barrier protects BRIX. |
   | Cloth | Actual 1,085-vertex collision drape; 107 frames exported to MDD. Source solver disabled for stable playback. |
   | Honey | Golden thick mesh with slow stretch and sticky fold shape animation. |
   | Sand | Collapsing mound mesh plus 160 animated grain instances. |
   | Water | Actual 32-division Mantaflow liquid with 107 cached mesh frames. |
   | Lava | Animated glowing crust mesh, flattening impact, warm light and timed sliding safety shield. |

7. **Preview status:** All simulations, caches, proxy deformations and rendered media are review quality. No high-resolution fluid, heavy granular simulation, detailed fracture, Cycles final render or production video has been started. The review video is silent.
8. **Duration:** 37.5 seconds on the production timeline; 37.6 seconds in the 7.5 FPS review encoding due to frame sampling. Seven tests run about 4.5 seconds each, with a longer lava ending, opening hook and final question.
9. **Previews:** `previews/EP002_Review_v009.mp4` (324 × 576); `previews/EP002_Review_ContactSheet_v002.jpg`; ten `EP002_*_v002.png` representative stills, including honey and outro. Source scripts and simulation reports are preserved under `scripts/` and `edit/`.
10. **Problems / decisions:** A live Blender scene-export crash was recovered from the saved stage checkpoint. Background export and simulation completed successfully. No technical decision is required to review. The low-resolution water and stylized honey/sand/lava proxies should be judged for look and timing before increasing simulation detail.

Verification compared SHA-256 hashes for **1,394 protected files**, covering EP001 and the pre-existing shared masters/templates. All are unchanged. Cold-load scene and media checks are recorded in `scene_verification.json` and `delivery_verification.json`.

Use v009 and v002 preview stills for review; earlier checkpoints and export backups are retained as development history.
