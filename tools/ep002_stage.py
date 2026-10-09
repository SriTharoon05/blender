import bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender'); EP=ROOT/'02_EPISODES/EP002_Impossible_Blankets'; s=bpy.context.scene; s.name='EP002_Impossible_Blankets'
assert not any(o.name.startswith('EP001_') for o in s.objects)
C={}
for name in ['ENVIRONMENT','BED','CHARACTER','LIGHTS','CAMERAS','UI','SLIME','GLASS','CLOTH','HONEY','SAND','WATER','LAVA']:
    c=bpy.data.collections.new('EP002_'+name); s.collection.children.link(c); C[name]=c
def load(path,kind,names):
    with bpy.data.libraries.load(str(ROOT/path),link=False) as (a,b):setattr(b,kind,names)
    return getattr(b,kind)
char=load('00_LIBRARY/Characters/BRIX/BRIX_Master.blend','collections',['ASSET_BRIX'])[0]
for o in list(char.objects):C['CHARACTER'].objects.link(o)
bpy.data.collections.remove(char)
with bpy.data.libraries.load(str(ROOT/'00_LIBRARY/Materials/BRIX_Materials.blend'),link=False) as (a,b):b.materials=[n for n in a.materials if n not in bpy.data.materials]
load('00_LIBRARY/UI/BRIX_UI.blend','objects',['UI_Title'])
source=bpy.data.objects['UI_Title']; font=source.data.font
with bpy.data.libraries.load(str(ROOT/'00_LIBRARY/Lighting/BRIX_StudioLighting.blend'),link=False) as (a,b):b.lights=['LIGHT_Key','LIGHT_Fill','LIGHT_Rim']
def matcopy(source,name,col=None,rough=None):
    m=bpy.data.materials[source].copy(); m.name=name; m.use_fake_user=True; p=m.node_tree.nodes.get('Principled BSDF')
    if col:
        p.inputs['Base Color'].default_value=(*col,1)
        for n in m.node_tree.nodes:
            if n.type=='VALTORGB':
                n.color_ramp.elements[0].color=(*[x*.82 for x in col],1); n.color_ramp.elements[-1].color=(*col,1)
    if rough is not None:p.inputs['Roughness'].default_value=rough
    return m
M={n:bpy.data.materials['MAT_'+n] for n in ['Wood_Warm','Metal_Brushed','Metal_Chrome','Cloth_Neutral','Glass_Clear','Honey','Sand','Water','Lava','Jelly_Blue','Jelly_Red','Plastic_Orange','Plastic_Blue']}
M['Floor']=matcopy('MAT_Lab_SatinCyan','MAT_TestStage_Sky',(.23,.45,.57),.48)
M['Bed']=matcopy('MAT_Cloth_Neutral','MAT_TestBed_Terracotta',(.48,.055,.027),.65)
M['Pillow']=matcopy('MAT_Cloth_Neutral','MAT_TestBed_Linen',(.83,.82,.70),.72)
M['Slime']=matcopy('MAT_Jelly_Blue','MAT_TestStage_Jelly_Green',(.035,.70,.14),.16)
M['Trim']=bpy.data.materials['MAT_Light_Cyan']; M['Ink']=bpy.data.materials['MAT_Ink_DeepNavy']; M['White']=bpy.data.materials['MAT_UI_White']
def place(o,name,mat,c):
    o.name=name; o.data.name=name+'_Geometry'
    for old in list(o.users_collection):old.objects.unlink(o)
    C[c].objects.link(o)
    if mat:o.data.materials.append(mat)
    return o
def box(name,loc,size,mat,c,bevel=.06):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=place(bpy.context.view_layer.objects.active,name,mat,c); o.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('Soft manufactured corners','BEVEL'); b.width=bevel; b.segments=3
        o.modifiers.new('Weighted edge normals','WEIGHTED_NORMAL')
        for p in o.data.polygons:p.use_smooth=True
    return o
def sphere(name,loc,scale,mat,c):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc); o=place(bpy.context.view_layer.objects.active,name,mat,c); o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return o
def text(name,body,size,loc):
    d=bpy.data.curves.new(name+'_Typography','FONT'); d.body=body; d.align_x='CENTER'; d.size=size; d.font=font; d.extrude=0; d.bevel_depth=0
    o=bpy.data.objects.new(name,d); C['UI'].objects.link(o); o.parent=cam; o.location=loc; d.materials.append(M['White']); return o
