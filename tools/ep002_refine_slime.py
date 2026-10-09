import bpy,struct,math,json,sys
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');main=bpy.data.scenes['EP002_Impossible_Blankets'];C=bpy.data.collections['EP002_CHARACTER'];o=bpy.data.objects['FX_EP002_Slime_Blanket'];r=bpy.data.objects['RIG_BRIX']
for layer in r.animation_data.action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fc in bag.fcurves:
                if 'rotation_euler' in fc.data_path and fc.array_index==0 and any(n in fc.data_path for n in ['upper_arm.','forearm.']):
                    for p in fc.keyframe_points:
                        if 92<=p.co.x<=360:
                            val=-.12 if p.co.x==282 and 'upper_arm.L' in fc.data_path else 0;p.co.y=val;p.handle_left.y=val;p.handle_right.y=val
version=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '012b'
span=max(v.co.y for v in o.data.vertices)-min(v.co.y for v in o.data.vertices)
for v in o.data.vertices:v.co.y*=2.12/span
o.location.y=-.78
for m in list(o.modifiers):
    if m.type!='SOFT_BODY':o.modifiers.remove(m)
mod=o.modifiers[0];mod.show_viewport=True;mod.show_render=True;st=mod.settings;st.pull=.24;st.push=.24;st.damping=20;st.bend=.06;st.use_stiff_quads=False;st.use_face_collision=False;st.use_edge_collision=False;st.step_min=10;st.step_max=60
sim=bpy.data.scenes.new('SIM_EP002_Slime_Refine');sim.render.fps=60;sim.frame_start=168;sim.frame_end=356;sim.collection.children.link(C);sim.collection.objects.link(o)
for n in ['PROP_TestBed_Mattress','PROP_TestBed_Pillow','PROP_TestBed_WalnutFrame','COLL_EP002_Floor']:sim.collection.objects.link(bpy.data.objects[n])
bpy.context.window.scene=sim;N=len(o.data.vertices);path=EP/'cache/softbody'/('EP002_Slime_Physical60_v'+version+'.mdd');samples={}
with path.open('wb') as file:
    file.write(struct.pack('>2i',189,N));file.write(struct.pack('>189f',*[i/60 for i in range(189)]))
    for f in range(168,357):
        sim.frame_set(f);bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[tuple(v.co) for v in me.vertices];coords=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();assert all(math.isfinite(a) for v in vs for a in v);file.write(struct.pack('>'+str(3*N)+'f',*[a for v in vs for a in v]))
        if (f-168)%30==0:print('SLIME_REFINEMENT',f,flush=True);samples[f]={'z':[min(v.z for v in coords),max(v.z for v in coords)],'y':[min(v.y for v in coords),max(v.y for v in coords)]}
mod.show_render=False;mod.show_viewport=False;mc=o.modifiers.new('Refined elastic dynamics playback','MESH_CACHE');mc.cache_format='MDD';mc.filepath='//../cache/softbody/'+path.name;mc.frame_start=168;mc.interpolation='LINEAR';sub=o.modifiers.new('Smooth gel skin','SUBSURF');sub.levels=1;sub.render_levels=2
bpy.context.window.scene=main;bpy.data.scenes.remove(sim);main.frame_set(48);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend'/('EP002_v'+version+'.blend')),compress=True);(EP/'edit'/('slime_refinement_report_v'+version+'.json')).write_text(json.dumps(samples,indent=2));print('REFINED_SLIME_COMPLETE')
