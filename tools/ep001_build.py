import bpy, math, random, json, itertools
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender'); EP=ROOT/'02_EPISODES/EP001_Material_Test'
s=bpy.context.scene; s.name='EP001_Material_Test'; s.frame_start=1; s.frame_end=1290; s.render.fps=30
assert 'EP001_v001' in bpy.data.filepath
for o in list(bpy.data.objects):
    if o.name.startswith('Cube') or o.name.startswith('TEMP_'):bpy.data.objects.remove(o,do_unlink=True)
def coll(name):
    c=bpy.data.collections.new(name); s.collection.children.link(c); return c
FX=coll('EP001_TestAssets'); COLL=coll('EP001_Colliders'); CT=coll('EP001_Controls')
def put(o,c):
    for old in list(o.users_collection):old.objects.unlink(o)
    c.objects.link(o); return o
def objmesh(name,verts,faces,mat,c=FX):
    me=bpy.data.meshes.new(name+'_Mesh'); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); c.objects.link(o)
    if mat:me.materials.append(bpy.data.materials[mat])
    return o
def cube(name,loc,size,mat,bevel=.04,c=FX):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=put(bpy.context.view_layer.objects.active,c); o.name=name; o.data.name=name+'_Mesh'; o.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(bpy.data.materials[mat])
    if bevel:
        b=o.modifiers.new('Rounded edges','BEVEL'); b.width=bevel; b.segments=3
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
        for p in o.data.polygons:p.use_smooth=True
    return o
def sphere(name,loc,scale,mat,segments=24,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc); o=put(bpy.context.view_layer.objects.active,FX); o.name=name; o.data.name=name+'_Mesh'; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(bpy.data.materials[mat])
    for p in o.data.polygons:p.use_smooth=True
    return o
def key(o,path,f,value,index=-1):
    if index<0:setattr(o,path,value)
    else:getattr(o,path)[index]=value
    o.keyframe_insert(data_path=path,frame=f,index=index)
def prop(o,name,f,value):o[name]=value; o.keyframe_insert(data_path='["'+name+'"]',frame=f)
def visible(o,start,end):
    for f,v in [(1,True),(start,False),(end+1,True)]:
        key(o,'hide_render',f,v); key(o,'hide_viewport',f,v)
def collision(o):
    m=o.modifiers.new('Preview collision','COLLISION'); o.collision.thickness_outer=.015; return m
def active(o):bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
def rigid(o,typ='ACTIVE'):
    active(o); bpy.ops.rigidbody.object_add(); o.rigid_body.type=typ; o.rigid_body.collision_shape='CONVEX_HULL'; o.rigid_body.use_margin=True; o.rigid_body.collision_margin=.005; o.rigid_body.friction=.5; return o.rigid_body
sample=bpy.data.objects['PROP_MaterialSample']; sample.hide_render=True; sample.hide_viewport=True
# Reuse a library collider geometry, with an episode-specific physics modifier.
platform=bpy.data.objects['PROP_TestPlatform_Pad']; collision(platform); rigid(platform,'PASSIVE')
floor=cube('EP001_CollisionFloor',(1.05,.35,.46),(3.4,3.4,.17),None,0,COLL); floor.hide_render=True; collision(floor); rigid(floor,'PASSIVE')
s.rigidbody_world.point_cache.frame_start=241; s.rigidbody_world.point_cache.frame_end=390; s.rigidbody_world.substeps_per_frame=3; s.rigidbody_world.solver_iterations=12

