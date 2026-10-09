import bpy,math,json,random,struct,itertools
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender'); EP=ROOT/'02_EPISODES/EP002_Impossible_Blankets'; s=bpy.context.scene
C={n:bpy.data.collections['EP002_'+n] for n in ['ENVIRONMENT','BED','CHARACTER','LIGHTS','CAMERAS','UI','SLIME','GLASS','CLOTH','HONEY','SAND','WATER','LAVA']}
M={n:bpy.data.materials[n] for n in ['MAT_TestStage_Jelly_Green','MAT_Glass_Clear','MAT_Cloth_Neutral','MAT_Honey','MAT_Sand','MAT_Water','MAT_Lava','MAT_Light_Cyan','MAT_Ink_DeepNavy','MAT_UI_White']}
def key(o,path,f,value,index=-1):
    if index<0:setattr(o,path,value)
    else:getattr(o,path)[index]=value
    o.keyframe_insert(data_path=path,frame=f,index=index)
def prop(o,name,f,v):o[name]=v; o.keyframe_insert(data_path='["'+name+'"]',frame=f)
def visible(o,a,b):
    for f,v in [(1,True),(a,False),(b+1,True)]:key(o,'hide_render',f,v); key(o,'hide_viewport',f,v)
def mesh(name,verts,faces,mat,col):
    d=bpy.data.meshes.new(name+'_Mesh'); d.from_pydata(verts,[],faces); d.update(); o=bpy.data.objects.new(name,d); C[col].objects.link(o); d.materials.append(mat)
    for p in d.polygons:p.use_smooth=True
    return o
def box(name,loc,size,mat,col,bev=.05):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.view_layer.objects.active; o.name=name; o.data.name=name+'_Mesh'
    for c in list(o.users_collection):c.objects.unlink(o)
    C[col].objects.link(o); o.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(mat)
    if bev:
        b=o.modifiers.new('Soft edge radius','BEVEL'); b.width=bev; b.segments=3; o.modifiers.new('Weighted edge normals','WEIGHTED_NORMAL')
        for p in o.data.polygons:p.use_smooth=True
    return o
def sphere(name,loc,scale,mat,col):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc); o=bpy.context.view_layer.objects.active; o.name=name; o.data.name=name+'_Mesh'
    for c in list(o.users_collection):c.objects.unlink(o)
    C[col].objects.link(o); o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o
def sheet(name,col,mat,nx=25,ny=29,width=1.9,length=2.1):
    verts=[(-width/2+width*x/(nx-1),-length/2+length*y/(ny-1),.025*math.sin(x*.62)*math.sin(y*.41)) for y in range(ny) for x in range(nx)]; faces=[(y*nx+x,y*nx+x+1,(y+1)*nx+x+1,(y+1)*nx+x) for y in range(ny-1) for x in range(nx-1)]
    o=mesh(name,verts,faces,mat,col); o.location=(0,-.50,3.0); return o
def collision(o):
    if not any(m.type=='COLLISION' for m in o.modifiers):o.modifiers.new('Blanket collision','COLLISION')
    o.collision.thickness_outer=.025
def text_copy(name,body,size,loc):
    source=bpy.data.objects['UI_EP002_MaterialName']; o=source.copy(); o.data=source.data.copy(); o.name=name; o.data.body=body; o.data.size=size; o.location=loc; C['UI'].objects.link(o); return o
def clarity(src,name,amount):
    m=bpy.data.materials[src].copy(); m.name=name; n=m.node_tree.nodes; l=m.node_tree.links; out=n.get('Material Output'); p=n.get('Principled BSDF'); t=n.new('ShaderNodeBsdfTransparent'); mix=n.new('ShaderNodeMixShader'); mix.inputs[0].default_value=amount; l.new(p.outputs[0],mix.inputs[1]); l.new(t.outputs[0],mix.inputs[2]); l.new(mix.outputs[0],out.inputs[0]); return m
