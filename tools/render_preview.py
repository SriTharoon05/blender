import bpy, json
from pathlib import Path
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender')
scene=bpy.context.scene
scene.render.filepath=str(ROOT/'01_TEMPLATES/Previews/BRIX_Foundation_v001.png')
bpy.ops.render.render(write_still=True)
print('PREVIEW_READY '+scene.render.filepath)
