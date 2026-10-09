import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender'); EP=ROOT/'02_EPISODES/EP002_Impossible_Blankets'; s=bpy.data.scenes['EP002_Impossible_Blankets']; bpy.context.window.scene=s
C={n:bpy.data.collections['EP002_'+n] for n in ['CHARACTER','BED','SLIME','GLASS','CLOTH','HONEY','SAND','WATER','LAVA','UI']}
def key(o,path,f,v,index=-1):
    if index<0:setattr(o,path,v)
    else:getattr(o,path)[index]=v
    o.keyframe_insert(data_path=path,frame=f,index=index)
def vis(o,a,b):
    for f,v in [(1,True),(a,False),(b+1,True)]:key(o,'hide_render',f,v)
def box(name,loc,size,col,mat=None,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    C[col].objects.link(o);o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(mat)
    if bevel:
        m=o.modifiers.new('Rounded edges','BEVEL');m.width=bevel;m.segments=3
    return o
def mesh(name,verts,faces,col,mat):
    me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);C[col].objects.link(o);me.materials.append(mat)
    for p in me.polygons:p.use_smooth=True
    return o
# Correct arm direction: the previous positive FK rotation drove hands into the mattress.
r=bpy.data.objects['RIG_BRIX']
for layer in r.animation_data.action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fc in bag.fcurves:
                factor=None
                if 'upper_arm.' in fc.data_path and 'rotation_euler' in fc.data_path and fc.array_index==0:factor=-.62
                if 'forearm.' in fc.data_path and 'rotation_euler' in fc.data_path and fc.array_index==0:factor=.42
                if factor is not None:
                    for p in fc.keyframe_points:p.co.y*=factor;p.handle_left.y*=factor;p.handle_right.y*=factor
# Replace only generated EP002 test objects; keep the existing shared masters untouched.
for n in ['SLIME','CLOTH','HONEY','SAND','WATER']:
    for o in list(C[n].objects):bpy.data.objects.remove(o,do_unlink=True)
for o in list(C['LAVA'].objects):
    if o.name.startswith('FX_'):bpy.data.objects.remove(o,do_unlink=True)
if 'SIM_EP002_Water' in bpy.data.scenes:bpy.data.scenes.remove(bpy.data.scenes['SIM_EP002_Water'])
for o in list(C['CHARACTER'].objects):
    if o.name.startswith('COLL_EP002_'):bpy.data.objects.remove(o,do_unlink=True)
if 'PROP_EP002_GlassCatchShield' in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects['PROP_EP002_GlassCatchShield'],do_unlink=True)
# True moving body colliders. Copies retain the original armature modifier and follow every FK pose.
colliders=[];names=['Body','Jacket_Hem','ChestBadge','Neck','Head','Thigh_L','Thigh_R','Shin_L','Shin_R','Boot_L','Boot_R','BootSole_L','BootSole_R','BootAccent_L','BootAccent_R','UpperArm_L','UpperArm_R','Forearm_L','Forearm_R','Cuff_L','Cuff_R','Hand_L','Hand_R','Thumb_L','Thumb_R']
for name in names:
    src=bpy.data.objects['CHAR_BRIX_'+name];o=src.copy();o.data=src.data.copy();o.name='COLL_EP002_Anatomy_'+name;o.animation_data_clear();o.hide_render=True;o.hide_viewport=False;o.display_type='WIRE';C['CHARACTER'].objects.link(o)
    for m in list(o.modifiers):
        if m.type in ['COLLISION','FLUID','RIGID_BODY']:o.modifiers.remove(m)
    cm=o.modifiers.new('Moving body contact','COLLISION');o.collision.thickness_outer=.018;o.collision.thickness_inner=.012;o.collision.damping=.35;o.collision.cloth_friction=60
    colliders.append(o)
for name in ['PROP_TestBed_Mattress','PROP_TestBed_Pillow','PROP_TestBed_WalnutFrame','COLL_EP002_Floor']:
    o=bpy.data.objects[name]
    if not any(m.type=='COLLISION' for m in o.modifiers):o.modifiers.new('Material contact','COLLISION')
    o.collision.thickness_outer=.012;colliders.append(o)
