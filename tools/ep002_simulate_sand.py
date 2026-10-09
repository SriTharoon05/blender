import bpy,random,math,struct,json,sys,bmesh
from pathlib import Path
from mathutils import Vector
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');main=bpy.data.scenes['EP002_Impossible_Blankets'];C=bpy.data.collections['EP002_CHARACTER'];target=bpy.data.collections['EP002_SAND'];start,end=1256,1430
version=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '012'
if version=='015b':
    original_args=sys.argv[:];sys.argv=['blender','--','015a'];exec((EP.parent.parent/'tools/ep002_refine_slime.py').read_text(),{});sys.argv=original_args;bpy.context.window.scene=main
for old in list(target.objects):bpy.data.objects.remove(old,do_unlink=True)
sim=bpy.data.scenes.new('SIM_EP002_Physical_Sand');sim.render.fps=60;sim.frame_start=start;sim.frame_end=end;sim.collection.children.link(C);bpy.context.window.scene=sim
sources=[o for o in C.objects if o.name.startswith('COLL_EP002_Anatomy_')]+[bpy.data.objects[n] for n in ['PROP_TestBed_Mattress','PROP_TestBed_Pillow','PROP_TestBed_WalnutFrame','COLL_EP002_Floor']];colliders=[];bones={};rig=bpy.data.objects['RIG_BRIX'];sim.frame_set(start);dep=bpy.context.evaluated_depsgraph_get()
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.hide_viewport=False;o.select_set(True);bpy.context.view_layer.objects.active=o
for src in sources:
    if src.name not in sim.objects:sim.collection.objects.link(src)
    weights={g.index:0 for g in src.vertex_groups}
    for v in src.data.vertices:
        for g in v.groups:weights[g.group]+=g.weight
    bone=src.vertex_groups[max(weights,key=weights.get)].name if weights else None
    if bone and bone not in rig.pose.bones:bone=None
    B=rig.matrix_world@rig.pose.bones[bone].matrix if bone else src.matrix_world.copy();inv=B.inverted();e=src.evaluated_get(dep);me=e.to_mesh();vs=[tuple(inv@(e.matrix_world@v.co)) for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons];e.to_mesh_clear();data=bpy.data.meshes.new('SandContact_'+src.name);data.from_pydata(vs,[],faces);data.update();o=bpy.data.objects.new('SIM_SandContact_'+src.name,data);sim.collection.objects.link(o);o.matrix_world=B;o.rotation_mode='QUATERNION';o.hide_render=True;colliders.append(o)
    if bone:bones[o]=bone
for f in range(start,end+1):
    sim.frame_set(f);bpy.context.view_layer.update()
    for o,bone in bones.items():
        o.matrix_world=rig.matrix_world@rig.pose.bones[bone].matrix;o.keyframe_insert(data_path='location',frame=f);o.keyframe_insert(data_path='rotation_quaternion',frame=f)
sim.collection.children.unlink(C)
for src in sources:
    if src.name in sim.collection.objects:sim.collection.objects.unlink(src)
sim.frame_set(start)
for o in colliders:
    active(o);bpy.ops.rigidbody.object_add();b=o.rigid_body;b.type='PASSIVE';b.kinematic=True;b.collision_shape='CONVEX_HULL';b.mesh_source='BASE';b.use_deform=False;b.friction=.65;b.use_margin=True;b.collision_margin=.002
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1);tmp=bpy.context.object;grain_mesh=tmp.data;grain_mesh.name='Physical_Granule_Convex';bpy.data.objects.remove(tmp,do_unlink=True)
bm=bmesh.new();bm.from_mesh(grain_mesh);unit_volume=abs(bm.calc_volume());bm.free()
rng=random.Random(2277);grains=[];radii=[]
for z in range(3):
    for y in range(25):
        for x in range(20):
            i=len(grains);o=bpy.data.objects.new('SIM_Grain_'+str(i),grain_mesh);sim.collection.objects.link(o);radius=rng.uniform(.032,.036);radii.append(radius);o.scale=(radius,radius*.94,radius*1.08);o.location=((x-9.5)*.08+rng.uniform(-.002,.002),-.96+(y-12)*.08+rng.uniform(-.002,.002),3.12+z*.08);o.rotation_euler=[rng.uniform(-math.pi,math.pi) for _ in range(3)]
            grains.append(o)
            if i%500==0:print('GRAIN_BUILD',i,flush=True)
bpy.ops.object.select_all(action='DESELECT')
for o in grains:o.select_set(True)
bpy.context.view_layer.objects.active=grains[0];bpy.ops.rigidbody.objects_add(type='ACTIVE')
for o,radius in zip(grains,radii):
    b=o.rigid_body;b.mass=2650*unit_volume*radius**3*.94*1.08;b.collision_shape='CONVEX_HULL';b.use_margin=True;b.collision_margin=.0008;b.friction=.72;b.restitution=.015;b.linear_damping=.08;b.angular_damping=.15
world=sim.rigidbody_world;world.point_cache.frame_end=end;world.point_cache.frame_start=start;world.substeps_per_frame=4;world.solver_iterations=15
path=EP/'cache/particles'/('EP002_Granular_Physical60_v'+version+'.mdd');N=len(grains);initial=[];ranges={}
for g in grains:
    initial.extend([tuple(g.matrix_world@v) for v in [Vector((0,0,0)),Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]])
