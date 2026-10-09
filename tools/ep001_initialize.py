import bpy, hashlib, json
from pathlib import Path
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender'); EP=ROOT/'02_EPISODES/EP001_Material_Test'
for p in ['blend','cache/rigidbody','cache/softbody','cache/cloth','cache/fluid','cache/particles','previews','renders/frames','audio','edit','scripts']:(EP/p).mkdir(parents=True,exist_ok=True)
dest=EP/'blend/EP001_v001.blend'; assert not dest.exists(),'Episode v001 already exists; do not overwrite.'
paths=[ROOT/'01_TEMPLATES/BRIX_Shorts_Master.blend']+sorted((ROOT/'00_LIBRARY').rglob('*.blend'))
(EP/'edit/master_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2),encoding='utf-8')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'01_TEMPLATES/BRIX_Shorts_Master.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
bpy.context.scene.name='EP001_Material_Test'
print('EPISODE_COPY_READY '+bpy.data.filepath)
# Inspect fluid RNA using a small, unbaked test object in the episode copy.
bpy.ops.mesh.primitive_cube_add(); o=bpy.context.object; o.name='TEMP_EP001_FluidRNA'; mod=o.modifiers.new('Fluid RNA inspection','FLUID'); mod.fluid_type='DOMAIN'; bpy.context.view_layer.update(); d=mod.domain_settings; d.domain_type='LIQUID'
print('FLUID_DOMAIN '+str([(p.identifier,str(getattr(d,p.identifier))) for p in d.bl_rna.properties if any(w in p.identifier for w in ['visco','cache','mesh','resolution','time','use_diff','surface','particle','border'])]))
bpy.data.objects.remove(o,do_unlink=True)