# Wider blankets include the toes and side drapes, while their head edge stops below the face.
nx,ny=25,33;w,l=2.10,2.54;verts=[]
for z in [-.09,.09]:verts.extend([(-w/2+w*x/(nx-1),-l/2+l*y/(ny-1),z) for y in range(ny) for x in range(nx)])
N=nx*ny;faces=[]
for off in [0,N]:
    for y in range(ny-1):
        for x in range(nx-1):
            q=(off+y*nx+x,off+y*nx+x+1,off+(y+1)*nx+x+1,off+(y+1)*nx+x);faces.append(q if off else tuple(reversed(q)))
border=list(range(nx))+[y*nx+nx-1 for y in range(1,ny)]+list(range(N-2,N-nx-1,-1))+[y*nx for y in range(ny-2,0,-1)]
for a,b in zip(border,border[1:]+border[:1]):faces.append((a,b,b+N,a+N))
slime=mesh('FX_EP002_Slime_Blanket',verts,faces,'SLIME',bpy.data.materials['MAT_TestStage_Jelly_Green']);slime.location=(0,-.96,3.18)
# Internal vertical springs make this a deformable volume, rather than a sheet with a preset shape.
edges=[(i,i+N) for i in range(N) if i not in set(border)];old=slime.data;me=bpy.data.meshes.new('Slime_VolumetricSpringMesh');me.from_pydata(verts,edges,faces);me.update();me.materials.append(old.materials[0]);slime.data=me
for p in me.polygons:p.use_smooth=True
sb=slime.modifiers.new('Viscoelastic spring volume','SOFT_BODY');st=sb.settings;st.use_goal=False;st.use_edges=True;st.pull=.30;st.push=.30;st.damping=8;st.bend=.4;st.use_stiff_quads=True;st.use_edge_collision=True;st.use_face_collision=True;st.use_self_collision=False;st.step_min=20;st.step_max=150;st.mass=.35
sb.point_cache.frame_end=178;sb.point_cache.frame_start=84;vis(slime,84,178);slime['method']='Actual soft-body viscoelastic spring volume with internal thickness springs and animated anatomical collisions.'
# Real woven cloth; high mesh density makes shoulder, toe and side contact readable.
nx,ny=45,55;w,l=2.35,2.65;vs=[(-w/2+w*x/(nx-1),-l/2+l*y/(ny-1),.008*math.sin(x*.9)*math.sin(y*.6)) for y in range(ny) for x in range(nx)];fs=[(y*nx+x,y*nx+x+1,(y+1)*nx+x+1,(y+1)*nx+x) for y in range(ny-1) for x in range(nx-1)]
cloth=mesh('FX_EP002_Cloth_Blanket',vs,fs,'CLOTH',bpy.data.materials['MAT_Cloth_Neutral']);cloth.location=(0,-.78,3.15)
for v in cloth.data.vertices:v.co.y*=2.12/2.65
cm=cloth.modifiers.new('Moving body fabric simulation','CLOTH');st=cm.settings;st.quality=20;st.mass=.22;st.tension_stiffness=35;st.compression_stiffness=35;st.shear_stiffness=18;st.bending_stiffness=.6;st.air_damping=3;cm.collision_settings.use_self_collision=True;cm.collision_settings.self_distance_min=.009;cm.collision_settings.distance_min=.018;cm.collision_settings.collision_quality=8;cm.point_cache.frame_end=446;cm.point_cache.frame_start=337;vis(cloth,337,446)
# Glass fragments stay assembled until release, then gravity/contact determine their motion.
s.frame_set(201)
for o in [o for o in C['GLASS'].objects if o.name.startswith('FX_EP002_GlassShard_')]:
    pos=o.location.copy();o.animation_data_clear();o.rotation_mode='XYZ';o.rotation_euler=(0,0,0);o.location=(pos.x,pos.y-.40,3.17);o.hide_viewport=False;vis(o,221,309)
