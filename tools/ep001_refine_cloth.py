import bpy,math,struct,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test'); main=bpy.data.scenes['EP001_Material_Test']; cloth=bpy.data.objects['EP001_Cloth']; support=bpy.data.objects['EP001_ClothSupport']
def remove_hide_curve(obj):
    if obj.animation_data:
        for layer in obj.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in list(bag.fcurves):
                        if fc.data_path=='hide_viewport':bag.fcurves.remove(fc)
    obj.hide_viewport=False; obj.hide_set(False)
remove_hide_curve(cloth); remove_hide_curve(support)
for mod in list(cloth.modifiers):
    if mod.type in {'CLOTH','MESH_CACHE'}:cloth.modifiers.remove(mod)
solid=next(m for m in cloth.modifiers if m.type=='SOLIDIFY'); solid.show_viewport=False; solid.show_render=False
for v in cloth.data.vertices:v.co.x*=2.25/1.7; v.co.y*=2.25/1.7; v.co.z*=2
cloth.location.z=2.5; cloth.rotation_euler.x=.16
for m in list(support.modifiers):
    if m.type=='COLLISION':support.modifiers.remove(m)
support.modifiers.new('Fresh cloth support collision','COLLISION'); support.collision.thickness_outer=.025
sim=bpy.data.scenes.new('SIM_EP001_Cloth'); sim.render.fps=30; sim.frame_start=417; sim.frame_end=525
for o in [cloth,support,bpy.data.objects['PROP_TestPlatform_Pad'],bpy.data.objects['EP001_CollisionFloor']]:sim.collection.objects.link(o)
if bpy.context.window:bpy.context.window.scene=sim
cm=cloth.modifiers.new('Refined lightweight drape source','CLOTH'); cloth.modifiers.move(len(cloth.modifiers)-1,0); st=cm.settings; st.quality=6; st.mass=.3; st.tension_stiffness=18; st.compression_stiffness=18; st.shear_stiffness=12; st.bending_stiffness=.22; cm.collision_settings.use_collision=True; cm.collision_settings.use_self_collision=False; cm.collision_settings.distance_min=.025; cm.collision_settings.collision_quality=4; cm.point_cache.frame_end=525; cm.point_cache.frame_start=417
frames=[]; heights={}
for f in range(417,526):
    sim.frame_set(f); bpy.context.view_layer.update(); obj=cloth.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=obj.to_mesh(); coords=[tuple(v.co) for v in me.vertices]; world=[(obj.matrix_world@v.co).z for v in me.vertices]; obj.to_mesh_clear(); assert all(math.isfinite(a) for v in coords for a in v); frames.append(coords)
    if f in [450,470,497,525]:heights[f]=[min(world),max(world)]
assert heights[497][1]>1.2,('Drape missed support',heights)
dest=EP/'cache/cloth/EP001_Cloth_Drape_v002.mdd'
with dest.open('wb') as file:
    file.write(struct.pack('>2i',len(frames),625)); file.write(struct.pack('>'+str(len(frames))+'f',*[i/30 for i in range(len(frames))]))
    for coords in frames:file.write(struct.pack('>1875f',*[a for v in coords for a in v]))
cm.show_viewport=False; cm.show_render=False
mc=cloth.modifiers.new('Portable refined drape preview','MESH_CACHE'); mc.cache_format='MDD'; mc.filepath='//../cache/cloth/'+dest.name; mc.frame_start=417; mc.deform_mode='OVERWRITE'; mc.interpolation='LINEAR'; cloth.modifiers.move(len(cloth.modifiers)-1,1); solid.show_viewport=True; solid.show_render=True
for obj,start in [(cloth,417),(support,391)]:
    for f,v in [(1,True),(start,False),(536,True)]:obj.hide_viewport=v; obj.keyframe_insert(data_path='hide_viewport',frame=f)
if bpy.context.window:bpy.context.window.scene=main
bpy.data.scenes.remove(sim); main.frame_set(24); main['latest_episode_version']='EP001_v009.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP001_v009.blend'),compress=True)
(EP/'edit/cloth_refinement_report.json').write_text(json.dumps({'frames':heights,'vertices':625,'cache':'cache/cloth/'+dest.name},indent=2),encoding='utf-8'); print('REFINED_DRAPE_READY '+json.dumps(heights))
