import bpy,math,json,struct
from pathlib import Path
from mathutils import Vector
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets'); main=bpy.data.scenes['EP002_Impossible_Blankets']
def active(o):bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); o.hide_viewport=False; o.hide_set(False); bpy.context.view_layer.objects.active=o
def disable_view_keys(o):
    if o.animation_data:
        for layer in o.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for f in list(bag.fcurves):
                        if f.data_path=='hide_viewport':bag.fcurves.remove(f)
    o.hide_viewport=False
report={}
# Actual low-resolution fabric drape around static collision silhouettes.
cloth=bpy.data.objects['FX_EP002_Cloth_Blanket']; disable_view_keys(cloth)
sim=bpy.data.scenes.new('SIM_EP002_Cloth'); sim.render.fps=30; sim.frame_start=337; sim.frame_end=443
colliders=[o for o in main.objects if o.name.startswith('COLL_EP002_') and not o.name.startswith('COLL_EP002_Water_')]+[bpy.data.objects['PROP_TestBed_Mattress'],bpy.data.objects['PROP_TestBed_Pillow']]
for o in [cloth]+colliders:sim.collection.objects.link(o)
if bpy.context.window:bpy.context.window.scene=sim
cm=cloth.modifiers.new('Actual lightweight fabric drape','CLOTH'); st=cm.settings; st.quality=5; st.mass=.25; st.tension_stiffness=18; st.compression_stiffness=18; st.shear_stiffness=10; st.bending_stiffness=.25; cm.collision_settings.use_self_collision=False; cm.collision_settings.distance_min=.022; cm.collision_settings.collision_quality=3; cm.point_cache.frame_end=443; cm.point_cache.frame_start=337
frames=[]; heights={}
for f in range(337,444):
    sim.frame_set(f); bpy.context.view_layer.update(); e=cloth.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=e.to_mesh(); vs=[tuple(v.co) for v in me.vertices]; z=[(e.matrix_world@v.co).z for v in me.vertices]; e.to_mesh_clear(); assert all(math.isfinite(a) for v in vs for a in v); frames.append(vs)
    if f in [365,400,440]:heights[f]=[min(z),max(z)]
path=EP/'cache/cloth/EP002_Cloth_Drape.mdd'
with path.open('wb') as file:
    file.write(struct.pack('>2i',len(frames),len(frames[0]))); file.write(struct.pack('>'+str(len(frames))+'f',*[i/30 for i in range(len(frames))]))
    for vs in frames:file.write(struct.pack('>'+str(3*len(vs))+'f',*[a for v in vs for a in v]))
cm.show_viewport=False; cm.show_render=False; cache=cloth.modifiers.new('Portable fabric preview','MESH_CACHE'); cache.cache_format='MDD'; cache.filepath='//../cache/cloth/'+path.name; cache.frame_start=337; cache.interpolation='LINEAR'; cache.deform_mode='OVERWRITE'
sub=cloth.modifiers.new('Soft fabric finish','SUBSURF'); sub.levels=1; sub.render_levels=1; sol=cloth.modifiers.new('Fabric thickness','SOLIDIFY'); sol.thickness=.012
for f,v in [(1,True),(337,False),(447,True)]:cloth.hide_viewport=v; cloth.keyframe_insert(data_path='hide_viewport',frame=f)
report['cloth']={'vertices':len(frames[0]),'frames':[337,443],'heights':heights,'cache':'cache/cloth/'+path.name}
if bpy.context.window:bpy.context.window.scene=main
bpy.data.scenes.remove(sim)

# Actual small rigid-body fracture pass. No disk-cache toggling is performed.
shards=sorted([o for o in main.objects if o.name.startswith('FX_EP002_GlassShard_')],key=lambda o:o.name)
sim=bpy.data.scenes.new('SIM_EP002_Glass'); sim.render.fps=30; sim.frame_start=201; sim.frame_end=307
for o in shards+[bpy.data.objects['PROP_EP002_GlassCatchShield'],bpy.data.objects['COLL_EP002_Floor']]:sim.collection.objects.link(o)
if bpy.context.window:bpy.context.window.scene=sim
for i,o in enumerate(shards):
    disable_view_keys(o); active(o); bpy.ops.rigidbody.object_add(); b=o.rigid_body; b.type='ACTIVE'; b.mass=.12; b.collision_shape='CONVEX_HULL'; b.use_margin=True; b.collision_margin=.001; b.restitution=.26; b.friction=.28; b.kinematic=True
    b.keyframe_insert(data_path='kinematic',frame=201); b.keyframe_insert(data_path='kinematic',frame=239); b.kinematic=False; b.keyframe_insert(data_path='kinematic',frame=240)
    sim.frame_set(238); center=o.location.copy(); o.location=(center.x*1.04,(center.y+.5)*1.04-.5,2.26); o.keyframe_insert(data_path='location',frame=239); o.rotation_euler=(.025*math.sin(i),.035*math.cos(i),.022*math.sin(i*2)); o.keyframe_insert(data_path='rotation_euler',frame=239)
for name in ['PROP_EP002_GlassCatchShield','COLL_EP002_Floor']:
    o=bpy.data.objects[name]; disable_view_keys(o); active(o); bpy.ops.rigidbody.object_add(); o.rigid_body.type='PASSIVE'; o.rigid_body.collision_shape='MESH'; o.rigid_body.friction=.3
sim.rigidbody_world.point_cache.frame_end=307; sim.rigidbody_world.point_cache.frame_start=201; sim.rigidbody_world.substeps_per_frame=4; sim.rigidbody_world.solver_iterations=12
trans={o.name:[] for o in shards}
for f in range(201,308):
    sim.frame_set(f); bpy.context.view_layer.update(); dep=bpy.context.evaluated_depsgraph_get()
    for o in shards:
        loc,rot,scale=o.evaluated_get(dep).matrix_world.decompose(); trans[o.name].append({'frame':f,'location':list(loc),'rotation':list(rot)})
sim.frame_set(250)
for o in shards:
    active(o); bpy.ops.rigidbody.object_remove(); o.rotation_mode='QUATERNION'
    for record in trans[o.name]:
        o.location=record['location']; o.rotation_quaternion=record['rotation']; o.keyframe_insert(data_path='location',frame=record['frame']); o.keyframe_insert(data_path='rotation_quaternion',frame=record['frame'])
    for f,v in [(1,True),(201,False),(310,True)]:o.hide_viewport=v; o.keyframe_insert(data_path='hide_viewport',frame=f)
for name in ['PROP_EP002_GlassCatchShield','COLL_EP002_Floor']:
    o=bpy.data.objects[name]; active(o); bpy.ops.rigidbody.object_remove()
(EP/'cache/rigidbody/EP002_Glass_Transforms.json').write_text(json.dumps(trans),encoding='utf-8'); report['glass']={'fragments':len(shards),'thickness_m':.012,'frames':[201,307],'barrier_z':2.18,'source':'actual rigid bodies sampled to keyframes'}
if bpy.context.window:bpy.context.window.scene=main
bpy.data.scenes.remove(sim); main.frame_set(24)
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v005.blend'),compress=True)
(EP/'edit/simulation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print('PHYSICAL_CLOTH_AND_GLASS_READY '+json.dumps(report))
