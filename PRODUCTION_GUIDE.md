# BRIX production system

## Approved defaults for future 2D content

The user approved the recurring 2D guy from EP003 on 2026-10-08. Use this same character for all future 2D content unless the user explicitly requests another character. Preserve his face silhouette, dark angular hair, skin palette, simple facial features and blue hoodie design; change poses and expressions as the story requires.

The canonical native Grease Pencil collection is `CHAR_School_Guy_2D` in `00_LIBRARY/Characters/School_Guy_2D/School_Guy_2D_v001.blend`. The user's approved image is `00_LIBRARY/Characters/School_Guy_2D/Approved_Character_Reference.png`. Reuse this asset rather than redesigning the character each episode.

For future 2D episodes, start from `01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v005.blend` and immediately save an episode copy before editing. The user's latest defaults supersede the earlier 720p preference: **1080 x 1920 portrait (9:16) at 24 fps**, with fast **Eevee rendering on the GTX 1650 Ti**. Do not use 720p or 60fps for future 2D content unless the user requests it. Completed episodes retain their delivered settings and files.

For **all future videos**, place captions higher, with the user's requested **approximately 2–3cm gap from the top** on the reference phone, avoiding only the **notification/status/cutout area**. This latest correction supersedes the previous conservative 25–39% placement and full app-header/filter-chip clearance. Default main-caption top is **y=300px (15.6%)** on a **1080 x 1920** export. Physical centimeters vary with the device/player, so use the requested visual gap and phone-scale preview rather than claiming an exact device-independent centimeter measurement. Keep **all titles and taglines at the top, never bottom**.

Use **x=108–918px**, main caption **y=300–480px**, and optional tagline just beneath it at **y=500–548px**, measured from top-left including the thick outline. Keep important faces below **y=600px** when composing shots; remove the previous unnecessarily large top gap. Use Arial Black or equally bold text, white fill, thick black outline, exact wording and sensible wrapping. Keep captions fixed through camera shake. Apply `tools/shorts_caption_safe_area.py:place_caption` using `00_LIBRARY/Caption_Layouts/Shorts_Reels_Upper_Safe_Area_v002.json` and inspect a phone-scale preview for notification-area overlap.

Dad or other explicitly requested roles may use an age/costume variant of the approved character while retaining the recognizable face and hair design.

All production assets, scripts, previews, versions and episodes live in this folder. BRIX is an original recurring character; no downloaded character or texture assets are used.

For every future video delivery, measure and report the actual animation render elapsed time. Report video running length separately from render time; also record encoding time in the episode delivery verification.

## Start an episode

1. Open `01_TEMPLATES/BRIX_Shorts_Master.blend`.
2. Immediately **Save As** `02_EPISODES/EP_001_Name/EP_001_Name_v001.blend` before editing.
3. Keep scene changes and animation in that episode copy. Check `00_LIBRARY` before making a new asset.
4. Before a significant change, save a new numbered version. Never overwrite the character master, template master, or an approved episode.
5. Episode caches belong in `02_EPISODES/EP_001_Name/cache/`, never in the library. Render approved outputs into the appropriate `03_FINAL_OUTPUT` platform folder.

## BRIX controls

Select `RIG_BRIX`. Pose Mode exposes root, pelvis, spine, head and separate FK upper arm, forearm, hand, thigh, shin and foot bones on each side. Meshes have rigid bone weights and an Armature modifier. This is a lightweight FK rig; there is no automatic IK or cloth simulation.

Object custom properties provide ten expression weights: NEUTRAL, CONFIDENT, CURIOUS, SUSPICIOUS, SURPRISED, SCARED, DISGUSTED, IMPRESSED, RELIEVED, EXCITED. Set one to 1 and the others to 0 for a clean preset. Keyframe properties for transitions. Mouth shape keys, eye shape keys and eyebrow drivers respond to these weights.

Manual controls blend on top: `blink`, `squint`, `wide_open`, `look_x`, `look_y`, `smile`, `nervous_smile`, `open_surprise`, `frown`, `worried`, `impressed_O`. `look_x` and `look_y` range from -1 to 1. Other controls range from 0 to 1. Use manual mouth controls with expression weights at zero to avoid additive overshoot.

## Experiment station and UI

Select `CTRL_Experiment_Press` and keyframe `travel_m` from 0 to 2.2 for a downward press motion. This moves the piston and press head without a physics simulation. The shield is a separate thick glass side panel and can be moved vertically. The sample is a reusable material demonstration block.

Select `CTRL_UI`, then set or keyframe `selected_material`: 0 SLIME, 1 GLASS, 2 CLOTH, 3 WATER, 4 HONEY, 5 SAND, 6 LAVA. Each tile has a driven cyan selected state. Selection is a visual indicator; assign the matching library material to the experiment object yourself. SLIME uses the Jelly material family. UI_Title and UI_Parameter are native editable Blender text. UI objects follow CAM_MainVertical. Keep words short and preview on a phone before approving an episode.

## Library and reuse

Canonical collections are stored in separate blend libraries. Use File > Append > collection to reuse BRIX, laboratory, station, lighting, camera and UI. Materials are marked as assets and have fake users. Collections are marked as assets too. Existing template assets were assembled from the same original datablocks; do not rebuild them per episode.

The template uses local editable assets so character drivers, poses and UI can be animated within an episode without editing library files. Library changes are intentionally not pushed into completed episodes. To update a reusable asset, create a versioned library file and review it first. The camera and UI are a matched assembly: append them together or relink the UI parents to the episode camera. Text font data is packed.

## Laptop and transfer settings

The master uses EEVEE at 1080 x 1920, 30 fps. Resolution percentage 50 is the normal development preview (540 x 960). Set 100 for a full-size still or approved output. Subdivision is capped at 1. Geometry has small bevels; surfaces use lightweight procedural textures, with no image textures or volumetrics. No simulation or animation has been baked.

Transfer the whole Blender folder to the final machine. Packed font and procedural materials avoid external asset dependencies. Render and library references use relative paths. Validate EEVEE shaders and reflections on the destination machine before rendering. Final Cycles animation and expensive simulations require explicit approval.

## Tools and versions

`tools/blender_bridge.py` connects to the installed Blender MCP bridge at localhost:9876. `tools/build_foundation.py` builds the original foundation only when canonical masters do not exist. It is not an episode tool. Work-in-progress files and QA previews are kept under `01_TEMPLATES/Versions` and `01_TEMPLATES/Previews`. Save the full folder as a backup before upgrading Blender.
