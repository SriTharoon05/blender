import bpy, json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test')
s=bpy.data.scenes['EP001_Material_Test']; bpy.context.window.scene=s
results={}
for name,typ in [('EP001_Slime','SOFT_BODY'),('EP001_Cloth','CLOTH')]:
    o=bpy.data.objects[name]; mod=next(m for m in o.modifiers if m.type==typ); cache=mod.point_cache
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    s.frame_set(cache.frame_start)
    with bpy.context.temp_override(point_cache=cache):bpy.ops.ptcache.bake(bake=True)
    results[name]={'baked':cache.is_baked,'frames':[cache.frame_start,cache.frame_end]}
    print(json.dumps(results[name]))
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP001_v003.blend'),compress=True)
(EP/'edit/deform_bake_report.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('DEFORM_CACHES_READY')