glass=clarity('MAT_Glass_Clear','MAT_TestStage_Glass_Preview',.40); water=clarity('MAT_Water','MAT_TestStage_Water_Preview',.28); shieldmat=clarity('MAT_Glass_Clear','MAT_TestStage_Shield',.88)
r=bpy.data.objects['RIG_BRIX']; head=r.pose.bones['head']; head.rotation_euler.x=.45
# Save clean reusable set and the new template before episode animation begins.
def write(path,blocks):
    p=ROOT/path; assert not p.exists(),'Do not overwrite reusable file: '+str(p); bpy.data.libraries.write(str(p),set(blocks),path_remap='RELATIVE_ALL',fake_user=True,compress=True)
clean=bpy.data.scenes.new('BRIX_TestStage'); clean.world=s.world; clean.camera=s.camera
for n in ['ENVIRONMENT','BED','LIGHTS','CAMERAS','UI']:clean.collection.children.link(C[n])
clean.render.engine='BLENDER_EEVEE'; clean.render.resolution_x=1080; clean.render.resolution_y=1920; clean.render.resolution_percentage=50; clean.render.fps=30; clean.eevee.use_raytracing=True; clean.view_settings.view_transform='AgX'
bpy.context.window.scene=clean
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'00_LIBRARY/Environments/BRIX_TestStage.blend'),copy=True,compress=True)
bpy.context.window.scene=s
bpy.data.scenes.remove(clean)
# The template is written as a full standalone scene, with only empty test collections.
s['production_role']='MASTER TEMPLATE v002: Save As into a new episode before editing.'; s.frame_end=240; s.render.filepath='//../03_FINAL_OUTPUT/YouTube/BRIX_'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'01_TEMPLATES/BRIX_Shorts_Master_v002.blend'),copy=True,compress=True)
s['production_role']='EP002 preview: original impossible blanket story'; s.frame_end=1125

# Static low mesh body collision proxies follow the visible supine silhouette.
proxies=[]
for name,loc,size in [('Torso',(0,-.03,1.39),(1.04,.98,.55)),('Legs',(0,-.96,1.42),(.92,1.05,.61)),('Feet',(0,-1.30,1.50),(1.03,.40,.62))]:
    o=box('COLL_EP002_'+name,loc,size,None,'CHARACTER',.07); o.hide_render=True; o.display_type='WIRE'; collision(o); proxies.append(o)
for name in ['PROP_TestBed_Mattress','PROP_TestBed_Pillow','PROP_TestBed_WalnutFrame']:collision(bpy.data.objects[name])
floor=box('COLL_EP002_Floor',(0,0,-.075),(9,9,.10),None,'BED',0); floor.hide_render=True; floor.display_type='WIRE'; collision(floor)

tests=[('SLIME',46,180,100),('GLASS',181,315,240),('CLOTH',316,450,365),('HONEY',451,585,526),('SAND',586,720,642),('WATER',721,855,776),('LAVA',856,1035,970)]
ui=bpy.data.objects['UI_EP002_MaterialSelector']; base=bpy.data.objects['UI_EP002_MaterialName']; base.hide_render=True; base.hide_viewport=True
for i,(name,a,b,impact) in enumerate(tests):
    o=text_copy('UI_EP002_Name_'+name,name,.042,(0,.376,-1)); visible(o,a,b); prop(ui,'selected_material',a,i)
