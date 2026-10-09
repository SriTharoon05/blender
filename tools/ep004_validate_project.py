import bpy,json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP004_Dad_Mechanical_Keyboard';s=bpy.data.scenes['EP004_Dad_Mechanical_Keyboard'];bpy.context.window.scene=s
obj=bpy.data.objects['GP_EP004_Dad_Office_Keyboard'];assert obj.type=='GREASEPENCIL' and len(obj.data.layers[0].frames)==240
for f in obj.data.layers[0].frames:
    t=(f.frame_number-1)/24
    if t>=1.6:break
    u=max(0,min(1,(t-.9)/.7));u=u*u*(3-2*u)
    for st in f.drawing.strokes:
        if not st.cyclic or len(st.points)!=5:continue
        pts=[p.position for p in st.points];w=max(p.x for p in pts)-min(p.x for p in pts);h=max(p.y for p in pts)-min(p.y for p in pts)
        if abs(w-.23)<.001 and abs(h-.67)<.001 and min(p.x for p in pts)>.15 and max(p.x for p in pts)<.5:
            top=max(p.y for p in pts)
            for p in st.points:
                if p.position.y<top-.3:p.position=(p.position.x,p.position.y+.49*(1-u),p.position.z)
    f.drawing.tag_positions_changed()
assert (s.render.resolution_x,s.render.resolution_y,s.render.fps,s.frame_end,s.render.engine)==(1080,1920,24,240,'BLENDER_EEVEE')
assert s.sequence_editor.strips[0].sound.packed_file
bounds={}
for name,exact in [('CAPTION_EP004_Main_GP','POV: Your dad uses your mechanical keyboard.'),('CAPTION_EP004_Tag_GP','...every. single. time.')]:
    ob=bpy.data.objects[name];assert ob['exact_text']==exact;points=[p.position for st in ob.data.layers['White letters'].frames[0].drawing.strokes for p in st.points]
    lo=[min(p[k] for p in points) for k in [0,1]];hi=[max(p[k] for p in points) for k in [0,1]]
    assert lo[0]>-4 and hi[0]<4 and lo[1]-.055>4.8 and hi[1]+.055<8
    bounds[name]={'minimum_xy':lo,'maximum_xy':hi,'inside_top_20_percent':True}
hashes=json.loads((EP/'edit/protected_hashes.json').read_text());assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
s.frame_set(24);s.render.filepath='//../renders/frames_1080p24/EP004_######'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP004_Dad_Keyboard_GP_v004.blend'),compress=True)
(EP/'edit/project_verification.json').write_text(json.dumps({'frames':240,'fps':24,'resolution':[1080,1920],'duration_seconds':10,'native_grease_pencil':True,'audio_packed':True,'captions':bounds,'protected_blend_files_unchanged':len(hashes)},indent=2));print('EP004_PROJECT_VALIDATED',flush=True)
