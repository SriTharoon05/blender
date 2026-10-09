import bpy, json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test')
reports=[]
for name,start,end in [('Water',566,675),('Honey',716,825)]:
    sim=bpy.data.scenes['SIM_EP001_'+name]; bpy.context.window.scene=sim
    o=bpy.data.objects['EP001_'+name+'_Domain']; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    d=next(m for m in o.modifiers if m.type=='FLUID').domain_settings
    if d.has_cache_baked_any:bpy.ops.fluid.free_all()
    # Set the end first: Blender clamps the start to the previous end otherwise.
    d.cache_frame_end=end; d.cache_frame_start=start
    if o.animation_data:
        action=o.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for f in list(bag.fcurves):
                        if f.data_path=='hide_viewport':bag.fcurves.remove(f)
    o.hide_viewport=False; o.display_type='WIRE'; o.update_tag()
    sim.frame_set(start); bpy.context.view_layer.update()
    bpy.ops.fluid.bake_all()
    meshdir=Path(bpy.path.abspath(d.cache_directory))/'mesh'; files=list(meshdir.glob('*.bobj.gz')); maxsize=max([p.stat().st_size for p in files],default=0)
    result={'test':name,'resolution':d.resolution_max,'frames':[start,end],'mesh_frames':len(files),'largest_mesh_bytes':maxsize,'data_baked':d.has_cache_baked_data,'mesh_baked':d.has_cache_baked_mesh}
    reports.append(result); print(json.dumps(result)); assert maxsize>200,'Fluid cache has empty meshes: '+name
bpy.context.window.scene=bpy.data.scenes['EP001_Material_Test']; bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP001_v005.blend'),compress=True)
(EP/'edit/fluid_bake_report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print('VERIFIED_FLUID_CACHES_READY')