prop(ui,'selected_material',1,0)
hook=bpy.data.objects['UI_EP002_Hook']; visible(hook,1,45)
outro=text_copy('UI_EP002_Outro','WHICH ONE\nWOULD YOU CHOOSE?',.032,(0,.377,-1)); outro.data.space_line=.8; visible(outro,1066,1125)
finalname=text_copy('UI_EP002_FinalMaterial','LAVA',.042,(0,.376,-1)); visible(finalname,1036,1065)
expressions=['NEUTRAL','CONFIDENT','CURIOUS','SUSPICIOUS','SURPRISED','SCARED','DISGUSTED','IMPRESSED','RELIEVED','EXCITED']
for e in expressions:prop(r,e,1,float(e=='RELIEVED'))
for p in ['blink','squint','wide_open','look_x','look_y','smile','nervous_smile','worried','frown','open_surprise','impressed_O']:prop(r,p,1,0.)
def expr(f,name):
    vals={e:0. for e in expressions}
    if name=='AMUSED':vals.update(RELIEVED=.4,EXCITED=.6)
    elif name=='ANNOYED':vals.update(DISGUSTED=.55,SUSPICIOUS=.45)
    elif name=='EXHAUSTED':vals.update(RELIEVED=.2,DISGUSTED=.45,SUSPICIOUS=.35)
    else:vals[name]=1.
    for p,v in vals.items():prop(r,p,f,v)
def pose(f,tilt=.45,yaw=0,arms=(0,0),fore=(0,0),torso=0):
    for name,rotation in [('head',(tilt,yaw,0)),('spine',(torso,0,0)),('upper_arm.L',(arms[0],0,-.12)),('upper_arm.R',(arms[1],0,.12)),('forearm.L',(fore[0],0,0)),('forearm.R',(fore[1],0,0))]:key(r.pose.bones[name],'rotation_euler',f,rotation)
pose(1)
for name,a,b,impact in tests:
    pose(a,tilt=.45); pose(a+22,tilt=.65,yaw=.05,arms=(.10,.10)); pose(impact+5,tilt=.68,arms=(.5,.55),fore=(-.45,-.55),torso=.035); pose(b-10,tilt=.48,yaw=.26,arms=(.1,.1))
for f,e in [(1,'RELIEVED'),(47,'CURIOUS'),(100,'SURPRISED'),(136,'AMUSED'),(181,'SUSPICIOUS'),(230,'SCARED'),(254,'SURPRISED'),(299,'ANNOYED'),(317,'SUSPICIOUS'),(372,'RELIEVED'),(410,'RELIEVED'),(452,'CURIOUS'),(526,'DISGUSTED'),(552,'ANNOYED'),(587,'CONFIDENT'),(645,'DISGUSTED'),(684,'ANNOYED'),(722,'CURIOUS'),(773,'SURPRISED'),(809,'ANNOYED'),(856,'ANNOYED'),(882,'CURIOUS'),(901,'SURPRISED'),(927,'SCARED'),(968,'SCARED'),(994,'RELIEVED'),(1031,'EXHAUSTED'),(1125,'EXHAUSTED')]:expr(f,e)
for f in [31,74,155,208,295,407,497,581,610,703,736,821,869,1002,1075]:
    for ff,v in [(f,0),(f+3,1),(f+7,0)]:prop(r,'blink',ff,v)
for f,x,y in [(1,.35,-.1),(69,0,.6),(107,.1,-.2),(166,.35,-.1),(217,0,.85),(255,.35,-.05),(348,0,.6),(408,.35,-.1),(482,0,.7),(555,.35,-.1),(623,0,.6),(687,.35,-.1),(757,0,.8),(815,.35,-.1),(881,0,.5),(908,.35,-.1),(923,0,.85),(1005,.35,-.1),(1039,.35,-.1),(1125,.35,-.1)]:prop(r,'look_x',f,x); prop(r,'look_y',f,y)
pose(141,tilt=.5,arms=(.65,.1),fore=(-.6,0)); pose(169,tilt=.45)
pose(239,tilt=.70,yaw=0,arms=(1.1,1.0),fore=(-1.2,-1.1)); pose(266,tilt=.55,yaw=.32,arms=(.5,.4))
for f in [393,402,412,421]:prop(r,'blink',f,1. if f in [402,412] else 0.)
for f,arms in [(655,(.7,.8)),(670,(.2,.6)),(684,(.8,.3)),(701,(.1,.2))]:pose(f,tilt=.55,yaw=.2,arms=arms,fore=(-.6,-.5))
pose(753,tilt=.7,torso=.12,arms=(.25,.25)); pose(779,tilt=.82,arms=(1.,.9),fore=(-.8,-.9),torso=.05)
pose(883,tilt=.68); pose(908,tilt=.55,yaw=.32); pose(930,tilt=.85,arms=(.8,.8)); pose(952,tilt=.8,yaw=-.25,arms=(1.2,1.1),fore=(-1,-1)); pose(992,tilt=.55,yaw=.2); pose(1036,tilt=.50,yaw=.32,arms=(.1,.15)); pose(1125,tilt=.50,yaw=.32,arms=(.1,.15))
# Small escape attempt, then a restrained final camera look.
for f,loc in [(1,(1.62,-1.45,1.025)),(930,(1.62,-1.45,1.025)),(956,(1.38,-1.49,1.05)),(979,(1.38,-1.49,1.05)),(1018,(1.62,-1.45,1.025)),(1125,(1.62,-1.45,1.025))]:key(r,'location',f,loc)

