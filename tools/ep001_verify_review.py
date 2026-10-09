import bpy,json,hashlib,math
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test'); ROOT=EP.parent.parent; s=bpy.data.scenes['EP001_Material_Test']
if bpy.context.window:bpy.context.window.scene=s
report={'file':bpy.data.filepath,'master_files_unchanged':False,'frames':{},'invalid_drivers':[],'cache_paths':[]}
assert [s.render.resolution_x,s.render.resolution_y,s.render.fps,s.frame_end]==[1080,1920,30,1290]
hashes=json.loads((EP/'edit/master_hashes.json').read_text()); report['master_files_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items()); assert report['master_files_unchanged']
for frame,name in [(155,'EP001_Slime'),(321,'EP001_GlassShard_01'),(470,'EP001_Cloth'),(599,'EP001_Water_Domain'),(745,'EP001_Honey_Domain'),(934,'EP001_Sand_GranularProxy'),(1115,'EP001_Lava_ViscousProxy')]:
    s.frame_set(frame); bpy.context.view_layer.update(); o=bpy.data.objects[name]; assert not o.hide_render,(name,frame,'hidden'); e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=e.to_mesh(); coords=[e.matrix_world@v.co for v in me.vertices]; e.to_mesh_clear(); assert coords and all(math.isfinite(x) for co in coords for x in co),(name,'nonfinite'); report['frames'][name]={'frame':frame,'vertices':len(coords),'world_z':[min(v.z for v in coords),max(v.z for v in coords)]}
    if 'Domain' in name:assert len(coords)>8,(name,'Liquid mesh absent')
for db in list(bpy.data.objects)+list(bpy.data.shape_keys):
    if db.animation_data:
        for f in db.animation_data.drivers:
            if not f.is_valid:report['invalid_drivers'].append(db.name+':'+f.data_path)
assert not report['invalid_drivers'],report['invalid_drivers']
for o in s.objects:
    for m in o.modifiers:
        if m.type=='MESH_CACHE':
            p=Path(bpy.path.abspath(m.filepath)); assert p.is_file(),p; report['cache_paths'].append(m.filepath)
        if m.type=='FLUID' and m.fluid_type=='DOMAIN':
            d=m.domain_settings; assert d.resolution_max==32; assert Path(bpy.path.abspath(d.cache_directory)).is_dir(); report['cache_paths'].append(d.cache_directory)
for marker in ['BUTTON_CLICK','MACHINE_MOVE','SLIME_SQUISH','GLASS_CRACK','CLOTH_FLAP','WATER_SPLASH','HONEY_STRETCH','SAND_POUR','LAVA_SIZZLE','BRIX_REACTION','FINAL_COMEDY_BEAT']:assert marker in s.timeline_markers,marker
(EP/'edit/review_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print('REVIEW_VERIFIED '+json.dumps(report))
