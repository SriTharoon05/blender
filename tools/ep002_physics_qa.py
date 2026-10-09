import bpy,sys
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s;s.render.resolution_percentage=18;s.eevee.taa_render_samples=32;s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG'
for name,f in [('Slime_Physics',240),('Glass_Physics',520),('Cloth_Impact',710),('Cloth_Physics',820)]:
    s.frame_set(f);s.render.filepath=str(EP/'previews'/('EP002_'+name+'_QA.png'));bpy.ops.render.render(write_still=True)