# Episode UI uses the existing camera mounted type and selector system.
title=bpy.data.objects['UI_Title']; title.data.body="BRIX'S\nMATERIAL TEST"; title.data.size=.037; title.data.space_line=.9; title.location.y=.372
bpy.data.objects['UI_TitleRule'].location.y=.29
template=bpy.data.objects['UI_Parameter']; template.hide_render=True; template.hide_viewport=True
testrows=[('SLIME',91,240,150,'SOFTNESS: HIGH'),('GLASS',241,390,302,'THICKNESS: 0.5 cm'),('CLOTH',391,540,450,'SOFTNESS: 80%'),('WATER',541,690,586,'VISCOSITY: LOW'),('HONEY',691,840,765,'VISCOSITY: HIGH'),('SAND',841,990,909,'GRAIN SIZE: SMALL'),('LAVA',991,1170,1100,'TEMPERATURE: EXTREME')]
ui=bpy.data.objects['CTRL_UI']
for i,(name,start,end,impact,param) in enumerate(testrows):
    o=template.copy(); o.data=template.data.copy(); o.name='EP001_UI_Parameter_'+name; bpy.data.collections['ASSET_MobileUI'].objects.link(o); o.data.body=name+'  /  '+param; o.data.size=.0125; o.data.bevel_depth=0; o.data.extrude=0; o.location.y=.264; visible(o,start,end); prop(ui,'selected_material',start,i)
for o in bpy.data.collections['ASSET_MobileUI'].objects:
    if o.type=='FONT':o.data.bevel_depth=0; o.data.extrude=0
caption=bpy.data.objects['UI_MaterialSelector_Caption']; caption.data.body='MATERIAL SEQUENCE'; caption.data.size=.012
intro=template.copy(); intro.data=template.data.copy(); intro.name='EP001_UI_Intro'; bpy.data.collections['ASSET_MobileUI'].objects.link(intro); intro.data.body='SEVEN MATERIALS. ONE VERY BAD IDEA.'; intro.data.size=.011; intro.data.bevel_depth=0; intro.location.y=.264; visible(intro,1,90)
outro=template.copy(); outro.data=template.data.copy(); outro.name='EP001_UI_Final'; bpy.data.collections['ASSET_MobileUI'].objects.link(outro); outro.data.body='CONTAINED. CONFIDENCE: 0%'; outro.data.size=.014; outro.data.bevel_depth=0; outro.location.y=.264; visible(outro,1171,1290)
prop(ui,'selected_material',1,0)
# UI selections and visibility use constant key interpolation.

r=bpy.data.objects['RIG_BRIX']; expressions=['NEUTRAL','CONFIDENT','CURIOUS','SUSPICIOUS','SURPRISED','SCARED','DISGUSTED','IMPRESSED','RELIEVED','EXCITED']
manual=['blink','squint','wide_open','look_x','look_y','smile','nervous_smile','open_surprise','frown','worried','impressed_O']
for name in expressions+manual:prop(r,name,1,float(name=='CONFIDENT'))
def expression(f,name,blend=8):
    # AMUSED and CONCERNED are performances made from existing controls.
    amounts={x:0. for x in expressions+['worried','smile','squint']}
    if name=='AMUSED':amounts.update(EXCITED=.6,RELIEVED=.4)
    elif name=='CONCERNED':amounts.update(SUSPICIOUS=.35,SCARED=.5,worried=.4)
    elif name=='ANNOYED':amounts.update(DISGUSTED=.55,SUSPICIOUS=.45)
    else:amounts[name]=1.
    for p,v in amounts.items():prop(r,p,f,v)
def pose(f,head=0,lean=0,arms=(0,0),fore=(0,0),crouch=0):
    for name,rot in [('head',(lean,head,0)),('spine',(lean*.6,0,0)),('upper_arm.L',(0,0,arms[0])),('upper_arm.R',(0,0,arms[1])),('forearm.L',(fore[0],0,-.15)),('forearm.R',(fore[1],0,.15)),('thigh.L',(crouch,0,0)),('thigh.R',(crouch,0,0)),('shin.L',(-crouch*1.7,0,0)),('shin.R',(-crouch*1.7,0,0))]:
        b=r.pose.bones[name]; b.rotation_mode='XYZ'; key(b,'rotation_euler',f,rot)
    b=r.pose.bones['pelvis']; key(b,'location',f,(0,-crouch*.13,0))
