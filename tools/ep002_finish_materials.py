import bpy,random,json,sys
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s
def bump(mat,scale,strength,distance):
    n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=3;bn=n.new('ShaderNodeBump');bn.inputs['Strength'].default_value=strength;bn.inputs['Distance'].default_value=distance;l.new(noise.outputs['Fac'],bn.inputs['Height']);l.new(bn.outputs['Normal'],p.inputs['Normal'])
cloth=bpy.data.objects['FX_EP002_Cloth_Blanket'];uv=cloth.data.uv_layers.new(name='Physical_WeaveUV')
for poly in cloth.data.polygons:
    for li in poly.loop_indices:
        co=cloth.data.vertices[cloth.data.loops[li].vertex_index].co;uv.data[li].uv=((co.x+1.175)/2.35,(co.y+1.06)/2.12)
mat=cloth.data.materials[0].copy();mat.name='MAT_EP002_Cloth_Woven4K';cloth.data.materials[0]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');waves=[]
for direction in ['X','Y']:
    wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction=direction;wave.inputs['Scale'].default_value=330;wave.inputs['Distortion'].default_value=.2;l.new(tc.outputs['UV'],wave.inputs['Vector']);waves.append(wave)
mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(waves[0].outputs['Fac'],mul.inputs[0]);l.new(waves[1].outputs['Fac'],mul.inputs[1]);bn=n.new('ShaderNodeBump');bn.inputs['Strength'].default_value=.22;bn.inputs['Distance'].default_value=.0012;l.new(mul.outputs[0],bn.inputs['Height']);l.new(bn.outputs['Normal'],p.inputs['Normal']);p.inputs['Roughness'].default_value=.78;p.inputs['Sheen Weight'].default_value=.25;p.inputs['Sheen Roughness'].default_value=.7
for name in ['MAT_TestBed_Terracotta','MAT_TestBed_Linen']:
    if name in bpy.data.materials:bump(bpy.data.materials[name],230,.18,.0014)
# Slime is an actual simulated translucent volume. Embedded air pockets follow its cached deformation.
slime=bpy.data.objects['FX_EP002_Slime_Blanket'];mat=slime.data.materials[0].copy();mat.name='MAT_EP002_ViscoelasticSlime';slime.data.materials[0]=mat;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.018,.55,.075,1);p.inputs['Transmission Weight'].default_value=.72;p.inputs['Roughness'].default_value=.10;p.inputs['IOR'].default_value=1.4;p.inputs['Coat Weight'].default_value=.35;p.inputs['Coat Roughness'].default_value=.065
attr=slime.data.attributes.new('air_pocket','BOOLEAN','POINT');rng=random.Random(401)
sites=rng.sample([i for i,v in enumerate(slime.data.vertices) if v.co.z>.05 and abs(v.co.x)<.9 and abs(v.co.y)<1.05],30)
for i in sites:attr.data[i].value=True
air=bpy.data.materials.new('MAT_EP002_EmbeddedAir');air.use_nodes=True;ap=air.node_tree.nodes.get('Principled BSDF');ap.inputs['Base Color'].default_value=(.8,1,.86,1);ap.inputs['Transmission Weight'].default_value=1;ap.inputs['IOR'].default_value=1.05;ap.inputs['Roughness'].default_value=.02
o=slime.copy();o.data=slime.data;o.name='FX_EP002_Slime_AdvectedAirPockets';bpy.data.collections['EP002_SLIME'].objects.link(o)
for m in list(o.modifiers):
    if m.type!='MESH_CACHE':o.modifiers.remove(m)
ng=bpy.data.node_groups.new('EP002_EmbeddedAir_PhysicalAdvection','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=ng.nodes;l=ng.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');a=n.new('GeometryNodeInputNamedAttribute');a.data_type='BOOLEAN';a.inputs['Name'].default_value='air_pocket';pos=n.new('GeometryNodeSetPosition');normal=n.new('GeometryNodeInputNormal');vm=n.new('ShaderNodeVectorMath');vm.operation='SCALE';vm.inputs[3].default_value=-.025;l.new(normal.outputs[0],vm.inputs[0]);l.new(vm.outputs['Vector'],pos.inputs['Offset']);l.new(inp.outputs[0],pos.inputs['Geometry']);pts=n.new('GeometryNodeMeshToPoints');pts.mode='VERTICES';l.new(pos.outputs[0],pts.inputs['Mesh']);l.new(a.outputs['Attribute'],pts.inputs['Selection']);ico=n.new('GeometryNodeMeshIcoSphere');ico.inputs['Radius'].default_value=.012;ico.inputs['Subdivisions'].default_value=2;sm=n.new('GeometryNodeSetMaterial');sm.inputs['Material'].default_value=air;l.new(ico.outputs['Mesh'],sm.inputs['Geometry']);inst=n.new('GeometryNodeInstanceOnPoints');l.new(sm.outputs[0],inst.inputs['Instance']);l.new(pts.outputs[0],inst.inputs['Points']);l.new(inst.outputs[0],out.inputs['Geometry']);mod=o.modifiers.new('Embedded gas pockets','NODES');mod.node_group=ng
# Optical properties stay physically distinct; continuous procedural textures retain detail at 4K.
glass=bpy.data.materials['MAT_Glass_Clear'].copy();glass.name='MAT_EP002_TemperedGlass';gp=glass.node_tree.nodes.get('Principled BSDF');gp.inputs['Transmission Weight'].default_value=1;gp.inputs['IOR'].default_value=1.52;gp.inputs['Roughness'].default_value=.025
for obj in bpy.data.collections['EP002_GLASS'].objects:
    if obj.name.startswith('FX_EP002_GlassShard_'):obj.data.materials[0]=glass
shieldmat=glass.copy();shieldmat.name='MAT_EP002_PolycarbonateShield';shieldmat.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.586
for obj in bpy.data.collections['EP002_LAVA'].objects:
    if obj.name=='PROP_EP002_SafetyShield' or obj.name.startswith('COLL_EP002_ShieldWall_'):obj.data.materials[0]=shieldmat
for name,color,density in [('HONEY',(.88,.34,.035,1),1.1),('WATER',(.62,.9,1,1),.018)]:
    mat=bpy.data.materials['MAT_EP002_Physical_'+name];n=mat.node_tree.nodes;l=mat.node_tree.links;out=n.get('Material Output');absorb=n.new('ShaderNodeVolumeAbsorption');absorb.inputs['Color'].default_value=color;absorb.inputs['Density'].default_value=density;l.new(absorb.outputs[0],out.inputs['Volume'])
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=2160;s.render.resolution_y=3840;s.render.resolution_percentage=100;s.render.fps=60;s.render.fps_base=1;s.frame_start=1;s.frame_end=2250;s.frame_step=1;s.eevee.taa_render_samples=128;s.eevee.shadow_ray_count=4;s.eevee.use_raytracing=True;s.render.use_simplify=False;s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=30
if hasattr(s.render,'use_motion_blur'):s.render.use_motion_blur=True;s.render.motion_blur_shutter=.25
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if fc.data_path in ['hide_render','hide_viewport','["selected_material"]']:
                        for k in fc.keyframe_points:k.interpolation='CONSTANT'
version=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '016'
s['delivery_spec']='2160x3840 vertical 4K, true 60fps, 37.5 seconds, physical material simulations, procedural surface detail.';s.render.filepath='//../renders/frames/EP002_4K60_';s.frame_set(48);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend'/('EP002_v'+version+'.blend')),compress=True);print('4K60_MATERIAL_FINISH_COMPLETE')
