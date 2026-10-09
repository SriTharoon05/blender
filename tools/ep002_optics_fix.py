import bpy
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s
def optical(name,colour,ior,rough,thickness,transmission=1):
 m=bpy.data.materials[name];n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 for link in list(l):
  if link.to_node==p and link.to_socket.name in ['Base Color','Normal']:l.remove(link)
 p.inputs['Base Color'].default_value=(*colour,1);p.inputs['Metallic'].default_value=0;p.inputs['Transmission Weight'].default_value=transmission;p.inputs['IOR'].default_value=ior;p.inputs['Roughness'].default_value=rough;p.inputs['Coat Weight'].default_value=0
 m.use_raytrace_refraction=True;m.thickness_mode='SLAB';m.use_thickness_from_shadow=False;n.get('Material Output').inputs['Thickness'].default_value=thickness
 return m
optical('MAT_EP002_Physical_WATER',(.98,.995,1),1.333,.035,.018)
optical('MAT_EP002_Physical_HONEY',(1,.81,.36),1.47,.085,.055)
optical('MAT_EP002_TemperedGlass',(.98,.995,1),1.52,.025,.028)
optical('MAT_EP002_PolycarbonateShield',(.99,1,1),1.586,.035,.065)
optical('MAT_EP002_ViscoelasticSlime',(.075,.75,.15),1.4,.08,.10,.9)
for name in ['HONEY','WATER','LAVA']:
 o=bpy.data.objects['FX_EP002_'+name.title()+'_Domain']
 ng=bpy.data.node_groups.new('EP002_'+name+'_SmoothFluidNormals','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=ng.nodes;l=ng.links;a=n.new('NodeGroupInput');b=n.new('NodeGroupOutput');smooth=n.new('GeometryNodeSetShadeSmooth');smooth.domain='FACE';l.new(a.outputs['Geometry'],smooth.inputs['Geometry']);l.new(smooth.outputs['Geometry'],b.inputs['Geometry']);m=o.modifiers.new('Smooth liquid surface normals','NODES');m.node_group=ng
 sm=o.modifiers.new('Subvoxel surface polish','SMOOTH');sm.factor=.35;sm.iterations=2
s.frame_set(48);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP002_v021.blend'),compress=True)
s.render.resolution_percentage=25;s.render.image_settings.color_depth='8';s.eevee.taa_render_samples=64
for name,f in [('Water',1590),('Honey',1100),('Glass',478),('Slime',288)]:
 s.frame_set(f);s.render.filepath=str(EP/'previews'/('EP002_Optics_'+name+'_v021.png'));bpy.ops.render.render(write_still=True)
print('OPTICAL_REVIEW_COMPLETE',flush=True)
