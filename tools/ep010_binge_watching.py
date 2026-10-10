"""Build the EP010 cut-out puppet foreground and two-plate composition.

Preparation only: this entrypoint saves an editable project and never renders.
The current brief explicitly authorizes two static Cycles living-room plates;
Peter remains flat and his static SVG parts move through skeletal pivots.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.cutout_puppet_toolkit import contour_mesh, flat_material, shape, visibility
from tools.grease_pencil_toolkit import configure_scene, create_caption, select_caption_font, start_episode_from_master

EP = ROOT / '02_EPISODES/EP010_Binge_Watching'
SCENE = 'EP010_Binge_Watching'
FRAMES = 528
UNIT = 16 / 1920


def xy(x, y):
    return (x - 540) * UNIT, (960 - y) * UNIT


def constant(data):
    if not data.animation_data or not data.animation_data.action:
        return
    for slot in data.animation_data.action.slots:
        for layer in data.animation_data.action.layers:
            for strip in layer.strips:
                bag = strip.channelbag(slot, ensure=False)
                if bag:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation = 'CONSTANT'


def show_caption(ob, intervals, pop=False):
    for layer in ob.data.layers:
        layer.opacity = 0
        layer.keyframe_insert(data_path='opacity', frame=1)
        for start, end in intervals:
            for frame, value in [(max(1, start - 1), 0), (start, 1), (end + 1, 0)]:
                layer.opacity = value
                layer.keyframe_insert(data_path='opacity', frame=frame)
    constant(ob.data)
    if pop:
        box = ob['caption_export_bounds_px']
        cx, cy = xy((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        for layer in ob.data.layers:
            for frame in layer.frames:
                for stroke in frame.drawing.strokes:
                    for point in stroke.points:
                        point.position.x -= cx
                        point.position.y -= cy
                frame.drawing.tag_positions_changed()
        ob.location.x, ob.location.y = cx, cy
        for start, end in intervals:
            for frame, scale in [(start, .90), (min(start + 2, end), 1), (end, 1)]:
                ob.scale = (scale, scale, scale)
                ob.keyframe_insert(data_path='scale', frame=frame)


def rectangle(x, y, w, h, color, stroke=None, width=0):
    return shape([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], color, stroke, width)


def stage_text(collection, body, x, y, size, color, name, interval=(1, FRAMES), depth=2.7):
    import bpy
    data = bpy.data.curves.new(name, 'FONT')
    data.body = body
    data.size = size * UNIT
    data.align_x = 'CENTER'
    data.align_y = 'CENTER'
    data.font = select_caption_font()[0]
    data.materials.append(flat_material('EP010_TEXT_' + color.lstrip('#'), color))
    ob = bpy.data.objects.new(name, data)
    collection.objects.link(ob)
    ob.location = (*xy(x, y), depth)
    visibility(ob, [interval], total_frames=FRAMES)
    return ob


def compose(scene, plates, target):
    """Keep AgX-baked plate colors and flat sRGB puppet colors intact."""
    import bpy
    group = bpy.data.node_groups.new('EP010_Two_Static_Cycles_Plates_Alpha_Over', 'CompositorNodeTree')
    scene.compositing_node_group = group
    group.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    nodes, links = group.nodes, group.links
    output = nodes.new('NodeGroupOutput')
    output.location = (600, 80)
    images = []
    for index, plate in enumerate(plates):
        image = bpy.data.images.load(str(ROOT / plate), check_existing=True)
        if tuple(image.size) != (1080, 1920):
            raise ValueError('Plate must be full 1080 x 1920')
        image.filepath = '//' + os.path.relpath(ROOT / plate, target.parent).replace('\\', '/')
        image.pack()
        node = nodes.new('CompositorNodeImage')
        node.image = image
        node.location = (-700, 250 - index * 250)
        images.append(node)
    switch = nodes.new('ShaderNodeMix')
    switch.data_type = 'RGBA'
    switch.label = 'Same room: night until sunrise at 15 seconds'
    switch.location = (-450, 170)
    links.new(images[0].outputs['Image'], switch.inputs[6])
    links.new(images[1].outputs['Image'], switch.inputs[7])
    for frame, value in [(1, 0), (360, 0), (361, 1), (528, 1)]:
        switch.inputs[0].default_value = value
        switch.inputs[0].keyframe_insert(data_path='default_value', frame=frame)
    constant(group)
    layers = nodes.new('CompositorNodeRLayers')
    layers.scene = scene
    layers.location = (-450, -160)
    layers.label = 'Transparent Eevee: rigged static SVG puppet and captions'
    over = nodes.new('CompositorNodeAlphaOver')
    over.inputs['Factor'].default_value = 1
    over.location = (180, 80)
    links.new(switch.outputs[2], over.inputs['Background'])
    links.new(layers.outputs['Image'], over.inputs['Foreground'])
    links.new(over.outputs[0], output.inputs['Image'])
    raw = nodes.new('CompositorNodeOutputFile')
    raw.directory = '//' + os.path.relpath(EP / 'renders' / (target.stem + '_Transparent'), target.parent).replace('\\', '/')
    raw.file_name = ''
    raw.format.media_type = 'IMAGE'
    raw.format.file_format = 'PNG'
    raw.format.color_mode = 'RGBA'
    raw.format.color_depth = '8'
    raw.format.compression = 50
    raw.save_as_render = True
    raw.file_output_items.new('RGBA', 'EP010_Transparent_######')
    links.new(layers.outputs['Image'], raw.inputs[0])
    raw.location = (150, -180)
    scene.render.use_compositing = True
    scene.render.compositor_device = 'GPU'
    return group


def main():
    import bpy
    from tools.ep010_binge_puppet import build_episode_puppets
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='02_EPISODES/EP010_Binge_Watching/blend/EP010_Binge_Watching_v004.blend')
    parser.add_argument('--cues', default='02_EPISODES/EP010_Binge_Watching/edit/v001/speech_cues_v001.json')
    parser.add_argument('--plates', default='02_EPISODES/EP010_Binge_Watching/edit/plate_composition_v002.json')
    parser.add_argument('--report', default='02_EPISODES/EP010_Binge_Watching/edit/v004/project_verification_v004.json')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
    target, cue_path, plate_path, report_path = [(ROOT / value).resolve() for value in (args.output, args.cues, args.plates, args.report)]
    if any(not path.is_relative_to(ROOT) for path in (target, cue_path, plate_path, report_path)):
        raise ValueError('Use repository-relative episode paths')
    if report_path.exists():
        raise FileExistsError('Choose a new numbered project report')
    cues = json.loads(cue_path.read_text(encoding='utf-8'))
    plate_info = json.loads(plate_path.read_text(encoding='utf-8'))
    defaults = json.loads((ROOT / 'config/production_defaults.json').read_text(encoding='utf-8'))
    identity = defaults['tts_character_voices']['Peter']
    peter_lines = [line for line in cues['lines'] if line['speaker'] in {'peter', 'inner'}]
    if not peter_lines or any(line['voice'] != identity['voice'] or line.get('character') != 'Peter' for line in peter_lines):
        raise ValueError('Every Peter line and inner thought must use his locked Charon identity')
    start_episode_from_master(target)
    scene = bpy.data.scenes.new(SCENE)
    bpy.context.window.scene = scene
    configure_scene(scene, duration_seconds=22, transparent=True)
    scene.eevee.taa_render_samples = 16
    scene.render.filepath = '//../renders/' + target.stem + '/EP010_######'
    scene.world = bpy.data.worlds.new('EP010_Transparent_Unlit_World')
    puppets = build_episode_puppets(scene, cues, xy)
    stage = bpy.data.collections.new('EP010_Fictional_Streaming_UI_And_Props')
    scene.collection.children.link(stage)
    shake = bpy.data.objects.new('CTRL_EP010_Three_Frame_Shake', None)
    stage.objects.link(shake)
    for key in ('main', 'inner'):
        puppets[key]['rig'].parent = shake
    # Projected television screen coordinates from the actual locked plate camera.
    quad = plate_info['tv_screen_quad_px']
    def uv(u, v):
        a, b, c, d = quad
        return ((1-v)*((1-u)*a[0]+u*b[0])+v*((1-u)*d[0]+u*c[0]),
                (1-v)*((1-u)*a[1]+u*b[1])+v*((1-u)*d[1]+u*c[1]))
    def screen_rect(u, v, w, h, color):
        return shape([uv(u,v),uv(u+w,v),uv(u+w,v+h),uv(u,v+h)], color, None, 0)
    screen = contour_mesh('EP010_Fictional_TV_Screen', [shape(quad,'#15284B',None,0),
        screen_rect(.035,.055,.36,.06,'#86AFFF'),screen_rect(.07,.33,.23,.35,'#FFBF69'),
        screen_rect(.37,.33,.23,.35,'#728EF6'),screen_rect(.67,.33,.23,.35,'#FF879E'),
        screen_rect(.05,.81,.9,.12,'#202F52')], xy, stage, z=.10, scale=UNIT)
    screen.parent = shake
    sx, sy = uv(.50, .21)
    stage_text(stage,'AFTER HOURS',sx,sy,20,'#FFFFFF','TV_Fictional_Show',depth=.20).parent=shake
    for label, interval in [('ONE EPISODE',(1,144)),('NEXT EPISODE: 5',(145,168)),
                            ('NEXT EPISODE: 4',(169,186)),('PLAYING EPISODE 02',(187,240)),
                            ('STILL WATCHING?',(241,288)),('SEASON FINALE',(289,360)),
                            ('PLAY NEXT SEASON',(361,528))]:
        tx, ty = uv(.50,.88)
        stage_text(stage,label,tx,ty,13,'#FFFFFF','TV_'+label.replace(' ','_'),interval,depth=.20).parent=shake
    # Persistent clock graphics communicate jump cuts without re-rendering room geometry.
    clock = contour_mesh('EP010_Clock_Card', [rectangle(654,568,293,77,'#152238','#FFFFFF',3)],xy,stage,z=2.4,scale=UNIT)
    clock.parent=shake
    for body, interval in [('9:00 PM',(1,144)),('11:47 PM',(145,240)),('3:26 AM',(241,360)),('6:02 AM',(361,528))]:
        stage_text(stage,body,800,606,42,'#FFFFFF','CLOCK_'+body.replace(':','_'),interval).parent=shake
    # Solid-color window overlay crosses only the window panes, leaving the room static.
    if 'window_glass_strips_px' in plate_info:
        glow = contour_mesh('EP010_Time_Lapse_Window_Overlay',
            [shape(win,'#DB8E73',None,0) for win in plate_info['window_glass_strips_px']],xy,stage,z=-.10,scale=UNIT)
        visibility(glow,[(321,360)],total_frames=FRAMES)
    # Reuse the static table pixels as a foreground occluder: seated slippers
    # pass behind the table rather than floating over its top. No new 3D render.
    for index,source in enumerate(plate_info['plates']):
        mesh=bpy.data.meshes.new('EP010_Table_Occluder_'+str(index))
        corners=[(158,1730),(925,1730),(925,1920),(158,1920)]
        # Include the existing bowl's silhouette, which rises above the table.
        # Only that contour occludes the seated left slipper; neighboring couch
        # pixels remain transparent rather than hiding the whole lower leg.
        bowl=[(236,1704),(238,1694),(249,1687),(273,1682),(313,1680),(355,1684),
              (384,1692),(396,1703),(393,1720),(381,1735),(361,1745),(271,1745),
              (253,1737),(243,1722)]
        points=corners+bowl
        mesh.from_pydata([(*xy(x,y),1.4) for x,y in points],[],[(0,1,2,3),tuple(range(4,len(points)))])
        mesh.uv_layers.new(name='Full_Frame_Plate_Pixels')
        for loop,(x,y) in zip(mesh.uv_layers.active.data,points):
            loop.uv=(x/1080,1-y/1920)
        ob=bpy.data.objects.new(mesh.name,mesh)
        stage.objects.link(ob)
        image=bpy.data.images.load(str(ROOT/source),check_existing=True)
        image.pack()
        material=flat_material('EP010_Table_Plate_Material_'+str(index),'#FFFFFF')
        texture=material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.image=image
        material.node_tree.links.new(texture.outputs['Color'],next(node for node in material.node_tree.nodes if node.type=='EMISSION').inputs['Color'])
        mesh.materials.append(material)
        visibility(ob,[(1,360) if index==0 else (361,528)],total_frames=FRAMES)
    # The requested three-frame realization shake moves artwork only; captions stay fixed.
    thirty = next((word['start_frame'] for word in cues['words'] if word['word'].strip('.,!?').lower()=='thirty'),449)
    for frame,dx,dy in [(1,0,0),(thirty-1,0,0),(thirty,3,-2),(thirty+1,-3,2),(thirty+2,1,-1),(thirty+3,0,0),(528,0,0)]:
        shake.location=(dx*UNIT,-dy*UNIT,0)
        shake.keyframe_insert(data_path='location',frame=frame)
    constant(shake)
    words=sorted(cues['words'],key=lambda item:item['start'])
    records=[]
    for index,word in enumerate(words):
        start,end=word['start_frame'],word['end_frame']
        if index+1<len(words) and words[index+1]['start_frame']>start:
            end=min(end,words[index+1]['start_frame']-1)
        end=max(start,end)
        caption,bounds=create_caption(scene,word['word'],'CAPTION_EP010_%02d'%index,slot='dialogue',size=.94,outline_radius=.048)
        caption.location.z=5
        show_caption(caption,[(start,end)],pop=True)
        records.append({'word':word['word'],'speaker':word['speaker'],'start_frame':start,'end_frame':end,'max_bounds_px':bounds})
    titles=[]
    for body,name,interval,size in [('BINGE WATCHING\nEXPECTATION vs REALITY','Setup',(1,516),.58),
        ('POV: ONE EPISODE TURNED\nINTO THE WHOLE SEASON.','Final',(517,528),.58)]:
        caption,bounds=create_caption(scene,body,'TITLE_EP010_'+name,slot='main',size=size)
        caption.location.z=5
        show_caption(caption,[interval])
        titles.append({'text':body,'interval':list(interval),'bounds_px':bounds})
    plates=plate_info['plates']
    compose(scene,plates,target)
    audio=(ROOT/cues['mix_file']).resolve()
    strip=scene.sequence_editor_create().strips.new_sound('EP010 Charon dialogue + original comedy sound design',str(audio),channel=1,frame_start=1)
    strip.sound.pack()
    strip.sound.filepath='//'+os.path.relpath(audio,target.parent).replace('\\','/')
    scene.render.use_sequencer=False
    for line in cues['lines']:
        scene.timeline_markers.new(line['speaker']+': '+line['text'],frame=math.floor(line['start']*24)+1)
    scene['peter_voice']=identity['voice']
    scene['visual_style']='Flat solid-color SVG Peter over two matching realistic static room plates, explicitly requested in EP010 brief'
    scene['lip_sync_method']=cues['lip_sync_method']
    scene['hybrid_authorization']='Current EP010 user brief: Cycles static night and dawn plates, Eevee transparent 2D foreground'
    scene.frame_set(25)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
    parts=puppets['main']['part_objects']+puppets['inner']['part_objects']
    assert all(not ob.data.animation_data for ob in parts)
    report={'schema_version':1,'scene':SCENE,'built_project':target.relative_to(ROOT).as_posix(),
        'frames':528,'video_seconds':22,'resolution':[1080,1920],'fps':24,'engine':'BLENDER_EEVEE',
        'character_library':defaults['character_library'],'static_character_parts':len(parts),
        'skeletal_bones':sum(len(puppets[key]['rig'].data.bones) for key in ('main','inner')),
        'character_geometry_redraws_per_frame':0,'character_mesh_animation':False,'background_count':2,
        'background_plates':plates,'hybrid_authorization':scene['hybrid_authorization'],
        'compositor':'Packed static night/dawn images -> timed hard cut -> Alpha Over transparent Eevee foreground',
        'compositor_device':'GPU','transparent_foreground_sequence':str((EP/'renders'/(target.stem+'_Transparent')).relative_to(ROOT)),
        'color_management':'AgX baked into static Cycles PNG; Standard foreground/composition preserves solid SVG colors and baked plate appearance',
        'caption_font':'LuckiestGuy-Regular.ttf','spoken_caption_records':records,'title_records':titles,
        'final_title_bounds_px':titles[-1]['bounds_px'],'caption_shake_fixed':True,'shake_start_frame':thirty,
        'lip_sync_method':cues['lip_sync_method'],'peter_voice':identity['voice'],'speech_cues':cue_path.relative_to(ROOT).as_posix(),
        'packed_audio':True,'audio':audio.relative_to(ROOT).as_posix(),'visual_reviewed':False,'puppet_metadata':puppets['metadata']}
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('EP010_BUILD_COMPLETE',json.dumps({'project':report['built_project'],'parts':len(parts),'frames':528}),flush=True)


if __name__=='__main__':
    main()
