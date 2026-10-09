import bpy
from pathlib import Path
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender')
s=bpy.data.scenes['BRIX_TestStage']; bpy.context.window.scene=s
for scene in list(bpy.data.scenes):
    if scene!=s:bpy.data.scenes.remove(scene)
keep=set(s.objects)
for o in list(bpy.data.objects):
    if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
    if c.name not in ['EP002_ENVIRONMENT','EP002_BED','EP002_LIGHTS','EP002_CAMERAS','EP002_UI']:bpy.data.collections.remove(c)
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
assert len(bpy.data.scenes)==1
s['production_role']='Reusable BRIX bed test set: environment, bed, camera, soft lights and top selector only.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'00_LIBRARY/Environments/BRIX_TestStage.blend'),compress=True)
print('CLEAN_STAGE_VERIFIED',len(s.objects),'objects; no character or simulation')
