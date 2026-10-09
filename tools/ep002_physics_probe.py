import bpy,json
s=bpy.data.scenes['EP002_Impossible_Blankets']; bpy.context.window.scene=s; s.frame_set(118); r=bpy.data.objects['RIG_BRIX']; out={}
for a in [0,.5,-.5,1,-1]:
    for side in ['L','R']:r.pose.bones['upper_arm.'+side].rotation_euler=(a,0,0);r.pose.bones['forearm.'+side].rotation_euler=(0,0,0)
    bpy.context.view_layer.update();e=bpy.data.objects['CHAR_BRIX_Hand_L'].evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();vs=[e.matrix_world@v.co for v in m.vertices];out[str(a)]={'z':[min(p.z for p in vs),max(p.z for p in vs)],'y':[min(p.y for p in vs),max(p.y for p in vs)]};e.to_mesh_clear()
bpy.ops.mesh.primitive_cube_add();o=bpy.context.object
for kind in ['SOFT_BODY','CLOTH','FLUID']:
    m=o.modifiers.new('probe_'+kind,kind)
    if kind=='FLUID':m.fluid_type='DOMAIN';bpy.context.view_layer.update();m.domain_settings.domain_type='LIQUID';settings=m.domain_settings
    else:settings=m.settings
    out[kind]={p.identifier: str(getattr(settings,p.identifier,None)) for p in settings.bl_rna.properties if any(w in p.identifier for w in ['viscos','diffus','pressure','bend','pull','push','step','damp','effector','time_scale'])}
print('PHYSICS_PROBE '+json.dumps(out))
