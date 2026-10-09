import bpy,json
from pathlib import Path
EP=Path(__file__).resolve().parent.parent/'02_EPISODES/EP003_Gaming_Laptop_GP'
s=bpy.data.scenes['EP003_Gaming_Laptop_GreasePencil'];bpy.context.window.scene=s
o=bpy.data.objects['GP_EP003_Characters_Set_Laptops'];assert o.type=='GREASEPENCIL';assert len(o.data.layers[0].frames)==660
caption=bpy.data.objects['TXT_EP003_Constant_Caption'].data.body.replace('\n',' ')
assert caption=='Pov: You bring a gaming laptop to school instead of the normal mac book'
assert (s.render.engine,s.render.resolution_x,s.render.resolution_y,s.render.fps,s.frame_end)==('BLENDER_EEVEE',1080,1920,60,660)
assert len(s.sequence_editor.strips)==1
bpy.ops.file.pack_all()
assert s.sequence_editor.strips[0].sound.packed_file is not None
s.render.filepath='//../renders/frames_1080p60/EP003_######';s.render.image_settings.compression=50;s.frame_set(1)
o.data.layers.active=o.data.layers[0];bpy.context.view_layer.objects.active=o;o.select_set(True)
s['delivery_video']='../../../03_FINAL_OUTPUT/YouTube/EP003_Gaming_Laptop_GreasePencil_1080p60_v001.mp4'
s['audio_packed']=True
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP003_Gaming_Laptop_GP_v006.blend'),compress=True)
(EP/'edit/project_verification.json').write_text(json.dumps({'grease_pencil_drawings':660,'caption_exact':caption,'sound_packed':True,'fps':60,'resolution':[1080,1920],'renderer':'Eevee','duration_seconds':11,'editable_source':'blend/EP003_Gaming_Laptop_GP_v006.blend'},indent=2))
print('GP_PACKED_PROJECT_VALIDATED',flush=True)
