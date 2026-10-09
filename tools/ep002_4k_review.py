import bpy,time,json,sys
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s;s.render.image_settings.media_type='IMAGE';s.render.resolution_percentage=100;timings={}
for name,f in [('Opening',48),('Slime',238),('Glass_Impact',478),('Cloth',818),('Honey',1100),('Sand',1340),('Water',1570),('Lava',1950),('Outro',2216)]:
    if '--' in sys.argv and sys.argv[sys.argv.index('--')+1]=='solids' and name not in ['Opening','Slime','Cloth']:continue
    start=time.monotonic();s.frame_set(f);s.render.filepath=str(EP/'previews'/('EP002_4K60_'+name+'_v016.png'));bpy.ops.render.render(write_still=True);timings[name]=round(time.monotonic()-start,2);print('4K_REVIEW_FRAME',name,timings[name],flush=True)
    if name=='Opening':
        for warmf in [49,50]:
            start=time.monotonic();s.frame_set(warmf);s.render.filepath=str(EP/'previews'/('EP002_4K60_WarmBenchmark_'+str(warmf)+'.png'));bpy.ops.render.render(write_still=True);timings['Warm_'+str(warmf)]=round(time.monotonic()-start,2);print('4K_WARM_BENCHMARK',warmf,timings['Warm_'+str(warmf)],flush=True)
(EP/'edit/4k_render_benchmark.json').write_text(json.dumps(timings,indent=2));print('4K_REVIEW_COMPLETE')
