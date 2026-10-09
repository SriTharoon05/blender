import bpy,json,bmesh
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');main=bpy.data.scenes['EP002_Impossible_Blankets'];C=bpy.data.collections['EP002_CHARACTER'];shards=sorted([o for o in main.objects if o.name.startswith('FX_EP002_GlassShard_')],key=lambda o:o.name);colliders=[o for o in C.objects if o.name.startswith('COLL_EP002_Anatomy_')]+[bpy.data.objects[n] for n in ['PROP_TestBed_Mattress','PROP_TestBed_Pillow','PROP_TestBed_WalnutFrame','COLL_EP002_Floor']]
sim=bpy.data.scenes.new('SIM_EP002_Glass_FinalContact');sim.render.fps=60;sim.frame_start=442;sim.frame_end=616;sim.collection.children.link(C)
for o in shards+colliders:
    if o.name not in sim.objects:sim.collection.objects.link(o)
bpy.context.window.scene=sim;sim.frame_set(442)
def active(o):bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.hide_viewport=False;o.select_set(True);bpy.context.view_layer.objects.active=o
for o in shards:
    active(o);bpy.ops.rigidbody.object_add();b=o.rigid_body;bm=bmesh.new();bm.from_mesh(o.data);b.mass=max(.1,abs(bm.calc_volume())*2500);bm.free();b.collision_shape='CONVEX_HULL';b.use_margin=True;b.collision_margin=.001;b.restitution=.06;b.friction=.7;b.linear_damping=.12;b.angular_damping=.3
for o in colliders:
    active(o);bpy.ops.rigidbody.object_add();b=o.rigid_body;b.type='PASSIVE';b.kinematic=True;b.collision_shape='MESH';b.mesh_source='FINAL';b.use_deform=True;b.friction=.65;b.use_margin=True;b.collision_margin=.003
pairs=set();joints=[]
for i,o in enumerate(shards):
    nearest=sorted([j for j in range(len(shards)) if j!=i],key=lambda j:(shards[j].location-o.location).length)[:3]
    for j in nearest:pairs.add(tuple(sorted((i,j))))
for i,j in sorted(pairs):
    a,b=shards[i],shards[j];joint=bpy.data.objects.new('SIM_GlassBreakJoint_'+str(i)+'_'+str(j),None);sim.collection.objects.link(joint);joint.location=(a.location+b.location)*.5;active(joint);bpy.ops.rigidbody.constraint_add();c=joint.rigid_body_constraint;c.type='FIXED';c.object1=a;c.object2=b;c.use_breaking=True;c.breaking_threshold=4;c.disable_collisions=True;joints.append(joint)
world=sim.rigidbody_world;world.point_cache.frame_end=616;world.point_cache.frame_start=442;world.substeps_per_frame=10;world.solver_iterations=30;records={o.name:[] for o in shards}
for f in range(442,617):
    sim.frame_set(f);bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
    for o in shards:
        loc,rot,scale=o.evaluated_get(dep).matrix_world.decompose();records[o.name].append({'frame':f,'location':list(loc),'rotation':list(rot)})
for o in shards:
    active(o);bpy.ops.rigidbody.object_remove();o.rotation_mode='QUATERNION'
    for p in records[o.name]:o.location=p['location'];o.rotation_quaternion=p['rotation'];o.keyframe_insert(data_path='location',frame=p['frame']);o.keyframe_insert(data_path='rotation_quaternion',frame=p['frame'])
for o in colliders:active(o);bpy.ops.rigidbody.object_remove()
for joint in joints:bpy.data.objects.remove(joint,do_unlink=True)
bpy.context.window.scene=main;bpy.data.scenes.remove(sim);main.frame_set(48);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v015c.blend'),compress=True);(EP/'cache/rigidbody/EP002_Glass_Physical60_v015c.json').write_text(json.dumps(records));print('GLASS_FINAL_CONTACT_COMPLETE')
