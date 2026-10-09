import bpy,time,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test'); version=Path(bpy.data.filepath).stem.rsplit('_',1)[1]; s=bpy.data.scenes['EP001_Material_Test']; bpy.context.window.scene=s
# A full-duration 7.5-fps preview sampled from the 30-fps production timeline.
# This is a review animatic, not final animation rendering.
s.render.resolution_percentage=30; s.eevee.taa_render_samples=16; s.eevee.shadow_ray_count=1
s.frame_step=4; s.render.fps=30; s.render.fps_base=4
s.render.image_settings.media_type='VIDEO'; s.render.ffmpeg.format='MPEG4'; s.render.ffmpeg.codec='H264'; s.render.ffmpeg.constant_rate_factor='MEDIUM'; s.render.ffmpeg.ffmpeg_preset='REALTIME'; s.render.ffmpeg.audio_codec='NONE'; s.render.filepath=str(EP/'previews'/('EP001_Review_'+version+'.mp4'))
def progress(scene,*args):
    if scene.frame_current%40==1:(EP/'edit/preview_render_progress.json').write_text(json.dumps({'frame':scene.frame_current,'end':1290,'percent':round(scene.frame_current/1290*100,1),'preview_only':True}),encoding='utf-8')
bpy.app.handlers.render_write.append(progress)
start=time.time()
try:bpy.ops.render.render(animation=True)
finally:
    bpy.app.handlers.render_write.remove(progress); s.frame_step=1; s.render.fps_base=1; s.render.image_settings.media_type='IMAGE'; s.render.image_settings.file_format='PNG'; s.render.resolution_percentage=25; s.eevee.taa_render_samples=32; s.eevee.shadow_ray_count=2; s.render.filepath='//../renders/frames/EP001_'; s.frame_set(24)
(EP/'edit/preview_render_report.json').write_text(json.dumps({'resolution':[324,576],'fps':7.5,'duration_seconds':43.07,'render_seconds':round(time.time()-start,1),'type':'silent full-story EEVEE review animatic','file':'previews/EP001_Review_'+version+'.mp4'},indent=2),encoding='utf-8'); print('REVIEW_ANIMATION_READY')
