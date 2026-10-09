import bpy,ast,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP006_Call_Vs_Text'
s=bpy.data.scenes['EP006_Call_Vs_Text'];bpy.context.window.scene=s
obj=bpy.data.objects['GP_EP006_Original_Split_Drawings'];gp=obj.data;layer=gp.layers[0];indices={m.name.removeprefix('GP_EP006_'):i for i,m in enumerate(gp.materials)};strokes=[]
for file,names in [('ep003_gp_laptop.py',{'shape','line','ellipse','rect','curve','smooth','mix','head'}),('ep006_call_text_gp.py',{'transform','room','phone','face','body','left','right','draw'})]:
    for node in ast.parse((ROOT/'tools'/file).read_text(encoding='utf-8-sig')).body:
        if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),globals())
# Build original native GP font contours for the phone's notification card.
font=next((f for f in bpy.data.fonts if 'ariblk' in f.filepath.lower()),None)
if font is None:font=bpy.data.fonts.load('C:/Windows/Fonts/ariblk.ttf');font.pack()
cu=bpy.data.curves.new('UI_EP006_Incoming_Call_EditableSource','FONT');cu.body='Incoming\nCall';cu.size=.22;cu.font=font;cu.align_x='CENTER';cu.space_line=1.16
source=bpy.data.objects.new(cu.name,cu);s.collection.objects.link(source);bpy.context.view_layer.update()
ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();letters=[[(mesh.vertices[i].co.x,mesh.vertices[i].co.y) for i in tri.vertices] for tri in mesh.loop_triangles];ev.to_mesh_clear();source.hide_render=True;source.hide_viewport=True
# Reuse the font geometry rather than duplicating 1,817 triangles each frame.
textgp=bpy.data.grease_pencils.new('UI_EP006_Incoming_Call');textgp.stroke_depth_order='2D';textob=bpy.data.objects.new(textgp.name,textgp);s.collection.objects.link(textob);textob.location.z=.75;textgp.materials.append(gp.materials[indices['ink']])
textlayer=textgp.layers.new('Incoming Call lettering',set_active=True);textlayer.use_lights=False;drawing=textlayer.frames.new(1).drawing;drawing.add_strokes([3]*len(letters))
for i,tri in enumerate(letters):
    st=drawing.strokes[i];st.material_index=0;st.cyclic=True;st.fill_id=i+1;st.hide_stroke=True;st.fill_opacity=1
    for p,(a,b) in zip(st.points,tri):p.position=(-3.75+a,.85+b,0);p.radius=0;p.opacity=1
drawing.tag_positions_changed()
for fr,v in [(1,0),(72,0),(73,1),(192,1),(193,0)]:textlayer.opacity=v;textlayer.keyframe_insert(data_path='opacity',frame=fr)
for fr in range(73,193):textob.location.x=.035*math.sin((fr-1)/24*81);textob.keyframe_insert(data_path='location',index=0,frame=fr)
UI_LETTERS=[]
for fr in range(1,433):
    layer.frames.remove(fr);draw((fr-1)/24,fr)
    if fr%48==0:print('POLISHED_FRAME',fr,flush=True)
assert len(layer.frames)==432 and s.sequence_editor.strips[0].sound.packed_file
s.frame_set(97);s.render.filepath='//../renders/frames_1080p24/EP006_######';bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP006_Call_Text_GP_v003.blend'),compress=True)
for fr in [49,97,145,229,361]:
    s.frame_set(fr);s.render.filepath=str(EP/'previews'/f'EP006_Polished_{fr:04d}.png');bpy.ops.render.render(write_still=True)
print('EP006_POLISHED_COMPLETE',flush=True)
