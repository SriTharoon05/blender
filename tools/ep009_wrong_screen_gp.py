"""Superseded EP009 draft; retained as historical reference and helper source.

The final entrypoint is ep009_wrong_screen_cutout.py. This older per-frame
character/two-plate proposal is not the current approved puppet pipeline.
Only its constant/show_intervals helpers are reused by the final builder.

Build only. Render through the production queue after reviewing actual frames.
All spoken captions derive from the aligned audio cue sheet, never guessed time.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.grease_pencil_toolkit import (DrawingBuilder, color, commit_drawing,
    configure_scene, create_caption, create_gp_object, start_episode_from_master)

EP = ROOT / '02_EPISODES/EP009_Wrong_Screen'
SCENE = 'EP009_Wrong_Screen'
UNIT = 16 / 1920


def xy(x, y):
    return ((x - 540) * UNIT, (960 - y) * UNIT)


def smooth(value):
    value = max(0., min(1., value))
    return value * value * (3 - 2 * value)


def constant(data):
    if not data.animation_data or not data.animation_data.action:
        return
    action = data.animation_data.action
    for slot in action.slots:
        for layer in action.layers:
            for strip in layer.strips:
                bag = strip.channelbag(slot, ensure=False)
                if bag:
                    for fc in bag.fcurves:
                        for key in fc.keyframe_points:
                            key.interpolation = 'CONSTANT'


def show_intervals(ob, intervals, pop=False):
    """Opacity uses hard word boundaries; scale pops stay within fitted bounds."""
    for layer in ob.data.layers:
        layer.opacity = 0
        layer.keyframe_insert(data_path='opacity', frame=1)
        for start, end in intervals:
            for frame, opacity in [(max(1, start - 1), 0), (start, 1), (end + 1, 0)]:
                layer.opacity = opacity
                layer.keyframe_insert(data_path='opacity', frame=frame)
    constant(ob.data)
    if pop:
        # Set a geometric origin so pop motion does not drag a bottom word upward.
        bounds = ob['caption_export_bounds_px']
        cx, cy = xy((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
        for layer in ob.data.layers:
            for frame in layer.frames:
                for stroke in frame.drawing.strokes:
                    for point in stroke.points:
                        point.position.x -= cx
                        point.position.y -= cy
                frame.drawing.tag_positions_changed()
        ob.location.x, ob.location.y = cx, cy
        for start, end in intervals:
            for frame, scale in [(start, .90), (min(start + 2, end), 1.), (end, 1.)]:
                ob.scale = (scale, scale, scale)
                ob.keyframe_insert(data_path='scale', frame=frame)


def main():
    import bpy
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='02_EPISODES/EP009_Wrong_Screen/blend/EP009_Wrong_Screen_GP_v001.blend')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
    target = (ROOT / args.output).resolve()
    cue_path = EP / 'edit/speech_cues_v001.json'
    cues = json.loads(cue_path.read_text(encoding='utf-8'))
    asset_dir = ROOT / '00_LIBRARY/Characters/Peter_2D'
    candidates = sorted(asset_dir.glob('*paths*.json')) + sorted(asset_dir.glob('*contours*.json'))
    if not candidates:
        candidates = [p for p in sorted(asset_dir.glob('*.json')) if 'paths' in json.loads(p.read_text(encoding='utf-8'))]
    assert candidates, 'Reusable Peter vector contour asset is required'
    vector_path = candidates[0]
    vector = json.loads(vector_path.read_text(encoding='utf-8'))
    plates = json.loads((EP / 'edit/plate_composition.json').read_text(encoding='utf-8'))
    screen_quad = plates['screen_quad_px_clockwise_from_top_left']
    mouse_x,mouse_y=plates['composition_landmarks_px']['mouse_center']
    start_episode_from_master(target)
    scene = bpy.data.scenes.new(SCENE)
    bpy.context.window.scene = scene
    configure_scene(scene, duration_seconds=18, transparent=True)
    scene.render.filepath = '//../renders/frames_1080p24/EP009_######'
    scene['character'] = 'Peter: native editable SVG-derived Grease Pencil'
    scene['approved_character_library'] = str(vector_path.relative_to(ROOT)).replace('\\', '/')
    scene['caption_policy'] = 'Luckiest Guy; aligned word-by-word lower-safe-band captions; top POV ending'
    scene['lip_sync'] = 'Audio-aligned speech mouth frames; silent off-screen host does not move Peter mouth'
    scene['source_audio_cues'] = '//../edit/speech_cues_v001.json'
    scene['speech_models'] = json.dumps(cues.get('models', {}))
    palette = {'skin': 'EFA773', 'skinShade': 'BA785A', 'shirt': 'F6F3EA',
        'shirtShade': 'CFCBD0', 'tie': 'A74453', 'ink': '191A24', 'line': '191A24',
        'white': 'FFFFFF', 'paper': 'EAF0F5', 'blue': '4788F5', 'green': '40C58C',
        'red': 'EF5962', 'dark': '202A43', 'screen': '182238', 'sweat': 'A4E9F4',
        'gold': 'FFC879', 'grey': 'AAB6CC'}
    obj, indices = create_gp_object(scene, 'GP_EP009_Peter_Acting', palette)
    char_collection = bpy.data.collections.new('CHAR_Peter_2D_EP009')
    scene.collection.children.link(char_collection)
    scene.collection.objects.unlink(obj)
    char_collection.objects.link(obj)
    drawing = DrawingBuilder(indices)
    svg_materials = {}

    def svg_material(path):
        key = (path.get('fill'), path.get('stroke'))
        if key not in svg_materials:
            mat = bpy.data.materials.new('Peter_Vector_%02d' % len(svg_materials))
            bpy.data.materials.create_gpencil_data(mat)
            mat.grease_pencil.show_fill = bool(key[0])
            mat.grease_pencil.show_stroke = bool(key[1])
            mat.grease_pencil.fill_color = color((key[0] or '#000000').lstrip('#'))
            mat.grease_pencil.color = color((key[1] or '#000000').lstrip('#'))
            obj.data.materials.append(mat)
            svg_materials[key] = len(obj.data.materials) - 1
        return svg_materials[key]

    paths = vector['paths']
    for path in paths:
        svg_material(path)
    expressions = vector['expressions']
    for group in expressions.values():
        for expression_paths in group.values():
            for path in expression_paths:
                svg_material(path)
    mouths = {}
    flat_mouths = cues.get('mouths', cues.get('mouth_frames', []))
    if isinstance(flat_mouths, dict):
        flat_mouths = list(flat_mouths.values())
    for line in cues['lines']:
        if line['speaker'].lower() in {'employee', 'peter'}:
            for item in line.get('mouth_frames', []):
                mouths[item['frame']] = item
    for item in flat_mouths:
        if item.get('speaker', 'employee').lower() in {'employee', 'peter'}:
            mouths[item['frame']] = item

    def shape(points, mat, width=4, closed=True):
        drawing.shape([xy(*p) for p in points], mat, width * UNIT / 2, closed)

    def line(points, mat='line', width=4):
        shape(points, mat, width, False)

    def rect(x, y, width, height, mat, stroke=3):
        shape([(x, y), (x + width, y), (x + width, y + height), (x, y + height)], mat, stroke)

    def ellipse(cx, cy, rx, ry, mat, stroke=3):
        shape([(cx + rx * math.cos(i * math.tau / 36), cy + ry * math.sin(i * math.tau / 36)) for i in range(36)], mat, stroke)

    def vector_shape(path, panic, collapse, nod, time):
        group = path.get('group', '')
        pts = path['points']
        if not pts:
            return
        px = sum(p[0] for p in pts) / len(pts)
        py = sum(p[1] for p in pts) / len(pts)
        identity = path.get('id', '').lower()
        coordinates = []
        tremble = math.sin(time * 42) * 2.3 if 10 <= time < 13 else 0
        for x, y in pts:
            if panic and group == 'eyes' and ('pupil' in identity or 'iris' in identity):
                x, y = px + (x - px) * .60, py + (y - py) * .60
            if group == 'brows' and panic:
                y -= 25
            if group == 'eyes' and not panic and ('pupil' in identity or 'iris' in identity):
                x += -12 if time < 6 else 0
            scale = .65 * (1 + .045 * smooth((time - 6) / .24))
            xx = 540 + (x - 620) * scale + tremble
            yy = 740 + (y - 440) * scale + nod + collapse
            coordinates.append(xy(xx, yy))
        radius = path.get('stroke_width', 0) * .65 * UNIT / 2 if path.get('stroke') else 0
        drawing.strokes.append((coordinates, svg_material(path), radius, path.get('closed', True)))

    def uv(u, v):
        a, b, c, d = screen_quad
        return ((1-v)*((1-u)*a[0]+u*b[0])+v*((1-u)*d[0]+u*c[0]),
                (1-v)*((1-u)*a[1]+u*b[1])+v*((1-u)*d[1]+u*c[1]))

    def screen_rect(u, v, width, height, mat, stroke=0):
        shape([uv(u, v), uv(u+width, v), uv(u+width, v+height), uv(u, v+height)], mat, stroke)

    # UI font objects remain editable. All are linked to fixed native screen-plane geometry.
    def ui_text(text, u, v, size, hexcode='FFFFFF', name='UI'):
        x, y = uv(u, v)
        data = bpy.data.curves.new('EP009_'+name, 'FONT')
        data.body, data.size = text, size * UNIT
        data.align_y = 'CENTER'
        ob = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(ob)
        ob.location = (*xy(x, y), 2)
        mat = bpy.data.materials.new(data.name+'_Ink')
        mat.diffuse_color = color(hexcode)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        emission = nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = color(hexcode)
        out = nodes.new('ShaderNodeOutputMaterial')
        mat.node_tree.links.new(emission.outputs[0], out.inputs[0])
        data.materials.append(mat)
        return ob

    texts = []
    def text_interval(text, u, v, size, start=1, end=432, hexcode='FFFFFF', name='UI'):
        ob = ui_text(text, u, v, size, hexcode, name)
        for frame, hidden in [(1, start > 1), (max(1, start-1), True), (start, False), (end+1, True)]:
            ob.hide_render = hidden
            ob.keyframe_insert(data_path='hide_render', frame=frame)
        constant(ob)
        texts.append(ob)
        return ob

    text_interval('Quarterly update', .08, .17, 28, 1, 144, name='Presentation_Title')
    text_interval('Everything is under control.', .08, .31, 15, 1, 144, 'A9BEDC', 'Presentation_Subtitle')
    text_interval('SHARING: ENTIRE SCREEN', .035, .08, 15, 145, 432, 'FFF2F2', 'Wrong_Share_Status')
    text_interval('47 TABS OPEN', .07, .20, 26, 145, 432, 'FFC879', 'Forty_Seven_Tabs')
    text_interval('Search: how to look busy at work', .055, .37, 17, 145, 432, '202A43', 'Search_History')
    text_interval('can my boss see this?', .07, .50, 17, 145, 432, 'E4EBFA', 'Search_Panic')
    text_interval('DO_NOT_OPEN', .545, .71, 21, 145, 432, 'FFF5D8', 'Suspicious_Folder')
    text_interval('Presentation.pptx', .05, .82, 14, 145, 432, 'B1BED6', 'Ignored_Presentation')

    for frame in range(1, 433):
        drawing.clear()
        t = (frame - 1) / 24
        panic = 6 <= t < 13
        collapse = 330 * smooth((t-14.45)/1.5) if t >= 14.45 else 0
        nod = -8 * math.sin(t*3) if t < 6 else 0
        body_dy = collapse*.6
        # Native flat-color office variant; portrait face/hair coordinates stay intact.
        shape([(487,920+body_dy),(604,920+body_dy),(638,1060+body_dy),(463,1060+body_dy)],'skin',5)
        shape([(490,983+body_dy),(381,1004+body_dy),(329,1056+body_dy),(347,1348+body_dy),
               (729,1348+body_dy),(752,1058+body_dy),(693,1015+body_dy),(592,982+body_dy),
               (548,1031+body_dy)],'shirt',7)
        shape([(490,979+body_dy),(545,1028+body_dy),(516,1072+body_dy),(466,1005+body_dy)],'shirtShade',4)
        shape([(593,979+body_dy),(545,1028+body_dy),(571,1070+body_dy),(620,1005+body_dy)],'shirtShade',4)
        shape([(535,1044+body_dy),(557,1044+body_dy),(569,1060+body_dy),(550,1085+body_dy),
               (532,1060+body_dy)],'tie',3)
        shape([(542,1080+body_dy),(555,1080+body_dy),(580,1215+body_dy),(550,1242+body_dy),
               (528,1214+body_dy)],'tie',3)
        if t < 6:
            shape([(355,1025),(381,1070),(231,1055),(190,997),(218,976)],'shirt',5)
            ellipse(190,957,29,21,'skin',4)
            line([(174,954),(179,925),(188,934)],width=4)
        else:
            shake = math.sin(t*58)*5 if panic else 0
            shape([(354,1060+body_dy),(386,1069+body_dy),(221,1225),(172,1205),(188,1176)],'shirt',5)
            ellipse(181+shake,1194,30,19,'skin',4)
        blink = any(abs(t-b) < .052 for b in [1.32,4.75,8.35,13.4])
        for path in paths:
            group = path.get('group','')
            if group in {'hoodie','neck','mouth'} or (blink and group=='eyes'):
                continue
            vector_shape(path, panic, collapse, nod, t)
        if blink:
            for path in expressions.get('eyes', {}).get('blink', []):
                vector_shape(path, panic, collapse, nod, t)
        mouth = mouths.get(frame, {'shape':'rest','openness':0})
        mouth_shape = {'A':'AA','E':'EE','O':'OH'}.get(mouth.get('shape'),mouth.get('shape','rest'))
        if mouth_shape not in expressions['mouth']:
            mouth_shape = 'AA' if mouth.get('openness',0) > .35 else 'rest'
        for path in expressions['mouth'][mouth_shape]:
            vector_shape(path, panic, collapse, nod, t)
        if panic:
            sy = 704 + (t-6)*10 % 65
            shape([(822,sy-13),(835,sy+16),(828,sy+33),(813,sy+31),(805,sy+17)],'sweat',3)
            if t >= 10:
                for dx in [-1,1]:
                    line([(540+dx*235,605),(540+dx*258,580)],'red',4)
        # Screen layer renders after the person: correct seated-behind-laptop occlusion.
        screen_rect(0,0,1,1,'screen')
        if t < 6:
            screen_rect(0,0,1,.055,'dark')
            screen_rect(.045,.065,.91,.042,'green')
            screen_rect(.06,.52,.56,.032,'blue')
            screen_rect(.06,.62,.42,.025,'grey')
            screen_rect(.06,.72,.62,.025,'grey')
            screen_rect(.82,.88,.10,.035,'green')
        else:
            screen_rect(0,0,1,.12,'red')
            for tab in range(18):
                screen_rect(.018+tab*.053,.125,.049,.028,'grey' if tab%3 else 'blue')
            screen_rect(.035,.32,.93,.09,'paper')
            screen_rect(.57,.57,.15,.11,'gold',2)
            screen_rect(.57,.54,.065,.045,'gold',2)
            if 10 <= t < 10.13:
                for u,v in [(.02,.28),(.9,.22),(.02,.89),(.9,.9)]:
                    p=uv(u,v)
                    line([(p[0]-12,p[1]-9),(p[0]+8,p[1]+5)],'red',4)
        cursor_u = .77 if t < 3.8 else .87
        cursor_v = .73 if t < 3.8 else .87
        if t >= 6:
            cursor_u = .84 + .06*math.sin(t*11)
            cursor_v = .76 + .12*math.sin(t*9)
        cursor = uv(cursor_u, cursor_v)
        shape([(cursor[0],cursor[1]),(cursor[0]+7,cursor[1]+23),(cursor[0]+13,cursor[1]+16),
               (cursor[0]+20,cursor[1]+15)],'white',2)
        # Contact hand settles on the mouse; final hovering hand is retained after collapse.
        hand_y = mouse_y-18 + (5*math.sin(t*23) if panic else 0)
        ellipse(mouse_x,hand_y,38,20,'skin',4)
        for finger in range(3):
            line([(mouse_x-17+finger*10,hand_y-10),(mouse_x-15+finger*10,hand_y+2)],width=2)
        commit_drawing(obj, frame, drawing, layer_name='Peter acting and comic screen UI')
        if frame % 72 == 0:
            print('EP009_BUILD_FRAME', frame, flush=True)

    # Speaker tile has actual voice activity indication, Peter stays still for host turns.
    tile_data, tile_indices = create_gp_object(scene, 'GP_EP009_Meeting_Host', palette)
    tile_draw = DrawingBuilder(tile_indices)
    for frame in range(1,433):
        t=(frame-1)/24
        active=any(line['speaker'].lower() not in {'employee','peter'} and line['start']<=t<line['end'] for line in cues['lines'])
        tile_draw.clear()
        def tile_shape(points,mat,w=3):
            tile_draw.shape([xy(*p) for p in points],mat,w*UNIT/2,True)
        tile_shape([(858,630),(1010,630),(1010,792),(858,792)],'green' if active else 'grey',0)
        tile_shape([(863,635),(1005,635),(1005,787),(863,787)],'dark',0)
        for cx,cy,rx,ry,mat in [(935,686,29,33,'skin'),(935,765,47,37,'blue')]:
            tile_shape([(cx+rx*math.cos(i*math.tau/30),cy+ry*math.sin(i*math.tau/30)) for i in range(30)],mat,3)
        for ex in [925,945]:
            tile_shape([(ex-2,681),(ex+2,681),(ex+2,686),(ex-2,686)],'ink',0)
        tile_shape([(925,699),(945,699),(943,709 if active and frame%4<2 else 702),(927,709 if active and frame%4<2 else 702)],'ink',0)
        commit_drawing(tile_data,frame,tile_draw,layer_name='Host speaker activity')

    caption_records=[]
    words=cues.get('words') or [word for line in cues['lines'] for word in line['words']]
    words=sorted(words,key=lambda word:word['start'])
    for index,word in enumerate(words):
        start=max(1,int(word.get('start_frame',math.floor(word['start']*24)+1)))
        end=min(432,int(word.get('end_frame',math.ceil(word['end']*24))))
        if index+1<len(words):
            next_start=max(1,int(words[index+1].get('start_frame',math.floor(words[index+1]['start']*24)+1)))
            if next_start>start:
                end=min(end,next_start-1)
        end=max(start,end)
        ob,bounds=create_caption(scene,word['word'],'CAPTION_EP009_Word_%02d'%index,slot='dialogue',size=.94,outline_radius=.048)
        show_intervals(ob,[(start,end)],pop=True)
        caption_records.append({'word':word['word'],'start_frame':start,'end_frame':end,'max_bounds_px':bounds})
    title,bounds=create_caption(scene,'POV: YOU SHARED\nTHE WRONG SCREEN.','CAPTION_EP009_Final_POV',slot='main',size=.65)
    show_intervals(title,[(361,432)])

    # Blender 5.2 compositor: static Cycles plates + transparent native 2D foreground.
    ng=bpy.data.node_groups.new('EP009_Two_Cycles_Plates_Peter_GP','CompositorNodeTree')
    scene.compositing_node_group=ng
    ng.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    nodes,links=ng.nodes,ng.links
    out=nodes.new('NodeGroupOutput')
    out.location=(750,100)
    plate_nodes=[]
    for name in plates['plates']:
        image=bpy.data.images.load(str(EP/'plates'/name),check_existing=True)
        image.filepath='//../plates/'+name
        image.pack()
        node=nodes.new('CompositorNodeImage');node.image=image
        plate_nodes.append(node)
    switch=nodes.new('ShaderNodeMix');switch.data_type='RGBA'
    links.new(plate_nodes[0].outputs['Image'],switch.inputs[6])
    links.new(plate_nodes[1].outputs['Image'],switch.inputs[7])
    for frame,value in [(1,0),(144,0),(145,1),(432,1)]:
        switch.inputs[0].default_value=value
        switch.inputs[0].keyframe_insert(data_path='default_value',frame=frame)
    constant(ng)
    rl=nodes.new('CompositorNodeRLayers');rl.scene=scene
    over=nodes.new('CompositorNodeAlphaOver');over.inputs['Factor'].default_value=1
    links.new(switch.outputs[2],over.inputs['Background'])
    links.new(rl.outputs['Image'],over.inputs['Foreground'])
    links.new(over.outputs[0],out.inputs['Image'])
    scene.render.use_compositing=True
    scene.render.compositor_device='GPU'
    # Shake only artwork; word captions stay in their safe band.
    for ob in [obj,tile_data,*texts]:
        base_x,base_y=ob.location.x,ob.location.y
        for frame,dx,dy in [(1,0,0),(240,0,0),(241,4,-3),(242,-4,3),(243,2,-1),(244,0,0),(432,0,0)]:
            ob.location.x,ob.location.y=base_x+dx*UNIT,base_y-dy*UNIT
            ob.keyframe_insert(data_path='location',frame=frame)
        constant(ob)
    for line_item in cues['lines']:
        marker=scene.timeline_markers.new(line_item['speaker']+': '+line_item['text'],frame=math.floor(line_item['start']*24)+1)
    sound=bpy.data.sounds.load(str(EP/'audio/EP009_Final_Mix_18s_v001.wav'),check_existing=True)
    sound.pack()
    sound.filepath='//../audio/EP009_Final_Mix_18s_v001.wav'
    editor=scene.sequence_editor_create()
    strip=editor.strips.new_sound('EP009 synchronized original sound',sound.filepath,channel=1,frame_start=1)
    strip.sound=sound
    scene.render.use_sequencer=False
    bpy.ops.file.pack_all()
    scene.frame_set(85)
    bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
    report={'scene':SCENE,'frames':432,'video_seconds':18,'resolution':[1080,1920],'fps':24,
        'engine':'BLENDER_EEVEE','compositor_device':'GPU','character_contours':str(vector_path.relative_to(ROOT)),
        'caption_font':'LuckiestGuy-Regular.ttf','spoken_caption_records':caption_records,
        'final_title_bounds_px':bounds,'lip_sync_source':str(cue_path.relative_to(ROOT)),
        'screen_quad_px':screen_quad,'packed_plates':2,'packed_audio':True,
        'built_project':str(target.relative_to(ROOT)),'visual_reviewed':False}
    (EP/'edit/project_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('EP009_BUILD_COMPLETE',json.dumps(report,default=str),flush=True)


if __name__=='__main__':
    main()