pose(1,head=.22,arms=(-.12,.08)); key(r,'location',1,(-1.05,0,0)); key(r,'location',24,(0,0,0))
# Walk to the console, press, then return to the left of the experiment.
key(r,'location',38,(3.12,-.05,0)); key(r,'location',72,(3.12,-.05,0)); key(r,'location',95,(0,0,0))
for f in range(1,96,6):
    a=.32*math.sin(f*.34) if f<38 or f>72 else 0
    for side,sgn in [('L',1),('R',-1)]:
        b=r.pose.bones['thigh.'+side]; key(b,'rotation_euler',f,(a*sgn,0,0)); b=r.pose.bones['shin.'+side]; key(b,'rotation_euler',f,(max(0,-a*sgn)*.55,0,0))
pose(38,head=1.9,arms=(-.12,-.5),fore=(0,-.65)); pose(58,head=1.9,arms=(-.12,-.5),fore=(0,-.65)); pose(74,head=.7); pose(95,head=.22,arms=(-.1,.1))
# A transient IK constraint guides the existing right arm to the actual button.
reach=bpy.data.objects.new('CTRL_EP001_ButtonReach',None); CT.objects.link(reach); reach.location=(2.38,-.08,1.59); reach.empty_display_type='SPHERE'; reach.empty_display_size=.08
ik=r.pose.bones['forearm.R'].constraints.new('IK'); ik.name='Episode button reach'; ik.target=reach; ik.chain_count=2
for f,v in [(1,0),(42,0),(54,1),(66,1),(76,0)]:key(ik,'influence',f,v)
button=bpy.data.objects['PROP_ControlButton']; bz=button.location.z
for f,z in [(1,bz),(57,bz),(63,bz-.075),(70,bz-.075),(77,bz)]:key(button,'location',f,z,2)
press=bpy.data.objects['CTRL_Experiment_Press']
for f,v in [(1,0),(78,0),(89,-.30),(1190,-.30)]:prop(press,'travel_m',f,v)
beats=[(1,'CONFIDENT'),(95,'CONFIDENT'),(149,'CONFIDENT'),(158,'SURPRISED'),(188,'AMUSED'),(233,'CURIOUS'),(270,'CURIOUS'),(305,'SURPRISED'),(325,'SCARED'),(370,'RELIEVED'),(397,'SUSPICIOUS'),(454,'CURIOUS'),(495,'IMPRESSED'),(535,'RELIEVED'),(551,'CURIOUS'),(590,'SURPRISED'),(625,'ANNOYED'),(680,'CONCERNED'),(701,'CURIOUS'),(750,'DISGUSTED'),(800,'IMPRESSED'),(850,'CONFIDENT'),(916,'ANNOYED'),(972,'CONCERNED'),(996,'CONFIDENT'),(1021,'CURIOUS'),(1035,'SURPRISED'),(1060,'SCARED'),(1132,'SCARED'),(1174,'RELIEVED'),(1210,'ANNOYED'),(1250,'RELIEVED')]
for f,e in beats:expression(f,e)
for start,end,impact in [(91,240,150),(241,390,302),(391,540,450),(541,690,586),(691,840,765),(841,990,909)]:
    pose(start,head=.45,arms=(-.10,.08)); pose(impact-10,head=.65,lean=.07,fore=(-.18,-.12)); pose(impact+8,head=.24,lean=-.10,arms=(-.45,.45),fore=(-.7,-.8),crouch=.14); pose(end-18,head=.22,arms=(-.1,.1),fore=(-.1,-.15))
