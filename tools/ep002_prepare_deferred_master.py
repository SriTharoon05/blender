import bpy,json,struct,array
from pathlib import Path
from mathutils import Vector
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s
# The visible catcher uses the exact watertight geometry used in the liquid simulation.
s.frame_set(1876);shield=bpy.data.objects['PROP_EP002_SafetyShield'];proxy=bpy.data.objects['COLL_EP002_Lava_WatertightCatcher'];me=proxy.data.copy();me.name='EP002_VisibleWatertightPolycarbonateCatcher';inv=shield.matrix_world.inverted()
for v in me.vertices:v.co=inv@(proxy.matrix_world@v.co)
me.materials.clear();me.materials.append(bpy.data.materials['MAT_EP002_PolycarbonateShield']);shield.data=me
for m in list(shield.modifiers):
 if m.type=='BEVEL':shield.modifiers.remove(m)
bevel=shield.modifiers.new('Polished catcher edges','BEVEL');bevel.width=.006;bevel.segments=3
for o in bpy.data.collections['EP002_LAVA'].objects:
 if o.name.startswith(('PROP_EP002_ShieldEdge_','PROP_EP002_ShieldRim_','COLL_EP002_ShieldWall_')):
  o.animation_data_clear();o.hide_render=True
rig=bpy.data.objects['RIG_BRIX']
air=bpy.data.materials.get('MAT_EP002_EmbeddedAir')
if air:
 air.node_tree.nodes.clear();g=air.node_tree.nodes.new('ShaderNodeBsdfGlass');g.inputs['Color'].default_value=(1,1,1,1);g.inputs['Roughness'].default_value=.015;g.inputs['IOR'].default_value=1/1.4;out=air.node_tree.nodes.new('ShaderNodeOutputMaterial');air.node_tree.links.new(g.outputs['BSDF'],out.inputs['Surface']);air['optical_note']='Trapped air pocket boundary: air-to-gel relative refractive index 1/1.4.'
for layer in rig.animation_data.action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    if 'rotation_euler' in fc.data_path and fc.array_index==0 and any(x in fc.data_path for x in ['upper_arm.','forearm.']):
     for k in fc.keyframe_points:
      if 1804<=k.co.x<=2066:k.co.y=0;k.handle_left.y=0;k.handle_right.y=0
     for f in [1804,1844,2066]:fc.keyframe_points.insert(f,0,options={'FAST'})
     fc.update()
# Portable native-60fps fine-grain cache; each grain has its own simulated translation and spin.
path=EP/'cache/particles/EP002_FineGranular_Physical60_v023.mdd'
with path.open('rb') as f:
 count,N=struct.unpack('>2i',f.read(8));assert count==175 and N==59400*4;f.seek(8+count*4);coords=array.array('f');coords.frombytes(f.read(N*12));coords.byteswap()
me=bpy.data.meshes.new('EP002_FineGrains_CachedOrientations');me.from_pydata([coords[i:i+3] for i in range(0,len(coords),3)],[],[]);me.update();radius=me.attributes.new('grain_radius','FLOAT','POINT');ids=me.attributes.new('grain_index','INT','POINT')
for i in range(N):
 a=(i//4)*12;r=(Vector(coords[a+3:a+6])-Vector(coords[a:a+3])).length;radius.data[i].value=r;ids.data[i].value=i//4
o=bpy.data.objects['FX_EP002_Sand_GranularBody'];o.data=me;cache=next(m for m in o.modifiers if m.type=='MESH_CACHE');cache.filepath='//../cache/particles/'+path.name;cache.frame_start=1256
ng=next(m for m in o.modifiers if m.type=='NODES').node_group
for n in ng.nodes:
 if n.bl_idname=='GeometryNodeMeshIcoSphere':n.inputs['Subdivisions'].default_value=2
 if n.bl_idname=='ShaderNodeMath' and n.operation=='MULTIPLY' and abs(n.inputs[1].default_value-.94)<.001:n.inputs[1].default_value=1
 if n.bl_idname=='ShaderNodeMath' and n.operation=='MULTIPLY' and abs(n.inputs[1].default_value-1.08)<.001:n.inputs[1].default_value=1
o['physical_grain_count']=59400;o['method']='Each spherical grain simulated with gravity, equal/opposite contact impulses, Coulomb friction and spin, at 480Hz. Moving oriented body collision volumes.'
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=128;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.015;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=False;s.cycles.use_auto_tile=True;s.cycles.tile_size=256;s.cycles.max_bounces=12;s.cycles.transmission_bounces=8;s.cycles.transparent_max_bounces=8;s.render.use_persistent_data=False;s.render.use_border=False;s.render.use_crop_to_border=False
s.render.resolution_x=2160;s.render.resolution_y=3840;s.render.resolution_percentage=100;s.render.fps=60;s.render.fps_base=1;s.frame_start=1;s.frame_end=2250;s.frame_step=1;s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='16';s.render.image_settings.compression=30;s.render.filepath='//../renders/frames/EP002_4K60_'
for action in bpy.data.actions:
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if fc.data_path in ['hide_render','hide_viewport']:
      for k in fc.keyframe_points:k.interpolation='CONSTANT'
s['render_status']='DEFERRED by user instruction. Native 4K60 configured; final video has not been rendered.';s['physics_methods']='Volume-conserving viscoelastic slime, breakable constrained rigid glass, self-colliding cloth, viscous honey, individual fine-grain DEM, FLIP water, viscous lava in a watertight catcher.';s['quality_note']='Numerical simulations approximate physical materials. CPU Cycles configured because full-frame CUDA 4K tests failed on this GPU. Final motion and full-resolution path-traced validation remain deferred with rendering.'
bpy.data.objects['COLL_EP002_Floor'].dimensions=(200,200,.10)
sound=EP/'audio/EP002_Original_Material_SoundDesign_v002.wav'
if sound.exists():
 editor=s.sequence_editor_create()
 if 'EP002_Original_Material_SoundDesign' not in editor.strips:
  editor.strips.new_sound('EP002_Original_Material_SoundDesign',str(sound),channel=1,frame_start=1)
 s.render.use_sequencer=False
s['original_sound_design']='//../audio/EP002_Original_Material_SoundDesign_v002.wav'
s.frame_set(48);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v024.blend'),compress=True);print('DEFERRED_4K60_MASTER_SAVED',flush=True)
