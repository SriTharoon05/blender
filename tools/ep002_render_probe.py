import bpy,json,gpu
s=bpy.data.scenes['EP002_Impossible_Blankets'];out={'engine':s.render.engine,'samples':s.eevee.taa_render_samples,'eevee':{},'ray_options':{},'gpu':{}}
for p in s.eevee.bl_rna.properties:
    if any(t in p.identifier for t in ['blur','ray','sample','volume']):out['eevee'][p.identifier]=str(getattr(s.eevee,p.identifier))
for p in s.eevee.ray_tracing_options.bl_rna.properties:out['ray_options'][p.identifier]=str(getattr(s.eevee.ray_tracing_options,p.identifier))
for n in ['renderer_get','vendor_get','backend_type_get']:
    try:out['gpu'][n]=getattr(gpu.platform,n)()
    except Exception as e:out['gpu'][n]=str(e)
print('RENDER_PROFILE '+json.dumps(out),flush=True)