pose(330,head=.5,lean=.18,arms=(-.75,.75),fore=(-1.1,-1.1),crouch=.6)
pose(578,head=.78,lean=.24,fore=(-.2,-.2)); pose(601,head=.2,lean=-.18,arms=(-.8,.3),fore=(-1,-.5))
pose(926,head=.34,arms=(-.9,.18),fore=(-1,-.3)); pose(943,head=.32,arms=(-.3,.1),fore=(-.3,-.2)); pose(959,head=.31,arms=(-.85,.1),fore=(-.9,-.1))
pose(996,head=.45); pose(1038,head=.24,arms=(-.2,.2)); pose(1052,head=.75); pose(1070,head=.28,lean=-.12,arms=(-.9,.9),fore=(-1.05,-1),crouch=.15); pose(1115,head=.7,lean=-.18,arms=(-1.0,1),fore=(-1.2,-1.1),crouch=.35); pose(1177,head=.3,fore=(-.7,-.6)); pose(1220,head=.24,lean=.04,arms=(-.13,.13),fore=(-.25,-.2)); pose(1290,head=.24)
for f,loc in [(95,(0,0,0)),(1035,(0,0,0)),(1072,(-.22,.18,0)),(1096,(-.48,.35,0)),(1130,(-.65,.46,0)),(1180,(-.48,.3,0)),(1240,(-.3,.15,0)),(1290,(-.3,.15,0))]:key(r,'location',f,loc)
for f in [116,207,274,411,512,552,645,733,824,877,956,1020,1165,1241]:
    for ff,v in [(f,0),(f+3,1),(f+7,0)]:prop(r,'blink',ff,v)
for f,x,y in [(1,0,0),(95,.55,-.25),(154,.6,-.4),(220,0,0),(290,.7,-.25),(334,.6,-.3),(495,.5,-.4),(572,.85,-.45),(613,0,0),(749,.7,-.5),(802,.7,-.5),(909,.6,-.45),(1036,0,.3),(1053,.8,.1),(1090,.9,-.3),(1175,.4,-.4),(1210,0,0),(1290,0,0)]:prop(r,'look_x',f,x); prop(r,'look_y',f,y)

# Camera retains the established framing, with restrained push-ins and shakes.
cam=s.camera; cam.animation_data_clear(); loc=cam.location.copy(); rot=cam.rotation_euler.copy()
for f,lens in [(1,72),(91,72),(241,72),(330,75),(390,72),(541,72),(641,74),(690,72),(991,72),(1060,74),(1130,73),(1170,72),(1240,79),(1290,79)]:key(cam.data,'lens',f,lens)
for f in [150,302,586,909,1100]:
    for ff,delta in [(f-1,0),(f,.025),(f+2,-.018),(f+5,0)]:key(cam,'rotation_euler',ff,(rot.x+delta*.12,rot.y,rot.z+delta*.10))