# Slime: optimized flexible volume mesh, with a designed wrap/jiggle deformation.
slime=box('FX_EP002_Slime_Blanket',(0,-.5,3.1),(1.88,2.08,.20),M['MAT_TestStage_Jelly_Green'],'SLIME',.09)
bpy.context.view_layer.objects.active=slime
for m in list(slime.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
sub=slime.modifiers.new('Light flexible lattice','SUBSURF'); sub.subdivision_type='SIMPLE'; sub.levels=2; bpy.ops.object.modifier_apply(modifier=sub.name)
slime.shape_key_add(name='Basis'); sk=slime.shape_key_add(name='BodyWrap')
for p,v in zip(sk.data,slime.data.vertices):
    x,y,z=v.co; center=max(0,1-(x/.95)**2); p.co=(x*1.10,y*1.04,z*.72+.28*center-.30*(abs(x)/.95)**3+.045*math.sin(y*8))
for f,z in [(66,3.1),(83,3.1),(98,1.62),(105,1.46),(118,1.50),(143,1.48),(176,1.48)]:key(slime,'location',f,z,2)
for f,v in [(66,0),(97,.10),(106,1),(116,.65),(130,.92),(143,.85),(176,.85)]:key(sk,'value',f,v)
for f,scale in [(98,(1,1,1)),(106,(1.10,1.02,.78)),(118,(.98,1,1.15)),(132,(1.02,1,.94)),(158,(1,1,1))]:key(slime,'scale',f,scale)
visible(slime,66,178); slime['method']='Optimized volume-preserving-ish keyed wrap deformation; no live soft-body solver.'

# Glass: twelve planar Voronoi fragments, each with real 12 mm thickness.
rng=random.Random(202); seeds=[Vector((rng.uniform(-.8,.8),rng.uniform(-.9,.9))) for _ in range(12)]
def clip(poly,n,d):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        va=n.dot(a)-d; vb=n.dot(b)-d
        if va<=0:out.append(a)
        if (va<=0)!=(vb<=0):out.append(a+(b-a)*(va/(va-vb)))
    return out
shards=[]
for i,seed in enumerate(seeds):
    poly=[Vector((-.90,-1.02)),Vector((.90,-1.02)),Vector((.90,1.02)),Vector((-.90,1.02))]
    for q in seeds:
        if (q-seed).length>1e-5:poly=clip(poly,q-seed,(q.length_squared-seed.length_squared)/2)
    center=sum(poly,Vector((0,0)))/len(poly); N=len(poly); verts=[(p.x-center.x,p.y-center.y,z) for z in [-.006,.006] for p in poly]; faces=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(j,(j+1)%N,(j+1)%N+N,j+N) for j in range(N)]
    o=mesh('FX_EP002_GlassShard_'+str(i+1).zfill(2),verts,faces,glass,'GLASS'); o.location=(center.x,center.y-.50,3.05); bev=o.modifiers.new('Glass edge polish','BEVEL'); bev.width=.002; bev.segments=2; o.modifiers.new('Plate normals','WEIGHTED_NORMAL')
    for p in o.data.polygons:p.use_smooth=False
    for f,z in [(201,3.05),(220,3.05),(238,2.26),(239,2.25)]:key(o,'location',f,(center.x,center.y-.50,z))
    # Fracture kick then physical ballistic trajectories sampled below.
    visible(o,201,309); shards.append(o)
