import bpy,json
s=bpy.data.scenes['EP002_Impossible_Blankets']; bpy.context.window.scene=s; s.frame_set(118)
report={}
for o in bpy.data.collections['EP002_CHARACTER'].all_objects:
    if o.type=='MESH' and not o.hide_render:
        e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m=e.to_mesh(); v=[e.matrix_world@p.co for p in m.vertices]; report[o.name]={'min':[min(p[i] for p in v) for i in range(3)],'max':[max(p[i] for p in v) for i in range(3)]}; e.to_mesh_clear()
print('BODY_BOUNDS '+json.dumps(report))