# SLIME: actual low mesh soft-body, no large simulation.
slime=cube('EP001_Slime',(1.05,.35,2.48),(.76,.76,.76),'MAT_Jelly_Red',.10)
active(slime)
for m in list(slime.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
# A compact subdivision supplies spring structure, applied before the solver.
sub=slime.modifiers.new('Preview spring lattice','SUBSURF'); sub.subdivision_type='SIMPLE'; sub.levels=1; active(slime); bpy.ops.object.modifier_apply(modifier=sub.name)
sb=slime.modifiers.new('Lightweight jelly soft-body','SOFT_BODY'); st=sb.settings; st.use_goal=False; st.use_edges=True; st.pull=.8; st.push=.8; st.damping=8; st.bend=3; st.use_stiff_quads=True; st.step_min=2; st.step_max=12
sb.point_cache.frame_start=115; sb.point_cache.frame_end=225; sb.point_cache.use_disk_cache=True; sb.point_cache.filepath='//../cache/softbody/'; visible(slime,115,235)

# GLASS: 14 true volumetric Voronoi cells, not a high fragment-count fracture.
rng=random.Random(1001); seeds=[Vector((rng.uniform(-.37,.37),rng.uniform(-.37,.37),rng.uniform(-.37,.37))) for _ in range(14)]
def cell(seed):
    planes=[(Vector((1,0,0)),.4),(Vector((-1,0,0)),.4),(Vector((0,1,0)),.4),(Vector((0,-1,0)),.4),(Vector((0,0,1)),.4),(Vector((0,0,-1)),.4)]
    for p in seeds:
        if (p-seed).length>.0001:planes.append((p-seed,(p.length_squared-seed.length_squared)/2))
    points=[]
    for a,b,c in itertools.combinations(planes,3):
        from mathutils import Matrix
        mat=Matrix((a[0],b[0],c[0]))
        if abs(mat.determinant())<1e-7:continue
        p=mat.inverted() @ Vector((a[1],b[1],c[1]))
        if all(n.dot(p)<=d+1e-5 for n,d in planes) and not any((p-q).length<1e-4 for q in points):points.append(p)
    faces=[]
    for n,d in planes:
        ids=[i for i,p in enumerate(points) if abs(n.dot(p)-d)<1e-4]
        if len(ids)<3:continue
        center=sum((points[i] for i in ids),Vector())/len(ids); u=n.cross(Vector((0,0,1)))
        if u.length<.01:u=n.cross(Vector((0,1,0)))
        u.normalize(); v=n.normalized().cross(u)
        ids.sort(key=lambda i:math.atan2((points[i]-center).dot(v),(points[i]-center).dot(u))); faces.append(ids)
    return points,faces
shards=[]
for i,seed in enumerate(seeds):
    pts,faces=cell(seed); center=sum(pts,Vector())/len(pts); o=objmesh('EP001_GlassShard_'+str(i+1).zfill(2),[p-center for p in pts],faces,'MAT_Glass_Clear'); o.location=Vector((1.05,.35,2.4))+center
    b=o.modifiers.new('Shard edge highlights','BEVEL'); b.width=.004; b.segments=2
    body=rigid(o); body.mass=.08; body.restitution=.12; body.kinematic=True
    key(body,'kinematic',241,True); key(body,'kinematic',301,True); key(body,'kinematic',302,False)
    for f,z in [(265,2.4),(289,1.8),(300,1.03)]:key(o,'location',f,(1.05+center.x,.35+center.y,z+center.z))
    key(o,'location',301,(1.05+center.x*1.06,.35+center.y*1.06,1.01+center.z)); visible(o,265,380); shards.append(o)

# CLOTH: 25x25 drape, 625 vertices, no self-collision.
N=25; verts=[(-.85+1.7*x/(N-1),-.85+1.7*y/(N-1),.015*math.sin(x*.8)*math.sin(y*.6)) for y in range(N) for x in range(N)]; faces=[(y*N+x,y*N+x+1,(y+1)*N+x+1,(y+1)*N+x) for y in range(N-1) for x in range(N-1)]
cloth=objmesh('EP001_Cloth',verts,faces,'MAT_Cloth_Neutral'); cloth.location=(1.05,.35,2.38); cloth.rotation_euler.z=.24; cm=cloth.modifiers.new('Low mesh fabric drape','CLOTH'); cs=cm.settings; cs.quality=4; cs.mass=.25; cs.tension_stiffness=12; cs.compression_stiffness=12; cs.shear_stiffness=8; cs.bending_stiffness=.4; cm.collision_settings.use_self_collision=False; cm.point_cache.frame_start=417; cm.point_cache.frame_end=525; cm.point_cache.use_disk_cache=True; cm.point_cache.filepath='//../cache/cloth/'; solid=cloth.modifiers.new('Fabric thickness','SOLIDIFY'); solid.thickness=.012; visible(cloth,417,535)
support=sample.copy(); support.data=sample.data; support.name='EP001_ClothSupport'; FX.objects.link(support); support.animation_data_clear(); support.hide_render=False; support.hide_viewport=False; support.data=sample.data.copy(); support.data.materials.clear(); support.data.materials.append(bpy.data.materials['MAT_Stone_Rough']); visible(support,391,535); collision(support)

# WATER/HONEY: two small 32-division Mantaflow domains; bake sequentially.
fluids=[]
for name,start,end,mat,visc,scale in [('Water',566,675,'MAT_Water',0,1),('Honey',716,825,'MAT_Honey',.08,.48)]:
    domain=cube('EP001_'+name+'_Domain',(1.05,.35,1.68),(2.22,2.22,2.20),mat,0)
    fm=domain.modifiers.new('32 division liquid preview','FLUID'); fm.fluid_type='DOMAIN'; bpy.context.view_layer.update(); d=fm.domain_settings; d.domain_type='LIQUID'; d.resolution_max=32; d.cache_type='ALL'; d.cache_frame_start=start; d.cache_frame_end=end; d.cache_directory='//../cache/fluid/'+name.lower(); d.use_mesh=True; d.mesh_scale=1; d.mesh_particle_radius=1.7; d.mesh_smoothen_pos=2; d.mesh_smoothen_neg=2; d.timesteps_min=1; d.timesteps_max=3; d.time_scale=scale
    if visc:d.use_viscosity=True; d.viscosity_value=visc
    visible(domain,start,end)
    flow=sphere('EP001_'+name+'_Source',(1.05,.35,2.36),(.34,.34,.34) if name=='Water' else (.19,.19,.49),mat)
    flow.hide_render=True; flow.display_type='WIRE'; mod=flow.modifiers.new('Initial liquid volume','FLUID'); mod.fluid_type='FLOW'; bpy.context.view_layer.update(); fs=mod.flow_settings; fs.flow_type='LIQUID'; fs.flow_behavior='GEOMETRY'
    # Domain bottom is positioned exactly over the platform: the box border
    # provides a stable small containment area for this preview.
    sim=bpy.data.scenes.new('SIM_EP001_'+name); sim.render.fps=30; sim.frame_start=start; sim.frame_end=end; sim.collection.objects.link(domain); sim.collection.objects.link(flow); fluids.append((domain,flow,sim))

# SAND: animated shape collapse plus 96 instanced grains (no rigid-body swarm).
sand=cube('EP001_Sand_Block',(1.05,.35,2.4),(.77,.77,.77),'MAT_Sand',.035); visible(sand,865,975)
for f,loc,scale in [(865,(1.05,.35,2.4),(1,1,1)),(891,(1.05,.35,1.55),(1,1,1)),(908,(1.05,.35,.97),(1,1,1)),(929,(1.05,.35,.73),(1.8,1.8,.37)),(950,(1.05,.35,.66),(2.1,2.1,.21))]:key(sand,'location',f,loc); key(sand,'scale',f,scale)
grainmesh=None
for i in range(96):
    if grainmesh is None:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1); o=put(bpy.context.view_layer.objects.active,FX); o.name='EP001_SandGrain_001'; grainmesh=o.data; grainmesh.name='EP001_SandGrain_InstancedMesh'; grainmesh.materials.append(bpy.data.materials['MAT_Sand'])
    else:o=bpy.data.objects.new('EP001_SandGrain_'+str(i+1).zfill(3),grainmesh); FX.objects.link(o)
    angle=rng.uniform(0,math.tau); radius=rng.uniform(.1,1); size=rng.uniform(.025,.045); o.scale=(size,size*.8,size*.75)
    for f,loc in [(906,(1.05+math.cos(angle)*.32,.35+math.sin(angle)*.32,.99)),(918,(1.05+math.cos(angle)*radius,.35+math.sin(angle)*radius,rng.uniform(.82,1.25))),(939,(1.05+math.cos(angle)*radius,.35+math.sin(angle)*radius,.60+size))]:key(o,'location',f,loc)
    visible(o,906,978)

