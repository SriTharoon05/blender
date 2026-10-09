"""Recover from v005, sample actual sims into portable lightweight animation."""
import bpy, math, struct, json, shutil
from pathlib import Path
from mathutils import Vector
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test'); s=bpy.data.scenes['EP001_Material_Test']
if bpy.context.window:bpy.context.window.scene=s
# Reconstruct the stable slime lattice matching the successfully completed bake.
o=bpy.data.objects['EP001_Slime']; old=next(m for m in o.modifiers if m.type=='SOFT_BODY'); o.modifiers.remove(old)
bpy.ops.mesh.primitive_cube_add(size=.76); temp=bpy.context.view_layer.objects.active; temp.name='TEMP_SlimeLattice'; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=3); bpy.ops.object.mode_set(mode='OBJECT'); o.data=temp.data; o.data.name='EP001_Slime_StableSpringMesh'; bpy.data.objects.remove(temp,do_unlink=True); o.data.materials.append(bpy.data.materials['MAT_Jelly_Red'])
for v in o.data.vertices:
    inner=Vector([max(-.29,min(.29,a)) for a in v.co]); delta=v.co-inner
    if delta.length:v.co=inner+delta.normalized()*.09
for p in o.data.polygons:p.use_smooth=True
for f,z in [(115,2.48),(137,1.6),(147,1.03),(153,.80),(162,1.12),(177,.95),(196,.97),(225,.97)]:o.location.z=z; o.keyframe_insert(data_path='location',index=2,frame=f)
sb=o.modifiers.new('Stable guided jelly source','SOFT_BODY'); st=sb.settings; st.use_goal=True; st.goal_default=.65; st.goal_spring=.45; st.goal_friction=7; st.use_edges=True; st.pull=.55; st.push=.55; st.damping=8; st.bend=.5; st.use_stiff_quads=True; st.step_min=5; st.step_max=30
c=sb.point_cache; c.frame_end=225; c.frame_start=115; c.name='EP001_Slime'; c.use_external=True; c.filepath='//../cache/softbody/'; c.index=0
cloth=bpy.data.objects['EP001_Cloth']; cm=next(m for m in cloth.modifiers if m.type=='CLOTH'); cc=cm.point_cache; prefix='EP001_Cloth'.encode().hex().upper()
for p in (EP/'blend/blendcache_EP001_v002').glob(prefix+'_*'):shutil.copy2(p,EP/'cache/cloth'/p.name)
cc.use_external=True; cc.filepath='//../cache/cloth/'; cc.name=prefix; cc.index=0
# Export MDD coordinates so playback/rendering does not depend on versioned
# point-cache names. Keep disabled source solvers for future reviewed rebakes.
reports={}
for obj,mod,start,end,kind in [(o,sb,115,225,'softbody'),(cloth,cm,417,525,'cloth')]:
    # Cloth's thickness modifier must stay after the coordinate cache.
    after=[m for m in obj.modifiers if m!=mod]
    for m in after:m.show_viewport=False; m.show_render=False
    coords=[]
    for f in range(start,end+1):
        s.frame_set(f); bpy.context.view_layer.update(); e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=e.to_mesh(); vs=[tuple(v.co) for v in me.vertices]; e.to_mesh_clear()
        assert len(vs)==len(obj.data.vertices),(obj.name,len(vs),len(obj.data.vertices))
        assert all(math.isfinite(a) for v in vs for a in v),'Nonfinite deformation'
        coords.append(vs)
    dest=EP/'cache'/kind/(obj.name+'.mdd')
    with dest.open('wb') as file:
        file.write(struct.pack('>2i',len(coords),len(coords[0]))); file.write(struct.pack('>'+str(len(coords))+'f',*[i/30 for i in range(len(coords))]))
        for vs in coords:file.write(struct.pack('>'+str(len(vs)*3)+'f',*[a for v in vs for a in v]))
    mod.show_viewport=False; mod.show_render=False
    mc=obj.modifiers.new('Portable baked '+kind+' preview','MESH_CACHE'); mc.cache_format='MDD'; mc.filepath='//../cache/'+kind+'/'+dest.name; mc.frame_start=start; mc.frame_scale=1; mc.deform_mode='OVERWRITE'; mc.interpolation='LINEAR'
    idx=list(obj.modifiers).index(mc); obj.modifiers.move(idx,1)
    for m in after:m.show_viewport=True; m.show_render=True
    reports[kind]={'source':'actual cached simulation','frames':[start,end],'vertices':len(coords[0]),'coordinate_variation':max(abs(a-b) for va,vb in zip(coords[0],coords[-1]) for a,b in zip(va,vb)),'mdd':str(dest.relative_to(EP))}
# Simulate fourteen shards in memory, then store their rigid-body transforms.
shards=sorted([o for o in bpy.data.objects if o.name.startswith('EP001_GlassShard_')],key=lambda o:o.name)
transforms={o.name:[] for o in shards}
rc=s.rigidbody_world.point_cache; rc.frame_end=390; rc.frame_start=241
for f in range(241,391):
    s.frame_set(f); bpy.context.view_layer.update(); dep=bpy.context.evaluated_depsgraph_get()
    for obj in shards:
        mat=obj.evaluated_get(dep).matrix_world; loc,quat,scale=mat.decompose(); transforms[obj.name].append({'frame':f,'location':list(loc),'rotation_quaternion':list(quat)})
s.frame_set(320)
for obj in shards:
    obj.hide_viewport=False; obj.hide_set(False)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj; bpy.ops.rigidbody.object_remove(); obj.rotation_mode='QUATERNION'
    for v in transforms[obj.name]:
        obj.location=v['location']; obj.rotation_quaternion=v['rotation_quaternion']; obj.keyframe_insert(data_path='location',frame=v['frame']); obj.keyframe_insert(data_path='rotation_quaternion',frame=v['frame'])
(EP/'cache/rigidbody/EP001_Glass_Transforms.json').write_text(json.dumps(transforms),encoding='utf-8')
reports['glass']={'source':'actual in-memory rigid body simulation','shards':len(shards),'frames':[241,390],'cache':'cache/rigidbody/EP001_Glass_Transforms.json'}
s.frame_set(1); s.render.resolution_percentage=25; bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP001_v006.blend'),compress=True)
(EP/'edit/cache_portability_report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8'); print('RECOVERY_READY '+json.dumps(reports))
