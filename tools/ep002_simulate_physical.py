import bpy,math,struct,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');main=bpy.data.scenes['EP002_Impossible_Blankets'];C=bpy.data.collections['EP002_CHARACTER']
colliders=[o for o in C.objects if o.name.startswith('COLL_EP002_Anatomy_')]+[bpy.data.objects[n] for n in ['PROP_TestBed_Mattress','PROP_TestBed_Pillow','PROP_TestBed_WalnutFrame','COLL_EP002_Floor']]
def scene(name,start,end,objects):
    sim=bpy.data.scenes.new(name);sim.render.fps=60;sim.frame_start=start;sim.frame_end=end;sim.collection.children.link(C)
    for o in objects:
        if o.name not in sim.objects:sim.collection.objects.link(o)
    bpy.context.window.scene=sim;return sim
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.hide_viewport=False;o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
report={}
for name,start,end,typ in [('Slime',168,356,'SOFT_BODY'),('Cloth',674,892,'CLOTH')]:
    o=bpy.data.objects['FX_EP002_'+name+'_Blanket'];sim=scene('SIM_EP002_Physical_'+name,start,end,[o]+colliders);mod=next(m for m in o.modifiers if m.type==typ)
    if typ=='SOFT_BODY':
        mod.settings.use_face_collision=False;mod.settings.use_edge_collision=False;mod.settings.step_min=10;mod.settings.step_max=60
    for collider in colliders:collider.collision.thickness_outer=.035 if typ=='SOFT_BODY' else .018
    path=EP/('cache/softbody' if typ=='SOFT_BODY' else 'cache/cloth')/('EP002_'+name+'_Physical60_v011.mdd');N=len(o.data.vertices);bounds={}
    with path.open('wb') as file:
        file.write(struct.pack('>2i',end-start+1,N));file.write(struct.pack('>'+str(end-start+1)+'f',*[i/60 for i in range(end-start+1)]))
        for f in range(start,end+1):
            sim.frame_set(f);bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[tuple(v.co) for v in me.vertices];world=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();assert len(vs)==N;assert all(math.isfinite(a) and abs(a)<50 for v in vs for a in v),(name,f)
            file.write(struct.pack('>'+str(3*N)+'f',*[a for v in vs for a in v]))
            if f in [start,start+35,end-10]:bounds[f]={'z':[min(v.z for v in world),max(v.z for v in world)]}
            if (f-start)%20==0:print('SOLVER_PROGRESS',name,f,flush=True)
    mod.show_viewport=False;mod.show_render=False;cache=o.modifiers.new('Physical60 portable playback','MESH_CACHE');cache.cache_format='MDD';cache.filepath='//../'+str(path.relative_to(EP)).replace('\\','/');cache.frame_start=start;cache.interpolation='LINEAR'
    sub=o.modifiers.new('Detailed smooth surface','SUBSURF');sub.levels=1;sub.render_levels=2
    if typ=='CLOTH':sol=o.modifiers.new('Woven thickness','SOLIDIFY');sol.thickness=.008
    report[name]={'solver':typ,'vertices':N,'frames':[start,end],'bounds':bounds,'cache':str(path.relative_to(EP))}
    bpy.context.window.scene=main;bpy.data.scenes.remove(sim)
# Real gravity-driven glass, with low restitution and actual moving anatomical contact.
shards=sorted([o for o in main.objects if o.name.startswith('FX_EP002_GlassShard_')],key=lambda o:o.name);sim=scene('SIM_EP002_Physical_Glass',442,616,shards+colliders)
for o in shards:
    active(o);bpy.ops.rigidbody.object_add();b=o.rigid_body;b.mass=.18;b.collision_shape='CONVEX_HULL';b.use_margin=True;b.collision_margin=.001;b.restitution=.06;b.friction=.7;b.linear_damping=.12;b.angular_damping=.3
for o in colliders:
    active(o);bpy.ops.rigidbody.object_add();b=o.rigid_body;b.type='PASSIVE';b.collision_shape='MESH';b.mesh_source='FINAL';b.use_deform=True;b.friction=.65;b.use_margin=True;b.collision_margin=.003
world=sim.rigidbody_world;world.point_cache.frame_end=616;world.point_cache.frame_start=442;world.substeps_per_frame=8;world.solver_iterations=25;record={o.name:[] for o in shards}
for f in range(442,617):
    sim.frame_set(f);bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
    for o in shards:
        loc,rot,scale=o.evaluated_get(dep).matrix_world.decompose();record[o.name].append({'frame':f,'location':list(loc),'rotation':list(rot)})
for o in shards:
    active(o);bpy.ops.rigidbody.object_remove();o.rotation_mode='QUATERNION'
    for p in record[o.name]:o.location=p['location'];o.rotation_quaternion=p['rotation'];o.keyframe_insert(data_path='location',frame=p['frame']);o.keyframe_insert(data_path='rotation_quaternion',frame=p['frame'])
for o in colliders:active(o);bpy.ops.rigidbody.object_remove()
(EP/'cache/rigidbody/EP002_Glass_Physical60_v011.json').write_text(json.dumps(record));report['Glass']={'fragments':len(shards),'frames':[442,616],'contact':'actual moving body; no floating shield','restitution':.06}
bpy.context.window.scene=main;bpy.data.scenes.remove(sim);main.frame_set(48);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v011.blend'),compress=True)
(EP/'edit/physical_solid_report_v011.json').write_text(json.dumps(report,indent=2));print('PHYSICAL_SOLIDS_COMPLETE '+json.dumps(report),flush=True)