# Clear containment shield appears as an intentional mechanism for the lava test.
shield=bpy.data.objects['PROP_EP002_SafetyShield'];shield.animation_data_clear();shield.location=(3.4,-.96,2.03);shield.scale=(1,1,1);shield.dimensions=(2.2,2.64,.065)
for f,x in [(1,3.4),(938,3.4),(949,0),(1034,0),(1050,3.4)]:key(shield,'location',f,x,0)
vis(shield,938,1050)
for name in ['L','R']:
    edge=bpy.data.objects['PROP_EP002_ShieldEdge_'+name];edge.animation_data_clear();edge.location=(1.09 if name=='R' else -1.09,0,.028);edge.dimensions=(.025,2.63,.032);vis(edge,938,1050)
for name,y in [('Head',1.31),('Foot',-1.31)]:
    edge=box('PROP_EP002_ShieldRim_'+name,(0,0,0),(2.18,.025,.15),'LAVA',bpy.data.materials['MAT_Light_Cyan'],.008);edge.parent=shield;edge.location=(0,y,.075);vis(edge,938,1050)
# Small transparent raised rim physically catches the viscous lava instead of letting it touch BRIX.
for name,x in [('L',-1.10),('R',1.10)]:
    wall=box('COLL_EP002_ShieldWall_'+name,(0,0,0),(.035,2.64,.20),'LAVA',bpy.data.materials['MAT_TestStage_Shield'],.01);wall.parent=shield;wall.location=(x,0,.115);vis(wall,938,1050)
src=bpy.data.objects['UI_EP002_MaterialName'];label=src.copy();label.data=src.data.copy();label.name='UI_EP002_ShieldLocked';label.data.body='SHIELD LOCKED';label.data.size=.014;label.location=(0,.251,-1);C['UI'].objects.link(label);vis(label,949,1033)
# Actual three liquid domains, each with material-specific viscosity and open spill boundaries.
config={
 'HONEY':dict(start=492,end=582,res=64,viscosity=.12,material='MAT_Honey',dims=(3.3,4.1,3.7),source=(2.0,2.5,.24)),
 'WATER':dict(start=744,end=850,res=72,viscosity=0,material='MAT_Water',dims=(4.6,5.2,3.7),source=(2.0,2.5,.24)),
 'LAVA':dict(start=938,end=1033,res=56,viscosity=.6,material='MAT_TestStage_Lava_Crust',dims=(3.4,4.3,3.7),source=(1.92,2.28,.22))}
