import bpy,json,hashlib
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test'); ROOT=EP.parent.parent; s=bpy.data.scenes['EP001_Material_Test']; bpy.context.window.scene=s
r=bpy.data.objects['RIG_BRIX']; exprs=['NEUTRAL','CONFIDENT','CURIOUS','SUSPICIOUS','SURPRISED','SCARED','DISGUSTED','IMPRESSED','RELIEVED','EXCITED']
for f in [1250,1290]:
    for e in exprs:
        r[e]=.55 if e=='DISGUSTED' else .45 if e=='SUSPICIOUS' else 0.; r.keyframe_insert(data_path='["'+e+'"]',frame=f)
    r['squint']=.18; r.keyframe_insert(data_path='["squint"]',frame=f)
    r['look_x']=0.; r['look_y']=0.; r.keyframe_insert(data_path='["look_x"]',frame=f); r.keyframe_insert(data_path='["look_y"]',frame=f)
    b=r.pose.bones['head']; b.rotation_euler=(.025,.51,0); b.keyframe_insert(data_path='rotation_euler',frame=f)
for name,frame in [('BRIX_REACTION_GLASS',325),('BRIX_REACTION_CLOTH',495),('BRIX_REACTION_WATER',625),('BRIX_REACTION_HONEY',800),('BRIX_REACTION_SAND',926),('BRIX_REACTION_LAVA',1060)]:s.timeline_markers.new(name,frame=frame)
# Keep all generated audio/score absent; named markers provide editorial hooks.
s['review_status']='PREVIEW ONLY / awaiting user review / silent timing preview'
s['latest_episode_version']='EP001_v008.blend'; s['review_notes']='32 division water/honey; guided actual soft-body result; 14 glass rigid-body shards; cloth drape; stylized granular sand and viscous lava proxies. No high resolution bake or final rendering.'
s.frame_set(24); s.render.fps=30; s.render.fps_base=1; s.frame_step=1; s.render.resolution_percentage=25; s.eevee.taa_render_samples=32; s.render.image_settings.file_format='PNG'; s.render.filepath='//../renders/frames/EP001_'; bpy.ops.file.make_paths_relative()
hashes=json.loads((EP/'edit/master_hashes.json').read_text()); assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP001_v008.blend'),compress=True)
print('EPISODE_READY_FOR_REVIEW_RENDER / master hashes unchanged')
