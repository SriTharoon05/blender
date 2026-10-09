import bpy,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP004_Dad_Mechanical_Keyboard'
def caption_outline(ob):
    white=ob.data.layers['White letters'].frames[0].drawing
    edges={}
    for st in white.strokes:
        vertices=[(round(p.position.x,6),round(p.position.y,6)) for p in st.points]
        for a,b in zip(vertices,vertices[1:]+vertices[:1]):
            key=tuple(sorted([a,b]));edges[key]=edges.get(key,0)+1
    boundary=[key for key,count in edges.items() if count==1]
    d=ob.data.layers['Black outline'].frames[0].drawing;d.remove_strokes();d.add_strokes([2]*len(boundary))
    radius=.045 if 'Tag' in ob.name else .055
    for i,(a,b) in enumerate(boundary):
        st=d.strokes[i];st.material_index=0;st.cyclic=False;st.fill_id=0;st.hide_stroke=False
        for p,xy in zip(st.points,[a,b]):p.position=(*xy,0);p.radius=radius;p.opacity=1
    d.tag_positions_changed()
    return len(boundary)

s=bpy.data.scenes['EP004_Dad_Mechanical_Keyboard'];bpy.context.window.scene=s
counts={}
for ob in s.objects:
    if ob.type=='GREASEPENCIL' and ob.name.startswith('CAPTION_'):counts[ob.name]=caption_outline(ob)
obj=bpy.data.objects['GP_EP004_Dad_Office_Keyboard'];mat=bpy.data.materials.new('GP_EP004_Glasses_Line');bpy.data.materials.create_gpencil_data(mat);mat.grease_pencil.color=(.38,.42,.44,1);obj.data.materials.append(mat);idx=len(obj.data.materials)-1
for f in obj.data.layers[0].frames:
    for st in f.drawing.strokes:
        if len(st.points)==5 and not st.cyclic:
            pts=[p.position for p in st.points];w=max(p.x for p in pts)-min(p.x for p in pts);h=max(p.y for p in pts)-min(p.y for p in pts)
            if .5<w<.68 and .25<h<.36 and min(p.y for p in pts)>1.7:
                st.material_index=idx
                for point in st.points:point.radius=.027
    f.drawing.tag_positions_changed()
s.frame_set(24);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP004_Dad_Keyboard_GP_v003.blend'),compress=True)
for frame in [36,97,230]:
    s.frame_set(frame);s.render.filepath=str(EP/'previews'/f'EP004_Final_Review_{frame:04d}.png');bpy.ops.render.render(write_still=True)
(EP/'edit/polish_verification.json').write_text(json.dumps({'caption_boundary_edges':counts,'glasses_material':'Visible grey metal','caption_outline':'Rounded native GP contour strokes; removes font-offset spikes'},indent=2))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v002.blend'))
for ob in bpy.context.scene.objects:
    if ob.type=='GREASEPENCIL' and ob.name.startswith('CAPTION_'):caption_outline(ob)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v003.blend'),compress=True)
print('EP004_AND_TEMPLATE_POLISHED',flush=True)
