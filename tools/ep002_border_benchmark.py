import bpy,time
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s;s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.02;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=False;s.cycles.device='GPU';s.cycles.max_bounces=8;s.cycles.transmission_bounces=8;s.render.resolution_percentage=100;s.render.use_persistent_data=True;s.cycles.use_auto_tile=True;s.cycles.tile_size=256
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='CUDA';p.get_devices()
for dev in p.devices:dev.use=dev.type=='CUDA'
s.frame_set(1590);s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.25;s.render.border_max_x=.75;s.render.border_min_y=.125;s.render.border_max_y=.375;s.render.filepath=str(EP/'previews/EP002_Native4K_CroppedTest_v021.png');t=time.monotonic();bpy.ops.render.render(write_still=True);print('BORDER_NATIVE4K_SECONDS',time.monotonic()-t,flush=True)
