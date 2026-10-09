import bpy,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test'); version=Path(bpy.data.filepath).stem.rsplit('_',1)[1]; out=EP/'previews'/('review_'+version); out.mkdir(exist_ok=True); s=bpy.data.scenes['EP001_Material_Test']; bpy.context.window.scene=s
s.render.resolution_percentage=50; s.eevee.taa_render_samples=64; s.render.image_settings.file_format='PNG'
shots=[('01_Establishing',24),('02_ButtonClick',63),('03_Slime',155),('04_Glass',321),('05_Cloth',470),('06_Water',599),('07_HoneyStretch',745),('08_Sand',934),('09_LavaClimax',1115),('10_FinalComedy',1265)]
for name,frame in shots:
    s.frame_set(frame); s.render.filepath=str(out/(name+'.png')); bpy.ops.render.render(write_still=True); print('REVIEW_STILL '+name,flush=True)
s.frame_set(24); s.render.resolution_percentage=25; s.eevee.taa_render_samples=32; s.render.filepath='//../renders/frames/EP001_'
(EP/'edit/review_shots.json').write_text(json.dumps(shots,indent=2),encoding='utf-8'); print('REVIEW_STILLS_READY')
