import bpy,bmesh,struct,json,math
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];C=bpy.data.collections['EP002_CHARACTER'];o=bpy.data.objects['FX_EP002_Slime_Blanket'];bm=bmesh.new();bm.from_mesh(o.data);target=abs(bm.calc_volume());bm.free()
for m in list(o.modifiers):o.modifiers.remove(m)
mod=o.modifiers.new('Incompressible viscoelastic volume','CLOTH');st=mod.settings;st.quality=18;st.mass=.35;st.tension_stiffness=8;st.compression_stiffness=8;st.shear_stiffness=4;st.bending_stiffness=.06;st.tension_damping=25;st.compression_damping=25;st.shear_damping=25;st.air_damping=2;st.use_pressure=True;st.use_pressure_volume=True;st.target_volume=target;st.uniform_pressure_force=0;st.pressure_factor=500;mod.collision_settings.use_self_collision=True;mod.collision_settings.self_distance_min=.012;mod.collision_settings.distance_min=.018;mod.collision_settings.collision_quality=6;mod.point_cache.frame_end=356;mod.point_cache.frame_start=168
sim=bpy.data.scenes.new('SIM_EP002_VolumeSlime');sim.render.fps=60;sim.frame_start=168;sim.frame_end=356;sim.collection.children.link(C);sim.collection.objects.link(o)
for n in ['PROP_TestBed_Mattress','PROP_TestBed_Pillow','PROP_TestBed_WalnutFrame','COLL_EP002_Floor']:sim.collection.objects.link(bpy.data.objects[n])
bpy.context.window.scene=sim;N=len(o.data.vertices);path=EP/'cache/softbody/EP002_Slime_Volume60_v020.mdd';samples={}
with path.open('wb') as file:
    file.write(struct.pack('>2i',189,N));file.write(struct.pack('>189f',*[i/60 for i in range(189)]))
    for f in range(168,357):
        sim.frame_set(f);bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[tuple(v.co) for v in me.vertices];assert len(vs)==N;assert all(math.isfinite(a) and abs(a)<20 for v in vs for a in v);file.write(struct.pack('>'+str(3*N)+'f',*[a for v in vs for a in v]))
        if (f-168)%30==0:
            bm=bmesh.new();bm.from_mesh(me);volume=abs(bm.calc_volume());bm.free();samples[f]={'volume':volume,'ratio':volume/target,'z':[min((e.matrix_world@v.co).z for v in me.vertices),max((e.matrix_world@v.co).z for v in me.vertices)]};print('GEL_VOLUME_PROGRESS',f,volume/target,flush=True)
        e.to_mesh_clear()
mod.show_viewport=False;mod.show_render=False;mc=o.modifiers.new('Conserved-volume gel playback','MESH_CACHE');mc.cache_format='MDD';mc.filepath='//../cache/softbody/'+path.name;mc.frame_start=168;mc.interpolation='LINEAR';sub=o.modifiers.new('Smooth gel surface','SUBSURF');sub.levels=1;sub.render_levels=2
air=bpy.data.objects['FX_EP002_Slime_AdvectedAirPockets'];am=next(m for m in air.modifiers if m.type=='MESH_CACHE');am.filepath=mc.filepath;am.frame_start=168
bpy.context.window.scene=s;bpy.data.scenes.remove(sim);s.frame_set(48);o['method']='Pressure-constrained damped elastic closed volume; actual collision solver; volume target '+str(target);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v020.blend'),compress=True);(EP/'edit/slime_volume_report_v020.json').write_text(json.dumps(samples,indent=2));print('CONSERVATIVE_GEL_SOLVER_COMPLETE')
