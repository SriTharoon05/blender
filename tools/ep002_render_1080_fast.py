import bpy,time,json,sys,struct
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');args=sys.argv[sys.argv.index('--')+1:];first,last=map(int,args[:2]);s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s
state=json.loads((EP/'edit/render_request_state.json').read_text());assert state['allow_render']
assert s.render.engine=='BLENDER_EEVEE' and (s.render.resolution_x,s.render.resolution_y,s.render.fps)==(1080,1920,60)
s.render.resolution_percentage=100;s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';folder=EP/'renders/frames_1080p60';folder.mkdir(parents=True,exist_ok=True);t=time.monotonic();new=0
for f in range(first,last+1):
 p=folder/('EP002_1080p60_'+str(f).zfill(6)+'.png');valid=False
 if p.exists() and p.stat().st_size>10000:
  with p.open('rb') as h:head=h.read(24)
  valid=head[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>2I',head[16:24])==(1080,1920)
 if not valid:break
else:
 print('FAST_RENDER_SEGMENT_COMPLETE',first,last,flush=True);sys.exit(0)
resume=f;s.frame_start=resume;s.frame_end=last;s.frame_step=1;s.render.filepath=str(folder/'EP002_1080p60_######')
def progress_handler(scene,*args):
 global new
 f=scene.frame_current;new+=1
 if f%10==0 or f==resume:
  progress={'phase':'Eevee GPU render','completed_frame':f,'total_frames':2250,'segment':[first,last],'resolution':[1080,1920],'fps':60,'samples':s.eevee.taa_render_samples,'elapsed_seconds':round(time.monotonic()-t,1),'frames_this_run':new};(EP/'edit/render_1080p60_progress.json').write_text(json.dumps(progress,indent=2));print('RENDER_PROGRESS',json.dumps(progress),flush=True)
bpy.app.handlers.render_write.append(progress_handler)
# A single animation render keeps Eevee's GPU resources alive across frames.
bpy.ops.render.render(animation=True)
bpy.app.handlers.render_write.remove(progress_handler)
print('FAST_RENDER_SEGMENT_COMPLETE',first,last,flush=True)
