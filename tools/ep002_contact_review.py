import bpy,json,sys,time
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s;s.render.resolution_percentage=25;s.eevee.taa_render_samples=32;s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.image_settings.color_depth='8';frames=[('Slime_Impact',208),('Slime_Settle',288),('Glass_Impact',478),('Glass_Settle',550),('Cloth_Settle',818),('Honey_Impact',1020),('Honey_Settle',1100),('Sand_Impact',1290),('Sand_Settle',1360),('Water_Impact',1520),('Water_Settle',1590),('Lava_Impact',1910),('Lava_Settle',1980),('Final',2140)]
for name,f in frames:
    s.frame_set(f);s.render.filepath=str(EP/'previews'/('EP002_Contact_'+name+'_v020.png'));bpy.ops.render.render(write_still=True);print('CONTACT_REVIEW',name,f,flush=True)
print('ALL_CONTACT_REVIEW_STILLS_COMPLETE')
