import bpy,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets'); ROOT=EP.parent.parent
s=bpy.data.scenes['EP002_Impossible_Blankets']; bpy.context.window.scene=s
assert s.frame_end==1125 and s.render.fps==30 and s.render.fps_base==1 and s.frame_step==1
assert (s.render.resolution_x,s.render.resolution_y)==(1080,1920)
assert bpy.data.objects['RIG_BRIX'].type=='ARMATURE'
for name in ['ENVIRONMENT','BED','CHARACTER','LIGHTS','CAMERAS','UI','SLIME','GLASS','CLOTH','HONEY','SAND','WATER','LAVA']:assert 'EP002_'+name in bpy.data.collections
cloth=bpy.data.objects['FX_EP002_Cloth_Blanket']; mod=next(m for m in cloth.modifiers if m.type=='MESH_CACHE'); assert Path(bpy.path.abspath(mod.filepath)).is_file()
water=bpy.data.objects['FX_EP002_Water_Domain']; domain=next(m for m in water.modifiers if m.type=='FLUID').domain_settings; assert len(list((Path(bpy.path.abspath(domain.cache_directory))/'mesh').glob('*.bobj.gz')))==107
report={'file':bpy.data.filepath,'frame_range':[s.frame_start,s.frame_end],'resolution':[1080,1920],'fps':30,'preview_percentage':s.render.resolution_percentage,'markers':len(s.timeline_markers),'cloth_cache_exists':True,'water_mesh_frames':107,'glass_fragments':len([o for o in s.objects if o.name.startswith('FX_EP002_GlassShard_')]),'fonts_packed':all(f.packed_file or f.filepath=='<builtin>' for f in bpy.data.fonts),'libraries':{}}
for p in [ROOT/'00_LIBRARY/Environments/BRIX_TestStage.blend',ROOT/'01_TEMPLATES/BRIX_Shorts_Master_v002.blend']:
    with bpy.data.libraries.load(str(p),link=False) as (src,dst):report['libraries'][p.name]={'scenes':list(src.scenes),'collections':list(src.collections),'character_present':'RIG_BRIX' in src.objects}
assert not report['libraries']['BRIX_TestStage.blend']['character_present']
assert report['libraries']['BRIX_Shorts_Master_v002.blend']['character_present']
assert report['fonts_packed']
(EP/'edit/scene_verification.json').write_text(json.dumps(report,indent=2)); print('EP002_COLD_LOAD_VERIFIED '+json.dumps(report))
