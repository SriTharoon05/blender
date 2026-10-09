# Peter 2D character, v001

## Current flat puppet style, v002

The user's latest style overrides the initial shaded portrait interpretation.
`Peter_2D_Flat_Puppet_v002.svg` and `Peter_2D_Flat_Puppet_Paths_v002.json`
contain bright solid fills and crisp black lines with zero shading, gradients,
or textures. Fifteen independent body parts declare skeletal pivots and parents:
head, neck, torso, upper/lower arms, hands, upper/lower legs and feet. The full
body uses a blue hoodie, yellow trousers and white shoes; role costumes can vary.

Head contours retain the original 1254-pixel reference coordinates. The full
modular figure uses a `1254 x 2200` view box. Viseme/blink presets are separate
static vectors; build their meshes once and switch visibility while skeletal
joints animate. Do not create a complete new drawing for each frame.

`tools/peter_flat_puppet_tools.py` reads this current source, returns independent
part copies and selects expression contours. `build_peter_flat_puppet.py`
regenerates SVG/JSON without Blender. The v001 SVG/native library remain preserved
as historical interpretations, not the current flat puppet default.

`tools/peter_flat_rig_library.py` builds the native v002 skeletal cutout library
through Blender without rendering. It writes only a new protected version,
`Peter_2D_Flat_Puppet_v002.blend`, containing `CHAR_Peter_2D_Flat_Puppet`.

## Original portrait interpretation, v001

Peter is the user-approved recurring character from the supplied portrait. This
new versioned asset preserves the former School Guy library and delivered work.

- `Peter_2D_v001.svg`: fully editable vector portrait, transparent background.
- `Peter_2D_Rest_v001.svg`: closed-mouth portrait for idle/rest poses.
- `Peter_2D_v001.blend`: standalone asset-marked native Grease Pencil collection
  `CHAR_Peter_2D`, with object `GP_Peter_2D` and a neutral rest-mouth drawing.
- `Peter_2D_Paths_v001.json`: the same 79 curated paths as sampled contours,
  including seven mouth poses and a closed-eye blink.
- `build_peter_vector.py`: portable source generator; no raster tracing or
  embedded image data. Rebuilds the three source assets without Blender.
- `Peter_2D_Preview_v001.png`: an inspected raster preview of these vectors;
  the episode character uses native vector/Grease Pencil contours, not this PNG.
- `Approved_Peter_Reference.png`: supplied original reference, preserved for
  future likeness reviews and available inside the repository.

Coordinate system: `viewBox="0 0 1254 1254"`, x to the right and y down.
JSON colors are sRGB and have equivalent hexadecimal and RGBA fields. Convert
to linear RGB for native Blender materials. Preserve list order: front and back
hair occur at different depths. Widths are full SVG stroke widths in image pixels.
For Grease Pencil, convert to the appropriate half-width radius in scene units.

Semantic groups: `hoodie`, `neck`, `ears`, `face`, `hair`, `brows`, `eyes`, `nose`,
`mouth`, `face_detail`. All contours are genuine paths; no `<image>` elements.
SVG groups have unique IDs and a shared `data-feature` attribute when a feature
appears in more than one depth layer.

The original smile appears in the base portrait. Lip-sync variants `rest`, `MBP`,
`AA`, `EE`, `OH`, `FV`, and `smile` share mouth pivot `(670,651)`. Replace the base
`mouth` group rather than drawing expressions on top of the original smile.
Blink replaces only the `eyes` group; under-eye details stay visible.

`tools/peter_svg_tools.py:pose_paths` selects those variants, small gaze changes,
and a head-only drawing for role-specific costumes. The head's reference pivot
is `(627,495)`. The character's layered brown hair, warm skin, asymmetrical face,
large dark eyes, cheek mole, and navy hoodie are the recognizable identity.

The native collection uses 0.01 scene units per reference pixel and keeps all
78 neutral-pose strokes editable. `tools/peter_native_library.py` builds this
standalone library through Blender 5.2 without rendering and refuses to overwrite
an existing library. The native version has 78 strokes because its one closed
rest-mouth stroke replaces the reference smile's two vector paths.

This is a curated flat-color interpretation rather than a pixel-identical
reproduction of the source illustration. The source's texture and gradients
are represented by clean colored vector regions suitable for editable animation.
