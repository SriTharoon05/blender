"""Read-only cold-load verification, run with Blender --background."""
import bpy, json
from pathlib import Path
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender')
s=bpy.context.scene; r=bpy.data.objects['RIG_BRIX']
exprs=['NEUTRAL','CONFIDENT','CURIOUS','SUSPICIOUS','SURPRISED','SCARED','DISGUSTED','IMPRESSED','RELIEVED','EXCITED']
result={'file':bpy.data.filepath,'render_engine':s.render.engine,'format':[s.render.resolution_x,s.render.resolution_y,s.render.fps],'resolution_percentage':s.render.resolution_percentage,'checks':{},'library_contents':{},'external_paths':[]}
assert s.render.engine=='BLENDER_EEVEE'
assert [s.render.resolution_x,s.render.resolution_y,s.render.fps]==[1080,1920,30]
for i,e in enumerate(exprs):
    for name in exprs:r[name]=float(name==e)
    r.update_tag(); s.frame_set(i+2); bpy.context.view_layer.update()
    k=bpy.data.objects['CHAR_BRIX_Mouth'].data.shape_keys.key_blocks[e]
    assert k.value==1,(e,k.value); result['checks'][e]='PASS'
ctrl=bpy.data.objects['CTRL_Experiment_Press']; ctrl['travel_m']=1.; ctrl.update_tag(); s.frame_set(20); bpy.context.view_layer.update()
assert abs(ctrl.location.z-2.55)<.0001,ctrl.location.z
result['checks']['press_travel']='PASS'
for path in sorted((ROOT/'00_LIBRARY').rglob('*.blend')):
    with bpy.data.libraries.load(str(path),link=False) as (source,target):
        result['library_contents'][str(path.relative_to(ROOT))]={'collections':list(source.collections),'scenes':list(source.scenes),'materials':len(source.materials)}
assert result['library_contents']['00_LIBRARY\\Characters\\BRIX\\BRIX_Master.blend']['scenes']==['BRIX_Character_Master']
for font in bpy.data.fonts:
    if font.filepath and font.filepath!='<builtin>' and not font.packed_file:result['external_paths'].append(font.filepath)
assert not result['external_paths'],result['external_paths']
(ROOT/'01_TEMPLATES/Previews/saved_master_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('SAVED_MASTER_VERIFIED '+json.dumps(result))
