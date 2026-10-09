import bpy,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
folder=ROOT/'00_LIBRARY/Characters/School_Guy_2D';folder.mkdir(exist_ok=True)
asset=folder/'School_Guy_2D_v001.blend'
template=ROOT/'01_TEMPLATES/GreasePencil_Shorts_720p24_Master_v001.blend'
assert not asset.exists() and not template.exists(), 'Preserve existing canonical versions.'
source=bpy.data.objects['GP_EP003_Characters_Set_Laptops'];drawing=next(f for f in source.data.layers[0].frames if f.frame_number==75).drawing
data=bpy.data.grease_pencils.new('GP_School_Guy_2D_Approved');data.stroke_depth_order='2D'
obj=bpy.data.objects.new('CHAR_School_Guy_2D',data)
coll=bpy.data.collections.new('CHAR_School_Guy_2D');coll.objects.link(obj)
for mat in source.data.materials:data.materials.append(mat)
layer=data.layers.new('Approved character - editable strokes',set_active=True);layer.use_lights=False
chosen=[]
character={'skin','skinShade','hair','hairLight','shirt','shirtShade','shirtLight','white','ink','sweat'}
for stroke in drawing.strokes:
    mat=source.data.materials[stroke.material_index].name.removeprefix('GP_EP003_')
    coords=[tuple(p.position) for p in stroke.points]
    belongs=mat in character
    if mat in {'line','lightLine','chalk'}:
        belongs=all(-2.8<=p[0]<=1.02 and -2.97<=p[1]<=3.05 for p in coords)
    if belongs:chosen.append(stroke)
assert len(chosen)>20
dest=layer.frames.new(1).drawing;dest.add_strokes([len(st.points) for st in chosen])
for i,src in enumerate(chosen):
    st=dest.strokes[i];st.material_index=src.material_index;st.cyclic=src.cyclic;st.fill_id=i+1 if src.cyclic else 0;st.fill_opacity=1
    for p,q in zip(st.points,src.points):p.position=q.position;p.radius=q.radius;p.opacity=q.opacity
dest.tag_positions_changed();obj['identity']='Approved recurring 2D guy from EP003. Preserve face silhouette, hair, skin palette and hoodie design.'
coll.asset_mark();coll.asset_data.description='Canonical recurring 2D student, reused directly from the approved EP003 Grease Pencil drawings.'
bpy.data.libraries.write(str(asset),{coll},fake_user=True,compress=True)
reference=Path(r'C:/Users/assri/AppData/Local/Temp/codex-clipboard-01b749cb-8642-4699-8298-e88588008460.png')
shutil.copy2(reference,folder/'Approved_Character_Reference.png')
manifest={'character':'School Guy 2D','approved_reference':'Approved_Character_Reference.png','asset':'School_Guy_2D_v001.blend','collection':'CHAR_School_Guy_2D','source_episode':'EP003_Gaming_Laptop_GP','source_frame':75,'reuse_for':'All future 2D content unless user explicitly requests another character','preserve':['face silhouette','dark angular hair','skin colour','simple eye and mouth design','blue hoodie design'],'future_render_defaults':{'width':720,'height':1280,'fps':24,'engine':'Eevee','gpu':'NVIDIA GTX 1650 Ti'},'character_strokes':len(chosen)}
(folder/'character_manifest.json').write_text(json.dumps(manifest,indent=2))
# A clean template containing the approved asset, leaving all source episodes untouched.
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='2D_GreasePencil_Shorts_720p24'
with bpy.data.libraries.load(str(asset),link=False) as (src,dst):dst.collections=['CHAR_School_Guy_2D']
s.collection.children.link(dst.collections[0])
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=720;s.render.resolution_y=1280;s.render.resolution_percentage=100;s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=264
s.eevee.taa_render_samples=8;s.eevee.use_raytracing=False;s.render.use_motion_blur=False;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=50;s.render.filepath='//../renders/frames_720p24/'
s.view_settings.view_transform='Standard';s.view_settings.look='None'
world=bpy.data.worlds.new('Warm_2D_Background');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=bpy.data.materials['GP_EP003_wall'].grease_pencil.fill_color;s.world=world
camera=bpy.data.cameras.new('CAM_2D_Portrait');camera.type='ORTHO';camera.ortho_scale=16;cam=bpy.data.objects.new('CAM_2D_Portrait',camera);s.collection.objects.link(cam);cam.location=(0,0,30);s.camera=cam
o=bpy.data.objects['CHAR_School_Guy_2D'];bpy.context.view_layer.objects.active=o;o.select_set(True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
s['future_2d_defaults']='Use approved School Guy 2D for all future 2D content; 720x1280, 24fps, fast Eevee on GTX 1650 Ti.'
bpy.ops.wm.save_as_mainfile(filepath=str(template),compress=True)
assert o.type=='GREASEPENCIL' and len(o.data.layers[0].frames[0].drawing.strokes)==len(chosen)
print('APPROVED_2D_CHARACTER_AND_TEMPLATE_SAVED',len(chosen),flush=True)