glassshield=box('PROP_EP002_GlassCatchShield',(0,-.5,2.18),(2.04,2.26,.045),shieldmat,'GLASS',.035); visible(glassshield,228,309); glassshield['safety']='Physical collision barrier above BRIX, with clear face exclusion at head end.'

# Cloth: actual 31x35 simulation source, exported to MDD by a separate pass.
cloth=sheet('FX_EP002_Cloth_Blanket','CLOTH',M['MAT_Cloth_Neutral'],31,35,2.1,2.15); visible(cloth,337,446)

# Honey: optimized viscous ribbon/pool with stretching, folds and slow settling.
honey=sheet('FX_EP002_Honey_Blanket','HONEY',M['MAT_Honey'],23,27,1.7,1.95); honey.location.z=3.03; honey.shape_key_add(name='Basis'); hk=honey.shape_key_add(name='StickyFold')
for p,v in zip(hk.data,honey.data.vertices):
    x,y,z=v.co; p.co=(x*1.15,y*.99,.19*max(0,1-(x/.87)**2)-.20*(abs(x)/.87)**3+.075*math.sin(y*11)*math.cos(x*6))
solid=honey.modifiers.new('Honey volume','SOLIDIFY'); solid.thickness=.12; solid.offset=0
for f,z in [(474,3.03),(491,3.03),(512,2.65),(530,1.65),(550,1.47),(579,1.47)]:key(honey,'location',f,z,2)
for f,v in [(474,0),(510,.2),(537,.78),(564,1),(579,1)]:key(hk,'value',f,v)
for f,scale in [(474,(1,1,1)),(512,(.8,.9,1.6)),(542,(1.05,1.05,.85)),(579,(1.1,1.06,.82))]:key(honey,'scale',f,scale)
visible(honey,474,582)

# Sand: sheet/block collapses into a mound with 160 instanced granular tokens.
sand=sheet('FX_EP002_Sand_Mound','SAND',M['MAT_Sand'],25,29,1.85,2.12); sand.location.z=3.02; sand.shape_key_add(name='Basis'); mound=sand.shape_key_add(name='GranularCollapse')
for p,v in zip(mound.data,sand.data.vertices):
    x,y,z=v.co; p.co=(x*1.08,y*1.02,-.22+.50*max(0,1-(x/.95)**2)+.09*math.sin(y*6)+rng.uniform(-.03,.03))
sol=sand.modifiers.new('Contained sand depth','SOLIDIFY'); sol.thickness=.26; sol.offset=-1
for f,z in [(607,3.02),(626,3.02),(642,1.63),(652,1.53),(678,1.49)]:key(sand,'location',f,z,2)
for f,v in [(607,0),(641,.08),(657,.82),(682,1),(715,1)]:key(mound,'value',f,v)
visible(sand,607,715); grains=None
for i in range(160):
    if grains is None:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1); o=bpy.context.view_layer.objects.active; o.name='FX_EP002_SandGrain_001'
        for c in list(o.users_collection):c.objects.unlink(o)
        C['SAND'].objects.link(o); grains=o.data; grains.name='FX_EP002_InstancedGrain'; grains.materials.append(M['MAT_Sand'])
    else:o=bpy.data.objects.new('FX_EP002_SandGrain_'+str(i+1).zfill(3),grains); C['SAND'].objects.link(o)
    size=rng.uniform(.018,.035); o.scale=(size,size,size); x=rng.uniform(-.84,.84); y=rng.uniform(-1.45,.46); dx=rng.uniform(-.8,.8); dy=rng.uniform(-.2,.2)
    for f,loc in [(639,(x,y,2.05)),(651,(x+dx*.5,y+dy,1.9+rng.uniform(0,.3))),(676,(x+dx,y+dy,1.15 if abs(x+dx)<.9 else .035))]:key(o,'location',f,loc)
    visible(o,639,715)