for name,c in config.items():
    mat=bpy.data.materials[c['material']].copy();mat.name='MAT_EP002_Physical_'+name
    p=mat.node_tree.nodes.get('Principled BSDF')
    if name in ['HONEY','WATER']:
        p.inputs['Transmission Weight'].default_value=.82 if name=='HONEY' else 1;p.inputs['Roughness'].default_value=.10 if name=='HONEY' else .055;p.inputs['IOR'].default_value=1.47 if name=='HONEY' else 1.333
        p.inputs['Base Color'].default_value=(.8,.32,.035,1) if name=='HONEY' else (.68,.91,1,1)
    domain=box('FX_EP002_'+name.title()+'_Domain',(0,-.87,1.68),c['dims'],name,mat);fm=domain.modifiers.new(name+' physical liquid','FLUID');fm.fluid_type='DOMAIN';bpy.context.view_layer.update();d=fm.domain_settings;d.domain_type='LIQUID';d.resolution_max=c['res'];d.cache_type='ALL';d.cache_frame_end=c['end'];d.cache_frame_start=c['start'];d.cache_directory='//../cache/fluid/physical_'+name.lower()+'_v010';d.use_mesh=True;d.mesh_scale=2;d.mesh_particle_radius=1.3;d.mesh_smoothen_pos=2;d.mesh_smoothen_neg=2;d.timesteps_max=6;d.timesteps_min=2;d.flip_ratio=.95 if name=='WATER' else .65;d.use_viscosity=bool(c['viscosity']);d.viscosity_value=max(.000001,c['viscosity']);d.use_collision_border_bottom=False;d.use_collision_border_front=False;d.use_collision_border_back=False;d.use_collision_border_left=False;d.use_collision_border_right=False
    d.use_speed_vectors=True
    if hasattr(d,'surface_tension'):d.surface_tension=.072 if name=='WATER' else (.08 if name=='HONEY' else .35)
    vis(domain,c['start'],c['end']);domain.display_type='WIRE'
    flow=box('FX_EP002_'+name.title()+'_Source',(0,-.96,3.17),c['source'],name,None,.04);flow.hide_render=True;flow.display_type='WIRE';ff=flow.modifiers.new('Initial slab liquid volume','FLUID');ff.fluid_type='FLOW';bpy.context.view_layer.update();ff.flow_settings.flow_type='LIQUID';ff.flow_settings.flow_behavior='GEOMETRY';ff.flow_settings.use_plane_init=False
    sim=bpy.data.scenes.new('SIM_EP002_Physical_'+name);sim.render.fps=30;sim.frame_start=c['start'];sim.frame_end=c['end'];sim.collection.objects.link(domain);sim.collection.objects.link(flow);sim.collection.children.link(C['CHARACTER'])
    originals=colliders if name!='LAVA' else [shield]+[bpy.data.objects[n] for n in ['COLL_EP002_ShieldWall_L','COLL_EP002_ShieldWall_R','PROP_EP002_ShieldRim_Head','PROP_EP002_ShieldRim_Foot']]
    for src in originals:
        o=src.copy();o.data=src.data.copy();o.name='COLL_EP002_'+name+'_'+src.name
        for m in list(o.modifiers):
            if m.type in ['COLLISION','FLUID']:o.modifiers.remove(m)
        o.hide_render=True;o.hide_viewport=False;C[name].objects.link(o);sim.collection.objects.link(o);fm=o.modifiers.new('Animated liquid obstacle','FLUID');fm.fluid_type='EFFECTOR';bpy.context.view_layer.update();fm.effector_settings.surface_distance=.003
    # Source and domain visibility never disable viewport during the solver pass.
    domain['physical_parameters']=json.dumps(c)
s['physics_methods']='Actual soft-body slime; rigid-body glass; self-colliding cloth; viscous honey liquid; rigid-body granular sand; water FLIP liquid; viscous lava liquid on safety shield. All body collision meshes follow the rig.'
s.timeline_markers['LAVA_IMPACT'].frame=954;s.timeline_markers['SAFETY_SHIELD'].frame=949
# Resample production timing to true 60 FPS before any new simulations are evaluated.
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for p in fc.keyframe_points:
                        if 'rotation_euler' in fc.data_path and fc.array_index==0 and any(t in fc.data_path for t in ['upper_arm.','forearm.']) and 316<=p.co.x<=450:p.co.y=0;p.handle_left.y=0;p.handle_right.y=0
                        p.co.x*=2;p.handle_left.x*=2;p.handle_right.x*=2
for scene in bpy.data.scenes:
    scene.render.fps=60;scene.render.fps_base=1;scene.frame_start=max(1,scene.frame_start*2);scene.frame_end*=2
for o in bpy.data.objects:
    for m in o.modifiers:
        if m.type in ['SOFT_BODY','CLOTH']:m.point_cache.frame_end*=2;m.point_cache.frame_start*=2
        if m.type=='FLUID' and m.fluid_type=='DOMAIN':m.domain_settings.cache_frame_end*=2;m.domain_settings.cache_frame_start*=2
for marker in s.timeline_markers:marker.frame*=2
for c in config.values():c['start']*=2;c['end']*=2
s.frame_start=1;s.render.resolution_x=2160;s.render.resolution_y=3840;s.frame_set(48);s.render.resolution_percentage=25;s.eevee.taa_render_samples=64;s.eevee.use_raytracing=True;s.eevee.shadow_ray_count=3;s.render.use_simplify=False
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v010.blend'),compress=True)
(EP/'edit/physical_liquid_plan_v010.json').write_text(json.dumps(config,indent=2));print('PHYSICAL_REBUILD_READY')
