import bpy,json,time
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s
for name in ['HONEY','WATER','LAVA']:
 sim=bpy.data.scenes['SIM_EP002_Physical_'+name];o=bpy.data.objects['FX_EP002_'+name.title()+'_Domain'];d=next(m for m in o.modifiers if m.type=='FLUID').domain_settings
 print('SIM_SETTINGS',name,sim.render.fps,sim.render.fps_base,list(sim.gravity),d.time_scale,'DOMAINMATS',[m.name for m in o.data.materials],flush=True)
 if name=='LAVA':
  for x in sim.objects:
   for m in x.modifiers:
    if m.type=='FLUID' and m.fluid_type=='FLOW':print('FLOW',x.name,m.flow_settings.use_initial_velocity,list(m.flow_settings.velocity_coord),flush=True)
s.render.resolution_percentage=25;s.render.image_settings.color_depth='8';s.eevee.taa_render_samples=64;s.frame_set(1590)
m=bpy.data.materials['MAT_EP002_Physical_WATER'];out=m.node_tree.nodes.get('Material Output')
for l in list(m.node_tree.links):
 if l.to_node==out and l.to_socket.name=='Volume':m.node_tree.links.remove(l)
out.inputs['Thickness'].default_value=0
s.render.filepath=str(EP/'previews/EP002_Water_NoVolume_v021.png');bpy.ops.render.render(write_still=True)
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices();print('DEVICES',[(x.name,x.type) for x in prefs.devices],flush=True)
for dev in prefs.devices:dev.use=dev.type=='CUDA'
s.cycles.device='GPU';s.render.filepath=str(EP/'previews/EP002_Water_Cycles_v021.png');t=time.monotonic();bpy.ops.render.render(write_still=True);print('CYCLES_TIME',time.monotonic()-t,flush=True)
