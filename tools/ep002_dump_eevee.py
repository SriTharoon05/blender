import bpy
s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s
print('EEVEE',[(p.identifier,str(getattr(s.eevee,p.identifier))) for p in s.eevee.bl_rna.properties if any(x in p.identifier for x in ['gi','trace','shadow','sample'])])
for light in bpy.data.lights:print('LIGHT',light.name,light.type,light.energy,[(p.identifier,str(getattr(light,p.identifier))) for p in light.bl_rna.properties if any(x in p.identifier for x in ['shadow','jitter'])])
