import bpy,json,struct,math,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender');EP=ROOT/'02_EPISODES/EP002_Impossible_Blankets';s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s
assert [s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage,s.render.fps,s.render.fps_base,s.frame_start,s.frame_end,s.frame_step]==[1080,1920,100,60,1,1,2250,1]
assert s.render.engine=='BLENDER_EEVEE' and s.render.image_settings.color_depth=='8';assert json.loads((EP/'edit/render_request_state.json').read_text())['allow_render']
report={'status':'Validated for native 1080p60 Eevee render','resolution':[1080,1920],'fps':60,'frame_count':2250,'duration_seconds':37.5,'png_bits':8,'renderer':'Eevee NVIDIA GTX 1650 Ti, 16 samples','simulations':{},'limitations':['Eevee transparency uses fast raster approximations.','Numerical physics approximates materials; granular contacts use spherical grains and moving oriented body volumes.']}
for name in ['FX_EP002_Slime_Blanket','FX_EP002_Cloth_Blanket','FX_EP002_Sand_GranularBody']:
 o=bpy.data.objects[name];m=next(x for x in o.modifiers if x.type=='MESH_CACHE');path=Path(bpy.path.abspath(m.filepath));assert path.exists()
 with path.open('rb') as file:
  nf,nv=struct.unpack('>2i',file.read(8));times=np.frombuffer(file.read(nf*4),dtype='>f4');assert np.max(np.abs(np.diff(times)-1/60))<1e-5;assert path.stat().st_size==8+nf*4+nf*nv*12
  minimum=float('inf');maximum=float('-inf');floor_gap=float('inf')
  for f in range(nf):
   points=np.frombuffer(file.read(nv*12),dtype='>f4').reshape(-1,3);assert np.isfinite(points).all();minimum=min(minimum,float(points[:,2].min()));maximum=max(maximum,float(points[:,2].max()))
   if name.endswith('GranularBody'):
    p=points.reshape(-1,4,3);r=np.linalg.norm(p[:,1]-p[:,0],axis=1);floor_gap=min(floor_gap,float(np.min(p[:,0,2]-r)))
  data={'cache':str(path.relative_to(EP)),'frames':nf,'vertices':nv,'world_z_range':[minimum,maximum],'fps':60}
  if name.endswith('GranularBody'):
   assert nv==59400*4 and nf==175;assert floor_gap>-.00007;data['individual_grains']=59400;data['minimum_floor_gap_m']=floor_gap
  report['simulations'][name]=data
for name in ['HONEY','WATER','LAVA']:
 o=bpy.data.objects['FX_EP002_'+name.title()+'_Domain'];d=next(m for m in o.modifiers if m.type=='FLUID').domain_settings;path=Path(bpy.path.abspath(d.cache_directory));files=list((path/'mesh').glob('*.bobj.gz'));assert len(files)==d.cache_frame_end-d.cache_frame_start+1;report['simulations'][name]={'frames':len(files),'resolution':d.resolution_max,'mesh_scale':d.mesh_scale,'cache':str(path.relative_to(EP))}
hashes=json.loads((EP/'edit/protected_hashes.json').read_text());changed=[p for p,h in hashes.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h];assert not changed;report['protected_files_unchanged']=len(hashes)
(EP/'edit/fast_master_verification_v026.json').write_text(json.dumps(report,indent=2));print('FAST_MASTER_VALIDATED',json.dumps(report),flush=True)
