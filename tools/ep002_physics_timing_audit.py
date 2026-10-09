import bpy
for name in ['HONEY','WATER','LAVA']:
 s=bpy.data.scenes['SIM_EP002_Physical_'+name];bpy.context.window.scene=s;o=bpy.data.objects['FX_EP002_'+name.title()+'_Domain'];d=next(m for m in o.modifiers if m.type=='FLUID').domain_settings
 print('TIMING',name,s.render.fps,s.render.fps_base,s.unit_settings.scale_length)
 print([(p.identifier,str(getattr(d,p.identifier))) for p in d.bl_rna.properties if any(x in p.identifier for x in ['time','frame_length','gravity'])])
 print('EFFECTOR_WEIGHTS_GRAVITY',d.effector_weights.gravity)
