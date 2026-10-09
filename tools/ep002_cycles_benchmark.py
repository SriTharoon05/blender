import bpy,time,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s;s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.025;s.cycles.use_denoising=True;s.cycles.device='GPU';s.cycles.max_bounces=8;s.cycles.transmission_bounces=8;s.cycles.transparent_max_bounces=8;s.render.resolution_percentage=100;s.render.use_persistent_data=True
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='CUDA';p.get_devices()
for dev in p.devices:dev.use=dev.type=='CUDA'
s.cycles.use_auto_tile=True;s.cycles.tile_size=512;s.cycles.denoising_use_gpu=False;s.render.use_persistent_data=False
results=[]
for name,f in [('Water',1590),('Honey',1100),('Slime',288)]:
 s.frame_set(f);s.render.filepath=str(EP/'previews'/('EP002_4K_Cycles_'+name+'_v021.png'));t=time.monotonic();bpy.ops.render.render(write_still=True);results.append({'name':name,'seconds':time.monotonic()-t});print('BENCHMARK',results[-1],flush=True)
(EP/'edit/cycles4k_benchmark.json').write_text(json.dumps(results,indent=2))
