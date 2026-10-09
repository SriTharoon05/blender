import bpy
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets')
s=bpy.data.scenes['EP002_Impossible_Blankets']; bpy.context.window.scene=s
lava=bpy.data.objects['FX_EP002_Lava_Blanket']; lava.location.y=-.85
if lava.animation_data:
    for layer in lava.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if fc.data_path=='location' and fc.array_index==2:
                        for p in fc.keyframe_points:
                            p.co.y-=.18; p.handle_left.y-=.18; p.handle_right.y-=.18
shield=bpy.data.objects['PROP_EP002_SafetyShield']; shield.location.y=-.85; shield.location.z=2.05; shield.scale.y=.9
bpy.data.objects['LIGHT_EP002_LavaGlow'].location=(0,-.85,2.2)
s.render.resolution_percentage=35; s.eevee.taa_render_samples=64
s.render.image_settings.media_type='IMAGE'; s.render.image_settings.file_format='PNG'
for name,f in [('Opening',24),('Slime',118),('Glass',260),('Cloth',409),('Honey',550),('Sand',678),('Water',790),('Lava',986),('Final',1050),('Outro',1108)]:
    s.frame_set(f); s.render.filepath=str(EP/'previews'/('EP002_'+name+'_v002.png')); bpy.ops.render.render(write_still=True)
s.frame_set(24); s.render.filepath='//../previews/EP002_'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v008.blend'),compress=True)
print('POLISHED_STILLS_SAVED')