# Water uses an actual small 32-division liquid scene (baked separately).
domain=box('FX_EP002_Water_Domain',(0,-.5,1.71),(2.85,3.00,3.50),water,'WATER',0); fm=domain.modifiers.new('32 division water preview','FLUID'); fm.fluid_type='DOMAIN'; bpy.context.view_layer.update(); d=fm.domain_settings; d.domain_type='LIQUID'; d.resolution_max=32; d.cache_type='ALL'; d.cache_frame_end=850; d.cache_frame_start=744; d.cache_directory='//../cache/fluid/water'; d.mesh_scale=1; d.use_mesh=True; d.mesh_particle_radius=1.65; d.mesh_smoothen_pos=2; d.mesh_smoothen_neg=2; d.timesteps_max=3
domain.display_type='WIRE'
# Domain must remain viewport-enabled throughout baking; render visibility is discrete.
for f,v in [(1,True),(744,False),(851,True)]:key(domain,'hide_render',f,v)
flow=box('FX_EP002_Water_Source',(0,-.50,3.08),(1.65,1.95,.27),M['MAT_Water'],'WATER',.05); flow.hide_render=True; flow.display_type='WIRE'; ff=flow.modifiers.new('Contained liquid source','FLUID'); ff.fluid_type='FLOW'; bpy.context.view_layer.update(); fs=ff.flow_settings; fs.flow_type='LIQUID'; fs.flow_behavior='GEOMETRY'
waterSim=bpy.data.scenes.new('SIM_EP002_Water'); waterSim.render.fps=30; waterSim.frame_start=744; waterSim.frame_end=850; waterSim.collection.objects.link(domain); waterSim.collection.objects.link(flow)
effectors=[]
for original in [bpy.data.objects['PROP_TestBed_Mattress']]+proxies:
    e=original.copy(); e.data=original.data.copy(); e.animation_data_clear(); e.name='COLL_EP002_Water_'+original.name; C['WATER'].objects.link(e); e.parent=None; e.matrix_world=original.matrix_world.copy(); e.hide_render=True; e.hide_viewport=False; e.display_type='WIRE'
    for mod in list(e.modifiers):
        if mod.type=='COLLISION':e.modifiers.remove(mod)
    ff=e.modifiers.new('Liquid collision','FLUID'); ff.fluid_type='EFFECTOR'; bpy.context.view_layer.update(); waterSim.collection.objects.link(e); effectors.append(e)

# Lava is a viscous optimized volume. A sliding shield locks under it just in time.
lavaMat=M['MAT_Lava'].copy(); lavaMat.name='MAT_TestStage_Lava_Crust'; p=lavaMat.node_tree.nodes.get('Principled BSDF'); p.inputs['Roughness'].default_value=.30; p.inputs['Emission Strength'].default_value=1.6
n=lavaMat.node_tree.nodes; l=lavaMat.node_tree.links; noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=6; noise.inputs['Detail'].default_value=2; noise.noise_dimensions='4D'
for f,w in [(876,0),(1034,.8)]:key(noise.inputs['W'],'default_value',f,w)
ram=n.new('ShaderNodeValToRGB'); ram.color_ramp.elements[0].position=.46; ram.color_ramp.elements[0].color=(.006,.0005,.0002,1); ram.color_ramp.elements[1].position=.63; ram.color_ramp.elements[1].color=(1,.15,.004,1); e=ram.color_ramp.elements.new(.59); e.color=(.8,.025,.001,1); l.new(noise.outputs['Fac'],ram.inputs[0]); l.new(ram.outputs[0],p.inputs['Base Color']); l.new(ram.outputs[0],p.inputs['Emission Color'])
lava=box('FX_EP002_Lava_Blanket',(0,-.5,3.02),(1.79,2.04,.23),lavaMat,'LAVA',.11); visible(lava,884,1033)
for f,z in [(884,3.02),(937,3.02),(956,2.75),(970,2.40),(985,2.37),(1033,2.37)]:key(lava,'location',f,z,2)
for f,sc in [(884,(1,1,1)),(970,(1.04,1.02,.78)),(988,(1.15,1.08,.46)),(1033,(1.17,1.09,.44))]:key(lava,'scale',f,sc)
shield=box('PROP_EP002_SafetyShield',(0,-.50,2.23),(2.13,2.38,.045),shieldmat,'LAVA',.035)
for f,x in [(1,3.4),(951,3.4),(963,0),(1034,0),(1053,3.4)]:key(shield,'location',f,x,0)
visible(shield,948,1053)
for name,x in [('L',-1.06),('R',1.06)]:
    edge=box('PROP_EP002_ShieldEdge_'+name,(x,-.50,2.24),(.02,2.37,.024),M['MAT_Light_Cyan'],'LAVA',.006); edge.parent=shield; edge.location=(x,0,.008); visible(edge,948,1053)
