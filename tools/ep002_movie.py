import bpy
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets')
s=bpy.data.scenes['EP002_Impossible_Blankets']; bpy.context.window.scene=s
s.render.resolution_percentage=30; s.eevee.taa_render_samples=16; s.render.fps=30; s.render.fps_base=4; s.frame_step=4
s.render.image_settings.media_type='VIDEO'; s.render.ffmpeg.format='MPEG4'; s.render.ffmpeg.codec='H264'; s.render.ffmpeg.constant_rate_factor='MEDIUM'; s.render.ffmpeg.ffmpeg_preset='GOOD'; s.render.filepath=str(EP/'previews/EP002_Review_v009.mp4')
bpy.ops.render.render(animation=True)
s.render.fps_base=1; s.frame_step=1; s.render.image_settings.media_type='IMAGE'; s.render.image_settings.file_format='PNG'; s.render.resolution_percentage=35; s.eevee.taa_render_samples=64; s.frame_set(24); s.render.filepath='//../previews/EP002_'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v009.blend'),compress=True)
print('FULL_REVIEW_MOVIE_COMPLETE')
