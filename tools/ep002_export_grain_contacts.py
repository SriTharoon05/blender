import bpy,json
from pathlib import Path
from mathutils import Vector
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');s=bpy.data.scenes['EP002_Impossible_Blankets'];bpy.context.window.scene=s;rig=bpy.data.objects['RIG_BRIX'];s.frame_set(1256);dg=bpy.context.evaluated_depsgraph_get();boxes=[]
names=['Body','Jacket_Hem','ChestBadge','Neck','Head','Thigh_L','Thigh_R','Shin_L','Shin_R','Boot_L','Boot_R','BootSole_L','BootSole_R','BootAccent_L','BootAccent_R','UpperArm_L','UpperArm_R','Forearm_L','Forearm_R','Cuff_L','Cuff_R','Hand_L','Hand_R','Thumb_L','Thumb_R']
for name in ['CHAR_BRIX_'+x for x in names]+['PROP_TestBed_Mattress','PROP_TestBed_Pillow','PROP_TestBed_WalnutFrame','COLL_EP002_Floor']:
 src=bpy.data.objects[name];weights={}
 for v in src.data.vertices:
  for g in v.groups:weights[g.group]=weights.get(g.group,0)+g.weight
 bone=src.vertex_groups[max(weights,key=weights.get)].name if weights else None
 if bone and bone not in rig.pose.bones:bone=None
 B=rig.matrix_world@rig.pose.bones[bone].matrix if bone else src.matrix_world.copy();e=src.evaluated_get(dg);me=e.to_mesh();inv=B.inverted();v=[inv@(e.matrix_world@x.co) for x in me.vertices];lo=Vector([min(x[i] for x in v) for i in range(3)]);hi=Vector([max(x[i] for x in v) for i in range(3)]);e.to_mesh_clear();boxes.append({'name':name,'bone':bone,'lo':list(lo),'hi':list(hi),'matrices':[]})
for f in range(1256,1431):
 s.frame_set(f);bpy.context.view_layer.update()
 for box in boxes:
  src=bpy.data.objects[box['name']];B=rig.matrix_world@rig.pose.bones[box['bone']].matrix if box['bone'] else src.matrix_world.copy();box['matrices'].append([list(row) for row in B])
(EP/'cache/particles/fine_grain_colliders_v023.json').write_text(json.dumps({'start':1256,'end':1430,'fps':60,'boxes':boxes}));print('MOVING_GRAIN_CONTACTS_EXPORTED')
