import bpy,json
from pathlib import Path
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender')
dest=ROOT/'00_LIBRARY/Materials/BRIX_EEVEE_Clarity_v001.blend'
names=['MAT_EP001_Glass_Clarity','MAT_EP001_Shield_Clarity','MAT_EP001_Water_Clarity']
materials=[bpy.data.materials[n] for n in names]
for m in materials:
    m.asset_mark(); m.asset_data.description='Reusable low-cost EEVEE preview clarity variant; does not replace the original physical material.'
assert not dest.exists(),'Preserve existing canonical clarity library'
bpy.data.libraries.write(str(dest),set(materials),path_remap='RELATIVE_ALL',fake_user=True,compress=True)
print('NEW_REUSABLE_MATERIAL_VARIANTS '+str(dest))
