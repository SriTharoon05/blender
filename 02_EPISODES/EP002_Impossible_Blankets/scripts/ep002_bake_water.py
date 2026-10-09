import bpy,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets'); sim=bpy.data.scenes['SIM_EP002_Water']; bpy.context.window.scene=sim; o=bpy.data.objects['FX_EP002_Water_Domain']; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o; o.hide_viewport=False; sim.frame_set(744)
d=next(m for m in o.modifiers if m.type=='FLUID').domain_settings
bpy.ops.fluid.bake_all()
files=list((Path(bpy.path.abspath(d.cache_directory))/'mesh').glob('*.bobj.gz')); biggest=max(p.stat().st_size for p in files); assert biggest>500,'Liquid cache empty'
report={'resolution':32,'frames':[744,850],'mesh_frames':len(files),'largest_mesh_bytes':biggest,'cache':d.cache_directory,'baked':d.has_cache_baked_mesh}
bpy.context.window.scene=bpy.data.scenes['EP002_Impossible_Blankets']; bpy.context.scene.frame_set(24); bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v006.blend'),compress=True)
(EP/'edit/water_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print('SMALL_WATER_CACHE_READY '+json.dumps(report))
