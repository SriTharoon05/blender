import bpy,json,time
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');main=bpy.data.scenes['EP002_Impossible_Blankets'];sim=bpy.data.scenes['SIM_EP002_Physical_LAVA'];bpy.context.window.scene=sim;sim.frame_end=2066;sim.frame_start=1876;sim.render.fps=60;sim.frame_set(1876)
shield=bpy.data.objects['PROP_EP002_SafetyShield']
# Lock the catcher well before the source is released. Its motion no longer pushes into falling fluid.
for layer in shield.animation_data.action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    if fc.data_path=='location' and fc.array_index==0:
     for k in fc.keyframe_points:
      if k.co.x==1876:k.co.x=1804;k.handle_left.x=1804;k.handle_right.x=1804
      elif k.co.x==1898:k.co.x=1844;k.handle_left.x=1844;k.handle_right.x=1844
     fc.update()
for o in bpy.data.collections['EP002_LAVA'].objects:
 if o.name.startswith(('PROP_EP002_SafetyShield','PROP_EP002_ShieldEdge_','PROP_EP002_ShieldRim_','COLL_EP002_ShieldWall_')):
  if o.animation_data:
   for layer in o.animation_data.action.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for fc in bag.fcurves:
       if fc.data_path=='hide_render':
        for k in fc.keyframe_points:
         if k.co.x==1876:k.co.x=1804;k.handle_left.x=1804;k.handle_right.x=1804
        fc.update()
for o in list(sim.objects):
 if o.name.startswith('COLL_EP002_LAVA_'):
  sim.collection.objects.unlink(o)
  for m in o.modifiers:
   if m.type=='FLUID':m.show_viewport=False;m.show_render=False
# A single watertight trough resolves the sub-voxel plate leak. Interior contact surface is exact.
# Wall and base thickness exceed two grid cells; all shared faces are joined.
xs=[-1.28,-1.09,1.09,1.28];ys=[-1.50,-1.30,1.30,1.50];zs=[1.85,2.0625,2.34];occupied=set()
for z in range(2):
 for y in range(3):
  for x in range(3):
   if z==0 or x!=1 or y!=1:occupied.add((x,y,z))
verts=[];faces=[];lookup={}
directions=[((-1,0,0),[(0,0,0),(0,0,1),(0,1,1),(0,1,0)]),((1,0,0),[(1,0,0),(1,1,0),(1,1,1),(1,0,1)]),((0,-1,0),[(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),((0,1,0),[(0,1,0),(0,1,1),(1,1,1),(1,1,0)]),((0,0,-1),[(0,0,0),(0,1,0),(1,1,0),(1,0,0)]),((0,0,1),[(0,0,1),(1,0,1),(1,1,1),(0,1,1)])]
for x,y,z in occupied:
 for (dx,dy,dz),corners in directions:
  if (x+dx,y+dy,z+dz) in occupied:continue
  face=[]
  for a,b,c in corners:
   co=(xs[x+a],ys[y+b]-.96,zs[z+c])
   if co not in lookup:lookup[co]=len(verts);verts.append(co)
   face.append(lookup[co])
  faces.append(face)
me=bpy.data.meshes.new('EP002_WatertightLavaCatchGeometry');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('COLL_EP002_Lava_WatertightCatcher',me);sim.collection.objects.link(o);bpy.data.collections['EP002_LAVA'].objects.link(o);o.hide_render=True;o.display_type='WIRE';fm=o.modifiers.new('Closed grid-resolved lava catcher','FLUID');fm.fluid_type='EFFECTOR';bpy.context.view_layer.update();fm.effector_settings.surface_distance=.25
domain=bpy.data.objects['FX_EP002_Lava_Domain'];d=next(m for m in domain.modifiers if m.type=='FLUID').domain_settings;d.cache_directory='//../cache/fluid/physical_lava_60fps_v022';d.resolution_max=72;d.timesteps_min=3;d.timesteps_max=12;d.cfl_condition=2;d.viscosity_value=.02;d.use_viscosity=True;d.use_diffusion=True;d.surface_tension=.05;d.use_speed_vectors=True;domain.hide_viewport=False;sim.frame_set(1876);bpy.ops.object.select_all(action='DESELECT');domain.select_set(True);bpy.context.view_layer.objects.active=domain
print('LAVA_REBAKE_BEGIN',flush=True);t=time.monotonic();bpy.ops.fluid.bake_all();files=list((Path(bpy.path.abspath(d.cache_directory))/'mesh').glob('*.bobj.gz'));assert len(files)==191
bpy.context.window.scene=main;main.frame_set(48);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v022.blend'),compress=True);(EP/'edit/lava_recontain_report_v022.json').write_text(json.dumps({'cache':d.cache_directory,'resolution':72,'frames':191,'viscosity':.02,'wall_thickness_m':.19,'base_thickness_m':.2125,'collider':'single watertight trough, grid-resolved, exact interior contact plane','elapsed':time.monotonic()-t},indent=2));print('LAVA_REBAKE_COMPLETE',flush=True)
