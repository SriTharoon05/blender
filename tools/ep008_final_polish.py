"""Final contact-aware desk collapse and packed-source verification."""
import bpy,ast,json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
EP=ROOT/'02_EPISODES/EP008_Research_Then_Now'
s=bpy.data.scenes['EP008_Research_Then_Now'];bpy.context.window.scene=s
source=ROOT/'tools/ep008_research_gp.py'
def extract(path,names=None):
    for node in ast.parse(path.read_text(encoding='utf-8-sig')).body:
        if isinstance(node,ast.FunctionDef) and (names is None or node.name in names):
            if node.name not in ['extract','visibility']:
                exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),globals())
extract(ROOT/'tools/ep003_gp_laptop.py',{'color','shape','line','ellipse','rect','curve','smooth','mix','head'})
extract(source)
for node in ast.parse(source.read_text(encoding='utf-8')).body:
    if isinstance(node,ast.Assign) and any(isinstance(v,ast.Name) and v.id in ['GLYPHS','CARDS'] for v in node.targets):
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),globals())
obj=bpy.data.objects['GP_EP008_Student_And_Research_Props'];gp=obj.data;layer=gp.layers[0]
indices={m.name.replace('GP_EP008_',''):i for i,m in enumerate(gp.materials)}
for fr in range(565,577):
    layer.frames.remove(fr);strokes=[];reality((fr-1)/24);commit(fr)
packed={}
for node in s.compositing_node_group.nodes:
    if node.type=='IMAGE':
        im=node.image;path=EP/'plates'/Path(im.filepath).name
        expected=hashlib.sha256(path.read_bytes()).hexdigest()
        if not im.packed_file or hashlib.sha256(bytes(im.packed_file.data)).hexdigest()!=expected:
            replacement=bpy.data.images.load(str(path),check_existing=False)
            replacement.filepath='//../plates/'+path.name;replacement.pack();node.image=replacement;im=replacement
        assert hashlib.sha256(bytes(im.packed_file.data)).hexdigest()==expected
        packed[path.name]=expected
assert len(packed)==2 and len(layer.frames)==576
report=json.loads((EP/'edit/project_verification.json').read_text())
report.update({'packed_plate_sha256':packed,'collapse_polish':'Forward torso compression, hidden upright neck, angular head/ear resting on crossed sleeve; exact desk-impact frame571','final_project_version':4})
(EP/'edit/project_verification.json').write_text(json.dumps(report,indent=2))
s.frame_set(85);s.render.use_compositing=True;s.render.filepath='//../renders/frames_1080p24/EP008_######'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP008_Research_GP_v004.blend'),compress=True)
for fr in [529,565,571,576]:
    s.frame_set(fr);s.render.filepath=str(EP/'previews'/f'EP008_Review_{fr:04d}.png');bpy.ops.render.render(write_still=True)
print('EP008_FINAL_POLISH_COMPLETE',packed,flush=True)
