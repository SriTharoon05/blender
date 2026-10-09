import bpy, json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test')
sim=bpy.data.scenes['SIM_EP001_Honey']; bpy.context.window.scene=sim
o=bpy.data.objects['EP001_Honey_Domain']; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o; sim.frame_set(sim.frame_start)
mod=next(m for m in o.modifiers if m.type=='FLUID'); d=mod.domain_settings
print('BAKING_HONEY_32_DIVISIONS '+d.cache_directory)
bpy.ops.fluid.bake_all()
result={'name':'HONEY','resolution':d.resolution_max,'frames':[d.cache_frame_start,d.cache_frame_end],'viscosity':d.viscosity_value,'time_scale':d.time_scale,'data_baked':d.has_cache_baked_data,'mesh_baked':d.has_cache_baked_mesh,'cache':d.cache_directory}
assert d.has_cache_baked_mesh,result
bpy.context.window.scene=bpy.data.scenes['EP001_Material_Test']; bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP001_v005.blend'),compress=True)
(EP/'edit/honey_bake_report.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result))