warm=bpy.data.lights.new('LIGHT_EP002_LavaGlow_Source','POINT'); warm.color=(1,.12,.01); warm.shadow_soft_size=.7; wo=bpy.data.objects.new('LIGHT_EP002_LavaGlow',warm); C['LAVA'].objects.link(wo); wo.location=(0,-.5,2.4)
for f,v in [(1,0),(880,0),(906,80),(962,220),(995,180),(1040,0)]:key(warm,'energy',f,v)

cam=s.camera; rot=cam.rotation_euler.copy()
for f,lens in [(1,70),(180,70),(246,72),(300,70),(855,70),(945,72),(995,70),(1050,73),(1125,73)]:key(cam.data,'lens',f,lens)
for f in [240,776,970]:
    for ff,offset in [(f-1,0),(f,.008),(f+2,-.005),(f+5,0)]:key(cam,'rotation_euler',ff,(rot.x+offset,rot.y,rot.z+offset*.3))
markers={'INTRO':1,'SELECT_SLIME':46,'SLIME_DROP':84,'SLIME_SQUISH':100,'BRIX_SLIME_REACTION':106,'SELECT_GLASS':181,'GLASS_DROP':221,'GLASS_SHATTER':240,'BRIX_GLASS_REACTION':255,'SELECT_CLOTH':316,'CLOTH_DROP':337,'CLOTH_SETTLE':397,'SELECT_HONEY':451,'HONEY_DROP':492,'HONEY_STRETCH':512,'SELECT_SAND':586,'SAND_RELEASE':628,'SAND_IMPACT':642,'SELECT_WATER':721,'WATER_RELEASE':744,'WATER_SPLASH':776,'SELECT_LAVA':856,'LAVA_WARNING':884,'LAVA_DROP':938,'SAFETY_SHIELD':963,'LAVA_IMPACT':970,'BRIX_FINAL_LOOK':1031,'OUTRO':1066}
for name,f in markers.items():s.timeline_markers.new(name,frame=f)
# All boolean and selector transitions are held, not interpolated.
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if fc.data_path in ['hide_render','hide_viewport','["selected_material"]']:
                        for kp in fc.keyframe_points:kp.interpolation='CONSTANT'
s.frame_set(24); s.render.resolution_percentage=35; s.eevee.taa_render_samples=32; s.render.filepath='//../previews/EP002_'; s['duration_seconds']=37.5; s['physics_methods']='Slime keyed wrap; glass small rigid-body scatter; cloth actual cached simulation; honey viscous deformation proxy; sand 160 instances+mound; water actual 32 div Mantaflow; lava shielded viscous proxy'
bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v004.blend'),compress=True)
(EP/'edit/storyboard.json').write_text(json.dumps({'title':"BRIX'S IMPOSSIBLE BLANKETS",'duration':37.5,'tests':tests,'markers':markers,'methods':s['physics_methods']},indent=2),encoding='utf-8'); print('COMPLETE_EP002_TIMELINE_READY')
