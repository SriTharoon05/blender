import bpy,json,hashlib,ast,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP005_Lost_Mom_Checkout'
s=bpy.data.scenes['EP005_Lost_Mom_Checkout'];bpy.context.window.scene=s
assert (s.render.resolution_x,s.render.resolution_y,s.render.fps,s.frame_end)==(1080,1920,24,528)
assert s.render.engine=='BLENDER_EEVEE'
ob=bpy.data.objects['GP_EP005_Checkout_Drawings'];assert ob.type=='GREASEPENCIL' and len(ob.data.layers[0].frames)==528
gp=ob.data;layer=gp.layers[0];indices={m.name.removeprefix('GP_EP005_'):i for i,m in enumerate(gp.materials)};strokes=[]
for file,names in [('ep003_gp_laptop.py',{'shape','line','ellipse','rect','curve','smooth','mix','head'}),('ep005_checkout_gp.py',{'transform','sign_text','gumball','backdrop','kid','draw'})]:
    tree=ast.parse((ROOT/'tools'/file).read_text(encoding='utf-8-sig'))
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),globals())
GLYPHS={'L':[(0,1),(0,0),(.6,0)],'A':[(0,0),(.3,1),(.6,0),(.45,.5),(.15,.5)],'N':[(0,0),(0,1),(.6,0),(.6,1)],'E':[(.6,1),(0,1),(0,0),(.6,0),(0,0),(0,.5),(.5,.5)],'4':[(.5,0),(.5,1),(0,.35),(.7,.35)]}
for fr in list(range(185,197))+list(range(241,385))+list(range(481,529)):
    layer.frames.remove(fr);draw((fr-1)/24,fr)
    if fr%48==0:print('POLISHED_FRAME',fr,flush=True)
tag=bpy.data.objects['CAPTION_EP005_Tag_GP']
for la in tag.data.layers:
    drawing=la.frames[0].drawing
    for st in drawing.strokes:
        for p in st.points:p.position.x*=1.2;p.position.y=-6.35+(p.position.y+6.35)*1.2;p.radius*=1.1
    drawing.tag_positions_changed()
assert s.sequence_editor.strips[0].sound.packed_file
caption=bpy.data.objects['CAPTION_EP005_Main_GP'];assert caption['exact_text']=='When you lose your mom in the grocery store checkout line'
pts=[p.position for st in caption.data.layers['White letters'].frames[0].drawing.strokes for p in st.points]
bounds=[min(p.x for p in pts),max(p.x for p in pts),min(p.y for p in pts),max(p.y for p in pts)]
assert bounds[0]>-4.1 and bounds[1]<4.1 and bounds[2]>3.2 and bounds[3]<7.7,bounds
assert bpy.data.objects['CAPTION_EP005_Tag_GP']['exact_text']=='MISSION: FIND MOM — INITIATED.'
hashes=json.loads((EP/'edit/protected_hashes.json').read_text());assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
s.frame_set(49);s.render.filepath='//../renders/frames_1080p24/EP005_######'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP005_Checkout_GP_v003.blend'),compress=True)
(EP/'edit/project_verification.json').write_text(json.dumps({'native_GP':True,'drawings':528,'packed_audio':True,'caption_bounds_world':bounds,'top30_verified':True,'protected_files':len(hashes)},indent=2))
print('EP005_PROJECT_VERIFIED',bounds,flush=True)
for fr in [185,289,505]:
    s.frame_set(fr);s.render.filepath=str(EP/'previews'/f'EP005_Polished_{fr:04d}.png');bpy.ops.render.render(write_still=True)