def light(name,data,loc,power,color,size):
    d=bpy.data.lights[data].copy(); d.name=name+'_Source'; d.energy=power; d.color=color; d.shape='DISK'; d.size=size; o=bpy.data.objects.new(name,d); C['LIGHTS'].objects.link(o); o.location=loc; o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
light('LIGHT_EP002_Key','LIGHT_Key',(-3.8,-4.5,7),1100,(1,.92,.80),5)
light('LIGHT_EP002_Fill','LIGHT_Fill',(4.5,-1,5),620,(.57,.83,1),4)
light('LIGHT_EP002_Rim','LIGHT_Rim',(-1,4.5,6),1350,(.6,.88,1),3.5)
world=bpy.data.worlds.new('WORLD_BRIX_TestStage'); world.use_nodes=True; world.node_tree.nodes.get('Background').inputs[0].default_value=(.26,.42,.55,1); world.node_tree.nodes.get('Background').inputs[1].default_value=.38; s.world=world
# Studio cove is wider than every camera ray and uses a quiet procedural finish.
profile=[(-40,0),(5,0)]
for i in range(1,25):
    a=math.pi/2*i/24; profile.append((5+4*math.sin(a),4-4*math.cos(a)))
profile.append((9,30)); L=len(profile); verts=[(x,y,z-.035) for x in [-40,40] for y,z in profile]; me=bpy.data.meshes.new('BRIX_TestStage_CoveMesh'); me.from_pydata(verts,[],[(i,i+1,L+i+1,L+i) for i in range(L-1)]); me.materials.append(M['Floor']); o=bpy.data.objects.new('ENV_BRIX_TestStage_SeamlessCove',me); C['ENVIRONMENT'].objects.link(o)
for p in me.polygons:p.use_smooth=True
bed=bpy.data.objects.new('PROP_BRIX_TestBed',None); C['BED'].objects.link(bed); bed.empty_display_size=.2; bed['design']='Original floating walnut rails, terracotta upholstery and ivory bolster; no pixel art.'
pieces=[]
pieces.append(box('PROP_TestBed_WalnutFrame',(0,.10,.63),(1.94,3.95,.23),M['Wood_Warm'],'BED',.12))
pieces.append(box('PROP_TestBed_Mattress',(0,.10,.91),(1.82,3.74,.40),M['Bed'],'BED',.15))
pieces.append(box('PROP_TestBed_Pillow',(0,1.08,1.18),(1.30,.86,.22),M['Pillow'],'BED',.105))
pieces.append(box('PROP_TestBed_Headboard',(0,2.06,1.12),(1.95,.17,1.06),M['Wood_Warm'],'BED',.08))
pieces.append(box('PROP_TestBed_HeadboardInset',(0,1.966,1.25),(1.57,.04,.45),M['Bed'],'BED',.07))
for x in [-.74,.74]:
    for y in [-1.48,1.66]:pieces.append(box('PROP_TestBed_Leg_'+str(x)+'_'+str(y),(x,y,.26),(.22,.25,.49),M['Wood_Warm'],'BED',.05))
for x in [-.96,.96]:pieces.append(box('PROP_TestBed_RailTrim_'+str(x),(x,.1,.69),(.018,3.4,.035),M['Metal_Brushed'],'BED',.009))
for o in pieces:
    worldmat=o.matrix_world.copy(); o.parent=bed; o.matrix_world=worldmat
