import bpy,json,hashlib
from pathlib import Path
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender'); EP=ROOT/'02_EPISODES/EP002_Impossible_Blankets'
for p in ['blend','cache/rigidbody','cache/softbody','cache/cloth','cache/fluid','cache/particles','previews','renders/frames','audio','edit','scripts']:(EP/p).mkdir(parents=True,exist_ok=True)
assert not (EP/'blend/EP002_v001.blend').exists(),'Episode exists; preserve versions.'
protected=list((ROOT/'02_EPISODES/EP001_Material_Test').rglob('*'))+list((ROOT/'00_LIBRARY').rglob('*.blend'))+list((ROOT/'01_TEMPLATES').glob('*.blend'))
(EP/'edit/protected_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.is_file()},indent=2),encoding='utf-8')
# Create a separate scene; no operators are run on EP001 and no EP001 file is saved.
new=bpy.data.scenes.new('EP002_Impossible_Blankets'); bpy.context.window.scene=new
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v001.blend'),compress=True)
print('EP002_SEPARATE_FILE_CREATED')
