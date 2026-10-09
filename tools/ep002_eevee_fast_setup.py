import bpy,json,sys,time,struct
from pathlib import Path
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender');EP=ROOT/'02_EPISODES/EP002_Impossible_Blankets';mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'review'
source=(ROOT/'tools/ep002_prepare_deferred_master.py').read_text()
exec(source.split('# Portable native-60fps')[0])
if mode=='prepare':
 path=EP/'cache/particles/EP002_FineGranular_Physical60_v023.mdd'
 with path.open('rb') as f:nf,nv=struct.unpack('>2i',f.read(8))
 assert path.stat().st_size==8+nf*4+nf*nv*12,'Fine-grain simulation is incomplete'
 exec('# Portable native-60fps'+source.split('# Portable native-60fps')[1].split("s.render.engine='CYCLES'")[0])
 # Tiny grains use compact instanced geometry; cached physical movement is unchanged.
 for n in ng.nodes:
  if n.bl_idname=='GeometryNodeMeshIcoSphere':n.inputs['Subdivisions'].default_value=1

def fast_dielectric(name,tint,ior,rough):
 mat=bpy.data.materials[name];nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear()
 out=nodes.new('ShaderNodeOutputMaterial');clear=nodes.new('ShaderNodeBsdfTransparent');clear.inputs['Color'].default_value=(*tint,1);reflect=nodes.new('ShaderNodeBsdfAnisotropic');reflect.inputs['Color'].default_value=(.96,.99,1,1);reflect.inputs['Roughness'].default_value=rough;fresnel=nodes.new('ShaderNodeFresnel');fresnel.inputs['IOR'].default_value=ior;mix=nodes.new('ShaderNodeMixShader');links.new(fresnel.outputs['Fac'],mix.inputs[0]);links.new(clear.outputs['BSDF'],mix.inputs[1]);links.new(reflect.outputs['BSDF'],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface']);mat.surface_render_method='BLENDED';mat.use_raytrace_refraction=False;mat.use_backface_culling=True
 if hasattr(mat,'use_transparency_overlap'):mat.use_transparency_overlap=False
 mat['optical_method']='Fast Eevee Fresnel reflection plus tinted transmission; no expensive raytraced refraction.'
for name,tint,ior,rough in [
 ('MAT_EP002_Physical_WATER',(.93,.98,1),1.333,.055),
 ('MAT_EP002_Physical_HONEY',(.98,.61,.11),1.47,.1),
 ('MAT_EP002_TemperedGlass',(.96,.99,1),1.52,.04),
 ('MAT_EP002_PolycarbonateShield',(.96,.99,1),1.586,.04),
 ('MAT_EP002_ViscoelasticSlime',(.08,.68,.12),1.4,.09)]:fast_dielectric(name,tint,ior,rough)
if bpy.data.materials.get('MAT_EP002_EmbeddedAir'):fast_dielectric('MAT_EP002_EmbeddedAir',(.96,1,.96),1.05,.03)
# Amber surface scattering keeps honey readable against the cool blue set.
mat=bpy.data.materials['MAT_EP002_Physical_HONEY'];n=mat.node_tree.nodes;l=mat.node_tree.links;clear=next(x for x in n if x.type=='BSDF_TRANSPARENT');clear.inputs['Color'].default_value=(1,.94,.75,1);outer=next(x for x in n if x.type=='MIX_SHADER');amber=n.new('ShaderNodeBsdfDiffuse');amber.inputs['Color'].default_value=(.8,.24,.006,1);amber.inputs['Roughness'].default_value=.15;body=n.new('ShaderNodeMixShader');body.inputs[0].default_value=.30;l.new(clear.outputs[0],body.inputs[1]);l.new(amber.outputs[0],body.inputs[2]);l.new(body.outputs[0],outer.inputs[1])
for light in bpy.data.lights:
 if hasattr(light,'use_shadow_jitter'):light.use_shadow_jitter=False
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=60;s.render.fps_base=1;s.frame_start=1;s.frame_end=2250;s.frame_step=1
s.eevee.taa_render_samples=16;s.eevee.shadow_ray_count=1;s.eevee.shadow_step_count=2;s.eevee.use_raytracing=False
if hasattr(s.eevee,'use_fast_gi'):s.eevee.use_fast_gi=False
s.render.use_motion_blur=False;s.render.use_simplify=True;s.render.simplify_subdivision_render=1;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.use_sequencer=False;s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=10;s.render.filepath='//../renders/frames_1080p60/EP002_1080p60_'
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if fc.data_path in ['hide_render','hide_viewport']:
      for k in fc.keyframe_points:k.interpolation='CONSTANT'
s['delivery_spec']='Native vertical 1080x1920, 60fps, Eevee GPU rendering. 16 samples, no raytracing, Fresnel transmission for fast clear materials.';s['render_status']='Rendering authorized by user; supersedes prior pause and 4K request.';s['original_sound_design']='//../audio/EP002_Original_Material_SoundDesign_v002.wav';s.frame_set(48)
version='026' if mode=='prepare' else '025';bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend'/('EP002_v'+version+'.blend')),compress=True)
if mode=='review':
 results=[]
 for name,f in [('Opening',48),('Water',1590),('Honey',1100),('Slime',288),('Lava',1950),('Glass',478)]:
  s.frame_set(f);s.render.filepath=str(EP/'previews'/('EP002_Fast1080_'+name+'_v025.png'));t=time.monotonic();bpy.ops.render.render(write_still=True);results.append({'name':name,'seconds':time.monotonic()-t});print('FAST_BENCHMARK',results[-1],flush=True)
 import gpu
 print('ACTUAL_GPU',gpu.platform.renderer_get(),gpu.platform.vendor_get(),gpu.platform.backend_type_get(),flush=True)
 (EP/'edit/eevee_fast_benchmark.json').write_text(json.dumps(results,indent=2))
print('FAST_1080P60_'+mode.upper()+'_COMPLETE',flush=True)