r=bpy.data.objects['RIG_BRIX']; r.animation_data_clear()
for b in r.pose.bones:b.rotation_mode='XYZ'; b.rotation_euler=(0,0,0); b.location=(0,0,0)
r.rotation_euler=(-math.pi/2,0,0); r.location=(1.62,-1.45,1.025)
# Elevate the existing head onto the pillow, using the original head bone.
head=r.pose.bones['head']; head.location=r.data.bones['head'].matrix_local.to_3x3().inverted()@Vector((0,-.21,0)); head.rotation_euler.x=.13
r.pose.bones['upper_arm.L'].rotation_euler.z=-.12; r.pose.bones['upper_arm.R'].rotation_euler.z=.12
for n in ['NEUTRAL','CONFIDENT','CURIOUS','SUSPICIOUS','SURPRISED','SCARED','DISGUSTED','IMPRESSED','RELIEVED','EXCITED']:r[n]=float(n=='RELIEVED')
r['look_x']=.14; r['look_y']=0.; r['blink']=0.; r['squint']=0.; r.update_tag()
cd=bpy.data.cameras.new('CAM_EP002_Main_Lens'); cam=bpy.data.objects.new('CAM_EP002_Main',cd); C['CAMERAS'].objects.link(cam); cam.location=(4.5,-6.4,5.7); cam.rotation_euler=(Vector((0,.1,1.55))-cam.location).to_track_quat('-Z','Y').to_euler(); cd.lens=70; cd.sensor_width=36; cd.sensor_fit='HORIZONTAL'; s.camera=cam; cd.dof.use_dof=False
# Original miniature material tokens in compact cyan-edged square slots.
ui=bpy.data.objects.new('UI_EP002_MaterialSelector',None); C['UI'].objects.link(ui); ui.parent=cam; ui['selected_material']=0; ui.id_properties_ui('selected_material').update(min=0,max=6,description='SLIME GLASS CLOTH HONEY SAND WATER LAVA')
nameobj=text('UI_EP002_MaterialName','SLIME',.042,(0,.376,-1))
labels=['SLIME','GLASS','CLOTH','HONEY','SAND','WATER','LAVA']
def uiattach(o,x,y,z=-1.012):o.parent=cam; o.location=(x,y,z); return o
for i,label in enumerate(labels):
    x=(i-3)*.061
    slot=box('UI_EP002_Slot_'+label,(0,0,0),(.055,.056,.003),M['Ink'],'UI',.006); uiattach(slot,x,.319)
    for side,loc,size in [('T',(x,.347),(.056,.002)),('B',(x,.291),(.056,.002)),('L',(x-.027,.319),(.002,.055)),('R',(x+.027,.319),(.002,.055))]:
        border=box('UI_EP002_Active_'+label+'_'+side,(0,0,0),(*size,.001),M['Trim'],'UI',.0005); uiattach(border,*loc,-1.006)
        for path in ['hide_render','hide_viewport']:
            d=border.driver_add(path).driver; v=d.variables.new(); v.name='selection'; v.type='SINGLE_PROP'; v.targets[0].id=ui; v.targets[0].data_path='["selected_material"]'; d.expression=f'selection != {i}'
    mats=[M['Slime'],M['Glass_Clear'],M['Pillow'],M['Honey'],M['Sand'],M['Water'],M['Lava']]
    if label in ['SLIME','GLASS','CLOTH','SAND']:
        icon=box('UI_EP002_Icon_'+label,(0,0,0),(.027,.027,.015),mats[i],'UI',.003); uiattach(icon,x,.319,-.989); icon.rotation_euler=(.2,-.25,.16)
    else:
        icon=sphere('UI_EP002_Icon_'+label,(0,0,0),(.015,.017,.009),mats[i],'UI'); uiattach(icon,x,.319,-.989)
    if label=='CLOTH':
        for j in [-1,0,1]:
            strip=box('UI_EP002_FabricWeave_'+str(j),(0,0,0),(.025,.001,.001),M['Metal_Brushed'],'UI',0); uiattach(strip,x,.319+j*.006,-.98)
    if label=='SAND':icon.rotation_euler=(.3,.3,.3)
hook=text('UI_EP002_Hook','WHICH BLANKET\nWOULD YOU CHOOSE?',.021,(0,.236,-1)); hook.data.space_line=.85
# Remove unloaded UI dependency objects; preserve only linked stage/character items.
for o in list(bpy.data.objects):
    if not o.users_collection:bpy.data.objects.remove(o,do_unlink=True)
s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=1080; s.render.resolution_y=1920; s.render.resolution_percentage=50; s.render.fps=30; s.eevee.use_raytracing=True; s.eevee.taa_render_samples=64; s.eevee.shadow_ray_count=2; s.view_settings.view_transform='AgX'; s.render.use_simplify=True; s.render.simplify_subdivision=1; s.render.simplify_subdivision_render=1; s.frame_start=1; s.frame_end=1125; s.render.filepath=str(EP/'previews/EP002_Stage_Layout_v001.png')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'; a.spaces.active.shading.type='SOLID'
bpy.ops.file.pack_all(); bpy.context.view_layer.update(); bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v003.blend'),compress=True); bpy.ops.render.render(write_still=True)
print('NEW_STAGE_LAYOUT_READY')
