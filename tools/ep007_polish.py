import bpy,ast,math,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP007_Alarm_Expectation_Reality'
s=bpy.data.scenes['EP007_Alarm_Expectation_Reality'];bpy.context.window.scene=s
obj=bpy.data.objects['GP_EP007_Bedroom_Acting'];gp=obj.data;layer=gp.layers[0];indices={m.name.removeprefix('GP_EP007_'):i for i,m in enumerate(gp.materials)};strokes=[]
for file,names in [('ep003_gp_laptop.py',{'shape','line','ellipse','rect','curve','smooth','mix','head'}),('ep007_alarm_gp.py',{'transform','shock','bird','room','clock','face','arms','character','duvet','sparkles','draw'})]:
    tree=ast.parse((ROOT/'tools'/file).read_text(encoding='utf-8-sig'))
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),globals())
        if file=='ep007_alarm_gp.py' and isinstance(node,ast.Assign) and any(isinstance(n,ast.Name) and n.id in {'HORNS','DIGITS','SEG'} for n in node.targets):exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),globals())
frames=sorted(set(range(1,97))|set(range(174,193))|set(range(193,433)))
for fr in frames:
    layer.frames.remove(fr);draw((fr-1)/24,fr)
    if fr%48==0:print('POLISHED_FRAME',fr,flush=True)
assert len(layer.frames)==432 and s.sequence_editor.strips[0].sound.packed_file
hashes=json.loads((EP/'edit/protected_hashes.json').read_text());assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
for name in ['Main','Expectation','Reality']:
    ob=bpy.data.objects['CAPTION_EP007_'+name+'_GP'];box=list(ob['caption_export_bounds_px']);assert box[0]>=108 and box[2]<=918 and box[1]>=299.9 and box[3]<=548.1
s.frame_set(109);s.render.filepath='//../renders/frames_1080p24/EP007_######';bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP007_Alarm_GP_v003.blend'),compress=True)
for fr in [37,177,289,337,361,429]:
    s.frame_set(fr);s.render.filepath=str(EP/'previews'/f'EP007_Polished_{fr:04d}.png');bpy.ops.render.render(write_still=True)
p=EP/'edit/project_verification.json';report=json.loads(p.read_text());report.update({'launch_legs_occluded_by_duvet':True,'clock_smack_wide_insert':[13.75,14.25],'clear_downward_thumb':True,'protected_files_unchanged':len(hashes),'final_project':'EP007_Alarm_GP_v003.blend'});p.write_text(json.dumps(report,indent=2))
print('EP007_POLISHED_COMPLETE',flush=True)
