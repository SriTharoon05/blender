import bpy, json, uuid
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender')
s=bpy.context.scene; rig=bpy.data.objects['RIG_BRIX']; cam=s.camera
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'01_TEMPLATES/Versions/BRIX_Foundation_v006.blend'))
bpy.data.objects['CHAR_BRIX_Hair_SweptFringe'].location.z+=.075
mouth=bpy.data.objects['CHAR_BRIX_Mouth']
for name in ['SURPRISED','SCARED','IMPRESSED','EXCITED','open_surprise','impressed_O']:
    for v in mouth.data.shape_keys.key_blocks[name].data:v.co.z-=.025
bpy.data.objects['PROP_MaterialSelector_Display'].location.y=1.13
bpy.data.objects['PROP_MaterialSelector_Label'].location.y=1.09
for name in ['MAT_Jelly_Red','MAT_Jelly_Blue']:
    # Clearer smooth surface finish for the template demonstration.
    m=bpy.data.materials[name]
    for n in m.node_tree.nodes:
        if n.type=='BUMP':n.inputs['Strength'].default_value=0
        if n.type=='TEX_NOISE':n.inputs['Scale'].default_value=3
for side in ['L','R']:
    o=bpy.data.objects['CHAR_BRIX_EyeCatchlight_'+side]; f=o.driver_add('hide_render'); d=f.driver; v=d.variables.new(); v.name='blink'; v.type='SINGLE_PROP'; v.targets[0].id=rig; v.targets[0].data_path='["blink"]'; d.expression='blink > 0.95'
guide=bpy.data.texts.new('README_BRIX_Production'); guide.write((ROOT/'PRODUCTION_GUIDE.md').read_text(encoding='utf-8'))
catalogs={name:str(uuid.uuid4()) for name in ['Characters','Materials','Props','Environments','UI','Lighting','Cameras']}
(ROOT/'00_LIBRARY/blender_assets.cats.txt').write_text('# BRIX production asset catalogs\nVERSION 1\n\n'+'\n'.join(f'{u}:{n}:{n}' for n,u in catalogs.items())+'\n',encoding='utf-8')
for name,cat in [('ASSET_BRIX','Characters'),('ASSET_Lab','Environments'),('ASSET_ExperimentStation','Props'),('ASSET_MobileUI','UI'),('ASSET_StudioLighting','Lighting'),('ASSET_VerticalCamera','Cameras')]:
    c=bpy.data.collections[name]; c.asset_data.catalog_id=catalogs[cat]; c.asset_data.description='BRIX original reusable '+cat.lower()+' / foundation v1.0'; c.asset_data.author='BRIX Production'
for m in bpy.data.materials:
    if m.asset_data:m.asset_data.catalog_id=catalogs['Materials']; m.asset_data.description='Lightweight procedural BRIX material / EEVEE preview'; m.asset_data.author='BRIX Production'
def write(path,blocks):
    dest=ROOT/path; assert not dest.exists(),f'Refusing to overwrite canonical: {dest}'
    bpy.data.libraries.write(str(dest),set(blocks),path_remap='RELATIVE_ALL',fake_user=True,compress=True)
    return {'path':path,'bytes':dest.stat().st_size}
def library_scene(name,cols,camera=None):
    sc=bpy.data.scenes.new(name)
    for col in cols:sc.collection.children.link(bpy.data.collections[col])
    sc.world=s.world; sc.camera=camera; sc.render.engine='BLENDER_EEVEE'; sc.render.resolution_x=1080; sc.render.resolution_y=1920; sc.render.resolution_percentage=50; sc.render.fps=30
    sc.eevee.use_raytracing=True; sc.eevee.taa_render_samples=96; sc.view_settings.view_transform='AgX'
    sc['production_role']='CANONICAL LIBRARY / save a version before significant edits / append collections into episode copies'
    return sc
# A standalone character scene has its own preview camera; production rig and
# geometry stay identical to the assembled template.
charcamdata=bpy.data.cameras.new('CAM_BRIX_CharacterPreview_Lens'); charcam=bpy.data.objects.new('CAM_BRIX_CharacterPreview',charcamdata)
charcam.location=(2.5,-6.5,3.6); charcam.rotation_euler=(Vector((-1.62,-.35,1.55))-charcam.location).to_track_quat('-Z','Y').to_euler(); charcamdata.lens=60
char_scene=library_scene('BRIX_Character_Master',['ASSET_BRIX','ASSET_StudioLighting'],charcam); char_scene.collection.objects.link(charcam)
env_scene=library_scene('BRIX_Laboratory_Master',['ASSET_Lab','ASSET_ExperimentStation','ASSET_StudioLighting','ASSET_VerticalCamera'],cam)
bpy.ops.file.pack_all(); bpy.context.view_layer.update()
manifest=[]
manifest.append(write('00_LIBRARY/Characters/BRIX/BRIX_Master.blend',[char_scene,guide]))
manifest.append(write('00_LIBRARY/Environments/BRIX_Lab_Master.blend',[env_scene,guide]))
manifest.append(write('00_LIBRARY/Props/BRIX_ExperimentStation.blend',[bpy.data.collections['ASSET_ExperimentStation']]))
manifest.append(write('00_LIBRARY/Materials/BRIX_Materials.blend',list(bpy.data.materials)))
manifest.append(write('00_LIBRARY/UI/BRIX_UI.blend',[bpy.data.collections['ASSET_MobileUI']]))
manifest.append(write('00_LIBRARY/Lighting/BRIX_StudioLighting.blend',[bpy.data.collections['ASSET_StudioLighting'],s.world]))
manifest.append(write('00_LIBRARY/Cameras/BRIX_VerticalCamera.blend',[bpy.data.collections['ASSET_VerticalCamera']]))
# Remove auxiliary master scenes from the working template after exporting.
bpy.data.scenes.remove(char_scene); bpy.data.scenes.remove(env_scene); bpy.data.objects.remove(charcam,do_unlink=True)
s.render.resolution_percentage=100; s.eevee.taa_render_samples=192
s.render.filepath=str(ROOT/'01_TEMPLATES/Previews/BRIX_Foundation_Preview.png')
bpy.ops.render.render(write_still=True)
s.render.resolution_percentage=50; s.eevee.taa_render_samples=96; s.render.filepath='//Previews/BRIX_Foundation_Preview.png'
s['asset_manifest']='//../00_LIBRARY/asset_manifest.json'
bpy.ops.file.make_paths_relative()
dest=ROOT/'01_TEMPLATES/BRIX_Shorts_Master.blend'; assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
manifest.append({'path':'01_TEMPLATES/BRIX_Shorts_Master.blend','bytes':dest.stat().st_size})
(ROOT/'00_LIBRARY/asset_manifest.json').write_text(json.dumps({'foundation_version':'1.0','blender_version':bpy.app.version_string,'libraries':manifest,'preview':'01_TEMPLATES/Previews/BRIX_Foundation_Preview.png','asset_reuse':'Append canonical collections. Animate only within saved episode copies.','validation':'01_TEMPLATES/Previews/validation_report.json'},indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2))
