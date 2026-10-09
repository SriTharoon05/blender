import bpy,time,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets')
state=EP/'edit/render_request_state.json'
if state.exists() and not json.loads(state.read_text()).get('allow_render',False):
    raise RuntimeError('Rendering is deferred by the user. Obtain a new user instruction to render before changing render_request_state.json.')
s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s;s.render.resolution_percentage=100;s.render.fps=60;s.render.fps_base=1;s.frame_step=1;s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';folder=EP/'renders/frames';folder.mkdir(parents=True,exist_ok=True);start=time.monotonic();done=0
for f in range(1,2251):
    p=folder/('EP002_4K60_'+str(f).zfill(6)+'.png')
    if p.exists() and p.stat().st_size>10000:continue
    s.frame_set(f);s.render.filepath=str(p);bpy.ops.render.render(write_still=True);done+=1
    if f%10==0 or f==1:
        report={'phase':'final_render','completed_frame':f,'total_frames':2250,'resolution':[2160,3840],'fps':60,'new_frames_this_run':done,'elapsed_seconds':round(time.monotonic()-start,1)};(EP/'edit/final_render_progress.json').write_text(json.dumps(report,indent=2));print('FINAL_PROGRESS',json.dumps(report),flush=True)
s.frame_set(48);s.render.filepath='//../renders/frames/EP002_4K60_';bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_Rendered_4K60.blend'),compress=True);print('ALL_NATIVE_4K60_FRAMES_COMPLETE',flush=True)
