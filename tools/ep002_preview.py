import bpy,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets')
s=bpy.data.scenes['EP002_Impossible_Blankets']; bpy.context.window.scene=s
s.render.engine='BLENDER_EEVEE'; s.render.resolution_percentage=35; s.eevee.taa_render_samples=24
s.render.image_settings.media_type='IMAGE'; s.render.image_settings.file_format='PNG'
for name,f in [('Opening',24),('Slime',118),('Glass',260),('Cloth',409),('Honey',550),('Sand',678),('Water',790),('Lava',986),('Final',1050)]:
    s.frame_set(f); s.render.filepath=str(EP/'previews'/('EP002_'+name+'_v001.png')); bpy.ops.render.render(write_still=True)
s.frame_set(24); s.render.resolution_percentage=35; s.eevee.taa_render_samples=32
s.render.filepath='//../previews/EP002_'; bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v007.blend'),compress=True)
print('REPRESENTATIVE_PREVIEWS_COMPLETE')
