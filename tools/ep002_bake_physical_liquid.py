import bpy,json,sys
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');name=sys.argv[sys.argv.index('--')+1];version={'HONEY':'013','WATER':'014','LAVA':'015'}[name];sim=bpy.data.scenes['SIM_EP002_Physical_'+name];bpy.context.window.scene=sim;o=bpy.data.objects['FX_EP002_'+name.title()+'_Domain'];o.hide_viewport=False;o.hide_set(False);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;sim.frame_set(sim.frame_start)
d=next(m for m in o.modifiers if m.type=='FLUID').domain_settings;d.use_speed_vectors=True
sim.frame_end=d.cache_frame_end;sim.frame_start=d.cache_frame_start;sim.frame_set(sim.frame_start)
d.viscosity_value={'HONEY':.007,'WATER':.000001,'LAVA':.04}[name];d.cache_directory='//../cache/fluid/physical_'+name.lower()+'_60fps_v013'
if name in ['WATER','LAVA']:d.use_diffusion=True;d.viscosity_base=1;d.viscosity_exponent=6
if name=='HONEY':
    for obj in bpy.data.objects:
        if obj.name=='COLL_EP002_Floor' or (obj.name.startswith('COLL_EP002_') and obj.name.endswith('COLL_EP002_Floor')):obj.location.z+=.025
if name=='LAVA' and 'PROP_EP002_SafetyShield' not in sim.objects:sim.collection.objects.link(bpy.data.objects['PROP_EP002_SafetyShield'])
if hasattr(d,'surface_tension'):d.surface_tension=.072 if name=='WATER' else (.08 if name=='HONEY' else .35)
print('LIQUID_BEGIN',name,d.resolution_max,d.cache_frame_start,d.cache_frame_end,'viscosity',d.viscosity_value,flush=True);bpy.ops.fluid.bake_all();meshes=list((Path(bpy.path.abspath(d.cache_directory))/'mesh').glob('*.bobj.gz'));assert len(meshes)==sim.frame_end-sim.frame_start+1;(EP/'edit'/('physical_'+name.lower()+'_report.json')).write_text(json.dumps({'material':name,'fps':60,'resolution':d.resolution_max,'mesh_scale':d.mesh_scale,'viscosity_enabled':d.use_viscosity,'viscosity':d.viscosity_value,'mesh_frames':len(meshes),'largest_mesh_bytes':max(p.stat().st_size for p in meshes),'cache':d.cache_directory},indent=2));bpy.context.window.scene=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.scene.frame_set(48);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend'/('EP002_v'+version+'.blend')),compress=True);print('PHYSICAL_LIQUID_COMPLETE',name,flush=True)
