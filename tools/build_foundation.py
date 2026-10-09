"""BRIX foundation v001. Run through Blender MCP; no external dependencies."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender')
FOLDERS=['00_LIBRARY/Characters/BRIX/textures','00_LIBRARY/Materials','00_LIBRARY/Props','00_LIBRARY/Environments','00_LIBRARY/UI','00_LIBRARY/Lighting','00_LIBRARY/Cameras','00_LIBRARY/Textures','01_TEMPLATES','02_EPISODES','03_FINAL_OUTPUT/YouTube','03_FINAL_OUTPUT/Instagram','03_FINAL_OUTPUT/TikTok','01_TEMPLATES/Previews','01_TEMPLATES/Versions','tools']
for p in FOLDERS: (ROOT/p).mkdir(parents=True,exist_ok=True)
assert not (ROOT/'01_TEMPLATES/BRIX_Shorts_Master.blend').exists(), 'Canonical master exists: create a new version instead.'
assert not (ROOT/'00_LIBRARY/Characters/BRIX/BRIX_Master.blend').exists(), 'Character master already exists.'
# The initial scene was inspected and contains only the unsaved default starter objects.
for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
scene=bpy.context.scene
scene.name='BRIX_Shorts_Foundation'
def collection(name):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); return c
CHAR=collection('ASSET_BRIX'); ENV=collection('ASSET_Lab'); PROPS=collection('ASSET_ExperimentStation'); LIGHTS=collection('ASSET_StudioLighting'); CAMS=collection('ASSET_VerticalCamera'); UI=collection('ASSET_MobileUI')
def put(o,c):
    for old in list(o.users_collection): old.objects.unlink(o)
    c.objects.link(o); return o
def material(name,col,rough=.35,metal=0,trans=0,sss=0,bump=.0,scale=35):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.use_fake_user=True
    m.diffuse_color=(*col,1); n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*col,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal; p.inputs['Transmission Weight'].default_value=trans; p.inputs['Subsurface Weight'].default_value=sss
    if bump:
        tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=scale; tex.inputs['Detail'].default_value=2
        b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=.18; b.inputs['Distance'].default_value=bump
        l.new(tex.outputs['Fac'],b.inputs['Height']); l.new(b.outputs['Normal'],p.inputs['Normal'])
        ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color=(*[x*.8 for x in col],1); ramp.color_ramp.elements[1].color=(*col,1)
        l.new(tex.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs['Color'],p.inputs['Base Color'])
    m.asset_mark(); return m
M={}
specs=[('Metal_Brushed',(.38,.49,.54),.29,.85,0,0,.006,120),('Metal_Chrome',(.7,.82,.9),.13,1,0,0,0,35),('Wood_Warm',(.36,.16,.055),.37,0,0,0,.018,5),('Stone_Rough',(.25,.29,.31),.8,0,0,0,.025,32),('Plastic_Blue',(.018,.32,.47),.27,0,0,0,.002,80),('Plastic_Orange',(.95,.18,.028),.3,0,0,0,.002,70),('Glass_Clear',(.7,.92,1),.09,0,1,0,0,35),('Jelly_Red',(.8,.018,.04),.2,0,.65,.15,.006,10),('Jelly_Blue',(.025,.36,.9),.18,0,.7,.12,.006,10),('Cloth_Neutral',(.74,.77,.72),.72,0,0,0,.004,160),('Water',(.72,.9,.98),.07,0,1,0,0,35),('Honey',(.65,.22,.012),.17,0,.8,.04,.003,15),('Sand',(.62,.4,.15),.86,0,0,0,.012,160),('Lava',(.52,.018,.001),.4,0,0,0,.015,7)]
for name,*args in specs: M[name]=material('MAT_'+name,*args)
# Directional grain and anisotropic brushed metal, all procedural.
wood=M['Wood_Warm']; tex=next(n for n in wood.node_tree.nodes if n.type=='TEX_NOISE'); mapping=wood.node_tree.nodes.new('ShaderNodeVectorMath'); mapping.operation='MULTIPLY'; mapping.inputs[1].default_value=(1,28,3); coord=wood.node_tree.nodes.new('ShaderNodeTexCoord'); wood.node_tree.links.new(coord.outputs['Generated'],mapping.inputs[0]); wood.node_tree.links.new(mapping.outputs[0],tex.inputs['Vector'])
M['Metal_Brushed'].node_tree.nodes.get('Principled BSDF').inputs['Anisotropic'].default_value=.4
for name,ior in [('Water',1.333),('Honey',1.47),('Glass_Clear',1.45),('Jelly_Red',1.38),('Jelly_Blue',1.38)]: M[name].node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=ior
p=M['Lava'].node_tree.nodes.get('Principled BSDF'); p.inputs['Emission Color'].default_value=(1,.035,.002,1); p.inputs['Emission Strength'].default_value=.6
M['Skin']=material('MAT_BRIX_Porcelain',(.94,.62,.32),.38,sss=.06,bump=.001)
M['Ink']=material('MAT_Ink_DeepNavy',(.009,.018,.035),.28)
M['White']=material('MAT_Ceramic_Ivory',(.88,.94,.92),.24)
M['Floor']=material('MAT_Lab_SatinCyan',(.11,.24,.29),.36,bump=.003)
M['Wall']=material('MAT_Lab_SoftBlue',(.055,.16,.23),.6,bump=.002)
M['Rubber']=material('MAT_Rubber_Graphite',(.017,.032,.039),.68,bump=.003)
M['Cheek']=material('MAT_BRIX_Coral',(.92,.19,.09),.5)
def emission(name,col,power):
    m=material(name,col,.3); p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Emission Color'].default_value=(*col,1); p.inputs['Emission Strength'].default_value=power; return m
M['Glow']=emission('MAT_Light_Cyan',(.035,.72,1),3)
M['WarmGlow']=emission('MAT_Light_Amber',(1,.19,.025),3)
M['UIWhite']=emission('MAT_UI_White',(.82,.96,1),1)
def finish(o,name,mat,c):
    o.name=name; o.data.name=name+'_Geometry'; put(o,c)
    if mat:o.data.materials.append(mat)
    return o
def box(name,loc,size,mat,c,bevel=.06):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=finish(bpy.context.object,name,mat,c); o.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('Soft manufactured edges','BEVEL'); b.width=bevel; b.segments=3
        b=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL'); b.keep_sharp=True
    return o
def uv(name,loc,size,mat,c):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc); o=finish(bpy.context.object,name,mat,c); o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return o
def cyl(name,loc,radius,depth,mat,c):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth,location=loc); o=finish(bpy.context.object,name,mat,c)
    b=o.modifiers.new('Machined edge radius','BEVEL'); b.width=.035; b.segments=3
    o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    for p in o.data.polygons:p.use_smooth=True
    return o
def line(name,pts,radius,mat,c):
    d=bpy.data.curves.new(name+'_Curve','CURVE'); d.dimensions='3D'; d.resolution_u=12; d.bevel_depth=radius; d.bevel_resolution=3
    s=d.splines.new('POLY'); s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new(name,d); c.objects.link(o); d.materials.append(mat); return o
def text(name,body,loc,size,mat,c,align='CENTER'):
    d=bpy.data.curves.new(name+'_Typography','FONT'); d.body=body; d.align_x=align; d.size=size; d.extrude=.001; d.bevel_depth=.0005
    font=Path('C:/Windows/Fonts/arialbd.ttf')
    if font.exists():d.font=bpy.data.fonts.load(str(font),check_existing=True)
    o=bpy.data.objects.new(name,d); c.objects.link(o); o.location=loc; o.rotation_euler=(math.pi/2,0,0); d.materials.append(mat); return o

# Original character: soft rectangular head, swept hair, cropped technical jacket.
cx=-1.62; cy=-.35
parts={}
def cb(name,loc,size,mat,bone,bev=.06):
    o=box('CHAR_BRIX_'+name,(cx+loc[0],cy+loc[1],loc[2]),size,M[mat],CHAR,bev); parts[o]=bone; return o
def cs(name,loc,size,mat,bone):
    o=uv('CHAR_BRIX_'+name,(cx+loc[0],cy+loc[1],loc[2]),size,M[mat],CHAR); parts[o]=bone; return o
cb('Body',(0,0,1.39),(.85,.53,.83),'Plastic_Blue','spine',.13)
cb('Jacket_Hem',(0,-.012,1.05),(.88,.56,.13),'Plastic_Orange','spine',.04)
cb('Neck',(0,0,1.91),(.29,.3,.2),'Skin','head',.06)
cb('Head',(0,0,2.47),(1.18,.8,1.04),'Skin','head',.19)
cb('Hair_Crown',(0,.07,2.98),(1.21,.79,.3),'Ink','head',.13)
o=cb('Hair_SweptFringe',(-.22,-.335,2.91),(.71,.23,.28),'Ink','head',.10); o.rotation_euler.y=-.14
cb('Hair_SideLock_R',(.5,.015,2.76),(.16,.69,.36),'Ink','head',.07)
for side,x in [('L',-.62),('R',.62)]:
    cb('Ear_'+side,(x,.02,2.44),(.19,.3,.35),'Skin','head',.09)
for side,x in [('L',-.26),('R',.26)]:
    cb('Thigh_'+side,(x,0,.84),(.32,.39,.48),'Ink','thigh.'+side,.08)
    cb('Shin_'+side,(x,-.015,.45),(.3,.36,.38),'Plastic_Blue','shin.'+side,.07)
    cb('Boot_'+side,(x,-.11,.16),(.43,.67,.27),'Ink','foot.'+side,.08)
    cb('BootSole_'+side,(x,-.13,.07),(.45,.69,.09),'White','foot.'+side,.025)
    cb('BootAccent_'+side,(x,-.445,.18),(.24,.027,.065),'Plastic_Orange','foot.'+side,.012)
for side,sgn in [('L',-1),('R',1)]:
    cb('UpperArm_'+side,(sgn*.57,0,1.52),(.3,.41,.48),'Plastic_Blue','upper_arm.'+side,.09)
    cb('Forearm_'+side,(sgn*.67,-.08,1.17),(.25,.34,.37),'Cloth_Neutral','forearm.'+side,.07)
    cb('Cuff_'+side,(sgn*.68,-.095,1.03),(.29,.37,.12),'Plastic_Orange','forearm.'+side,.04)
    cb('Hand_'+side,(sgn*.69,-.09,.89),(.28,.32,.28),'Skin','hand.'+side,.075)
    cs('Thumb_'+side,(sgn*.55,-.21,.93),(.085,.11,.13),'Skin','hand.'+side)
cb('Jacket_Zip',(0,-.275,1.46),(.035,.028,.59),'Metal_Brushed','spine',.009)
cb('ChestBadge',(.22,-.286,1.65),(.18,.04,.16),'White','spine',.03)
o=text('CHAR_BRIX_BadgeMark','B',(cx+.22,cy-.315,1.60),.12,M['Ink'],CHAR); parts[o]='spine'
cb('Nose',(0,-.445,2.39),(.17,.16,.15),'Skin','head',.07)
for side,x in [('L',-.28),('R',.28)]:
    cs('Cheek_'+side,(x*1.4,-.383,2.28),(.12,.019,.055),'Cheek','head')

# Armature uses rigid deform groups: lightweight, stable and easy to animate.
ad=bpy.data.armatures.new('RIG_BRIX_Skeleton'); rig=bpy.data.objects.new('RIG_BRIX',ad); CHAR.objects.link(rig); rig.show_in_front=True
bpy.context.view_layer.objects.active=rig; rig.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
bone_defs={'root':((cx,cy,0),(cx,cy,.35),None),'pelvis':((cx,cy,.85),(cx,cy,1.12),'root'),'spine':((cx,cy,1.12),(cx,cy,1.91),'pelvis'),'head':((cx,cy,1.91),(cx,cy,2.95),'spine')}
for side,s in [('L',-1),('R',1)]:
    bone_defs.update({'thigh.'+side:((cx+s*.26,cy,1.05),(cx+s*.26,cy,.63),'pelvis'),'shin.'+side:((cx+s*.26,cy,.63),(cx+s*.26,cy,.23),'thigh.'+side),'foot.'+side:((cx+s*.26,cy,.23),(cx+s*.26,cy-.4,.15),'shin.'+side),'upper_arm.'+side:((cx+s*.47,cy,1.78),(cx+s*.63,cy,1.28),'spine'),'forearm.'+side:((cx+s*.63,cy,1.28),(cx+s*.69,cy-.09,1.02),'upper_arm.'+side),'hand.'+side:((cx+s*.69,cy-.09,1.02),(cx+s*.69,cy-.09,.76),'forearm.'+side)})
for name,(h,t,parent) in bone_defs.items():
    b=ad.edit_bones.new(name); b.head=h; b.tail=t
    if parent:b.parent=ad.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT'); rig.select_set(False)
expressions=['NEUTRAL','CONFIDENT','CURIOUS','SUSPICIOUS','SURPRISED','SCARED','DISGUSTED','IMPRESSED','RELIEVED','EXCITED']
for name in expressions:
    rig[name]=1.0 if name=='CONFIDENT' else 0.0; rig.id_properties_ui(name).update(min=0,max=1,description='Expression blend. Set other expression weights to zero for a clean preset.')
for name in ['blink','squint','wide_open','look_x','look_y','smile','nervous_smile','open_surprise','frown','worried','impressed_O']:
    rig[name]=0.0; rig.id_properties_ui(name).update(min=-1 if name.startswith('look') else 0,max=1)
def driver(target,path,expr,props,index=None):
    f=target.driver_add(path) if index is None else target.driver_add(path,index); d=f.driver; d.type='SCRIPTED'; d.expression=expr
    for prop in props:
        v=d.variables.new(); v.name=prop; v.type='SINGLE_PROP'; v.targets[0].id=rig; v.targets[0].data_path='["'+prop+'"]'
def keys(o,variants):
    o.shape_key_add(name='Basis')
    for name,coords in variants.items():
        k=o.shape_key_add(name=name)
        for p,co in zip(k.data,coords):p.co=co
        driver(k,'value',name,[name])
def ellipse_shape(o,zfactor): return [(v.co.x,v.co.y,v.co.z*zfactor) for v in o.data.vertices]
for side,x in [('L',-.27),('R',.27)]:
    eye=cs('Eye_'+side,(x,-.386,2.52),(.195,.075,.23),'White','head')
    keys(eye,{'blink':ellipse_shape(eye,.065),'squint':ellipse_shape(eye,.45),'wide_open':ellipse_shape(eye,1.22)})
    for shape,expr,props in [('squint','min(1,squint+0.22*CONFIDENT+0.48*SUSPICIOUS+0.35*DISGUSTED+0.35*RELIEVED)',['squint','CONFIDENT','SUSPICIOUS','DISGUSTED','RELIEVED']),('wide_open','min(1,wide_open+SURPRISED+SCARED+0.4*EXCITED)',['wide_open','SURPRISED','SCARED','EXCITED'])]:
        d=eye.data.shape_keys.key_blocks[shape].driver_add('value').driver; d.expression=expr
        for prop in props[1:]:
            v=d.variables.new(); v.name=prop; v.type='SINGLE_PROP'; v.targets[0].id=rig; v.targets[0].data_path='["'+prop+'"]'
    pupil=cs('Pupil_'+side,(x,-.461,2.52),(.093,.038,.127),'Ink','head')
    glint=cs('EyeCatchlight_'+side,(x-.025,-.498,2.565),(.026,.012,.029),'White','head')
    for o in [pupil,glint]:
        driver(o,'location',str(o.location.x)+'+0.085*look_x',['look_x'],0); driver(o,'location',str(o.location.z)+'+0.09*look_y',['look_y'],2)
        driver(o,'scale','max(0.02,1-blink)',['blink'],2)
    brow=cb('Eyebrow_'+side,(x,-.401,2.815),(.35,.065,.075),'Ink','head',.033)
    sign=1 if side=='L' else -1
    driver(brow,'rotation_euler',f'{sign}*(0.13*CONFIDENT+0.28*CURIOUS+0.3*SUSPICIOUS-0.3*SCARED-0.22*worried-0.22*DISGUSTED)',['CONFIDENT','CURIOUS','SUSPICIOUS','SCARED','worried','DISGUSTED'],1)
    driver(brow,'location',str(brow.location.z)+'+0.08*SURPRISED+0.065*SCARED+0.045*EXCITED+0.07*CURIOUS-0.035*SUSPICIOUS',['SURPRISED','SCARED','EXCITED','CURIOUS','SUSPICIOUS'],2)

# Mouth is a filled ribbon/ellipse mesh with fixed topology and expression keys.
def mouthcoords(width,height,curve,openform=False,asym=0):
    out=[]; N=48
    for i in range(N):
        a=2*math.pi*i/N; x=width*math.cos(a); z=height*math.sin(a)+curve*(x/width)**2+asym*x
        out.append((x,-.007*math.cos(a),z))
    out.append((0,0,0)); return out
base=mouthcoords(.19,.019,.025)
me=bpy.data.meshes.new('CHAR_BRIX_Mouth_Geometry'); me.from_pydata(base,[],[(48,i,(i+1)%48) for i in range(48)]); me.update()
mouth=bpy.data.objects.new('CHAR_BRIX_Mouth',me); CHAR.objects.link(mouth); mouth.location=(cx,cy-.422,2.22); me.materials.append(M['Ink']); parts[mouth]='head'
mouthforms={'NEUTRAL':(.19,.018,.018,0),'CONFIDENT':(.23,.038,.07,.08),'CURIOUS':(.11,.055,.01,0),'SUSPICIOUS':(.19,.022,-.018,.13),'SURPRISED':(.115,.145,0,0),'SCARED':(.18,.11,-.03,0),'DISGUSTED':(.19,.04,-.065,.18),'IMPRESSED':(.09,.115,0,0),'RELIEVED':(.21,.025,.075,0),'EXCITED':(.235,.11,.08,0),'smile':(.23,.05,.075,0),'nervous_smile':(.22,.036,.025,.12),'open_surprise':(.115,.145,0,0),'frown':(.19,.024,-.075,0),'worried':(.17,.045,-.055,0),'impressed_O':(.09,.115,0,0)}
keys(mouth,{name:mouthcoords(w,h,c,asym=a) for name,(w,h,c,a) in mouthforms.items()})
for o,bone in parts.items():
    if o.type=='MESH':
        group=o.vertex_groups.new(name=bone); group.add(list(range(len(o.data.vertices))),1,'REPLACE'); mod=o.modifiers.new('BRIX rigid deform','ARMATURE'); mod.object=rig
        o.parent=rig
    else:
        # Non-mesh insignia follows the torso using a Child Of bone constraint.
        con=o.constraints.new('CHILD_OF'); con.target=rig; con.subtarget=bone
        con.inverse_matrix=(rig.matrix_world @ rig.pose.bones[bone].matrix).inverted()
rig['asset_version']='1.0'; rig['controls_help']='Pose Mode: FK limbs, root/pelvis/spine/head. Object custom properties: one expression weight at 1, others 0; manual eyes/mouth controls blend on top.'
CHAR.asset_mark(); CHAR['original_design']='BRIX / rounded ceramic face, midnight swept crest, teal technical suit, orange utility trim'

# Seamless studio cove, procedural surfaces, restrained architectural depth.
profile=[(-7,0),(3.5,0)]
for i in range(1,17):
    a=math.pi/2*i/16; profile.append((3.5+2.5*math.sin(a),2.5-2.5*math.cos(a)))
profile.append((6,9))
verts=[(x,y,z-.025) for x in [-12,12] for y,z in profile]; L=len(profile)
me=bpy.data.meshes.new('ENV_Lab_Cyclorama_Geometry'); me.from_pydata(verts,[],[(i,i+1,L+i+1,L+i) for i in range(L-1)]); me.materials.append(M['Floor']); me.update()
o=bpy.data.objects.new('ENV_Lab_SeamlessCove',me); ENV.objects.link(o)
for p in me.polygons:p.use_smooth=True
box('ENV_Lab_BackWallInset',(0,5.82,3.1),(7.8,.14,4.55),M['Wall'],ENV,.32)
for x in [-4.05,4.05]:
    box('ENV_Lab_WoodFin_'+('L' if x<0 else 'R'),(x,5.58,3.1),(.28,.44,5.35),M['Wood_Warm'],ENV,.075)
    box('ENV_Lab_LightFin_'+('L' if x<0 else 'R'),(x*.94,5.48,3.1),(.045,.055,4.75),M['Glow'],ENV,.02)
box('ENV_Lab_WoodBench',(0,4.95,.85),(6.7,1,.23),M['Wood_Warm'],ENV,.065)
box('ENV_Lab_BenchPlinth',(0,5.1,.38),(6.25,.73,.75),M['Wall'],ENV,.15)
o=text('ENV_Lab_WallIdentity','B R I X  /  L A B',(0,5.65,4.24),.38,M['UIWhite'],ENV)
o=text('ENV_Lab_WallCaption','MATERIAL EXPERIMENTS',(0,5.64,3.91),.115,M['UIWhite'],ENV)
for x in [-2.6,-1.3,0,1.3,2.6]:box('ENV_Lab_BackPanel_'+str(x),(x,5.70,2.7),(1.1,.09,1.32),M['Floor'],ENV,.13)
for side,x in [('L',-4.9),('R',4.9)]:
    box('ENV_Lab_Accent_'+side,(x,2.3,1.7),(.12,.16,3.3),M['WarmGlow'],ENV,.05)

# Modular experiment station: real thickness, piston, shield, console.
px=1.05; py=.35
cyl('PROP_TestPlatform_Base',(px,py,.15),1.08,.3,M['Rubber'],PROPS)
cyl('PROP_TestPlatform_Wood',(px,py,.36),1.01,.18,M['Wood_Warm'],PROPS)
cyl('PROP_TestPlatform_LightRing',(px,py,.472),.97,.045,M['Glow'],PROPS)
cyl('PROP_TestPlatform_Top',(px,py,.53),.93,.08,M['Metal_Brushed'],PROPS)
cyl('PROP_TestPlatform_Pad',(px,py,.581),.72,.025,M['Ink'],PROPS)
box('PROP_TestMachine_Spine',(px,py+1.14,2.18),(.65,.68,3.9),M['White'],PROPS,.18)
box('PROP_TestMachine_RearTrim',(px,py+1.5,2.13),(.18,.11,3.47),M['Plastic_Orange'],PROPS,.04)
box('PROP_TestMachine_Overhead',(px,py+.37,4.12),(1.8,2.12,.53),M['White'],PROPS,.17)
box('PROP_TestMachine_CyanBand',(px,py-.69,4.12),(1.32,.055,.09),M['Glow'],PROPS,.03)
cyl('PROP_TestMachine_Piston',(px,py,3.55),.16,.61,M['Metal_Chrome'],PROPS)
cyl('PROP_TestMachine_PressHead',(px,py,3.2),.57,.18,M['Metal_Brushed'],PROPS)
cyl('PROP_TestMachine_PressPad',(px,py,3.10),.52,.06,M['Rubber'],PROPS)
press=bpy.data.objects.new('CTRL_Experiment_Press',None); PROPS.objects.link(press); press.location=(px,py,3.55); press.empty_display_type='ARROWS'; press.empty_display_size=.35
for name in ['PROP_TestMachine_Piston','PROP_TestMachine_PressHead','PROP_TestMachine_PressPad']:
    o=bpy.data.objects[name]; world=o.matrix_world.copy(); o.parent=press; o.matrix_world=world
press['travel_m']=0.; press.id_properties_ui('travel_m').update(min=0,max=2.2,description='Downward press travel in metres. Keyframe this property. No simulation.')
f=press.driver_add('location',2); d=f.driver; d.expression='3.55-travel'; v=d.variables.new(); v.name='travel'; v.type='SINGLE_PROP'; v.targets[0].id=press; v.targets[0].data_path='["travel_m"]'
box('PROP_ControlConsole_Base',(2.38,-.02,.72),(.7,.67,1.35),M['White'],PROPS,.12)
box('PROP_ControlConsole_Top',(2.38,-.03,1.43),(.77,.7,.13),M['Ink'],PROPS,.07)
cyl('PROP_ControlButton',(2.38,-.08,1.54),.19,.11,M['Plastic_Orange'],PROPS)
cyl('PROP_ControlButton_Glow',(2.38,-.08,1.486),.215,.025,M['WarmGlow'],PROPS)
for side,x in [('L',px-1.0),('R',px+1.0)]:
    cyl('PROP_ShieldPost_'+side,(x,py-.45,1.0),.055,1.7,M['Metal_Brushed'],PROPS)
    uv('PROP_ShieldPostCap_'+side,(x,py-.45,1.87),(.075,.075,.075),M['Plastic_Orange'],PROPS)
# Side shield keeps the hero object visible and adds edge reflections.
shield=box('PROP_SafetyShield',(px+.98,py+.12,1.13),(.035,1.18,1.38),M['Glass_Clear'],PROPS,.016)
shield['retract_help']='Move along local Z to lower shield. Side placement preserves camera visibility.'
box('PROP_MaterialSelector_Display',(px+.025,py+1.505,2.75),(.51,.06,.87),M['Ink'],PROPS,.065)
o=text('PROP_MaterialSelector_Label','READY',(px,py+1.465,2.93),.1,M['Glow'],PROPS)
# Reusable small hero sample; a material demonstration, no episode or simulation.
sample=box('PROP_MaterialSample',(px,py,1.02),(.77,.77,.82),M['Jelly_Red'],PROPS,.17)
sample.rotation_euler.z=.18
sample['asset_role']='Reusable preview swatch. Replace or animate only in an episode copy.'
PROPS.asset_mark(); ENV.asset_mark()

# Professional soft studio rig.
world=bpy.data.worlds.new('WORLD_Lab_Studio'); world.use_nodes=True; world.node_tree.nodes.get('Background').inputs[0].default_value=(.13,.23,.33,1); world.node_tree.nodes.get('Background').inputs[1].default_value=.32; scene.world=world
def light(name,loc,power,color,size,target):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.color=color; d.shape='DISK'; d.size=size
    o=bpy.data.objects.new(name,d); LIGHTS.objects.link(o); o.location=loc; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler(); return o
light('LIGHT_Key',(-3.8,-4.4,7),1350,(1,.88,.72),5,(0,0,1.5))
light('LIGHT_Fill',(4,-3,4.4),850,(.49,.8,1),4,(0,0,2))
light('LIGHT_Rim',(1.1,3.4,6.5),1650,(.4,.83,1),3,(0,0,2))
light('LIGHT_Accent',(-4,2,3.4),360,(1,.26,.07),2,(-1,0,1.5))
light('LIGHT_Overhead',(0,1.2,7.8),700,(.7,.92,1),4,(0,0,0))
LIGHTS.asset_mark()
cd=bpy.data.cameras.new('CAM_MainVertical_Lens'); cam=bpy.data.objects.new('CAM_MainVertical',cd); CAMS.objects.link(cam); cam.location=(7.1,-13.5,7.0); target=Vector((0,.7,2.4)); cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); cd.lens=48; cd.sensor_width=36; cd.sensor_fit='HORIZONTAL'; cd.dof.use_dof=False; scene.camera=cam; CAMS.asset_mark()

# Camera mounted typography and selector: real editable native Blender text.
# At distance 1, horizontal width = 0.75, vertical height = 1.333.
ctrl=bpy.data.objects.new('CTRL_UI',None); UI.objects.link(ctrl); ctrl.parent=cam; ctrl.location=(0,0,0); ctrl.empty_display_size=.1
ctrl['selected_material']=0; ctrl.id_properties_ui('selected_material').update(min=0,max=6,description='0 SLIME / 1 GLASS / 2 CLOTH / 3 WATER / 4 HONEY / 5 SAND / 6 LAVA')
def uitext(name,body,x,y,size,mat):
    o=text(name,body,(0,0,0),size,mat,UI); o.parent=cam; o.location=(x,y,-1.005); o.rotation_euler=(0,0,0); return o
def uibox(name,x,y,w,h,mat):
    o=box(name,(0,0,0),(w,h,.003),mat,UI,min(h*.25,.008)); o.parent=cam; o.location=(x,y,-1.015); o.rotation_euler=(0,0,0); return o
uitext('UI_Title','BRIX LAB',0,.492,.061,M['UIWhite'])
uitext('UI_Parameter','M A T E R I A L   T E S T   /   0 1',0,.458,.014,M['Glow'])
uibox('UI_TitleRule',0,.432,.13,.003,M['WarmGlow'])
uitext('UI_MaterialSelector_Caption','CHOOSE A MATERIAL',0,-.415,.014,M['UIWhite'])
labels=['SLIME','GLASS','CLOTH','WATER','HONEY','SAND','LAVA']
for i,label in enumerate(labels):
    x=(i-3)*.089
    uibox('UI_MaterialSelector_Tile_'+label,x,-.451,.082,.037,M['Ink'])
    h=uibox('UI_MaterialSelector_Selected_'+label,x,-.451,.085,.04,M['Glow']); h.location.z=-1.013
    f=h.driver_add('hide_render'); d=f.driver; d.expression=f'selected != {i}'; v=d.variables.new(); v.name='selected'; v.type='SINGLE_PROP'; v.targets[0].id=ctrl; v.targets[0].data_path='["selected_material"]'
    f=h.driver_add('hide_viewport'); d=f.driver; d.expression=f'selected != {i}'; v=d.variables.new(); v.name='selected'; v.type='SINGLE_PROP'; v.targets[0].id=ctrl; v.targets[0].data_path='["selected_material"]'
    uitext('UI_MaterialSelector_Label_'+label,label,x,-.456,.012,M['UIWhite'])
UI.asset_mark()

# Mobile camera format and conservative laptop preview profile.
scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=1080; scene.render.resolution_y=1920; scene.render.resolution_percentage=50; scene.render.fps=30
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.render.use_simplify=True; scene.render.simplify_subdivision=1; scene.render.simplify_subdivision_render=1
scene.render.image_settings.color_mode='RGBA'; scene.view_settings.view_transform='AgX'
scene.render.filepath=str(ROOT/'01_TEMPLATES/Previews/BRIX_Foundation_v001.png')
scene.frame_start=1; scene.frame_end=240; scene.frame_set(1)
scene['production_role']='MASTER FOUNDATION: always Save As into 02_EPISODES before animation.'
scene['hardware_profile']='EEVEE / 50% preview / subdivision cap 1 / procedural textures / no simulations'
scene['output_profile']='1080 x 1920, 30 fps; set percentage 100 for full size still or approved final output.'
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active=rig
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'; area.spaces.active.shading.type='MATERIAL'
# Pack the typography font so the library transfers without system-font dependencies.
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'01_TEMPLATES/Versions/BRIX_Foundation_v001.blend'))
print(json.dumps({'built_objects':len(bpy.data.objects),'materials':len(bpy.data.materials),'expressions':expressions,'work_file':bpy.data.filepath,'folders':FOLDERS},indent=2))
