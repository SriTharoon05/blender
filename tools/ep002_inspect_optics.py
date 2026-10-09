import bpy,json
s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s
for name in ['MAT_EP002_Physical_WATER','MAT_EP002_Physical_HONEY','MAT_EP002_TemperedGlass','MAT_EP002_PolycarbonateShield','MAT_EP002_ViscoelasticSlime']:
 m=bpy.data.materials[name];print('MATERIAL',name)
 for n in m.node_tree.nodes:
  if n.type=='BSDF_PRINCIPLED':
   print([(i.name,str(i.default_value),i.is_linked) for i in n.inputs if i.name in ['Base Color','Metallic','Roughness','IOR','Transmission Weight','Normal','Alpha']])
 print('LINKS',[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links])
 print('MATPROPS',[(p.identifier,str(getattr(m,p.identifier))) for p in m.bl_rna.properties if any(x in p.identifier for x in ['refra','thick','render_method'])])
o=bpy.data.objects['FX_EP002_Lava_Domain'];d=next(m for m in o.modifiers if m.type=='FLUID').domain_settings
for f in [1876,1890,1900,1910,1920,1940,1960,1980]:
 s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(dg);me=e.to_mesh();print('LAVAMESH',f,len(me.vertices),[list(o.matrix_world@v.co) for v in me.vertices[:2]]);e.to_mesh_clear()
print('DOMAIN',[(p.identifier,str(getattr(d,p.identifier))) for p in d.bl_rna.properties if p.identifier in ['resolution_max','cache_directory','effector_weights','use_viscosity','viscosity_value']])
