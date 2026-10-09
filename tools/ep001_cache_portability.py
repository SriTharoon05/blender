import bpy, shutil, json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test')
s=bpy.data.scenes['EP001_Material_Test']; bpy.context.window.scene=s
src=EP/'blend/blendcache_EP001_v002'
report={}
for name,kind,frame in [('EP001_Slime','softbody',188),('EP001_Cloth','cloth',500)]:
    o=bpy.data.objects[name]; mod=next(m for m in o.modifiers if m.type in {'CLOTH','SOFT_BODY'}); cache=mod.point_cache
    prefix=name.encode().hex().upper(); files=list(src.glob(prefix+'_*')); dest=EP/'cache'/kind
    for p in files:shutil.copy2(p,dest/p.name)
    cache.use_external=True; cache.filepath='//../cache/'+kind+'/'; cache.index=0
    s.frame_set(frame); bpy.context.view_layer.update()
    dep=bpy.context.evaluated_depsgraph_get(); e=o.evaluated_get(dep); me=e.to_mesh(); z=[(e.matrix_world@v.co).z for v in me.vertices]; e.to_mesh_clear()
    report[name]={'files':len(files),'cache_info':cache.info,'min_world_z':min(z),'max_world_z':max(z)}
    print(json.dumps(report[name]))
    assert len(files)>100 and min(z)<1.7,'Deformation cache not loading: '+name
# Rigid-body cache is generated once and transferred to an explicit episode folder.
cache=s.rigidbody_world.point_cache; cache.use_disk_cache=True
for f in range(241,391):s.frame_set(f)
with bpy.context.temp_override(point_cache=cache):bpy.ops.ptcache.bake(bake=True)
src2=EP/'blend/blendcache_EP001_v005'; files=list(src2.glob('*.bphys'))
for p in files:shutil.copy2(p,EP/'cache/rigidbody'/p.name)
cache.use_external=True; cache.filepath='//../cache/rigidbody/'; cache.index=0
report['rigidbody']={'cache_files':len(files),'cache_info':cache.info}
s.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP001_v006.blend'),compress=True)
(EP/'edit/cache_portability_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print('PORTABLE_CACHES_READY')
