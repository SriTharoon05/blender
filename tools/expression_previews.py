import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender'); s=bpy.context.scene; r=bpy.data.objects['RIG_BRIX']; cam=s.camera
saved=(cam.location.copy(),cam.rotation_euler.copy(),cam.data.lens,s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage,s.render.filepath,s.eevee.taa_render_samples)
UI=bpy.data.collections['ASSET_MobileUI']; UI.hide_render=True
cam.location=(-.9,-3.7,2.75); cam.rotation_euler=(Vector((-1.62,-.35,2.54))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=68
s.render.resolution_x=360; s.render.resolution_y=360; s.render.resolution_percentage=100; s.eevee.taa_render_samples=64
exprs=['NEUTRAL','CONFIDENT','CURIOUS','SUSPICIOUS','SURPRISED','SCARED','DISGUSTED','IMPRESSED','RELIEVED','EXCITED']
try:
    for expr in exprs:
        for e in exprs:r[e]=float(e==expr)
        r.update_tag(); s.frame_set(s.frame_current+1); bpy.context.view_layer.update()
        s.render.filepath=str(ROOT/('01_TEMPLATES/Previews/BRIX_Expression_'+expr+'.png')); bpy.ops.render.render(write_still=True)
finally:
    for e in exprs:r[e]=float(e=='CONFIDENT')
    r.update_tag(); UI.hide_render=False
    cam.location,cam.rotation_euler,cam.data.lens,s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage,s.render.filepath,s.eevee.taa_render_samples=saved
    s.frame_set(1); bpy.context.view_layer.update()
print('TEN_EXPRESSION_PREVIEWS_READY')
