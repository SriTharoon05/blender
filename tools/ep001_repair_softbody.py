import bpy, math, shutil, json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test'); s=bpy.data.scenes['EP001_Material_Test']; bpy.context.window.scene=s
o=bpy.data.objects['EP001_Slime']; m=next(m for m in o.modifiers if m.type=='SOFT_BODY'); c=m.point_cache
c.use_external=False
with bpy.context.temp_override(point_cache=c):bpy.ops.ptcache.free_bake()
bpy.ops.mesh.primitive_cube_add(size=.76); temp=bpy.context.view_layer.objects.active; temp.name='TEMP_SlimeStableLattice'; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=3); bpy.ops.object.mode_set(mode='OBJECT')
o.data=temp.data; o.data.name='EP001_Slime_StableSpringMesh'; bpy.data.objects.remove(temp,do_unlink=True); o.data.materials.clear(); o.data.materials.append(bpy.data.materials['MAT_Jelly_Red'])
for v in o.data.vertices:
    inner=Vector((max(-.29,min(.29,a)) for a in v.co)) if False else None
    from mathutils import Vector
    inner=Vector([max(-.29,min(.29,a)) for a in v.co]); delta=v.co-inner
    if delta.length:v.co=inner+delta.normalized()*.09
for p in o.data.polygons:p.use_smooth=True
st=m.settings; st.use_goal=True; st.goal_default=.65; st.goal_spring=.45; st.goal_friction=7; st.use_edges=True; st.pull=.55; st.push=.55; st.damping=8; st.bend=.5; st.use_stiff_quads=True; st.step_min=5; st.step_max=30
for f,z in [(115,2.48),(137,1.6),(147,1.03),(153,.80),(162,1.12),(177,.95),(196,.97),(225,.97)]:o.location.z=z; o.keyframe_insert(data_path='location',index=2,frame=f)
c.name='EP001_Slime'; c.frame_start=115; c.frame_end=225; c.use_disk_cache=True
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o; s.frame_set(115)
with bpy.context.temp_override(point_cache=c):bpy.ops.ptcache.bake(bake=True)
src=EP/'blend/blendcache_EP001_v005'; files=list(src.glob('EP001_Slime_*.bphys'))
for p in files:shutil.copy2(p,EP/'cache/softbody'/p.name)
c.use_external=True; c.filepath='//../cache/softbody/'; c.name='EP001_Slime'; c.index=0
checks={}
for f in [147,155,188,220]:
    s.frame_set(f); bpy.context.view_layer.update(); e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); vals=[(e.matrix_world@v.co).z for v in e.data.vertices]; assert all(math.isfinite(z) for z in vals),'Nonfinite softbody'; checks[f]=[min(vals),max(vals)]
cloth=bpy.data.objects['EP001_Cloth']; cc=next(m for m in cloth.modifiers if m.type=='CLOTH').point_cache; prefix='EP001_Cloth'.encode().hex().upper(); src=EP/'blend/blendcache_EP001_v002'
for p in src.glob(prefix+'_*'):shutil.copy2(p,EP/'cache/cloth'/p.name)
cc.use_external=True; cc.filepath='//../cache/cloth/'; cc.name=prefix; cc.index=0
s.frame_set(500); bpy.context.view_layer.update(); e=cloth.evaluated_get(bpy.context.evaluated_depsgraph_get()); vals=[(e.matrix_world@v.co).z for v in e.data.vertices]; assert all(math.isfinite(z) for z in vals); checks['cloth']=[min(vals),max(vals),cc.info]
# Bake only fourteen rigid bodies and use an explicit cache identifier.
rc=s.rigidbody_world.point_cache; rc.name='EP001_Glass'; rc.frame_start=241; rc.frame_end=390; rc.use_disk_cache=True
with bpy.context.temp_override(point_cache=rc):bpy.ops.ptcache.bake(bake=True)
src=EP/'blend/blendcache_EP001_v005'
for p in src.glob('EP001_Glass_*'):shutil.copy2(p,EP/'cache/rigidbody'/p.name)
rc.use_external=True; rc.filepath='//../cache/rigidbody/'; rc.name='EP001_Glass'; rc.index=0
s.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP001_v006.blend'),compress=True)
(EP/'edit/cache_portability_report.json').write_text(json.dumps(checks,indent=2),encoding='utf-8'); print(json.dumps(checks))