# LAVA: explicit viscous proxy; no fluid bake or volumetrics.
lavaMat=bpy.data.materials['MAT_Lava'].copy(); lavaMat.name='MAT_EP001_Lava_Crust'; lavaMat.use_fake_user=True
n=lavaMat.node_tree.nodes; l=lavaMat.node_tree.links; p=n.get('Principled BSDF'); p.inputs['Roughness'].default_value=.32
noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=5; noise.inputs['Detail'].default_value=2
ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.36; ramp.color_ramp.elements[0].color=(.006,.001,.001,1); ramp.color_ramp.elements[1].position=.65; ramp.color_ramp.elements[1].color=(1,.07,.003,1); l.new(noise.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],p.inputs['Base Color']); l.new(ramp.outputs[0],p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value=2.3
lava=sphere('EP001_Lava_ViscousProxy',(1.05,.35,2.6),(.35,.35,.48),'MAT_Lava'); lava.data.materials[0]=lavaMat; visible(lava,1045,1185)
for f,loc,scale in [(1045,(1.05,.35,2.6),(1,1,1)),(1075,(1.05,.35,2.35),(.8,.8,1.3)),(1100,(1.05,.35,1.17),(.9,.9,1.5)),(1118,(1.05,.35,.83),(1.7,1.7,.45)),(1140,(1.05,.35,.74),(2,2,.25)),(1185,(1.05,.35,.73),(2.1,2.1,.23))]:key(lava,'location',f,loc); key(lava,'scale',f,scale)
warm=bpy.data.lights.new('LIGHT_EP001_LavaGlow','POINT'); warm.color=(1,.16,.025); warm.shadow_soft_size=.6; lo=bpy.data.objects.new('LIGHT_EP001_LavaGlow',warm); FX.objects.link(lo); lo.location=(1.05,.35,1.0)
for f,power in [(1,0),(1035,0),(1085,105),(1110,190),(1160,130),(1200,0)]:key(warm,'energy',f,power)
# Reuse the safety shield mesh for three extra episode-only containment panels.
shield=bpy.data.objects['PROP_SafetyShield']; shield.animation_data_clear()
for f,z in [(1,-.7),(1045,-.7),(1084,1.13),(1180,1.13),(1210,-.7)]:key(shield,'location',f,z,2)
for name,loc,rot in [('Front',(1.05,-.65,1.13),math.pi/2),('Back',(1.05,1.35,1.13),math.pi/2),('Left',(.06,.35,1.13),0)]:
    o=shield.copy(); o.data=shield.data; o.animation_data_clear(); o.name='EP001_Containment_'+name; FX.objects.link(o); o.rotation_euler.z=rot; o.location=loc
    for f,z in [(1,-.7),(1045,-.7),(1084,1.13),(1180,1.13),(1210,-.7)]:key(o,'location',f,z,2)
# Front transparency occasionally occludes fine features in EEVEE; actual panel
# thickness and edges are preserved and the glass material stays reusable.

markers={'BUTTON_CLICK':63,'MACHINE_MOVE':82,'SLIME_SQUISH':150,'GLASS_CRACK':302,'CLOTH_FLAP':450,'WATER_SPLASH':586,'HONEY_STRETCH':765,'SAND_POUR':909,'LAVA_SIZZLE':1100,'BRIX_REACTION':158,'FINAL_COMEDY_BEAT':1230,'SHIELD_LOCK':1084}
s.timeline_markers.clear()
for name,frame in markers.items():s.timeline_markers.new(name,frame=frame)
for i,(name,a,b,impact,param) in enumerate(testrows):s.timeline_markers.new('TEST_'+name,frame=a)
# Discrete visibility and state controls must not interpolate.
def curves(action):
    for layer in action.layers:
        for strip in layer.strips:
            if hasattr(strip,'channelbags'):
                for bag in strip.channelbags:
                    for fc in bag.fcurves:yield fc
for action in bpy.data.actions:
    for fc in curves(action):
        if fc.data_path in ['hide_render','hide_viewport','kinematic','["selected_material"]']:
            for kp in fc.keyframe_points:kp.interpolation='CONSTANT'
s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=1080; s.render.resolution_y=1920; s.render.resolution_percentage=25; s.eevee.taa_render_samples=32; s.eevee.shadow_ray_count=2; s.render.filepath='//../previews/EP001_Preview.png'; s['production_role']='EPISODE PREVIEW / no final high-resolution bake / no final output'; s['duration_seconds']=43; s['simulation_plan']='Soft-body: ~300 vertices; glass:14 cells; cloth:625 verts; water/honey:32 div; sand:96 instances; lava:animated proxy'
text=bpy.data.texts.new('EP001_Storyboard'); text.write(json.dumps({'duration':43,'tests':testrows,'markers':markers,'simulation_limits':s['simulation_plan']},indent=2))
s.frame_set(1); bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP001_v002.blend'),compress=True)
(EP/'edit/storyboard.json').write_text(text.as_string(),encoding='utf-8')
print('EPISODE_TIMELINE_BUILT '+str(len(bpy.data.objects))+' objects; saved v002')
