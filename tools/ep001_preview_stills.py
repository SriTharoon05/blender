import bpy,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test'); s=bpy.data.scenes['EP001_Material_Test']; bpy.context.window.scene=s
s.render.resolution_percentage=50; s.eevee.taa_render_samples=48; s.render.image_settings.file_format='PNG'
shots=[('01_Establishing',24),('02_ButtonClick',63),('03_Slime',155),('04_Glass',321),('05_Cloth',497),('06_Water',608),('07_Honey',792),('08_Sand',934),('09_LavaClimax',1115),('10_FinalComedy',1230)]
report={}
for name,frame in shots:
    s.frame_set(frame); bpy.context.view_layer.update(); s.render.filepath=str(EP/'previews'/(name+'.png')); bpy.ops.render.render(write_still=True)
    assets=[]
    for o in s.objects:
        if o.type=='MESH' and o.name.startswith('EP001_') and not o.hide_render:
            e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); assets.append({'object':o.name,'vertices':len(e.data.vertices)})
    report[name]={'frame':frame,'assets':assets}
    print('PREVIEW_STILL '+name,flush=True)
s.frame_set(1); s.render.resolution_percentage=25; s.eevee.taa_render_samples=32; s.render.filepath='//../previews/EP001_Preview.png'
(EP/'edit/still_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('STILLS_READY')
