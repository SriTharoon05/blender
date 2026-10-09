import bpy,time,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s;s.render.resolution_percentage=100;s.eevee.taa_render_samples=64;s.eevee.shadow_ray_count=2;s.eevee.fast_gi_ray_count=1;s.eevee.ray_tracing_options.resolution_scale='4';timings={}
for f in [48,49,50]:
    s.frame_set(f);s.render.filepath=str(EP/'previews'/('EP002_4K60_RenderBenchmark64_'+str(f)+'.png'));start=time.monotonic();bpy.ops.render.render(write_still=True);timings[f]=time.monotonic()-start;print('NATIVE4K_BENCHMARK64',f,timings[f],flush=True)
(EP/'edit/4k_benchmark64.json').write_text(json.dumps(timings,indent=2));print('NATIVE4K_BENCHMARK64_COMPLETE')
