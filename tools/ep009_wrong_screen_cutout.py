"""Build EP009 from static SVG puppet parts, skeletal pivots and aligned speech.

No character geometry is generated per frame. Only bone rotations, preset
visibility and caption pops are animated over one locked flat background.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.cutout_puppet_toolkit import (bind_part,contour_mesh,ellipse,flat_material,
    make_rig,rotate_joint,shape,visibility)
from tools.grease_pencil_toolkit import configure_scene,create_caption,start_episode_from_master
from tools.ep009_wrong_screen_gp import constant,show_intervals
from tools.ep009_flat_office import contours

EP=ROOT/'02_EPISODES/EP009_Wrong_Screen'
SCENE='EP009_Wrong_Screen_Cutout'
UNIT=16/1920

def xy(x,y):
    return ((x-540)*UNIT,(960-y)*UNIT)

def rect(x,y,w,h,color,stroke='#000000',width=4):
    return shape([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],color,stroke,width)

def runs(values):
    result={}
    for frame,value in enumerate(values,1):
        intervals=result.setdefault(value,[])
        if intervals and intervals[-1][1]==frame-1:
            intervals[-1][1]=frame
        else:
            intervals.append([frame,frame])
    return result

def main():
    import bpy
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='02_EPISODES/EP009_Wrong_Screen/blend/EP009_Wrong_Screen_Cutout_v001.blend')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    target=(ROOT/args.output).resolve()
    asset_path=ROOT/'00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_Paths_v002.json'
    asset=json.loads(asset_path.read_text(encoding='utf-8'))
    cues=json.loads((EP/'edit/speech_cues_v001.json').read_text(encoding='utf-8'))
    plate=json.loads((EP/'edit/flat_plate_composition.json').read_text(encoding='utf-8'))
    start_episode_from_master(target)
    scene=bpy.data.scenes.new(SCENE)
    bpy.context.window.scene=scene
    configure_scene(scene,duration_seconds=18,transparent=False)
    scene.eevee.taa_render_samples=16
    scene.render.use_compositing=False
    scene.render.filepath='//../renders/cutout_frames_1080p24/EP009_######'
    scene.world=bpy.data.worlds.new('EP009_Unlit_Flat_World')
    scene.world.color=(1,1,1)
    collection=bpy.data.collections.new('CHAR_Peter_Office_Cutout')
    scene.collection.children.link(collection)
    stage=bpy.data.collections.new('EP009_One_Static_Vector_Stage')
    scene.collection.children.link(stage)
    ui=bpy.data.collections.new('EP009_Fake_Screen_Share_UI')
    scene.collection.children.link(ui)
    # One locked background plate. Its exact source is the editable office SVG.
    mesh=bpy.data.meshes.new('EP009_Locked_Background_Plane')
    mesh.from_pydata([(-4.5,-8,-1),(4.5,-8,-1),(4.5,8,-1),(-4.5,8,-1)],[],[(0,1,2,3)])
    mesh.uv_layers.new(name='Full_Frame')
    for loop,uv in zip(mesh.uv_layers.active.data,[(0,0),(1,0),(1,1),(0,1)]):
        loop.uv=uv
    background=bpy.data.objects.new(mesh.name,mesh)
    stage.objects.link(background)
    image=bpy.data.images.load(str(ROOT/plate['plate_png']),check_existing=True)
    image.filepath='//../plates/'+Path(plate['plate_png']).name
    image.pack()
    material=flat_material('EP009_Static_Flat_Office_Plate','#FFFFFF')
    nodes=material.node_tree.nodes
    tex=nodes.new('ShaderNodeTexImage');tex.image=image
    material.node_tree.links.new(tex.outputs['Color'],next(n for n in nodes if n.type=='EMISSION').inputs['Color'])
    mesh.materials.append(material)
    background['background_count']=1
    background['editable_source_svg']='//../plates/'+Path(plate['svg']).name
    # Rigid skeletal pivots. Legs are complete modular parts behind the desk.
    bones={
        'root':{'head':[540,1260],'tail':[540,1160],'parent':None},
        'torso':{'head':[540,1250],'tail':[540,1030],'parent':'root'},
        'neck':{'head':[540,1030],'tail':[540,964],'parent':'torso'},
        'head':{'head':[540,964],'tail':[540,740],'parent':'neck'},
        'jaw':{'head':[573,875],'tail':[573,845],'parent':'head'},
        'upper_arm.L':{'head':[355,1020],'tail':[235,1090],'parent':'torso'},
        'lower_arm.L':{'head':[235,1090],'tail':[190,965],'parent':'upper_arm.L'},
        'hand.L':{'head':[190,965],'tail':[190,935],'parent':'lower_arm.L'},
        'upper_arm.R':{'head':[728,1020],'tail':[800,1250],'parent':'torso'},
        'lower_arm.R':{'head':[800,1250],'tail':[899,1394],'parent':'upper_arm.R'},
        'hand.R':{'head':[899,1394],'tail':[899,1424],'parent':'lower_arm.R'},
        'upper_leg.L':{'head':[455,1230],'tail':[443,1560],'parent':'torso'},
        'lower_leg.L':{'head':[443,1560],'tail':[440,1790],'parent':'upper_leg.L'},
        'foot.L':{'head':[440,1790],'tail':[405,1810],'parent':'lower_leg.L'},
        'upper_leg.R':{'head':[625,1230],'tail':[637,1560],'parent':'torso'},
        'lower_leg.R':{'head':[637,1560],'tail':[640,1790],'parent':'upper_leg.R'},
        'foot.R':{'head':[640,1790],'tail':[680,1810],'parent':'lower_leg.R'}}
    rig=make_rig(collection,bones,xy,name='RIG_EP009_Peter_Office_Puppet')
    body={
      'upper_leg.L':[rect(425,1200,64,375,'#243851')],
      'lower_leg.L':[rect(427,1535,52,270,'#243851')],
      'foot.L':[shape([(422,1788),(476,1788),(485,1815),(396,1815),(399,1800)],'#FFFFFF')],
      'upper_leg.R':[rect(591,1200,64,375,'#243851')],
      'lower_leg.R':[rect(601,1535,52,270,'#243851')],
      'foot.R':[shape([(604,1788),(660,1788),(682,1800),(685,1815),(597,1815)],'#FFFFFF')],
      'torso':[shape([(485,986),(391,1000),(340,1035),(357,1280),(726,1280),(749,1035),
          (686,1000),(595,986),(540,1034)],'#FFFFFF'),
          shape([(485,986),(540,1034),(514,1072),(460,1005)],'#FFFFFF'),
          shape([(595,986),(540,1034),(568,1072),(620,1005)],'#FFFFFF'),
          shape([(529,1042),(551,1042),(564,1060),(548,1082),(526,1062)],'#FF4C67'),
          shape([(537,1080),(551,1080),(574,1218),(548,1246),(527,1218)],'#FF4C67')],
      'neck':[shape([(488,928),(600,928),(611,1012),(543,1034),(476,1006)],'#FFC38A')],
      'upper_arm.L':[shape([(349,1015),(379,1027),(263,1114),(235,1090),(224,1065)],'#FFFFFF')],
      'lower_arm.L':[shape([(229,1092),(260,1102),(232,983),(204,978),(181,1000)],'#FFFFFF')],
      'hand.L':[ellipse(190,959,30,22,'#FFC38A'),
          shape([(172,955),(177,920),(186,920),(190,951)],'#FFC38A')],
      'upper_arm.R':[shape([(721,1015),(750,1029),(819,1230),(778,1261)],'#FFFFFF')],
      'lower_arm.R':[shape([(780,1236),(811,1235),(921,1380),(887,1408)],'#FFFFFF')],
      'hand.R':[ellipse(899,1394,34,20,'#FFC38A'),
          shape([(882,1386),(884,1398)],None,stroke_width=2),
          shape([(893,1384),(895,1397)],None,stroke_width=2),
          shape([(904,1384),(906,1397)],None,stroke_width=2)]}
    part_objects=[]
    for index,(bone,paths) in enumerate(body.items()):
        ob=contour_mesh('PETER_'+bone,paths,xy,collection,z=.03+index*.003,scale=UNIT)
        bind_part(ob,rig,bone)
        part_objects.append(ob)
    # All facial geometry is authored once from the new flat Peter SVG.
    def head_xy(x,y):
        return xy(540+(x-620)*.65,740+(y-440)*.65)
    head_paths=asset['parts']['head']['paths']
    base=[path for path in head_paths if path.get('group') not in {'eyes','mouth'}]
    head=contour_mesh('PETER_head_flat_identity',base,head_xy,collection,z=.2,scale=UNIT*.65)
    bind_part(head,rig,'head');part_objects.append(head)
    eye_paths=[path for path in head_paths if path.get('group')=='eyes']
    eyes=contour_mesh('PETER_eyes_normal',eye_paths,head_xy,collection,z=.36,scale=UNIT*.65)
    bind_part(eyes,rig,'head');part_objects.append(eyes)
    blink_paths=asset['expressions']['eyes']['blink']
    blink=contour_mesh('PETER_eyes_blink',blink_paths,head_xy,collection,z=.36,scale=UNIT*.65)
    bind_part(blink,rig,'head');part_objects.append(blink)
    panic_paths=json.loads(json.dumps(eye_paths))
    for path in panic_paths:
        pts=path['points'];cx=sum(p[0] for p in pts)/len(pts);cy=sum(p[1] for p in pts)/len(pts)
        factor=.42 if any(v in path.get('id','') for v in ['iris','pupil']) else 1.13
        path['points']=[[cx+(x-cx)*factor,cy+(y-cy)*factor] for x,y in pts]
    panic_eyes=contour_mesh('PETER_eyes_panic_static_preset',panic_paths,head_xy,collection,z=.36,scale=UNIT*.65)
    bind_part(panic_eyes,rig,'head');part_objects.append(panic_eyes)
    eye_values=['panic' if 145<=f<=312 else 'normal' for f in range(1,433)]
    for center in [32,114,201,322]:
        for f in [center,center+1]:eye_values[f-1]='blink'
    eye_runs=runs(eye_values)
    for ob,value in [(eyes,'normal'),(blink,'blink'),(panic_eyes,'panic')]:
        visibility(ob,eye_runs.get(value,[]))
    mouth_values=['rest']*432
    mouth_rows={item['frame']:item for item in cues['mouth_frames']}
    for frame,item in mouth_rows.items():
        if item.get('speaker')=='employee':
            mouth_values[frame-1]={'A':'AA','E':'EE','O':'OH'}.get(item['shape'],item['shape'])
    mouth_runs=runs(mouth_values)
    for state,paths in asset['expressions']['mouth'].items():
        ob=contour_mesh('PETER_mouth_'+state,paths,head_xy,collection,z=.40,scale=UNIT*.65)
        bind_part(ob,rig,'jaw');visibility(ob,mouth_runs.get(state,[]));part_objects.append(ob)
    # Seated-body leg parts are hidden by a fixed foreground desk apron, not deleted.
    front_shapes=[rect(-8,1487,1096,107,'#FFC575'),rect(-8,1594,1096,153,'#F4A959'),
        rect(-8,1582,1096,20,'#C87C40')]
    contour_mesh('EP009_Foreground_Desk_Occlusion',front_shapes,xy,stage,z=.9,scale=UNIT)
    all_bg,_=contours()
    laptop_shapes=[p for p in all_bg if p['id'].startswith(('laptop-','key-')) or p['id']=='spacebar']
    contour_mesh('EP009_Foreground_Laptop_Occlusion',laptop_shapes,xy,stage,z=1,scale=UNIT)
    # Right hand is explicitly above the mouse/keyboard foreground.
    for vertex in bpy.data.objects['PETER_hand.R'].data.vertices:vertex.co.z+=1.13
    # Joint-only action: relaxed gestures, panic tremor, then a fold behind the laptop.
    rotate_joint(rig,'head',[(1,0),(28,-2),(48,0),(108,-3),(132,0),(145,4),(150,0),
        (241,-2),(242,2),(243,-1),(244,0),(312,0),(337,-4),(349,-12),(361,-36),(373,-105),(385,-180),(432,-180)])
    rotate_joint(rig,'torso',[(1,0),(48,-2),(96,0),(145,1),(149,-1),(154,0),(312,0),(361,-2),(385,0),(432,0)])
    # The bowed head passes behind the lid and stays occluded in the final hold.
    for ob in part_objects:
        if ob['pivot_bone'] in {'head','jaw','neck'}:
            if ob.name in {'PETER_head_flat_identity','PETER_neck'}:
                ob.hide_render=False
                ob.keyframe_insert(data_path='hide_render',frame=1)
            for frame,hidden in [(385,True),(432,True)]:
                ob.hide_render=hidden
                ob.keyframe_insert(data_path='hide_render',frame=frame)
    rotate_joint(rig,'upper_arm.L',[(1,9),(24,-5),(42,10),(60,0),(145,-12),(175,12),(200,-8),(240,-6),(312,0),(361,14),(432,14)])
    rotate_joint(rig,'lower_arm.L',[(1,0),(24,8),(48,0),(145,22),(168,18),(241,-4),(244,6),(312,0),(361,-25),(432,-25)])
    rotate_joint(rig,'hand.L',[(1,0),(24,-6),(48,0),(145,6),(180,-6),(240,6),(244,-6),(312,0),(432,0)])
    rotate_joint(rig,'hand.R',[(1,0),(96,-3),(99,0),(145,-4),(149,4),(154,0),(241,-3),(244,3),(247,0),(312,0),(432,0)])
    # No narration from the offscreen host drives Peter's mouth or jaw.
    rotate_joint(rig,'jaw',[(frame,1.8*item['openness']) for frame,item in mouth_rows.items()
        if item.get('speaker')=='employee'])
    # Static screen graphics switch once at the reveal.
    quad=plate['screen_quad_px_clockwise_from_top_left']
    def uv(u,v):
        a,b,c,d=quad
        return ((1-v)*((1-u)*a[0]+u*b[0])+v*((1-u)*d[0]+u*c[0]),
            (1-v)*((1-u)*a[1]+u*b[1])+v*((1-u)*d[1]+u*c[1]))
    def ui_rect(u,v,w,h,c):
        return shape([uv(u,v),uv(u+w,v),uv(u+w,v+h),uv(u,v+h)],c,None,0)
    good=[shape(quad,'#18243B',None,0),ui_rect(0,0,1,.065,'#273952'),ui_rect(.03,.072,.94,.05,'#34CB8B'),
        ui_rect(.08,.49,.70,.045,'#64A7FF'),ui_rect(.08,.64,.53,.03,'#BFCFE7'),ui_rect(.08,.77,.65,.03,'#BFCFE7')]
    bad=[shape(quad,'#18243B',None,0),ui_rect(0,0,1,.125,'#FF455A'),
        ui_rect(.035,.33,.93,.10,'#FFFFFF'),ui_rect(.57,.60,.17,.11,'#FFD25A'),ui_rect(.57,.56,.065,.055,'#FFD25A')]
    bad.extend(ui_rect(.014+i*.054,.13,.049,.033,'#8DB8FB' if i%3 else '#C8D6EA') for i in range(18))
    for label,paths,interval in [('Professional_Presentation',good,(1,144)),('Wrong_Entire_Desktop',bad,(145,432))]:
        ob=contour_mesh('UI_'+label,paths,xy,ui,z=1.35,scale=UNIT);visibility(ob,[interval])
    def text(text,u,v,size,hexcode,interval,name):
        x,y=uv(u,v)
        data=bpy.data.curves.new(name,'FONT');data.body=text;data.size=size*UNIT;data.align_y='CENTER'
        ob=bpy.data.objects.new(name,data);ui.objects.link(ob);ob.location=(*xy(x,y),1.6)
        data.materials.append(flat_material('UI_INK_'+hexcode,hexcode))
        visibility(ob,[interval]);return ob
    text('Quarterly update',.08,.22,30,'FFFFFF',(1,144),'UI_Presentation_Title')
    text('Everything is under control.',.08,.37,16,'BFCFE7',(1,144),'UI_Presentation_Subtitle')
    text('SHARING: ENTIRE SCREEN',.035,.07,15,'FFFFFF',(145,432),'UI_Full_Desktop_Status')
    text('47 TABS OPEN',.07,.245,29,'FFD25A',(145,432),'UI_47_Tabs')
    text('Search: how to look busy at work',.055,.38,17,'18243B',(145,432),'UI_Search_History')
    text('can my boss see this?',.07,.515,18,'FFFFFF',(145,432),'UI_Search_Panic')
    text('DO_NOT_OPEN',.53,.775,23,'FFD25A',(145,432),'UI_Suspicious_Folder')
    text('Presentation.pptx',.05,.89,15,'BFCFE7',(145,432),'UI_Missed_Presentation')
    # Native static cursor follows its own small pivot bone.
    cx,cy=uv(.84,.86)
    cursor_paths=[shape([(cx,cy),(cx+7,cy+24),(cx+14,cy+15),(cx+22,cy+14)],'#FFFFFF',stroke_width=2)]
    cursor=contour_mesh('UI_Cursor_Static_Cutout',cursor_paths,xy,ui,z=1.8,scale=UNIT)
    cursor_rig=make_rig(ui,{'cursor':{'head':[cx,cy],'tail':[cx,cy-20],'parent':None}},xy,'RIG_EP009_Cursor_Pivot')
    bind_part(cursor,cursor_rig,'cursor')
    rotate_joint(cursor_rig,'cursor',[(1,0),(96,-7),(99,0),(145,18),(160,-12),(175,20),(240,-15),(244,14),(312,0),(432,0)])
    # Host tile stays static except for preset talking mouth and speaker border.
    host_base=[rect(864,652,143,163,'#2A3A54'),ellipse(935,704,29,33,'#FFC38A'),
        ellipse(935,785,45,34,'#64A7FF'),ellipse(925,701,2.4,3.2,'#000000',None,0),ellipse(945,701,2.4,3.2,'#000000',None,0)]
    contour_mesh('UI_Meeting_Host_Static_Tile',host_base,xy,ui,z=2,scale=UNIT)
    active=[(49,96),(193,240)]
    host_talk=contour_mesh('UI_Host_Talking_Preset',[ellipse(935,718,9,6,'#000000',None,0)],xy,ui,z=2.2,scale=UNIT)
    visibility(host_talk,active)
    border=contour_mesh('UI_Host_Speaker_Indicator',[rect(860,648,151,171,None,'#36CF92',5)],xy,ui,z=2.2,scale=UNIT)
    visibility(border,active)
    # A sharp three-frame red alert is an overlay; the single background never moves.
    alert=contour_mesh('UI_Red_Alert_Static',[rect(182,973,716,400,None,'#FF304C',8)],xy,ui,z=2.3,scale=UNIT)
    visibility(alert,[(241,242),(244,244)])
    # Authoritative word timing controls prebuilt caption objects.
    records=[]
    words=sorted(cues['words'],key=lambda item:item['start'])
    for index,item in enumerate(words):
        start=item['start_frame'];end=item['end_frame']
        if index+1<len(words) and words[index+1]['start_frame']>start:
            end=min(end,words[index+1]['start_frame']-1)
        end=max(start,end)
        caption,bounds=create_caption(scene,item['word'],'CAPTION_EP009_Word_%02d'%index,slot='dialogue',size=.94,outline_radius=.048)
        caption.location.z=5
        show_intervals(caption,[(start,end)],pop=True)
        records.append({'word':item['word'],'start_frame':start,'end_frame':end,'max_bounds_px':bounds})
    title,bounds=create_caption(scene,'POV: YOU SHARED\nTHE WRONG SCREEN.','CAPTION_EP009_Final_POV',slot='main',size=.65)
    title.location.z=5;show_intervals(title,[(361,432)])
    # Pack source audio for editing; production queue performs the final mux.
    audio=EP/'audio/EP009_Final_Mix_18s_v001.wav'
    editor=scene.sequence_editor_create()
    strip=editor.strips.new_sound('EP009 synchronized Gemini dialogue and original score',str(audio),channel=1,frame_start=1)
    strip.sound.pack();strip.sound.filepath='//../audio/'+audio.name
    scene.render.use_sequencer=False
    for item in cues['lines']:
        scene.timeline_markers.new(item['speaker']+': '+item['text'],frame=math.floor(item['start']*24)+1)
    scene['visual_style']='Flat SVG solid colors, crisp black outlines, zero shading/gradients'
    scene['animation_technique']='2D cut-out skeletal puppet; static geometry bound rigidly to pivot bones'
    scene['character_library']='00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_v002.blend'
    scene['background_count']=1
    scene['caption_policy']='Luckiest Guy aligned word pops; lower [130,1340,870,1470], top ending POV'
    scene['lip_sync_method']=cues['lip_sync_method']
    scene.frame_set(85)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
    assert all(ob.type=='MESH' for ob in part_objects)
    assert all(not ob.data.animation_data for ob in part_objects)
    report={'scene':SCENE,'frames':432,'video_seconds':18,'resolution':[1080,1920],'fps':24,'engine':'BLENDER_EEVEE',
        'character_library':scene['character_library'],'static_character_parts':len(part_objects),
        'skeletal_bones':len(rig.data.bones),'character_geometry_redraws_per_frame':0,'character_mesh_animation':False,
        'background_count':1,'background_plate':plate['plate_png'],'caption_font':'LuckiestGuy-Regular.ttf',
        'spoken_caption_records':records,'final_title_bounds_px':bounds,'lip_sync_method':cues['lip_sync_method'],
        'built_project':str(target.relative_to(ROOT)),'visual_reviewed':False}
    (EP/'edit/project_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('EP009_CUTOUT_BUILD_COMPLETE',json.dumps(report),flush=True)

if __name__=='__main__':
    main()
