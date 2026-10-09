"""Version the 2D master with the screenshot-calibrated caption placement."""
import bpy,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT/'tools'))
from shorts_caption_safe_area import place_caption,policy
s=bpy.context.scene
old=ROOT/'01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v003.blend'
before=hashlib.sha256(old.read_bytes()).hexdigest()
out=ROOT/'01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v004.blend';assert not out.exists()
report={}
for ob in s.objects:
    if ob.type=='GREASEPENCIL' and ob.name.startswith('CAPTION_'):
        report[ob.name]=place_caption(ob)
        ob['style']='Arial Black, white, thick black outline; export y=480–680, below Shorts/Reels headers.'
        ob['exact_text']=ob.get('exact_text','YOUR CAPTION GOES HERE')
    elif ob.type=='GREASEPENCIL':
        # Keep the approved native geometry, moving it as one intact asset.
        points=[ob.matrix_world@p.position for la in ob.data.layers for fr in la.frames for st in fr.drawing.strokes for p in st.points]
        if points:
            top=max(p.y for p in points);ceiling=16/1920*(960-820)
            if top>ceiling:ob.location.y-=top-ceiling
            ob['caption_clearance']='Head and face kept below source y=820px; retain this in episode zooms.'
s['caption_defaults']='Upper band y=480–748px, main y=480–680px, tag y=700–748px; x=108–918px. All text top, never bottom. Screenshot calibrated.'
s['caption_policy']='00_LIBRARY/Caption_Layouts/Shorts_Reels_Upper_Safe_Area_v001.json'
s['future_2d_defaults']='1080x1920, 24fps, fast Eevee NVIDIA GTX1650Ti; approved recurring character.'
s.frame_set(1);s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=24
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
assert hashlib.sha256(old.read_bytes()).hexdigest()==before
folder=ROOT/'01_TEMPLATES/Previews';folder.mkdir(exist_ok=True)
s.render.filepath=str(folder/'GreasePencil_Master_v004_Upper_Caption_Preview.png');bpy.ops.render.render(write_still=True)
(ROOT/'00_LIBRARY/Caption_Layouts/Template_Placement_Verification_v001.json').write_text(json.dumps({'bounds_px':report,'previous_master_unchanged':True,'template':str(out),'policy':policy()},indent=2))
print('UPPER_CAPTION_TEMPLATE_VERIFIED',report,flush=True)