with path.open('wb') as file:
    file.write(struct.pack('>2i',end-start+1,N*4));file.write(struct.pack('>'+str(end-start+1)+'f',*[i/60 for i in range(end-start+1)]))
    for f in range(start,end+1):
        sim.frame_set(f);bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();vs=[]
        for g in grains:
            matrix=g.evaluated_get(dep).matrix_world;vs.extend([tuple(matrix@v) for v in [Vector((0,0,0)),Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]])
        assert all(math.isfinite(v) for p in vs for v in p);file.write(struct.pack('>'+str(12*N)+'f',*[a for p in vs for a in p]))
        if (f-start)%30==0:print('GRANULAR_PROGRESS',f,flush=True);ranges[f]=[min(v[2] for v in vs[::4]),max(v[2] for v in vs[::4])]
for o in colliders:bpy.data.objects.remove(o,do_unlink=True)
for o in grains:bpy.data.objects.remove(o,do_unlink=True)
bpy.context.window.scene=main;bpy.data.scenes.remove(sim)
me=bpy.data.meshes.new('Physical_Granular_Points');me.from_pydata(initial,[],[]);me.update();attr=me.attributes.new('grain_radius','FLOAT','POINT')
ids=me.attributes.new('grain_index','INT','POINT')
for i in range(N*4):attr.data[i].value=radii[i//4];ids.data[i].value=i//4
o=bpy.data.objects.new('FX_EP002_Sand_GranularBody',me);target.objects.link(o);cache=o.modifiers.new('Actual granular dynamics cache','MESH_CACHE');cache.cache_format='MDD';cache.filepath='//../cache/particles/'+path.name;cache.frame_start=start;cache.interpolation='LINEAR'
mat=bpy.data.materials['MAT_Sand'].copy();mat.name='MAT_EP002_GranularSand';p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.82
noise=mat.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=140;noise.inputs['Detail'].default_value=3;bump=mat.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.35;bump.inputs['Distance'].default_value=.0015;mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);mat.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
ng=bpy.data.node_groups.new('EP002_PhysicalGranule_Instances','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=ng.nodes;L=ng.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');pts=n.new('GeometryNodeMeshToPoints');pts.mode='VERTICES';ico=n.new('GeometryNodeMeshIcoSphere');ico.inputs['Radius'].default_value=1;ico.inputs['Subdivisions'].default_value=1;sm=n.new('GeometryNodeSetMaterial');sm.inputs['Material'].default_value=mat;inst=n.new('GeometryNodeInstanceOnPoints');a=n.new('GeometryNodeInputNamedAttribute');a.data_type='FLOAT';a.inputs['Name'].default_value='grain_radius';xyz=n.new('ShaderNodeCombineXYZ')
L.new(inp.outputs['Geometry'],pts.inputs['Mesh']);L.new(ico.outputs['Mesh'],sm.inputs['Geometry']);L.new(sm.outputs['Geometry'],inst.inputs['Instance']);L.new(pts.outputs['Points'],inst.inputs['Points'])
idx=n.new('GeometryNodeInputIndex');modulo=n.new('ShaderNodeMath');modulo.operation='MODULO';modulo.inputs[1].default_value=4;select=n.new('ShaderNodeMath');select.operation='LESS_THAN';select.inputs[1].default_value=.5;L.new(idx.outputs[0],modulo.inputs[0]);L.new(modulo.outputs[0],select.inputs[0]);L.new(select.outputs[0],pts.inputs['Selection'])
gid=n.new('GeometryNodeInputNamedAttribute');gid.data_type='INT';gid.inputs['Name'].default_value='grain_index';mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=4;L.new(gid.outputs['Attribute'],mult.inputs[0]);position=n.new('GeometryNodeInputPosition');samples=[]
for offset in range(4):
    add=n.new('ShaderNodeMath');add.operation='ADD';add.inputs[1].default_value=offset;L.new(mult.outputs[0],add.inputs[0]);sample=n.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';L.new(inp.outputs['Geometry'],sample.inputs['Geometry']);L.new(position.outputs[0],sample.inputs['Value']);L.new(add.outputs[0],sample.inputs['Index']);samples.append(sample.outputs['Value'])
directions=[]
for i in [1,3]:
    sub=n.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';L.new(samples[i],sub.inputs[0]);L.new(samples[0],sub.inputs[1]);directions.append(sub.outputs['Vector'])
az=n.new('FunctionNodeAlignEulerToVector');az.axis='Z';L.new(directions[1],az.inputs['Vector']);ax=n.new('FunctionNodeAlignEulerToVector');ax.axis='X';ax.pivot_axis='Z';L.new(az.outputs['Rotation'],ax.inputs['Rotation']);L.new(directions[0],ax.inputs['Vector']);L.new(ax.outputs['Rotation'],inst.inputs['Rotation'])
for axis,factor in [('X',1),('Y',.94),('Z',1.08)]:
    scale=n.new('ShaderNodeMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=factor;L.new(a.outputs['Attribute'],scale.inputs[0]);L.new(scale.outputs[0],xyz.inputs[axis])
L.new(xyz.outputs[0],inst.inputs['Scale']);L.new(inst.outputs['Instances'],out.inputs['Geometry']);mod=o.modifiers.new('Detailed physical sand grains','NODES');mod.node_group=ng
for f,v in [(1,True),(start,False),(1431,True)]:o.hide_render=v;o.keyframe_insert(data_path='hide_render',frame=f)
main.frame_set(48);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend'/('EP002_v'+version+'.blend')),compress=True)
report={'rigid_body_grains':N,'frames':[start,end],'radii_m':[min(radii),max(radii)],'restitution':.015,'friction':.72,'range_samples':ranges,'cache':str(path.relative_to(EP))};(EP/'edit'/('physical_sand_report_v'+version+'.json')).write_text(json.dumps(report,indent=2));print('ACTUAL_GRANULAR_SOLVER_COMPLETE',json.dumps(report),flush=True)
